# Architecture Overview

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         User terminal                             │
└────────────────────────────────┬─────────────────────────────────┘
                                 │  nemo <command> [...args]
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ nemo_cli.cli           Typer app, registers subcommands         │
│ nemo_cli.__main__      python -m nemo_cli entry               │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ nemo_cli.commands.*    one module per subcommand                │
│                          Pure orchestration — no HTTP here.       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ nemo_cli.api.client    api_request(): adds Authorization,       │
│                          refreshes token on 401, single source    │
│                          of truth for HTTP to the Vector portal.  │
└──────┬─────────────────────────────────────────────┬─────────────┘
       │                                             │
       ▼                                             ▼
┌─────────────────────────┐                ┌────────────────────────────┐
│ nemo_cli.auth.service │                │ nemo_cli.auth.token_store│
│ POST /shared/auth/SignIn│                │ persists token as JSON in  │
│ returns bearer token    │                │ user-config dir            │
└────────────┬────────────┘                └────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ nemo_cli.config        Hardcodes API_BASE_URL. No env vars; │
│                          credentials come from `nemo login`.     │
└──────────────────────────────────────────────────────────────────┘
```

## Layer Structure

- **Entry layer** (`nemo_cli.cli`, `nemo_cli.__main__`) — wires `typer`, parses
  `argv`, dispatches to a command handler. Knows nothing about HTTP or
  authentication.
- **Command layer** (`nemo_cli.commands`) — one module per subcommand. Handlers
  translate CLI flags into service calls, format output for humans, and choose exit
  codes. They do not call `httpx` directly.
- **API layer** (`nemo_cli.api.client`) — the only module that performs
  authenticated HTTP calls to the Vector portal. Centralises auth-header injection
  and the renewal flow: proactive/reactive `RefreshToken`, surfacing
  `session expired — run nemo login` when renewal fails (ADR-025).
- **Auth layer** (`nemo_cli.auth`) — `service` obtains a token from the `SignIn`
  endpoint using credentials passed in by the `login` command (never read from the
  environment), and renews via `RefreshToken`; `token_store` persists and clears the
  token locally.
- **Config layer** (`nemo_cli.config`) — holds the hardcoded API base URL. It no
  longer reads environment variables: credentials are entered interactively via
  `nemo login` (ADR-025).

## Module Map

| Module                       | Purpose                                                      | Key files                                |
|------------------------------|--------------------------------------------------------------|------------------------------------------|
| Entry                        | CLI bin and program assembly                                 | `src/nemo_cli/cli.py`, `__main__.py`   |
| Commands                     | Subcommand handlers (login, logout, whoami, instruments, …)  | `src/nemo_cli/commands/`               |
| API                          | Authenticated HTTP client                                    | `src/nemo_cli/api/client.py`           |
| Auth                         | SignIn + RefreshToken calls, JWT-exp peek, local token persistence | `src/nemo_cli/auth/`               |
| Instruments                  | Local + international market services and dataclasses        | `src/nemo_cli/instruments/`            |
| Portfolio                    | Holdings service + computed totals (P&L, classification breakdown) + movements (dividends, trades, cash flows) | `src/nemo_cli/portfolio/`        |
| Config                       | Env-var loader, hardcoded API base URL                       | `src/nemo_cli/config.py`               |

## API base URL and sub-prefixes

`API_BASE_URL = "https://portalclientes.vectorcapital.cl/api"`. Each caller passes
the explicit sub-prefix:

| Sub-prefix      | Used by                                            |
|-----------------|----------------------------------------------------|
| `/publicapi`    | `auth.service` — `POST /publicapi/shared/auth/SignIn` and `GET /publicapi/shared/auth/RefreshToken` (renewal, ADR-012) |
| `/shared`       | `instruments.local` — `GET /shared/Instrumentos/FiltrarInstrumentos` |
| `/frontoffice`  | `instruments.international` — `GET /frontoffice/shared/Asset` |
| `/frontoffice`  | `portfolio.summary` — `GET /frontoffice/shared/cartera/CierreCarteraResumidaOnline` |
| `/frontoffice`  | `instruments.prices` — `GET /frontoffice/shared/PublicadorPrecio/GetPreciosInstrumento` (local instruments only) |
| `/frontoffice`  | `portfolio.movements` — `GET /frontoffice/shared/MovimientosCajas/Movimientos` |

## Data Flow

1. The user runs `nemo <command>` (or `python -m nemo_cli <command>`).
2. `typer` dispatches to the matching handler in `nemo_cli.commands`.
3. The handler calls `api_request()` for any portal request, never `httpx`
   directly.
4. The user first authenticates with `nemo login`, which collects credentials
   (prompt or `--user` / `--password` flags), calls `service.sign_in(...)`, and
   caches the returned bearer token. Credentials are never stored.
5. `api_request()` reads the cached token from `token_store`. If it is close to
   expiry it renews via `RefreshToken` first. The request is then sent with
   `Authorization: Bearer <token>`. On `401`, it tries `RefreshToken` once and
   retries; if renewal fails (or no token is cached) it raises
   `Session expired — run nemo login` — there are no stored credentials to
   re-`SignIn` (ADR-025).
6. The handler renders the result to stdout (`typer.echo` / `typer.secho`) and
   exits with `0` on success or `1` on failure (via `typer.Exit`).

## External Dependencies

| Service                                  | Purpose                          | Notes                                      |
|------------------------------------------|----------------------------------|--------------------------------------------|
| `portalclientes.vectorcapital.cl`        | Vector Capital client portal API | Auth via `POST /shared/auth/SignIn`        |
