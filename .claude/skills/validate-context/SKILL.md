---
description: Audit CFD context-file integrity — verify CLAUDE.md size, @-references resolve, ADR index consistency, no duplicated context, and CURRENT_STATUS.md freshness. Use when the user asks to "validate context", "audit docs", or check whether the CFD scaffolding is healthy.
---

Run a CFD context-integrity check. Do not modify files; just report findings.

Checks to perform:

1. **CLAUDE.md size.** It should be under ~150 lines and consist mostly of
   `@docs/...` references plus the build/run section and critical rules. Flag if
   it has grown into a long-form document.
2. **`@`-references resolve.** Every `@docs/...` reference in `CLAUDE.md` points to
   a file that exists.
3. **ADR index integrity.** Every file matching `docs/decisions/[0-9]*.md` is listed
   in `docs/decisions/_index.md`, and every row in the index points to a file that
   exists.
4. **No duplicated context.** Spot-check that the tech stack is described in
   `docs/STACK.md` only (not also expanded inside `CLAUDE.md` or `ARCHITECTURE.md`),
   and that decision rationale is in the relevant ADR (not duplicated in
   `ARCHITECTURE.md`).
5. **`CURRENT_STATUS.md` freshness.** Look at the `Last updated:` line. If it is
   more than two working days behind today's date, flag it.

Output a short report grouped by check, with `✓` / `✗` and a one-line note for each.
End with a one-line overall verdict: `Context healthy.` or
`Context needs attention: <N> issues.`
