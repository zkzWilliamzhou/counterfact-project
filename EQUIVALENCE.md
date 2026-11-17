# Equivalence gate — "no function changed"

The operator required that the architecture improvement pass must not change
any function of the program. A refactor of the highest-churn module is exactly
where a silent behaviour change hides, so unit tests alone were not accepted
as evidence. ADR-0004 records the decision.

## Mechanism

`scripts/equivalence.py` runs a deterministic three-scenario corpus through the
**real** execution path (`counterfact.cli._flow`), with real child processes:

| Scenario | Expected observable behaviour |
| --- | --- |
| `single_factor` | one causal factor (`TZ`) among decoys → `CONFIRMED` |
| `two_factor_interaction` | `TZ` + `CI` jointly required → `CONFIRMED` with both |
| `no_reproduction` | failure signature never appears → `INCONCLUSIVE`, no factors |

The report object plus the inert plan are serialised into a normalised JSON
snapshot and compared byte-for-byte. Non-deterministic fields are normalised
rather than ignored: `duration_ms` is removed from each experiment, and the
absolute interpreter path in the command is replaced with `<PYTHON>`.
`tests/fixtures/golden_behaviour.json` is the frozen pre-refactor record.

```
python scripts/equivalence.py --record   # before the refactor
python scripts/equivalence.py --check    # after the refactor, and in CI
```

## Sequence

1. **Before the refactor** — golden recorded: `27,761 bytes`, three scenarios,
   full experiment logs, statuses, replication counts, warnings, oracle and
   scope notice included.
2. **Refactor landed** — `runner.py` split into `composition.py` (pure),
   `workspace.py` and `process.py` (two adapters), `ports.py` (Observer
   interface) and a thin `runner.py` orchestrator.
3. **After the refactor** — `--check` returned:
   `EQUIVALENCE OK: observable behaviour unchanged (27761 bytes)`.
4. **Regression suite** — 58 tests green; 12-round audit 12/12 PASS.

## What the gate does and does not prove

It proves that observable behaviour on the frozen corpus is unchanged. It does
not prove equivalence on untested inputs, and it does not replace the test
suite, the fuzz rounds or the benchmark. Any intentional behaviour change must
re-record the golden with a documented reason and a new test — see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

The gate runs in CI (`action.yml` / `.github/workflows/ci.yml`) and in review
round 8.
