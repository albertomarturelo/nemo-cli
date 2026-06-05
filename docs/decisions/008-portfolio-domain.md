# ADR-008: Portfolio Domain — Holdings and Computed Aggregates

## Status

Accepted

## Date

2026-05-01

## Context

Vector exposes
`GET /api/frontoffice/shared/cartera/CierreCarteraResumidaOnline`
which returns a flat array of the user's current positions. Each row carries
account info, instrument metadata (`nemotecnico`, `dscInstrumento`,
classification / sub-classification), quantities, prices (cost vs market),
multiple currency fields, and a query date. There are no pagination, no
top-level envelope, and no precomputed totals.

To make this useful — both for human reading and for the planned investing-
research agent — we need three things:

1. **Project** the wire shape into a typed, lean dataclass (per ADR-006).
2. **Compute** derived metrics that aren't on the wire: P&L (absolute and
   percentage), totals per `clasificacion`, and a grand total.
3. **Display** as a Rich table for humans and emit `--json` whose payload
   includes the derived metrics, so the agent doesn't have to re-derive them.

## Decision

- New module `nemo_cli.portfolio` with `summary.py` containing the
  dataclasses and the service. New Typer subapp at
  `nemo_cli.commands.portfolio`. First subcommand: `summary`.
- Domain types (all `frozen=True`):
  - `PortfolioHolding` — single position, projected fields (account,
    nemotécnico, descripción, clasificación, sub-clasificación, currency,
    quantity, avg buy price, market price, cost basis, market value, pnl,
    pnl_pct, query_date).
  - `ClassificationTotal` — aggregate per `clasificacion`.
  - `PortfolioTotals` — grand total + tuple of `ClassificationTotal`.
  - `Portfolio` — top-level envelope: `holdings` + `totals` + `currency` +
    `query_date`.
- The service computes derived metrics in pure Python:
  - `pnl = market_value - cost_basis` (per holding and at totals).
  - `pnl_pct = pnl / cost_basis` if `cost_basis > 0` else `0.0`.
  - `query_date` at the envelope level is the latest `fechaConsulta` across
    holdings (typically uniform).
- CLI flags on `nemo portfolio summary`:
  - `--account-id INT` (default `0` — all accounts).
  - `--currency TEXT` (default `CLP`).
  - `--with-dividends / --no-dividends` (default on).
  - `--json` for machine-readable output.
- The query parameter `tipo` is **hardcoded to `Cuenta`** for now — the
  observed SignIn response carries `tipoFiltroFrontOffice: "Cuenta"` for
  client-role users, and there is no other documented value yet. Expose as
  a flag only when a second value appears in practice.
- Money values use `float`. `decimal.Decimal` is overkill for display and
  adds JSON-serialization friction. If the future agent needs exact
  arithmetic, that's a follow-up ADR — not a reason to pre-emptively pay
  the cost now.
- `--json` payload shape:
  ```json
  {
    "currency": "CLP",
    "query_date": "2026-05-01T00:00:00",
    "totals": {
      "market_value": ...,
      "cost_basis": ...,
      "pnl": ...,
      "pnl_pct": ...,
      "by_classification": [
        { "classification": "...", "market_value": ..., "cost_basis": ...,
          "pnl": ..., "pnl_pct": ... }
      ]
    },
    "holdings": [
      { "nemotecnico": "...", "descripcion": "...", "classification": "...",
        "sub_classification": "...", "currency": "CLP", "quantity": ...,
        "avg_buy_price": ..., "market_price": ..., "cost_basis": ...,
        "market_value": ..., "pnl": ..., "pnl_pct": ...,
        "account": "...", "query_date": "..." }
    ]
  }
  ```
  Diverges from the instruments envelope (`{ market, page, page_size, total,
  items }`) because this endpoint is not paginated and the agent benefits
  from receiving precomputed totals. Both envelopes are first-class
  contracts.

## Alternatives Considered

- **Compute aggregates only at display time, return a flat list.** Simpler
  but the JSON would force the consumer to re-aggregate. The agent would
  recompute the same totals on every read. Rejected.
- **Use `decimal.Decimal` for money.** More precise but unnecessary for the
  current display + JSON pass-through use case. Rejected; revisit if precise
  arithmetic becomes a real need.
- **Group holdings by classification in the table.** Visually nicer but
  reduces compactness and complicates `--json`. Rejected — the totals block
  already gives the breakdown. A `--group-by` flag could be added later
  without changing the JSON shape.
- **Match the instruments envelope shape.** Forces fake `page` /
  `page_size` / `total` fields for an endpoint that is not paginated.
  Rejected.
- **Spanish-language command (`nemo cartera summary`).** Rejected per the
  prior CLI naming convention (English commands, Spanish field display).

## Consequences

- New `portfolio` subcommand group; the integration contract for downstream
  consumers grows by one envelope shape.
- Adding a future `nemo portfolio history` (movements, transactions) is
  mechanical: another subcommand under `portfolio`, its own dataclasses.
- Edge case explicitly handled: `cost_basis == 0` → `pnl_pct = 0.0`.
- The `tipo` parameter remains a known unknown; if a different value
  appears for non-client roles, expose `--filter-type` and document.
- The portfolio JSON payload is the most structured surface so far —
  expected to drive the bulk of the planned Chilean-investing-research
  agent's prompts.
