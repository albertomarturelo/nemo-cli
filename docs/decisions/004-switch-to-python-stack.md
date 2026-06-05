# ADR-004: Switch CLI Stack to Python (typer + httpx + pipx)

## Status

Accepted (supersedes ADR-002)

## Date

2026-05-01

## Context

ADR-002 chose Node.js + TypeScript + commander as the foundation stack. After the
initial scaffold was in place, the user clarified two preferences:

1. The "install once, invoke from anywhere" UX matters. The Python `pipx` idiom
   (`pipx install .`) was the user's mental model — isolated venv, binary on
   `$PATH`, single-command uninstall.
2. Python is the user's preferred language for this kind of utility.

Node.js does offer the same end-state via `npm link` / `npm install -g`, but the
user explicitly preferred Python. Combined with the likelihood that future commands
will parse financial data (statements, transactions, CLP amounts), the Python data
ecosystem (`decimal`, `dateutil`, eventually `pandas`) is a better fit.

## Decision

Replace the Node.js stack with:

- **Runtime:** CPython ≥ 3.11.
- **CLI framework:** `typer` (built on `click`).
- **HTTP client:** `httpx` (sync API).
- **Config dir / token store:** `platformdirs` for the OS-correct user config path,
  plain JSON for the token file.
- **Env loading:** `python-dotenv`.
- **Dev tooling:** `pytest`, `pyright` (strict), `ruff`.
- **Build / packaging:** `pyproject.toml` + Hatchling backend.
- **Distribution:** `pipx install .` from the repo root.

The package layout is `src/nemo_cli/` with a `[project.scripts]` entry exposing
`nemo = "nemo_cli.cli:main"`.

The Vector API base URL is **hardcoded** as a module constant in
`nemo_cli.config`. No env override is exposed; reintroduce one via a new ADR
if and when a staging environment appears.

## Alternatives Considered

- **Stay on Node + `npm link`.** Functionally equivalent install UX, but the user
  preferred Python and we would still pay an ongoing tax in financial-data parsing.
  Rejected.
- **Python + Click directly (no Typer).** Slightly less abstraction, but Typer gives
  us type-hint-driven argument parsing for free, which keeps command handlers terse.
  Rejected.
- **Python + `requests`.** Mature but in maintenance mode and lacking the ergonomic
  API of `httpx` (timeouts, async option for free). Rejected.
- **Expose an env override for the API base URL.** YAGNI — there is no
  staging environment today, and an env-var-overridable base URL is a
  footgun for credentials sent to the wrong host. Reintroduce only when
  justified.

## Consequences

- All previous Node source files, `package.json`, `tsconfig.json`, `dist/`, and
  `node_modules/` are removed in this change.
- ADR-003 still holds (env vars for credentials, cached token, 401 retry); the
  implementation language changes and the API base URL is hardcoded. ADR-003 is
  updated to reflect the new file paths and the dropped env override.
- Future contributors need a Python ≥ 3.11 toolchain. `pipx` is the recommended
  install path; `pip install -e .[dev]` works for development.
- Tests are now `pytest`-driven; conventions for test placement are under `tests/`.
