#!/usr/bin/env python3
"""Verify the reactive 401 → Refresh → SignIn fallback path against prod.

What this script does:

1. Reads the currently cached bearer (so it can be restored on failure
   diagnostics).
2. **Overwrites** the cache with a deliberately invalid token shape.
3. Calls `api_request` against a cheap real endpoint
   (`/shared/Instrumentos/FiltrarInstrumentos`) with `limit=1`.
4. Asserts that the call returns `200` — which can only happen if:
   a) the corrupted token gets a `401`, then
   b) `RefreshToken` is attempted and **also** fails (the corrupted
      bearer is invalid), then
   c) the runtime falls back to `SignIn` with the env-var credentials,
      caches the new bearer, and retries.
5. Verifies the cache now holds a fresh JWT (not the corrupted blob),
   confirming the SignIn-fallback wrote it.

Run with the venv active (the script imports `nemo_cli.*`):

    ./scripts/verify_reactive_fallback.py

Or without activating:

    .venv/bin/python scripts/verify_reactive_fallback.py

Exits 0 on success, 1 on any failed assertion. Prints the trail of
events for clarity.

Notes:
- This script **modifies your cached token** on disk. After a
  successful run, the cache will hold a fresh token from the SignIn
  fallback (not the original) — this is harmless but worth knowing.
- Requires `NEMO_USERNAME` and `NEMO_PASSWORD` in the env so the
  SignIn-fallback step can succeed.
"""

from __future__ import annotations

import sys

from nemo_cli.api.client import api_request
from nemo_cli.auth.jwt import is_expiring_within
from nemo_cli.auth.token_store import get_token, set_token

CORRUPTED_TOKEN = "deliberately.invalid.token"


def _short(token: str, n: int = 24) -> str:
    return f"{token[:n]}…{token[-n:]}"


def main() -> int:
    print("Step 1: snapshot current cache state")
    original = get_token()
    if original is None:
        print(
            "  [!] No cached token to start with. Run `.venv/bin/nemo login` first.",
            file=sys.stderr,
        )
        return 1
    print(f"  current cached bearer: {_short(original)}")
    print()

    print("Step 2: overwrite cache with a deliberately invalid token")
    set_token(CORRUPTED_TOKEN)
    print(f"  cached bearer is now:  {CORRUPTED_TOKEN}")
    print()

    print("Step 3: hit a real endpoint via api_request")
    print("  GET /shared/Instrumentos/FiltrarInstrumentos?page=1&limit=1")
    print("  expected ladder: corrupted → 401 → Refresh fails → SignIn → retry → 200")
    print()
    response = api_request(
        "GET",
        "/shared/Instrumentos/FiltrarInstrumentos",
        params={
            "page": 1,
            "limit": 1,
            "filterNemotecnico": "",
            "codSubClaseInstrumentos": "ACC",
        },
    )
    print(f"  response status: {response.status_code}")
    print()

    print("Step 4: inspect the cache afterwards")
    after = get_token()
    if after is None:
        print("  [!] Cache is empty after the call — unexpected.", file=sys.stderr)
        return 1
    print(f"  cached bearer after:   {_short(after)}")
    print()

    print("=" * 60)
    print("Verdict")
    print("=" * 60)

    checks = [
        ("api_request returned 200 (full ladder succeeded)", response.status_code == 200),
        ("Cache was rewritten with a fresh token", after != CORRUPTED_TOKEN),
        ("Fresh cached token looks like a real JWT", after.count(".") == 2),
        (
            "Fresh cached token is not yet expired",
            not is_expiring_within(after, 0),
        ),
    ]

    all_ok = True
    for label, passed in checks:
        marker = "✓" if passed else "✗"
        print(f"  [{marker}] {label}")
        if not passed:
            all_ok = False

    if all_ok:
        print()
        print(
            "Reactive fallback works end-to-end:\n"
            "  corrupted bearer → 401 → Refresh rejected → SignIn → retry → 200."
        )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
