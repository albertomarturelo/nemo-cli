---
description: Review a nemo-cli Pull Request against the project's curated checklist — sourced from the ADRs, CONVENTIONS.md, and any linked issue's acceptance criteria — instead of re-discovering intent from code. Use when the user asks to "review PR", "review this branch", "check my PR", or passes a PR number. Implements ADR-020.
---

Review a PR against the project's context (ADR-020), not by re-discovering its
intent from code. The agenda comes from the indices; read source to the depth
the checklist demands.

## 1. Identify the PR

The user passes a PR number. If not, infer from the current branch:

```bash
gh pr status --json number --jq '.currentBranch.number'
```

If still none, ask.

## 2. Fetch PR metadata + diff + commit story

```bash
gh pr view <n> --json baseRefName,headRefName,title,body,labels,commits,closingIssuesReferences
gh pr diff <n>
git log <base>..<head> --pretty=format:%s
```

## 3. Load the agenda

- `docs/CONVENTIONS.md`
- `docs/decisions/_index.md`, plus every ADR named in the PR body or a linked
  issue.
- The linked issue body via `gh issue view <issue-n>` if one exists (ADR-021):
  extract the acceptance-criteria checklist and the "ADRs to load" list.
- `.github/PULL_REQUEST_TEMPLATE.md` if present.

## 4. Read changed files to the depth the agenda demands

For nemo-cli this means **reading changed source files in full** — strict
`pyright` and the `api_request()` boundary rule require verifying call sites,
types, and that no handler or service calls `httpx` directly. This is
verification against known rules, not discovery.

## 5. Apply the checklist

### Workflow (ADR-005, ADR-014)

- Branch name follows `<type>/<slug>` (`feat`/`fix`/`docs`/`chore`/`refactor`/`test`).
- Base branch is `main`; merge will be a squash with a Conventional-Commits title.
- PR title is Conventional Commits and English.
- PR body references `Closes #<n>` when an issue exists (ADR-021).
- **No AI-attribution metadata** anywhere — no `Co-Authored-By:` trailer and no
  "Generated with …" line, in any commit or the PR body (ADR-022). Flag any that
  appear.

### HTTP boundary (ADR-003, critical rule)

- All Vector-portal HTTP goes through `api_request()` in
  `src/nemo_cli/api/client.py`. No `httpx.request(...)` in command handlers or
  services. Only allowed exception: `nemo_cli.auth.service.sign_in`.
- Endpoint paths passed to `api_request()` are relative (e.g. `/shared/...`).
- A new slow endpoint overrides `timeout=` at the service layer and adds a row
  to the Timeouts table in `CONVENTIONS.md` — the global default is unchanged.

### Conventions (CONVENTIONS.md)

- Only `nemo_cli.config` reads `os.environ`.
- Imports are absolute; new subcommand = one module exporting one verb function,
  registered in `cli.py`.
- Response shapes are typed at the call site (TypedDict/dataclass), not in a
  global types module.
- Errors: command handlers print a red one-line message to stderr and raise
  `typer.Exit(code=1)`; library code raises `RuntimeError`.
- A `--json` flag, when added, echoes the request scope + typed result.

### Types

- `pyright` strict passes; explicit return types on public functions; PEP-604
  unions (`str | None`); no `Any`.

### Testing (CONVENTIONS.md)

- HTTP mocked via `respx`; CLI tested via `CliRunner`; tests mirror the package
  tree; private helpers tested directly; coverage stays ≥ 95%.

### Decisions & docs drift

- Any new significant decision has an ADR in this PR (ADR-013); `_index.md`
  updated.
- A clarified convention is captured in `CONVENTIONS.md` (ADR-016).
- A user-facing change has a `CHANGELOG.md` entry (ADR-007).
- Each acceptance-criteria `[ ]` from the linked issue is implemented; no
  out-of-scope changes.

## 6. Output a structured review

```text
## Critical (must fix before merge)
- <file>:<line> — <issue> — citation: <ADR-N / CONVENTIONS line>. Suggested fix: <…>.

## Suggestions (should fix)
- <file>:<line> — <issue> — citation.

## Nits
- <file>:<line> — <issue>.

## Summary
- Overall assessment, AC coverage X/Y, architecture compliance ✓/⚠/✗.
```

## Rules

- **Do NOT auto-fix.** Report only; the author fixes next session.
- If the checklist needs a rule not yet in an ADR or `CONVENTIONS.md`, surface
  it as a finding ("missing convention for X") and propose `new-decision` — do
  not silently invent it.
