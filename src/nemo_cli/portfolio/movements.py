import re
from dataclasses import dataclass
from typing import Any, Literal, cast

from nemo_cli.api.client import api_request

MovementKind = Literal[
    "dividend",
    "buy",
    "sell",
    "commission",
    "cash_in",
    "cash_out",
    "other",
]


@dataclass(frozen=True)
class DividendInfo:
    ex_date: str | None
    nemotecnico: str
    per_unit_amount: float


@dataclass(frozen=True)
class TradeInfo:
    nemotecnico: str
    side: Literal["buy", "sell"]


@dataclass(frozen=True)
class Movement:
    cash_bucket_id: int
    cash_bucket_name: str
    account: str
    sequence: int
    movement_date: str
    settlement_date: str
    description: str
    kind: MovementKind
    credit: float
    debit: float
    balance: float
    currency: str
    dividend: DividendInfo | None
    trade: TradeInfo | None


@dataclass(frozen=True)
class DividendSummaryItem:
    nemotecnico: str
    total_received: float
    occurrences: int


@dataclass(frozen=True)
class TradeSummaryItem:
    nemotecnico: str
    side: Literal["buy", "sell"]
    total_amount: float
    occurrences: int


@dataclass(frozen=True)
class MovementsSummary:
    total_cash_in: float
    total_cash_out: float
    total_dividends: float
    total_commissions: float
    total_buys: float
    total_sells: float
    by_dividend: tuple[DividendSummaryItem, ...]
    by_trade: tuple[TradeSummaryItem, ...]


@dataclass(frozen=True)
class CashBucket:
    bucket_id: int
    name: str
    movements: tuple[Movement, ...]
    summary: MovementsSummary


@dataclass(frozen=True)
class Movements:
    desde: str
    hasta: str
    buckets: tuple[CashBucket, ...]
    summary: MovementsSummary


_DIVIDEND_PATTERN = re.compile(
    r"^DIV;(\d{1,2}-\d{1,2}-\d{4});([^;]+);([\d,\.]+)$"
)
_TRADE_PATTERN = re.compile(r"^(COMPRA|VENTA) FONDOS CB - (\S+)$")
_COMMISSION_TEXT = "COMISION TRANSACCIÓN BOLSA"
_RUT_PATTERN = re.compile(r"^\d{1,2}(\.\d{3}){0,2}-[\dkK]$")


def get_movements(
    *,
    desde: str,
    hasta: str,
    account_id: int = 0,
) -> Movements:
    params: dict[str, Any] = {
        "id": account_id,
        "tipo": "Cuenta",
        "desde": desde,
        "hasta": hasta,
    }
    # The movements endpoint is markedly slower than the rest. The 180s value
    # is applied by httpx to every phase (connect / read / write / pool); read
    # is the only one that realistically pushes the limit when the server
    # generates a year of activity in one shot. If even this proves
    # insufficient, switch to a structured `httpx.Timeout(connect=10, read=…)`
    # via an `api_request` signature change.
    response = api_request(
        "GET",
        "/frontoffice/shared/MovimientosCajas/Movimientos",
        params=params,
        timeout=180.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to load movements "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, list):
        raise RuntimeError("Movements response was not a JSON array.")

    buckets = tuple(
        _to_bucket(cast(dict[str, object], item))
        for item in cast(list[object], raw)
        if isinstance(item, dict)
    )

    grand_movements = tuple(m for bucket in buckets for m in bucket.movements)
    grand_summary = _summarize(grand_movements)

    return Movements(
        desde=desde,
        hasta=hasta,
        buckets=buckets,
        summary=grand_summary,
    )


def _to_bucket(raw: dict[str, object]) -> CashBucket:
    bucket_id = _as_int(raw.get("idCajaCuenta"))
    name = _as_str(raw.get("dscCajaCuenta"))
    raw_movs = raw.get("movimientos")
    if not isinstance(raw_movs, list):
        movements: tuple[Movement, ...] = ()
    else:
        movements = tuple(
            _to_movement(cast(dict[str, object], item), bucket_id, name)
            for item in cast(list[object], raw_movs)
            if isinstance(item, dict)
        )
    return CashBucket(
        bucket_id=bucket_id,
        name=name,
        movements=movements,
        summary=_summarize(movements),
    )


def _to_movement(
    raw: dict[str, object],
    bucket_id_default: int,
    bucket_name_default: str,
) -> Movement:
    description = _as_str(raw.get("movimiento"))
    credit = _as_float(raw.get("abono"))
    debit = _as_float(raw.get("cargo"))

    kind, dividend, trade = _classify(description, credit, debit)

    return Movement(
        cash_bucket_id=_as_int(raw.get("idCajaCuenta")) or bucket_id_default,
        cash_bucket_name=_as_str(raw.get("dscCajaCuenta")) or bucket_name_default,
        account=_as_str(raw.get("numCuenta")),
        sequence=_as_int(raw.get("orden")),
        movement_date=_as_date(raw.get("fechaMovimiento")),
        settlement_date=_as_date(raw.get("fechaLiquidacion")),
        description=description,
        kind=kind,
        credit=credit,
        debit=debit,
        balance=_as_float(raw.get("saldo")),
        currency=_as_str(raw.get("codMoneda")),
        dividend=dividend,
        trade=trade,
    )


def _classify(
    description: str,
    credit: float,
    debit: float,
) -> tuple[MovementKind, DividendInfo | None, TradeInfo | None]:
    cleaned = description.strip()

    div_match = _DIVIDEND_PATTERN.match(cleaned)
    if div_match is not None:
        ex_dmy, nemo, amount_str = div_match.groups()
        ex_iso: str | None
        try:
            day_str, month_str, year_str = ex_dmy.split("-")
            ex_iso = f"{int(year_str):04d}-{int(month_str):02d}-{int(day_str):02d}"
        except ValueError:
            ex_iso = None
        try:
            per_unit = float(amount_str.replace(",", "."))
        except ValueError:
            per_unit = 0.0
        return (
            "dividend",
            DividendInfo(
                ex_date=ex_iso,
                nemotecnico=nemo.strip(),
                per_unit_amount=per_unit,
            ),
            None,
        )

    trade_match = _TRADE_PATTERN.match(cleaned)
    if trade_match is not None:
        side_es, nemo = trade_match.groups()
        side: Literal["buy", "sell"] = "buy" if side_es == "COMPRA" else "sell"
        return side, None, TradeInfo(nemotecnico=nemo.strip(), side=side)

    if cleaned == _COMMISSION_TEXT:
        return "commission", None, None

    if _RUT_PATTERN.match(cleaned):
        if credit > 0:
            return "cash_in", None, None
        if debit > 0:
            return "cash_out", None, None

    return "other", None, None


def _summarize(movements: tuple[Movement, ...]) -> MovementsSummary:
    total_cash_in = 0.0
    total_cash_out = 0.0
    total_dividends = 0.0
    total_commissions = 0.0
    total_buys = 0.0
    total_sells = 0.0

    div_totals: dict[str, list[float]] = {}
    trade_totals: dict[tuple[str, str], list[float]] = {}

    for mov in movements:
        if mov.kind == "cash_in":
            total_cash_in += mov.credit
        elif mov.kind == "cash_out":
            total_cash_out += mov.debit
        elif mov.kind == "commission":
            total_commissions += mov.debit
        elif mov.kind == "dividend":
            total_dividends += mov.credit
            if mov.dividend is not None:
                bucket = div_totals.setdefault(mov.dividend.nemotecnico, [])
                bucket.append(mov.credit)
        elif mov.kind == "buy":
            total_buys += mov.debit
            if mov.trade is not None:
                key = (mov.trade.nemotecnico, mov.trade.side)
                trade_totals.setdefault(key, []).append(mov.debit)
        elif mov.kind == "sell":
            total_sells += mov.credit
            if mov.trade is not None:
                key = (mov.trade.nemotecnico, mov.trade.side)
                trade_totals.setdefault(key, []).append(mov.credit)
        # "other" kinds intentionally do not contribute to any total.

    by_dividend = tuple(
        sorted(
            (
                DividendSummaryItem(
                    nemotecnico=nemo,
                    total_received=sum(amounts),
                    occurrences=len(amounts),
                )
                for nemo, amounts in div_totals.items()
            ),
            key=lambda item: item.total_received,
            reverse=True,
        )
    )

    by_trade = tuple(
        sorted(
            (
                TradeSummaryItem(
                    nemotecnico=nemo,
                    side=cast(Literal["buy", "sell"], side),
                    total_amount=sum(amounts),
                    occurrences=len(amounts),
                )
                for (nemo, side), amounts in trade_totals.items()
            ),
            key=lambda item: (item.nemotecnico, item.side),
        )
    )

    return MovementsSummary(
        total_cash_in=total_cash_in,
        total_cash_out=total_cash_out,
        total_dividends=total_dividends,
        total_commissions=total_commissions,
        total_buys=total_buys,
        total_sells=total_sells,
        by_dividend=by_dividend,
        by_trade=by_trade,
    )


def _as_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _as_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _as_date(value: object) -> str:
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return value if isinstance(value, str) else ""
