"""Tests for nemo_cli.auth.session: log_in and status."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

from nemo_cli.auth.session import AuthStatus, log_in, status
from nemo_cli.auth.token_store import get_token, set_token


class TestLogIn:
    def test_signs_in_and_caches_token(
        self, isolated_token_store: Path  # noqa: ARG002 — pins token path
    ) -> None:
        with patch(
            "nemo_cli.auth.session.sign_in", return_value="fresh.token"
        ) as mock_signin:
            log_in("u@example.com", "pw")

        mock_signin.assert_called_once_with("u@example.com", "pw")
        assert get_token() == "fresh.token"


class TestStatus:
    def test_logged_out_when_no_token(
        self, isolated_token_store: Path  # noqa: ARG002 — empty token store
    ) -> None:
        assert status() is AuthStatus.LOGGED_OUT

    def test_active_when_token_fresh(
        self,
        isolated_token_store: Path,  # noqa: ARG002
        jwt_factory: Callable[[int], str],
    ) -> None:
        set_token(jwt_factory(3600))
        assert status() is AuthStatus.ACTIVE

    def test_expiring_when_within_threshold(
        self,
        isolated_token_store: Path,  # noqa: ARG002
        jwt_factory: Callable[[int], str],
    ) -> None:
        set_token(jwt_factory(30))
        assert status() is AuthStatus.EXPIRING

    def test_expired_when_past(
        self,
        isolated_token_store: Path,  # noqa: ARG002
        jwt_factory: Callable[[int], str],
    ) -> None:
        set_token(jwt_factory(-30))
        assert status() is AuthStatus.EXPIRED

    def test_active_when_token_unreadable(
        self, isolated_token_store: Path  # noqa: ARG002
    ) -> None:
        # A malformed token is treated as fresh, mirroring the refresh-timing
        # helper — the server stays the authority (ADR-026).
        set_token("not.a.jwt")
        assert status() is AuthStatus.ACTIVE
