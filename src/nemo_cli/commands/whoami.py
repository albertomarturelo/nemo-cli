import typer

from nemo_cli.auth.token_store import get_token


def whoami() -> None:
    """Show whether an authentication token is currently cached.

    Since credentials are no longer read from the environment (ADR-025), there
    is no configured user to display. Surfacing the signed-in identity from the
    token is tracked separately as the "Rich whoami" work unit.
    """
    if get_token():
        typer.secho("Token: cached", fg=typer.colors.GREEN)
    else:
        typer.secho("Token: not cached (run `nemo login`)", fg=typer.colors.YELLOW)
