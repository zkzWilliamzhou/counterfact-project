# counterfact

**Don't rank environment differences. Run the experiment.**

`counterfact` finds the *smallest tested environment change* that flips a command
from passing to a specific failure — by running controlled counterfactual
experiments, not by diffing snapshots and guessing which line looks suspicious.

```text
$ counterfact demo

DEMO: 5 harmless differences, 1 real cause (TZ).

STATUS      : CONFIRMED
EXPERIMENTS : 13 logged (13 actual executions)
REPLICATION : 7 / 7 independent checks behaved as expected

Smallest tested causal set (1 factor(s)):
  - TZ     env   Asia/Shanghai  ->  UTC
```

> **Scope, up front:** this is a **1-minimal tested causal set** under the supplied
> oracle, runner and captured states. It is **not** proof of a unique root cause,
> **not** proof that your code is correct, and **not** valid outside these bounded
> conditions. A ranked diff is a hypothesis. `counterfact` produces evidence,
> and says "inconclusive" when it cannot.

---

## The gap

Every existing tool in this space **observes, compares, ranks, records or
reproduces**. None of them **intervenes on a minimal set of differences and
re-runs the command to see whether the outcome flips**.

| Tool | What it does | What it does not do |
| --- | --- | --- |
| `EnvFixer` | Heuristically ranks environment differences | Test whether an intervention changes the outcome |
| `envdiff` | Snapshots and compares two machines | Run counterfactual experiments |
| `DevRepro Doctor` | Read-only environment diagnostics | Intervene and re-run |
| `Tracebox` | Records and diffs two run traces | Minimise the causal configuration |
| `ReproZip` | Packs an experiment for reproduction | Shrink the difference set |
| `ci-debugging` skill | A human checklist | Execute and confirm |
| `falsegreen` / `FGD` | Detect green CI with missing evidence | Attribute an environment cause |

`counterfact` applies **delta debugging (ddmin)** to the *environment* rather
than to a test input, then independently re-runs the anchors and checks
necessity and stability before printing any conclusion.

## Install

```bash
pip install -e .          # or: python -m counterfact ... ; stdlib only, Python 3.9+
```

No dependencies. No network calls. No telemetry. No model in the loop.

## 60-second quick start

```bash
# 1. On the machine where it works
counterfact capture --out good.json

# 2. In CI / on the machine where it fails (copy the JSON back)
counterfact capture --out bad.json

# 3. READ-ONLY: see the differences. These are hypotheses, not causes.
counterfact compare --good good.json --bad bad.json

# 4. INERT: inspect exactly what would be executed. Nothing runs.
counterfact plan --good good.json --bad bad.json -- npm test

# 5. Only now, explicitly authorize controlled replay
counterfact run --good good.json --bad bad.json --yes \
  --expect-fail-text "ERR: timeout" -- npm test
```

`--expect-fail-text` is strongly recommended: without it, **any** non-zero exit
counts as the target failure. With it, a different crash or a timeout is
`UNRESOLVED`, never `FAIL`.

## What it actually does

1. **Capture** a structured, allowlisted, replayable state: locale/TZ, `PATH`,
   selected env keys, umask, and optional tool paths. Secrets are never
   captured by default.
2. **Diff** the two states into typed `Factor`s. Metadata (OS, Python version)
   is descriptive only and triggers a scope warning if it differs.
3. **Plan** (inert) an auditable experiment specification: exact argv, env
   deltas, budgets, oracle, redaction policy, and an upper bound on executions.
4. **Intervene** — only with `--yes`. Each experiment gets a fresh private
   workspace, a constructed environment, an argv list (never a shell),
   process-group termination, and wall/CPU/fsize/fd/output caps.
5. **Minimise** with ddmin to a 1-minimal set that still reproduces the failure.
6. **Verify** independently: sufficiency, stability of both anchors, and
   necessity of every member — with caching disabled so repeats are real.
7. **Report** in text, JSON, SARIF 2.1.0 or GitHub annotations, with secrets
   redacted and the scope limitation printed every time.

## Safety defaults

| Behaviour | Default |
| --- | --- |
| Execute the command | **Refused** — requires `--yes` |
| Shell interpretation | **Never** — argv list only |
| Inherit parent environment | **Never** — constructed baseline |
| Loader/interpreter vars (`LD_PRELOAD`, `PYTHONPATH`, `BASH_ENV`, …) | **Refused** |
| Snapshot → argv interpolation | **Impossible by design** |
| Untrusted config parsing | Bounded JSON; duplicate keys, depth, node and string limits; no YAML, no pickle, no user regex |
| Timeouts | Whole process group killed; timeout is `UNRESOLVED`, not `FAIL` |
| Output | Capped, ANSI-stripped, redacted |
| Flaky command | Reported as `FLAKY` / `INCONCLUSIVE`, never confirmed |

See [THREAT_MODEL.md](THREAT_MODEL.md) and [SECURITY.md](SECURITY.md).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | `CONFIRMED` or `PROBABLE` finding |
| 1 | Inconclusive, flaky, no reproduction, or budget exhausted |
| 2 | Usage or configuration error |
| 3 | Safety refusal (e.g. missing `--yes`) |
| 4 | Internal error |
| 130 | Interrupted |

## Prior art and honesty

Absolute novelty is not provable. Three earlier candidate ideas were **killed**
by prior-art search before this one was chosen (see [PLAN.md](PLAN.md)). For
this idea, the defensible claim is narrow: *no located tool performs active
causal minimisation over environment factors under a user-supplied oracle*.
A bounded search is not a proof of global novelty. See [PRIOR_ART.md](PRIOR_ART.md).

**On the 105,000-star target:** stars are not an engineering deliverable. They
depend on timing, distribution, network effects and luck. This project is
built against falsifiable quality gates (recovery rate on planted fixtures,
replication rate, safety gates), not against a star count. See
[ADOPTION.md](ADOPTION.md).

## Development

```bash
python -m unittest discover -s tests -v
python scripts/audit.py            # 8 review rounds, machine-checked
python scripts/equivalence.py      # behaviour-equivalence gate for refactors
```

## License

MIT
