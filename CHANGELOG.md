# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
Versioning policy and release process: [ADR-007](docs/decisions/007-versioning-and-changelog.md).

## [Unreleased]

### Added

- **`nemo status` command** — reports the current authentication session state
  (`active`, `expiring`, `expired`, or `logged out`) read from the cached token's
  `exp`, with no network call. Backed by a new `nemo_cli.auth.session` layer that
  encapsulates the login orchestration (`log_in`) and the session state (`status`)
  above the raw `service` / `token_store` modules. (ADR-026)

### Changed

- **Interactive login.** `nemo login` now prompts for email and password
  (password hidden), with optional `--user` / `--password` flags for
  non-interactive use. Credentials are passed explicitly to `sign_in()` and are
  never read from the environment or written to disk. (ADR-025)

### Removed

- **`NEMO_USERNAME` / `NEMO_PASSWORD` environment variables.** Credentials are no
  longer read from the environment (or a `.env` file); the `python-dotenv`
  dependency and `.env.example` are removed. Authenticate with `nemo login`.
  (ADR-025)
- **Automatic re-`SignIn` on expiry.** `api_request()` no longer re-authenticates
  silently from stored credentials. On token expiry it renews via `RefreshToken`;
  if that fails it raises `Session expired — run \`nemo login\``. This amends the
  `401` ladder of ADR-003 / ADR-012. (ADR-025)

### Changed (incidental)

- **`nemo whoami`** now reports only whether a token is cached (there is no
  configured user to display without stored credentials). Surfacing the signed-in
  identity from the token is tracked as a separate work unit.

## [0.0.1] - 2026-06-04

Initial public release on TestPyPI. The CLI is functional but versioned
under `0.0.x` to signal that the public surface may still change without
notice until `0.1.0` (see ADR-007).

### Added

- **Authentication.** `nemo login` / `nemo logout` / `nemo whoami`.
  Credentials read from `NEMO_USERNAME` / `NEMO_PASSWORD` (env vars only,
  never persisted by this CLI). Bearer token cached as JSON via
  `platformdirs`. Proactive refresh when the cached JWT expires within
  60s; reactive `RefreshToken → SignIn` ladder on `401`. Credentials
  touch the wire only on bootstrap and as a last resort. (ADR-003,
  ADR-012)
- **Instruments listing.**
  - `nemo instruments local` — Chilean instruments via
    `GET /api/shared/Instrumentos/FiltrarInstrumentos`. Filters:
    `--search`, `--classes`, `--page`, `--limit`.
  - `nemo instruments international` — US-listed assets via
    `GET /api/frontoffice/shared/Asset`. Filters: `--search`,
    `--exchange`, `--page`, `--page-size`.
  - Both commands accept `--json` for a machine-readable payload of the
    form `{ market, page, page_size, total, items: [...] }`. (ADR-006)
- **Instrument price history.** `nemo instruments prices --id <ID>`
  returns ~1 year of daily prices for a local Chilean instrument
  (`GET /api/frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento`),
  with computed stats (first/last, min/max with dates, mean, total
  return %, daily-return σ) and an ASCII sparkline. `--json` emits the
  full point series plus stats. **Local instruments only**: the upstream
  endpoint does not serve international assets. (ADR-010)
- **Portfolio summary.** `nemo portfolio summary` queries
  `GET /api/frontoffice/shared/cartera/CierreCarteraResumidaOnline` and
  returns each holding plus computed P&L and totals (per classification
  + grand total). Flags: `--account-id`, `--currency`,
  `--with-dividends/--no-dividends`, `--json`. (ADR-008)
- **Portfolio movements with classification.** `nemo portfolio movements
  --desde <YYYY-MM-DD> --hasta <YYYY-MM-DD>` queries
  `GET /api/frontoffice/shared/MovimientosCajas/Movimientos` and parses
  each movement description into a structured `kind` (`dividend`, `buy`,
  `sell`, `commission`, `cash_in`, `cash_out`, `other`) plus, when
  applicable, a typed `DividendInfo` (ex-date, nemotécnico, per-unit
  amount) or `TradeInfo` (nemotécnico, side). The service computes
  per-nemotécnico aggregates (`by_dividend`, `by_trade`) and global
  totals at the boundary. Endpoint is slow; the call uses a **180s
  timeout** documented in `docs/CONVENTIONS.md`. (ADR-011)
- **Authenticated HTTP client** at `nemo_cli.api.client.api_request` —
  the single point for portal HTTP, owns token injection and the
  refresh ladder.
- **Distribution.** `pipx install nemo-cli` (TestPyPI for now);
  `pip install -e .[dev]` for development. `nemo --version` / `-V`
  prints the CLI version from `nemo_cli.__version__`.
- **Unit-test suite** — 203 tests, ~98% line coverage, mirrors the
  package tree under `tests/`. `respx` mocks `httpx` at the transport
  layer (no real network calls); `typer.testing.CliRunner` drives the
  CLI. No CI/CD wired yet; tests run locally with `pytest`.
- **Context-First Development scaffolding** — `CLAUDE.md`,
  `docs/ARCHITECTURE.md`, `docs/STACK.md`, `docs/CONVENTIONS.md`,
  `docs/decisions/` (ADRs 001–012 minus 009), and the four CFD skills
  under `.claude/skills/` (`start-session`, `status`, `new-decision`,
  `validate-context`).
- **GitHub Flow** as the project branching strategy. (ADR-005)
- **Versioning policy** — SemVer + Keep a Changelog. (ADR-007)

[Unreleased]: https://github.com/albertomarturelo/nemo-cli/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/albertomarturelo/nemo-cli/releases/tag/v0.0.1
