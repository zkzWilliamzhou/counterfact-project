# Protocol: improve-codebase-architecture (adapted)

Source: `mattpocock/skills` → `skills/engineering/improve-codebase-architecture/SKILL.md`
Full vendored text: `skills/vendor/improve-codebase-architecture.SKILL.md`

## Vocabulary (used exactly, no drift)
**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**,
**locality**. Not "component", "service", "API", "boundary".

## Process as executed
1. **Explore / YAGNI scope.** We scoped to the recently changed, highest-churn
   module: `runner.py`. It mixed pure composition logic, filesystem adapters and
   process control in one shallow module.
2. **Read `GLOSSARY.md` and ADRs first.** ADR-0001 (no shell execution) and
   ADR-0002 (oracle scope) are not re-litigated.
3. **Deletion test.** Deleting the old `_compose` helper would merely move
   complexity; deleting the extracted `Composition` module would concentrate it.
   The latter is the signal to deepen.
4. **HTML report.** `docs/architecture-review.html` is a self-contained
   before/after visualisation with a Top recommendation section. (The upstream
   skill writes to the OS temp dir and opens it; we keep a copy in the repo so
   the deliverable is auditable. It uses inline SVG instead of CDN assets
   because the project is offline-only.)
5. **Grilling loop.** `skills/grilling.md`, applied to the chosen candidate:
   constraints, dependencies, module shape, what sits behind the seam, which
   tests survive.
6. **Domain model kept current.** New terms were added to `GLOSSARY.md`.

## Hard constraint from the operator
**No function of the program may change.** `scripts/equivalence.py --record`
freezes observable behaviour before the refactor; `--check` must pass after it.
`EQUIVALENCE.md` records the result.
