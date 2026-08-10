# Overview

> Nidavellir is a **GUI-driven, bring-your-own-agent cyber evaluation arena for
> active challenges**. It provisions reproducible targets, gives a human or
> external agent a contained research position, independently verifies observed
> effects, and produces scored, replayable, auditable results.

Nidavellir ships no autonomous pentesting agent. The participant is the system
under test; Nidavellir is the environment factory, capability boundary,
observer, referee, and comparison layer. For agent connection details see
[`MCP.md`](./MCP.md); for the product boundary see [`VISION.md`](./VISION.md);
for subsystem internals see
[`INTERNALS.md`](./INTERNALS.md); for the product sequence see
[`../ROADMAP.md`](../ROADMAP.md).

---

## What it evaluates

The unit under test is a **complete agent build**: model, scaffold, prompts,
tools, memory, policies, budgets, and version together. A model-only score is not
enough to explain whether an internal security agent improved.

The primary task is an **active challenge**: a real running application or
topology that responds to participant actions and may move through controlled
releases. This supports both one-shot offensive agents and continuous agents
that must notice a new component, avoid retesting unchanged surfaces, close a
fixed finding, and rediscover a regression.

Public CTF/CVE packs remain useful for calibration. Held-out/private challenges,
immutable identities, repeated trials, and independent validators are required
for a defensible comparison.

## Two operator journeys

- **Engagement:** one human or agent researches one challenge or ad-hoc target.
- **Evaluation:** pinned agent builds run repeated trials over a challenge suite
  and are compared on verified capability, regressions, latency, cost, and safety.

Both journeys use the same arena, gateway, event, evidence, validation, and
scoring engine.

## Product model

```text
Target + Scenario + truth/validators/episode
                 ↓
              Challenge ───────────────┐
                 │                     │
          Engagement              Evaluation
                 │            agent builds × suite × trials
                 │                     │
                 └──────────┬──────────┘
                            ↓
                         Run/Arena
                            ↓
             findings · evidence · trace · score
```

- A **Target** is an immutable Git object, OCI digest, source bundle, package,
  or future binary/VM identity.
- A **Scenario** is the provider-neutral topology specification.
- A **Challenge** adds participant instructions, visibility, truth/objectives,
  validators, and an optional staged episode.
- An **Arena** is temporary live infrastructure; durable engagement/run records
  and evidence survive its destruction.

---

## The engine pipeline

```text
Operator console
      │
      ├── choose/ingest target + challenge
      ├── review identity, setup, containment and limits
      ▼
Orchestrator ──tasks──▶ Worker ──provider──▶ isolated running arena
      │                                           │
      │ bind human/agent stance                   │ observed effects
      ▼                                           ▼
MCP gateway / external driver              monitor + validators
      │                                           │
      └──────── actions/findings/evidence ────────┘
                            │
                            ▼
                  events + trace + Score
                            │
                            ▼
                 run export / comparison
```

### Provisioning and target identity

- Scenario schema v3 defines arbitrary nodes and network segments.
- Docker-local creates per-arena networks and real containers.
- SUT targets can originate from pinned Git, digest-pinned public OCI images,
  or bounded local source bundles.
- Existing Dockerfiles are preferred; verified synthesis and package tiers fill
  gaps. Setup can be operator-scripted, HITL, or double-locked autonomous.

### Agent boundary

- Server-enforced key↔arena bindings and stance-scoped MCP tools.
- Attacker, MITM, defender, and special configurator capabilities.
- Provider-enforced containment, command limits, and append-only traces.
- Generic drivers for persistent/container/external agents are planned for the
  evaluation workbench; product-specific agent logic does not enter Nidavellir.

### Evidence and scoring

- Monitor signals cover crashes, sanitizer aborts, OOM/resource faults, and
  unhandled 5xx behavior.
- Deterministic validators prove effects such as observed XSS execution, marker
  disclosure, OAST callbacks, or correlated crashes.
- Verdicts are tri-state: confirmed, refuted, or unknown. Only confirmed earns
  credit; unknown is never silently converted into refuted.
- Benchmark mode scores against hidden truth. Discovery mode reports confirmed
  findings and fault sites without pretending that unknowable false negatives
  are zero.
- Structured scores, OpenInference-aligned traces, dataset export, and replay
  are already shipped.

---

## Console direction

The current console grew around implementation increments—Dashboard, Arenas,
Launch, SUT, Inventory, Logs, and Agents. Before adding suites, trials, and
comparisons, it is being reorganized around operator intent:

```text
Home
Engagements
Evaluations
Library → Challenges · Targets · Agents
Activity → Findings · Evidence · Audit trail
Administration
```

Launch and SUT become one contextual New Engagement wizard. The large arena page
becomes a shared engagement/run workspace:

```text
Overview · Live · Target · Findings · Evidence · Changes
Agent · Trace · Score · Infrastructure
```

The migration preserves existing backend flows and routes until replacements
reach feature parity. See [ADR-0012](./adr/0012-gui-first-product-model.md).

---

## Current status

- **Shipped:** dynamic Docker arenas, SUT provisioning, secure target intake,
  setup gates, monitoring, validators, structured scoring, findings/PoCs,
  eval export, reference harness, batch execution, replay, Git evidence,
  file transfer, and target-scoped browser tooling.
- **Next:** console information architecture, unified engagement creation, and
  contextual engagement/run workspace.
- **Then:** HTTP replay/modify, confined PoC sandbox, tunnelling, durable budgets
  and kill switches; followed by the GUI evaluation workbench.
- **Evaluation gap:** durable Agent build/Suite/Evaluation/Run/Trial records,
  active episode schedules, and paired N-vs-N+1 comparison do not exist yet.
- **Provider boundary:** Docker-local is mature. OpenStack, AWS, and libvirt are
  validation-level skeletons with no supported live apply.
- **Security boundary:** this remains a trusted-host/single-team system and is
  not safe to expose directly to an untrusted network; see
  [`SECURITY.md`](./SECURITY.md).
- **Verification:** the declared Python 3.11 container gate records 771 passing
  tests with Ruff and Bandit clean. Host Python 3.13 currently hangs in
  Starlette `TestClient` and is not the supported full-test path.
