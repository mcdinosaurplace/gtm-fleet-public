"""Deterministic off-cycle position trigger for performance-marketer (Block B2).

On non-position days, performance-marketer still runs its daily spend + ranking watch. When the
day's anomalies are serious enough, it should form an off-cycle (scoped) position
dossier rather than waiting for the Thursday position pass. This module decides
whether that bar is met — deterministically, not by model judgment.

Rule (mirrors state/identity/performance-marketer.md):
    - any HIGH-severity anomaly                  -> trigger
    - >= MED_CLUSTER MED anomalies on the day    -> trigger (clustered)
    - otherwise                                  -> no trigger
      (LOW-only, or a lone/sparse MED, stays journal-only)

Pure and network-free: same alerts in -> same decision out, pinned by golden
tests. The caller (the daily Tick) collects the day's spend_alerts + MED/HIGH
ranking anomalies and passes them in.
"""

DEFAULT_MED_CLUSTER = 3

HIGH = "HIGH"
MED = "MED"
LOW = "LOW"


def _sev(alert):
    return str(alert.get("severity", "")).strip().upper()


def _label(alert):
    """A short human label for the reason string."""
    return (alert.get("description")
            or alert.get("campaign_name")
            or alert.get("keyword")
            or alert.get("surface")
            or "anomaly")


def should_form_position(alerts, med_cluster=DEFAULT_MED_CLUSTER):
    """Decide whether the day's anomalies warrant an off-cycle dossier.

    `alerts` is a list of anomaly dicts, each with at least a `severity`
    ('LOW'|'MED'|'HIGH'). Returns:
        {
          "trigger":    bool,
          "severity":   'HIGH' | 'MED' | None,   # what tripped it
          "reason":     str,                       # for the dossier trigger_reason
          "triggering": list,                      # the anomalies that tripped it
        }
    """
    alerts = list(alerts or [])
    highs = [a for a in alerts if _sev(a) == HIGH]
    meds = [a for a in alerts if _sev(a) == MED]

    if highs:
        names = ", ".join(_label(a) for a in highs[:3])
        return {"trigger": True, "severity": HIGH, "triggering": highs,
                "reason": f"{len(highs)} HIGH anomaly(ies) — {names}"}

    if len(meds) >= med_cluster:
        names = ", ".join(_label(a) for a in meds[:3])
        return {"trigger": True, "severity": MED, "triggering": meds,
                "reason": f"clustered MED ({len(meds)} ≥ {med_cluster}) — {names}"}

    return {"trigger": False, "severity": None, "triggering": [],
            "reason": f"no HIGH; {len(meds)} MED (< {med_cluster} cluster) — journal only"}
