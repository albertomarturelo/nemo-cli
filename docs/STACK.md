# Tech Stack

## Runtime

- **CPython** ≥ 3.11. Required by `pyproject.toml`.

## Language

- Python with type hints throughout. Checked with `pyright` in strict mode.

## Runtime dependencies

| Package          | Version  | Why it is here                                                   |
|------------------|----------|------------------------------------------------------------------|
| `typer`          | ≥ 0.12   | CLI framework — type-hint-driven, built on `click`.              |
| `httpx`          | ≥ 0.27   | HTTP client. Sync API used; async available if ever needed.      |
| `platformdirs`   | ≥ 4.0    | Cross-platform user-config directory for the cached token.      |
| `rich`           | ≥ 13.0   | Table rendering for `instruments` listings and other tabular UX. Already a transitive dep of `typer`; declared explicitly per ADR-006. |

## Dev dependencies

| Package      | Version  | Why                                                  |
|--------------|----------|------------------------------------------------------|
| `pytest`     | ≥ 8.0    | Test runner                                          |
| `pytest-cov` | ≥ 5      | Coverage measurement + the CI ≥ 95% gate (ADR-023)   |
| `pyright`    | ≥ 1.1    | Strict static type checking                          |
| `ruff`       | ≥ 0.5    | Linting + import sorting                             |
| `respx`      | ≥ 0.21   | Transport-level HTTP mocking in tests                |

## Why this stack

Documented in **ADR-004** (which supersedes ADR-002). The short version: `typer` +
`httpx` is the lowest-friction modern Python CLI stack, type hints checked with
`pyright` give us most of the safety we had under TypeScript, and `pipx install .`
provides the install-once-use-everywhere UX the user wanted. The Python data
ecosystem (`decimal`, `dateutil`, eventually `pandas`) is a future-proofing bet for
financial data parsing.

## Out of scope (do not add without an ADR)

- **No async runtime.** `httpx` sync calls are sufficient for sequential CLI usage.
- **No DI / config framework.** Direct imports work for a CLI of this size.
- **No bundling / single-file builds.** `pipx`-based installation is the only
  supported distribution path.
- **No structured logger.** `typer.echo` + colours via `typer.secho` until there is
  an actual reason to log.
