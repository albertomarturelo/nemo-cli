"""Tests for `nemo portfolio` CLI commands."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from nemo_cli.cli import app
from nemo_cli.portfolio.movements import (
    CashBucket,
    DividendInfo,
    DividendSummaryItem,
    Movement,
    Movements,
    MovementsSummary,
    TradeInfo,
    TradeSummaryItem,
)
from nemo_cli.portfolio.summary import (
    ClassificationTotal,
    Portfolio,
    PortfolioHolding,
    PortfolioTotals,
)

runner = CliRunner()


def _holding(*, classification: str = "RENTA FIJA") -> PortfolioHolding:
    return PortfolioHolding(
        account="99999999/00",
        account_description="Test User",
        classification=classification,
        sub_classification="Sub",
        instrument_id=1,
        nemotecnico="CFIMRCLPR",
        descripcion="MONEDA RENTA CLP FI",
        sub_class="CFI",
        series=None,
        currency="CLP",
        quantity=100.0,
        avg_buy_price=18000.0,
        market_price=18500.0,
        cost_basis=1800000.0,
        market_value=1850000.0,
        pnl=50000.0,
        pnl_pct=50000.0 / 1800000.0,
        query_date="2026-05-01T00:00:00",
    )


def _portfolio() -> Portfolio:
    holding = _holding()
    totals = PortfolioTotals(
        market_value=1850000.0,
        cost_basis=1800000.0,
        pnl=50000.0,
        pnl_pct=50000.0 / 1800000.0,
        by_classification=(
            ClassificationTotal(
                classification="RENTA FIJA",
                market_value=1850000.0,
                cost_basis=1800000.0,
                pnl=50000.0,
                pnl_pct=50000.0 / 1800000.0,
            ),
        ),
    )
    return Portfolio(
        currency="CLP",
        query_date="2026-05-01T00:00:00",
        holdings=(holding,),
        totals=totals,
    )


def _empty_portfolio() -> Portfolio:
    return Portfolio(
        currency="CLP",
        query_date=None,
        holdings=(),
        totals=PortfolioTotals(
            market_value=0.0,
            cost_basis=0.0,
            pnl=0.0,
            pnl_pct=0.0,
            by_classification=(),
        ),
    )


class TestPortfolioSummary:
    def test_default_table_renders_holdings_and_totals(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            return_value=_portfolio(),
        ):
            result = runner.invoke(app, ["portfolio", "summary"])
        assert result.exit_code == 0
        # Holding nemotecnico appears in the holdings table.
        assert "CFIMRCLPR" in result.output
        # Classification appears in the by-classification table.
        assert "RENTA FIJA" in result.output

    def test_passes_default_args(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            return_value=_portfolio(),
        ) as mock_call:
            result = runner.invoke(app, ["portfolio", "summary"])
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        assert kwargs["account_id"] == 0
        assert kwargs["currency"] == "CLP"
        assert kwargs["with_dividends"] is True

    def test_passes_custom_args(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            return_value=_portfolio(),
        ) as mock_call:
            result = runner.invoke(
                app,
                [
                    "portfolio",
                    "summary",
                    "--account-id",
                    "42",
                    "--currency",
                    "USD",
                    "--no-dividends",
                ],
            )
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        assert kwargs["account_id"] == 42
        assert kwargs["currency"] == "USD"
        assert kwargs["with_dividends"] is False

    def test_json_output_has_documented_envelope(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            return_value=_portfolio(),
        ):
            result = runner.invoke(
                app, ["portfolio", "summary", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["currency"] == "CLP"
        assert payload["query_date"] == "2026-05-01T00:00:00"
        assert payload["totals"]["market_value"] == 1850000.0
        assert isinstance(payload["totals"]["by_classification"], list)
        assert isinstance(payload["holdings"], list)
        assert payload["holdings"][0]["nemotecnico"] == "CFIMRCLPR"

    def test_empty_portfolio_renders_friendly_message(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            return_value=_empty_portfolio(),
        ):
            result = runner.invoke(app, ["portfolio", "summary"])
        assert result.exit_code == 0
        assert "no holdings returned" in result.output

    def test_failure_exits_one(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_portfolio_summary",
            side_effect=RuntimeError("portfolio boom"),
        ):
            result = runner.invoke(app, ["portfolio", "summary"])
        assert result.exit_code == 1
        assert "portfolio boom" in result.output


def _movement_dividend() -> Movement:
    return Movement(
        cash_bucket_id=1,
        cash_bucket_name="CAJA CLP",
        account="99999999/00",
        sequence=1,
        movement_date="2025-07-11",
        settlement_date="2025-07-11",
        description="DIV;07-07-2025;CFIHMCREPA;24,1688914293",
        kind="dividend",
        credit=9909.0,
        debit=0.0,
        balance=17551.0,
        currency="CLP",
        dividend=DividendInfo(
            ex_date="2025-07-07", nemotecnico="CFIHMCREPA", per_unit_amount=24.1688914293
        ),
        trade=None,
    )


def _movement_buy() -> Movement:
    return Movement(
        cash_bucket_id=1,
        cash_bucket_name="CAJA CLP",
        account="99999999/00",
        sequence=2,
        movement_date="2025-06-26",
        settlement_date="2025-06-26",
        description="COMPRA FONDOS CB - CFIHMCREPA",
        kind="buy",
        credit=0.0,
        debit=395356.0,
        balance=1104653.0,
        currency="CLP",
        dividend=None,
        trade=TradeInfo(nemotecnico="CFIHMCREPA", side="buy"),
    )


def _movements() -> Movements:
    summary = MovementsSummary(
        total_cash_in=2_000_000.0,
        total_cash_out=0.0,
        total_dividends=9909.0,
        total_commissions=1762.0,
        total_buys=395356.0,
        total_sells=0.0,
        by_dividend=(
            DividendSummaryItem(
                nemotecnico="CFIHMCREPA",
                total_received=9909.0,
                occurrences=1,
            ),
        ),
        by_trade=(
            TradeSummaryItem(
                nemotecnico="CFIHMCREPA",
                side="buy",
                total_amount=395356.0,
                occurrences=1,
            ),
        ),
    )
    bucket = CashBucket(
        bucket_id=732706,
        name="CAJA CLP",
        movements=(_movement_dividend(), _movement_buy()),
        summary=summary,
    )
    return Movements(
        desde="2025-01-01",
        hasta="2026-01-01",
        buckets=(bucket,),
        summary=summary,
    )


def _empty_movements() -> Movements:
    summary = MovementsSummary(
        total_cash_in=0.0,
        total_cash_out=0.0,
        total_dividends=0.0,
        total_commissions=0.0,
        total_buys=0.0,
        total_sells=0.0,
        by_dividend=(),
        by_trade=(),
    )
    return Movements(
        desde="2025-01-01",
        hasta="2026-01-01",
        buckets=(),
        summary=summary,
    )


class TestPortfolioMovements:
    def test_default_panel_renders_summary_and_dividends(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            return_value=_movements(),
        ):
            result = runner.invoke(app, ["portfolio", "movements"])
        assert result.exit_code == 0
        # Both the dividends table and the trades table appear.
        assert "CFIHMCREPA" in result.output
        assert "Dividends by instrument" in result.output
        assert "Trades by instrument" in result.output

    def test_passes_explicit_dates(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            return_value=_movements(),
        ) as mock_call:
            result = runner.invoke(
                app,
                [
                    "portfolio",
                    "movements",
                    "--desde",
                    "2025-01-18",
                    "--hasta",
                    "2026-01-25",
                    "--account-id",
                    "42",
                ],
            )
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        assert kwargs["desde"] == "2025-01-18"
        assert kwargs["hasta"] == "2026-01-25"
        assert kwargs["account_id"] == 42

    def test_uses_default_dates_when_omitted(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            return_value=_movements(),
        ) as mock_call:
            result = runner.invoke(app, ["portfolio", "movements"])
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        # YYYY-MM-DD shape, no None passthrough.
        assert isinstance(kwargs["desde"], str)
        assert isinstance(kwargs["hasta"], str)
        assert len(kwargs["desde"]) == 10
        assert len(kwargs["hasta"]) == 10

    def test_json_envelope_shape(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            return_value=_movements(),
        ):
            result = runner.invoke(
                app, ["portfolio", "movements", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["desde"] == "2025-01-01"
        assert payload["hasta"] == "2026-01-01"
        # Grand summary is at the top level.
        assert payload["summary"]["total_dividends"] == 9909.0
        # by_dividend is precomputed and sorted.
        assert payload["summary"]["by_dividend"][0]["nemotecnico"] == "CFIHMCREPA"
        # Buckets carry their own summary plus full movements.
        bucket = payload["buckets"][0]
        assert bucket["bucket_id"] == 732706
        assert bucket["name"] == "CAJA CLP"
        assert bucket["summary"]["total_dividends"] == 9909.0
        # Each movement's `kind` is present and its dividend payload too.
        first_movement = bucket["movements"][0]
        assert first_movement["kind"] == "dividend"
        assert first_movement["dividend"]["nemotecnico"] == "CFIHMCREPA"

    def test_empty_movements_renders_friendly_message(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            return_value=_empty_movements(),
        ):
            result = runner.invoke(app, ["portfolio", "movements"])
        assert result.exit_code == 0
        assert "no movements returned" in result.output

    def test_failure_exits_one(self) -> None:
        with patch(
            "nemo_cli.commands.portfolio.get_movements",
            side_effect=RuntimeError("movements boom"),
        ):
            result = runner.invoke(app, ["portfolio", "movements"])
        assert result.exit_code == 1
        assert "movements boom" in result.output
