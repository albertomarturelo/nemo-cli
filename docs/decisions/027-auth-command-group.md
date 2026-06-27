# ADR-027: Group auth commands under `nemo auth`; remove `whoami`

## Status

Accepted

## Date

2026-06-26

## Context

After ADR-025 / ADR-026 the authentication commands were flat, top-level
commands: `nemo login`, `nemo logout`, `nemo whoami`, `nemo status`. The
portal-data commands are already grouped as Typer sub-apps —
`nemo instruments ...` and `nemo portfolio ...` — so the auth commands are the
odd ones out. Grouping them under `nemo auth` gives a consistent, discoverable
surface.

Separately, ADR-025 reduced `whoami` to reporting only whether a token is
cached. `status` (ADR-026) now reports a richer state (`logged_out` / `active` /
`expiring` / `expired`) that strictly contains what `whoami` showed, so `whoami`
is redundant.

## Decision

- **Introduce a `nemo auth` Typer sub-app**, assembled in `commands/auth.py`
  (mirroring `instruments` / `portfolio`), grouping the auth verbs:
  `nemo auth login`, `nemo auth logout`, `nemo auth status`. The per-verb
  modules (`login.py`, `logout.py`, `status.py`) stay one-verb-each; `auth.py`
  only wires them into the sub-app, registered in `cli.py` via `add_typer`.
- **Remove the `whoami` command and its module** — `status` supersedes it.
- **Update all "run `nemo login`" guidance** (the session-expired error in
  `api.client`, the `status` messages, and the docs) to `nemo auth login`.
- This **amends the command surface** of ADR-025 (`login` / `whoami`) and
  ADR-026 (flat `nemo status`); the decisions those ADRs recorded
  (interactive login, the `auth.session` layer) are unchanged.

## Alternatives Considered

- **Keep flat top-level auth commands.** Rejected: inconsistent with the
  `instruments` / `portfolio` grouping; a `nemo auth ...` namespace is what the
  user asked for and reads better as the CLI grows.
- **Keep `whoami` alongside `status`.** Rejected: post-ADR-025 `whoami` is a
  strict subset of `status` — two commands for one concern.
- **Group only `login` + `status`.** Rejected: `logout` is just as much an auth
  verb; grouping all three is the consistent choice.
- **Put all three verbs in one `auth.py` module** (like `instruments.py`).
  Rejected in favour of keeping the thin per-verb modules and a small assembler,
  so each verb stays independently testable and the diff is minimal.

## Consequences

- CLI surface becomes `nemo auth login | logout | status`. `nemo login`,
  `nemo logout`, `nemo whoami`, `nemo status` no longer exist — a breaking change
  for muscle memory and any scripts, acceptable while the package is `0.0.x`
  (ADR-007).
- The "Rich whoami" future work folds into enriching `status` rather than a
  separate command.
- `ARCHITECTURE.md` (module map, data flow), `README.md`, `CLAUDE.md`,
  `CONVENTIONS.md`, and the `CHANGELOG` are updated to the new surface.
- ADR-025 and ADR-026 are annotated in the index as having their command surface
  amended here.
