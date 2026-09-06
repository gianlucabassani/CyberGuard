# Agent continuity — Nidavellir

Before making material changes, read these sources in order:

1. `README.md` — product purpose: enterprise cyber arena for testing skills
   and AI agents; provisions N-node topologies, exposed via MCP gateways to
   bring-your-own agents as attacker/MITM/defender.
2. `ROADMAP.md` — authoritative sequenced plan, "Where the project stands",
   audit punch list (mostly fixed), and the two structural limits still open:
   (1) deploy path still tied to a frozen 3-VM OpenStack template instead of
   arbitrary N-node topologies; (2) the agent runtime (MCP gateways, stances)
   doesn't exist yet — that's the core of the product and isn't built.
3. `.lab.yaml` — quick commands (`docker compose up -d`, `pytest tests/`) and
   milestone checklist (kept in sync manually — cross-check against ROADMAP).
4. `git log` — only when the above are silent on something recent.

## Stack / gotchas

- Stack: Python, FastAPI, Celery, MCP, Docker, OpenStack, AWS.
- Provider abstraction (ADR-0003): `mock`, `docker-local`, `libvirt`,
  `openstack` — per-request provider selection, per-arena workspace isolation.
- PostgreSQL + SQLAlchemy + Alembic (ADR-0004), explicit lab state machine,
  append-only `events` audit table, TTL/stuck reaper.
- `MOCK_MODE` makes the full flow demoable/testable without cloud cost —
  use it before reaching for real OpenStack/AWS provisioning.
- `make check` runs ruff + bandit + pytest; CI runs the suite on SQLite and
  Postgres — run it before claiming anything "done."
- Guiding principle: **correctness and security before features** — the
  platform turns input into real infrastructure and gives agents command
  execution inside it. Treat any shortcut here as a regression, not a detail.
- Repo was last committed ~10 weeks ago (as of this file's creation) — verify
  current state against ROADMAP before assuming any punch-list item's status.

## Shared knowledge base

`~/Documents/NOTES` (curated by the `dante` profile) is the reference CS/
CyberSec knowledge base — read for context (e.g. prior notes on a relevant
attack surface or tool) when useful. Never write there; that's dante's job.

## Coding delegation

`nidavellirManager` tracks state, TODOs, and roadmap sequencing. It does not
write implementation code itself — for actual coding work, spawn Claude Code
from a terminal rooted at `~/Projects/Nidavellir` with a concrete, scoped
task description referencing the exact ROADMAP/ADR item.

## Reporting

Use the `project-status-report` skill for scheduled/on-demand status reports.

**Proactive reporting rule:** when a concrete deliverable lands outside a
scheduled report slot (a roadmap item completed, an ADR decision made),
report it immediately in the same format rather than waiting for the next
scheduled run — this rule lives here, not only in a chat conversation.
