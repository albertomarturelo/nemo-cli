"""Tests for nemo_cli.portfolio.summary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import httpx
import pytest
import respx

from nemo_cli.config import API_BASE_URL
from nemo_cli.portfolio.summary import (
    ClassificationTotal,
    Portfolio,
    PortfolioHolding,
    PortfolioTotals,
    _compute_totals,
    _to_holding,
    get_portfolio_summary,
)

PORTFOLIO_URL = (
    f"{API_BASE_URL}/frontoffice/shared/cartera/CierreCarteraResumidaOnline"
)


SAMPLE_WIRE_HOLDING: dict[str, object] = {
    "numCuenta": "99999999/00",
    "cuenta": "99999999/00",
    "dscCuenta": "Test User",
    "clasificacion": "RENTA FIJA",
    "subClasificacion": "Inversiones Alternativas",
    "idInstrumento": 52185,
    "nemotecnico": "CFIMRCLPR",
    "dscInstrumento": "MONEDA RENTA CLP FI, SERIE R",
    "codSubClaseInstrumento": "CFI",
    "serie": None,
    "codMonedaDflt": "CLP",
    "cantidad": 100.0,
    "tasaPrecioCompra": 18000.0,
    "tasaPrecio": 18500.0,
    "valorPresenteCompraMonDflt": 1800000.0,
    "valorPresenteMercadoMonDflt": 1850000.0,
    "fechaConsulta": "2026-05-01T00:00:00",
}


class TestToHolding:
    def test_projects_required_fields_and_computes_pnl(self) -> None:
        holding = _to_holding(SAMPLE_WIRE_HOLDING)
        assert holding.account == "99999999/00"
        assert holding.account_description == "Test User"
        assert holding.classification == "RENTA FIJA"
        assert holding.sub_classification == "Inversiones Alternativas"
        assert holding.instrument_id == 52185
        assert holding.nemotecnico == "CFIMRCLPR"
        assert holding.descripcion == "MONEDA RENTA CLP FI, SERIE R"
        assert holding.sub_class == "CFI"
        assert holding.series is None
        assert holding.currency == "CLP"
        assert holding.quantity == 100.0
        assert holding.cost_basis == 1800000.0
        assert holding.market_value == 1850000.0
        # P&L absolute and percentage.
        assert holding.pnl == pytest.approx(50000.0)
        assert holding.pnl_pct == pytest.approx(50000.0 / 1800000.0)

    def test_pnl_pct_is_zero_when_cost_basis_is_zero(self) -> None:
        item = {
            **SAMPLE_WIRE_HOLDING,
            "valorPresenteCompraMonDflt": 0.0,
            "valorPresenteMercadoMonDflt": 100.0,
        }
        holding = _to_holding(item)
        assert holding.pnl == 100.0
        assert holding.pnl_pct == 0.0

    def test_negative_pnl_when_below_cost(self) -> None:
        item = {
            **SAMPLE_WIRE_HOLDING,
            "valorPresenteMercadoMonDflt": 1700000.0,
        }
        holding = _to_holding(item)
        assert holding.pnl == pytest.approx(-100000.0)
        assert holding.pnl_pct < 0

    def test_falls_back_to_num_cuenta_when_cuenta_missing(self) -> None:
        item = {k: v for k, v in SAMPLE_WIRE_HOLDING.items() if k != "cuenta"}
        holding = _to_holding(item)
        assert holding.account == "99999999/00"

    def test_returns_frozen_dataclass(self) -> None:
        holding = _to_holding(SAMPLE_WIRE_HOLDING)
        assert isinstance(holding, PortfolioHolding)
        with pytest.raises(FrozenInstanceError):
            holding.nemotecnico = "OTHER"  # type: ignore[misc]


class TestComputeTotals:
    def _holding(
        self,
        *,
        classification: str,
        cost: float,
        market: float,
    ) -> PortfolioHolding:
        return PortfolioHolding(
            account="A",
            account_description="X",
            classification=classification,
            sub_classification="Sub",
            instrument_id=1,
            nemotecnico="NEMO",
            descripcion="d",
            sub_class="ACC",
            series=None,
            currency="CLP",
            quantity=1.0,
            avg_buy_price=cost,
            market_price=market,
            cost_basis=cost,
            market_value=market,
            pnl=market - cost,
            pnl_pct=((market - cost) / cost) if cost > 0 else 0.0,
            query_date="2026-05-01",
        )

    def test_empty_returns_zero_totals(self) -> None:
        totals = _compute_totals(())
        assert isinstance(totals, PortfolioTotals)
        assert totals.market_value == 0
        assert totals.cost_basis == 0
        assert totals.pnl == 0
        assert totals.pnl_pct == 0
        assert totals.by_classification == ()

    def test_computes_grand_total(self) -> None:
        holdings = (
            self._holding(classification="RENTA FIJA", cost=1000.0, market=1100.0),
            self._holding(
                classification="RENTA VARIABLE", cost=2000.0, market=1900.0
            ),
        )
        totals = _compute_totals(holdings)
        assert totals.market_value == pytest.approx(3000.0)
        assert totals.cost_basis == pytest.approx(3000.0)
        assert totals.pnl == pytest.approx(0.0)
        assert totals.pnl_pct == pytest.approx(0.0)

    def test_by_classification_aggregates_each_group(self) -> None:
        holdings = (
            self._holding(classification="RENTA FIJA", cost=1000.0, market=1100.0),
            self._holding(classification="RENTA FIJA", cost=500.0, market=550.0),
            self._holding(
                classification="RENTA VARIABLE", cost=2000.0, market=1900.0
            ),
        )
        totals = _compute_totals(holdings)
        # by_classification is sorted alphabetically.
        assert [c.classification for c in totals.by_classification] == [
            "RENTA FIJA",
            "RENTA VARIABLE",
        ]
        rf = totals.by_classification[0]
        rv = totals.by_classification[1]
        assert rf.market_value == pytest.approx(1650.0)
        assert rf.cost_basis == pytest.approx(1500.0)
        assert rf.pnl == pytest.approx(150.0)
        assert rf.pnl_pct == pytest.approx(0.10)
        assert rv.pnl == pytest.approx(-100.0)
        assert rv.pnl_pct == pytest.approx(-0.05)

    def test_handles_zero_cost_basis_in_classification_total(self) -> None:
        holdings = (
            self._holding(classification="RENTA FIJA", cost=0.0, market=100.0),
        )
        totals = _compute_totals(holdings)
        assert totals.by_classification[0].pnl_pct == 0.0
        assert totals.pnl_pct == 0.0

    def test_classification_total_is_a_dataclass(self) -> None:
        holdings = (
            self._holding(classification="RENTA FIJA", cost=1000.0, market=1100.0),
        )
        totals = _compute_totals(holdings)
        first = totals.by_classification[0]
        assert isinstance(first, ClassificationTotal)


class TestGetPortfolioSummary:
    @respx.mock
    def test_returns_typed_portfolio(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(200, json=[SAMPLE_WIRE_HOLDING])
        )

        portfolio = get_portfolio_summary()

        assert isinstance(portfolio, Portfolio)
        assert portfolio.currency == "CLP"
        assert len(portfolio.holdings) == 1
        assert portfolio.holdings[0].nemotecnico == "CFIMRCLPR"
        assert portfolio.totals.market_value == pytest.approx(1850000.0)

    @respx.mock
    def test_passes_default_query_params(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(200, json=[])
        )

        get_portfolio_summary()

        sent_url = str(route.calls.last.request.url)
        assert "id=0" in sent_url
        assert "tipo=Cuenta" in sent_url
        assert "codMonedaSld=CLP" in sent_url
        assert "conDividendos=true" in sent_url

    @respx.mock
    def test_passes_custom_params(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(200, json=[])
        )

        get_portfolio_summary(account_id=42, currency="USD", with_dividends=False)

        sent_url = str(route.calls.last.request.url)
        assert "id=42" in sent_url
        assert "codMonedaSld=USD" in sent_url
        assert "conDividendos=false" in sent_url

    @respx.mock
    def test_picks_latest_query_date(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {**SAMPLE_WIRE_HOLDING, "fechaConsulta": "2026-04-30T00:00:00"},
                    {**SAMPLE_WIRE_HOLDING, "fechaConsulta": "2026-05-01T00:00:00"},
                ],
            )
        )

        portfolio = get_portfolio_summary()
        assert portfolio.query_date == "2026-05-01T00:00:00"

    @respx.mock
    def test_query_date_is_none_for_empty_response(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        portfolio = get_portfolio_summary()
        assert portfolio.query_date is None
        assert portfolio.holdings == ()

    @respx.mock
    def test_skips_non_dict_entries(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(
                200, json=[SAMPLE_WIRE_HOLDING, "not a dict", 42, None]
            )
        )
        portfolio = get_portfolio_summary()
        assert len(portfolio.holdings) == 1

    @respx.mock
    def test_raises_on_4xx(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(403, text="forbidden")
        )
        with pytest.raises(RuntimeError, match=r"Failed to load portfolio summary"):
            get_portfolio_summary()

    @respx.mock
    def test_raises_on_non_array_payload(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PORTFOLIO_URL).mock(
            return_value=httpx.Response(200, json={"oops": "not an array"})
        )
        with pytest.raises(RuntimeError, match="not a JSON array"):
            get_portfolio_summary()
