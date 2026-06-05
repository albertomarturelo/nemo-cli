# ADR-007: Versioning Policy — SemVer + Keep a Changelog

## Status

Accepted

## Date

2026-05-01

## Context

The CLI now has its first usable surface (`login`, `logout`, `whoami`,
`instruments local`, `instruments international`). Two questions need to be
locked before we cut a first release:

1. What version-numbering scheme do we follow?
2. How is the changelog maintained, and what is the release process?

Without explicit answers, future releases will drift between ad-hoc tags and
unspecified compatibility promises — which would be especially painful once a
downstream consumer (e.g. the planned Chilean-investing-research agent that
will read `nemo instruments … --json`) needs to pin a known surface.

## Decision

- **Versions follow [Semantic Versioning 2.0.0](https://semver.org/).** The
  CLI's public surface is its set of subcommands, flags, and the `--json`
  payload schema. Bumping rules:
  - **MAJOR** — removed or renamed subcommand or flag, or breaking change to
    the `--json` payload shape.
  - **MINOR** — new subcommand, new flag, or new field in `--json`.
  - **PATCH** — bug fixes, internal refactors, doc updates, or dependency
    bumps with no surface change.
  - We start at `0.0.1`. While at `0.x.y`, MINOR bumps may carry breaking
    changes, but they must be called out explicitly in the changelog.
    The `0.0.x` range additionally signals that even PATCH bumps may
    change the public surface without notice — promotion to `0.1.0` is
    the signal that the surface stabilises into normal SemVer.

- **Changelog follows [Keep a Changelog 1.1.0](https://keepachangelog.com/).**
  - File: `CHANGELOG.md` at the repo root.
  - Sections per version, in this order: `Added`, `Changed`, `Deprecated`,
    `Removed`, `Fixed`, `Security`.
  - The top of the file always carries `## [Unreleased]`.
  - Each released version is dated and has a footer reference link (compare
    URL to the previous tag).

- **Release process.** A release is a single PR that:
  1. Moves entries from `## [Unreleased]` into a new
     `## [X.Y.Z] - YYYY-MM-DD` block.
  2. Bumps `version` in `pyproject.toml`.
  3. Bumps `__version__` in `src/nemo_cli/__init__.py` to match.
  4. After the squash merge to `main`, the merge commit is tagged as `vX.Y.Z`
     and the tag is pushed: `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`.
  5. Optionally a GitHub release is created mirroring the changelog entry.

- **Source of truth for the version string is `pyproject.toml`.** The
  `nemo_cli.__version__` constant must be updated in the same release PR.
  Verify with `python -c "import nemo_cli; print(nemo_cli.__version__)"`
  after building.

- **Changelog is updated *during* feature PRs, not at release time.** Every
  PR that changes the surface or fixes a bug adds entries to
  `## [Unreleased]`. The release PR is then mostly mechanical.

## Alternatives Considered

- **CalVer (e.g. `2026.05.0`).** Useful when releases happen on a regular
  schedule rather than by feature. We ship by feature, and breaking changes
  matter more than dates. Rejected.
- **No formal scheme — tag whenever.** Cheap now, painful later when a
  consumer (or our own future agent integration) pins to a specific surface.
  Rejected.
- **Conventional Commits + auto-generated changelog
  (e.g. `release-please`, `semantic-release`).** More automation but requires
  tooling we don't have yet, and our commit history is small enough that
  manual curation is faster than wiring the pipeline. Reconsider in a
  follow-up ADR if releases become frequent (>1/month).

## Consequences

- Every PR that touches surface or fixes a bug adds a line to
  `## [Unreleased]`. Small overhead per PR; large benefit at release time.
- The first release on TestPyPI is **`v0.0.1`**, capturing the current
  state of `main`. The `0.0.x` range is the public signal that the
  surface is experimental; downstream consumers should pin exact
  versions rather than ranges until we cut `0.1.0`. The timing of each
  cut is **user-signaled**, not automatic on PR merge — until the user
  requests it, entries continue to accumulate under `## [Unreleased]`
  in `CHANGELOG.md`.
- Future agent / SDK consumers have a stable promise: a `nemo-cli >= a, < b`
  pin actually means something.
- Release PRs are tiny and mechanical; no surprise behaviour.
