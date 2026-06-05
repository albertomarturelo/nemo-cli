"""Tests for nemo_cli.instruments.prices."""

from __future__ import annotations

import httpx
import pytest
import respx

from nemo_cli.config import API_BASE_URL
from nemo_cli.instruments.prices import (
    PriceHistory,
    PriceHistoryStats,
    PricePoint,
    _compute_stats,
    _to_point,
    get_price_history,
)

PRICES_URL = f"{API_BASE_URL}/frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento"


SAMPLE_WIRE_POINT: dict[str, object] = {
    "idInstrumento": 52185,
    "fecha": "2025-05-02T00:00:00",
    "precio": 18141.44,
    "fechaActualizacion": "2025-05-02T16:54:59.997",
}


class TestToPoint:
    def test_truncates_iso_datetime_to_date(self) -> None:
        point = _to_point(SAMPLE_WIRE_POINT)
        assert point.date == "2025-05-02"

    def test_keeps_short_date_string_as_is(self) -> None:
        point = _to_point({**SAMPLE_WIRE_POINT, "fecha": "2025-05-02"})
        assert point.date == "2025-05-02"

    def test_returns_empty_date_when_missing(self) -> None:
        point = _to_point({k: v for k, v in SAMPLE_WIRE_POINT.items() if k != "fecha"})
        assert point.date == ""

    def test_treats_null_updated_at_as_none(self) -> None:
        point = _to_point({**SAMPLE_WIRE_POINT, "fechaActualizacion": None})
        assert point.updated_at is None

    def test_treats_blank_updated_at_as_none(self) -> None:
        point = _to_point({**SAMPLE_WIRE_POINT, "fechaActualizacion": "   "})
        assert point.updated_at is None

    def test_parses_int_price(self) -> None:
        point = _to_point({**SAMPLE_WIRE_POINT, "precio": 100})
        assert point.price == 100.0

    def test_defaults_missing_price_to_zero(self) -> None:
        point = _to_point({k: v for k, v in SAMPLE_WIRE_POINT.items() if k != "precio"})
        assert point.price == 0.0


class TestComputeStats:
    def test_returns_none_for_empty_points(self) -> None:
        assert _compute_stats(()) is None

    def test_single_point_yields_zero_return_and_volatility(self) -> None:
        single = (PricePoint(date="2025-01-01", price=100.0, updated_at=None),)
        stats = _compute_stats(single)
        assert stats is not None
        assert stats.first_price == 100.0
        assert stats.last_price == 100.0
        assert stats.min_price == 100.0
        assert stats.max_price == 100.0
        assert stats.mean_price == 100.0
        assert stats.total_return_pct == 0.0
        assert stats.daily_return_std_pct == 0.0
        assert stats.days == 1

    def test_two_points_compute_total_return(self) -> None:
        points = (
            PricePoint(date="2025-01-01", price=100.0, updated_at=None),
            PricePoint(date="2025-01-02", price=110.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        # (110 - 100) / 100 = 0.10
        assert stats.total_return_pct == pytest.approx(0.10)
        # Only one daily return → stdev requires ≥ 2 → daily σ stays 0.
        assert stats.daily_return_std_pct == 0.0
        assert stats.days == 2

    def test_three_points_compute_daily_std(self) -> None:
        points = (
            PricePoint(date="2025-01-01", price=100.0, updated_at=None),
            PricePoint(date="2025-01-02", price=110.0, updated_at=None),
            PricePoint(date="2025-01-03", price=121.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        # Daily returns: 0.10 and 0.10 → stdev should be 0 (no variance).
        assert stats.daily_return_std_pct == pytest.approx(0.0)

    def test_min_max_dates_correct(self) -> None:
        points = (
            PricePoint(date="2025-01-01", price=100.0, updated_at=None),
            PricePoint(date="2025-01-02", price=80.0, updated_at=None),
            PricePoint(date="2025-01-03", price=120.0, updated_at=None),
            PricePoint(date="2025-01-04", price=110.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        assert stats.min_price == 80.0
        assert stats.min_date == "2025-01-02"
        assert stats.max_price == 120.0
        assert stats.max_date == "2025-01-03"

    def test_first_price_zero_yields_zero_total_return(self) -> None:
        # Defensive against pathological data.
        points = (
            PricePoint(date="2025-01-01", price=0.0, updated_at=None),
            PricePoint(date="2025-01-02", price=10.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        assert stats.total_return_pct == 0.0

    def test_skips_zero_prev_price_in_daily_returns(self) -> None:
        # If a previous price is 0, that step is omitted from the daily
        # returns (avoiding div-by-zero) but the rest still compute.
        points = (
            PricePoint(date="2025-01-01", price=100.0, updated_at=None),
            PricePoint(date="2025-01-02", price=0.0, updated_at=None),
            PricePoint(date="2025-01-03", price=110.0, updated_at=None),
            PricePoint(date="2025-01-04", price=121.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        # Should not raise.
        assert stats.days == 4

    def test_mean_price_uses_all_points(self) -> None:
        points = (
            PricePoint(date="2025-01-01", price=100.0, updated_at=None),
            PricePoint(date="2025-01-02", price=200.0, updated_at=None),
            PricePoint(date="2025-01-03", price=300.0, updated_at=None),
        )
        stats = _compute_stats(points)
        assert stats is not None
        assert stats.mean_price == pytest.approx(200.0)


class TestGetPriceHistory:
    @respx.mock
    def test_returns_history_with_points_and_stats(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        wire = [
            SAMPLE_WIRE_POINT,
            {**SAMPLE_WIRE_POINT, "fecha": "2025-05-03T00:00:00", "precio": 18056.26},
            {**SAMPLE_WIRE_POINT, "fecha": "2025-05-04T00:00:00", "precio": 18056.26},
        ]
        respx.get(PRICES_URL).mock(return_value=httpx.Response(200, json=wire))

        history = get_price_history(instrument_id=52185)

        assert isinstance(history, PriceHistory)
        assert history.instrument_id == 52185
        assert len(history.points) == 3
        assert history.stats is not None
        assert isinstance(history.stats, PriceHistoryStats)
        assert history.stats.first_date == "2025-05-02"
        assert history.stats.last_date == "2025-05-04"

    @respx.mock
    def test_sorts_points_by_date_even_if_api_returns_unsorted(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        wire = [
            {**SAMPLE_WIRE_POINT, "fecha": "2025-05-04T00:00:00", "precio": 200.0},
            {**SAMPLE_WIRE_POINT, "fecha": "2025-05-02T00:00:00", "precio": 100.0},
            {**SAMPLE_WIRE_POINT, "fecha": "2025-05-03T00:00:00", "precio": 150.0},
        ]
        respx.get(PRICES_URL).mock(return_value=httpx.Response(200, json=wire))

        history = get_price_history(instrument_id=52185)
        dates = [p.date for p in history.points]
        assert dates == ["2025-05-02", "2025-05-03", "2025-05-04"]

    @respx.mock
    def test_passes_id_in_query(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(PRICES_URL).mock(
            return_value=httpx.Response(200, json=[])
        )

        get_price_history(instrument_id=42)

        sent_url = str(route.calls.last.request.url)
        assert "idInstrumento=42" in sent_url

    @respx.mock
    def test_empty_response_yields_no_stats(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PRICES_URL).mock(return_value=httpx.Response(200, json=[]))

        history = get_price_history(instrument_id=52185)

        assert history.points == ()
        assert history.stats is None

    @respx.mock
    def test_skips_non_dict_entries(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PRICES_URL).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_WIRE_POINT, "not a dict", 42, None],
            )
        )

        history = get_price_history(instrument_id=52185)
        assert len(history.points) == 1

    @respx.mock
    def test_raises_on_4xx(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PRICES_URL).mock(
            return_value=httpx.Response(404, text="not found")
        )

        with pytest.raises(RuntimeError, match=r"Failed to load price history"):
            get_price_history(instrument_id=52185)

    @respx.mock
    def test_raises_on_non_array_payload(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(PRICES_URL).mock(
            return_value=httpx.Response(200, json={"unexpected": "shape"})
        )

        with pytest.raises(RuntimeError, match="not a JSON array"):
            get_price_history(instrument_id=52185)
