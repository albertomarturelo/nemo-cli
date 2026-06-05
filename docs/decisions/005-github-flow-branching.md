# ADR-005: GitHub Flow as Branching Strategy

## Status

Accepted

## Date

2026-05-01

## Context

Now that the repository is published to GitHub
(`github.com/albertomarturelo/nemo-cli`), we need an explicit branching strategy.
The project is a small CLI worked on primarily by one developer with AI assistance,
but the choice of strategy still affects:

- How features land on `main` (and therefore on whatever release artifacts get
  built from it).
- Whether code review is enforced and where it happens.
- How the CFD `CURRENT_STATUS.md` and ADR index stay synchronized with the code
  state — every change to `main` should be associated with a discoverable PR
  description that points at the relevant decisions.

Without an explicit policy, the default failure mode is direct commits to `main`
that mix code, ADR updates, and status updates without an audit trail.

## Decision

Adopt **GitHub Flow** as the branching strategy:

1. `main` is always installable. Anything merged to `main` is expected to pass
   `pyright`, `ruff check`, and `pytest`.
2. All work happens on short-lived feature branches cut from `main`. Branch names
   follow `<type>/<slug>`, where `<type>` is one of `feat`, `fix`, `docs`,
   `chore`, `refactor`, or `test`. Examples: `feat/proactive-token-refresh`,
   `fix/whoami-empty-token`, `docs/adr-006-something`.
3. Every change to `main` goes through a Pull Request — including solo work. The
   PR description references any relevant ADR or CFD context update.
4. PRs are merged via **squash merge**. The squash commit message uses
   Conventional-Commits-style prefixes (`feat:`, `fix:`, `docs:`, `chore:`,
   `refactor:`, `test:`) and ends with the standard `Co-Authored-By` footer when
   the change is AI-assisted.
5. Branches are deleted on the GitHub side after merge.
6. `main` is protected once GitHub branch protection is configured: no direct
   pushes, PRs required.

## Alternatives Considered

- **Trunk-based with direct pushes to `main`.** Lowest ceremony, fine for a solo
  developer, but loses the audit trail that comes for free with PRs and makes it
  harder to attach CFD updates (ADRs, `CURRENT_STATUS.md`) to specific changes.
  Rejected.
- **Git Flow (develop / release / hotfix branches).** Designed for versioned
  software with parallel maintenance lines. Overkill for a single-release-line
  CLI. Rejected.
- **Release branching.** Useful when multiple production versions must be
  supported simultaneously. Not the case here. Rejected.

## Consequences

- Every change has a discoverable, reviewable PR. ADR + `CURRENT_STATUS.md`
  updates travel with the code that needs them, satisfying the CFD principle of
  keeping context synchronized with implementation.
- Setting up GitHub branch protection on `main` is required to enforce the
  policy. Tracked as a one-time setup item in `docs/CURRENT_STATUS.md`.
- Squash merges keep `main`'s history linear and easy to read; the per-PR commit
  history is preserved on GitHub but does not pollute `git log` on `main`.
- A solo workflow still applies: open a PR against your own repo, self-review,
  merge. The discipline is the point — not the second pair of eyes.
- The initial bootstrap commit (root) was made directly to `main` before this
  ADR existed; that is grandfathered in. From this commit forward, the flow
  applies.
