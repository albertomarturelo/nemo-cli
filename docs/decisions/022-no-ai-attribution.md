# ADR-022: No AI-Attribution Metadata in Commits and PRs

## Status

Accepted (amends ADR-005 §4)

## Date

2026-06-16

## Context

ADR-005 §4 (GitHub Flow) prescribed that AI-assisted squash commits end with a
`Co-Authored-By` footer. In practice the repository was later recreated
specifically to remove every `Co-Authored-By` line and any "Generated with …"
attribution, to keep a clean history authored under the human author's name. The
documented decision and the actual practice conflicted; ADR-020 (PR review)
flagged it as unresolved and the `review-pr` checklist refused to assert either
side. This ADR resolves the conflict in favour of the established practice.

## Decision

Commits and PR descriptions in this repository carry **no AI-attribution
metadata** — no `Co-Authored-By:` trailer and no "🤖 Generated with …" line —
regardless of how much AI assistance was involved. Authorship is the human
author's.

This **amends ADR-005 §4**: the `Co-Authored-By` footer clause is dropped.
Everything else in ADR-005 stands (branch naming `<type>/<slug>`, squash merge,
PR-required, branch deletion on merge). Conventional-Commits prefixes and English
commit messages remain required. This project policy **overrides** any agent or
tooling default that would append attribution; if a tool adds one, strip it
before merge.

## Alternatives Considered

- **Keep ADR-005 §4 (require the footer).** Would force re-writing the existing
  clean history or accept a documented-vs-actual mismatch forever, and contradicts
  the deliberate repo recreation. Rejected.
- **Supersede ADR-005 entirely with a new branching ADR.** Heavy — it would
  orphan the still-valid majority of ADR-005 just to change one clause. A scoped
  amendment is the right granularity. Rejected.
- **Leave it unresolved.** Poisons PR review (the checklist cannot decide) and
  leaves an implicit decision — the anti-pattern ADR-013/016 forbid. Rejected.

## Consequences

- The `review-pr` checklist asserts "no AI-attribution metadata (ADR-022)"
  instead of flagging a mismatch; ADR-020's open-conflict note is closed.
- ADR-005's status records the §4 amendment; the original clause survives in git
  history (CFD Principle 4 — both states survive).
- `CLAUDE.md` gains a one-line critical rule so the policy is applied at every
  commit, overriding tooling defaults.
- No change to the existing commits on the CFD-alignment branch — they already
  comply.
