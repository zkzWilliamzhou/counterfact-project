# Adoption: why the 105k-star target was deliberately demoted

The brief asked for a program that could get over 105,000 GitHub stars. That is
not an engineering deliverable and this repository does not pretend otherwise.
Stars are an attention proxy shaped by timing, distribution, platform
visibility, network effects and luck. GitHub itself describes stars as a way to
save repositories for later, not as a measure of quality or production
readiness. No repository can be engineered to guarantee a star count.

The full adversarial assessment, including the "why this should not be built"
section, is in
[`docs/research/adoption_grill_agent_report.md`](docs/research/adoption_grill_agent_report.md).

## What replaced the target

Falsifiable quality gates, measured in this repository:

| Gate | Threshold | Evidence |
| --- | --- | --- |
| Recovery on planted failures | >= 90% | [`BENCHMARK.md`](BENCHMARK.md): 100% (20/20) |
| Search cost | 95% of successful searches <= 50 executions | 100% (20/20), max 37, median 23 |
| Replication of a conclusion | anchors, necessity and stability all re-run | `counterfact/proof.py` |
| Safety | 12 review rounds with zero open findings | [`REVIEW.md`](REVIEW.md) |
| Behaviour preservation during refactor | byte-identical golden snapshot | [`EQUIVALENCE.md`](EQUIVALENCE.md) |

## The single sharpest differentiator

Existing tools observe, compare, rank, record, reproduce or verify.
counterfact **intervenes**: it changes a subset of the differences and re-runs
the command to see whether the outcome flips. A ranked diff says a Node version
"looks suspicious"; a counterfactual experiment shows that restoring that
version changes a passing run into the target failure.

**Falsifiable claim:** in a documented corpus of planted failures, recover the
planted set in >= 90% of cases, with 95% of successful searches completing in
<= 50 executions. Measured result: 100% / 100% on 20 deterministic cases.

## Top failure modes and mitigations

| # | Failure mode | Mitigation in this repo |
| --- | --- | --- |
| 1 | Flaky command creates false causality | Stability baseline, `FLAKY` status, never exits 0 |
| 2 | Repeated execution costs too much | `--max-runs`, `--max-total`, caching, plan shows an execution upper bound |
| 3 | Running unknown commands is dangerous | `--yes` opt-in, no shell, constructed env, fresh workspace, process groups |
| 4 | Narrow audience | Target local-vs-CI first; `compare` supports read-only cases |
| 5 | False positives look authoritative | Scope notice in every renderer; `PROBABLE` vs `CONFIRMED` |
| 6 | CI minutes exceed the value | Bounded budgets and median 23 executions on the benchmark |
| 7 | Oracle mistakes any failure for the target | `--expect-fail-text`; unmatched failures are `UNRESOLVED` |
| 8 | Cross-platform semantics differ | Metadata diffs produce explicit scope warnings, never replayed |
| 9 | Secret leakage | Allowlist capture, redaction in text/JSON/SARIF/GitHub renderers |
| 10 | Diagnosis does not reproduce | Independent sufficiency + necessity re-runs with cache disabled |
| 11 | Minimal set hides an interaction | Two-factor cases are in the benchmark; 1-minimality is stated, uniqueness is not claimed |
| 12 | Users expect automatic repair | Diagnosis and repair are separate; no mutation of the original tree |

## Positioning

> counterfact is a local-first CLI for engineers who already have a command
> that passes in one environment and fails in another. It enumerates the
> differences that matter, tests them in an isolated runner, and returns the
> smallest environment configuration that flips the supplied outcome. It
> proves the intervention, not the code change.

**Demo:** `counterfact demo` — five harmless differences, one real cause,
13 real experiments, 7/7 replication, `CONFIRMED` in under a second.

**Distribution:** `pyproject.toml` console script (pip/uv), a composite GitHub
Action skeleton in `action.yml`, CI in `.github/workflows/ci.yml`. Homebrew,
signed binaries, pre-commit and an MCP server are deliberately deferred behind
the adoption gate.

## 90-day go/no-go gates

| Phase | Gate | No-go consequence |
| --- | --- | --- |
| Days 1–14 | Threat model, schema, inert harness, planted fixtures | Redefine supported failure class |
| Days 15–35 | >= 90% recovery, 95% <= 50 runs, public fixtures | Publish the failure; stop claiming causality |
| Days 36–60 | Three external teams run it on a real failure | Narrow to read-only diagnostics |
| Days 61–90 | >= 80% recovery on an independently authored frozen corpus; >= 2 teams weekly | Do not generalise or invest in growth |

## Why this should not be built (strongest form, preserved)

1. A static diff is nearly free; controlled experiments cost dozens of command
   executions and may rediscover what a short diff already shows.
2. Executing arbitrary commands puts the tool inside the user's execution trust
   boundary; that raises maintenance, support and supply-chain burden.
3. The causal claim requires a reproducible command, an accessible runner and a
   meaningful oracle — conditions absent from many debugging sessions.
4. Delta debugging identifies conditions associated with an outcome, not the
   underlying defect; engineers can silence a symptom and hide a design flaw.
5. The adjacent space is crowded with competent tools.

**Evidence that would change the verdict:** a public study showing intervention
changes the actionable diagnosis in >= 50% of independently authored cases
where a static diff left material ambiguity; an independently audited isolation
harness; three unrelated organisations reporting weekly use for four weeks;
and a frozen corpus with >= 80% recovery plus explicit counterexamples where
the tool correctly reports ambiguity.

Until then, this repository is an evidence-first experiment, not a growth bet.
