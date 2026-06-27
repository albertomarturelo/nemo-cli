from typing import Any

import httpx

from nemo_cli.auth.jwt import is_expiring_within
from nemo_cli.auth.service import refresh_token
from nemo_cli.auth.token_store import clear_token, get_token, set_token
from nemo_cli.config import API_BASE_URL

# How close to expiry (in seconds) we proactively renew the token before
# sending the next request. ADR-012 picks 60s as a balance between racing
# the actual expiry and refreshing too eagerly on short CLI invocations.
_PROACTIVE_REFRESH_SECONDS = 60

# Surfaced when there is no usable token and no way to renew it. With
# credentials no longer stored anywhere (ADR-025), the only path back into the
# system is an explicit `nemo login`.
_SESSION_EXPIRED_MESSAGE = "Session expired — run `nemo login` to authenticate."


def _ensure_token() -> str:
    """Return a usable bearer token, refreshing proactively if it is close to
    expiry.

    Raises ``RuntimeError`` telling the user to re-login when there is no cached
    token, or when the proactive refresh fails — there are no stored credentials
    to bootstrap a fresh SignIn (ADR-025, amending ADR-003 / ADR-012).
    """
    cached = get_token()
    if cached is None:
        raise RuntimeError(_SESSION_EXPIRED_MESSAGE)

    if is_expiring_within(cached, _PROACTIVE_REFRESH_SECONDS):
        # Cached token is about to expire — renew before using it.
        try:
            renewed = refresh_token(cached)
        except RuntimeError as error:
            clear_token()
            raise RuntimeError(_SESSION_EXPIRED_MESSAGE) from error
        set_token(renewed)
        return renewed

    return cached


def api_request(
    method: str,
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> httpx.Response:
    url = f"{API_BASE_URL}{path}"

    def send(token: str) -> httpx.Response:
        return httpx.request(
            method,
            url,
            json=json,
            params=params,
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
        )

    token = _ensure_token()
    response = send(token)

    if response.status_code == 401:
        # The proactive check missed (server-side revocation, clock skew,
        # schema change). Try Refresh once; if it fails there are no stored
        # credentials to re-SignIn, so tell the user to re-login. ADR-025
        # removes the SignIn rung from ADR-012's reactive ladder.
        try:
            renewed = refresh_token(token)
        except RuntimeError as error:
            clear_token()
            raise RuntimeError(_SESSION_EXPIRED_MESSAGE) from error
        set_token(renewed)
        response = send(renewed)

    return response
