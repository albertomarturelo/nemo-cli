---
description: Capture a new architecture decision as an ADR file in docs/decisions/ before any implementation code is written. Use when the user is about to make a significant technical choice (stack, pattern, library, branching strategy, infra) or asks to "document a decision", "open an ADR", or "record this as an ADR".
---

Help the user document a new architecture decision as an ADR. Do **not** write any
implementation code during this skill — its only output is the ADR file and the
updated index.

Steps:

1. **Elicit the decision.** Ask the user, one focused question at a time:
   - What problem is being solved? (the *context*)
   - What is the proposed change? (the *decision*)
   - What other options were considered, and why are they being rejected?
   - What becomes easier and what becomes harder as a result?

   Do not move on until you have crisp one-paragraph answers for each.

2. **Pick the next ADR number.** List `docs/decisions/` and choose the next zero-
   padded integer (e.g. if the highest is `005`, the new ADR is `006`).

3. **Write the ADR file** at `docs/decisions/<NNN>-<kebab-case-title>.md` using
   this exact template:

   ````markdown
   # ADR-<NNN>: <Title>

   ## Status

   Accepted

   ## Date

   <YYYY-MM-DD — today's date>

   ## Context

   <One or two paragraphs describing the problem.>

   ## Decision

   <The decision itself, stated as imperatives.>

   ## Alternatives Considered

   - **<Option A>.** <Why it was rejected.>
   - **<Option B>.** <Why it was rejected.>

   ## Consequences

   <Bullets describing what changes — positive and negative — as a result.>
   ````

4. **Update `docs/decisions/_index.md`** by appending a new row to the table.
   Preserve column alignment.

5. **Stop.** Do not modify source code in this skill. Tell the user the ADR is
   ready and that the next step is to implement it (or to invoke a separate task
   to do so).
