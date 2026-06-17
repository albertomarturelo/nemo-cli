---
description: Pick up a nemo-cli GitHub Issue as the focus of this session — fetch it, parse its fixed CFD sections, pre-load the ADRs it names, skim the pattern to mirror, and summarize the objective and acceptance checklist without scanning target files. Use when the user says "start issue", "work on #N", "pick up", or passes an issue number. Implements ADR-021.
---

Pick up a tracker issue as this session's focus (ADR-021). Orient from the issue
body and its ADRs — do not scan code at this step.

1. **Fetch the issue.** The user passes a number; if not, ask which.

   ```bash
   gh issue view <n>
   ```

2. **Parse the fixed sections** (ADR-021): `Context`, `Target`, `ADRs to load`,
   `Acceptance criteria`, `Reproduction` (fixes only), `Estimated sessions`. If
   a required section is missing, **STOP** — tell the user the issue is
   malformed and propose fixing it via `gh issue edit <n>`. Do not infer.

3. **Read each ADR listed in `ADRs to load`** from `docs/decisions/`. These set
   the constraints the implementation must satisfy.

4. **Read the `Pattern to mirror` file ONCE for shape.** Skim, don't study — the
   goal is to know what the produced code should look like.

5. **Do NOT read the `Target` files yet.** They are where the work *goes*, not
   where context comes *from*; reading them now is wasted tokens.

6. **Summarize for the user:**
   - **Objective** (one line, from `Context`).
   - **Acceptance checklist** (verbatim from `Acceptance criteria` — the DoD).
   - **ADRs loaded** and what each constrains.
   - **Target paths** you will write to.
   - **Pattern to mirror.**

7. Ask: **"Ready to start?"** If `Estimated sessions` > 1, remind the user the
   issue should be decomposed and offer to split it via `issue-new` (ADR-019).

**Token discipline:** the issue body + ADRs are the spec. Code reading happens
when implementation starts, not during orientation.
