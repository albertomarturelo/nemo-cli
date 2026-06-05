"""Tests for nemo_cli.instruments.international."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import httpx
import pytest
import respx

from nemo_cli.config import API_BASE_URL
from nemo_cli.instruments.international import (
    InternationalAsset,
    InternationalAssetsPage,
    _to_asset,
    list_international_assets,
)

INTL_URL = f"{API_BASE_URL}/frontoffice/shared/Asset"


SAMPLE_WIRE_ITEM: dict[str, object] = {
    "id": "41b54729-8470-4593-be38-b3a681871f81",
    "cusip": None,
    "assetClassName": "us_equity",
    "exchangeName": "NASDAQ",
    "symbol": "AAPL",
    "name": "Apple Inc. Common Stock",
    "status": "active",
    "tradable": True,
    "marginable": True,
    "shortable": True,
    "easyToBorrow": True,
    "fractionable": True,
    "tradeCount": 965283,
    "volume": 91998400,
}


class TestToAsset:
    def test_projects_required_fields(self) -> None:
        result = _to_asset(SAMPLE_WIRE_ITEM)
        assert result.asset_id == "41b54729-8470-4593-be38-b3a681871f81"
        assert result.symbol == "AAPL"
        assert result.name == "Apple Inc. Common Stock"
        assert result.exchange == "NASDAQ"
        assert result.asset_class == "us_equity"
        assert result.status == "active"
        assert result.tradable is True
        assert result.shortable is True
        assert result.fractionable is True
        assert result.volume == 91998400
        assert result.trade_count == 965283
        assert result.cusip is None

    def test_treats_missing_bool_as_false(self) -> None:
        item = {k: v for k, v in SAMPLE_WIRE_ITEM.items() if k != "tradable"}
        result = _to_asset(item)
        assert result.tradable is False

    def test_treats_null_cusip_as_none(self) -> None:
        result = _to_asset(SAMPLE_WIRE_ITEM)
        assert result.cusip is None

    def test_returns_frozen_dataclass(self) -> None:
        result = _to_asset(SAMPLE_WIRE_ITEM)
        assert isinstance(result, InternationalAsset)
        with pytest.raises(FrozenInstanceError):
            result.symbol = "OTHER"  # type: ignore[misc]


class TestListInternationalAssets:
    @respx.mock
    def test_returns_page_with_typed_items_and_total(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(
                200, json={"items": [SAMPLE_WIRE_ITEM], "totalCount": 12802}
            )
        )

        page = list_international_assets()

        assert isinstance(page, InternationalAssetsPage)
        assert page.total == 12802
        assert len(page.items) == 1
        assert page.items[0].symbol == "AAPL"

    @respx.mock
    def test_passes_search_exchange_and_pagination(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(INTL_URL).mock(
            return_value=httpx.Response(200, json={"items": [], "totalCount": 0})
        )

        list_international_assets(
            search="aapl", exchange="NASDAQ", page=3, page_size=20
        )

        sent_url = str(route.calls.last.request.url)
        assert "search=aapl" in sent_url
        assert "exchangeName=NASDAQ" in sent_url
        assert "page=3" in sent_url
        assert "pageSize=20" in sent_url

    @respx.mock
    def test_passes_empty_search_and_exchange_by_default(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(INTL_URL).mock(
            return_value=httpx.Response(200, json={"items": [], "totalCount": 0})
        )

        list_international_assets()

        sent_url = str(route.calls.last.request.url)
        # The defaults pass empty strings; the request should still include them.
        assert "search=" in sent_url
        assert "exchangeName=" in sent_url

    @respx.mock
    def test_skips_non_dict_items(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [SAMPLE_WIRE_ITEM, 1, "x", None],
                    "totalCount": 4,
                },
            )
        )

        page = list_international_assets()

        assert page.total == 4
        assert len(page.items) == 1

    @respx.mock
    def test_raises_on_4xx(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(403, text="forbidden")
        )

        with pytest.raises(
            RuntimeError, match=r"Failed to list international assets"
        ):
            list_international_assets()

    @respx.mock
    def test_raises_on_non_object_payload(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(200, json=["unexpected"])
        )

        with pytest.raises(RuntimeError, match="not a JSON object"):
            list_international_assets()

    @respx.mock
    def test_raises_when_items_missing(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(200, json={"totalCount": 0})
        )

        with pytest.raises(RuntimeError, match="missing 'items' array"):
            list_international_assets()

    @respx.mock
    def test_raises_when_total_not_int(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(INTL_URL).mock(
            return_value=httpx.Response(
                200, json={"items": [], "totalCount": "many"}
            )
        )

        with pytest.raises(RuntimeError, match="missing integer 'totalCount'"):
            list_international_assets()
