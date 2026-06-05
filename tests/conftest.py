"""Shared pytest fixtures for nemo-cli."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def credentials_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Populate NEMO_USERNAME / NEMO_PASSWORD with deterministic test values."""
    monkeypatch.setenv("NEMO_USERNAME", "test@example.com")
    monkeypatch.setenv("NEMO_PASSWORD", "test-password")


@pytest.fixture
def no_credentials_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove credentials from the environment so load_credentials() fails."""
    monkeypatch.delenv("NEMO_USERNAME", raising=False)
    monkeypatch.delenv("NEMO_PASSWORD", raising=False)


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
