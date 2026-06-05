from dataclasses import dataclass
from typing import Any, cast

from nemo_cli.api.client import api_request

DEFAULT_SUBCLASSES: tuple[str, ...] = ("ACC", "ACC_INT", "CFI", "ETF", "OPC")


@dataclass(frozen=True)
class LocalInstrument:
    id_instrumento: int
    nemotecnico: str
    descripcion: str
    cod_sub_clase: str
    cod_clase: str
    codigo_familia: str
    cod_moneda: str
    cod_pais: str
    isin: str | None


@dataclass(frozen=True)
class LocalInstrumentsPage:
    items: tuple[LocalInstrument, ...]
    total: int


def list_local_instruments(
    *,
    search: str = "",
    subclasses: tuple[str, ...] = DEFAULT_SUBCLASSES,
    page: int = 1,
    limit: int = 30,
) -> LocalInstrumentsPage:
    params: dict[str, Any] = {
        "page": page,
        "limit": limit,
        "filterNemotecnico": search,
        "codSubClaseInstrumentos": ",".join(subclasses),
    }
    response = api_request("GET", "/shared/Instrumentos/FiltrarInstrumentos", params=params)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to list local instruments "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, dict):
        raise RuntimeError("Local instruments response was not a JSON object.")
    payload = cast(dict[str, object], raw)

    raw_items = payload.get("result")
    raw_total = payload.get("total")
    if not isinstance(raw_items, list):
        raise RuntimeError("Local instruments response missing 'result' array.")
    if not isinstance(raw_total, int):
        raise RuntimeError("Local instruments response missing integer 'total'.")

    items = tuple(
        _to_instrument(cast(dict[str, object], item))
        for item in cast(list[object], raw_items)
        if isinstance(item, dict)
    )
    return LocalInstrumentsPage(items=items, total=raw_total)


def _to_instrument(item: dict[str, object]) -> LocalInstrument:
    return LocalInstrument(
        id_instrumento=_as_int(item.get("idInstrumento")),
        nemotecnico=_as_str(item.get("nemotecnico")),
        descripcion=_as_str(item.get("dscInstrumento")),
        cod_sub_clase=_as_str(item.get("codSubClaseInstrumento")),
        cod_clase=_as_str(item.get("codClaseInstrumento")),
        codigo_familia=_as_str(item.get("codigoFamilia")),
        cod_moneda=_as_str(item.get("codMoneda")),
        cod_pais=_as_str(item.get("codPais")),
        isin=_as_optional_str(item.get("isin")),
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
