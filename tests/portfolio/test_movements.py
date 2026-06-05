"""Tests for nemo_cli.portfolio.movements."""

from __future__ import annotations

import httpx
import pytest
import respx

from nemo_cli.config import API_BASE_URL
from nemo_cli.portfolio.movements import (
    DividendInfo,
    DividendSummaryItem,
    Movement,
    Movements,
    MovementsSummary,
    TradeInfo,
    TradeSummaryItem,
    _classify,
    _summarize,
    get_movements,
)

MOVEMENTS_URL = f"{API_BASE_URL}/frontoffice/shared/MovimientosCajas/Movimientos"


def _bare_movement(
    *,
    description: str,
    kind: str,
    credit: float = 0.0,
    debit: float = 0.0,
    dividend: DividendInfo | None = None,
    trade: TradeInfo | None = None,
) -> Movement:
    """Build a Movement from a tiny payload — used by aggregator tests."""
    return Movement(
        cash_bucket_id=1,
        cash_bucket_name="CAJA CLP",
        account="99999999/00",
        sequence=1,
        movement_date="2025-06-25",
        settlement_date="2025-06-25",
        description=description,
        kind=kind,  # type: ignore[arg-type]
        credit=credit,
        debit=debit,
        balance=0.0,
        currency="CLP",
        dividend=dividend,
        trade=trade,
    )


class TestClassifyDividend:
    def test_parses_full_dividend_descriptor(self) -> None:
        kind, dividend, trade = _classify(
            "DIV;07-07-2025;CFIHMCREPA;24,1688914293", credit=9909.0, debit=0.0
        )
        assert kind == "dividend"
        assert trade is None
        assert dividend is not None
        assert dividend.nemotecnico == "CFIHMCREPA"
        # Chilean DD-MM-YYYY → ISO YYYY-MM-DD.
        assert dividend.ex_date == "2025-07-07"
        # Chilean decimal-comma → float.
        assert dividend.per_unit_amount == pytest.approx(24.1688914293)

    def test_pads_single_digit_day_and_month(self) -> None:
        _, dividend, _ = _classify(
            "DIV;1-2-2025;CFIX;100", credit=10.0, debit=0.0
        )
        assert dividend is not None
        assert dividend.ex_date == "2025-02-01"

    def test_handles_integer_per_unit(self) -> None:
        _, dividend, _ = _classify(
            "DIV;19-07-2025;CFIMRCLPR;100", credit=2600.0, debit=0.0
        )
        assert dividend is not None
        assert dividend.per_unit_amount == pytest.approx(100.0)

    def test_unknown_format_falls_through_to_other(self) -> None:
        kind, dividend, trade = _classify(
            "DIV-without-semicolons-CFIX", credit=0.0, debit=0.0
        )
        assert kind == "other"
        assert dividend is None
        assert trade is None


class TestClassifyTrade:
    def test_compra_yields_buy(self) -> None:
        kind, dividend, trade = _classify(
            "COMPRA FONDOS CB - CFIHMCREPA", credit=0.0, debit=395356.0
        )
        assert kind == "buy"
        assert dividend is None
        assert trade is not None
        assert trade.nemotecnico == "CFIHMCREPA"
        assert trade.side == "buy"

    def test_venta_yields_sell(self) -> None:
        kind, dividend, trade = _classify(
            "VENTA FONDOS CB - CFIHMCREPA", credit=633356.0, debit=0.0
        )
        assert kind == "sell"
        assert dividend is None
        assert trade is not None
        assert trade.side == "sell"


class TestClassifyCommission:
    def test_exact_text_matches(self) -> None:
        kind, dividend, trade = _classify(
            "COMISION TRANSACCIÓN BOLSA", credit=0.0, debit=1762.0
        )
        assert kind == "commission"
        assert dividend is None
        assert trade is None

    def test_with_surrounding_whitespace(self) -> None:
        kind, _, _ = _classify(
            "  COMISION TRANSACCIÓN BOLSA  ", credit=0.0, debit=1.0
        )
        assert kind == "commission"


class TestClassifyRut:
    def test_rut_with_credit_is_cash_in(self) -> None:
        kind, _, _ = _classify("12.345.678-0", credit=2_000_000.0, debit=0.0)
        assert kind == "cash_in"

    def test_rut_with_debit_is_cash_out(self) -> None:
        kind, _, _ = _classify("12.345.678-0", credit=0.0, debit=633_357.0)
        assert kind == "cash_out"

    def test_rut_with_no_amount_falls_to_other(self) -> None:
        # Defensive: if abono and cargo are both zero, no flow direction.
        kind, _, _ = _classify("12.345.678-0", credit=0.0, debit=0.0)
        assert kind == "other"

    def test_rut_with_k_verifier(self) -> None:
        kind, _, _ = _classify("12.345.678-K", credit=100.0, debit=0.0)
        assert kind == "cash_in"


class TestClassifyOther:
    def test_random_text(self) -> None:
        kind, dividend, trade = _classify("some random thing", 0.0, 0.0)
        assert kind == "other"
        assert dividend is None
        assert trade is None

    def test_empty_string(self) -> None:
        kind, _, _ = _classify("", 0.0, 0.0)
        assert kind == "other"


class TestSummarize:
    def test_empty_returns_zero_summary(self) -> None:
        result = _summarize(())
        assert isinstance(result, MovementsSummary)
        assert result.total_cash_in == 0
        assert result.total_cash_out == 0
        assert result.total_dividends == 0
        assert result.total_commissions == 0
        assert result.total_buys == 0
        assert result.total_sells == 0
        assert result.by_dividend == ()
        assert result.by_trade == ()

    def test_aggregates_each_kind(self) -> None:
        movements = (
            _bare_movement(
                description="12.345.678-0", kind="cash_in", credit=1_000_000.0
            ),
            _bare_movement(
                description="12.345.678-0", kind="cash_out", debit=200_000.0
            ),
            _bare_movement(
                description="DIV;…", kind="dividend", credit=10_000.0,
                dividend=DividendInfo(ex_date="2025-07-07", nemotecnico="A", per_unit_amount=24.0),
            ),
            _bare_movement(
                description="DIV;…", kind="dividend", credit=5_000.0,
                dividend=DividendInfo(ex_date="2025-08-07", nemotecnico="A", per_unit_amount=12.0),
            ),
            _bare_movement(
                description="DIV;…", kind="dividend", credit=2_500.0,
                dividend=DividendInfo(ex_date="2025-08-07", nemotecnico="B", per_unit_amount=100.0),
            ),
            _bare_movement(
                description="COMISION TRANSACCIÓN BOLSA",
                kind="commission",
                debit=1_500.0,
            ),
            _bare_movement(
                description="COMPRA FONDOS CB - X",
                kind="buy",
                debit=300_000.0,
                trade=TradeInfo(nemotecnico="X", side="buy"),
            ),
            _bare_movement(
                description="COMPRA FONDOS CB - X",
                kind="buy",
                debit=100_000.0,
                trade=TradeInfo(nemotecnico="X", side="buy"),
            ),
            _bare_movement(
                description="VENTA FONDOS CB - X",
                kind="sell",
                credit=500_000.0,
                trade=TradeInfo(nemotecnico="X", side="sell"),
            ),
        )

        result = _summarize(movements)

        assert result.total_cash_in == 1_000_000.0
        assert result.total_cash_out == 200_000.0
        assert result.total_dividends == 17_500.0
        assert result.total_commissions == 1_500.0
        assert result.total_buys == 400_000.0
        assert result.total_sells == 500_000.0

    def test_by_dividend_sorted_by_total_descending(self) -> None:
        low = DividendInfo(ex_date="2025-07-07", nemotecnico="LOW", per_unit_amount=1.0)
        high = DividendInfo(ex_date="2025-07-07", nemotecnico="HIGH", per_unit_amount=1.0)
        mid = DividendInfo(ex_date="2025-07-08", nemotecnico="MID", per_unit_amount=1.0)
        movements = (
            _bare_movement(description="DIV;…", kind="dividend", credit=100.0, dividend=low),
            _bare_movement(description="DIV;…", kind="dividend", credit=10_000.0, dividend=high),
            _bare_movement(description="DIV;…", kind="dividend", credit=500.0, dividend=mid),
        )

        result = _summarize(movements)
        nemos = [item.nemotecnico for item in result.by_dividend]
        assert nemos == ["HIGH", "MID", "LOW"]

    def test_by_dividend_aggregates_same_nemo(self) -> None:
        movements = (
            _bare_movement(
                description="DIV;…", kind="dividend", credit=100.0,
                dividend=DividendInfo(ex_date="2025-07-07", nemotecnico="X", per_unit_amount=1.0),
            ),
            _bare_movement(
                description="DIV;…", kind="dividend", credit=200.0,
                dividend=DividendInfo(ex_date="2025-08-07", nemotecnico="X", per_unit_amount=2.0),
            ),
            _bare_movement(
                description="DIV;…", kind="dividend", credit=300.0,
                dividend=DividendInfo(ex_date="2025-09-07", nemotecnico="X", per_unit_amount=3.0),
            ),
        )

        result = _summarize(movements)
        assert len(result.by_dividend) == 1
        item = result.by_dividend[0]
        assert isinstance(item, DividendSummaryItem)
        assert item.nemotecnico == "X"
        assert item.total_received == 600.0
        assert item.occurrences == 3

    def test_by_trade_aggregates_per_nemo_and_side(self) -> None:
        movements = (
            _bare_movement(
                description="COMPRA FONDOS CB - X", kind="buy", debit=100.0,
                trade=TradeInfo(nemotecnico="X", side="buy"),
            ),
            _bare_movement(
                description="COMPRA FONDOS CB - X", kind="buy", debit=200.0,
                trade=TradeInfo(nemotecnico="X", side="buy"),
            ),
            _bare_movement(
                description="VENTA FONDOS CB - X", kind="sell", credit=300.0,
                trade=TradeInfo(nemotecnico="X", side="sell"),
            ),
            _bare_movement(
                description="COMPRA FONDOS CB - Y", kind="buy", debit=50.0,
                trade=TradeInfo(nemotecnico="Y", side="buy"),
            ),
        )

        result = _summarize(movements)
        # Ordered by (nemotecnico, side).
        assert [(t.nemotecnico, t.side) for t in result.by_trade] == [
            ("X", "buy"),
            ("X", "sell"),
            ("Y", "buy"),
        ]
        x_buy = result.by_trade[0]
        assert isinstance(x_buy, TradeSummaryItem)
        assert x_buy.total_amount == 300.0
        assert x_buy.occurrences == 2

    def test_other_kind_is_ignored_in_totals(self) -> None:
        movements = (
            _bare_movement(description="random", kind="other", credit=999.0, debit=999.0),
        )
        result = _summarize(movements)
        assert result.total_cash_in == 0
        assert result.total_cash_out == 0
        assert result.total_dividends == 0


SAMPLE_WIRE_MOVEMENT: dict[str, object] = {
    "idCajaCuenta": 732706,
    "orden": 1,
    "dscCajaCuenta": "CAJA CLP",
    "idCuenta": 426774,
    "fechaMovimiento": "2025-06-25T00:00:00",
    "fechaLiquidacion": "2025-06-25T00:00:00",
    "numCuenta": "99999999/00",
    "dscCuenta": "Test User",
    "abrNegocio": "CDB",
    "tipo": None,
    "movimiento": "12.345.678-0",
    "abono": 2_000_000.0,
    "cargo": 0.0,
    "saldo": 2_000_000.0,
    "codMoneda": "CLP",
    "codTipoCarAboCaja": "A",
}


SAMPLE_WIRE_BUCKET: dict[str, object] = {
    "idCajaCuenta": 732706,
    "dscCajaCuenta": "CAJA CLP",
    "movimientos": [SAMPLE_WIRE_MOVEMENT],
}


class TestGetMovements:
    @respx.mock
    def test_returns_typed_movements_with_summary(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[SAMPLE_WIRE_BUCKET])
        )

        result = get_movements(desde="2025-01-01", hasta="2026-01-01")

        assert isinstance(result, Movements)
        assert result.desde == "2025-01-01"
        assert result.hasta == "2026-01-01"
        assert len(result.buckets) == 1
        bucket = result.buckets[0]
        assert bucket.bucket_id == 732706
        assert bucket.name == "CAJA CLP"
        assert len(bucket.movements) == 1
        movement = bucket.movements[0]
        assert movement.kind == "cash_in"
        assert movement.credit == 2_000_000.0
        assert movement.movement_date == "2025-06-25"
        # Per-bucket and grand summary both reflect the cash_in.
        assert bucket.summary.total_cash_in == 2_000_000.0
        assert result.summary.total_cash_in == 2_000_000.0

    @respx.mock
    def test_passes_query_params(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[])
        )

        get_movements(
            desde="2025-01-18",
            hasta="2026-01-25",
            account_id=42,
        )

        sent_url = str(route.calls.last.request.url)
        assert "id=42" in sent_url
        assert "tipo=Cuenta" in sent_url
        assert "desde=2025-01-18" in sent_url
        assert "hasta=2026-01-25" in sent_url

    @respx.mock
    def test_aggregates_across_buckets(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        bucket_clp = SAMPLE_WIRE_BUCKET
        bucket_usd = {
            "idCajaCuenta": 999,
            "dscCajaCuenta": "CAJA USD",
            "movimientos": [
                {
                    **SAMPLE_WIRE_MOVEMENT,
                    "idCajaCuenta": 999,
                    "dscCajaCuenta": "CAJA USD",
                    "abono": 500.0,
                    "saldo": 500.0,
                    "codMoneda": "USD",
                }
            ],
        }
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[bucket_clp, bucket_usd])
        )

        result = get_movements(desde="2025-01-01", hasta="2026-01-01")

        assert len(result.buckets) == 2
        # Grand summary sums across buckets.
        assert result.summary.total_cash_in == 2_000_500.0

    @respx.mock
    def test_empty_response_yields_no_buckets(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        result = get_movements(desde="2025-01-01", hasta="2026-01-01")
        assert result.buckets == ()
        assert result.summary.total_cash_in == 0

    @respx.mock
    def test_skips_non_dict_buckets(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(
                200, json=[SAMPLE_WIRE_BUCKET, "not a dict", 42, None]
            )
        )
        result = get_movements(desde="2025-01-01", hasta="2026-01-01")
        assert len(result.buckets) == 1

    @respx.mock
    def test_handles_bucket_with_missing_movements(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        bucket_no_movs = {"idCajaCuenta": 123, "dscCajaCuenta": "CAJA EUR"}
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[bucket_no_movs])
        )
        result = get_movements(desde="2025-01-01", hasta="2026-01-01")
        assert result.buckets[0].movements == ()
        assert result.summary.total_cash_in == 0

    @respx.mock
    def test_dividend_descriptor_is_classified_in_pipeline(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        bucket = {
            "idCajaCuenta": 1,
            "dscCajaCuenta": "CAJA CLP",
            "movimientos": [
                {
                    **SAMPLE_WIRE_MOVEMENT,
                    "movimiento": "DIV;07-07-2025;CFIHMCREPA;24,1688914293",
                    "abono": 9909.0,
                    "cargo": 0.0,
                }
            ],
        }
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json=[bucket])
        )

        result = get_movements(desde="2025-01-01", hasta="2026-01-01")
        movement = result.buckets[0].movements[0]
        assert movement.kind == "dividend"
        assert movement.dividend is not None
        assert movement.dividend.nemotecnico == "CFIHMCREPA"
        # Grand summary has the per-nemotécnico aggregate ready for the agent.
        assert result.summary.by_dividend[0].nemotecnico == "CFIHMCREPA"
        assert result.summary.by_dividend[0].total_received == 9909.0

    @respx.mock
    def test_raises_on_4xx(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(403, text="forbidden")
        )

        with pytest.raises(RuntimeError, match=r"Failed to load movements"):
            get_movements(desde="2025-01-01", hasta="2026-01-01")

    @respx.mock
    def test_raises_on_non_array_payload(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(MOVEMENTS_URL).mock(
            return_value=httpx.Response(200, json={"oops": "object"})
        )

        with pytest.raises(RuntimeError, match="not a JSON array"):
            get_movements(desde="2025-01-01", hasta="2026-01-01")
