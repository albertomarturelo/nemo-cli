import statistics
from dataclasses import dataclass
from typing import cast

from nemo_cli.api.client import api_request


@dataclass(frozen=True)
class PricePoint:
    date: str
    price: float
    updated_at: str | None


@dataclass(frozen=True)
class PriceHistoryStats:
    first_date: str
    last_date: str
    first_price: float
    last_price: float
    min_price: float
    min_date: str
    max_price: float
    max_date: str
    mean_price: float
    total_return_pct: float
    daily_return_std_pct: float
    days: int


@dataclass(frozen=True)
class PriceHistory:
    instrument_id: int
    points: tuple[PricePoint, ...]
    stats: PriceHistoryStats | None


def get_price_history(instrument_id: int) -> PriceHistory:
    response = api_request(
        "GET",
        "/frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento",
        params={"idInstrumento": instrument_id},
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to load price history "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, list):
        raise RuntimeError("Price history response was not a JSON array.")

    points = tuple(
        sorted(
            (
                _to_point(cast(dict[str, object], item))
                for item in cast(list[object], raw)
                if isinstance(item, dict)
            ),
            key=lambda p: p.date,
        )
    )
    stats = _compute_stats(points)

    return PriceHistory(
        instrument_id=instrument_id,
        points=points,
        stats=stats,
    )


def _to_point(item: dict[str, object]) -> PricePoint:
    return PricePoint(
        date=_as_date(item.get("fecha")),
        price=_as_float(item.get("precio")),
        updated_at=_as_optional_str(item.get("fechaActualizacion")),
    )


def _compute_stats(points: tuple[PricePoint, ...]) -> PriceHistoryStats | None:
    if not points:
        return None

    prices = [p.price for p in points]
    first_point, last_point = points[0], points[-1]

    min_idx = min(range(len(prices)), key=lambda i: prices[i])
    max_idx = max(range(len(prices)), key=lambda i: prices[i])

    total_return = (
        (last_point.price - first_point.price) / first_point.price
        if first_point.price > 0
        else 0.0
    )

    if len(points) >= 2:
        daily_returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, len(prices))
            if prices[i - 1] > 0
        ]
        daily_std = statistics.stdev(daily_returns) if len(daily_returns) >= 2 else 0.0
    else:
        daily_std = 0.0

    return PriceHistoryStats(
        first_date=first_point.date,
        last_date=last_point.date,
        first_price=first_point.price,
        last_price=last_point.price,
        min_price=points[min_idx].price,
        min_date=points[min_idx].date,
        max_price=points[max_idx].price,
        max_date=points[max_idx].date,
        mean_price=statistics.fmean(prices),
        total_return_pct=total_return,
        daily_return_std_pct=daily_std,
        days=len(points),
    )


def _as_date(value: object) -> str:
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return value if isinstance(value, str) else ""


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _as_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0
