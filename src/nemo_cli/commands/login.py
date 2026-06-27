import typer

from nemo_cli.auth.session import log_in


def login(
    user: str | None = typer.Option(
        None, "--user", "-u", help="Email to sign in with. Prompted if omitted."
    ),
    password: str | None = typer.Option(
        None, "--password", "-p", help="Password. Prompted (hidden) if omitted."
    ),
) -> None:
    """Authenticate against the configured broker portal and cache the token locally.

    Prompts for any credential not supplied via --user / --password; the
    password prompt is hidden. Credentials are never written to disk (ADR-025)
    — only the resulting bearer token is cached.
    """
    email = user if user else typer.prompt("Email")
    secret = password if password else typer.prompt("Password", hide_input=True)
    try:
        log_in(email, secret)
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    typer.secho("Login successful. Token cached.", fg=typer.colors.GREEN)
