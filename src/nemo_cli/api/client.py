from typing import Any

import httpx

from nemo_cli.auth.jwt import is_expiring_within
from nemo_cli.auth.service import refresh_token, sign_in
from nemo_cli.auth.token_store import clear_token, get_token, set_token
from nemo_cli.config import API_BASE_URL

# How close to expiry (in seconds) we proactively renew the token before
# sending the next request. ADR-012 picks 60s as a balance between racing
# the actual expiry and refreshing too eagerly on short CLI invocations.
_PROACTIVE_REFRESH_SECONDS = 60


def _ensure_token() -> str:
    """Return a usable bearer token, refreshing proactively if it is close
    to expiry. Bootstraps via SignIn if no token is cached.
    """
    cached = get_token()
    if cached is None:
        return _bootstrap_signin()

    if is_expiring_within(cached, _PROACTIVE_REFRESH_SECONDS):
        # Cached token is about to expire — renew before using it.
        try:
            renewed = refresh_token(cached)
        except RuntimeError:
            # The server rejected our refresh (token is too stale or
            # otherwise invalid). Fall back to a fresh SignIn.
            return _bootstrap_signin()
        set_token(renewed)
        return renewed

    return cached


def _bootstrap_signin() -> str:
    """Clear any stale cache and obtain a fresh token via SignIn."""
    clear_token()
    fresh = sign_in()
    set_token(fresh)
    return fresh


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
        # The proactive check missed (server-side revocation, clock
        # skew, schema change). Try Refresh first; only re-SignIn if
        # Refresh itself fails. ADR-012.
        try:
            renewed = refresh_token(token)
            set_token(renewed)
            response = send(renewed)
        except RuntimeError:
            fresh = _bootstrap_signin()
            response = send(fresh)

    return response
