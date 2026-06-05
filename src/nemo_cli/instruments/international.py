from dataclasses import dataclass
from typing import Any, cast

from nemo_cli.api.client import api_request


@dataclass(frozen=True)
class InternationalAsset:
    asset_id: str
    symbol: str
    name: str
    exchange: str
    asset_class: str
    status: str
    tradable: bool
    shortable: bool
    fractionable: bool
    volume: int
    trade_count: int
    cusip: str | None


@dataclass(frozen=True)
class InternationalAssetsPage:
    items: tuple[InternationalAsset, ...]
    total: int


def list_international_assets(
    *,
    search: str = "",
    exchange: str = "",
    page: int = 1,
    page_size: int = 30,
) -> InternationalAssetsPage:
    params: dict[str, Any] = {
        "exchangeName": exchange,
        "search": search,
        "page": page,
        "pageSize": page_size,
    }
    response = api_request("GET", "/frontoffice/shared/Asset", params=params)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to list international assets "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, dict):
        raise RuntimeError("International assets response was not a JSON object.")
    payload = cast(dict[str, object], raw)

    raw_items = payload.get("items")
    raw_total = payload.get("totalCount")
    if not isinstance(raw_items, list):
        raise RuntimeError("International assets response missing 'items' array.")
    if not isinstance(raw_total, int):
        raise RuntimeError("International assets response missing integer 'totalCount'.")

    items = tuple(
        _to_asset(cast(dict[str, object], item))
        for item in cast(list[object], raw_items)
        if isinstance(item, dict)
    )
    return InternationalAssetsPage(items=items, total=raw_total)


def _to_asset(item: dict[str, object]) -> InternationalAsset:
    return InternationalAsset(
        asset_id=_as_str(item.get("id")),
        symbol=_as_str(item.get("symbol")),
        name=_as_str(item.get("name")),
        exchange=_as_str(item.get("exchangeName")),
        asset_class=_as_str(item.get("assetClassName")),
        status=_as_str(item.get("status")),
        tradable=_as_bool(item.get("tradable")),
        shortable=_as_bool(item.get("shortable")),
        fractionable=_as_bool(item.get("fractionable")),
        volume=_as_int(item.get("volume")),
        trade_count=_as_int(item.get("tradeCount")),
        cusip=_as_optional_str(item.get("cusip")),
    )


def _as_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _as_bool(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False
