# ADR-026: Auth session layer — encapsulate login and expose status

## Status

Accepted

## Date

2026-06-26

## Context

After ADR-025 the `login` command orchestrated `sign_in()` + `set_token()`
directly, and `whoami` only knew whether a token was cached. We want a
`nemo status` command that reports a richer session state — logged out, active,
expiring, or expired — derived from the cached token's `exp` claim.

That orchestration ("what it means to log in") and the state logic ("what is the
current session") do not belong in the command layer, which is meant to be thin
(see `ARCHITECTURE.md`), and should not be duplicated between commands. The auth
package already owns the pieces — `service` (raw `SignIn` / `RefreshToken` HTTP),
`token_store` (cache), and `jwt` (read-only `exp` peek) — but nothing composes
them into a session-level API.

## Decision

- **Introduce `nemo_cli.auth.session`**, an orchestration module above `service`
  and `token_store`:
  - `log_in(username, password) -> None` — `sign_in()` then `set_token()`. The
    `login` command becomes a thin wrapper that only collects credentials
    (prompt or flags) and calls this.
  - `status() -> AuthStatus` — a read-only state derived from the cached token's
    `exp`: `LOGGED_OUT` (no token), `EXPIRED` (`exp <= now`), `EXPIRING` (within
    the proactive 60s window), `ACTIVE` otherwise. A token we cannot decode is
    treated as `ACTIVE`, mirroring the refresh-timing helper — the server stays
    the authority and the reactive `401` path catches a token it actually
    rejects.
- **Add a `nemo status` command** that renders `auth.session.status()`. It is
  read-only and makes no network call.
- **Promote the 60s proactive-refresh threshold to a public constant**
  `PROACTIVE_REFRESH_SECONDS` in `auth.jwt` — the single source of truth shared
  by `api.client` (renewal timing, ADR-012) and `auth.session` (the `EXPIRING`
  boundary), so the two cannot drift.
- `service` keeps only the raw HTTP calls; `token_store` keeps only persistence.
  No new dependency.

## Alternatives Considered

- **Put `log_in` / `status` on `service`.** Rejected: `service` is the narrow,
  allowed direct-HTTP exception (ADR-003 / CONVENTIONS); mixing token-store
  orchestration into it blurs that boundary.
- **Keep the logic in the command layer.** Rejected: commands are thin
  orchestration; login/status logic there is untestable without the CLI and
  cannot be reused.
- **Reuse `whoami` for status.** Rejected: `whoami` answers *who* (identity,
  deferred to the Rich whoami work unit) while `status` answers *session state*.
  Separate concerns → separate commands.
- **A boolean status.** Rejected: the JWT `exp` is already on hand; the richer
  four-state result is cheap, more useful, and feeds a future "expires in N min"
  display.

## Consequences

- `login` shrinks to credential collection plus one call; the auth orchestration
  is unit-tested directly in `tests/auth/test_session.py`, independent of the CLI.
- `nemo status` gives users and scripted agents a quick session check with no
  network round-trip.
- One source of truth for the 60s threshold (`auth.jwt.PROACTIVE_REFRESH_SECONDS`);
  `api.client` imports it instead of a private copy.
- `status()` reports, it does not renew. An `EXPIRING` token is renewed
  transparently on the next real API call (ADR-012); `EXPIRED` / `LOGGED_OUT`
  require `nemo login`.
- The auth layer now has four modules (`service`, `token_store`, `jwt`,
  `session`); `ARCHITECTURE.md`'s Auth row and layer description are updated.
