<p align="center">
  <img src="docs/assets/logo.svg" alt="Nidavellir — Agentic Arena Forge" width="620">
</p>

<p align="center">
  <b>A GUI-driven cyber evaluation arena for active challenges.</b><br>
  Provision reproducible targets, connect a bring-your-own security agent, independently verify
  what it achieves, and compare complete agent builds through scored, replayable runs.
</p>

<p align="center">
  <a href="https://gianlucabassani.github.io/Nidavellir"><strong>Explore the Live Website & Interactive Docs »</strong></a>
</p>

<p align="center">
  <a href="https://gianlucabassani.github.io/Nidavellir"><img src="https://img.shields.io/badge/website-live-F5A524"></a>
  <img src="https://img.shields.io/badge/status-active_development-F5A524">
  <img src="https://img.shields.io/badge/stack-Python_·_FastAPI_·_Celery_·_MCP-3D9BFF">
  <img src="https://img.shields.io/badge/providers-docker--local_·_OpenStack_·_AWS-34D399">
  <img src="https://img.shields.io/badge/license-MIT-8A93A8">
</p>

---

Humans author and run engagements and evaluations; **the AI is the system under test**.
Nidavellir is the environment, capability boundary, observer, referee, and comparison layer—not
the pentesting agent. Interactive agents connect through scoped MCP gateways; persistent or
external agents will use the same evidence/scoring boundary through generic drivers. The mature
execution path runs locally with Docker.

> **AI-centered, never AI-required.** Built for testing AI agents and MCP-compliant throughout,
> but every arena stays fully drivable by a human pentester with no model in the loop.

## The console

<p align="center"><img src="docs/assets/dashboard.png" alt="Nidavellir dashboard — fleet, host capacity, live activity" width="900"></p>

A mission-control dashboard currently exposes live arenas, host capacity, and a source-split
activity stream (agent / human / system). The console is being reorganized around two durable
operator journeys—**Engagements** and **Evaluations**—plus a reusable Library and global Activity
views. Existing functions remain available during the migration. The current **Inventory** shows
scenario packs and live topology previews:

<p align="center"><img src="docs/assets/inventory.png" alt="Nidavellir inventory — scenario packs with machine line-ups + topology" width="900"></p>

The **Arena View** gives operators full live-control over active topologies:

<p align="center"><img src="docs/assets/arena.png" alt="Inside Arena View — instance control and network segments" width="900"></p>

## Three pillars

1. **Dynamic N-node topologies** (GOAD-inspired). A scenario is a provider-agnostic, data-defined
   topology — arbitrary `nodes[]` + network `segments[]`, not a frozen trio. One spec compiles to
   docker-local containers, OpenStack VMs, or AWS. Ships as **arena packs** with variants.
2. **Agent runtime via MCP gateways**. A BYO agent connects through a gateway
   that wires it into a running arena as **attacker** (offensive foothold, scored), **MITM**
   (in-path on a shared segment), or **defender** (blue: events, alerts, response) — with scope
   enforcement, guardrails, budgets, and traces. Reproducible single-agent runs are the current
   requirement; multi-agent red-vs-blue is deferred.
3. **Zero-to-prompt scenario generation** (BYO key). An LLM turns a brief into a topology spec;
   Nidavellir **validates** it against the schema and **compiles** it — never auto-deploying
   unreviewed infra.

The data model scales to new arena *kinds* cheaply — AD labs, service meshes, CTF web apps,
LLM-app targets, and **software-under-test (SUT) arenas**: point Nidavellir at any open-source
project and have a BYO agent pentest it, white- or black-box, deeply monitored and scored.

## Quick start

No cloud account needed — the dev stack runs everything in Docker, mock mode pinned:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
# Console: http://localhost:5000   (login: admin / nidavellir)
# API:     http://localhost:8000   (header: X-API-Key: dev-insecure-key)
```

To run **real container arenas** on the local Docker daemon, set `RANGE_PROVIDER=docker-local`
and `MOCK_MODE=false` on the worker (see `docker-compose.dev.yml`). For OpenStack/AWS, configure
the provider credentials and flip `MOCK_MODE=false`.

Import a ready-to-run target from [Vulhub](https://github.com/vulhub/vulhub) (container CVE
environments) in one call:

```bash
curl -sX POST localhost:8000/scenarios/import/vulhub -H "X-API-Key: dev-insecure-key" \
  -H 'Content-Type: application/json' -d '{"path":"log4j/CVE-2021-44228"}'
```

## Architecture

```
┌────────────┐   HTTP    ┌──────────────┐   tasks    ┌─────────────┐   provider   ┌──────────────┐
│  Console   │ ───────▶ │ Orchestrator │ ───────▶  │   Worker    │ ──────────▶ │ docker-local │
│  (Flask)   │ ◀─────── │ (FastAPI)    │ ◀── Redis │  (Celery)   │   drivers    │ OpenStack/AWS│
└────────────┘           └──────┬───────┘            └─────────────┘              └──────────────┘
       ▲                        │ append-only events · API-key auth · Fernet-at-rest
       │ MCP gateway            ▼
  BYO agent  ─────────▶  attacker / MITM / defender stances  ·  scope · guardrails · budgets · trace
```

- **Console** (Flask + Jinja) — fleet, launch, inventory, logs, agents, configurator, co-pilot.
- **Orchestrator** (FastAPI) — `/deploy`, `/scenarios`, `/exec`, scoring; API-key auth (ADR-0002),
  append-only `events` audit table, Fernet-encrypted outputs at rest.
- **Worker** (Celery + Redis) → **provider drivers** (`mock`, `docker-local`, `openstack`, `aws`).
- **MCP agent gateway** — the BYO-AI seam; stance-scoped toolset + guardrails + JSONL trace.

## Roadmap

The provisioning→monitoring→validation→score→eval-export engine is shipped. The roadmap was
reorganized on 2026-08-10 because the next constraint is product coherence: adding agent builds,
suites, trials, and comparisons to the current Launch/SUT/Arenas navigation would make the GUI
harder to use. The console information architecture therefore lands before the evaluation
workbench. Full detail is in [`ROADMAP.md`](ROADMAP.md).

| Stage | Focus | Status |
|---|---|---|
| **Shipped engine** | Dynamic arenas, target intake, repo→service, monitoring, validators, scoring, eval export and replay | ✅ shipped |
| **Research session** | Change evidence, file transfer, browser; proxy/sandbox/tunnel/durable guardrails remain | 🟢 partially shipped |
| **Console architecture** | Engagements, Evaluations, Library, Activity, unified creation and contextual run workspace | 🟡 **next** |
| **Research-ready runtime** | HTTP replay, confined PoC execution, tunnelling, fail-closed budgets and kill switches | ◻ planned after console foundation |
| **Evaluation workbench** | Agent registry, suites, trials, active episodes and GUI comparison of build N vs N+1 | ◻ planned |
| **Held-out proof** | Repeated private challenge suite and recorded comparison workflow | ◻ planned |
| **Deferred** | OAuth/multi-tenancy, live cloud/VM providers, purple-team, VNC and hosted-product concerns | ◻ deferred |

## Documentation

Visit the **[Nidavellir Live Website & Interactive Docs](https://gianlucabassani.github.io/Nidavellir)** to browse the codebase documentation in a clean, interactive single-page app.

Individual markdown documents:
- [`docs/VISION.md`](docs/VISION.md) — product purpose, scope and language
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — detailed setup & operations
- [`docs/API.md`](docs/API.md) — orchestrator REST API
- [`docs/SCENARIOS.md`](docs/SCENARIOS.md) — the v3 scenario schema + Vulhub import
- [`docs/SECURITY.md`](docs/SECURITY.md) — threat model & containment
- [`docs/adr/`](docs/adr/) — architecture decision records
- [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`ROADMAP.md`](ROADMAP.md)

## License

MIT.
