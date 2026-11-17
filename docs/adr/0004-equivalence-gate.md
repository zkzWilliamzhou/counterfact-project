# ADR-0004: no function may change during an architecture refactor

**Status:** accepted (operator requirement).

## Context

The operator required "use improve-codebase-architecture skill but first make
sure you didn't change any function of the program's function". A structural
refactor of the hottest module (`runner.py`) is exactly the kind of change that
silently alters observable behaviour.

## Decision

`scripts/equivalence.py --record` freezes a normalised snapshot of observable
behaviour across a deterministic three-scenario corpus (single factor,
two-factor interaction, no reproduction) before the refactor. The refactor may
land only if `--check` returns byte-identical output. Unit tests alone are not
sufficient evidence. The gate is also run in CI and in review round 8.

## Consequences

- Non-deterministic fields (`duration_ms`, the absolute interpreter path) are
  normalised, not ignored silently.
- Any intentional behavioural change requires re-recording the golden with a
  documented reason and a new test.
- Result: [`EQUIVALENCE.md`](../../EQUIVALENCE.md).
