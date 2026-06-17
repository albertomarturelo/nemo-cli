# ADR-016: Document the Convention, Not Just the Fix

## Status

Accepted

## Date

2026-06-16

## Context

`CLAUDE.md`'s "Critical Rules" section already accumulates project-specific
lessons. This ADR formalizes the habit behind it and adopts the CFD shareable-
catalog entry `adrs/process/document-corrections-not-fixes.md`.

The failure mode: an agent generates code that violates a convention, the fix is
applied inline, and next session the same violation recurs — because the
convention existed only in the user's head, not in the agent's context. The
project pays the same correction cost forever.

## Decision

A correction is incomplete until **both** are true:

1. The wrong code is fixed.
2. The violated convention is captured — in `docs/CONVENTIONS.md` for a
   style/pattern rule, or as a new ADR when the rule deserves alternatives
   consideration. A substantial, cross-cutting rule also gets a one-line entry
   in `CLAUDE.md`'s Critical Rules that points at the ADR or convention.

The completion phrase to use with the agent: *"Fix the code **and** add this
rule to `docs/CONVENTIONS.md` under `<section>`."* New conventions surface in
the **same PR** as the code that motivated them, never in a follow-up.

## Alternatives Considered

- **Trust the agent to learn within the session.** Does not survive a session
  restart. Rejected.
- **Put every rule directly in `CLAUDE.md`.** Inflates the index; `CLAUDE.md`
  stays a map, not a rulebook. Rejected.
- **Document only after the third occurrence.** The cost compounds — "we'll deal
  with it later" is how implicit conventions rot. Rejected.

## Consequences

- The `git log` of `docs/CONVENTIONS.md` shows new entries during active
  development; if it goes flat for a stretch, either the project is mature or
  corrections are being silently applied.
- New conventions land with their motivating code, not in a separate PR.
- Adds ~30 seconds per correction; payback is not re-explaining the same rule a
  month later.
