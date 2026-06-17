# ADR-021: Work Units Live in GitHub Issues with a Fixed Body Template

## Status

Accepted

## Date

2026-06-16

## Context

This ADR adopts the CFD shareable-catalog entry
`adrs/process/work-units-as-external-tracker.md`. Until now nemo-cli tracked
in-flight work only in `docs/CURRENT_STATUS.md`'s "Next Priorities" — fine for
orientation, but it does not tell a session *what exactly* to do, *where*, what
acceptance looks like, or which ADRs to load first. The gap is filled today by
re-explanation or by the agent scanning code — both expensive and drift-prone.

This is **new practice** for nemo-cli, not a pre-existing rule. It is adopted
now because the project is moving from "everything in CURRENT_STATUS" toward
issue-driven, atomic, one-session-sized units (ADR-017, ADR-019).

## Decision

Every non-trivial unit of work is a **GitHub Issue** (queried via `gh`) carrying
a fixed body template so any session parses it in O(1) tokens:

```markdown
## Context
<2–4 sentences: trigger + user-visible outcome>

## Target
- Files / dirs: <paths or modules>
- Pattern to mirror: <existing file to copy shape/naming from>

## ADRs to load
- [ADR-NNN](docs/decisions/NNN-*.md)

## Acceptance criteria
- [ ] <DoD item — becomes the PR checklist>

## Reproduction (fixes only)
<minimal repro the agent can run>

## Estimated sessions
<1 | 2–3 | 4+>
```

If "Estimated sessions" > 1, decompose into sub-issues before starting. The
`issue-new` skill creates issues from this template; `issue-start <n>` picks one
up and pre-loads its ADRs; the PR copies the acceptance checklist verbatim and
merging closes the issue. `docs/CURRENT_STATUS.md` references in-progress work by
`#N`. Trivial one-off changes may skip the tracker.

## Alternatives Considered

- **A `specs/` directory in the repo.** Duplicates state with wherever work is
  tracked; sync rots; no native collaboration surface. Rejected.
- **Free-form issues, no template.** Forces every session to re-discover the
  structure → token waste and parse errors. Rejected.
- **`CURRENT_STATUS.md` / `TODO.md` as the sole mechanism.** No querying, no DoD
  enforcement, no per-unit ADR list. This is the status quo we are augmenting;
  rejected as the *only* mechanism but retained as the running session log.

## Consequences

- `gh issue view <n>` on any in-progress issue returns the fixed sections; PRs
  reuse the acceptance checklist verbatim; merging closes the linked issue.
- Adds 3–5 minutes to issue creation, recovered on the next session (~1.5–3k
  tokens to orient vs ~10k+ for code discovery).
- Introduces a new habit. Until issues exist, `start-session` simply finds none
  and orientation falls back to `CURRENT_STATUS.md` — no regression.
- This is the one adopted ADR that adds a workflow nemo did not already follow;
  the other catalog ADRs (013–020) formalize existing practice.
