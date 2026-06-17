---
description: Create a self-sufficient nemo-cli unit of work as a GitHub Issue with the fixed CFD body template (Context, Target, ADRs to load, Acceptance criteria, Reproduction, Estimated sessions). Use when the user asks to "open an issue", "create a work item", "plan a task", or describes new work to be tracked. Implements ADR-021.
---

Guide the user through creating a GitHub Issue with the fixed body template from
ADR-021. The completeness of this issue determines how cheaply the next session
starts — be thorough here. Ask, in order, and confirm each answer:

1. **Type.** `feature` | `fix` | `chore` | `spike` | `docs`.
2. **Title.** Imperative, ≤ 80 chars, English (ADR-014). e.g. "Add `nemo
   portfolio export` command".
3. **Context.** 2–4 sentences: the trigger and the user-visible outcome.
4. **Target location.** Concrete paths. For a new subcommand, name the module
   and proposed file (e.g. `src/nemo_cli/commands/<verb>.py` — new file —
   registered in `src/nemo_cli/cli.py`).
5. **Pattern to mirror.** An existing file the implementation should copy in
   shape and naming (e.g. `src/nemo_cli/commands/instruments.py`). Flag
   explicitly if no analog exists.
6. **ADRs to load.** ADR numbers the agent must read first. If a needed decision
   is not yet an ADR, **STOP and run the `new-decision` skill** — implementing
   an undocumented decision is forbidden by ADR-013.
7. **Acceptance criteria (DoD).** Markdown `[ ]` items covering all three of:
   behaviour at the end, tests (kind + location under `tests/` mirroring the
   package tree, `respx`/`CliRunner` per CONVENTIONS, coverage ≥ 95%), and docs
   updated (CONVENTIONS, ADRs, README, CHANGELOG per ADR-007).
8. **Reproduction steps.** `fix` only — a minimal repro the agent can run.
9. **Estimated sessions.** `1` | `2–3` | `4+`. If > 1, **propose decomposing
   into sub-issues before continuing** (ADR-019).
10. **Labels.** The type plus any component (`auth`, `instruments`, `portfolio`,
    `api`, `ci`, …).

Then generate the body using the fixed template — do not change section order or
names; `issue-start` parses by header:

```markdown
## Context
<step 3>

## Target
- Files / dirs: <step 4>
- Pattern to mirror: <step 5>

## ADRs to load
- [ADR-NNN](docs/decisions/NNN-*.md)

## Acceptance criteria
- [ ] <step 7>

## Reproduction (fixes only)
<step 8 — OR omit this section entirely if not a fix>

## Estimated sessions
<step 9>
```

Then create it:

```bash
gh issue create --title "<step 2>" --body "<body above>" --label "<type>,<labels>"
```

Output the issue URL when done. English for the issue body (ADR-014); the issue
comment thread may be Spanish.
