import typer

from nemo_cli.auth.session import AuthStatus
from nemo_cli.auth.session import status as session_status

# Human-facing line + colour for each session state. EXPIRING is informational
# (the next API call renews it transparently, ADR-012); EXPIRED / LOGGED_OUT need
# an explicit `nemo login`.
_RENDERING: dict[AuthStatus, tuple[str, str]] = {
    AuthStatus.ACTIVE: ("Session: active", typer.colors.GREEN),
    AuthStatus.EXPIRING: (
        "Session: expiring — renews automatically on the next call",
        typer.colors.YELLOW,
    ),
    AuthStatus.EXPIRED: ("Session: expired — run `nemo login`", typer.colors.YELLOW),
    AuthStatus.LOGGED_OUT: (
        "Session: logged out — run `nemo login`",
        typer.colors.YELLOW,
    ),
}


def status() -> None:
    """Show the current authentication session state."""
    message, color = _RENDERING[session_status()]
    typer.secho(message, fg=color)
