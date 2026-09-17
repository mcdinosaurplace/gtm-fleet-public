#!/usr/bin/env python3
"""scripts/google_ads_mutate.py — constrained Tier-3a write tool (Block E1).

The ONLY path that writes to Google Ads. It exposes only the 3a allowlist
(scripts/paid/config.py), enforces the locked caps IN CODE (a violated cap
RAISES — it never silently clamps), runs validate_only before any apply, and
never applies unless PERFORMANCE_MARKETER_EXECUTE=live. Every applied (live) or simulated
(shadow) change is logged to applied_changes with a prior_value snapshot for
one-command rollback.

Modes (scripts/paid/config.execution_mode):
    off    -> refuse: no API calls, nothing applied (default; Phase 2 ships here)
    shadow -> validate_only against the live API; log would-apply; never applies
    live   -> validate_only, then apply (requires the explicit operator flip)

The guard/plan layer (plan_execution, _check_op) is pure and unit-tested. The
API layer (_build_*, execute) is exercised by shadow runs — its Google Ads
request shapes are not unit-testable offline, so a shadow pass is the gate
before the off/shadow -> live flip.

Op dict shape (from a greenlit proposal's target_value):
    {"op_type": "set_bid", "platform": "google_ads",
     "entity": "<adGroupCriterion resource_name>", "bid_change_pct": 12.0,
     "proposal_id": 7}
    {"op_type": "add_negative", "entity": "<adGroup resource_name>",
     "keyword_text": "free crm", "match_type": "EXACT", "proposal_id": 8}
"""
import json

from scripts.paid import config, db

# Ops with an implemented auto-apply path. The other allowlisted ops
# (match_type_promotion, create_experiment) are deferred to a human until built.
SUPPORTED_OPS = ("add_negative", "set_bid")


class GuardError(Exception):
    """A proposed op violates a 3a cap/allowlist. We raise — never silently clamp."""


class NoBidLever(Exception):
    """A set_bid op has no auto-applicable lever under the campaign's bidding
    strategy (e.g. Maximize Conversions with no target CPA). Routed to 3b/human."""


# ============================================================
# Pure guard / plan layer (unit-tested; no API, no network)
# ============================================================

def _check_op(op):
    """Validate one op against the 3a allowlist and bounds. Raises GuardError."""
    ot = op.get("op_type")
    if ot not in config.ALLOWED_OPS:
        raise GuardError(f"op_type {ot!r} not in 3a allowlist {config.ALLOWED_OPS}")
    if ot == "set_bid":
        if not op.get("campaign"):
            raise GuardError("set_bid requires a campaign resource_name (to resolve the bidding strategy)")
        pct = op.get("bid_change_pct")
        if isinstance(pct, bool) or not isinstance(pct, (int, float)):
            raise GuardError("set_bid requires a numeric bid_change_pct")
        if abs(pct) > config.BID_CHANGE_PCT_MAX:
            raise GuardError(
                f"set_bid {pct:+.1f}% exceeds the ±{config.BID_CHANGE_PCT_MAX:g}% envelope")
        return True
    if not op.get("entity"):
        raise GuardError(f"op {ot!r} missing target entity (resource_name)")
    return True


def plan_execution(ops, mode=None):
    """Resolve mode, guard every op (raise on any violation), enforce run caps,
    and split supported vs deferred. Pure — applies nothing, makes no API calls."""
    mode = mode or config.execution_mode()
    ops = list(ops or [])
    for op in ops:
        _check_op(op)  # any violation raises here, before anything else
    if len(ops) > config.MAX_OPS_PER_RUN:
        raise GuardError(f"{len(ops)} ops exceed MAX_OPS_PER_RUN={config.MAX_OPS_PER_RUN}")
    n_neg = sum(1 for o in ops if o.get("op_type") == "add_negative")
    if n_neg > config.MAX_NEGATIVES_PER_RUN:
        raise GuardError(f"{n_neg} negatives exceed MAX_NEGATIVES_PER_RUN={config.MAX_NEGATIVES_PER_RUN}")
    n_promo = sum(1 for o in ops if o.get("op_type") == "match_type_promotion")
    if n_promo > config.MAX_MATCH_TYPE_PROMOTIONS_PER_RUN:
        raise GuardError(
            f"{n_promo} promotions exceed MAX_MATCH_TYPE_PROMOTIONS_PER_RUN="
            f"{config.MAX_MATCH_TYPE_PROMOTIONS_PER_RUN}")
    supported = [o for o in ops if o.get("op_type") in SUPPORTED_OPS]
    deferred = [o for o in ops if o.get("op_type") not in SUPPORTED_OPS]
    return {
        "mode": mode,
        "execute": mode in ("shadow", "live"),
        "will_apply": mode == "live",
        "supported": supported,
        "deferred_to_human": deferred,
        "counts": {"total": len(ops), "supported": len(supported),
                   "deferred": len(deferred), "negatives": n_neg, "promotions": n_promo},
    }


# ============================================================
# API layer (exercised by shadow runs before the live flip)
# ============================================================

def _client():
    from scripts.google_auth import get_ads_client, get_ads_customer_id
    return get_ads_client(), get_ads_customer_id()


def resolve_bid_lever(strategy_type, target_cpa_micros=0, target_roas=0.0):
    """Which bid lever a set_bid can move under a campaign's bidding strategy.

    Returns 'manual_cpc' | 'target_cpa' | 'target_roas' | None. None means there
    is no adjustable lever (e.g. Maximize Conversions with no target) — the op is
    deferred to a human (3b). Pure; unit-tested.
    """
    if (strategy_type or "").upper() == "MANUAL_CPC":
        return "manual_cpc"
    if target_cpa_micros and target_cpa_micros > 0:
        return "target_cpa"
    if target_roas and target_roas > 0:
        return "target_roas"
    return None


def _build_set_bid(client, cid, op):
    """Strategy-aware bid nudge.

    Manual CPC -> adjust the ad-group-criterion cpc_bid_micros (op['entity']).
    Automated bidding with a target, or no adjustable lever -> raise NoBidLever so
    execute() defers the op to a human (3b). The op carries `campaign` (to resolve
    the strategy) and, for manual CPC, `entity` (the criterion).
    """
    from google.api_core import protobuf_helpers
    ga = client.get_service("GoogleAdsService")
    camp_rn = op["campaign"]
    crow = next(iter(ga.search(customer_id=cid, query=(
        "SELECT campaign.bidding_strategy_type, campaign.maximize_conversions.target_cpa_micros, "
        "campaign.target_cpa.target_cpa_micros, campaign.maximize_conversion_value.target_roas, "
        "campaign.target_roas.target_roas FROM campaign "
        f"WHERE campaign.resource_name = '{camp_rn}'"))))
    c = crow.campaign
    tcpa = c.maximize_conversions.target_cpa_micros or c.target_cpa.target_cpa_micros
    troas = c.maximize_conversion_value.target_roas or c.target_roas.target_roas
    lever = resolve_bid_lever(c.bidding_strategy_type.name, tcpa, troas)
    if lever != "manual_cpc":
        why = (f"{c.bidding_strategy_type.name} has no adjustable bid/target"
               if lever is None else f"{lever} adjustment is human-applied (3b) for now")
        raise NoBidLever(f"set_bid on {camp_rn.split('/')[-1]}: {why}")
    rn = op["entity"]
    row = next(iter(ga.search(customer_id=cid, query=(
        "SELECT ad_group_criterion.cpc_bid_micros FROM ad_group_criterion "
        f"WHERE ad_group_criterion.resource_name = '{rn}'"))))
    prior = int(row.ad_group_criterion.cpc_bid_micros)
    new = int(round(prior * (1 + op["bid_change_pct"] / 100.0)))
    operation = client.get_type("AdGroupCriterionOperation")
    operation.update.resource_name = rn
    operation.update.cpc_bid_micros = new
    client.copy_from(operation.update_mask,
                     protobuf_helpers.field_mask(None, operation.update._pb))
    request = client.get_type("MutateAdGroupCriteriaRequest")
    request.customer_id = cid
    request.operations.append(operation)
    return {"cpc_bid_micros": prior}, {"cpc_bid_micros": new}, "AdGroupCriterionService", request


def _build_add_negative(client, cid, op):
    """Add an ad-group-level negative keyword (additive; rollback = remove)."""
    operation = client.get_type("AdGroupCriterionOperation")
    crit = operation.create
    crit.ad_group = op["entity"]
    crit.negative = True
    crit.keyword.text = op["keyword_text"]
    crit.keyword.match_type = client.enums.KeywordMatchTypeEnum[op.get("match_type", "EXACT")]
    request = client.get_type("MutateAdGroupCriteriaRequest")
    request.customer_id = cid
    request.operations.append(operation)
    return ({}, {"keyword": op["keyword_text"], "match_type": op.get("match_type", "EXACT"),
                 "negative": True}, "AdGroupCriterionService", request)


_BUILDERS = {"set_bid": _build_set_bid, "add_negative": _build_add_negative}
_METHODS = {"AdGroupCriterionService": "mutate_ad_group_criteria"}


def _run(client, service_name, request, validate_only):
    request.validate_only = validate_only
    svc = client.get_service(service_name)
    return getattr(svc, _METHODS[service_name])(request=request)


def execute(ops, conn=None, approval_ref=None, now=None, mode=None):
    """Plan, then validate (always) and apply (live only) the supported ops.

    off -> no API calls, nothing applied. shadow -> validate_only each op.
    live -> validate_only then apply. Each acted op is logged to applied_changes
    when `conn` is given. `now` is a caller-supplied ISO timestamp. Returns a
    result dict; never applies anything that plan_execution did not clear.
    """
    plan = plan_execution(ops, mode=mode)
    out = {"mode": plan["mode"], "validated": [], "applied": [],
           "deferred_to_human": plan["deferred_to_human"]}
    if not plan["execute"]:
        out["note"] = "execution disabled (PERFORMANCE_MARKETER_EXECUTE=off)"
        return out

    client, cid = _client()
    for op in plan["supported"]:
        try:
            prior, new, service, request = _BUILDERS[op["op_type"]](client, cid, op)
        except NoBidLever as e:
            out["deferred_to_human"].append({**op, "defer_reason": str(e)})
            continue
        _run(client, service, request, validate_only=True)   # always validate first
        entity = op.get("entity") or op.get("campaign")
        out["validated"].append(entity)
        if plan["will_apply"]:
            resp = _run(client, service, request, validate_only=False)
            results = getattr(resp, "results", None)
            if results:
                entity = results[0].resource_name or entity
            out["applied"].append(entity)
        if conn is not None:
            db.insert(conn, "applied_changes", {
                "agent": "performance-marketer",
                "proposal_id": op.get("proposal_id"),
                "approval_ref": approval_ref,
                "platform": "google_ads",
                "entity": entity,
                "op_type": op["op_type"],
                "prior_value": json.dumps(prior, sort_keys=True),
                "new_value": json.dumps(new, sort_keys=True),
                "mode": plan["mode"],
                "applied_at": now,
                "created_at": now,
            })
    return out


def rollback(applied_change, conn=None, now=None, mode=None):
    """Reverse a previously applied 3a change using its prior_value snapshot.

    Mode-gated like execute(): off -> inert; shadow -> validate_only; live ->
    apply and stamp applied_changes.rolled_back_at. Handles set_bid (restore the
    prior bid) and add_negative (remove the created criterion).
    """
    mode = mode or config.execution_mode()
    out = {"mode": mode, "rolled_back": False, "entity": applied_change.get("entity")}
    if mode == "off":
        out["note"] = "execution disabled (PERFORMANCE_MARKETER_EXECUTE=off)"
        return out

    op_type = applied_change["op_type"]
    prior = applied_change.get("prior_value")
    prior = json.loads(prior) if isinstance(prior, str) and prior else (prior or {})
    entity = applied_change["entity"]
    client, cid = _client()
    operation = client.get_type("AdGroupCriterionOperation")
    if op_type == "set_bid":
        from google.api_core import protobuf_helpers
        operation.update.resource_name = entity
        operation.update.cpc_bid_micros = int(prior["cpc_bid_micros"])
        client.copy_from(operation.update_mask,
                         protobuf_helpers.field_mask(None, operation.update._pb))
    elif op_type == "add_negative":
        operation.remove = entity
    else:
        raise GuardError(f"no rollback path for op_type {op_type!r}")
    request = client.get_type("MutateAdGroupCriteriaRequest")
    request.customer_id = cid
    request.operations.append(operation)

    _run(client, "AdGroupCriterionService", request, validate_only=True)
    if mode == "live":
        _run(client, "AdGroupCriterionService", request, validate_only=False)
        out["rolled_back"] = True
        if conn is not None and applied_change.get("id") is not None:
            db.mark_rolled_back(conn, applied_change["id"], now)
    return out
