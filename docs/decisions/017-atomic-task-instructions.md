# ADR-017: Atomic Task Instructions for AI Sessions

## Status

Accepted

## Date

2026-06-16

## Context

This ADR adopts the CFD shareable-catalog entry
`adrs/process/atomic-task-instructions.md`. AI agents perform poorly on vague,
multi-objective prompts ("implement the portfolio domain") and well on scoped,
single-objective prompts. Without this discipline, sessions drift, output
diverges from conventions, and tokens are wasted re-discovering context for each
sub-task; the agent also accumulates tunnel vision as the prompt grows fuzzy.
nemo-cli has worked this way informally — this records it as the standard.

## Decision

Every implementation instruction MUST include:

1. **One objective**, expressed as a single deliverable.
2. **The exact target location** (file path or directory).
3. **The reference ADR or pattern** to follow.
4. **One existing file to mirror**, when one exists.

**Bad:** `Implement the portfolio movements feature.`

**Good:**

```
Add the movements service in src/nemo_cli/portfolio/movements.py.
Route all HTTP through api_request() (ADR-003) and override the timeout to
180s at the service layer (CONVENTIONS § Timeouts).
Mirror src/nemo_cli/portfolio/summary.py for shape, naming, and typed result.
```

If a task cannot be expressed atomically, decompose it first — that
decomposition is part of the work, not overhead.

## Alternatives Considered

- **Trust the agent with vague prompts and iterate.** Produces inconsistent
  output and consumes 3–5× more tokens. Rejected.
- **Always write a detailed spec before any prompt.** Overkill for small tasks;
  the atomic-prompt rule is the minimum viable spec. (For multi-session work,
  the spec lives in a tracker issue — see ADR-021.) Rejected as a blanket rule.

## Consequences

- A session's prompts can be skimmed: every implementation prompt carries a
  target path and a reference (ADR or example file).
- Re-prompts ("no, not that, do X instead") drop measurably.
- Costs one or two extra sentences per prompt; saves several times that in
  re-prompt rounds.
