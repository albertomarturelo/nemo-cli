# nemo-cli

A personal command-line tool to inspect your holdings on Chilean stockbroker portals. Authenticates with your own credentials, caches a bearer token locally, and exposes portal operations as composable terminal commands.

> **Disclaimer.** This project is **not affiliated, endorsed, or sponsored** by Vector Capital S.A. Corredores de Bolsa or any other broker. It is a personal, unofficial client and is provided "as is", without any warranty. You are the sole responsible party for compliance with your contract with the broker whose portal you connect to. The CLI calls only documented endpoints reachable from the official web UI under your own session, with your own credentials, and never redistributes data. Currently compatible with the Vector Capital client portal at `portalclientes.vectorcapital.cl`.

## Highlights

- One-command authentication — `nemo login` exchanges credentials for a token and caches it per user.
- Transparent token refresh — every authenticated call retries once on `401` after re-authenticating.
- Credentials live in environment variables; only the short-lived token is persisted.
- Browse Chilean and US-listed instruments — `nemo instruments local` / `nemo instruments international`, with `--json` output for downstream agent / scripted consumption.
- Inspect your portfolio — `nemo portfolio summary` returns each holding plus computed P&L and totals by classification.
- 1-year price history per local instrument — `nemo instruments prices --id <ID>` with stats (total return, σ, min/max) and an ASCII sparkline.
- Cash movements with classification — `nemo portfolio movements` parses each row into `dividend` / `buy` / `sell` / `commission` / `cash_in` / `cash_out` and aggregates by nemotécnico, ready for dividend-yield analysis.
- Pure-Python, type-hinted (`pyright` strict), tested (~98% line coverage), distributed via `pipx`.

## Requirements

- Python **≥ 3.11**
- [`pipx`](https://pipx.pypa.io/) (recommended) or `pip`
- A Chilean stockbroker portal account (currently: Vector Capital)

## Installation

The recommended path is [`pipx`](https://pipx.pypa.io/) so the `nemo` command is available in every terminal — isolated venv, automatic `$PATH` wiring, clean uninstall.

### 1. Install `pipx` (one-time)

**macOS (Homebrew):**

```bash
brew install pipx
pipx ensurepath
```

**Any platform (with `pip`):**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

After running `pipx ensurepath`, open a new terminal so the updated `$PATH` is picked up. Verify with `pipx --version`.

### 2. Install nemo-cli

```bash
git clone <repo-url> nemo-cli
cd nemo-cli
pipx install .
```

To upgrade after pulling new changes:

```bash
pipx install --force .
```

To uninstall:

```bash
pipx uninstall nemo-cli
```

## Configuration

Credentials are read from environment variables. The simplest way is a `.env` file at the project root (or your shell session):

```bash
cp .env.example .env
# then edit .env with your credentials
```

| Variable           | Required | Description               |
|--------------------|----------|---------------------------|
| `NEMO_USERNAME`  | yes      | Email used to sign in     |
| `NEMO_PASSWORD`  | yes      | Account password          |

> The Vector API base URL is intentionally hardcoded in `nemo_cli.config`. There is no env override; if you need one (e.g. for a staging environment), add an ADR first.

> The `.env` file is gitignored. Never commit real credentials.

The cached bearer token is stored under your OS user-config directory, e.g. `~/Library/Application Support/nemo-cli/token.json` on macOS. Run `nemo logout` to clear it.

## Usage

```bash
nemo login                              # authenticate and cache the token
nemo whoami                             # show the configured user and token state
nemo logout                             # drop the cached token
nemo instruments local --search BCI     # list Chilean instruments matching "BCI"
nemo instruments international --search aapl --page-size 5
nemo instruments prices --id 52185      # 1-year price history (local instruments only)
nemo portfolio summary                  # holdings + P&L + totals by classification
nemo portfolio movements                              # default window: last 365 days
nemo portfolio movements --desde 2025-01-18 --hasta 2026-01-25   # explicit date range (YYYY-MM-DD)
nemo --version                          # print the CLI version and exit
nemo --help                             # general help
nemo <cmd> --help                       # per-command help
```

### Commands

| Command                       | Description                                                                      |
|-------------------------------|----------------------------------------------------------------------------------|
| `login`                       | Authenticate against the configured broker portal and cache the bearer token.    |
| `logout`                      | Clear the cached bearer token.                                                   |
| `whoami`                      | Show the configured user and whether a token is currently cached.                |
| `instruments local`           | List Chilean instruments. Filters: `--search`, `--classes`, `--page`, `--limit`. |
| `instruments international`   | List US-listed assets. Filters: `--search`, `--exchange`, `--page`, `--page-size`. |
| `instruments prices`          | Show ~1 year of daily prices for a local Chilean instrument (stats + sparkline). Flag: `--id`. **Local instruments only.** |
| `portfolio summary`           | Show your holdings with P&L and totals by classification. Flags: `--account-id`, `--currency`, `--with-dividends/--no-dividends`. |
| `portfolio movements`         | List cash movements over a date range, classified per kind (dividend / buy / sell / commission / cash flows) with per-nemotécnico aggregates. Flags: `--desde YYYY-MM-DD` (default: 1 year ago), `--hasta YYYY-MM-DD` (default: today), `--account-id`. |

All listing commands accept `--json` to emit a machine-readable payload
(`{ market, page, page_size, total, items: [...] }`) instead of a Rich table.
That payload is the integration contract for downstream tooling.

More commands will be added incrementally.

## Development

For day-to-day development, install editable inside a virtual environment so changes are picked up immediately and tooling stays isolated from the rest of your system.

### Create and activate the venv

```bash
python3 -m venv .venv               # create the venv (one time)
source .venv/bin/activate           # activate it — macOS / Linux (bash, zsh)
# source .venv/bin/activate.fish      # fish shell
# .venv\Scripts\Activate.ps1          # PowerShell on Windows
pip install --upgrade pip
pip install -e .[dev]               # editable install with dev deps
```

Your prompt will show `(.venv)` while the environment is active. Leave it with `deactivate`.

### Day-to-day commands

```bash
python -m nemo_cli <cmd>     # run from source without installing the entry point
nemo <cmd>                   # the entry point also works (editable install wires it)
pyright                      # typecheck (strict, src/ only)
ruff check .                 # lint + import sort (src/ + tests/)
pytest                       # run the unit-test suite
pytest -k <name>             # run a single test or pattern
```

> If you only want a one-off run without polluting your shell, you can skip activation and call the binaries directly: `.venv/bin/nemo <cmd>`, `.venv/bin/pytest`, etc.

### Testing

The unit-test suite mirrors the package tree under `tests/` and runs in well
under a second. No real network calls — `httpx` is intercepted at the
transport layer with [`respx`](https://github.com/lundberg/respx) — and no
real filesystem writes outside `tmp_path`.

```bash
pytest                                   # ~144 tests, ~98% line coverage
pytest tests/portfolio/                  # one package
pytest tests/portfolio/test_summary.py   # one file
pytest -k "compute_totals"               # by name pattern
```

What the suite covers:

- Pure parsers (`_to_*`) and aggregators (`_compute_*`, `_sparkline`) — 100%.
- HTTP services (`sign_in`, `api_request`, the four list / detail endpoints) — happy paths plus the 401-refresh-and-retry-once flow, mocked end-to-end with `respx`.
- CLI commands via `typer.testing.CliRunner` — table output, args passthrough, `--json` envelope shape, error paths exit `1`.

Conventions for adding tests live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) (testing section). There is
**no CI/CD configured** at the moment — checks run locally before opening
a PR.

## Project Structure

```
.
├── CLAUDE.md                       # Index of agent-facing context
├── CHANGELOG.md                    # Keep a Changelog (see Versioning)
├── context-first-development.md    # CFD methodology
├── pyproject.toml                  # Project metadata, deps, entry point
├── docs/
│   ├── ARCHITECTURE.md
│   ├── STACK.md
│   ├── CONVENTIONS.md
│   └── decisions/                  # Architecture Decision Records
├── .claude/skills/                 # CFD skills (start-session, status, new-decision, validate-context)
├── src/nemo_cli/
│   ├── cli.py, __main__.py         # Entry + Typer app
│   ├── commands/                   # One module per subcommand (login, logout, whoami, instruments, portfolio)
│   ├── portfolio/                  # Holdings service + P&L / totals computation
│   ├── instruments/                # Local + international market services + price history
│   ├── api/client.py               # api_request — single point for portal HTTP
│   ├── auth/                       # SignIn call and local token store
│   └── config.py                   # Env-var loader; hardcoded base URL
└── tests/                          # Unit tests, mirror src/nemo_cli/ tree
    ├── conftest.py                 # Shared fixtures (env, isolated token store)
    ├── auth/, api/, instruments/, portfolio/, commands/
    └── test_cli.py, test_config.py
```

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/) and
maintains a [Keep a Changelog](https://keepachangelog.com/) — see
[`CHANGELOG.md`](CHANGELOG.md). The current version is the one declared in
`pyproject.toml` and mirrored in `nemo_cli.__version__`. The release process
is documented in [ADR-007](docs/decisions/007-versioning-and-changelog.md).

## Methodology

This repository follows **Context-First Development (CFD)**. Architecture, conventions, and decisions live in [`docs/`](docs/); the methodology itself is documented in [`context-first-development.md`](context-first-development.md). When pairing with an AI agent, start with [`CLAUDE.md`](CLAUDE.md).

### Starting a development session

The CFD session-start ritual loads project context without scanning source code — the agent orients itself in ~500 tokens instead of tens of thousands.

```bash
# 1. Sync the working copy with the remote
git pull --ff-only

# 2. Glance at open work (optional, requires GitHub CLI)
gh pr list --state open
gh issue list

# 3. Start Claude Code from the repo root
claude

# 4. Inside the session, run the orientation skill
> /start-session
```

`/start-session` reads `docs/CURRENT_STATUS.md` (a local-only file — see "Closing a session" below) and [`docs/decisions/_index.md`](docs/decisions/_index.md), and returns a short summary of what was in flight, what is blocked, and what the next priority should be. The other CFD skills shipped in [`.claude/skills/`](.claude/skills/):

| Skill                | When to use                                                                                |
|----------------------|--------------------------------------------------------------------------------------------|
| `/start-session`     | At the start of every session — load current status + recent decisions.                    |
| `/status`            | Quick "where are we" without the full orientation.                                         |
| `/new-decision`      | Before implementing any significant technical choice — captures it as an ADR.              |
| `/validate-context`  | Audit context-file integrity (CLAUDE.md size, @-references, ADR index, status freshness).  |

### Closing a session

Before ending, ask the agent to create or update `docs/CURRENT_STATUS.md` with what was done, what is still pending, and any blockers discovered. That file is the only thing the next session reads to know where work was left — skipping it breaks the loop.

`docs/CURRENT_STATUS.md` is **gitignored on purpose** — it is working state, not a shared artifact, so each clone keeps its own notes. The file does not exist in a fresh clone; the first `/start-session` after `git clone` will simply have less context to summarise, and you create the file when you close the session.

## Security

- Credentials never touch disk through this CLI. They are read from `os.environ` at command time.
- Only the bearer token is persisted, in a per-user JSON file under your OS config directory.
- Run `nemo logout` (or delete the JSON file) to revoke the local session at any time.
