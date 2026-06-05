# ADR-006: Instruments Domain — Local and International as Separate Markets

## Status

Accepted

## Date

2026-05-01

## Context

Vector Capital exposes two distinct endpoints for browsing tradable instruments:

- **Local (Chilean):** `GET /api/shared/Instrumentos/FiltrarInstrumentos`
  - Params: `page`, `limit`, `filterNemotecnico`, `codSubClaseInstrumentos`
  - Response: `{ result: Instrument[], total: int }` with Spanish field names
    (`nemotecnico`, `dscInstrumento`, `codSubClaseInstrumento`, `codClaseInstrumento`,
    `codigoFamilia`, `codMoneda`, `isin`, `idMercadoTransaccion`, …) and many
    Vector-internal navigation fields.
- **International (US equities):** `GET /api/frontoffice/shared/Asset`
  - Params: `exchangeName`, `search`, `page`, `pageSize`
  - Response: `{ items: Asset[], totalCount: int }` with English field names
    (`symbol`, `name`, `exchangeName`, `assetClassName`, `tradable`, `shortable`,
    `fractionable`, `volume`, `tradeCount`, `cusip`, …).

The two payloads share *no* meaningful field names. Their identifiers, status
flags, pagination metadata, and even the names of common attributes
(`dscInstrumento` vs `name`, `codMoneda` is implicit on the international side)
all diverge. A single polymorphic `Instrument` type would either lose information
or carry a noisy union; either choice would propagate ambiguity into every
downstream consumer.

The CLI is also intended to feed a future investment-research agent (Chilean
markets focus). That consumer needs a stable, structured, machine-readable
contract — which favours typing each market precisely rather than a lowest-
common-denominator mash-up.

This addition also forces a small refactor: the new endpoints sit under
`/api/shared/...` and `/api/frontoffice/...`, peers of `/api/publicapi/...`.
The existing `API_BASE_URL` is too narrow.

## Decision

1. **Two domain types, two services, two subcommands.** Model local and
   international as independent entities under `nemo_cli.instruments`:

   - `nemo_cli.instruments.local.LocalInstrument` + `list_local_instruments`
   - `nemo_cli.instruments.international.InternationalAsset` +
     `list_international_assets`

   Each service maps its own response into a typed, frozen `dataclass`. No
   shared base class.

2. **CLI surface.** Expose them as a Typer subcommand group:

   ```
   nemo instruments local         [--search NEMO] [--classes ACC,ETF,…] [--page N] [--limit N] [--json]
   nemo instruments international [--search TXT]  [--exchange NASDAQ]   [--page N] [--page-size N] [--json]
   ```

   Filters are market-specific. Pagination flag names mirror what each
   underlying endpoint accepts (`--limit` vs `--page-size`).

3. **`--json` per command.** Each instruments command supports `--json` to emit
   the typed dataclasses serialised to JSON (one object per item plus a `total`
   field), in addition to the default human-readable Rich table. JSON mode is
   the contract for future agent consumption. This is **per-command opt-in**,
   not a global flag (per the existing convention in `docs/CONVENTIONS.md`).

4. **`API_BASE_URL` refactor.** Move
   `https://portalclientes.vectorcapital.cl/api/publicapi` →
   `https://portalclientes.vectorcapital.cl/api`. All callers append the
   sub-prefix (`/publicapi/...`, `/shared/...`, `/frontoffice/...`) explicitly.
   The auth call in `nemo_cli.auth.service` is updated accordingly. ADR-003
   stands; this is a straightforward narrowing of one detail.

5. **`rich` becomes a runtime dependency.** Adds `rich>=13.0` for table
   rendering. Already a transitive dep of `typer`; making it explicit
   guarantees its presence and signals intent.

## Alternatives Considered

- **Single unified `Instrument` type with a `market: Literal["local", "international"]`
  discriminator.** Forces a lowest-common-denominator field set or a noisy
  union, and downstream consumers must always check the discriminator. Rejected
  — the markets *are* different, and pretending otherwise loses information.
- **One `nemo instruments list` command with `--market {local,international}`.**
  Same problem at the CLI layer: filter flags would have to be a soup that some
  apply to one market and not the other. Rejected.
- **Mixed-language naming (`nemo instrumentos` vs `nemo assets`),**
  mirroring Vector's own API naming. Inconsistent CLI surface; rejected in
  favour of keeping all top-level commands in English.
- **Keep `API_BASE_URL` at `/api/publicapi` and add per-domain base URLs.**
  More moving parts, more chances to send credentials to the wrong host.
  Rejected — single base + explicit path prefix is simpler.
- **Skip `rich`, format tables manually.** Saves a (small) dep but the table
  rendering becomes 30+ lines of padding logic per command. Rejected.

## Consequences

- New module: `src/nemo_cli/instruments/` with `local.py`, `international.py`,
  and a Typer subapp at `src/nemo_cli/commands/instruments.py`.
- The auth-call path in `nemo_cli.auth.service` becomes
  `/publicapi/shared/auth/SignIn`. No external behaviour change for end users.
- Adding a new market (derivatives, fixed income) is mechanical: drop in a new
  service module + dataclass + subcommand. No refactor of existing markets.
- `--json` becomes the de-facto integration contract. Once stabilised, the
  future Chilean-investing-research agent will consume it.
- Vector returns many fields per instrument (~50 on the local side). We
  intentionally project to a smaller, useful subset — surfacing what's relevant
  for browsing and analysis, ignoring navigation/internal fields. If a consumer
  needs a dropped field later, add it to the dataclass.
