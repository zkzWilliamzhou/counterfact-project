# PLAN — counterfact

**Status:** design approved by operator opt-out (the original brief said "start
working until the work is done" and "you are the boss and manager"). The
brainstorming skill's human-approval gate is waived by that instruction; this
document is the written design in its place. See
[`skills/brainstorming.md`](skills/brainstorming.md).

---

## 1. Intent and the why

The brief asked for a program that (a) has a function that does not exist yet,
(b) genuinely makes a difference, and (c) could plausibly attract 105,000 GitHub
stars.

**Decision:** (c) is not an engineering requirement. Stars are an attention
proxy driven by timing, distribution and network effects; no code can cause
them. Treating a star count as a spec would push the design toward spectacle
and unsafe defaults. This plan replaces it with falsifiable quality gates
(recovery rate, replication rate, safety gates). Full argument:
[`ADOPTION.md`](ADOPTION.md).

The real intent is narrower and sharper: **find a category of developer pain
where existing tools only observe, and build the tool that intervenes.**

## 2. Goals, non-goals, anti-goals

**Goals**
- Given a command that passes in one captured state and fails in another,
  return the *smallest tested set* of environment differences whose application
  flips the outcome.
- Produce evidence (an experiment log with every observation), not a guess.
- Be safe enough to execute arbitrary developer commands on a workstation.
- Say "inconclusive" when the evidence does not support a claim.

**Non-goals**
- Fix the code. counterfact is a diagnosis tool, not an auto-repair tool.
- Prove a unique root cause, or that the underlying code is correct.
- Sandbox against a determined local attacker (that requires a container/VM).
- Replace link checkers, linters, schema validators or doctest runners.
- Support network-dependent, interactive, or non-reproducible failures.

**Anti-goals** (would count as failure even if it technically works)
- A confident "root cause found" printed from a flaky command.
- A ranked diff dressed up as an experiment.
- Any default that executes a command without explicit opt-in.
- Any report that leaks a token, or treats a timeout as the target failure.
- Marketing that outruns the measured recovery rate.

## 3. Constraints

| Constraint | Kind | Consequence |
| --- | --- | --- |
| `git clone` blocked in build environment | real | Skill repos fetched as HTTPS tarballs instead |
| No third-party runtime dependencies | chosen | stdlib only; bounded JSON, no YAML, no pickle |
| Must run offline | chosen | No network, no model in the loop |
| Arbitrary user command must be replayed repeatedly | real | Shell-free argv, constructed env, process groups, resource caps |
| Absolute novelty is unprovable | real | Claim is "no located tool", with search boundaries recorded |
| `culprit` name already taken on PyPI | located evidence | Renamed to `counterfact` |
| No function may change during architecture work | operator | Behaviour-equivalence golden gate before/after |

## 4. Approaches considered (independent round, before prior-art search)

Labels follow the brainstorming skill: **idea**, **assumption**, **prediction**,
**located evidence**, **decision**.

| ID | Idea | Why it looked promising | Verdict |
| --- | --- | --- | --- |
| A | Zero-config *claim verifier* for README / `AGENTS.md` / CI (`Verity`) | AI coding agents act on stale context files; docs rot silently | **KILLED by evidence** |
| B | *Side-effect receipt* / false-green detector: exit 0 but nothing happened | Silent no-ops are a real and scary failure mode | **KILLED by evidence** |
| C | *Environment snapshot diff + ranked diagnosis* | "works on my machine" is universal | **KILLED by evidence** |
| D | *Counterfactual environment debugger*: intervene on a minimal set of differences and re-run | All killed candidates observe; none intervenes | **SELECTED** |

### Kill A — documentation / claim drift
Located: `stale-cli`, `driftmd`, `docverity`, `@ctxlint/ctxlint`,
`agents-lint`, `agenteval-cli`, `codeconscience`, `conventions-cli`, `Alembic`,
`Sintesi`, and an existing npm package literally named `@pietro-falco/verity`
that already verifies declared claims offline against repository state.
The full survey is in [`PRIOR_ART.md`](PRIOR_ART.md) and
[`docs/research/prior_art_agent_report.md`](docs/research/prior_art_agent_report.md).
The defensible remaining gap was "automatic inference", not "verification" —
too narrow and too noisy for a first release.

### Kill B — side-effect receipts / false-green
Located: `falsegreen` (Python/JS/Robot Framework), `testrot`, False-Green
Detector (FGD), `Prove the Check Can Fail`, `dynobox`, `reelier`, `Drifti`,
`agentlie`, `provenance-recorder`, `Tracebox`, `Hawkeye`, `ProcDrift`,
`dsh-driftwatch`. The space is crowded and includes explicit "prove the check
can fail" protocols.

### Kill C — static environment diagnosis
Located: `EnvFixer` (ranks diffs heuristically), `envdiff` (snapshots + compare),
`DevRepro Doctor` (read-only diagnostics), `AIHostCheck`, `Tracebox` (trace
diff), the `ci-debugging` skill (human checklist), `ReproZip` (reproduction
packs). A new ranked diff would be duplication.

### Reopened ideation after the evidence check
**Idea:** every killed candidate shares one property — it *observes* a state
or a diff. None changes one factor at a time and re-runs the command under a
supplied oracle to see whether the outcome flips. Delta debugging (ddmin) is a
mature algorithm for minimising failure-inducing inputs; applying it to the
**environment** rather than to a test input is a small, real, testable shift.

**Prediction:** on a corpus of planted single- and two-factor failures, a
counterfactual search should recover the planted set at >= 90% with <= 50
command executions in 95% of successful searches. Falsified by
[`BENCHMARK.md`](BENCHMARK.md) if those gates fail.

**Assumption:** the failure predicate is reasonably monotone. Non-monotone
interactions are a known delta-debugging limitation and are disclosed.

**Decision:** build D, with the claim narrowed to "1-minimal tested causal set
under the supplied oracle, runner and captured states".

## 5. Decision matrix (defined before scoring)

Criteria and weights were fixed before any score was assigned: distinctness
from located prior art (0.30), practical value (0.25), verifiability of the
claim (0.20), safety feasibility (0.15), breadth of audience (0.10). Scores
1–5, higher is better.

| Criterion (weight) | A | B | C | D |
| --- | --- | --- | --- | --- |
| Distinctness (0.30) | 2 | 1 | 1 | 4 |
| Practical value (0.25) | 4 | 4 | 4 | 4 |
| Verifiability (0.20) | 3 | 3 | 2 | 5 |
| Safety feasibility (0.15) | 5 | 4 | 5 | 2 |
| Audience breadth (0.10) | 4 | 3 | 4 | 3 |
| **Weighted total** | **3.35** | **2.85** | **2.85** | **3.85** |

**Dissent (preserved, not averaged away):** the adversarial reviewer argued D
should not be built at all — a static diff is nearly free, while D repeatedly
executes arbitrary commands, has a narrower audience, and may cost more CI
time than it saves. That objection is reproduced in full in
[`docs/research/adoption_grill_agent_report.md`](docs/research/adoption_grill_agent_report.md).
It is not resolved by the score. It is mitigated by (i) an inert default,
(ii) hard budgets, (iii) an explicit "inconclusive" status, and (iv) a public
benchmark that can falsify the value claim. **Gate:** if intervention does not
outperform a static diff on independently authored cases, the project stops.

## 6. The design

**Pipeline:** `capture` → `compare` (read-only hypotheses) → `plan` (inert
specification) → `run --yes` (controlled intervention) → `minimise` (ddmin) →
`verify` (sufficiency, stability, necessity) → `report` (text / JSON / SARIF /
GitHub annotations).

**Core modules** (see [`GLOSSARY.md`](GLOSSARY.md) for vocabulary):
`safety` (bounded parsing, denylist, redaction), `state` (capture/diff),
`plan` (typed RunSpec + inert plan), `composition` (pure env/argv transform),
`workspace` + `process` (adapters), `runner` (thin orchestrator), `oracle`,
`minimize`, `proof`, `report`, `cli`.

**Oracle contract.** A zero exit is PASS; a non-zero exit is FAIL only if it
matches `--expect-fail-text`; everything else (timeout, launcher error,
unmatched crash) is UNRESOLVED. Anchors must hold before any search.

**Safety contract.** No shell, constructed environment, allowlist capture,
symlink-resistant paths, process-group termination, wall/CPU/fsize/fd/output
caps, secret redaction in every renderer, `--yes` required to execute.
Full reasoning: [`THREAT_MODEL.md`](THREAT_MODEL.md).

**Honesty contract.** Every renderer prints the scope notice. `FLAKY` and
`INCONCLUSIVE` never exit 0. The word "root cause" is not used as a claim.

## 7. What is left to the builder / next actions

- Independent, externally authored failure corpus (the current corpus is
  planted in-repo — a real limitation).
- A container/VM adapter for stronger isolation on untrusted commands.
- Published pip/Homebrew/signed binaries and a thin GitHub Action (a composite
  action skeleton is included).
- Three external teams using it weekly — the real adoption gate.

See [`WORKFLOW.md`](WORKFLOW.md) for the agent workflow and manager gates,
and [`REVIEW.md`](REVIEW.md) for the 12-round review log.
