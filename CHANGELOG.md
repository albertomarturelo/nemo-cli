# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
Versioning policy and release process: [ADR-007](docs/decisions/007-versioning-and-changelog.md).

## [Unreleased]

## [0.2.0] - 2026-05-02

This release completes the planned read-only data surface (instrument price
history + portfolio movements with classification) and replaces the
credentials-on-every-401 renewal flow with a proper proactive-refresh +
reactive-fallback ladder.

### Added

- **Instrument price history.** `nemo instruments prices --id <ID>` returns
  ~1 year of daily prices for a local Chilean instrument
  (`GET /api/frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento`),
  with computed stats (first/last, min/max with dates, mean, total return %,
  daily-return σ — not annualised) and an ASCII sparkline of the trajectory.
  `--json` emits the full point series plus stats. **Local instruments only**:
  the upstream endpoint does not serve international assets. (ADR-010)
- **Portfolio movements with classification.** `nemo portfolio movements
  --desde <YYYY-MM-DD> --hasta <YYYY-MM-DD>` queries
  `GET /api/frontoffice/shared/MovimientosCajas/Movimientos` and parses each
  movement description into a structured `kind` (`dividend`, `buy`, `sell`,
  `commission`, `cash_in`, `cash_out`, `other`) plus, when applicable, a
  typed `DividendInfo` (ex-date, nemotécnico, per-unit amount with Chilean
  decimal-comma → float) or `TradeInfo` (nemotécnico, side). The service
  computes per-nemotécnico aggregates (`by_dividend`, `by_trade`) and global
  totals at the boundary, so consumers get the dividend-yield contract
  precomputed. Defaults: `--desde` 1 year ago, `--hasta` today,
  `--account-id` 0 (all). `--json` envelope:
  `{ desde, hasta, summary: { totals…, by_dividend, by_trade }, buckets: [{ bucket_id, name, summary, movements: [{ kind, dividend?, trade?, … }] }] }`.
  Note: the upstream endpoint is markedly slower than the rest of the
  surface; the call uses a **180s timeout** (vs. the 15s default elsewhere),
  documented in `docs/CONVENTIONS.md` → HTTP → Timeouts. (ADR-011)
- **Unit-test suite (203 tests, ~98% line coverage).** Mirrors the package
  tree under `tests/` with `respx` mocking `httpx` at the transport layer
  (no real network calls), shared fixtures in `tests/conftest.py` (env
  credentials, isolated token store), and `typer.testing.CliRunner` driving
  the CLI. Pure parsers, aggregators, and HTTP-flow services are at 100%;
  the only stable misses are entry-point code and a few display branches.
  No CI/CD wiring yet — tests run locally with `pytest`. (CONVENTIONS.md
  updated.)
- **Live verification scripts** under `scripts/`:
  - `verify_refresh.py` — happy-path verification of the RefreshToken
    endpoint against production (decodes both bearers, asserts six
    invariants, reports the empirical TTL).
  - `verify_reactive_fallback.py` — corrupts the cached token and exercises
    the full `corrupted → 401 → Refresh fails → SignIn → retry → 200`
    ladder against a real endpoint.

### Changed

- **Authentication renewal flow** layered on top of ADR-003: `api_request`
  now uses Vector's `RefreshToken` endpoint to renew the bearer instead of
  re-sending credentials on every renewal (ADR-012).
  - **Proactive:** before each request, decode the cached JWT's `exp` claim
    (read-only — signature is not verified). If it expires within **60s**,
    call `GET /api/publicapi/shared/auth/RefreshToken` and use the renewed
    bearer.
  - **Reactive:** on a `401` despite a fresh-looking token, try
    `RefreshToken` first; only fall back to `SignIn` if the refresh itself
    fails (token is too stale or otherwise invalid).
  - Net result: credentials (`NEMO_USERNAME` / `NEMO_PASSWORD`) touch the
    wire only on bootstrap and as a last resort.
  - New module `nemo_cli.auth.jwt` with a stdlib-only
    `is_expiring_within(token, seconds)` helper. No new dependency.
  - Empirical findings (verified against production, documented in
    ADR-012's Consequences): the renewed token is a full HS256 JWT with
    the same shape as `SignIn` and a **20-minute** TTL; each refresh mints
    a fresh `jti` and a new `iat`; `RefreshToken` rejects bearers already
    past their `exp` (the 60s threshold exists for exactly this reason).

## [0.1.0] - 2026-05-01

Initial release.

### Added

- **Authentication.** `nemo login` / `nemo logout` / `nemo whoami`.
  Credentials are read from `NEMO_USERNAME` and `NEMO_PASSWORD`;
  the bearer token is cached as JSON via `platformdirs`. Reactive token
  refresh on `401`. (ADR-003)
- **Instruments listing.**
  - `nemo instruments local` — Chilean instruments via
    `GET /api/shared/Instrumentos/FiltrarInstrumentos`. Filters: `--search`,
    `--classes`, `--page`, `--limit`.
  - `nemo instruments international` — US-listed assets via
    `GET /api/frontoffice/shared/Asset`. Filters: `--search`, `--exchange`,
    `--page`, `--page-size`.
  - Both commands accept `--json` for a machine-readable payload of the form
    `{ market, page, page_size, total, items: [...] }`. (ADR-006)
- **Portfolio summary.** `nemo portfolio summary` queries
  `GET /api/frontoffice/shared/cartera/CierreCarteraResumidaOnline` and
  returns each holding plus computed P&L and totals (per classification +
  grand total). Flags: `--account-id`, `--currency`,
  `--with-dividends/--no-dividends`, `--json`. The `--json` envelope is
  `{ currency, query_date, totals: { …, by_classification: [...] }, holdings: [...] }`
  (ADR-008).
- **Authenticated HTTP client** at `nemo_cli.api.client.api_request`,
  centralising token injection and the 401-refresh-and-retry flow.
- **Distribution as a `pipx`-installable Python package.**
  `pipx install .` puts the binary on `$PATH`; `pip install -e .[dev]` for
  development.
- **Context-First Development scaffolding.** `CLAUDE.md`, `docs/` (with
  `ARCHITECTURE`, `STACK`, `CONVENTIONS`, `CURRENT_STATUS`),
  `docs/decisions/` (ADR-001 through ADR-008), and CFD skills under
  `.claude/skills/` (`start-session`, `status`, `new-decision`,
  `validate-context`).
- **GitHub Flow** as the project branching strategy. (ADR-005)
- **Versioning policy** — SemVer + Keep a Changelog. (ADR-007)
- **`nemo --version` / `-V`** prints the CLI version (read from
  `nemo_cli.__version__`) and exits.

[Unreleased]: https://github.com/albertomarturelo/nemo-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/albertomarturelo/nemo-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/albertomarturelo/nemo-cli/releases/tag/v0.1.0
