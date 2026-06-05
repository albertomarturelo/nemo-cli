# ADR-002: Tech Stack — Node.js 20 + TypeScript + commander

## Status

Superseded by ADR-004

## Date

2026-05-01

## Context

The CLI needs to:

- Make HTTPS calls against a JSON REST API.
- Persist a small piece of state (a bearer token) per machine / per user.
- Be installable on developer macOS / Linux machines and, eventually, distributed.
- Be approachable for the user, who works primarily on web/JS-adjacent tooling.

The choice of language and runtime sets a long tail of downstream constraints
(packaging, tests, dependency surface), so it is worth nailing down before any
feature code is written.

## Decision

- **Runtime:** Node.js ≥ 20 (LTS). Native `fetch`, native ESM, stable.
- **Language:** TypeScript 5.6 in strict mode, compiled with `tsc` to ESM in `dist/`.
- **CLI framework:** `commander` v12.
- **Config loading:** `dotenv` for `.env`.
- **Persistent state:** `conf` v13 for the cached token.
- **Output styling:** `chalk` v5.
- **Tests:** `vitest`.

No HTTP client library is added; the platform `fetch` is sufficient.

## Alternatives Considered

- **Bun + TypeScript.** Faster startup and native TS, but the ecosystem is still
  catching up on some workflows (single-binary distribution, certain Node-only
  modules). Rejected for the foundation; can be revisited once the CLI is feature-
  complete and we measure startup time as a real problem.
- **Python + Click / Typer.** Excellent CLI ergonomics, but introduces a Python
  toolchain dependency the user does not currently maintain, and ships heavier when
  bundled. Rejected.
- **Go + cobra.** Best-in-class for distributable single-binary CLIs. Rejected for
  now because the project is in rapid-iteration mode and the user is more productive
  in TypeScript.
- **oclif (Salesforce CLI framework).** More structure (plugins, scaffolds), but
  significantly heavier than `commander` for the current command count. Rejected as
  premature.

## Consequences

- Distribution path is `npm` (eventually `npm publish` or `npx`-style usage).
- Native ESM means relative imports must use the `.js` extension in TypeScript
  source — codified in `docs/CONVENTIONS.md`.
- No bundler is needed; `tsc` output runs directly. If startup latency becomes a
  concern, `esbuild` / `tsup` is a low-risk swap-in.
- Switching to Bun later is plausible because the dependency list is intentionally
  small and standards-based.
