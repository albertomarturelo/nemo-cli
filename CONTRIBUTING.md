# Contributing to `nemo-cli`

Thanks for your interest. Please read this before opening an issue or forking.

## TL;DR — how this project takes contributions

`nemo-cli` is maintained by a single author and is a **personal, own-account**
tool: it talks to a broker portal under the user's own credentials, for their
own holdings. Because of that:

- ✅ **Bug reports, feature requests, and security reports are very welcome** —
  open an issue (or see [SECURITY.md](SECURITY.md) for vulnerabilities).
- ✅ **Forks are welcome** — the project is MIT-licensed; fork it and adapt it.
- ❌ **External pull requests are not accepted.** A solo maintainer cannot
  certify that outside code honours the own-account, personal-use posture, and
  the project's Context-First Development workflow is built around
  maintainer-authored work units (ADR-021) and context-based review (ADR-020).
  Recorded in [ADR-024](docs/decisions/024-repository-governance.md).

If you have a change you'd love to see, **open an issue describing it** — that is
the path that moves it forward.

## Reporting

- **Bug:** use the *Bug report* issue template.
- **Feature:** use the *Feature request* issue template.
- **Security vulnerability:** do **not** open a public issue — see
  [SECURITY.md](SECURITY.md).

> **Never paste real credentials, bearer tokens, JWTs, RUTs, or real portfolio
> amounts into an issue.** Use synthetic values — CI greps tracked files for
> known PII and blocks commits that leak it.

## Working on a fork

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest          # run the suite (no real network — respx-mocked)
ruff check .    # lint + import order
pyright         # strict type check
```

Conventions, architecture, and the decision log live in
[`docs/`](docs/); start from [`CLAUDE.md`](CLAUDE.md) and
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md). All model-facing context and code
are in English (ADR-014); commits carry no AI-attribution metadata (ADR-022).
