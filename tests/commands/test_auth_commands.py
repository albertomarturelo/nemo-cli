"""Tests for the login / logout / whoami CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from nemo_cli.cli import app

runner = CliRunner()


class TestLoginCommand:
    def test_login_success_caches_token(
        self,
        credentials_env: None,  # noqa: ARG002
        isolated_token_store: Path,  # noqa: ARG002
    ) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in", return_value="fresh.token"
        ) as mock_signin, patch(
            "nemo_cli.commands.login.set_token"
        ) as mock_set:
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 0
        assert "Login successful" in result.output
        mock_signin.assert_called_once_with()
        mock_set.assert_called_once_with("fresh.token")

    def test_login_surfaces_signin_failure(
        self, credentials_env: None  # noqa: ARG002
    ) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in",
            side_effect=RuntimeError("SignIn failed (401): bad credentials"),
        ):
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 1
        assert "SignIn failed (401)" in result.output


class TestLogoutCommand:
    def test_logout_clears_token_and_prints_message(
        self,
        cached_token: str,  # noqa: ARG002
    ) -> None:
        with patch("nemo_cli.commands.logout.clear_token") as mock_clear:
            result = runner.invoke(app, ["logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_clear.assert_called_once_with()


class TestWhoamiCommand:
    def test_whoami_with_cached_token(
        self,
        credentials_env: None,  # noqa: ARG002
    ) -> None:
        with patch(
            "nemo_cli.commands.whoami.get_token", return_value="cached"
        ):
            result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "test@example.com" in result.output
        assert "cached" in result.output

    def test_whoami_without_cached_token(
        self,
        credentials_env: None,  # noqa: ARG002
    ) -> None:
        with patch(
            "nemo_cli.commands.whoami.get_token", return_value=None
        ):
            result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "test@example.com" in result.output
        assert "not cached" in result.output

    def test_whoami_fails_when_credentials_missing(
        self,
        no_credentials_env: None,  # noqa: ARG002
    ) -> None:
        # No need to mock get_token; load_credentials() raises first.
        # Use a MagicMock for get_token so it's not called accidentally.
        with patch(
            "nemo_cli.commands.whoami.get_token",
            new=MagicMock(return_value=None),
        ):
            result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 1
        assert "Missing credentials" in result.output
