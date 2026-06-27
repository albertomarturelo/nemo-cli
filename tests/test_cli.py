"""Tests for nemo_cli.cli — root CLI assembly and `--version` flag."""

from __future__ import annotations

from typer.testing import CliRunner

from nemo_cli import __version__
from nemo_cli.cli import app

runner = CliRunner()


class TestVersionFlag:
    def test_version_long_form_prints_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert f"nemo {__version__}" in result.output

    def test_version_short_form_prints_version(self) -> None:
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert f"nemo {__version__}" in result.output

    def test_version_short_circuits_before_subcommand(self) -> None:
        # --version is eager; even if invoked alongside a subcommand, it prints
        # the version and exits without running the subcommand.
        result = runner.invoke(app, ["--version", "instruments"])
        assert result.exit_code == 0
        assert f"nemo {__version__}" in result.output


class TestRootHelp:
    def test_help_lists_all_subcommand_groups(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for command in ("auth", "instruments", "portfolio"):
            assert command in result.output

    def test_no_args_shows_help(self) -> None:
        # The Typer app is configured with no_args_is_help=True.
        result = runner.invoke(app, [])
        # Exit code 2 is Typer's "missing command, here's the help".
        assert result.exit_code == 2
        assert "Usage:" in result.output
