#!/usr/bin/env python3
"""Verify the refresh-token flow against the live Vector endpoint.

Smoke-tests the happy path of `nemo_cli.auth.service.refresh_token` and
the read-only `nemo_cli.auth.jwt.is_expiring_within` helper. Requires a
**fresh** cached token (still within its `exp` window) and live network.

Usage (venv active):
    ./scripts/verify_refresh.py

Usage (venv not active, from project root):
    .venv/bin/python scripts/verify_refresh.py

Recommended pattern — login + verify in one shot, before the token can
get close to expiring:

    .venv/bin/nemo login && ./scripts/verify_refresh.py

Output:
    - Cached-token claims (jti, exp, expected TTL).
    - The new token's claims after refresh, plus its observed TTL
      (exp - iat) and shape confirmation.
    - Pass/fail markers for: tokens differ, jti differs, new exp is
      later, new lifetime is reasonable, header is HS256 JWT.

Note: Vector's RefreshToken endpoint **rejects tokens that have already
passed `exp`** (verified empirically — returns 401). The proactive 60s
window in `_ensure_token` is the only window where Refresh is useful;
once the token is fully expired the runtime falls back to `SignIn`.
"""

from __future__ import annotations

import base64
import json
import sys
import time

from nemo_cli.auth.jwt import is_expiring_within
from nemo_cli.auth.service import refresh_token
from nemo_cli.auth.token_store import get_token


def _decode_jwt(token: str) -> tuple[dict[str, object], dict[str, object]] | None:
    """Return (header, payload) dicts for a 3-part JWT, or None on shape error."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        header_b64, payload_b64, _ = parts
        header_b64 += "=" * (-len(header_b64) % 4)
        payload_b64 += "=" * (-len(payload_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None
    return header, payload


def _short(token: str, n: int = 24) -> str:
    return f"{token[:n]}…{token[-n:]}"


def _print_token_block(label: str, token: str) -> dict[str, object] | None:
    print(f"{label}: {_short(token)}")
    decoded = _decode_jwt(token)
    if decoded is None:
        print("  [!] Not a 3-part JWT; cannot decode.")
        return None
    header, payload = decoded
    iat = payload.get("iat")
    exp = payload.get("exp")
    print(f"  alg/typ:   {header.get('alg')!r} / {header.get('typ')!r}")
    print(f"  jti:       {payload.get('jti')}")
    print(f"  iat:       {iat}")
    print(f"  exp:       {exp}")
    if isinstance(iat, (int, float)) and isinstance(exp, (int, float)):
        ttl = int(exp - iat)
        print(f"  TTL:       {ttl}s ({ttl // 60} min)")
    return payload


def main() -> int:
    current = get_token()
    if current is None:
        print("No cached token. Run `.venv/bin/nemo login` first.", file=sys.stderr)
        return 1

    current_decoded = _decode_jwt(current)
    if current_decoded is None:
        print(
            "Cached token does not look like a 3-part JWT. Re-run `nemo login`.",
            file=sys.stderr,
        )
        return 1

    _, current_payload = current_decoded
    current_exp = current_payload.get("exp")
    if isinstance(current_exp, (int, float)) and current_exp <= time.time():
        seconds_past = int(time.time() - current_exp)
        print(
            f"Cached token has been expired for {seconds_past}s. "
            "RefreshToken rejects already-expired bearers (verified empirically).\n"
            "Run `.venv/bin/nemo login` to mint a fresh token, then re-run this "
            "script before its `exp` passes.",
            file=sys.stderr,
        )
        return 1

    print("Cached token (input to refresh):")
    print()
    current_payload = _print_token_block("  bearer", current) or {}
    print()
    print(f"  Expiring within 60s? {is_expiring_within(current, 60)}")
    print()

    print("Calling refresh_token() against the live endpoint…")
    print()
    new = refresh_token(current)

    print("New token (output of refresh):")
    print()
    new_payload = _print_token_block("  bearer", new) or {}
    print()

    # Verdict.
    print("=" * 60)
    print("Verdict")
    print("=" * 60)

    def _num(value: object) -> float:
        return value if isinstance(value, (int, float)) else 0

    same_token = current == new
    same_jti = current_payload.get("jti") == new_payload.get("jti")
    current_exp_value = _num(current_payload.get("exp"))
    new_exp_value = _num(new_payload.get("exp"))
    new_iat_value = _num(new_payload.get("iat"))
    exp_delta = int(new_exp_value - current_exp_value)
    new_ttl = int(new_exp_value - new_iat_value)
    new_decoded = _decode_jwt(new)
    is_jwt_shape = new_decoded is not None
    new_header = new_decoded[0] if new_decoded else {}
    is_hs256 = new_header.get("alg") == "HS256"

    checks = [
        ("Tokens differ", not same_token),
        ("jti claims differ", not same_jti),
        ("New exp is later than the cached one", exp_delta > 0),
        ("New token has a usable lifetime (≥ 60s)", new_ttl >= 60),
        ("New token is a 3-part JWT", is_jwt_shape),
        ("New token uses HS256", is_hs256),
    ]

    all_ok = True
    for label, passed in checks:
        marker = "✓" if passed else "✗"
        print(f"  [{marker}] {label}")
        if not passed:
            all_ok = False

    print()
    print(f"  exp_delta:     +{exp_delta}s   (new bearer's exp is later by this much)")
    print(f"  new TTL:       {new_ttl}s ({new_ttl // 60} min)   ← refresh-issued lifetime")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
