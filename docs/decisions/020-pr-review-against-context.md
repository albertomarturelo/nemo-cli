# ADR-020: Review the PR Against Context, Not Against Intent Discovery

## Status

Accepted

## Date

2026-06-16

## Context

nemo-cli ships every change via a Pull Request (ADR-005, GitHub Flow). This ADR
adopts the CFD shareable-catalog entry `adrs/process/pr-review-against-context.md`
and is implemented by the `review-pr` skill.

Without indices, an agent asked to review a PR has to *discover the project's
intent from the code* — what patterns it uses, which conventions apply, why
choices were made. That discovery scales with repo size and burns the most
tokens. CFD's bet is that intent does not need re-discovery: it is captured in
`docs/CONVENTIONS.md`, the ADRs (with their consequences), ADR-005's PR
conventions, and — when present — a linked issue's acceptance criteria (ADR-021).

## Decision

PR review is mediated by the `review-pr` skill, which:

1. **Fetches** PR metadata, diff, and the branch commit story via `gh`.
2. **Loads the agenda**: `docs/CONVENTIONS.md`, the ADR index, every ADR named
   in the PR body or linked issue, and the PR template if one exists.
3. **Reads changed source files to the depth the agenda demands.** For nemo-cli
   that means reading changed source files in full — strict `pyright` and the
   `api_request()` boundary rule (ADR-003) require verifying call sites, types,
   and that no handler calls `httpx` directly.
4. **Reports** ✓ / ⚠ / ✗ per checklist item, each citing the specific ADR or
   `CONVENTIONS.md` line it satisfies or violates.
5. **Does NOT auto-fix.** Findings are surfaced for the author to address next
   session.

The skill body *is* the curated checklist; it grows as new conventions land,
echoing ADR-016.

## Alternatives Considered

- **Discovery-driven review (no indices).** Scales with repo size, re-derives
  intent each PR, ignores rejected alternatives that live only in ADRs.
  Rejected.
- **A project-agnostic depth rule** (always full files, or always diff-only).
  Depth belongs to the project; nemo-cli reads changed source in full. Rejected.
- **External code-review SaaS.** A useful complement but does not load nemo's
  ADRs as the review agenda. Not a replacement.

## Consequences

- A `review-pr` skill exists, embedding nemo's real checklist with real ADR
  numbers and `CONVENTIONS.md` references; review findings cite them rather than
  offering generic "looks good" reactions.
- Review quality depends on the indices being current; stale `CONVENTIONS.md` or
  out-of-date ADRs poison the review. Mitigated by `/validate-context` and the
  ADR-016 discipline.
- One known drift to reconcile: ADR-005 §4 still prescribes a `Co-Authored-By`
  footer on AI-assisted squash commits, while the recreated repo deliberately
  carries none. The checklist cites ADR-005 for commit/PR conventions but does
  **not** assert the footer rule until that conflict is resolved by amending or
  superseding ADR-005.
