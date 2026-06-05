"""Tests for `nemo instruments` CLI commands."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from nemo_cli.cli import app
from nemo_cli.commands.instruments import _sparkline
from nemo_cli.instruments.international import (
    InternationalAsset,
    InternationalAssetsPage,
)
from nemo_cli.instruments.local import LocalInstrument, LocalInstrumentsPage
from nemo_cli.instruments.prices import (
    PriceHistory,
    PriceHistoryStats,
    PricePoint,
)

runner = CliRunner()


def _local_instrument() -> LocalInstrument:
    return LocalInstrument(
        id_instrumento=1,
        nemotecnico="BCI",
        descripcion="BANCO BCI",
        cod_sub_clase="ACC",
        cod_clase="RV_NAC",
        codigo_familia="RV",
        cod_moneda="CLP",
        cod_pais="CL",
        isin="CL0000000001",
    )


def _international_asset() -> InternationalAsset:
    return InternationalAsset(
        asset_id="abc-123",
        symbol="AAPL",
        name="Apple Inc. Common Stock",
        exchange="NASDAQ",
        asset_class="us_equity",
        status="active",
        tradable=True,
        shortable=True,
        fractionable=True,
        volume=1000,
        trade_count=10,
        cusip=None,
    )


def _price_history() -> PriceHistory:
    points = (
        PricePoint(date="2025-01-01", price=100.0, updated_at=None),
        PricePoint(date="2025-01-02", price=110.0, updated_at=None),
    )
    stats = PriceHistoryStats(
        first_date="2025-01-01",
        last_date="2025-01-02",
        first_price=100.0,
        last_price=110.0,
        min_price=100.0,
        min_date="2025-01-01",
        max_price=110.0,
        max_date="2025-01-02",
        mean_price=105.0,
        total_return_pct=0.10,
        daily_return_std_pct=0.0,
        days=2,
    )
    return PriceHistory(instrument_id=42, points=points, stats=stats)


class TestInstrumentsLocal:
    def test_default_table_output(self) -> None:
        page = LocalInstrumentsPage(items=(_local_instrument(),), total=1)
        with patch(
            "nemo_cli.commands.instruments.list_local_instruments",
            return_value=page,
        ):
            result = runner.invoke(app, ["instruments", "local"])
        assert result.exit_code == 0
        assert "BCI" in result.output

    def test_passes_search_and_pagination_args(self) -> None:
        page = LocalInstrumentsPage(items=(), total=0)
        with patch(
            "nemo_cli.commands.instruments.list_local_instruments",
            return_value=page,
        ) as mock_call:
            result = runner.invoke(
                app,
                [
                    "instruments",
                    "local",
                    "--search",
                    "BCI",
                    "--page",
                    "2",
                    "--limit",
                    "10",
                    "--classes",
                    "ACC,ETF",
                ],
            )
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        assert kwargs["search"] == "BCI"
        assert kwargs["page"] == 2
        assert kwargs["limit"] == 10
        assert kwargs["subclasses"] == ("ACC", "ETF")

    def test_json_output_has_documented_envelope(self) -> None:
        page = LocalInstrumentsPage(items=(_local_instrument(),), total=1)
        with patch(
            "nemo_cli.commands.instruments.list_local_instruments",
            return_value=page,
        ):
            result = runner.invoke(
                app, ["instruments", "local", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["market"] == "local"
        assert payload["total"] == 1
        assert payload["page"] == 1
        assert payload["page_size"] == 30
        assert isinstance(payload["items"], list)
        assert payload["items"][0]["nemotecnico"] == "BCI"

    def test_failure_exits_one_with_error_message(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.list_local_instruments",
            side_effect=RuntimeError("api went boom"),
        ):
            result = runner.invoke(app, ["instruments", "local"])
        assert result.exit_code == 1
        assert "api went boom" in result.output


class TestInstrumentsInternational:
    def test_default_table_output(self) -> None:
        page = InternationalAssetsPage(items=(_international_asset(),), total=1)
        with patch(
            "nemo_cli.commands.instruments.list_international_assets",
            return_value=page,
        ):
            result = runner.invoke(app, ["instruments", "international"])
        assert result.exit_code == 0
        assert "AAPL" in result.output

    def test_passes_search_exchange_pagination(self) -> None:
        page = InternationalAssetsPage(items=(), total=0)
        with patch(
            "nemo_cli.commands.instruments.list_international_assets",
            return_value=page,
        ) as mock_call:
            result = runner.invoke(
                app,
                [
                    "instruments",
                    "international",
                    "--search",
                    "aapl",
                    "--exchange",
                    "NASDAQ",
                    "--page",
                    "2",
                    "--page-size",
                    "10",
                ],
            )
        assert result.exit_code == 0
        kwargs = mock_call.call_args.kwargs
        assert kwargs["search"] == "aapl"
        assert kwargs["exchange"] == "NASDAQ"
        assert kwargs["page"] == 2
        assert kwargs["page_size"] == 10

    def test_json_output_has_documented_envelope(self) -> None:
        page = InternationalAssetsPage(items=(_international_asset(),), total=1)
        with patch(
            "nemo_cli.commands.instruments.list_international_assets",
            return_value=page,
        ):
            result = runner.invoke(
                app, ["instruments", "international", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["market"] == "international"
        assert payload["total"] == 1
        assert payload["items"][0]["symbol"] == "AAPL"

    def test_failure_exits_one(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.list_international_assets",
            side_effect=RuntimeError("intl boom"),
        ):
            result = runner.invoke(app, ["instruments", "international"])
        assert result.exit_code == 1
        assert "intl boom" in result.output


class TestInstrumentsPrices:
    def test_default_table_renders_stats_and_sparkline(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            return_value=_price_history(),
        ):
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42"]
            )
        assert result.exit_code == 0
        # Sparkline characters or stats labels should appear.
        assert "Total return" in result.output

    def test_passes_id(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            return_value=_price_history(),
        ) as mock_call:
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42"]
            )
        assert result.exit_code == 0
        assert mock_call.call_args.kwargs["instrument_id"] == 42

    def test_json_output_has_documented_envelope(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            return_value=_price_history(),
        ):
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["instrument_id"] == 42
        assert payload["stats"]["first_price"] == 100.0
        assert payload["stats"]["last_price"] == 110.0
        assert isinstance(payload["points"], list)
        assert len(payload["points"]) == 2

    def test_handles_empty_history_gracefully(self) -> None:
        empty = PriceHistory(instrument_id=42, points=(), stats=None)
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            return_value=empty,
        ):
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42"]
            )
        assert result.exit_code == 0
        assert "No price data" in result.output

    def test_json_output_for_empty_history(self) -> None:
        empty = PriceHistory(instrument_id=42, points=(), stats=None)
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            return_value=empty,
        ):
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["stats"] is None
        assert payload["points"] == []

    def test_id_must_be_integer(self) -> None:
        # UUID-shaped strings (international ids) are rejected by Typer's
        # int conversion before any HTTP call is made.
        result = runner.invoke(
            app,
            ["instruments", "prices", "--id", "abc-123-not-int"],
        )
        assert result.exit_code != 0

    def test_failure_exits_one(self) -> None:
        with patch(
            "nemo_cli.commands.instruments.get_price_history",
            side_effect=RuntimeError("prices boom"),
        ):
            result = runner.invoke(
                app, ["instruments", "prices", "--id", "42"]
            )
        assert result.exit_code == 1
        assert "prices boom" in result.output


class TestSparkline:
    def test_empty_input_returns_empty_string(self) -> None:
        assert _sparkline([]) == ""

    def test_constant_input_returns_uniform_chars(self) -> None:
        spark = _sparkline([5.0, 5.0, 5.0, 5.0])
        assert len(spark) == 4
        # All characters equal — taken from the middle of the spark scale.
        assert len(set(spark)) == 1

    def test_min_to_max_uses_full_range(self) -> None:
        spark = _sparkline([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        # Should include both extremes of the sparkline scale.
        assert spark[0] == "▁"
        assert spark[-1] == "█"

    def test_downsamples_when_longer_than_width(self) -> None:
        prices = list(range(200))
        spark = _sparkline([float(p) for p in prices], width=10)
        assert len(spark) == 10

    def test_uses_full_length_when_shorter_than_width(self) -> None:
        spark = _sparkline([1.0, 2.0, 3.0], width=80)
        assert len(spark) == 3
