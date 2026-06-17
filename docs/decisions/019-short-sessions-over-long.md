# ADR-019: Short Sessions Over Long Ones

## Status

Accepted

## Date

2026-06-16

## Context

This ADR adopts the CFD shareable-catalog entry
`adrs/ai-workflow/short-sessions-over-long.md`. Even with a 1M-token context
window, an agent's adherence to conventions, the current acceptance criteria,
and previously-loaded ADRs measurably degrades as a single session lengthens:
it re-introduces rejected patterns, silently invents conventions that conflict
with `docs/CONVENTIONS.md`, loses track of which item it is implementing, and
mis-cites ADRs by number. This is an attention problem, not a token-budget one —
bigger windows do not push the drift horizon out proportionally.

The fix is procedural and is *only viable* because CFD keeps context outside the
session: `docs/CURRENT_STATUS.md` carries in-flight state, `docs/CONVENTIONS.md`
the rules, ADRs the rationale, and (per ADR-021) tracker issues the acceptance
criteria.

## Decision

Treat each working session as **disposable**:

- **Soft ceiling ~1 hour, hard ceiling ~2 hours.**
- Any drift signal above triggers an immediate `close-session` + restart, even
  mid-task.
- Do not chain unrelated work across one giant session; decompose into multiple
  sessions. For non-trivial work, roughly one session per coherent unit (often
  one tracker issue) is the right cadence.

A fresh `start-session` reaches the previous session's readiness in ~1.5–3k
tokens — there is no progress to lose.

## Alternatives Considered

- **Long single sessions.** Avoids restart overhead but pays for it in code that
  ignores conventions and a model that loses track of what it agreed to. Loses
  on net. Rejected.
- **One session per acceptance-criteria item, always.** Over-decomposition; pays
  the ~1.5k-token start cost more often than necessary. Rejected.
- **Trigger restart on token usage.** Indirect — the real signal is *drift*, not
  token count. Rejected.

## Consequences

- Most sessions last 30–60 minutes; `docs/CURRENT_STATUS.md` shows several
  updates per active day, not one nightly mega-update; PRs land at roughly
  "1 PR ≈ 1 session".
- Restart costs ~1.5–3k tokens — cheaper than drift, which costs minutes of
  re-prompts plus code that has to be redone.
- Depends on the close ritual (ADR-018) to make restart cheap; the two ADRs are
  paired.
