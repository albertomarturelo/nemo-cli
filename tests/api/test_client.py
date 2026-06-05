"""Tests for nemo_cli.api.client.api_request."""

from __future__ import annotations

import base64
import json
import time

import httpx
import pytest
import respx

from nemo_cli.api.client import api_request
from nemo_cli.auth.token_store import get_token
from nemo_cli.config import API_BASE_URL

SIGN_IN_URL = f"{API_BASE_URL}/publicapi/shared/auth/SignIn"
REFRESH_URL = f"{API_BASE_URL}/publicapi/shared/auth/RefreshToken"
ENDPOINT_URL = f"{API_BASE_URL}/shared/Some/Endpoint"


def _jwt_with_exp(exp_offset_seconds: int) -> str:
    """Build a minimal JWT whose `exp` is `now + exp_offset_seconds`.

    Negative offsets produce already-expired tokens; large positive
    offsets produce comfortably-fresh tokens.
    """
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload_dict = {"exp": int(time.time()) + exp_offset_seconds}
    payload = (
        base64.urlsafe_b64encode(json.dumps(payload_dict).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}.signature"


@pytest.fixture
def fresh_jwt(isolated_token_store: object) -> str:  # noqa: ARG001 — fixture pins path
    """Pre-populate the store with a JWT that expires comfortably in the future."""
    from nemo_cli.auth.token_store import set_token

    token = _jwt_with_exp(3600)
    set_token(token)
    return token


@pytest.fixture
def expiring_jwt(isolated_token_store: object) -> str:  # noqa: ARG001
    """Pre-populate the store with a JWT that is already expired."""
    from nemo_cli.auth.token_store import set_token

    token = _jwt_with_exp(-30)
    set_token(token)
    return token


class TestApiRequestHappyPath:
    @respx.mock
    def test_uses_cached_token_when_present(
        self,
        credentials_env: None,  # noqa: ARG002
        cached_token: str,
    ) -> None:
        # cached.jwt.token is not a valid JWT; is_expiring_within is
        # defensive and treats it as fresh, so no refresh is attempted.
        route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        sent = route.calls.last.request
        assert sent.headers["Authorization"] == f"Bearer {cached_token}"

    @respx.mock
    def test_does_not_refresh_when_token_is_fresh(
        self,
        credentials_env: None,  # noqa: ARG002
        fresh_jwt: str,
    ) -> None:
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        # No mock for REFRESH_URL on purpose — calling it would raise
        # AllMockedAssertionError and fail the test.

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert endpoint_route.calls.last.request.headers["Authorization"] == (
            f"Bearer {fresh_jwt}"
        )

    @respx.mock
    def test_signs_in_when_no_cached_token(
        self,
        credentials_env: None,
        isolated_token_store: object,  # noqa: ARG002 — empty token store
    ) -> None:
        signin_route = respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": "freshly.signed.in"})
        )
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert signin_route.call_count == 1
        sent = endpoint_route.calls.last.request
        assert sent.headers["Authorization"] == "Bearer freshly.signed.in"
        assert get_token() == "freshly.signed.in"

    @respx.mock
    def test_passes_query_params(
        self,
        credentials_env: None,  # noqa: ARG002
        cached_token: str,  # noqa: ARG002
    ) -> None:
        route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={})
        )
        api_request("GET", "/shared/Some/Endpoint", params={"a": 1, "b": "x"})
        sent = route.calls.last.request
        assert "a=1" in str(sent.url)
        assert "b=x" in str(sent.url)

    @respx.mock
    def test_passes_json_body(
        self,
        credentials_env: None,  # noqa: ARG002
        cached_token: str,  # noqa: ARG002
    ) -> None:
        route = respx.post(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={})
        )
        api_request("POST", "/shared/Some/Endpoint", json={"hello": "world"})
        sent = route.calls.last.request
        assert json.loads(sent.read()) == {"hello": "world"}


class TestProactiveRefresh:
    """ADR-012: when the cached token's `exp` is within the threshold,
    `_ensure_token` calls RefreshToken before sending the request."""

    @respx.mock
    def test_refreshes_proactively_when_close_to_expiry(
        self,
        credentials_env: None,  # noqa: ARG002
        expiring_jwt: str,
    ) -> None:
        refresh_route = respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="renewed.token")
        )
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert refresh_route.call_count == 1
        # The refresh call carried the stale token.
        sent_refresh = refresh_route.calls.last.request
        assert sent_refresh.headers["Authorization"] == f"Bearer {expiring_jwt}"
        # The endpoint call carried the renewed token.
        sent_endpoint = endpoint_route.calls.last.request
        assert sent_endpoint.headers["Authorization"] == "Bearer renewed.token"
        # Renewed token is cached.
        assert get_token() == "renewed.token"

    @respx.mock
    def test_falls_back_to_signin_when_proactive_refresh_fails(
        self,
        credentials_env: None,
        expiring_jwt: str,  # noqa: ARG002
    ) -> None:
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(401, text="too stale")
        )
        signin_route = respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": "fresh.from.signin"})
        )
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert signin_route.call_count == 1
        sent = endpoint_route.calls.last.request
        assert sent.headers["Authorization"] == "Bearer fresh.from.signin"
        assert get_token() == "fresh.from.signin"


class TestReactive401Retry:
    """ADR-012: when a fresh-looking cached token still gets a 401 (server
    revoked, schema change, clock skew), the path is RefreshToken first,
    SignIn as fallback."""

    @respx.mock
    def test_refresh_succeeds_and_retry_succeeds(
        self,
        credentials_env: None,  # noqa: ARG002
        cached_token: str,  # noqa: ARG002 — defensive: malformed JWT, no proactive refresh
    ) -> None:
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            side_effect=[
                httpx.Response(401),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        refresh_route = respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="refreshed.token")
        )
        # No SignIn mock — if the code tries it, the test fails loudly.

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert endpoint_route.call_count == 2
        assert refresh_route.call_count == 1
        # Second request used the refreshed token.
        assert endpoint_route.calls[1].request.headers["Authorization"] == (
            "Bearer refreshed.token"
        )
        assert get_token() == "refreshed.token"

    @respx.mock
    def test_refresh_fails_then_signin_succeeds(
        self,
        credentials_env: None,
        cached_token: str,  # noqa: ARG002
    ) -> None:
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            side_effect=[
                httpx.Response(401),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        refresh_route = respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(401, text="too stale")
        )
        signin_route = respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": "fresh.from.signin"})
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 200
        assert refresh_route.call_count == 1
        assert signin_route.call_count == 1
        assert endpoint_route.call_count == 2
        assert endpoint_route.calls[1].request.headers["Authorization"] == (
            "Bearer fresh.from.signin"
        )
        assert get_token() == "fresh.from.signin"

    @respx.mock
    def test_returns_second_401_without_third_attempt(
        self,
        credentials_env: None,
        cached_token: str,  # noqa: ARG002
    ) -> None:
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(401, text="still nope")
        )
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="renewed.but.also.bad")
        )

        response = api_request("GET", "/shared/Some/Endpoint")

        # The endpoint returned 401 a second time — surfaced, not retried again.
        assert response.status_code == 401
        assert endpoint_route.call_count == 2

    @respx.mock
    def test_does_not_retry_on_non_401_errors(
        self,
        credentials_env: None,  # noqa: ARG002
        cached_token: str,  # noqa: ARG002
    ) -> None:
        endpoint_route = respx.get(ENDPOINT_URL).mock(
            return_value=httpx.Response(500, text="boom")
        )
        # No mocks for refresh/signin — if the code tries either, the
        # test fails loudly. ADR-012 only triggers refresh on 401.
        response = api_request("GET", "/shared/Some/Endpoint")

        assert response.status_code == 500
        assert endpoint_route.call_count == 1
