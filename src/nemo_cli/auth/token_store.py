import json
from pathlib import Path
from typing import cast

from platformdirs import user_config_path

_APP_NAME = "nemo-cli"


def _config_file() -> Path:
    return user_config_path(_APP_NAME, ensure_exists=True) / "token.json"


def get_token() -> str | None:
    path = _config_file()
    if not path.exists():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    data = cast(dict[str, object], raw)
    token = data.get("token")
    return token if isinstance(token, str) and token else None


def set_token(token: str) -> None:
    path = _config_file()
    path.write_text(json.dumps({"token": token}), encoding="utf-8")


def clear_token() -> None:
    path = _config_file()
    if path.exists():
        path.unlink()
