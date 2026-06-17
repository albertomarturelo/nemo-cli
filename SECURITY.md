# Security Policy

## Supported versions

This project is pre-1.0 and single-maintainer. Only the **latest released
version** on PyPI (and `main`) receives security fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately via **GitHub Private Vulnerability Reporting**:
[Security → Report a vulnerability](https://github.com/albertomarturelo/nemo-cli/security/advisories/new).

If you can't use that, email **amarturelo@gmail.com** with `[nemo-cli security]`
in the subject.

You'll get an acknowledgement as soon as the maintainer can — this is a
best-effort, solo-maintained project, so please allow reasonable time.

### When you report, please

- Describe the issue and how to reproduce it.
- **Never include real credentials, bearer tokens, JWTs, session data, RUTs, or
  real portfolio amounts.** Redact or use synthetic values.

## Scope

In scope — issues in this project's own code:

- **Credential handling.** `NEMO_USERNAME` / `NEMO_PASSWORD` are read from the
  environment and never written to disk by this CLI.
- **The cached bearer token** stored as JSON under the OS user-config directory
  (e.g. `~/Library/Application Support/nemo-cli/token.json`) — leakage, weak
  permissions, or failure to clear on `nemo logout`.
- **The HTTP / auth layer** (`api_request`, the `SignIn` / `RefreshToken` flow):
  token handling, the 401-refresh path, header injection.

Out of scope:

- **The Vector Capital portal itself.** This project is **not affiliated with or
  endorsed by Vector Capital S.A. Corredores de Bolsa**; report portal issues to
  Vector directly.
- Rate-limiting or account locks imposed by the broker (expected behaviour, not a
  vulnerability in this tool).
