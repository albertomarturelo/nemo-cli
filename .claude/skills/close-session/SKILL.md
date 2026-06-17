---
description: Close a CFD session by running the non-negotiable session-close ritual — update docs/CURRENT_STATUS.md, capture any clarified convention or informal decision, and produce a PR-ready summary. Use when the user says "close session", "wrap up", "we're done for today", or invokes the CFD session-close ritual. Implements ADR-018.
---

Run the Context-First Development session-close ritual (ADR-018). This is
**non-negotiable** — a session that ends without step 1 leaves the next session
with stale context. Do all of the following, in order:

1. **Update `docs/CURRENT_STATUS.md`:**
   - Move completed items from "In Progress" to "Recently Completed".
   - Add anything still pending or newly surfaced this session.
   - Update "Known Issues / Open Questions" if anything new appeared.
   - Re-rank "Next Priorities".
   - Update the "Last updated" date to today.
   - If work was tracked as a GitHub issue (ADR-021), reference it by `#N`.

2. **Update `docs/CONVENTIONS.md`** if any convention was clarified or a pattern
   was corrected this session (ADR-016). Do not leave corrections only in chat
   history — they will be lost next session.

3. **If a significant decision was made informally** (in chat, in passing),
   propose creating an ADR via the `new-decision` skill before closing
   (ADR-013). Do not let an implicit decision ship undocumented.

4. **Ship `docs/` context changes in the same commit/PR as the session's code.**
   Exception specific to this project: `docs/CURRENT_STATUS.md` is local-only
   (gitignored), so it is updated locally every session but never travels in a
   PR — only `CONVENTIONS.md` and ADRs do.

Do **not** end the session without completing step 1.

After completing the ritual, output a one-paragraph session summary suitable for
pasting into a PR description (Spanish is fine here per ADR-014 — PR descriptions
are not reloaded into context).

If a PR was opened from this session, the natural next step is the `review-pr`
skill — it cross-checks the diff against the project's checklist (ADR-020).
