# ADR-012: Refresh-Token Flow — Proactive Renewal + Reactive Fallback

## Status

Accepted (refines ADR-003)

## Date

2026-05-02

## Context

ADR-003 set the original auth strategy: env-var credentials → `SignIn` →
cache the JWT → on `401` clear the cache and `SignIn` again. That works
but has two well-understood shortcomings, both flagged in ADR-003's own
"Consequences":

1. **Credentials are sent on every renewal.** A token lives ~20 minutes
   (`exp - iat = 1200s`); any longer-running session re-authenticates
   with the username/password every time. The principle of "use
   credentials only when you have to" is violated.
2. **Every renewal pays a failed-401 round trip.** The current path
   only refreshes *after* a request comes back `401` — the failed
   request is wasted.

Vector exposes a renewal endpoint:

```
GET /api/publicapi/shared/auth/RefreshToken
Authorization: Bearer <current-jwt>
```

The response body is a JSON-encoded string containing a freshly minted
JWT of the same shape as `SignIn`, with another ~20-minute window. There
is **no** separate "refresh token" in the OAuth-2 sense; the endpoint
re-issues an access token using the bearer the caller already has. The
verb being `GET` is unusual (creating a resource is conventionally POST)
but is the API as shipped — not our problem to fix.

The future Chilean-investing-research agent is the strongest motivator:
agents tend to make many calls in succession, far past the 20-minute
window, and we don't want every renewal to either re-send credentials or
pay a failed round trip.

## Decision

Layer two flows on top of ADR-003. **ADR-003 stands**: `SignIn` is the
bootstrap and the last resort. ADR-012 adds Refresh in front of it.

### 1. Proactive renewal (the common path)

In `api_request._ensure_token`, before sending any request, decode the
cached JWT's `exp` claim (read-only — we do **not** verify the
signature; the server is the authority). If the token expires within
**60 seconds**, call `RefreshToken` to get a new one and cache it before
proceeding. The threshold is a balance between:

- Too small → races the actual expiry, the request still 401s.
- Too large → unnecessary refreshes on short-lived CLI invocations.

60s is loose enough to absorb modest clock skew and any latency the
refresh call itself adds. The threshold is hardcoded; if it ever needs
tuning we expose it as an env var in a follow-up.

### 2. Reactive fallback (the edge cases)

If a request returns `401` *despite* the proactive check (the cached
token was actually invalid for reasons other than expiry — server
revoked, schema changed, clock badly off), the path is:

1. Call `RefreshToken` with the now-stale token. If it succeeds, retry
   the original request once with the new token.
2. If `RefreshToken` itself fails (token completely caducated, e.g. the
   CLI hasn't run in days), fall back to `SignIn` with credentials,
   cache the result, retry once.
3. A second `401` after the full-bootstrap retry is surfaced as an
   error.

This keeps the `api_request` contract from ADR-001 / ADR-003 ("centralise
auth, retry once at most") intact while making the renewal path cheaper
and more secure.

### 3. Client-side JWT parsing helper

A small `nemo_cli.auth.jwt.is_expiring_within(token, seconds) -> bool`
helper splits the JWT into its three parts, base64-URL-decodes the
payload, and reads `exp`. Returns `False` defensively on any decode
error — a token we can't read is treated as fresh, and the reactive
401 path catches it if the server disagrees. We do not add `pyjwt` as a
dependency for ~25 lines of stdlib code.

## Alternatives Considered

- **Proactive only (no reactive fallback).** Cleaner logic but loses the
  safety net for tokens that go stale for non-`exp` reasons (server
  revocation, clock drift larger than the threshold, schema change).
  Rejected.
- **Reactive only (refresh on 401, no proactive).** Always pays one
  failed round trip per renewal. Acceptable for human use but bad for
  agent workloads. Rejected once the agent integration was on the
  roadmap (it is, per
  `memory/project_future_chilean_research_agent.md`).
- **Always send through `RefreshToken` first, never re-`SignIn`.**
  Tempting, but if the token is months stale the server will reject
  Refresh and we'd have no way back into the system. Keeping `SignIn`
  as the last resort is mandatory.
- **Use `pyjwt` for the decode.** Adds a dependency for a 25-line
  function. The library would also verify the signature, which we
  *don't want* — we are not the authority on whether the token is
  valid; we just want to peek at `exp` for refresh-timing. Rejected.
- **Configurable refresh threshold via env var.** YAGNI for now. The
  60s value is documented and easy to change if real-world usage
  demands tuning.

## Consequences

- **Credentials touch the wire only on bootstrap and on a Refresh
  failure.** Steady-state long-running sessions never re-send
  `NEMO_USERNAME` / `NEMO_PASSWORD`. ADR-003's spirit ("use credentials
  only when you have to") is now actually enforced.
- **The common-path renewal eliminates the failed-401 round trip.**
  Net latency improvement for any session that crosses the 20-minute
  boundary.
- **`api_request` gains complexity.** The 401 handler is now a
  three-step ladder (refresh → signin → propagate). It is fully unit-
  tested (mocked `httpx`); the behaviour is centralised in one place
  per ADR-001.
- **Token-store invariant unchanged.** We always cache the *latest*
  bearer; refresh just replaces the value. Nothing downstream needs to
  change.
- **`nemo logout` still does what it says.** `clear_token()` removes
  the cached JWT; the next request triggers `SignIn` (no Refresh path,
  because there is no token to refresh).
- **The JWT-decode helper is intentionally read-only.** It does not
  verify the signature. This is the correct posture for refresh
  *timing* decisions: server is the authority on validity; we just
  want a hint for when to renew. The reactive path catches anything we
  miss.
- ADR-003 stays Accepted; this ADR refines its renewal flow without
  superseding it. The original strategy (env-var credentials, cached
  bearer, single retry on `401`) is preserved verbatim — Refresh just
  takes the place of `SignIn` as the *first* attempt on `401`, and runs
  proactively before requests when the cached `exp` is close.

### Empirical findings (verified against production)

These are confirmed properties of the live endpoint, captured here so a
future reader doesn't re-discover them:

- **`RefreshToken` is a `GET`, not a `POST`.** Semantically odd
  (creating a resource is conventionally POST), but as-shipped. The
  test in `tests/auth/test_service.py::TestRefreshToken::test_uses_get_method`
  pins this so a regression to POST would fail loudly.
- **The response body is a JSON-encoded string**, not an object. The
  parser accepts `"<jwt>"` and rejects `{"token": "<jwt>"}`.
- **The renewed token is a full HS256 JWT** with the same header and
  payload shape as `SignIn`. The `jti` is fresh on every refresh (so
  successive renewals are observable), and the `exp - iat` lifetime is
  the same **20 minutes (1200s)** as `SignIn`. The endpoint is a
  same-class renewal, not a long-lived refresh-token in the OAuth-2
  sense.
- **`RefreshToken` rejects bearers that are already past their `exp`
  with `401 Unauthorized`.** This is the practical reason the proactive
  60s threshold exists — once a token is fully expired, only `SignIn`
  with credentials can revive the session. The reactive fallback in
  `api_request` covers exactly this case: corrupted / expired bearer
  → `401` → Refresh also fails → SignIn → retry succeeds. Verified by
  `scripts/verify_reactive_fallback.py`.
- The 60s proactive threshold is generous enough to cover both modest
  clock skew and the latency of the refresh call itself.
