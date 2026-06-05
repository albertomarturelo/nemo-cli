"""Tests for nemo_cli.auth.service: sign_in and refresh_token."""

from __future__ import annotations

import httpx
import pytest
import respx

from nemo_cli.auth.service import refresh_token, sign_in
from nemo_cli.config import API_BASE_URL

SIGN_IN_URL = f"{API_BASE_URL}/publicapi/shared/auth/SignIn"
REFRESH_URL = f"{API_BASE_URL}/publicapi/shared/auth/RefreshToken"


class TestSignIn:
    @respx.mock
    def test_returns_token_on_success(self, credentials_env: None) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": "fresh.jwt.token"})
        )
        assert sign_in() == "fresh.jwt.token"

    @respx.mock
    def test_posts_credentials_in_request_body(
        self, credentials_env: None  # noqa: ARG002
    ) -> None:
        route = respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": "t"})
        )
        sign_in()
        assert route.called
        sent = route.calls.last.request.read()
        # Body is JSON-encoded credentials.
        import json as _json

        assert _json.loads(sent) == {
            "userName": "test@example.com",
            "password": "test-password",
        }

    @respx.mock
    def test_raises_on_4xx(self, credentials_env: None) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(401, text="Invalid credentials")
        )
        with pytest.raises(RuntimeError, match=r"SignIn failed \(401"):
            sign_in()

    @respx.mock
    def test_raises_on_5xx(self, credentials_env: None) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(500, text="boom")
        )
        with pytest.raises(RuntimeError, match=r"SignIn failed \(500"):
            sign_in()

    @respx.mock
    def test_raises_when_payload_is_not_object(
        self, credentials_env: None
    ) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json=["not", "an", "object"])
        )
        with pytest.raises(RuntimeError, match="not a JSON object"):
            sign_in()

    @respx.mock
    def test_raises_when_token_missing(
        self, credentials_env: None
    ) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"other": "field"})
        )
        with pytest.raises(RuntimeError, match="missing top-level 'token' string"):
            sign_in()

    @respx.mock
    def test_raises_when_token_is_empty(
        self, credentials_env: None
    ) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": ""})
        )
        with pytest.raises(RuntimeError, match="missing top-level 'token' string"):
            sign_in()

    @respx.mock
    def test_raises_when_token_is_not_string(
        self, credentials_env: None
    ) -> None:
        respx.post(SIGN_IN_URL).mock(
            return_value=httpx.Response(200, json={"token": 12345})
        )
        with pytest.raises(RuntimeError, match="missing top-level 'token' string"):
            sign_in()

    def test_raises_when_credentials_missing(
        self, no_credentials_env: None
    ) -> None:
        # No HTTP call should be made; load_credentials raises first.
        with pytest.raises(RuntimeError, match="Missing credentials"):
            sign_in()


class TestRefreshToken:
    @respx.mock
    def test_returns_new_token_on_success(self) -> None:
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="brand.new.token")
        )
        assert refresh_token("current.jwt") == "brand.new.token"

    @respx.mock
    def test_sends_current_token_in_authorization_header(self) -> None:
        route = respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="ok.token")
        )
        refresh_token("the.current.bearer")
        sent = route.calls.last.request
        assert sent.headers["Authorization"] == "Bearer the.current.bearer"

    @respx.mock
    def test_raises_on_4xx(self) -> None:
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(401, text="too stale")
        )
        with pytest.raises(RuntimeError, match=r"RefreshToken failed \(401"):
            refresh_token("any.token")

    @respx.mock
    def test_raises_on_5xx(self) -> None:
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(503, text="unavailable")
        )
        with pytest.raises(RuntimeError, match=r"RefreshToken failed \(503"):
            refresh_token("any.token")

    @respx.mock
    def test_raises_when_payload_is_not_string(self) -> None:
        # Vector returns a JSON-encoded string, not an object.
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json={"token": "wrapped"})
        )
        with pytest.raises(RuntimeError, match="not a non-empty string"):
            refresh_token("any.token")

    @respx.mock
    def test_raises_when_payload_is_empty_string(self) -> None:
        respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="")
        )
        with pytest.raises(RuntimeError, match="not a non-empty string"):
            refresh_token("any.token")

    @respx.mock
    def test_uses_get_method(self) -> None:
        # Vector exposes RefreshToken as GET (semantically odd but
        # verified empirically). If a future change accidentally
        # switched it to POST this assertion would catch it.
        route = respx.get(REFRESH_URL).mock(
            return_value=httpx.Response(200, json="ok")
        )
        refresh_token("any.token")
        assert route.calls.last.request.method == "GET"
