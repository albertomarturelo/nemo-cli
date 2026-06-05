"""Tests for nemo_cli.auth.token_store."""

from __future__ import annotations

import json
from pathlib import Path

from nemo_cli.auth.token_store import clear_token, get_token, set_token


class TestGetToken:
    def test_returns_none_when_file_missing(
        self, isolated_token_store: Path
    ) -> None:
        # Fixture creates the dir but no file.
        assert not isolated_token_store.exists()
        assert get_token() is None

    def test_returns_token_from_file(self, cached_token: str) -> None:
        assert get_token() == cached_token

    def test_returns_none_on_invalid_json(
        self, isolated_token_store: Path
    ) -> None:
        isolated_token_store.write_text("{this is not json", encoding="utf-8")
        assert get_token() is None

    def test_returns_none_when_payload_is_not_dict(
        self, isolated_token_store: Path
    ) -> None:
        isolated_token_store.write_text("[1, 2, 3]", encoding="utf-8")
        assert get_token() is None

    def test_returns_none_when_token_field_missing(
        self, isolated_token_store: Path
    ) -> None:
        isolated_token_store.write_text(
            json.dumps({"other": "field"}), encoding="utf-8"
        )
        assert get_token() is None

    def test_returns_none_when_token_is_empty_string(
        self, isolated_token_store: Path
    ) -> None:
        isolated_token_store.write_text(
            json.dumps({"token": ""}), encoding="utf-8"
        )
        assert get_token() is None

    def test_returns_none_when_token_is_not_string(
        self, isolated_token_store: Path
    ) -> None:
        isolated_token_store.write_text(
            json.dumps({"token": 12345}), encoding="utf-8"
        )
        assert get_token() is None


class TestSetToken:
    def test_writes_token_to_file(
        self, isolated_token_store: Path
    ) -> None:
        set_token("new.jwt.token")
        assert isolated_token_store.exists()
        data = json.loads(isolated_token_store.read_text(encoding="utf-8"))
        assert data == {"token": "new.jwt.token"}

    def test_set_then_get_round_trip(
        self, isolated_token_store: Path  # noqa: ARG002 — fixture pins the path
    ) -> None:
        set_token("round.trip.token")
        assert get_token() == "round.trip.token"

    def test_overwrites_existing_token(
        self, cached_token: str  # noqa: ARG002 — sets up a pre-existing token
    ) -> None:
        set_token("replacement.token")
        assert get_token() == "replacement.token"


class TestClearToken:
    def test_removes_existing_file(
        self, cached_token: str, isolated_token_store: Path  # noqa: ARG002
    ) -> None:
        assert isolated_token_store.exists()
        clear_token()
        assert not isolated_token_store.exists()

    def test_no_op_when_file_missing(
        self, isolated_token_store: Path
    ) -> None:
        assert not isolated_token_store.exists()
        # Must not raise.
        clear_token()
        assert not isolated_token_store.exists()
