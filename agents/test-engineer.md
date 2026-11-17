# Agent: test engineer

**Charter.** Red before green. Tests assert the *contract*, not the current
implementation's quirks. Cover safety boundaries, parsing, state diffing,
oracle semantics, ddmin, verification, renderers, runner isolation, CLI exit
codes and adversarial inputs.

**Inputs.** The design and the threat model's attack table.

**Deliverable.** `tests/` (58 tests), `scripts/benchmark.py` with a planted
fixture corpus, `BENCHMARK.md`.

**Acceptance gate.** A failure must be fixed in the implementation, never by
loosening an assertion. Benchmark uses real child processes, not mocks, and
publishes failures and cost. Rejected if a test only checks that a function
was called.

**Result.** First run: 55 PASS / 3 FAIL. The three failures were real defects
(truncation detection, JSON secret leakage, cross-machine `PATH` validation)
and were fixed before promotion.
