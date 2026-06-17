# ADR-018: The Session-Close Ritual

## Status

Accepted

## Date

2026-06-16

## Context

`CLAUDE.md` already makes "Update `docs/CURRENT_STATUS.md` before closing every
session" a non-negotiable critical rule. This ADR formalizes the full ritual,
adopts the CFD shareable-catalog entry `adrs/process/session-close-ritual.md`,
and is implemented by the `close-session` skill.

The failure mode it prevents — the single most common context-loss bug: a
session produces good work, closes, the next session starts, and the agent has
no record of what was just done. The cost is paid in re-explanation tokens or,
worse, an agent that invents a contradictory plan.

## Decision

Every session ends with the close ritual (the `close-session` skill):

1. **Update `docs/CURRENT_STATUS.md`:** move completed items from "In Progress"
   to "Recently Completed", note pending or newly surfaced work, update "Known
   Issues", re-rank "Next Priorities", and bump the "Last updated" date.
2. **Update `docs/CONVENTIONS.md`** if any convention was clarified (see
   ADR-016).
3. **Write an ADR** if a significant decision was made informally during the
   session (see ADR-013).
4. **Ship `docs/` context changes in the same commit/PR** as the session's code.

The ritual is **non-negotiable**. Note one project-specific carve-out:
`docs/CURRENT_STATUS.md` is local-only (gitignored) for this solo project, so
step 4's "same PR" applies to `CONVENTIONS.md` and ADRs; the status file is
still updated every session, just locally.

## Alternatives Considered

- **Update `CURRENT_STATUS.md` ad-hoc when convenient.** Predictably skipped
  under time pressure. Rejected.
- **Auto-generate `CURRENT_STATUS.md` from `git log`.** Loses the "why" and the
  "blocked by"; commit messages are too terse. Rejected.
- **Use a PM tool instead.** The agent does not read Jira/Linear by default, so
  the project-context surface stays blind to it. (Issues *are* used for work
  units per ADR-021, but the running session log stays in-repo.) Rejected as the
  status mechanism.

## Consequences

- `git log -1 --format=%ar -- docs/CURRENT_STATUS.md` is never older than the
  last working day during active development.
- Costs ~3–5 minutes per session, recovered roughly 10× in the next session's
  faster startup.
- The close ritual and the session-start orientation (`start-session`) are two
  halves of the same loop; short sessions (ADR-019) make the loop cheap.
