# Agent: architecture reviewer

**Charter.** Surface architectural friction as **deepening opportunities** —
refactors that turn shallow modules into deep ones. Use the vocabulary in
`GLOSSARY.md` and `skills/improve-codebase-architecture.md` exactly: module,
interface, depth, seam, adapter, leverage, locality. Apply the deletion test.

**Inputs.** Hot-spot history, `GLOSSARY.md`, ADR-0001…0004, the frozen
behaviour golden.

**Deliverable.** `docs/architecture-review.html` (self-contained, inline SVG,
before/after cards, Top recommendation), a grilling loop recorded in
`skills/grilling.md`, and the refactor itself.

**Hard constraint.** **No function of the program may change.**
`scripts/equivalence.py --record` must run *before* the refactor; `--check`
must pass byte-for-byte afterwards. ADR-0004 is not re-litigated.

**Result.** `runner.py` was shallow: it mixed pure composition, filesystem
copying and process control. Extracted `composition.py` (pure), `workspace.py`
and `process.py` (two adapters → a real seam), and `ports.py` (the Observer
interface as the test surface). `runner.py` is now a thin orchestrator.

**Acceptance gate.** EQUIVALENCE OK, 58 tests green, 12/12 audit PASS.
