import typer

from nemo_cli.auth.token_store import clear_token


def logout() -> None:
    """Clear the cached authentication token."""
    clear_token()
    typer.secho("Logged out. Cached token removed.", fg=typer.colors.GREEN)
