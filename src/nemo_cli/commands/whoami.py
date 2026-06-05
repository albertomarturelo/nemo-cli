import typer

from nemo_cli.auth.token_store import get_token
from nemo_cli.config import load_credentials


def whoami() -> None:
    """Show the configured user and whether a token is currently cached."""
    try:
        credentials = load_credentials()
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"User:    {credentials.user_name}")
    if get_token():
        typer.secho("Token:   cached", fg=typer.colors.GREEN)
    else:
        typer.secho("Token:   not cached (run `nemo login`)", fg=typer.colors.YELLOW)
