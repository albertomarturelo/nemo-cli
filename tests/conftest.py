"""Shared pytest fixtures for nemo-cli."""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def jwt_factory() -> Callable[[int], str]:
    """Return a builder for a minimal JWT whose `exp` is `now + offset` seconds.

    Negative offsets produce already-expired tokens; large positive offsets
    produce comfortably-fresh ones. Only the `exp` claim and the three-segment
    shape matter to the readers (`auth.jwt`, `auth.session`, `api.client`).
    """

    def _build(exp_offset_seconds: int) -> str:
        header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
        payload = (
            base64.urlsafe_b64encode(
                json.dumps({"exp": int(time.time()) + exp_offset_seconds}).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        return f"{header}.{payload}.signature"

    return _build


@pytest.fixture
def isolated_token_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect the token-cache file to a unique tmp path. Returns the file path."""
    token_dir = tmp_path / "nemo-cli"
    token_dir.mkdir()
    token_file = token_dir / "token.json"

    from nemo_cli.auth import token_store as ts

    monkeypatch.setattr(ts, "_config_file", lambda: token_file)
    return token_file


@pytest.fixture
def cached_token(isolated_token_store: Path) -> str:
    """Pre-populate the isolated token store with a known token. Returns the token."""
    token = "cached.jwt.token"
    isolated_token_store.write_text('{"token": "cached.jwt.token"}', encoding="utf-8")
    return token
