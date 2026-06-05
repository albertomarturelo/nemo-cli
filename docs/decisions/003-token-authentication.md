# ADR-003: Token-Based Authentication via Environment Variables

## Status

Accepted

## Date

2026-05-01

## Context

Vector Capital exposes a public `SignIn` endpoint that exchanges a `userName` /
`password` pair for a bearer token. The user has stated that:

- Credentials must be supplied via environment variables, not interactively prompted.
- The CLI will be invoked repeatedly (in scripts and ad-hoc terminal use), so
  authenticating on every command would add unnecessary latency and load on the
  Vector backend.

The request contract is:

```http
POST https://portalclientes.vectorcapital.cl/api/publicapi/shared/auth/SignIn
Content-Type: application/json

{ "userName": "...", "password": "..." }
```

The response contract — verified against a real call on 2026-05-01 — is:

```jsonc
{
  "token": "<JWT>",
  "user": {
    "userId": "<uuid>", "userName": "<email>", "nombre": "...",
    "role": ["Cliente"], "modulo": ["FrontOffice"], "idNegocio": [<int>, ...],
    "esPersonaJuridica": false, /* ... */
  },
  "systemConfig": {
    "cierreSistema": "<ISO datetime>", "codMonedaTipoCambioSistema": "CLP",
    "sistemaBloqueado": false, /* ... */
  }
}
```

The JWT carries standard claims; observed `exp - iat = 1200s`, so the token lives
~20 minutes from issuance.

## Decision

- Read credentials from `NEMO_USERNAME` and `NEMO_PASSWORD` (loaded via
  `python-dotenv`). Fail loudly at the start of any command that needs them if
  either is missing.
- After a successful `SignIn`, persist the bearer token as JSON at
  `platformdirs.user_config_path("nemo-cli") / "token.json"` (per-user file under
  the OS config directory). Credentials themselves are **never** persisted.
- All Vector API calls go through `api_request()` in `nemo_cli.api.client`, which:
  1. Reads the cached token; if absent, performs `SignIn` and caches the result.
  2. Sends the request with `Authorization: Bearer <token>`.
  3. On `401`, clears the cached token, performs `SignIn` again, and retries the
     request **once**. A second `401` is surfaced as an error.
- The `nemo login` command exists to force a fresh sign-in (useful for warm-up and
  for diagnosing credential issues). `nemo logout` clears the cached token.
- The Vector API base URL is **hardcoded** as a constant in `nemo_cli.config`. No
  env override is supported (see ADR-004 for the rationale tied to the Python
  rewrite).

## Alternatives Considered

- **Authenticate on every command.** Simplest, but adds a full HTTPS round-trip per
  invocation and unnecessary load on the Vector portal. Rejected.
- **Persist credentials encrypted at rest.** The user is explicit that credentials
  belong in env vars; storing them in our own file (encrypted or not) would
  duplicate the secret and broaden the attack surface. Rejected.
- **Time-based proactive token refresh.** Would be ideal, but requires knowing the
  token TTL. We do not have it documented yet. Reactive refresh on `401` is the
  correct conservative starting point; a follow-up ADR can switch to proactive
  refresh once we observe the real expiry behaviour.
- **OS keychain (`keyring` etc.).** More secure for credentials, but credentials
  are not stored at all in this design — only a short-lived token. The added
  dependency is not worth it for the token alone.

## Consequences

- The cached token file is per-user. If the user runs the CLI as a different OS user
  (e.g. in CI), they will need to re-authenticate; this is intentional.
- The first call after token expiry costs an extra round-trip (the failed request
  plus the refresh plus the retry). This is acceptable.
- The response shape is now confirmed. `nemo_cli.auth.service.sign_in` parses
  the top-level `token` string strictly; if Vector changes the contract the call
  fails loudly rather than silently degrading.
- Token TTL is short (~20 minutes). Reactive refresh on `401` remains correct,
  but a follow-up ADR may introduce proactive refresh that decodes the JWT's
  `exp` claim. Tracked in `docs/CURRENT_STATUS.md`.
- The `user` and `systemConfig` blocks in the `SignIn` response carry data that
  later commands may want (nombre, role, idNegocio, sistemaBloqueado). They are
  intentionally not persisted today — surface them via dedicated commands or
  cache them alongside the token in a future change.
- If Vector ever introduces a refresh-token mechanism, this ADR will be
  superseded rather than amended.
