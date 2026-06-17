# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

`nemo-cli` is a personal command-line tool to inspect holdings on Chilean
stockbroker portals. Currently compatible with the Vector Capital client portal
at `https://portalclientes.vectorcapital.cl/api`, which exposes three sub-
prefixes the CLI calls into: `/publicapi` (auth), `/shared` (local Chilean
instruments), and `/frontoffice` (international assets and portfolio summary).
The CLI authenticates with the public `SignIn` endpoint using the user's own
credentials provided via environment variables, caches the bearer token
locally, and never redistributes data.

> **Non-affiliation.** This project is not affiliated, endorsed, or sponsored
> by Vector Capital S.A. Corredores de Bolsa or any other broker. The README
> carries the user-facing version of this disclaimer.

## Methodology

This project follows **Context-First Development (CFD)**. The methodology essay lives
in `context-first-development.md` at the repo root (the conceptual source of truth for
*how* context, decisions, and sessions are managed); the upstream catalog is at
<https://github.com/albertomarturelo/context-first-development>. The project's binding
application of CFD is captured as process ADRs **013–021** (ADR-before-implementing,
English-only, Skills-over-slash-commands, document-corrections, atomic tasks, the
session-close ritual, short sessions, PR-review-against-context, work-units-as-issues).
`docs/session-flow.md` shows these flows as diagrams. Read the essay once if you are new;
do not re-read it every session.

## Architecture

@docs/ARCHITECTURE.md

## Tech Stack

@docs/STACK.md

## Conventions

@docs/CONVENTIONS.md

## Current Status

Tracked locally only — `docs/CURRENT_STATUS.md` is gitignored, so each clone
maintains its own working notes. Not loaded automatically; the CFD skills
(`/start-session`, `/status`) read it from disk when present.

## Key Decisions

@docs/decisions/_index.md

## Build & Run

- Install for everyday use (recommended): `pipx install .`
- Reinstall after local changes: `pipx install --force .`
- Install editable with dev tools: `pip install -e .[dev]`
- Run without installing: `python -m nemo_cli <command>`
- Run after install: `nemo <command>`
- Typecheck: `pyright`
- Lint: `ruff check .`
- Tests: `pytest`
- Run a single test file: `pytest tests/test_<file>.py`

## Environment

Credentials are loaded from environment variables (via `python-dotenv`). See
`.env.example`.

| Variable           | Required | Purpose                          |
|--------------------|----------|----------------------------------|
| `NEMO_USERNAME`  | yes      | Email used to sign in            |
| `NEMO_PASSWORD`  | yes      | Password used to sign in         |

The Vector API base URL is hardcoded in `nemo_cli.config.API_BASE_URL` — there is
no env override (see ADR-004). Reintroduce one via a new ADR if a staging environment
appears.

## Critical Rules

- **All HTTP traffic to the Vector API must go through `api_request()` in
  `src/nemo_cli/api/client.py`.** That function owns token retrieval, caching, and
  the 401-retry-after-refresh flow. Calling `httpx.request(...)` directly from a
  command bypasses re-authentication and will cause silent failures when tokens
  expire. The only allowed exception is `nemo_cli.auth.service.sign_in`, which is
  the bootstrap call. See ADR-003.
- **Never commit `.env` or any real credential.** `.env.example` is the only template
  in version control.
- **Document significant decisions as ADRs *before* writing the code that implements
  them.** Use the `new-decision` skill. Update `docs/decisions/_index.md` in the
  same change. See ADR-013 for the rationale.
- **When you correct a violated convention, fix the code *and* document the rule**
  (in `docs/CONVENTIONS.md`, or a new ADR if it warrants alternatives) in the same
  change — never leave the lesson only in chat. See ADR-016.
- **English for all model-facing context** (CLAUDE.md, docs/, ADRs, `.claude/skills/`,
  code identifiers, code comments). PR descriptions and chat with the user can be in
  Spanish — the user works in Spanish. See ADR-014.
- **Update `docs/CURRENT_STATUS.md` before closing every session.** This is how the
  next session knows what was in flight. CFD treats this as non-negotiable; run the
  `close-session` skill. See ADR-018.
- **The Vector API response shapes are not yet officially typed.** When integrating a
  new endpoint, capture a real response (redacted), then add a typed dataclass /
  `TypedDict` in the module that owns the call. Do not assume field names from
  external documentation without verification.
