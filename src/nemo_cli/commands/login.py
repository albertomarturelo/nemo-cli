import typer

from nemo_cli.auth.service import sign_in
from nemo_cli.auth.token_store import set_token


def login() -> None:
    """Authenticate against the configured broker portal and cache the token locally."""
    try:
        token = sign_in()
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    set_token(token)
    typer.secho("Login successful. Token cached.", fg=typer.colors.GREEN)
