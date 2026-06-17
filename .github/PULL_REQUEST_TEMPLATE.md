<!-- Keep this template's sections — the `review-pr` skill (ADR-020) parses them. -->

## Summary

<!-- 1-3 sentences: what the PR changes and why. -->

## Linked issue

Closes #<!-- N -->

<!-- If no linked issue, replace this section with a justification.
     Most non-trivial work should track an issue per ADR-021. -->

## Acceptance criteria

<!-- Copy verbatim from the issue body. Tick boxes as items land. -->

- [ ] <!-- behavior -->
- [ ] <!-- tests -->
- [ ] <!-- documentation -->

## ADRs touched

<!-- ADRs this PR depends on, supersedes, or amends. If you introduced a new
     decision, link the new ADR file. If none, write "none". -->

- ADR-NNN

## Test plan

<!-- Concrete commands a reviewer can run. HTTP is respx-mocked; no real
     network or real credentials, ever (CONVENTIONS.md § Testing). -->

```bash
pytest
ruff check .
pyright
```

## Notes for the reviewer

<!-- Anything non-obvious in the diff, deferred follow-ups, captured response
     shapes for a new endpoint, etc. No AI-attribution footer in commits (ADR-022). -->
