"""Tests for the `nemo auth` command group (login / logout / status)."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from nemo_cli.auth.session import AuthStatus
from nemo_cli.cli import app

runner = CliRunner()


class TestLoginCommand:
    def test_prompts_for_credentials_when_no_flags(self) -> None:
        with patch("nemo_cli.commands.login.log_in") as mock_login:
            result = runner.invoke(
                app, ["auth", "login"], input="user@example.com\nsecret\n"
            )

        assert result.exit_code == 0
        assert "Login successful" in result.output
        mock_login.assert_called_once_with("user@example.com", "secret")

    def test_uses_flags_without_prompting(self) -> None:
        with patch("nemo_cli.commands.login.log_in") as mock_login:
            result = runner.invoke(
                app,
                ["auth", "login", "--user", "flag@example.com", "--password", "flagpw"],
            )

        assert result.exit_code == 0
        mock_login.assert_called_once_with("flag@example.com", "flagpw")

    def test_prompts_only_for_missing_password(self) -> None:
        with patch("nemo_cli.commands.login.log_in") as mock_login:
            result = runner.invoke(
                app,
                ["auth", "login", "--user", "flag@example.com"],
                input="promptpw\n",
            )

        assert result.exit_code == 0
        mock_login.assert_called_once_with("flag@example.com", "promptpw")

    def test_surfaces_login_failure(self) -> None:
        with patch(
            "nemo_cli.commands.login.log_in",
            side_effect=RuntimeError("SignIn failed (401): bad credentials"),
        ):
            result = runner.invoke(
                app, ["auth", "login", "--user", "u@example.com", "--password", "pw"]
            )

        assert result.exit_code == 1
        assert "SignIn failed (401)" in result.output


class TestLogoutCommand:
    def test_logout_clears_token_and_prints_message(
        self,
        cached_token: str,  # noqa: ARG002
    ) -> None:
        with patch("nemo_cli.commands.logout.clear_token") as mock_clear:
            result = runner.invoke(app, ["auth", "logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_clear.assert_called_once_with()


class TestStatusCommand:
    def test_renders_active(self) -> None:
        with patch(
            "nemo_cli.commands.status.session_status", return_value=AuthStatus.ACTIVE
        ):
            result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "active" in result.output

    def test_renders_logged_out(self) -> None:
        with patch(
            "nemo_cli.commands.status.session_status",
            return_value=AuthStatus.LOGGED_OUT,
        ):
            result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "logged out" in result.output

    def test_renders_expiring(self) -> None:
        with patch(
            "nemo_cli.commands.status.session_status",
            return_value=AuthStatus.EXPIRING,
        ):
            result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "expiring" in result.output

    def test_renders_expired(self) -> None:
        with patch(
            "nemo_cli.commands.status.session_status",
            return_value=AuthStatus.EXPIRED,
        ):
            result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "expired" in result.output
