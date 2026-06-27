"""Tests for the login / logout / whoami CLI commands."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from nemo_cli.cli import app

runner = CliRunner()


class TestLoginCommand:
    def test_prompts_for_credentials_when_no_flags(self) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in", return_value="fresh.token"
        ) as mock_signin, patch("nemo_cli.commands.login.set_token") as mock_set:
            result = runner.invoke(
                app, ["login"], input="user@example.com\nsecret\n"
            )

        assert result.exit_code == 0
        assert "Login successful" in result.output
        mock_signin.assert_called_once_with("user@example.com", "secret")
        mock_set.assert_called_once_with("fresh.token")

    def test_uses_flags_without_prompting(self) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in", return_value="fresh.token"
        ) as mock_signin, patch("nemo_cli.commands.login.set_token"):
            result = runner.invoke(
                app,
                ["login", "--user", "flag@example.com", "--password", "flagpw"],
            )

        assert result.exit_code == 0
        mock_signin.assert_called_once_with("flag@example.com", "flagpw")

    def test_prompts_only_for_missing_password(self) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in", return_value="fresh.token"
        ) as mock_signin, patch("nemo_cli.commands.login.set_token"):
            result = runner.invoke(
                app, ["login", "--user", "flag@example.com"], input="promptpw\n"
            )

        assert result.exit_code == 0
        mock_signin.assert_called_once_with("flag@example.com", "promptpw")

    def test_surfaces_signin_failure(self) -> None:
        with patch(
            "nemo_cli.commands.login.sign_in",
            side_effect=RuntimeError("SignIn failed (401): bad credentials"),
        ):
            result = runner.invoke(
                app, ["login", "--user", "u@example.com", "--password", "pw"]
            )

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
    def test_reports_cached_token(self) -> None:
        with patch("nemo_cli.commands.whoami.get_token", return_value="cached"):
            result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "Token: cached" in result.output

    def test_reports_no_cached_token(self) -> None:
        with patch("nemo_cli.commands.whoami.get_token", return_value=None):
            result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "not cached" in result.output
