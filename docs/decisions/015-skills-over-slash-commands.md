# ADR-015: CFD Procedures Are Claude Skills, Not Slash Commands

## Status

Accepted

## Date

2026-06-16

## Context

CFD's automation procedures (session start/close, new-decision, issue new/start,
validate-context, review-pr) need an invocation primitive. The CFD shareable-
catalog entry `adrs/ai-workflow/slash-commands-vs-skills.md` calls both valid
and recommends **slash commands** for the mandatory-at-boundary procedures
(`session:start`, `session:close`) on determinism grounds, allowing Skills
"UNLESS the team has explicitly justified Skills with a per-project addendum
ADR". This ADR is that addendum: nemo-cli already ships its procedures as Skills
(`start-session`, `status`, `new-decision`, `validate-context`) and this records
why, including for the session boundaries.

## Decision

Implement every CFD procedure as a **Claude Skill** under
`.claude/skills/<name>/SKILL.md` — including the mandatory boundaries
(`start-session`, `close-session`). Rationale for choosing Skills even at the
boundary, against the catalog's default:

1. **Solo project.** There is no team-coordination cost to model-discovered
   invocation; the catalog's determinism argument is weakest here.
2. **Low friction, reliable discovery.** The Skill `description:` fields are
   written so the model surfaces them from natural phrasing ("start session",
   "close out", "review this PR").
3. **Claude-Code-only.** The portability argument for slash commands does not
   apply — there is no second agent to translate to.

If a non-Claude agent is ever added to the toolbox, migrate the boundary
procedures to slash commands; the migration is mechanical.

## Alternatives Considered

- **Slash commands only.** Buys determinism and portability but adds typing
  friction with no payoff on a solo, Claude-only project. Rejected for now.
- **Mixed (Skills for discovery-friendly procedures, slash commands for
  boundaries).** The catalog's recommended default; rejected to keep a single
  primitive and a single mental model.

## Consequences

- All CFD procedures live under `.claude/skills/`; `docs/CONVENTIONS.md` records
  that Skills own every procedure (no half-implemented slash-command duplicates).
- Accepts the catalog's noted risk: a Skill is model-discovered, so it offers no
  hard gate if the close ritual is forgotten. Mitigated by the non-negotiable
  critical rule in `CLAUDE.md` (see ADR-018) plus the `close-session` skill's
  discoverable description.
- The set of Skills is the project's CFD surface: `start-session`, `status`,
  `close-session`, `new-decision`, `validate-context`, `review-pr`,
  `issue-new`, `issue-start`.
