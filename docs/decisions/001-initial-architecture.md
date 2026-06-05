# ADR-001: Initial Layered Architecture

## Status

Accepted

## Date

2026-05-01

## Context

nemo-cli starts as a thin client over the Vector Capital portal API. It is expected
to grow as the user adds subcommands (portfolio queries, transactions, reports,
etc.). Two failure modes are likely if the architecture is not set up explicitly at
the start:

1. **HTTP and auth concerns spread across command handlers.** Each new command would
   call `fetch` directly and re-implement token retrieval, leading to inconsistent
   error handling and duplicated logic — exactly the pain the user wants to avoid by
   adopting CFD.
2. **Configuration coupled to feature code.** Reading `process.env` from anywhere
   makes commands hard to test and easy to break when env names change.

## Decision

Adopt a small but explicit layered structure with a single allowed direction of
dependency (top → bottom):

```
Entry (index.ts, cli.ts)
  └── Commands (src/commands/*)
        └── API client (src/api/client.ts)
              ├── Auth service (src/auth/auth-service.ts)
              ├── Token store (src/auth/token-store.ts)
              └── Config (src/config/env.ts)
```

Rules:

- Command handlers never call `fetch` directly; they go through `apiFetch()`.
- `apiFetch()` is the only place that injects `Authorization` and handles the
  `401 → refresh → retry` flow.
- Only `src/config/env.ts` reads `process.env`.

## Alternatives Considered

- **Flat `src/` with no enforced layering.** Faster to start, but every new command
  would re-derive the auth flow. Rejected because the project is explicitly being
  built to grow with multiple commands.
- **Hexagonal / ports-and-adapters.** Provides clean testability boundaries but
  requires interface-and-adapter pairs for what is currently a single HTTP backend
  and a single token store. Rejected as premature abstraction; revisit if a second
  backend (e.g. a different API or a mocked replay layer) becomes necessary.
- **Framework-based CLI (oclif, NestJS-CLI).** Brings opinionated structure but adds
  a heavy runtime and a learning surface that buys nothing for a project of this
  size. Rejected.

## Consequences

- New subcommands have a recipe: create a file in `src/commands/`, register it in
  `src/cli.ts`, call `apiFetch()` for any portal call. Onboarding new code is fast.
- Adding a non-HTTP side effect (e.g. writing reports to disk) does not fit cleanly
  into the current layers and will require an ADR amendment.
- Testing strategy follows directly: mock `fetch` to test `apiFetch()`; mock
  `apiFetch` to test command handlers; unit-test `token-store` and `env` directly.
