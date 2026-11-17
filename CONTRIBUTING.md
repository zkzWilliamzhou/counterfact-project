# Contributing

## Before you start

Read [`PLAN.md`](PLAN.md), [`GLOSSARY.md`](GLOSSARY.md) and the ADRs in
[`docs/adr/`](docs/adr/0001-no-shell-execution.md). ADR-0001 (no shell),
ADR-0002 (scope of causal claims), ADR-0003 (allowlist capture) and ADR-0004
(equivalence gate) are settled decisions, not suggestions.

## Local loop

```bash
python -m unittest discover -s tests -v
python scripts/equivalence.py --check
python scripts/benchmark.py
python scripts/audit.py
```

All four must pass. The audit has 12 rounds; a REVISE verdict blocks a merge.
If you change observable behaviour, you must re-record the golden with
`python scripts/equivalence.py --record` and explain why in the PR.

## Rules

- **No new runtime dependencies.** stdlib only, offline by design.
- **No shell execution.** argv lists, `shell=False`, always.
- **No user-supplied regex, YAML or pickle.** Bounded JSON with schema
  validation, always.
- **Every emitted string is redacted and control-character free.**
- **A timeout is `UNRESOLVED`, never `FAIL`.**
- **A flaky command never yields `CONFIRMED`.**
- **Tests assert the contract.** Do not weaken an assertion to get green.
- **Prose follows** [`skills/stop-slop.md`](skills/stop-slop.md): no
  superlatives without a number, no fake certainty, no throat-clearing.

## Adding a new factor kind

1. Add the validator in `counterfact/safety.py`.
2. Add the kind to `factor_kind` and `validate_factor_name`.
3. Handle it in `counterfact/composition.py`.
4. Add round-trip, adversarial and end-to-end tests.
5. Re-record the golden only if observable behaviour intentionally changed.

## Reporting issues

Include `counterfact --version`, platform, the inert `plan` output, and a
minimal reproducer with secrets redacted. For vulnerabilities see
[`SECURITY.md`](SECURITY.md).
