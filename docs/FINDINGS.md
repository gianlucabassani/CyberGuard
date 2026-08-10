# Bugs & Improvement Vectors

Findings from building and live-verifying M2 (scoring), the MCP loop, and M3 (eval
layer + reference harness). Two categories: **bugs** (defects, with the two found
this cycle already fixed) and **improvement vectors** (open work, ranked by
leverage). Companion to [`OVERVIEW.md`](./OVERVIEW.md) and [`INTERNALS.md`](./INTERNALS.md).

Severity: 🔴 high · 🟠 medium · 🟡 low. Effort: S/M/L.

---

## A. Bugs

### A1 — Unreachable target scored as *refuted* instead of *unknown* · 🟠 · **FIXED**
`validators` / `api._arena_http_fn`. `curl` still prints its `-w` status marker with
code `000` on a connection failure, so an unreachable victim produced an empty body
that the reflected-XSS check read as "reflected? no → **refuted**". A false *refuted*
violates the tri-state contract (`false` means "probe ran, effect absent"). **Fix:**
treat HTTP status `0` as unreachable → raise inside the probe → validator records
`null` (unknown). Caught during the live active-validator run; regression-tested.

### A2 — Discovery-mode findings never confirmed by the crash oracle · 🟠 · **FIXED**
`api.arena_score` / `scoring`. Passive crash correlation was gated on findings that
*matched a manifest vuln*, so in **discovery** mode (no manifest) a reported finding
on a crashed node was never credited — the score showed `0 confirmed` despite a real
crash. **Fix:** correlate **all** findings (not just matched) and add a
`confirmed_findings` count independent of manifest ids; the discovery answer/tier now
reflect it. Regression-tested.

### A3 — MCP `report_finding` doesn't forward the active-validation inputs · 🟠 · **FIXED**
`agent-gateway/gateway/{tools,server,rest_client}.py`. The orchestrator's
`FindingRequest` accepts `path`/`param`/`payload`/`oast_token` (the evidence that
lets an *active* validator confirm a finding), but the gateway's `report_finding`
tool only forwarded `title`/`cwe`/`node`/`evidence` — so an MCP agent's findings
could only be confirmed by **passive crash correlation**, never by the active
XSS/marker/OAST probe. **Fix:** the four optional fields are now threaded through the
tool schema (`server.py`), `tools.report_finding`, and `rest_client.report_finding`;
the ack stays neutral. An MCP agent can now get its web findings actively proven.
Regression-tested (`test_report_finding_forwards_verification_inputs`).

### A4 — `get_topology` "null node names" · 🟡 · **NOT A BUG**
The live `nodes: [null, null]` was a **diagnostic-script key mismatch**, not a
framework defect: the gateway correctly returns each node keyed `"node"` (with the
real name), and my throwaway MCP test client read `n.get("name")`. `get_topology` /
`list_targets` are internally consistent on `"node"`. Locked with a test
(`test_get_topology_returns_named_nodes`) asserting non-null names + the `"node"` key.

### A5 — Active probe assumes `curl` on the foothold · 🟡 · **FIXED**
`api._arena_http_fn` shelled `curl` only. **Fix:** the probe now prefers `curl`
(real HTTP status) and falls back to `wget --content-on-error` (status-unknown → a
`200` sentinel; the reflected-XSS/marker validators check the body, not the code);
no tool or no response still yields *unknown*, never a false *refuted*. Widens the
foothold images active validation works from.

---

## B. Improvement vectors

### B1 — Full-compose-stack verification · 🟢 · **VERIFIED (2026-07-14)**
Ran end-to-end through the live `docker-compose` stack (orchestrator + Celery worker +
beat + redis + webui, `docker-local`, real containers): import scenario → **worker
deploy** → active → **the monitor beat autonomously recorded a `crash` signal** (not a
manual trigger) → operator bind → agent finding → **crash correlation confirmed it** →
discovery score `1.0` → eval-export; plus the live **MCP gateway** path (real
`docker exec`, A3 forwarding). No defects — the three apparent "issues" during
verification were diagnostic-script errors on my side (wrong container-label key
`nidavellir.lab_id`, a bad jq filter, and misreading validation *inputs* as stored
fields). One real finding: **v3 `command` is string-only** (docker-py shlex-splits it),
not a list — the API validator rejects a list.

### UI-1 — Console didn't surface discovery-mode score or findings · 🟠 · **FIXED**
`webui/app.py::_score` returned `None` whenever there was no manifest, so **discovery /
SUT arenas showed no score at all**, and there was no findings list. **Fix:** `_score`
now returns the structured scorecard in both modes; the arena page has a compact,
mode-aware **Assessment** panel (benchmark = hidden known-vuln list matched by a parser;
discovery/SUT = agent-generated findings verified by the crash oracle / validators),
proper empty states, and a **Findings** list with per-finding verification. Live-verified.

### UI-2 — Configurator (agent-proposed steps) had no output console · 🟠 · **FIXED**
The `setup_step` event stored `command`/`exit_code` but **not stdout/stderr** — so an
operator approving an agent-proposed setup step saw no real output. **Fix:** the event
now persists bounded stdout/stderr, and the configurator card renders a **Setup
console** (command + exit + real output, terminal-style). Live-verified end-to-end.

### B2 — Headless-browser XSS execution oracle · 🟢 · DONE (2026-08-02)
`browser_visit` runs pinned disposable Chromium on the selected arena segment with
bounded resources/output and no arbitrary URL surface. `reflected_xss` now injects
a platform-owned DOM marker and confirms only observed JavaScript execution;
reflection alone remains unverified and a completed non-execution is refuted.

### B3 — Companion model-provider breadth (BACKLOG P3-4) · 🟢 · **DONE**
Fully shipped and live-verified. `openrouter` + `huggingface` + `custom` providers
added everywhere (`OPENAI_COMPAT_BASE`, api `MODEL_PROVIDERS`, webui picker/brands);
a generic `openai_base()` resolver reads `NIDAVELLIR_MODEL_BASE_URL`; and a
**per-connection `base_url`** now threads model → migration (0004) → `database` →
api (`/agent/model` + verify) → `model_chat`/`model_verify` (per-call base_url wins
over preset/env) → the webui modal (a Base-URL field shown for OpenAI-compatible
providers). Live: PUT `openrouter` + `base_url` → stored + masked read-back.
`make check` 684 green; scope stays companion-only (the BYO-agent path is untouched).

### UI-3 — Arena page + configurator UX overhaul · 🟢 · **DONE**
The arena detail page was a messy pile of ad-hoc-styled cards using an invalid
`var(--border)` token (invisible bars/borders). Rebuilt on the real design system
(`.usage-stat`, `.bar`, `.chips`, `.cfg-out`), reordered to an operator flow (arena →
configure → position → results → activity), and the **Configurator moved into a wide
modal overlay** — the page shows a compact overview (mode + steps + status) and the
method chooser (operator / agent-proposal / autonomous) + live setup console open in
the pop-up. Live-verified.

### B4 — Console information architecture cannot absorb evaluation cleanly · 🟠 · L

The console has real pages for arenas, launch, SUT intake, inventory, live agent
attribution, logs, settings, findings, evidence, and configuration, but those
capabilities reflect implementation increments rather than durable product
objects. Adding agent builds, suites, trials, runs, and comparisons as more
siblings would make navigation and arena detail substantially harder to use.

**Decision:** ADR-0012 and ROADMAP C1–C4 reorganize the GUI around Engagements,
Evaluations, Library, Activity, and Administration; unify Launch/SUT; decompose
arena detail into a contextual workspace; preserve feature parity during migration.

### B5 — Reference-agent auth matrix · 🟡 · S–M
`AnthropicBrain` (Messages API) needs an API key and hasn't been run against the real
API (no key available in dev). The subscription path (Claude Code) is wired and
flag-validated but its `claude -p` reasoning run is user-triggered (spending + nesting
make it inappropriate to auto-run). Optional: an `OpenAICompatBrain` so the harness
can drive OpenRouter/HF/DeepSeek models for API-key runs.

### B6 — Build tiers beyond Dockerfile · 🟡 · M (ADR-0008)
`build_planner` classifies **compose / devcontainer / buildpack** tiers but only the
Dockerfile tier + LLM synthesis are *executed*. Wiring a compose runtime, the
`devcontainer` CLI, or `pack`/Paketo would widen the set of repos that stand up
without synthesis.

### B7 — Research runtime remains incomplete · 🟠 · M–L

The browser and file/evidence slices are real, but a serious offensive runtime
still needs structured HTTP inspect/replay/modify, a confined PoC sandbox, SSH
tunnelling, durable fail-closed budgets, and kill switches. These now follow the
C1/C3 console foundation so their controls land in a stable workspace rather than
adding more arena-page cards.

### B8 — Evaluation is exportable but not yet a durable product · 🟠 · L

Eval rows are derived on demand from events, and the reference harness can run a
suite, but there are no first-class Agent build, Suite, Evaluation, Run, or Trial
records; no GUI experiment workflow; no active release episode; and no paired
N-vs-N+1 comparison. ROADMAP E1–E5 makes this the evaluation workbench after the
console and research-runtime foundations.

### B9 — Held-out benchmark proof is missing · 🟠 · M

Public labs and colocated manifests are useful calibration but weak public
evidence because of contamination and overfitting. The flagship needs a private
or held-out suite, repeated trials, a leakage policy, infrastructure-failure
handling, and a recorded GUI comparison—not only a successful exploit demo.

### B10 — VM / cloud providers are skeletons · 🟡 · L (deferred)
`openstack`/`aws`/`libvirt` pass `tofu validate` but have **no live apply**;
docker-local is the whole substrate today. Real VM arenas (libvirt/QEMU increment 2 —
live boot + `exec_in_node` + egress) unblock VM-class scenarios. Deliberately deferred
until the H1 spine is compelling.

### B11 — Doc/tree drift guardrail · 🟡 · S
Several times this cycle the ROADMAP/ADR status lagged the code (e.g. M2 "not yet
built" while `monitor.py` existed; ADR-0007/0008 stuck "Proposed" after shipping). A
lightweight check (or discipline) to reconcile ADR/ROADMAP status against the tree at
each milestone would prevent stale planning docs.

---

## C. What's solid (so the list above is in proportion)

- The **moat is real and proven**: crash oracle → deterministic validators →
  structured score, live-verified against real Docker arenas (a real crash detected,
  a real reflected-XSS confirmed over a socket, a real MCP finding scored).
- **Containment** is default-on and CI-tested (no-egress + canary).
- **No AI shipped** — the scope boundary holds across generation, validation, and the
  harness; the reference agent is thin, optional wiring.
- **771 tests passed in the declared Python 3.11 container gate** on 2026-08-02;
  Ruff clean and no medium/high Bandit findings. Host Python 3.13 currently hangs
  in Starlette `TestClient` and is not the supported full-test path.

---

## D. Suggested order

1. **B4 / ROADMAP C1:** prototype the object model and routes, then ship the
   grouped application shell with compatibility navigation.
2. **ROADMAP C2–C4:** unify engagement creation, decompose arena detail, add SSE,
   then build object-driven Activity/Home.
3. **B7 / ROADMAP R1–R3:** finish HTTP, PoC sandbox, tunnel, budgets, and kill switches.
4. **B8 / ROADMAP E1–E5:** durable experiment records, generic agent drivers,
   GUI suites/runs/comparisons, and active episodes.
5. **B9 / ROADMAP P1:** held-out repeated suite and recorded comparison proof.
6. Keep build-tier breadth and VM/cloud providers deferred unless a selected
   challenge requires them.
