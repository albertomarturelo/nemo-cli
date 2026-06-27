"""Read-only JWT introspection helpers.

Used to time refresh calls (peek at the `exp` claim). Signature
verification is intentionally skipped — the server is the authority on
whether a token is valid; we just want a hint for when to renew.
"""

import base64
import binascii
import json
import time
from typing import cast

# Tokens within this many seconds of their `exp` are renewed proactively
# (ADR-012) and reported as "expiring" by the auth session status (ADR-026).
# Single source of truth shared by `api.client` and `auth.session`.
PROACTIVE_REFRESH_SECONDS = 60


def is_expiring_within(token: str, seconds: int) -> bool:
    """True if the JWT's `exp` claim is at most `seconds` away from now.

    Already-expired tokens (exp <= now) return True. Malformed tokens
    return False — the caller treats them as fresh and lets the
    reactive 401 path handle any actual rejection.
    """
    payload = _decode_payload(token)
    if payload is None:
        return False
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return False
    return exp - time.time() <= seconds


def _decode_payload(token: str) -> dict[str, object] | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload_b64 = parts[1]
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded)
    except (ValueError, binascii.Error):
        return None
    try:
        parsed = json.loads(decoded)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return cast(dict[str, object], parsed)
