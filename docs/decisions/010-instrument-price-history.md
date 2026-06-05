# ADR-010: Instrument Price History — `nemo instruments prices`

## Status

Accepted

## Date

2026-05-01

## Context

Vector exposes
`GET /api/frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento?idInstrumento=...`
which returns ~1 year of daily prices for the requested instrument (one row per
calendar day, including weekend / holiday carry-forward). Each row carries
`fecha`, `precio`, and `fechaActualizacion`, plus many internal navigation
fields that are mostly null and have no analytical value.

**Important scope limitation:** This endpoint only works for **local
Chilean instruments** (the integer `idInstrumento` returned by
`/api/shared/Instrumentos/FiltrarInstrumentos`). It does **not** serve the
international assets returned by `/api/frontoffice/shared/Asset` (which use
UUID identifiers and live in a different price-feed pipeline). Verified
empirically; the asymmetry is documented as a server-side fact, not an
nemo-cli choice.

To make the data useful — both as a human glance and as input to the planned
investing-research agent — three things are needed:

1. **Project** the wire shape into a typed dataclass (per ADR-006) and drop the
   navigation noise.
2. **Compute** period-level metrics not present on the wire: first/last price,
   min/max with their dates, mean, total return, daily-return σ.
3. **Display** a stats panel + a quick visual hint of the trajectory; emit the
   full point series via `--json` for agent consumption (per ADR-006 / ADR-008
   envelope conventions).

The endpoint is conceptually *detail-by-id* on an instrument and is a sibling of
the portfolio endpoint under `/frontoffice/shared/...`. It belongs inside the
existing `instruments` package and Typer subapp rather than a new top-level
group.

## Decision

- **Module:** `src/nemo_cli/instruments/prices.py`. Service:
  `get_price_history(instrument_id: int) -> PriceHistory`.
- **Frozen dataclasses:** `PricePoint`, `PriceHistoryStats`, and `PriceHistory`
  (envelope: `instrument_id`, `points: tuple[PricePoint, ...]`,
  `stats: PriceHistoryStats | None`).
- **Computed stats at the service boundary:**
  - `first_date`, `last_date`, `first_price`, `last_price`
  - `min_price` / `min_date`, `max_price` / `max_date`
  - `mean_price`
  - `total_return_pct = (last - first) / first` (0.0 when `first == 0`)
  - `daily_return_std_pct` = stdev of daily returns; **not annualised** —
    consumers (notably the agent) annualise if they want, with the factor of
    their choice (√252 vs √365).
  - `days` = `len(points)`
  - `stats is None` only if there are no points; otherwise always populated.
- **CLI:** `nemo instruments prices --id <ID> [--json]`. Lives under the
  existing `instruments` Typer subapp. `--id` is typed as `int`, which by
  itself excludes the UUID-shaped international identifiers (a Typer
  type-check rejects UUID-shaped strings before the request is made). The
  command's docstring states explicitly that it serves **local Chilean
  instruments only**; if the underlying API ever exposes a sibling endpoint
  for international assets, expose it under a different name (e.g.
  `nemo instruments international-prices`) rather than overloading
  `prices`.
- **Default output:** a Rich table with the stats fields, followed by an ASCII
  sparkline (`▁▂▃▄▅▆▇█`) sampled to a max width of 80 characters.
- **`--json` envelope:**
  `{ "instrument_id", "stats": { … } | null, "points": [ {date, price, updated_at}, … ] }`.
  Diverges from the listing envelope intentionally — this is a detail-by-id
  response, not a paged list, so `page`, `page_size`, `total` are not
  meaningful.

## Alternatives Considered

- **Annualise volatility in the service** (multiply daily σ by √252 or √365).
  Rejected — the right factor depends on the consumer's intent (calendar vs
  trading days, daily-quoted CFI vs traded equity). Exposing raw daily σ is
  honest and pushes the choice to the consumer.
- **Stats-only output, no sparkline.** Rejected — the user explicitly asked
  for the "evolution" over a year; a single-line trajectory hint is the
  cheapest way to convey shape without dumping 365 rows.
- **Print all 365 points as a table by default.** Rejected — too long for a
  glance; `--json` is the right channel for the full series.
- **Add `--start` / `--end` / `--period` flags.** The endpoint accepts only
  `idInstrumento`; period is fixed by the server. Flags that don't change the
  backend response are footguns. Skipped until the API exposes a knob.
- **New top-level `nemo prices` group.** Rejected — prices belong to
  instruments. Living inside `instruments` makes the relationship
  discoverable (`nemo instruments --help`) without a parallel hierarchy.
- **Resolve `--nemo` to `idInstrumento` automatically** (extra round-trip
  through `FiltrarInstrumentos`). Useful but out of scope; today the workflow
  is `nemo instruments local --search NEMO --json | jq '.items[].id_instrumento'`.
  Tracked as a follow-up.
- **Make `prices` work for international assets too.** Rejected because the
  upstream endpoint does not serve them — the asymmetry lives on the server
  side. If Vector adds a sibling endpoint for international assets, we add a
  separate command rather than overloading `prices`.

## Consequences

- The `instruments` subapp now mixes list (`local`, `international`) and
  detail-by-id (`prices`) shapes. `--help` makes the distinction clear; future
  detail commands on instruments fit the same pattern.
- A third `--json` envelope joins the integration contract surface (after
  instruments listing and portfolio summary). The agent now has typed access
  to per-instrument trajectories with precomputed stats.
- `daily_return_std_pct` surfaces a per-instrument volatility signal that
  could feed a future `nemo portfolio risk` command. Out of scope here.
- When the API exposes a date range, a follow-up ADR adds `--start` /
  `--end`. Until then, the period is whatever the server returns
  (~1 year).
- The endpoint sits behind `/frontoffice/shared/PublicadorPrecio`, a new
  third-level prefix under `/frontoffice` for nemo-cli. The existing
  `api_request` contract is unchanged; the path moves into the caller per
  ADR-006.
