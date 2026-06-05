# ADR-011: Portfolio Movements with Classification and Dividend Parsing

## Status

Accepted

## Date

2026-05-01

## Context

Vector exposes
`GET /api/frontoffice/shared/MovimientosCajas/Movimientos?id=&tipo=&desde=&hasta=`
which returns the full list of cash movements (movimientos de caja) for the
account over a date range, grouped by *caja* (cash bucket — typically one per
currency: `CAJA CLP`, `CAJA USD`, …). Each movement carries an `abono`
(credit), a `cargo` (debit), a `saldo` (running balance), and a free-form
`movimiento` description string.

The free-form description encodes structured data that the agent needs:

| Pattern in `movimiento`                       | Category    | Embedded data                                           |
|-----------------------------------------------|-------------|---------------------------------------------------------|
| `DIV;07-07-2025;CFIHMCREPA;24,1688914293`     | dividend    | ex-date (DD-MM-YYYY), nemotécnico, per-unit amount      |
| `COMPRA FONDOS CB - CFIHMCREPA`               | buy         | nemotécnico                                             |
| `VENTA FONDOS CB - CFIHMCREPA`                | sell        | nemotécnico                                             |
| `COMISION TRANSACCIÓN BOLSA`                  | commission  | —                                                       |
| `12.345.678-0` (RUT) + abono > 0              | cash_in     | external deposit                                        |
| `12.345.678-0` (RUT) + cargo > 0              | cash_out    | external withdrawal                                     |
| anything else                                 | other       | —                                                       |

The user's stated motivation: surfacing dividends per instrument is
"muy útil" for the planned investing-research agent — knowing which
instruments paid dividends and how much over a period is a primary input to
yield analysis and to evaluating whether to keep / rotate a position.

Without classification, the consumer would have to re-implement the regex
soup. With classification + per-nemotécnico aggregates in the service, the
agent gets a clean contract.

## Decision

- **New module** `src/nemo_cli/portfolio/movements.py`.
- **Frozen dataclasses**:
  - `Movement` — one row, with the raw description preserved plus a `kind`
    discriminator (`Literal["dividend", "buy", "sell", "commission",
    "cash_in", "cash_out", "other"]`) and structured payloads
    (`dividend: DividendInfo | None`, `trade: TradeInfo | None`).
  - `DividendInfo(ex_date, nemotecnico, per_unit_amount)` — `ex_date`
    normalised to `YYYY-MM-DD`; `per_unit_amount` parses Chilean
    decimal-comma (`24,1688914293` → `24.1688914293`) into `float`.
  - `TradeInfo(nemotecnico, side: Literal["buy", "sell"])`.
  - `DividendSummaryItem`, `TradeSummaryItem` — per-nemotécnico aggregates.
  - `MovementsSummary` — totals (cash_in, cash_out, dividends,
    commissions, buys, sells, occurrences, plus
    `by_dividend: tuple[DividendSummaryItem, ...]` and
    `by_trade: tuple[TradeSummaryItem, ...]`).
  - `CashBucket` — one bucket (one currency), its movements, and its own
    summary.
  - `Movements` — top-level envelope: `desde`, `hasta`, `buckets`, and a
    grand `summary` aggregated across buckets.
- **Service** `get_movements(*, desde, hasta, account_id) -> Movements`:
  - Validates input dates are `YYYY-MM-DD` (Typer enforces it at the CLI
    boundary too).
  - Aggregates are computed at the service boundary (per ADR-008
    convention): the agent never has to re-aggregate.
- **CLI** `nemo portfolio movements [--desde] [--hasta] [--account-id]
  [--json]`:
  - `--desde` defaults to **1 year ago** in ISO; `--hasta` defaults to
    **today** in ISO. The user's primary use case is dividend yield
    over the last twelve months, so a 1-year window is a sensible default
    and matches the URL example shipped with this work.
  - `--account-id` defaults to `0` (all accounts), same convention as
    `portfolio summary`.
  - `--json` envelope shape:
    ```json
    {
      "desde": "...", "hasta": "...",
      "summary": { "total_cash_in": ..., "total_cash_out": ...,
                   "total_dividends": ..., "total_commissions": ...,
                   "total_buys": ..., "total_sells": ...,
                   "by_dividend": [ { "nemotecnico", "total_received",
                                      "occurrences" } ],
                   "by_trade":    [ { "nemotecnico", "side", "total_amount",
                                      "occurrences" } ] },
      "buckets": [ { "bucket_id", "name", "summary": {…},
                     "movements": [ { "movement_date", "settlement_date",
                                      "description", "kind", "credit",
                                      "debit", "balance", "currency",
                                      "dividend": {…} | null,
                                      "trade": {…} | null,
                                      "account", "sequence" } ] } ]
    }
    ```
- **Default human output**: a Rich panel with `Summary` (totals), a
  `Dividends by instrument` table sorted by total received desc, and a
  `Trades by instrument` table grouped by nemotécnico (buys / sells side
  by side). Full per-row movements are *not* dumped to stdout by default —
  if the user wants them, `--json | jq …` is the right channel.

## Alternatives Considered

- **Skip classification, expose raw `movimiento` strings.** Cheapest
  service code, but pushes the regex soup onto every consumer (especially
  the agent, which would re-implement it on every prompt). Rejected — the
  whole point of this feature is to lock the dividend / trade contract.
- **Use `decimal.Decimal` for amounts.** The Chilean per-unit-amount has
  10 decimal places. Floats are good for ~15 significant digits, plenty
  for display and aggregation. Rejected for now per the precedent in
  ADR-008; if precise arithmetic becomes a real need, follow-up ADR.
- **Annotate `kind` with `pydantic` Literal validation.** Pydantic would
  give us validation at parse time, but it adds a runtime dependency and
  duplicates what `Literal[...]` already provides at the type-check
  boundary. Rejected.
- **Dump all movements to stdout by default.** Could be 200+ rows per
  year. Rejected — `--json` is the channel for full data; the default
  panel is the glance.
- **Per-row table by default with paging.** More implementation, doesn't
  serve the agent or the typical user query ("how much did X pay this
  year?"). Rejected.
- **Add `--kind` filter.** Tempting (`--kind dividend` to print only
  dividend rows), but `jq 'select(.kind == "dividend")'` on `--json` does
  the same. Skipped to keep the surface minimal; revisit if it comes up.
- **Lookup `idInstrumento` from the parsed nemotécnico.** Would let the
  agent join movements to the instrument metadata directly. Possible
  follow-up; out of scope here. The `nemotecnico` string itself is the
  stable identifier and matches `instruments local --search NEMO` and
  `portfolio summary`.

## Consequences

- The integration contract for downstream consumers grows by another
  envelope shape. Three so far (instruments listing, portfolio summary,
  price history) → four with movements. Each is intentionally distinct.
- Classification regexes live in code with explicit unit-test coverage
  (every pattern + the fall-through `other` branch). When Vector adds a
  new movement kind, an unmatched description falls through to `other`
  with the raw `description` preserved — no data loss, just a missing
  classification. We extend the regex catalog in a follow-up PR.
- `kind` is a stable `Literal` value — adding a new kind in the future is
  a `MINOR` bump per ADR-007 (new field in the contract) unless we
  retire an existing one.
- The dividend per-unit-amount uses Chilean decimal comma in the wire;
  parsed as `float` post-translation. The sum stored on the row is
  `abono` (already in CLP integer-ish), which is what totals compute
  against — the per-unit value is informational and lets the agent
  reconcile units × per-unit ≈ abono if it cares.
- Default `desde` of one year ago is opinionated; if the user wants
  shorter / longer, they pass the flag explicitly. The default is
  documented in `--help`.
- Test coverage target stays ≥ 95% (per CONVENTIONS); the parsing helpers
  must be at 100% because they are the contract.
- **Operational note: the endpoint is markedly slower than the rest of
  the surface.** Empirical findings during the first integration:
  - The default `api_request` timeout of 15s was killing the call.
  - 60s was *also* insufficient for a full-year window in practice.
  - **180s currently holds.** Set at the service layer
    (`get_movements`), not as the global default — fast endpoints keep
    their tighter budget so real problems don't get masked.
  - If 180s ever stops being enough, the documented escalation path is
    to widen `api_request`'s signature to accept `float | httpx.Timeout`
    so each phase (connect / read / write / pool) gets its own value
    instead of all four sharing one budget. This is the only known case
    in the suite that might need that treatment. Documented in
    `docs/CONVENTIONS.md` (HTTP → Timeouts).
