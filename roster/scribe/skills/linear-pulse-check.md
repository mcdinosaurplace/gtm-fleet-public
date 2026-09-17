# Skill: linear-pulse-check

Read-only Tue–Fri pulse. Snapshots the **active** marketing Linear projects + issues
(including orphans) into `pm_projects` / `pm_issues` / `pm_blockers`, computes health,
detects missed deadlines (C2), and (when not in cycle 1) DMs owners on a state decline.
**Zero Linear writes.** Determinism: the agent does MCP I/O + normalization;
`scripts/pm/pulse.py` computes every row; `scripts/pm/db.py` writes. Invoked via
`/scribe pulse` or the scheduled Tue–Fri fire.

**Bounded active-window fetch — we do NOT re-pull the whole Marketing universe.** The
Marketing team's Linear history is thousands of issues, ~85% of them terminal
(completed/canceled) — finished work whose health can never change — plus a long tail of
dormant "zombie" projects created and never worked. Re-fetching and recomputing all of it
every run is what used to flood context and burn the run. Instead:

```
compute universe = active-window fetch  ∪  open-commitment referents
                 = list_*(updatedAt = today − scope_window_days)  ∪  live pm_commitments refs
```

Everything else in the cache — terminal, OR non-terminal but stale beyond
`scope_window_days` (a **hygiene/backlog** problem, not live work) — is **frozen**: kept in
the DB as the historical record, NOT re-fetched, NOT recomputed, NOT re-upserted, and
instead **counted into the hygiene tally** for candid Thursday-agenda reporting.
`pulse.select_working_set` assembles this set; `pulse.check_brake` guards it. The window,
brake ceilings, and thresholds all live in `state/identity/scribe-pm-cadence.yaml`
(`pulse:` block, validated fail-closed). **The same bounded path runs every day** — there
is no separate "Friday full pull" (the old delta-watermark scheme is gone).

**Context safety.** All bulk MCP results (the `list_*` pages, the per-issue
`get_issue(includeRelations)` loop, the `get_status_updates` calls) are fetched inside a
**fetch subagent** that writes raw JSON to `/tmp/pm_*.json` and returns only counts + a
manifest. The bulk payloads never enter the main agent's context; the main agent does only
the cheap deterministic Python (normalize → select_working_set → check_brake →
compute_pulse). This is what keeps the run flat regardless of scope.

## Preflight

- PM Librarian (see `roster/scribe/prompt.md`): load `scribe.md` + `scribe-pm.md`; validate
  the cadence config — `python3 -m scripts.pm.config` (abort on non-zero exit, fail closed);
  read the PM journal; run pending migrations.
- Anchor: confirm today is **Tue–Fri**. A manual off-cadence run proceeds with a note.
- **Run mode.** Note whether this is a **headless** run (scheduled / non-interactive fire)
  or an **interactive** run (`/scribe pulse` typed by a human). This governs the brake's
  behavior on a trip (Steps 3–4): headless auto-narrows + flags; interactive stops and asks.
  **An interactive run MUST export `PM_RUN_MODE=interactive` in the environment** before
  running the Step 3/4 heredocs (they read `os.environ`, not argv — a stdin heredoc's argv
  is always `-`). Headless/scheduled runs leave it unset (defaults to `headless`).
- MCP preflight: **Slack + Linear essential**. Abort before any write if either fails to
  bind (log `MCP_BIND_FAILURE` to Scott).

## Steps

1. **Prior state + commitment refs + config.** Via `db.py`: `fetchall` current
   `pm_projects`, `pm_issues`, open `pm_blockers` (`resolved_at IS NULL`), and the set of
   `project_id`s already in `pm_missed_deadlines`. Also load the **open-commitment
   referents** — the belt-and-suspenders set that pins committed-to work into scope even if
   it fell outside the activity window:
   ```bash
   python3 - <<'PY'
   import json, sys; sys.path.insert(0, ".")
   from scripts.pm import db
   c = db.connect()
   rows = db.fetchall(c, """
     SELECT issue_id, project_id FROM pm_commitments
     WHERE completion_status != 'completed'
       AND (issue_id IS NOT NULL OR project_id IS NOT NULL)
   """)
   json.dump({
       "issue_ids":   sorted({r["issue_id"]   for r in rows if r["issue_id"]}),
       "project_ids": sorted({r["project_id"] for r in rows if r["project_id"]}),
   }, open("/tmp/pm_commit_refs.json", "w"))
   # prior rows -> /tmp for the compute heredoc (avoid re-querying)
   json.dump({r["id"]: dict(r) for r in db.fetchall(c, "SELECT * FROM pm_projects")}, open("/tmp/pm_prior_projects.json","w"), default=str)
   json.dump({r["id"]: dict(r) for r in db.fetchall(c, "SELECT * FROM pm_issues")},   open("/tmp/pm_prior_issues.json","w"),   default=str)
   json.dump([dict(r) for r in db.fetchall(c, "SELECT * FROM pm_blockers WHERE resolved_at IS NULL")], open("/tmp/pm_prior_blockers.json","w"), default=str)
   json.dump(sorted({r["project_id"] for r in db.fetchall(c, "SELECT project_id FROM pm_missed_deadlines")}), open("/tmp/pm_prior_missed_ids.json","w"))
   c.close()
   print("commit refs:", len(json.load(open("/tmp/pm_commit_refs.json"))["issue_ids"]), "issues,",
         len(json.load(open("/tmp/pm_commit_refs.json"))["project_ids"]), "projects")
   PY
   ```
   Compute the window cutoff: `today − pulse.scope_window_days` as an ISO-8601 date
   (`load_config().pulse.scope_window_days`, default 90).

2. **Active-window fetch (FETCH SUBAGENT → `/tmp`).** Spawn a subagent (Agent tool) whose
   entire job is the bulk Linear reads; it must write raw JSON to `/tmp` and return **only
   counts**, so no bulk payload enters the main context. Brief it to:
   - `list_projects(team="Marketing", updatedAt="<cutoff ISO>")`, paginate via `cursor`.
     **Do NOT pass `includeMembers`** (this Linear MCP returns HTTP 400 for it — verified);
     omit `includeMilestones`; **do NOT pass `includeArchived: true`** (leave default
     `false`). Write the raw project objects to `/tmp/pm_delta_projects_raw.json`.
   - `list_issues(team="Marketing", limit=250, updatedAt="<cutoff ISO>")`, paginate. Write
     raw issue objects to `/tmp/pm_delta_issues_raw.json`.
   - **Commitment backfill:** for any id in `/tmp/pm_commit_refs.json` NOT present in the two
     lists above, `get_project(id)` / `get_issue(id)` and append to the respective raw file.
   - Return a one-line manifest: `{projects: N, issues: M, commit_backfilled: k}`.
   Consequence of omitting `includeMembers` (unchanged from before): a project with no lead
   resolves to `Unassigned` (`owner_source='unassigned'`) and is flagged for Thursday rather
   than guessed.

3. **Scope + emergency brake (main agent — cheap Python, no MCP).** Normalize the raw
   delta, assemble the working set, and run the brake **before** the expensive relation
   loop:
   ```bash
   python3 - <<'PY'
   import json, os, sys; sys.path.insert(0, ".")
   from datetime import date
   from scripts.pm import pulse, config
   cfg = config.load_config()
   refs = json.load(open("/tmp/pm_commit_refs.json"))
   prior_projects = json.load(open("/tmp/pm_prior_projects.json"))
   prior_issues   = json.load(open("/tmp/pm_prior_issues.json"))
   dprojects = [pulse.normalize_project(p) for p in json.load(open("/tmp/pm_delta_projects_raw.json"))]
   dissues   = [pulse.normalize_issue(i)   for i in json.load(open("/tmp/pm_delta_issues_raw.json"))]
   ws = pulse.select_working_set(dprojects, dissues, prior_projects, prior_issues,
            commitment_project_ids=refs["project_ids"], commitment_issue_ids=refs["issue_ids"])
   brake = pulse.check_brake(ws["scope_counts"], cfg)
   MODE = os.environ.get("PM_RUN_MODE", "headless")   # interactive runs export PM_RUN_MODE=interactive
   proj, iss = ws["projects"], ws["issues"]
   if brake["tripped"]:
       if MODE == "interactive":
           print("BRAKE_TRIPPED_INTERACTIVE:", "; ".join(brake["reasons"])); sys.exit(3)
       # headless: auto-narrow to the active floor and flag for manual review
       floor = pulse.select_safe_floor(iss, now=date.today().isoformat(), config=cfg,
                                       commitment_issue_ids=refs["issue_ids"])
       keep_iids = {i["id"] for i in floor}
       keep_pids = {i.get("project_id") for i in floor} | set(refs["project_ids"])
       iss  = [i for i in iss if i["id"] in keep_iids]
       proj = [p for p in proj if p["id"] in keep_pids]
       print("BRAKE_TRIPPED_HEADLESS_NARROWED:", "; ".join(brake["reasons"]))
   json.dump({"project_ids": [p["id"] for p in proj], "issue_ids": [i["id"] for i in iss]}, open("/tmp/pm_working_ids.json","w"))
   json.dump({"scope_counts": ws["scope_counts"], "hygiene": ws["hygiene"], "brake": brake, "mode": MODE}, open("/tmp/pm_scope.json","w"))
   print("scope:", json.dumps(ws["scope_counts"]))
   print("hygiene:", json.dumps({k: v for k, v in ws["hygiene"].items() if k != "zombie_project_ids"}))
   PY
   ```
   - **Interactive trip** (`exit 3` / `BRAKE_TRIPPED_INTERACTIVE`): STOP. Do not fetch
     relations, do not write. Report the scope + reasons to Scott and ask whether to proceed
     or narrow. This is the only interactive halt.
   - **Headless trip** (`BRAKE_TRIPPED_HEADLESS_NARROWED`): the working set has been narrowed
     to the safe floor. Append a **loud flag** to `state/journal/ops-incidents.md` (severity
     `MED`, `PM_SCOPE_BRAKE`) with the reasons + counts, and a handoff to chief-of-staff:
     *"PM pulse scope brake tripped (N active-open issues) — ran the safe floor only; manual
     inspection + re-run needed."* Then continue with the narrowed set.
   - **No trip:** continue with the full working set.

4. **Blockers + owner-declared health (FETCH SUBAGENT → `/tmp`).** Select the blocker-fetch
   subset from the working issues, apply the runtime backstop, then spawn a subagent for the
   relation + status reads (again returning only counts):
   ```bash
   python3 - <<'PY'
   import json, sys; sys.path.insert(0, ".")
   from datetime import date
   from scripts.pm import pulse, config
   cfg = config.load_config()
   work = json.load(open("/tmp/pm_working_ids.json"))
   dissues = {i["id"]: i for i in (
       [pulse.normalize_issue(x) for x in json.load(open("/tmp/pm_delta_issues_raw.json"))])}
   # only working issues, only those open + active within the window
   work_issues = [dissues[i] for i in work["issue_ids"] if i in dissues]
   sel = pulse.issues_to_fetch_blockers(work_issues, now=date.today().isoformat())
   scope = json.load(open("/tmp/pm_scope.json"))
   refs = json.load(open("/tmp/pm_commit_refs.json"))
   brake2 = pulse.check_brake(scope["scope_counts"], cfg, relation_fetch_count=len(sel))
   if brake2["tripped"]:
       if scope["mode"] == "interactive":
           print("BRAKE_TRIPPED_INTERACTIVE_RELATIONS:", "; ".join(brake2["reasons"])); sys.exit(3)
       # headless: bound the relation loop to the active floor (do NOT fetch the full set) and flag
       floor = {i["id"] for i in pulse.select_safe_floor(work_issues, now=date.today().isoformat(),
                                                         config=cfg, commitment_issue_ids=refs["issue_ids"])}
       sel = [i for i in sel if i["id"] in floor]
       print("BRAKE_TRIPPED_HEADLESS_RELATIONS_NARROWED:", "; ".join(brake2["reasons"]))
   json.dump([i["id"] for i in sel], open("/tmp/pm_blocker_ids.json","w"))
   print("blocker fetch: %d issues; active projects: %d" % (len(sel), len(work["project_ids"])))
   PY
   ```
   Brief the subagent to:
   - For each id in `/tmp/pm_blocker_ids.json`: `get_issue(id, includeRelations=true)`;
     collect `blockedBy` target ids. Write `{issue_id: [blocker ids]}` to
     `/tmp/pm_issue_blockers.json` (omit issues with no blockers).
   - For each **active** project id in `/tmp/pm_working_ids.json`:
     `get_status_updates(type="project", project=<id>)`; keep the latest update's `health`
     enum. Write `{project_id: enum}` to `/tmp/pm_status_health.json`.
   - Return `{blockers: b, status: s}` counts only.
   (Runtime backstop: on a headless relation-fetch trip that Step 3's issue/project ceilings
   didn't already catch — e.g. relation count in the band above `brake_max_relation_fetches`
   but active-open issues under `brake_max_issues` — `sel` is narrowed to the safe floor
   above; file the same `PM_SCOPE_BRAKE` incident + chief-of-staff handoff as Step 3 and log the
   relation count in the journal.)

5. **Compute + write (single deterministic heredoc, main agent).** Re-derive the working set
   deterministically, restrict it to the Step-3 ids (so a headless narrowing is honored), and
   run the compute:
   ```bash
   python3 - <<'PY'
   import json, sys
   sys.path.insert(0, ".")   # run from repo root so scripts.pm imports resolve
   from datetime import datetime, timezone
   from scripts.pm import pulse, db, config
   cfg = config.load_config()
   now = datetime.now(timezone.utc); created = now.strftime("%Y-%m-%dT%H:%M:%SZ")
   refs = json.load(open("/tmp/pm_commit_refs.json"))
   prior_projects = json.load(open("/tmp/pm_prior_projects.json"))
   prior_issues   = json.load(open("/tmp/pm_prior_issues.json"))
   prior_blockers = json.load(open("/tmp/pm_prior_blockers.json"))
   prior_missed   = set(json.load(open("/tmp/pm_prior_missed_ids.json")))
   dprojects = [pulse.normalize_project(p) for p in json.load(open("/tmp/pm_delta_projects_raw.json"))]
   dissues   = [pulse.normalize_issue(i)   for i in json.load(open("/tmp/pm_delta_issues_raw.json"))]
   ws = pulse.select_working_set(dprojects, dissues, prior_projects, prior_issues,
            commitment_project_ids=refs["project_ids"], commitment_issue_ids=refs["issue_ids"])
   keep = json.load(open("/tmp/pm_working_ids.json"))
   kp, ki = set(keep["project_ids"]), set(keep["issue_ids"])
   projects = [p for p in ws["projects"] if p["id"] in kp]
   issues   = [i for i in ws["issues"]   if i["id"] in ki]
   res = pulse.compute_pulse(
       projects=projects, issues=issues,
       issue_blockers=json.load(open("/tmp/pm_issue_blockers.json")),
       status_health=json.load(open("/tmp/pm_status_health.json")),
       prior_projects=prior_projects, prior_issues=prior_issues, prior_blockers=prior_blockers,
       prior_missed_ids=prior_missed, config=cfg,
       now=now.date().isoformat(), created_at=created)
   c = db.connect()
   for r in res["project_rows"]: db.upsert(c, "pm_projects", r, key_cols=["id"])
   for r in res["issue_rows"]:   db.upsert(c, "pm_issues",   r, key_cols=["id"])
   for r in res["blocker_opens"]: db.insert(c, "pm_blockers", r)
   for r in res["blocker_resolves"]:
       c.execute("UPDATE pm_blockers SET resolved_at=? WHERE id=?", (r["resolved_at"], r["id"]))
   for r in res["missed"]:        db.insert(c, "pm_missed_deadlines", r)
   c.commit(); c.close()
   out = {**res["summary"], "hygiene": ws["hygiene"], "scope_counts": ws["scope_counts"]}
   json.dump(out, open("/tmp/pm_pulse_out.json","w"), indent=2)
   print(json.dumps({k: out[k] for k in ("projects","issues","orphans","blocker_opens","blocker_resolves","missed")}))
   PY
   ```
   Only the working-set rows are upserted; the frozen (terminal / stale-zombie) rows are
   left untouched in the DB.

6. **Zero Linear writes.** Confirm no `save_*`/`update_*` Linear tool was called this run (by
   this agent or any subagent).

7. **C2 — missed deadlines.** For each new `missed` row:
   - **Cycle 1 (`accountability_mode == state_only`):** do NOT DM; leave `prompted_at` NULL and
     mark the project for the Thursday agenda.
   - Otherwise: one DM to the owner (quiet-hours-aware), stamp `prompted_at`. Message names the
     project, the missed date, and the 48h ask for a one-paragraph Linear comment.
   For prior unresolved missed rows inside their 48h window: `list_comments(projectId=...)`,
   find the owner's explanation comment → stamp `acknowledged_at` + `explanation` +
   `linear_comment_link`. If 48h have lapsed with no comment → set `surfaced_in_thursday=1`.

8. **State-change DMs.** Consume `summary` / `dm_events` — **empty in cycle 1** (gated). When
   live: ≤1 DM per person per worsening transition (G→Y, Y→R, orphan active→stale/blocked),
   quiet-hours-aware.

9. **Journal.** Append one entry to `state/journal/scribe_project_management.md`:
   `## <ISO> | Pulse — N projects, M issues (K orphans), {blocker opens/resolves}, {missed}`,
   plus:
   - **The scope line:** active-window (`scope_window_days`), the `scope_counts`
     (active-open issues, active projects, commitment refs pinned in), and whether the
     **brake** tripped (+ narrowed) this run.
   - **The hygiene tally:** `stale_open_issues`, `zombie_projects` (`empty_zombie_projects`) —
     frozen out of the pulse, standing Thursday-agenda talking points.
   - The **owner-vs-agent health discrepancies** (`summary.health_discrepancies`).
   - Any **external-owner hints to {{HEAD_OF_MARKETING_FIRST}}** (`owner_source == external_default`).
   **Apply the Linear pre-send link gate** (every project name / issue key rendered as a
   clickable link — `docs/linear-reference-formatting.md`).

10. **Commit** all `state/` changes with the `state-bot` identity:
    `[state-bot] Scribe | Skill: linear-pulse-check | <ISO UTC>`. Push. (A `state/` data commit;
    the PM pre-commit gate does not fire on it.)

## Acceptance

- Runs Tue–Fri; **read-only on Linear** (no writes, main agent or subagents).
- **Bounded, uniform fetch every run:** only work active in Linear (`updatedAt`) within
  `scope_window_days`, plus open-commitment referents. No full-universe re-pull, no
  Friday special case. Terminal + stale-zombie items are frozen (kept in the DB, counted
  in the hygiene tally, never re-fetched/recomputed/re-upserted).
- **Context-flat:** all bulk MCP reads happen in a fetch subagent that writes `/tmp` and
  returns counts; the main agent holds only the deterministic Python.
- **Brake:** `check_brake` trips over the configured ceilings; headless auto-narrows to
  `select_safe_floor` + files a `PM_SCOPE_BRAKE` incident + chief-of-staff handoff; interactive
  stops and asks. Never spins, never silently no-ops.
- Scope-selection / brake / safe-floor are deterministic (golden-gated in
  `tests/pm/test_pulse.py`: `select_working_set`, `check_brake`, `select_safe_floor`);
  health remains golden-gated (`compute_pulse`).
- Orphans tracked in `pm_issues`; blocked = open `blockedBy` relation.
- A project past its immutable `original_due_date` and not closed lands `off_track` + a single
  `pm_missed_deadlines` seed row (never re-seeded). Overdue projects that have gone stale
  beyond the window are surfaced via the hygiene tally, not re-swept.
- External-led projects resolve `owner` to the configured `default_external_owner` ({{HEAD_OF_MARKETING_FIRST}}) with
  `owner_source='external_default'` and a Thursday hint.
- No DMs in cycle 1 (`state_only`); `dm_events` empty.
