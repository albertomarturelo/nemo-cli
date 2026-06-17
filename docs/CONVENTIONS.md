# Conventions

## File and module layout

- One subcommand per module under `src/nemo_cli/commands/`. The module exports a
  single function named after the verb (e.g. `login`, `logout`). `nemo_cli.cli`
  registers it via `app.command()(login)`.
- Module names are `snake_case.py`. Function and variable names are `snake_case`,
  classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Imports are absolute (`from nemo_cli.api.client import api_request`), never
  relative.
- Only `nemo_cli.config` is allowed to read `os.environ` directly. Every other
  module imports typed accessors from there.

## HTTP

- All requests to the Vector portal go through `api_request()` in
  `nemo_cli.api.client`. No `httpx.request(...)` calls in command handlers or
  services. The only exception is `nemo_cli.auth.service.sign_in`, which is the
  bootstrap call.
- Endpoint paths passed to `api_request()` are *relative* to the configured base URL
  (e.g. `/shared/auth/SignIn`, not the full URL).
- Response shapes from the Vector API are typed at the call site, in the module that
  owns the call. Do not add a global `types` module dump.

### Timeouts

`api_request()` accepts a `timeout: float` keyword (default **15s**) that
`httpx` applies uniformly to every phase — connect / read / write / pool
each get the same budget. For most Vector endpoints (auth, instruments
listing, portfolio summary, prices) 15s is comfortable.

Two endpoints are known to require a bigger budget; both override the
timeout at the service layer rather than bumping the global default:

| Service                             | Timeout | Why                                                                                            |
|-------------------------------------|---------|------------------------------------------------------------------------------------------------|
| `portfolio.movements.get_movements` | **180s** | The endpoint generates the full year of cash movements in one shot and is the slowest in the suite. 60s was empirically insufficient; 180s holds today. |

If even 180s stops working, the next escalation is to switch
`api_request`'s signature to accept either `float` **or**
`httpx.Timeout(connect=10, read=300, write=30, pool=10)` and pass the
structured form from the slow service. Keep the global default a plain
`float` — only the slow services need the structured override.

When you discover a new slow endpoint:

1. Confirm the slowness empirically (the symptom is a `ReadTimeout`
   raised by httpx).
2. Override at the service layer with a generous `timeout=...`. Do not
   bump the global default — the global default protects fast paths
   from masking real problems.
3. Add a row to the table above and explain the empirical reason.

## Authentication

- Credentials live exclusively in environment variables (`NEMO_USERNAME`,
  `NEMO_PASSWORD`). They are never written to disk by this CLI.
- The bearer token is cached as JSON at
  `platformdirs.user_config_path("nemo-cli") / "token.json"`. On macOS this lands
  in `~/Library/Application Support/nemo-cli/token.json`.
- A `401` response invalidates the cached token, triggers a fresh `SignIn`, and
  retries the original request **once**. A second `401` is surfaced as an error.

## Error handling

- Command handlers catch errors at the top level, print a red one-line message via
  `typer.secho(..., fg=typer.colors.RED, err=True)`, and raise `typer.Exit(code=1)`.
  Stack traces are not printed unless `--verbose` is implemented (not yet).
- Library code (`auth/`, `api/`, `config`) raises plain `RuntimeError` with
  human-readable messages. No custom exception classes until there is a real reason
  for one.

## Output

- Human-readable output goes to **stdout** for results and **stderr** for errors.
- Use `typer.colors.GREEN` for success, `RED` for errors, `YELLOW` for warnings.
- `--json` is the convention for machine-readable output and is added **per
  command** (not as a global flag). Each `--json` payload is a JSON object that
  echoes the request scope and the typed result, e.g.
  `{ "market": "...", "page": N, "page_size": N, "total": N, "items": [...] }`.
  This output is the contract for downstream agent / scripted consumers.

## Type checking

- `pyright` runs in strict mode. All public functions get explicit return types.
- Prefer modern PEP-604 unions (`str | None`) over `Optional[str]`.
- Avoid `Any`. If a Vector response shape is unknown, use `object` or
  `dict[str, object]` and narrow with `isinstance`.

## Testing

- Tests live under `tests/` mirroring the package tree (`tests/auth/`,
  `tests/api/`, `tests/instruments/`, `tests/portfolio/`, `tests/commands/`).
  Use `pytest`.
- HTTP mocking goes through **`respx`** (transport-level interception of
  `httpx`). No real network calls in any test; no sandbox account exists.
- Shared fixtures live in `tests/conftest.py`:
  - `credentials_env` / `no_credentials_env` — toggle `NEMO_USERNAME` /
    `NEMO_PASSWORD` deterministically.
  - `isolated_token_store` — redirects the token-cache file to a per-test
    `tmp_path`, so tests never touch the user's real config dir.
  - `cached_token` — pre-populates the isolated store with a known token.
- CLI commands are tested via `typer.testing.CliRunner`, mocking the
  underlying service functions with `unittest.mock.patch` (avoids the
  `respx` round-trip when only the wiring is under test).
- Private helpers (e.g. `_compute_stats`, `_to_holding`, `_sparkline`) are
  imported directly in tests — they are tested as units even though the
  underscore signals "internal".
- Tests are **excluded from pyright strict** (`[tool.pyright] include = ["src"]`)
  to avoid noise from `pytest`'s fixture-injection idiom; `ruff` still
  enforces style and import order on test code.
- Coverage target: **≥ 95%** of the source under `src/nemo_cli/`. Pure
  helpers and parsers are expected to be 100%; the only acceptable misses
  are unreachable entry-point code (`__main__.py`, `cli.main()` body) and
  rare display branches (e.g. pagination hint when more pages remain).
- **CI** (`.github/workflows/ci.yml`, ADR-023) runs `pytest`, `ruff check`,
  and `pyright` on every PR and push to `main`, plus a `validate-context`
  job enforcing ADR index/completeness and the `api_request()` boundary
  (ADR-003). Run all three locally before opening a PR.

## CFD workflow (Skills)

Every CFD procedure is a **Claude Skill** under `.claude/skills/<name>/SKILL.md`
— including the mandatory session boundaries (ADR-015 records why Skills, not
slash commands). One primitive, one mental model; no slash-command duplicates.

| Procedure                | Skill              | Implements         |
|--------------------------|--------------------|--------------------|
| Orient at session start  | `start-session`    | —                  |
| Quick status read        | `status`           | —                  |
| Close the session        | `close-session`    | ADR-018            |
| Capture a decision (ADR) | `new-decision`     | ADR-013            |
| Audit context integrity  | `validate-context` | —                  |
| Review a PR              | `review-pr`        | ADR-020            |
| Create a work unit       | `issue-new`        | ADR-021            |
| Pick up a work unit      | `issue-start`      | ADR-021            |

Work crossing session boundaries lives as a GitHub Issue with the fixed body
template (ADR-021), not only in `CURRENT_STATUS.md`.

## Patterns we explicitly avoid

- **No module-level mutable state** beyond the `dotenv.load_dotenv()` call in
  `config`. Pass dependencies as arguments where it would otherwise be tempting.
- **No silent fallbacks** for missing credentials — fail loudly at startup of any
  command that needs them.
- **No new third-party HTTP / config dependencies** without an ADR. The current set
  is intentionally minimal.
