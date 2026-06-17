# ADR-024: Repository Governance — Security Policy, Contribution Posture, Templates

## Status

Accepted

## Date

2026-06-16

## Context

As a public repository that handles a user's personal broker credentials,
nemo-cli lacked a security-reporting policy, contribution guidance, and
issue/PR templates. A researcher who found a vulnerability had no private
channel (only public issues — dangerous for a credential-handling tool), and
issues/PRs had no structure to feed the CFD work-unit flow (ADR-021) or the
context-based PR review (ADR-020). The sibling project `sii-cli` ships a
governance set; this ADR adopts it, adapted to nemo (MIT, no MCP server, Vector
Capital non-affiliation).

## Decision

Adopt a governance layer:

- **`SECURITY.md`** — report privately via GitHub Private Vulnerability
  Reporting (advisory URL) or email. In-scope = nemo's own code (env-var
  credential handling, the token cache, the `api_request`/auth layer);
  out-of-scope = the Vector Capital portal itself (non-affiliation). Reporters
  must never include real credentials or RUTs.
- **`CONTRIBUTING.md`** — bug reports, feature requests, and security reports are
  welcome; **external pull requests are not accepted** (a solo maintainer cannot
  certify outside code against the own-account, personal-use posture, and the
  CFD workflow is built around maintainer-authored work units). Forks are welcome
  under MIT.
- **`.github/PULL_REQUEST_TEMPLATE.md`** — the sections `review-pr` (ADR-020)
  expects: Summary, Linked issue, Acceptance criteria, ADRs touched, Test plan,
  Notes.
- **`.github/ISSUE_TEMPLATE/`** — `work-unit.md` (the ADR-021 fixed body, parsed
  by `issue-start`), `bug_report.md`, `feature_request.md`, and `config.yml`
  (blank issues disabled, security routed to the advisory page).

## Alternatives Considered

- **No governance files.** Leaves vulnerability reporters with only public issues
  and keeps issues/PRs unstructured, breaking the CFD skill integration.
  Rejected.
- **Accept external PRs.** A solo maintainer cannot review outside code against
  the broker terms-of-service / own-account posture, and the CFD flow assumes
  maintainer-authored units. Rejected — forks stay open under MIT.
- **Fold security into `CONTRIBUTING.md`.** A separate `SECURITY.md` is the
  GitHub convention and powers the "Report a vulnerability" UI. Rejected merging
  them.

## Consequences

- A private disclosure channel exists; the security posture and Vector
  non-affiliation are explicit and discoverable.
- Issues/PRs created from the templates feed the CFD skills directly
  (`work-unit` ↔ `issue-start`/`issue-new`, PR template ↔ `review-pr`).
- One-time manual follow-up: enable **Private Vulnerability Reporting** in repo
  settings so the advisory URL resolves.
- The no-external-PR stance is documented and easily reversed by a future ADR if
  collaboration ever scales.
