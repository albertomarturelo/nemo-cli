# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
Versioning policy and release process: [ADR-007](docs/decisions/007-versioning-and-changelog.md).

## [Unreleased]

## [0.0.2] - 2026-06-04

Cuts the path from TestPyPI to PyPI prod. No CLI surface change.

### Added

- **`publish-to-pypi` job** in `.github/workflows/publish.yml` — same
  Trusted Publishing pattern as TestPyPI but gated on the `pypi`
  GitHub environment with required reviewers, so PyPI prod releases
  require a one-click approval after the workflow reaches the publish
  step. The two jobs run sequentially (`testpypi` first, `pypi` after)
  off the same build, so a failed TestPyPI upload short-circuits the
  prod publish.
- Workflow renamed `Publish to TestPyPI` → `Publish` to reflect the
  dual-target nature.

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

[Unreleased]: https://github.com/albertomarturelo/nemo-cli/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/albertomarturelo/nemo-cli/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/albertomarturelo/nemo-cli/releases/tag/v0.0.1
