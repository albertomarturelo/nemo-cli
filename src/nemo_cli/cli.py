import typer

from nemo_cli import __version__
from nemo_cli.commands.instruments import app as instruments_app
from nemo_cli.commands.login import login
from nemo_cli.commands.logout import logout
from nemo_cli.commands.portfolio import app as portfolio_app
from nemo_cli.commands.whoami import whoami

app = typer.Typer(
    name="nemo",
    help="Personal CLI for Chilean stockbroker portals.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"nemo {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(  # noqa: ARG001 — consumed via callback
        False,
        "--version",
        "-V",
        help="Show the CLI version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Personal CLI for Chilean stockbroker portals."""


app.command()(login)
app.command()(logout)
app.command()(whoami)
app.add_typer(instruments_app, name="instruments")
app.add_typer(portfolio_app, name="portfolio")


def main() -> None:
    app()
