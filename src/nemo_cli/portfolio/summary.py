from dataclasses import dataclass
from typing import Any, cast

from nemo_cli.api.client import api_request


@dataclass(frozen=True)
class PortfolioHolding:
    account: str
    account_description: str
    classification: str
    sub_classification: str
    instrument_id: int
    nemotecnico: str
    descripcion: str
    sub_class: str
    series: str | None
    currency: str
    quantity: float
    avg_buy_price: float
    market_price: float
    cost_basis: float
    market_value: float
    pnl: float
    pnl_pct: float
    query_date: str | None


@dataclass(frozen=True)
class ClassificationTotal:
    classification: str
    market_value: float
    cost_basis: float
    pnl: float
    pnl_pct: float


@dataclass(frozen=True)
class PortfolioTotals:
    market_value: float
    cost_basis: float
    pnl: float
    pnl_pct: float
    by_classification: tuple[ClassificationTotal, ...]


@dataclass(frozen=True)
class Portfolio:
    currency: str
    query_date: str | None
    holdings: tuple[PortfolioHolding, ...]
    totals: PortfolioTotals


def get_portfolio_summary(
    *,
    account_id: int = 0,
    currency: str = "CLP",
    with_dividends: bool = True,
) -> Portfolio:
    params: dict[str, Any] = {
        "id": account_id,
        "tipo": "Cuenta",
        "codMonedaSld": currency,
        "conDividendos": "true" if with_dividends else "false",
    }
    response = api_request(
        "GET",
        "/frontoffice/shared/cartera/CierreCarteraResumidaOnline",
        params=params,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to load portfolio summary "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, list):
        raise RuntimeError("Portfolio summary response was not a JSON array.")

    holdings = tuple(
        _to_holding(cast(dict[str, object], item))
        for item in cast(list[object], raw)
        if isinstance(item, dict)
    )
    totals = _compute_totals(holdings)
    query_date = _latest_query_date(holdings)

    return Portfolio(
        currency=currency,
        query_date=query_date,
        holdings=holdings,
        totals=totals,
    )


def _to_holding(item: dict[str, object]) -> PortfolioHolding:
    cost_basis = _as_float(item.get("valorPresenteCompraMonDflt"))
    market_value = _as_float(item.get("valorPresenteMercadoMonDflt"))
    pnl = market_value - cost_basis
    pnl_pct = (pnl / cost_basis) if cost_basis > 0 else 0.0

    return PortfolioHolding(
        account=_as_str(item.get("cuenta")) or _as_str(item.get("numCuenta")),
        account_description=_as_str(item.get("dscCuenta")),
        classification=_as_str(item.get("clasificacion")),
        sub_classification=_as_str(item.get("subClasificacion")),
        instrument_id=_as_int(item.get("idInstrumento")),
        nemotecnico=_as_str(item.get("nemotecnico")),
        descripcion=_as_str(item.get("dscInstrumento")),
        sub_class=_as_str(item.get("codSubClaseInstrumento")),
        series=_as_optional_str(item.get("serie")),
        currency=_as_str(item.get("codMonedaDflt")),
        quantity=_as_float(item.get("cantidad")),
        avg_buy_price=_as_float(item.get("tasaPrecioCompra")),
        market_price=_as_float(item.get("tasaPrecio")),
        cost_basis=cost_basis,
        market_value=market_value,
        pnl=pnl,
        pnl_pct=pnl_pct,
        query_date=_as_optional_str(item.get("fechaConsulta")),
    )


def _compute_totals(holdings: tuple[PortfolioHolding, ...]) -> PortfolioTotals:
    by_class: dict[str, list[PortfolioHolding]] = {}
    for holding in holdings:
        by_class.setdefault(holding.classification, []).append(holding)

    classification_totals: list[ClassificationTotal] = []
    for classification in sorted(by_class):
        items = by_class[classification]
        market = sum(h.market_value for h in items)
        cost = sum(h.cost_basis for h in items)
        pnl = market - cost
        pnl_pct = (pnl / cost) if cost > 0 else 0.0
        classification_totals.append(
            ClassificationTotal(
                classification=classification,
                market_value=market,
                cost_basis=cost,
                pnl=pnl,
                pnl_pct=pnl_pct,
            )
        )

    total_market = sum(h.market_value for h in holdings)
    total_cost = sum(h.cost_basis for h in holdings)
    total_pnl = total_market - total_cost
    total_pnl_pct = (total_pnl / total_cost) if total_cost > 0 else 0.0

    return PortfolioTotals(
        market_value=total_market,
        cost_basis=total_cost,
        pnl=total_pnl,
        pnl_pct=total_pnl_pct,
        by_classification=tuple(classification_totals),
    )


def _latest_query_date(holdings: tuple[PortfolioHolding, ...]) -> str | None:
    dates = [h.query_date for h in holdings if h.query_date]
    return max(dates) if dates else None


def _as_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _as_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0
