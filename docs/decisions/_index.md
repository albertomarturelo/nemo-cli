# Architecture Decision Records

| ID  | Title                                                                  | Status                | Date       |
|-----|------------------------------------------------------------------------|-----------------------|------------|
| 001 | [Initial layered architecture](001-initial-architecture.md)            | Accepted              | 2026-05-01 |
| 002 | [Tech stack: Node.js + TypeScript + commander](002-tech-stack.md)      | Superseded by ADR-004 | 2026-05-01 |
| 003 | [Token-based authentication via env vars](003-token-authentication.md) | Accepted (credential source & 401 flow amended by ADR-025) | 2026-05-01 |
| 004 | [Switch CLI stack to Python](004-switch-to-python-stack.md)            | Accepted              | 2026-05-01 |
| 005 | [GitHub Flow as branching strategy](005-github-flow-branching.md)      | Accepted (§4 amended by ADR-022) | 2026-05-01 |
| 006 | [Instruments domain: local and international markets](006-instruments-domain.md) | Accepted    | 2026-05-01 |
| 007 | [Versioning policy: SemVer + Keep a Changelog](007-versioning-and-changelog.md)  | Accepted    | 2026-05-01 |
| 008 | [Portfolio domain: holdings and computed aggregates](008-portfolio-domain.md)    | Accepted    | 2026-05-01 |
| 010 | [Instrument price history: nemo instruments prices](010-instrument-price-history.md) | Accepted | 2026-05-01 |
| 011 | [Portfolio movements with classification and dividend parsing](011-portfolio-movements.md) | Accepted | 2026-05-01 |
| 012 | [Refresh-token flow: proactive renewal + reactive fallback](012-refresh-token-flow.md) | Accepted | 2026-05-02 |
| 013 | [Write the ADR before implementing the decision](013-adr-before-implementing.md) | Accepted | 2026-06-16 |
| 014 | [English as the context language](014-english-as-context-language.md) | Accepted | 2026-06-16 |
| 015 | [CFD procedures are Claude Skills, not slash commands](015-skills-over-slash-commands.md) | Accepted | 2026-06-16 |
| 016 | [Document the convention, not just the fix](016-document-corrections-not-fixes.md) | Accepted | 2026-06-16 |
| 017 | [Atomic task instructions for AI sessions](017-atomic-task-instructions.md) | Accepted | 2026-06-16 |
| 018 | [The session-close ritual](018-session-close-ritual.md) | Accepted | 2026-06-16 |
| 019 | [Short sessions over long ones](019-short-sessions-over-long.md) | Accepted | 2026-06-16 |
| 020 | [Review the PR against context, not intent discovery](020-pr-review-against-context.md) | Accepted | 2026-06-16 |
| 021 | [Work units live in GitHub Issues with a fixed body template](021-work-units-external-tracker.md) | Accepted | 2026-06-16 |
| 022 | [No AI-attribution metadata in commits and PRs](022-no-ai-attribution.md) | Accepted (amends ADR-005 §4) | 2026-06-16 |
| 023 | [Continuous Integration via GitHub Actions](023-continuous-integration.md) | Accepted | 2026-06-16 |
| 024 | [Repository governance: security, contribution, templates](024-repository-governance.md) | Accepted | 2026-06-16 |
| 025 | [Interactive login replacing env-var credentials](025-interactive-login.md) | Accepted (amends ADR-003; command surface amended by ADR-027) | 2026-06-26 |
| 026 | [Auth session layer: encapsulate login and expose status](026-auth-session-layer.md) | Accepted (command surface amended by ADR-027) | 2026-06-26 |
| 027 | [Group auth commands under `nemo auth`; remove `whoami`](027-auth-command-group.md) | Accepted (amends ADR-025/026 surface) | 2026-06-26 |

## CFD methodology ADRs

ADRs 013–021 were adopted from the [Context-First Development shareable ADR
catalog](https://github.com/albertomarturelo/context-first-development/tree/main/adrs)
on 2026-06-16. They record the *process* decisions behind how this project is
developed (001–012 record *product/architecture* decisions). All but ADR-021
formalize practices nemo-cli already followed. Catalog entries that contradict
existing decisions were deliberately **not** adopted: repository-pattern and
layered-clean-architecture (covered by ADR-001), integration-over-mocks
(contradicts the `respx` testing convention in `CONVENTIONS.md`), and
trunk-based-with-release-candidates (contradicts ADR-005, GitHub Flow).
