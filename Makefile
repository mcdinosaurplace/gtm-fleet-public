# gtm-agent-fleet — common tasks. `make help` lists them.
PY      ?= python3.12
VENV    := .venv
PYTHON  := $(VENV)/bin/python
PROFILE ?= orrery
TERMS   ?= ../private/terms.source.yaml
# tier-2: vocabulary allowed in this repo's history but never in its tree / renders / kits
TERMS2  ?= ../private/terms.tier2.yaml
CLAUDE  ?= $(shell command -v claude 2>/dev/null || echo $$HOME/.local/bin/claude)

.PHONY: help setup seed test verify render compose claude demo demo-reset demo-run demo-run-paid demo-run-content validate schedule clean

help:
	@echo "setup       create $(VENV) and install requirements"
	@echo "seed        rebuild state/ with synthetic demo data (PROFILE=$(PROFILE))"
	@echo "test        run the full pytest suite"
	@echo "verify      zero-leak gate; needs TERMS=<private terms yaml> (refuses to run without it)"
	@echo "            adds a tree-only TERMS2 run (--skip-history) and gates build/$(PROFILE) strictly when they exist"
	@echo "render      render the tokenized kit for PROFILE into build/$(PROFILE)/"
	@echo "compose     compose a client fleet from FLEET=<fleet.yaml> (gate runs per terms file that exists: TERMS, TERMS2)"
	@echo "validate    claude plugin validate ."
	@echo "claude      open Claude Code here with the plugin loaded"
	@echo "demo-reset  seed as of yesterday, empty the demo outbox, render the fixture MCP config"
	@echo "demo-run    demo-reset, then the three hero ticks headless: revops-watchdog -> chief-of-staff -> Scribe"
	@echo "demo-run-paid     the paid loop headless (run after demo-run or demo-reset; no reset of its own)"
	@echo "demo-run-content  the content engine headless (run after demo-run or demo-reset; no reset of its own)"
	@echo "demo        demo-reset, then open Claude Code with the fixture connectors bound"
	@echo "schedule    print the (disabled) crontab rendering of schedule.yaml"

setup:
	test -d $(VENV) || $(PY) -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r scripts/requirements.txt -r scripts/pm/requirements.txt pytest
	@$(PYTHON) scripts/fleet_paths.py --check || true

seed:
	$(PYTHON) scripts/seed_demo_state.py --profile $(PROFILE) --as-of $$(date +%F) --force

test:
	$(PYTHON) -m pytest

verify:
	@test -f "$(TERMS)" || { echo "verify: private terms file not found: $(TERMS) (set TERMS=…)"; exit 1; }
	$(PYTHON) scripts/sanitize/verify.py --root . --terms "$(TERMS)"
	@test ! -f "$(TERMS2)" || $(PYTHON) scripts/sanitize/verify.py --root . --terms "$(TERMS2)" --skip-history
	@# build/$(PROFILE), when it has been rendered: strict — a finding fails make.
	@# --skip-history is a no-op there (no .git in a build dir); passed for symmetry with the tree runs.
	@test ! -d build/$(PROFILE) || $(PYTHON) scripts/sanitize/verify.py --root build/$(PROFILE) --terms "$(TERMS)" --skip-history
	@test ! -d build/$(PROFILE) || test ! -f "$(TERMS2)" || $(PYTHON) scripts/sanitize/verify.py --root build/$(PROFILE) --terms "$(TERMS2)" --skip-history

render:
	$(PYTHON) scripts/profile_render.py --profile $(PROFILE)

FLEET ?= fleet.yaml
compose:
	$(PYTHON) scripts/compose_fleet.py --fleet $(FLEET) $(if $(wildcard $(TERMS)),--terms "$(TERMS)") $(if $(wildcard $(TERMS2)),--terms2 "$(TERMS2)")

validate:
	$(CLAUDE) plugin validate .

claude:
	$(CLAUDE) --plugin-dir .

# --- DEMO_MODE: the hero loop with no credentials (docs/demo-runbook.md) ---
# Seeded as of yesterday so the planted SAL->SQL dip is already three ticks old and today
# is still unwritten. The fixture servers in mcp/demo.json serve every connector read;
# Slack and Notion writes land in state/demo-outbox/.
demo-reset:
	$(PYTHON) scripts/seed_demo_state.py --profile $(PROFILE) --as-of yesterday --force
	$(PYTHON) scripts/demo/render_config.py

demo-run: demo-reset
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent revops-watchdog --mode daily --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent chief-of-staff --mode am --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent scribe --mode weekly --runner claude

# Optional second and third acts (docs/demo-runbook.md §3–4). Deliberately no
# demo-reset here: run them on the same seeded day as demo-run, in order.
demo-run-paid:
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent performance-marketer --mode daily --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent performance-marketer --mode weekly --runner claude

demo-run-content:
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent content-researcher --mode weekly --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent scribe --mode notion-topic-sync --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent content-producer --mode daily --runner claude
	DEMO_MODE=1 $(PYTHON) scripts/tick.py --agent brand-designer --mode queue --runner claude

demo: demo-reset
	DEMO_MODE=1 $(CLAUDE) --plugin-dir . --mcp-config state/working/demo-mcp.resolved.json

schedule:
	$(PYTHON) scripts/schedule_render.py --format crontab

clean:
	rm -rf build .pytest_cache $$(find . -name __pycache__ -not -path './.venv/*')
