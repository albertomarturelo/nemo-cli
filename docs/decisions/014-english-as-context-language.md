# ADR-014: English as the Context Language

## Status

Accepted

## Date

2026-06-16

## Context

`CLAUDE.md` already mandates "English for all model-facing context". This ADR
formalizes that as a decision and adopts the CFD shareable-catalog entry
`adrs/ai-workflow/english-as-context-language.md`. The author works in Spanish,
so this is a deliberate choice, not a default.

LLM tokenizers (Anthropic's and others') are optimized for English. The same
information in Spanish can consume 20–40% more tokens, and non-English context
shows higher hallucination rates on several public benchmarks. In files loaded
every session (`CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/STACK.md`,
`docs/CONVENTIONS.md`) that overhead compounds.

## Decision

All technical context written for the agent is in English:

- `CLAUDE.md`
- `docs/**/*.md` (ARCHITECTURE, STACK, CONVENTIONS, CURRENT_STATUS, decisions)
- `.claude/skills/**/SKILL.md`
- ADRs
- Code identifiers and code comments

Team communication that is *not* reloaded into context every session — PR
descriptions and chat with the user — may be in Spanish, the author's working
language.

## Alternatives Considered

- **Write context in Spanish.** Honest about the author's language; costs
  20–40% more tokens per session forever. Rejected.
- **Auto-translate on session start.** Adds a build step; translation drift
  becomes a context-integrity problem. Rejected.
- **Maintain both languages.** Doubles the maintenance surface and guarantees
  the two will drift. Rejected.

## Consequences

- A language-detect check on `docs/**/*.md` and `CLAUDE.md` returns English with
  high confidence — a check the `/validate-context` skill can run.
- The author writes context in a non-native language; the patterns are simple
  and repetitive, and the agent can translate user prompts on demand.
- The boundary is explicit: anything the model reloads each session is English;
  anything that lives only in GitHub or chat may be Spanish.
