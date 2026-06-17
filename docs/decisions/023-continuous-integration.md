# ADR-023: Continuous Integration via GitHub Actions

## Status

Accepted

## Date

2026-06-16

## Context

nemo-cli has had no CI: `pytest`, `ruff`, and `pyright` ran only locally, and
branch protection on `main` required a PR but enforced **no status checks**
(tracked as the top "Next Priority" in `CURRENT_STATUS.md`). A regression — or a
broken ADR index — could merge while looking green. The sibling project
`sii-cli` runs a GitHub Actions pipeline; this ADR adopts the same shape adapted
to nemo's stack. ADR-013 requires documenting a new workflow step before
implementing it, hence this record.

## Decision

Add `.github/workflows/ci.yml`, triggered on `pull_request` and `push` to
`main`, with three jobs:

1. **`tests`** — matrix over Python **3.11 / 3.12 / 3.13** (the supported
   range): `pip install -e .[dev]`, then `pytest` and `ruff check .`.
2. **`types`** — `pyright` in strict mode (single version, 3.12).
3. **`validate-context`** — codifies the `validate-context` skill as enforced
   gates: ADR index integrity (files ↔ `_index.md`), ADR 5-section completeness
   (Status / Context / Decision / Alternatives Considered / Consequences), the
   **`api_request()` boundary guard** (no `httpx.*` usage in `src/` outside
   `api/client.py` and `auth/service.py`, per ADR-003), and an optional PII
   RUT-denylist guard that is skipped unless the `PII_RUT_DENYLIST` secret is set.

Actions are pinned at `checkout@v4` / `setup-python@v5` with pip caching. Once
the workflow is green, it is marked a **required status check** on `main`'s
branch protection (a one-time GitHub setting). CI does **not** publish — the
existing `publish.yml` (OIDC Trusted Publishing) remains the release path.

## Alternatives Considered

- **Keep local-only checks.** Relies entirely on discipline; a tired solo
  developer merges red. The whole point of branch protection is undercut without
  a required check. Rejected.
- **Copy `sii-cli`'s `ci.yml` verbatim.** It uses `uv` + `mypy` + `ruff format`
  + a frozen lockfile — none of which nemo uses (pip + `pyright` + `ruff check`,
  no formatter, no lockfile). Adapted instead of copied.
- **Fold release/publish into this workflow.** nemo already publishes via
  `publish.yml` over OIDC; merging the concerns would regress a better setup.
  Rejected.

## Consequences

- Every PR and push to `main` runs tests + lint + types + context checks; a red
  build is visible before merge.
- The `validate-context` job turns CFD context-integrity rules — and ADR-003's
  HTTP boundary — into enforced gates, not just a skill someone remembers to run.
- One-time manual follow-up: mark the CI check **required** in branch protection
  (until then it informs but does not block). Optional: set the
  `PII_RUT_DENYLIST` secret to activate the PII guard.
- Adds ~1–2 minutes per push; pip caching keeps it fast.
