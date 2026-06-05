"""Tests for nemo_cli.auth.jwt.is_expiring_within."""

from __future__ import annotations

import base64
import json
import time

from nemo_cli.auth.jwt import is_expiring_within


def _make_token(payload: object) -> str:
    """Build a minimal three-part JWT-shaped string with the given payload.

    The signature segment is a fixed placeholder — `is_expiring_within`
    never validates it.
    """
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    body = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{body}.signature"


class TestIsExpiringWithin:
    def test_token_close_to_expiry(self) -> None:
        token = _make_token({"exp": int(time.time()) + 30})
        assert is_expiring_within(token, 60) is True

    def test_token_with_plenty_of_life(self) -> None:
        token = _make_token({"exp": int(time.time()) + 3600})
        assert is_expiring_within(token, 60) is False

    def test_already_expired_token(self) -> None:
        token = _make_token({"exp": int(time.time()) - 30})
        assert is_expiring_within(token, 60) is True

    def test_threshold_is_inclusive_at_boundary(self) -> None:
        # exp = now + 60 → boundary; the helper uses <=, so this is True.
        token = _make_token({"exp": int(time.time()) + 60})
        assert is_expiring_within(token, 60) is True

    def test_zero_threshold_returns_true_only_when_expired(self) -> None:
        future = _make_token({"exp": int(time.time()) + 30})
        past = _make_token({"exp": int(time.time()) - 30})
        assert is_expiring_within(future, 0) is False
        assert is_expiring_within(past, 0) is True

    def test_float_exp_is_supported(self) -> None:
        token = _make_token({"exp": time.time() + 30.5})
        assert is_expiring_within(token, 60) is True


class TestMalformedTokens:
    def test_token_without_three_parts_returns_false(self) -> None:
        assert is_expiring_within("only.two", 60) is False
        assert is_expiring_within("nopartsatall", 60) is False
        assert is_expiring_within("", 60) is False

    def test_token_with_invalid_base64_in_payload_returns_false(self) -> None:
        assert is_expiring_within("aaa.!!!not-base64!!!.zzz", 60) is False

    def test_token_with_non_json_payload_returns_false(self) -> None:
        garbage_b64 = base64.urlsafe_b64encode(b"this is not json").rstrip(b"=").decode()
        token = f"aaa.{garbage_b64}.zzz"
        assert is_expiring_within(token, 60) is False

    def test_token_with_array_payload_returns_false(self) -> None:
        # JSON parses, but not as an object → can't have an `exp` claim.
        body = base64.urlsafe_b64encode(b"[1, 2, 3]").rstrip(b"=").decode()
        token = f"aaa.{body}.zzz"
        assert is_expiring_within(token, 60) is False

    def test_token_with_no_exp_claim_returns_false(self) -> None:
        token = _make_token({"sub": "user-id"})
        assert is_expiring_within(token, 60) is False

    def test_token_with_string_exp_returns_false(self) -> None:
        # `exp` must be numeric; a string is treated as malformed.
        token = _make_token({"exp": "not-a-number"})
        assert is_expiring_within(token, 60) is False

    def test_test_fixture_cached_jwt_token_returns_false(self) -> None:
        # The test-fixture string used elsewhere ("cached.jwt.token")
        # base64-decodes to garbage; the helper must treat it as fresh
        # so the existing test suite does not break.
        assert is_expiring_within("cached.jwt.token", 60) is False
