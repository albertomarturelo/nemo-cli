# ADR-013: Write the ADR Before Implementing the Decision

## Status

Accepted

## Date

2026-06-16

## Context

nemo-cli has treated "document significant decisions as ADRs before writing
the code that implements them" as a `CLAUDE.md` critical rule since inception —
the `002 → 004` stack supersession is the canonical example. This ADR promotes
that rule to a first-class, reviewable decision and adopts the CFD shareable-
catalog entry `adrs/ai-workflow/adr-before-implementing.md`.

The failure mode it prevents: a decision lands in code, its rationale and
rejected alternatives evaporate, and a future session — seeing only *what* the
code does, not *why* — proposes refactoring back toward an already-rejected
option. That is how an AI agent develops "tunnel vision".

## Decision

Before any qualifying change is implemented:

1. Run the `/new-decision` skill.
2. Articulate Context, Decision, Alternatives Considered, Consequences.
3. Save as `docs/decisions/<NNN>-<slug>.md`.
4. Update `docs/decisions/_index.md` in the same change.
5. **Only then** implement.

A change *qualifies* when it introduces a new dependency / library / service,
changes a convention (testing strategy, layer boundaries, error handling), adds
a workflow step (CI, release, distribution), or picks one of several plausible
patterns. Skip for trivial choices (a colour, a log phrasing) and bug fixes
that do not change a pattern. If implementation later reveals a flaw, supersede
the ADR with a new one — as ADR-004 superseded ADR-002 — rather than silently
changing behaviour.

## Alternatives Considered

- **Document decisions in PR descriptions.** PRs are not loaded at session
  start; they are discoverable only via `gh pr view` archaeology. Rejected.
- **Document decisions in a wiki / Confluence.** Same problem — not in the
  agent's context. Rejected.
- **Document only after a decision proves correct.** Selection bias: you lose
  the record of decisions that turned out wrong, which is the most useful kind
  to keep. Rejected.

## Consequences

- The `git log` of `docs/decisions/` shows each ADR landing in the same PR (or
  an earlier one) as the code it justifies; reverting a feature reverts or
  supersedes its ADR atomically.
- Adds ~10 minutes per significant decision, recovered within one or two future
  sessions that would otherwise re-litigate the same question.
- Enforced by the `/new-decision` skill and cross-referenced from `CLAUDE.md`'s
  Critical Rules, which now points here for the rationale.
