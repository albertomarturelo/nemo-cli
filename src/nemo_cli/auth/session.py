"""Authentication session orchestration (ADR-026).

Sits above the raw HTTP calls in `service` and the token cache in `token_store`:
`log_in` performs and persists a sign-in; `status` reports the current session
state derived from the cached token. Keeping this here lets the CLI commands stay
thin and lets the orchestration be unit-tested without the CLI.
"""

from enum import StrEnum

from nemo_cli.auth.jwt import PROACTIVE_REFRESH_SECONDS, is_expiring_within
from nemo_cli.auth.service import sign_in
from nemo_cli.auth.token_store import get_token, set_token


class AuthStatus(StrEnum):
    """Coarse authentication state derived from the cached bearer token."""

    LOGGED_OUT = "logged_out"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"


def log_in(username: str, password: str) -> None:
    """Sign in with explicit credentials and cache the resulting bearer token.

    The orchestration the `login` command performs, lifted into the auth layer
    so it can be reused and tested independently of the CLI.
    """
    token = sign_in(username, password)
    set_token(token)


def status() -> AuthStatus:
    """Report the current session state from the cached token (read-only).

    Decodes the token's `exp` claim without verifying the signature. A token we
    cannot read is treated as `ACTIVE`, mirroring the refresh-timing helper: the
    server remains the authority and the reactive 401 path catches a token it
    actually rejects. This never renews — it reports.
    """
    token = get_token()
    if token is None:
        return AuthStatus.LOGGED_OUT
    if is_expiring_within(token, 0):
        return AuthStatus.EXPIRED
    if is_expiring_within(token, PROACTIVE_REFRESH_SECONDS):
        return AuthStatus.EXPIRING
    return AuthStatus.ACTIVE
