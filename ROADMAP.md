# Roadmap

> **North star:** Nidavellir is the GUI-driven, bring-your-own-agent cyber
> evaluation arena for active challenges. It provisions a reproducible target,
> gives a human or agent a contained research position, observes what really
> happened, verifies evidence, and turns the session into a replayable result.
>
> The AI is the system under test. Nidavellir is the environment, capability
> boundary, observer, referee, and comparison layer.

This roadmap was reorganized on 2026-08-10 after the provisioning, scoring,
eval-export, target-intake, evidence, file-transfer, and browser slices had
landed. The next constraint is no longer a missing backend primitive: the
console has accumulated many independently useful functions without a durable
product information architecture. Adding suites, trials, agent builds, and
comparisons to the current navigation would make that problem worse.

The sequence is therefore:

1. preserve the shipped engine;
2. establish a coherent GUI product model and migrate existing workflows into it;
3. finish the agent-grade research runtime inside that structure;
4. build GUI-driven agent regression evaluation;
5. publish the held-out proof.

Correctness, containment, and independent verification remain ahead of feature
count. The authoritative product boundary is
[`docs/VISION.md`](docs/VISION.md). Architecture
decisions live in [`docs/adr/`](docs/adr/).

---

## 1. Product definition

Nidavellir evaluates **complete agents**, not only models. A result identifies
the model, scaffold, tools, budgets, target, starting state, and evidence. The
primary benchmark is an **active challenge**: a real running system whose state
and responses change as the participant acts. Static CTFs and known-CVE packs
remain useful calibration lanes, but they are not the whole product.

Nidavellir supports two first-class operator journeys:

- **Engagement:** one human or agent performs security research in one active
  arena. The operator configures the target, observes work, and reviews evidence.
- **Evaluation:** one or more pinned agent builds run repeated trials over a
  challenge suite. Nidavellir compares verified capability, regressions, cost,
  latency, and safety.

Both journeys reuse the same arena, gateway, event, evidence, validation, and
scoring substrate. Evaluation is not a second engine layered beside engagements.

### Product objects and relationships

| Object | Meaning |
|---|---|
| **Target** | An immutable Git object, OCI digest, source bundle, package, or future VM/binary identity. |
| **Scenario** | The provider-agnostic topology specification (`nodes[]`, `segments[]`, services, stances). This remains the engine term. |
| **Challenge** | A scenario plus target identity, participant brief, visibility policy, objectives/hidden truth, validators, and optionally a staged episode. |
| **Agent build** | A pinned external system under test: identity, version/digest, driver, model/scaffold metadata, and default limits. |
| **Engagement** | One operator-led research session against one challenge or ad-hoc target. |
| **Evaluation** | A configured experiment: agent builds × challenge suite × trials × budgets. |
| **Run** | One agent build on one challenge for one trial/seed. |
| **Arena** | The live infrastructure allocated to an engagement or run. It is an execution resource, not the top-level product workflow. |
| **Evidence** | Findings, PoCs, monitor signals, files, patches, traces, and validator verdicts tied to immutable identities. |

The existing code/database terms `deployment` and `lab` may remain internally
until migrated safely. New operator-facing prose uses the glossary above.

---

## 2. Current status — shipped engine

### S1 — Control plane and dynamic arenas · shipped

- FastAPI orchestrator ↔ Redis/Celery worker ↔ provider drivers.
- PostgreSQL/SQLAlchemy/Alembic, explicit arena state machine, append-only events,
  TTL/stuck reaper, log redaction, and optional Fernet encryption at rest.
- Scenario schema v3 with arbitrary nodes/segments and a Docker-local compiler.
- API-key roles, CSRF, rate limits, input validation, and server-enforced
  key↔arena stance bindings.
- Mature `docker-local` path; `mock` for tests/demo. OpenStack, AWS, and libvirt
  remain non-live skeletons and are deliberately deferred.

### S2 — Target → running service · shipped (legacy M1)

- Repository introspection and deterministic Dockerfile build path.
- Verified LLM Dockerfile synthesis fallback and `service.package` install.
- Git target resolution to immutable object IDs.
- Public OCI tag resolution to digest-pinned references.
- Bounded local tar/tar.gz intake with canonical hashes and safe materialization.
- SUT setup modes: operator-scripted, HITL, and double-locked autonomous
  configurator; white-box source access separated from the target runtime.

Remaining breadth—not a blocker for the present product sequence: execute
Compose/devcontainer/buildpack tiers; binary/installer and VM-image intake.

### S3 — Observation, validation, scoring, and eval export · shipped (legacy M2–M3)

- Crash/sanitizer/5xx/resource monitor and deduplicated evidence signals.
- Deterministic validators, including observed browser execution for reflected XSS.
- Structured Inspect-style `Score`, benchmark/discovery modes, and milestone
  progress for incomplete runs.
- Reproducible PoCs and operator confirm/refute workflow.
- OpenInference/OTel-aligned traces and eval dataset rows.
- Reference MCP harness, concurrency-capped suites, and deterministic transcript
  replay.

The engine can score and export a run today. It does not yet have durable
evaluation/suite/trial records or paired agent-version comparisons.

### S4 — Research session and attacker tooling · partially shipped (legacy M4)

Shipped:

- authorization/scope declarations and fail-closed target preflight;
- Git change intelligence for staged, unstaged, and selected untracked files;
- SHA-256 patch evidence artifacts attachable to findings;
- bounded foothold upload/download with body-free audit metadata;
- target-scoped disposable headless browser shared with the XSS validator.

Still required:

- structured HTTP inspect/replay/modify proxy;
- confined Python/PoC sandbox through a worker-owned isolation boundary;
- foothold-scoped SSH tunnel lifecycle;
- durable fail-closed step/time/token/cost budgets;
- arena and system kill switches that drain or stop work predictably;
- before/after manifests for non-Git/binary targets.

### Verified health boundary

- Python 3.11 is the declared CI/runtime line; the last full container gate
  recorded 771 passing tests, Ruff clean, and no medium/high Bandit findings.
- Host Python 3.13 currently hangs in Starlette `TestClient`, including a minimal
  FastAPI reproduction. Do not describe a host-3.13 run as green; use the declared
  Python 3.11 gate until compatibility is deliberately added.
- Docker-local is the only provider whose complete lifecycle is regularly
  live-verified.

---

## 3. Console product architecture — next milestone

### C1 — Information architecture and application shell · **COMPLETE**

**Goal.** Give every shipped and planned function one predictable home before
adding evaluation features. This is a workflow reorganization, not a visual-only
redesign and not a backend rewrite.

The primary console navigation becomes:

```text
Home

Engagements
  Active
  History
  New engagement

Evaluations
  Suites
  Runs
  Comparisons
  New evaluation

Library
  Challenges
  Targets
  Agents

Activity
  Findings
  Evidence
  Audit trail

Administration
  Providers & capacity
  Security
  Settings
```

**Migration mapping.** Existing functions are preserved while routes/templates
move incrementally:

| Current surface | Destination |
|---|---|
| Dashboard | Home, redesigned last from the new objects |
| Arenas | Engagements; arena lifecycle remains visible inside an engagement/run |
| Launch + SUT wizard | Global Create → New engagement |
| Inventory / scenarios | Library → Challenges |
| Git/OCI/bundle intake | Library → Targets and the engagement wizard |
| Agents live-connections page | Run/engagement Agent tab; Library → Agents becomes the build registry |
| Logs | Activity → Audit trail |
| Findings/evidence/change cards | Activity indexes plus contextual run/engagement tabs |
| Settings/profile/model connection | Administration/Account |

**Application-shell work.** Establish grouped navigation, breadcrumbs, a global
Create action, consistent page headers, filters, tables, statuses, empty states,
and responsive behavior. Existing routes may remain as aliases during migration.

**Shipped first slice (2026-08-10).** The Flask console now has collapsible
Engagements, Evaluations, Library, Activity, and Administration groups; a global
Create menu routes operators into the existing challenge- and target-based
engagement flows. Target-language routes coexist with the legacy URLs, and
honest foundation pages reserve planned destinations without pretending their
data models exist. Page titles and breadcrumbs now use the target vocabulary.
The responsive shell now shares one compact-navigation breakpoint, provides a
mobile dismissal layer and keyboard dismissal, and exposes its state to
assistive technology. Filterable indexes share the same toolbar pattern.
Automated route/render coverage is green. Live-browser visual verification and
the final shell review are still required before C1 is complete.

**Completion (2026-08-18).** The shell was reviewed in a real browser against the
running compose stack. Twenty-three destinations — Home, both engagement pages,
the evaluation and library and activity and administration destinations, the
arena workspace, and every legacy alias — were walked at 1440×900 and 390×844.
Each renders with a breadcrumb, exactly one current navigation item, no
horizontal overflow at compact width, and no page-level console error or failed
request. The review found and fixed two real defects: the New engagement steps
rendered 1 → 3 → 4 → 2 because the participant/policy slice was inserted above
the source step, and `/launch` and `/wizard` opened the Engagements group without
marking any item current. Both are now covered by regression tests, and the
console serves its own `favicon.ico` instead of 404ing. The remaining 404 on an
arena's research preflight is correct: a challenge-based arena has none, and the
card hides itself.

**Acceptance.** A clickable, realistic prototype and route map cover Home,
Engagements, Evaluations, Library, Activity, Administration, and the workspace
below. An operator can locate every existing function; no shipped capability is
orphaned or duplicated. → ADR-0012.

### C2 — Unified engagement creation · **COMPLETE**

Replace separate Launch/SUT mental models with one GUI wizard composed from
shared steps:

1. purpose: calibration, benchmark, discovery, or manual research;
2. challenge or ad-hoc target;
3. target identity and black/white-box visibility;
4. human/agent participants and stance;
5. setup mode and explicit consent;
6. tools, containment, and limits;
7. scoring/monitoring policy;
8. immutable review and launch.

Advanced choices stay collapsed until relevant. Generated infrastructure and
autonomous configuration keep their existing review/double-lock gates.

**Shipped first slice (2026-08-10).** `/engagements/new` is now the canonical
GUI entry point. It captures benchmark, discovery, calibration, or manual
research purpose plus challenge/target source, then hands off to the existing
validated builder with the chosen context visible. Global Create, Home,
Engagements, and challenge-library actions use this entry; `/launch` and
`/wizard` remain compatibility routes. No deployment endpoint, authorization
confirmation, setup consent, or review gate was weakened. The remaining C2 work
at that point was participant/policy composition. Purpose was validated by every
deployment request and persisted as an append-only `engagement_intent` event;
compatibility clients could omit it. Generated, pasted, and Vulhub challenges return to the same builder
with the imported challenge selected and purpose preserved instead of dropping
the operator into the library. Remaining policy controls wait for matching
backend enforcement.

**Completion (2026-08-10).** The composed journey now captures purpose, source,
participant mode, and an enforced engagement time box. Every predefined,
custom, generated, pasted, Vulhub, Git, OCI, and local-bundle path carries that
contract into the existing backend request. Purpose/participants/policy are
recorded once as append-only intent; the time box controls deployment expiry.
Review distinguishes selectable intent from authoritative policy: agent access
and stance remain binding-enforced, target agent visibility remains black-box
unless a challenge explicitly declares white-box source, runtime containment is
provider-enforced, and monitoring/scoring are automatically derived. Generated
infrastructure still requires import/review before launch, and target
authorization/setup consent is unchanged. Legacy `/launch` and `/wizard` routes
remain valid compatibility entry points.

**Acceptance.** From the browser, the operator can launch every currently
supported predefined, custom, generated, Vulhub, Git, OCI, and local-bundle path
through one coherent journey, with the same backend validation as today.

**Met in source/render/contract tests, and confirmed live on 2026-08-18.** In the
browser, Create → New engagement → configuration → launch produced an active
arena from the challenge path with the composed contract intact: the
`engagement_intent` event recorded purpose, source, participant mode, time box,
and the platform-enforced containment/monitoring/scoring values, and the chosen
30-minute time box became the deployment expiry.

### C3 — Engagement/run workspace

Decompose the growing arena-detail page into one contextual workspace:

```text
Overview · Live · Target · Findings · Evidence · Changes
Agent · Trace · Score · Infrastructure
```

Only applicable tabs appear. Setup is a phase inside Overview/Live, not a permanent
page block. Destroyed arenas become read-only records whose evidence remains
available. Add SSE for live state, events, monitor signals, agent actions, findings,
and budgets; retire five-second polling.

**Acceptance.** An operator can follow provision → setup → engagement → result
without leaving the workspace, while detailed evidence and infrastructure remain
available on demand rather than competing on one page.

### C4 — Home and cross-cutting activity

Redesign Home only after C1–C3 so it reflects the real product model:

- active engagements and running evaluations;
- findings awaiting review;
- failed/blocked runs and containment warnings;
- recent comparisons;
- provider/capacity health.

Activity supplies global Findings, Evidence, and Audit indexes; each item links
back to its engagement/run context.

---

## 4. Research-ready runtime — complete the existing session

This work follows the C1 shell and C3 workspace foundations so new controls have
a durable place in the product. It completes, rather than replaces, legacy M4.

### R1 — HTTP research primitive

Ship structured, arena-target-only HTTP inspect/replay/modify over REST and
attacker MCP. Accept node plus relative path—not arbitrary URLs. Bound and hash
request/response bodies; keep audit events body-free; apply binding, budget,
timeout, and target-scope checks. Keep this distinct from MITM packet observation.

### R2 — Confined PoC execution

Run Python/PoC work in disposable CPU/RAM/PID/time-capped containers with no
filesystem or egress by default. Route lifecycle through the worker; never widen
the orchestrator's root-equivalent Docker-socket authority. Prove the sandbox
cannot reach the internet or cloud metadata.

### R3 — Pivoting and durable guardrails

- Foothold-scoped SSH forwards with explicit destinations, expiry, cleanup, and trace.
- Cross-process step/time/token/cost budgets with fail-closed accounting.
- Per-arena stop plus system-wide emergency stop; reject new work, cancel where
  safe, terminate disposable helpers, and flush final traces.

**Research-runtime acceptance.** A BYO agent confirms XSS in the browser, develops
a PoC in the sandbox, transfers payload/evidence, inspects and replays HTTP, and
tunnels to an internal service. Every action is scoped and traced; a breached
budget freezes further work; containment tests remain green.

---

## 5. GUI-driven agent evaluation workbench

### E1 — Durable experiment model

Add first-class records for agent builds, suites, evaluations, runs, and trials.
Every run records agent version/digest, model/scaffold, target/scenario digest,
visibility, seed, budgets, tool versions, start/end state, score, cost, trace, and
reset proof. Existing event-derived eval rows remain the export projection.

### E2 — Generic external-agent drivers

Support different agent shapes without embedding any agent's product logic:

- `mcp-interactive` for agents that use Nidavellir tools directly;
- `container-service` for persistent/event-driven agents;
- `external-webhook` for an authorized system outside the stack.

The driver owns prepare/start/wait/metadata/stop. Findings and evidence still
enter through Nidavellir's authenticated, independently validated path. A
continuous pentesting agent is the first serious internal validation case, not
a hard-coded dependency.

### E3 — Agent registry and suite builder

Library → Agents registers pinned builds, connectivity, driver, model/scaffold
metadata, secret references, and default limits. Evaluations → Suites composes
held-out challenges, trial counts, seeds, visibility, budgets, and reset policy.

### E4 — Active challenge episodes

A challenge may define deterministic phases:

```text
baseline release → representative traffic → changed component
→ observation window → fixed release → regression release
```

This measures agents that react to changes as well as one-shot exploit agents.
The episode controller is generic and provider-contained. Hidden truth and
release schedules are never exposed to the agent.

### E5 — New Evaluation wizard, live execution, and comparison

Entirely from the browser, an operator:

1. selects baseline and candidate builds;
2. selects a suite and trials;
3. reviews identities, seeds, budgets, and containment;
4. launches and watches live progress;
5. inspects failures/retries;
6. receives per-challenge and aggregate comparisons;
7. drills down to findings, validator evidence, timeline, and trace;
8. exports OpenInference/Inspect-compatible data.

Comparison metrics include verified TP/FP/FN, precision/recall where truth exists,
progress rate, detection latency, unnecessary retesting, fixed/regressed finding
lifecycle, steps/requests/tokens/cost, timeouts, and scope violations. Show paired
rows and uncertainty; never hide regressions inside one aggregate.

**Evaluation acceptance.** From the GUI, one operator runs two pinned agent builds
over the same active held-out suite for at least three trials, gets independently
verified results, and sees exactly where capability, false positives, latency,
cost, or safety improved or regressed.

---

## 6. Proof, release, and later extensions

### P1 — Held-out flagship proof

- Build a private/held-out challenge set; public labs are calibration only.
- Include static known-vulnerability, randomized, and active-change episodes.
- Publish leakage policy, scaffold/tool disclosure, repeated-trial methodology,
  uncertainty, and infrastructure-failure handling.
- Record the GUI journey: register builds → run evaluation → inspect proof → compare.

**Acceptance.** The public artifact demonstrates a reproducible agent-version
comparison, not merely a successful single exploit.

### P2 — Optional LLM-application targets

After the workbench is credible, add prompt-injection RAG, secret-exfiltration,
improper-output-handling, and excessive-agency challenges aligned with OWASP LLM
and Agentic Top 10. Reuse the same challenge, episode, validator, and comparison
model; do not create a separate evaluation product.

---

## 7. Explicitly deferred

These do not block the single-team, self-hosted evaluation product:

- MCP OAuth 2.1 and third-party tool-supply-chain defense;
- multi-tenant workspaces, SSO, graduated organization RBAC, and hosted billing;
- real AWS/OpenStack/libvirt apply and VM/binary desktop targets;
- multi-agent red-vs-blue and defender detection scoring;
- in-browser VNC/Guacamole and a full hosted web terminal;
- large public leaderboards.

Re-promote them only for a concrete need, roughly in this order: worker/socket
isolation → OAuth/tool trust → multi-tenant identity → VM/cloud providers →
multi-agent/purple-team.

---

## 8. Standing principles

- **GUI-driven product, API-backed architecture.** Every normal operator workflow
  is complete in the browser. Business logic, orchestration, and persistence stay
  in the orchestrator/services; Flask/Jinja presents and drives them.
- **Bring your own agent.** Nidavellir ships a neutral substrate and thin reference
  connectors, never the agent whose capability it claims to measure.
- **AI-centered, never AI-required.** A human can operate an engagement and submit
  evidence without a model.
- **Immutable identity before score.** Targets, agent builds, scenarios, tools,
  seeds, and starting state are recorded. A comparison without them is invalid.
- **Deterministic proof before judgment.** Validators and observed effects outrank
  agent claims. Unknown is not refuted; discovery mode does not pretend to know
  false negatives.
- **Containment is the primary control.** No egress by default, narrow tools,
  explicit consent, bounded helpers, and live containment tests.
- **Preserve feature parity during UI migration.** Reorganize incrementally; do not
  replace working backend flows or strand existing capabilities.
- **Verify the product, not only tests.** Each milestone needs automated coverage
  and a live Docker-local path through the real compose stack.
- **One source of status truth.** ROADMAP is the public sequence. The internal
  backlog and active development handoff must be reconciled with it at each
  milestone boundary.

---

## 9. Legacy milestone mapping

| Previous roadmap | New location |
|---|---|
| M1 repo→service | S2, shipped |
| M2 monitoring/scoring | S3, shipped |
| M3 eval/export/reference harness | S3, shipped; durable comparison continues in E1–E5 |
| M4 research workspace/tooling | S4 shipped slice + R1–R3 remainder |
| M5 regression/eval pipeline | E1–E5, now explicitly GUI-driven |
| M6 LLM-app targets | P2, optional after proof |
| Former console/SSE items | C1–C4 |
| OAuth, multi-tenancy, cloud/VM, purple-team, VNC | §7 deferred |

Detailed historical `Pn-m` implementation records remain in
[`.agent/backlog/BACKLOG.md`](.agent/backlog/BACKLOG.md) and git history.

---

## 10. Architecture decisions

- ADR-0002 — API-key authentication and WebUI login.
- ADR-0003 — provider driver interface and scenario compilation.
- ADR-0004 — PostgreSQL persistence and event spine.
- ADR-0005 — MCP gateway, stances, bindings, and guardrails.
- ADR-0007 — software-under-test arenas.
- ADR-0008 — repository-to-image pipeline.
- ADR-0009 — monitoring, validators, and structured scoring.
- ADR-0010 — eval export, reference harness, and replay.
- ADR-0011 — reproducible research sessions and change intelligence.
- **ADR-0012 — GUI-first product model and console information architecture.**

The detailed state-of-the-art references behind the shipped design remain in the
ADRs and repository history. New evaluation work should integrate with established
formats such as Inspect and OpenInference rather than inventing a general-purpose
eval framework around Nidavellir's specialized cyber environment.
