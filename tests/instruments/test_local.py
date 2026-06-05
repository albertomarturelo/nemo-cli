"""Tests for nemo_cli.instruments.local."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import httpx
import pytest
import respx

from nemo_cli.config import API_BASE_URL
from nemo_cli.instruments.local import (
    DEFAULT_SUBCLASSES,
    LocalInstrument,
    LocalInstrumentsPage,
    _to_instrument,
    list_local_instruments,
)

LOCAL_URL = f"{API_BASE_URL}/shared/Instrumentos/FiltrarInstrumentos"


SAMPLE_WIRE_ITEM: dict[str, object] = {
    "idInstrumento": 1,
    "codPais": "CL",
    "codMoneda": "CLP",
    "codSubClaseInstrumento": "ACC",
    "nemotecnico": "AESANDES",
    "dscInstrumento": "AES ANDES S.A.",
    "isin": "CL0002694637",
    "codClaseInstrumento": "RV_NAC",
    "codigoFamilia": "RV",
}


class TestToInstrument:
    def test_projects_required_fields(self) -> None:
        result = _to_instrument(SAMPLE_WIRE_ITEM)
        assert result.id_instrumento == 1
        assert result.nemotecnico == "AESANDES"
        assert result.descripcion == "AES ANDES S.A."
        assert result.cod_sub_clase == "ACC"
        assert result.cod_clase == "RV_NAC"
        assert result.codigo_familia == "RV"
        assert result.cod_moneda == "CLP"
        assert result.cod_pais == "CL"
        assert result.isin == "CL0002694637"

    def test_treats_blank_isin_as_none(self) -> None:
        item = dict(SAMPLE_WIRE_ITEM)
        item["isin"] = "   "
        result = _to_instrument(item)
        assert result.isin is None

    def test_treats_missing_isin_as_none(self) -> None:
        item = {k: v for k, v in SAMPLE_WIRE_ITEM.items() if k != "isin"}
        result = _to_instrument(item)
        assert result.isin is None

    def test_treats_null_isin_as_none(self) -> None:
        item = dict(SAMPLE_WIRE_ITEM)
        item["isin"] = None  # type: ignore[assignment]
        result = _to_instrument(item)
        assert result.isin is None

    def test_strips_whitespace_from_strings(self) -> None:
        item = dict(SAMPLE_WIRE_ITEM)
        item["nemotecnico"] = "  AESANDES  "
        result = _to_instrument(item)
        assert result.nemotecnico == "AESANDES"

    def test_defaults_missing_int_field_to_zero(self) -> None:
        item = {k: v for k, v in SAMPLE_WIRE_ITEM.items() if k != "idInstrumento"}
        result = _to_instrument(item)
        assert result.id_instrumento == 0

    def test_defaults_missing_string_field_to_empty(self) -> None:
        item = {k: v for k, v in SAMPLE_WIRE_ITEM.items() if k != "nemotecnico"}
        result = _to_instrument(item)
        assert result.nemotecnico == ""

    def test_returns_frozen_dataclass(self) -> None:
        result = _to_instrument(SAMPLE_WIRE_ITEM)
        assert isinstance(result, LocalInstrument)
        with pytest.raises(FrozenInstanceError):
            result.nemotecnico = "OTHER"  # type: ignore[misc]


class TestListLocalInstruments:
    @respx.mock
    def test_returns_page_with_typed_items_and_total(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(
                200, json={"result": [SAMPLE_WIRE_ITEM], "total": 2508}
            )
        )

        page = list_local_instruments()

        assert isinstance(page, LocalInstrumentsPage)
        assert page.total == 2508
        assert len(page.items) == 1
        assert page.items[0].nemotecnico == "AESANDES"

    @respx.mock
    def test_passes_default_subclasses(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(200, json={"result": [], "total": 0})
        )

        list_local_instruments()

        assert route.called
        sent = route.calls.last.request
        # codSubClaseInstrumentos is comma-joined.
        assert "codSubClaseInstrumentos=" + ",".join(DEFAULT_SUBCLASSES) in str(
            sent.url
        ).replace("%2C", ",")

    @respx.mock
    def test_passes_search_and_pagination(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(200, json={"result": [], "total": 0})
        )

        list_local_instruments(search="BCI", page=2, limit=10)

        sent_url = str(route.calls.last.request.url)
        assert "filterNemotecnico=BCI" in sent_url
        assert "page=2" in sent_url
        assert "limit=10" in sent_url

    @respx.mock
    def test_passes_custom_subclasses(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        route = respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(200, json={"result": [], "total": 0})
        )

        list_local_instruments(subclasses=("ACC", "ETF"))

        sent_url = str(route.calls.last.request.url).replace("%2C", ",")
        assert "codSubClaseInstrumentos=ACC,ETF" in sent_url

    @respx.mock
    def test_skips_non_dict_items_in_result(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "result": [SAMPLE_WIRE_ITEM, "not a dict", 123, None],
                    "total": 4,
                },
            )
        )

        page = list_local_instruments()

        # Total stays as reported by the API; items are filtered to dicts only.
        assert page.total == 4
        assert len(page.items) == 1

    @respx.mock
    def test_raises_on_4xx(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(403, text="forbidden")
        )

        with pytest.raises(RuntimeError, match=r"Failed to list local instruments"):
            list_local_instruments()

    @respx.mock
    def test_raises_on_non_object_payload(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(200, json=["unexpected"])
        )

        with pytest.raises(RuntimeError, match="not a JSON object"):
            list_local_instruments()

    @respx.mock
    def test_raises_when_result_missing(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(200, json={"total": 0})
        )

        with pytest.raises(RuntimeError, match="missing 'result' array"):
            list_local_instruments()

    @respx.mock
    def test_raises_when_total_not_int(
        self, cached_token: str  # noqa: ARG002
    ) -> None:
        respx.get(LOCAL_URL).mock(
            return_value=httpx.Response(
                200, json={"result": [], "total": "many"}
            )
        )

        with pytest.raises(RuntimeError, match="missing integer 'total'"):
            list_local_instruments()
