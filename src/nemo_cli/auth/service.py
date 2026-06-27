from typing import cast

import httpx

from nemo_cli.config import API_BASE_URL


def sign_in(username: str, password: str) -> str:
    """Exchange explicit credentials for a bearer token via the SignIn endpoint.

    Credentials are passed in by the caller (the `login` command collects them
    interactively or from flags) and are never read from the environment or
    written to disk (ADR-025).
    """
    url = f"{API_BASE_URL}/publicapi/shared/auth/SignIn"
    response = httpx.post(
        url,
        json={"userName": username, "password": password},
        timeout=15.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"SignIn failed ({response.status_code} {response.reason_phrase}): {response.text}"
        )

    raw: object = response.json()
    if not isinstance(raw, dict):
        raise RuntimeError("SignIn response was not a JSON object.")

    payload = cast(dict[str, object], raw)
    token = payload.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("SignIn response missing top-level 'token' string.")
    return token


def refresh_token(current_token: str) -> str:
    """Trade an existing bearer token for a freshly minted one.

    Calls `GET /api/publicapi/shared/auth/RefreshToken` with the current
    token in the Authorization header. The response body is a
    JSON-encoded string containing the new JWT. Raises RuntimeError on
    any non-2xx or malformed payload — the caller is expected to fall
    back to `sign_in()` with credentials.
    """
    url = f"{API_BASE_URL}/publicapi/shared/auth/RefreshToken"
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {current_token}"},
        timeout=15.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"RefreshToken failed "
            f"({response.status_code} {response.reason_phrase}): {response.text}"
        )

    payload: object = response.json()
    if not isinstance(payload, str) or not payload:
        raise RuntimeError("RefreshToken response was not a non-empty string.")
    return payload
