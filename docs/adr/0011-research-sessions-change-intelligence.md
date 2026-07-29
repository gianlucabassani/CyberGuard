# ADR-0011: Reproducible research sessions and shared change intelligence

- Status: Accepted
- Date: 2026-07-29

## Context

Nidavellir must support three different jobs: training on known labs,
controlled comparison of agents, and vulnerability research on current
open-source or authorized private/closed-source products. Treating them as one
leaderboard hides benchmark leakage and assigns false precision to research
targets whose unknown vulnerabilities have no complete ground truth.

Humans and agents also need the same evidence primitives. A GUI-only diff cannot
be automated; an MCP-only diff prevents analyst review and trust.

## Decision

The durable product unit is a **reproducible security research session**:
immutable target identity, declared authorization/scope/source visibility,
isolated reset point, action trace, changes, evidence, findings and replayable
result.

Training, controlled benchmark and discovery/research remain separate reporting
tracks. Only the controlled track uses hidden known-vulnerability recall as an
accuracy measure. Research reports confirmed findings, crash sites, coverage,
reproducibility and effort without pretending unknown false negatives are known.

Change intelligence is a provider capability used by REST, MCP and GUI:

- repository paths come only from provider outputs;
- attacker bindings see only an explicitly white-box, arena-scoped research
  copy; it is writable on the foothold but separate from the running target;
- configurators see writable setup source;
- Git runs with fixed argv and repository hooks, pagers, textconv and external
  diff drivers disabled;
- revisions and relative pathspecs are validated;
- output is bounded and paginated before leaving the target;
- untracked names are shown but untracked contents are not opened, avoiding
  symlink-based arbitrary reads;
- audit events retain metadata, not potentially sensitive diff bodies.

Git target intake resolves the requested branch/tag to a commit before compiling
the scenario. The target manifest stores requested and resolved refs separately,
the operator's authorization basis/scope confirmation, and the reset strategy.
An infrastructure preflight checks identity, authorization, target/foothold
health, workspace availability and reset reproducibility. Required failures stop
the pre-armed setup session from opening. REST, GUI and MCP consume the same
event-backed result.

Public OCI intake uses registry metadata only in the control plane. Tags resolve
to manifest SHA-256 digests and deployment specs contain only the digest-pinned
runtime reference. Supplied digests are verified. Registry redirects, internal
hosts, non-HTTPS token realms and private credentials are outside this slice.
The target manifest also fixes the runtime platform so an immutable
multi-architecture index cannot select different child artifacts across hosts.
The provider preserves native image startup—even for distroless artifacts—and
treats an early exit as a failed preflight instead of changing behavior with a
shell keepalive. Packaged images skip source-workspace and configurator checks.

## Consequences

The first implementation supports Git-backed docker-local workspaces, immutable
Git intake, and public OCI digest intake. Providers that cannot implement the
primitive fail explicitly. Closed-source research next requires immutable binary/installer intake,
before/after filesystem manifests and a snapshot-capable local VM provider; it
must not be simulated with a source diff.

The UI and MCP now agree on what changed. Future patch export and finding
attachments must build on this capability rather than creating alternate paths.
