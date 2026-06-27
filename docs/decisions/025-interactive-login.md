# ADR-025: Interactive login replacing env-var credentials

## Status

Accepted

## Date

2026-06-26

## Context

Per ADR-003, the CLI obtains the user's email and password exclusively from the
`NEMO_USERNAME` / `NEMO_PASSWORD` environment variables, loaded via `dotenv` in
`nemo_cli.config`. Every command that needs authentication fails loudly unless
those variables are present, so a first-time user must create a `.env` file or
export shell variables before *anything* works — friction that contradicts the
"install once, use everywhere" UX goal behind ADR-004. The env-var requirement
is also the load-bearing assumption of ADR-003's re-authentication flow: on a
`401`, `api_request()` clears the cached token, calls `sign_in()` (which reads
the credentials from `config`), and retries. Remove the env vars and that silent
re-`sign_in` has no credentials to use.

We want `nemo login` to be a self-contained, human-friendly entry point: prompt
for credentials when run interactively, accept flags when scripted, and keep the
existing token cache — without ever writing the user's password to disk and
without the env-var ceremony.

## Decision

- **`nemo login` prompts interactively** for email and password (password input
  hidden), and **also accepts optional `--user` / `--password` flags** for
  non-interactive use. When a flag is supplied it is used as-is; otherwise the
  value is prompted for.
- **`sign_in()` receives credentials as explicit arguments** instead of reading
  them from `config`. The command layer owns credential collection (prompt or
  flags) and passes them down; the auth layer stays I/O-free with respect to the
  terminal.
- **Remove `NEMO_USERNAME` / `NEMO_PASSWORD` entirely.** Drop the dotenv
  credential load and the typed credential accessors from `nemo_cli.config`, and
  delete the variables from `.env.example`, `README.md`, and the env table in
  `CLAUDE.md`. `config` keeps only the hardcoded API base URL concern.
- **Never persist credentials to disk.** Only the bearer token (and refresh
  token, per ADR-012) is cached, exactly as today.
- **Rework the `api_request()` re-auth path.** On token expiry, renew via the
  RefreshToken endpoint (ADR-012). When refresh *also* fails, `api_request()` no
  longer re-`sign_in()`s — there are no credentials available — it surfaces a
  clear `Session expired — run \`nemo login\`` error and exits non-zero. The user
  re-authenticates explicitly.

## Alternatives Considered

- **OS keychain via `keyring`.** Store credentials in the macOS Keychain /
  Windows Credential Manager / libsecret so the token can be refreshed silently
  forever. Rejected: adds a third-party dependency and a cross-platform support
  surface for marginal benefit; the user explicitly prefers zero credentials on
  disk and an explicit re-login over silent storage.
- **Encrypted local credentials file.** Rejected: we would own key management and
  still write secrets to disk — more risk than simply re-prompting when the
  session fully expires.
- **Keep env vars as a CI/automation fallback.** Rejected: a single, unambiguous
  auth path is preferred; env-var support is dead weight for a personal CLI with
  no current CI authentication need. It can be reintroduced via a new ADR if an
  automation need arises.
- **Flags-only, no prompt.** Rejected: passwords passed on the command line leak
  into shell history and process listings.

## Consequences

- **Easier:** first-run UX — `nemo login` works with no `.env` setup; one obvious
  authentication path; no secrets written to disk; `config` shrinks to the API
  base URL concern only.
- **Harder / trade-offs:** a long-running command can fail mid-flight when *both*
  the access and refresh tokens have expired, requiring an explicit re-login.
  This is acceptable because RefreshToken renewal (ADR-012) makes full expiry
  rare. Any future CI/automation use must reintroduce a non-interactive
  credential source via a new ADR.
- **ADR-003 is amended:** its env-var credential mechanism and its automatic
  `401 → re-sign_in-from-env → retry` flow are superseded. Token-based
  persistence (the rest of ADR-003) stands. ADR-012's refresh flow becomes the
  primary renewal mechanism and the only silent re-authentication path.
- **CONVENTIONS.md / CLAUDE.md updates:** the "only `nemo_cli.config` reads
  `os.environ`" rule no longer has any credential variables to read; the
  Authentication section and the env table must be updated to describe the
  interactive flow and the explicit-re-login behaviour.
