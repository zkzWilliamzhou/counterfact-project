# Culprit Should Be Built as an Experiment-Backed CLI, Not as a Star-Count Bet

## Executive assessment: the technical idea is credible, but a 105,000-star outcome is not forecastable

**Culprit should be built only as a narrowly scoped, evidence-first CLI, not as a bet on reaching 105,000 GitHub stars within 90 days.** The core mechanism is credible: delta debugging already has a long theoretical and empirical foundation for narrowing failure-inducing circumstances through repeated tests [3][4]. Prior tools capture, compare, diagnose, record, or replay environment state, but none establishes a minimal causal set through controlled interventions. That gap is the strongest reason to build a first version.

The commercial and popularity case is much weaker. The highest-traffic projects in the supplied ecosystem are agent-skill repositories, not environment-debugging CLIs. Star counts are an attention proxy, not a reliable predictor of installs, repeated usage, revenue, or engineering value. A star target is therefore not a valid product requirement. Culprit should be evaluated against falsifiable quality and adoption gates instead.

The decisive constraint is causal honesty. Delta debugging can establish a 1-minimal failure-inducing configuration under a supplied test oracle; it cannot prove a unique global root cause or identify latent code defects [3][4]. The marketing claim must therefore be that culprit finds “the smallest tested environment configuration that flips the supplied command between the supplied outcomes,” never that it identifies “the root cause.”

The proposed 90-day program should be treated as a research and distribution experiment. Proceed only if real, independently created failures produce reproducible results at acceptable cost, users can explain the output, and at least one external engineering team runs culprit on a recurring problem. If the tool cannot satisfy those conditions, the correct outcome is a documented negative result—not a pivot into generic AI diagnosis, automatic remediation, or a broader agent platform.

## 1. Culprit’s only durable edge is intervention, not another environment comparison

**Culprit must be sold as the CLI that tests whether changing an environment factor changes the command outcome.** Every existing project in the supplied ecosystem observes, compares, ranks, records, replays, reproduces, contracts, or verifies. None is documented as deliberately intervening on a minimal set of environment differences and rerunning the supplied command to check whether the outcome flips.

The distinctions are substantive rather than cosmetic:

| Project | Documented mechanism | What it does not do |
|---|---|---|
| EnvFixer | Heuristically ranks environment differences and proposes fixes | Treats the oracle as authoritative; cannot establish that an intervention changes the outcome [6] |
| envdiff | Captures environment snapshots and ranks differences | Compares states but does not run counterfactual experiments [5] |
| DevRepro Doctor | Performs language-agnostic diagnosis and conformance checks | Remains primarily diagnostic rather than intervention-based [7] |
| Tracebox | Records command evidence and diffs two traces | Records and compares traces without performing delta debugging [8] |
| ci-debugging skill | Provides a checklist and human-led hypothesis process | Delegates execution and confirmation to a person [9] |
| ReproZip | Traces an experiment and packs it for reproduction | Preserves provenance and dependencies but does not shrink the causal configuration [10] |
| Drifti | Observes agent capabilities and checks them against a contract | Detects contract drift; it is not a sandbox or causal search engine [11] |
| dynobox | Unpacks, modifies, re-signs, and repacks Android firmware | Is unrelated to command-level environment causality [12] |

**The differentiator is intervention under a user-supplied oracle.** Given a command that passes in one captured environment and fails in another, culprit should:

1. build a structured candidate configuration from observable environment deltas;
2. intervene on subsets of those deltas in an isolated runner;
3. rerun the supplied command; and
4. return the smallest tested set whose removal or restoration changes the outcome.

This is materially stronger than a heuristic ordering of differences. A ranked diff can say that a Node version or environment variable *looks suspicious*. A counterfactual experiment can show that restoring one environment variable or toolchain version changes a passing run into the observed failure. The former is a hypothesis; the latter is testable evidence.

**The scientific edge also creates the main scientific limitation.** Controlled experiments can demonstrate that a particular intervention is sufficient to flip the supplied command under the supplied oracle. They cannot prove that the discovered configuration is the only cause, the global minimum, or the underlying code defect. Confounding from partial state replacement is a known delta-debugging problem: replacing selected state can induce behavior absent from both original executions [4].

Culprit should therefore report results as a **causal claim with explicit scope**, such as:

> Under these runner conditions, this intervention set, and this outcome definition, the command’s outcome flipped in N of M repeats.

It should not present the output as “the answer.” The best result is an auditable, testable explanation—not a universal root-cause certificate.

### The falsifiable claim must be narrow enough to survive contact with real failures

**Culprit’s primary claim is testable: in a documented corpus of planted, single-factor environment failures, it should recover the planted factor at least 90% of the time, with 95% of successful searches completing in 50 or fewer command executions.** “At least 90%” is intentionally conservative: it accommodates oracle noise, environmental leakage, and search failure. A 100% claim would be technically indefensible.

A second falsifiable claim should govern reproducibility: **for recovered factors, the same intervention should reproduce the original pass/fail flip in at least 19 of 20 independent repeats when the oracle is deterministic and the runner is held constant.** Both claims must be published with confidence intervals, failures, wall-clock cost, and raw logs. Marketing language should never be allowed to outrun this evidence.

These thresholds are a launch hypothesis, not an industry benchmark. They are justified by the need to prove two separate properties: search validity and experimental stability. If the tool misses more than 10% of planted causes or cannot reproduce its conclusion 95% of the time, its core value proposition has failed and should not be rescued through looser wording.

## 2. A zero-config CLI cannot credibly promise 105,000 stars, and the available comparisons do not support that target

**No public evidence can guarantee that culprit, or any other CLI, will reach 105,000 GitHub stars.** Stars are influenced by distribution, network effects, platform visibility, timing, novelty, emotional shareability, community activity, and external promotion. They are not generated by code quality alone. GitHub itself describes stars as a way to save repositories for later, not as a metric of quality, correctness, production readiness, or economic value. A star count is therefore an outcome signal, not a forecastable engineering deliverable.

The supplied star counts for obra/superpowers, mattpocock/skills, affaan-m/ECC, and anthropics/skills are striking, but they do not transfer to culprit. Those repositories are primarily **agent-skill collections and workflow references**. Their audience includes casual GitHub visitors, AI-tooling enthusiasts, people browsing curated methodology lists, and users seeking reusable agent behaviors.

Culprit, by contrast, targets engineers who already have a command that can be made to pass and fail, an accessible runner, and a meaningful oracle. Its value is concentrated, high intent, and operationally narrow. A skills collection can attract interest by promising better agent behavior. A CLI must first prove that it can safely execute a user’s command, return a meaningful result, and justify its compute cost.

The implication is structural: skills repositories scale through shareable ideas; culprit scales only through trusted execution and repeated usefulness. Those are different adoption curves.

**A realistic goal is an evidence-backed wedge, not a viral total.** Within 90 days, a credible public experiment should aim for:

- a small but real weekly active user base;
- adoption by at least three independent engineering teams;
- a demonstrated recovery rate on public, independently created fixtures;
- a reproducible demo that turns an unexplained failure into a named intervention; and
- clear, auditable result artifacts.

A star total can be tracked as a trailing curiosity, but it must not become a steering metric. Optimizing for stars would encourage spectacle, overbroad positioning, and unsafe default behavior. Optimizing for reproducible causality would push the product toward conservative execution, transparent scope, and measurable reliability.

### Five conditions must align before a breakout outcome becomes plausible

**Zero setup must mean zero configuration for the intended failure class, not zero configuration for every system.** A credible first-run path is:

```bash
culprit run --pass "command" --fail "command"
```

Culprit can infer an oracle from exit code by default, but only after warning the user that this may conflate the target failure with any other failure. For richer cases, the CLI should accept a check command, output assertion, or recorded failure fingerprint.

The demo must work on macOS and Linux without Docker, containerd, or kernel features in the common case. It should clearly state when isolation requires a container, VM, or other elevated mechanism. “Zero config” cannot mean “runs the user’s command with their full shell authority and network access.”

**The first demo must convert doubt into understanding within 30 seconds.** The ideal demonstration is not a wall of JSON. It is:

```text
PASSING baseline
  └─ apply N environment changes
FAILURE appears

Culprit tested M configurations in T seconds.
Smallest tested causal set:
  1. NODE_VERSION = 18.19.0  → restore to 20.10.0
  2. FOO_TIMEOUT = 500       → remove or restore

Replication: 19/20 repeats produced the original failure.
This is a 1-minimal set under the supplied oracle, not a proof of unique cause.
```

The technical result must be visible before the marketing explanation. A memorable demo shows the unknown becoming knowable; it does not merely assert that the tool is clever.

**Distribution must place culprit exactly where the failing command already runs.** The initial release channels should be pip or uv for Python environments, Homebrew for macOS and Linux users who prefer a native package, standalone signed binaries for users who do not want a language runtime, and a GitHub Action for CI. pre-commit should be added only if culprit can inspect a pre-commit hook failure without mutating the staged tree.

The product boundary must remain a CLI and a machine-readable event format. The GitHub Action should call the same binary used locally, not a separate cloud service. If a GitHub App or bot is introduced, it should post a report and links, never modify a repository without a separate human review step.

**Timing must exploit an operational pain point that users can reproduce today.** The most favorable wedge is not general AI debugging. It is a concrete recurring class of failures: local versus CI, lockfile versus runtime, Node or Python version drift, timezone or locale, feature flags, environment variables, or PATH and toolchain drift.

The product should not claim to solve “all flaky tests” or “all agent failures.” A narrow promise can be tested and trusted. A universal promise invites counterexamples immediately.

**A star breakout would require a second engine beyond the technology.** The technology can create a memorable demo, but a 100,000-star-level result also requires:

- a clear name and narrative;
- a low-risk installation path;
- a high-retention community;
- a compelling README;
- creator amplification;
- platform visibility;
- at least one infrastructure partner or distribution channel; and
- repeated public evidence that the tool saves time.

No amount of delta-debugging theory can substitute for that social and distribution machinery. If the 105,000-star target remains fixed, it should be treated as an arbitrary aspiration rather than a project requirement.

## 3. The top 12 failure modes all point toward one conclusion: defaults must be narrow, explicit, and opt-in

**The largest product risk is not that the algorithm fails in theory. It is that users interpret a narrow experimental result as a universal diagnosis and act on it unsafely.** Every failure mode therefore needs an explicit mitigation that changes the default behavior rather than merely improving the documentation.

| # | Failure mode | Why it would destroy trust | Concrete mitigation |
|---|---|---|---|
| 1 | Flaky command creates false causality | A chance pass can prune the real cause or preserve a spurious one | Use a configurable Bernoulli or sequential test; retain unresolved outcomes; require a stability baseline before searching; label all results as probabilistic |
| 2 | Repeated execution consumes too much CI time | A search that triggers dozens or hundreds of test runs may cost more than manual debugging | Cap runs, time, and concurrency; cache and reuse configurations; estimate cost before searching; offer a dry-run plan |
| 3 | Running unknown commands is dangerous | The tool must execute user-supplied commands, which may destroy data, deploy artifacts, or exfiltrate secrets | Never execute in the host shell by default; require a disposable runner; block network and secrets unless explicitly allowed; print every command and diff |
| 4 | The audience is too small | Culprit needs a reproducible command, an accessible runner, and a meaningful oracle—conditions absent from many debugging sessions | Target local versus CI, container builds, and test environments first; provide read-only simulation and a static diff mode for unsupported cases |
| 5 | False positives look authoritative | A 1-minimal configuration may be an interaction effect rather than the production defect | Label findings as “tested causal set,” show repeat counts and counterfactuals, distinguish causes from correlates, and identify confounding warnings |
| 6 | CI minutes erase the value | If the search costs more than the saved investigation, teams will disable it | Add budget controls, parallelism, early termination, a local-first mode, and a public cost dashboard |
| 7 | The oracle mistakes any failure for the target failure | A crash, timeout, or missing dependency may be misclassified as the original bug | Fingerprint stderr or output predicates, allow a user-supplied check command, and treat different failure classes as unresolved |
| 8 | Cross-platform semantics differ | The same command can rely on shell, path, locale, kernel, or package semantics unavailable in the runner | Record a platform and tooling manifest; require a matching runner by default; warn when probes are unavailable rather than fabricating values |
| 9 | Secret or private state leaks | Snapshots and logs may contain tokens, keys, internal paths, or proprietary data | Mask known secret patterns, exclude files and shell history, allow deny and allow lists, support local-only operation, and provide a redaction preview |
| 10 | Reproducibility still fails after a diagnosis | A named environment difference may not recreate the failure when a human reapplies it | Make the final intervention set directly executable or exportable, rerun it independently, and report the replication rate |
| 11 | A minimal set hides an interaction | Removing one factor may appear irrelevant until another factor is restored | Use 1-minimality as a starting point; optionally test two-way interactions when the budget allows; disclose when interaction search is incomplete |
| 12 | Users expect automatic repair | A diagnosis tool that silently mutates the environment becomes a liability and creates support drag | Keep diagnosis and repair as separate binaries; require explicit plans, dry runs, isolated application, rollback, and human confirmation for any change |

**The mitigations reinforce a single product philosophy: every powerful behavior must be visible, reversible, and opt-in.** The CLI should refuse to “help” when it lacks a safe and meaningful oracle. A dangerous but enthusiastic tool produces fewer stars over time than a conservative tool that explains exactly what it can and cannot prove.

## 4. Positioning must promise a testable explanation, not autonomous debugging

**The correct positioning is an experimental environment debugger, not an autonomous root-cause engine.** The core value proposition is that culprit turns a frustrating binary—“it works on my machine”—into an intervention experiment that either produces evidence or honestly reports that no tested intervention is sufficient.

### Positioning statement

> Culprit is a local-first CLI for engineers who already have a command that passes in one environment and fails in another. It enumerates the differences that matter, tests them in an isolated runner, and returns the smallest environment configuration that flips the supplied outcome. It proves the intervention, not the code change.

This statement is deliberately narrower than “AI debugging” or “automated root cause analysis.” It identifies the user, the precondition, the mechanism, and the epistemic boundary in one sentence.

### README hook

```text
culprit — test what actually breaks your command.

Most tools rank environment differences.
culprit runs controlled experiments to find the smallest
environment change that flips a passing command into your
exact failure.

  culprit run --pass "npm test" --fail "npm test" --runner ./ci-shell.sh

  ✓ Smallest tested causal set: NODE_VERSION, FOO_TIMEOUT
  ✓ Replicated 19/20 times in a disposable runner
  ✗ Not a proof that this is the only cause

Local-first. Explicit commands. Auditable experiments.
```

The hook leads with action and ends with the limitation. That ordering builds credibility instead of inviting users to discover the boundary only after a bad result.

### Demo scenario

A maintainer reports that `npm test` passes locally but fails in CI with a timeout. Locally, Node is 20.10.0 and `FOO_TIMEOUT` is unset. In CI, Node is 18.19.0 and `FOO_TIMEOUT` is 500.

`culprit capture` records both baselines and generates a structured diff. `culprit plan` proposes five tests, including:

- baseline-only runs;
- a single Node downgrade;
- setting `FOO_TIMEOUT=500`; and
- both interventions together.

After the runs complete, culprit reports that the interaction of the Node downgrade and `FOO_TIMEOUT=500` flipped the command in 19 of 20 repeats, while neither factor reproduced the failure alone.

The output must show:

- the number of experiments;
- the wall-clock cost;
- the oracle definition;
- the exact environment deltas;
- the replication rate; and
- the scope boundary.

The conclusion should be framed as a testable hypothesis: “Restore Node 20.10.0 and unset `FOO_TIMEOUT` in CI, then rerun the original command.” It should not declare that the code is correct.

### Distribution plan

**Distribution must serve trust and velocity simultaneously.** Each channel should solve a specific user problem rather than being adopted merely because it exists.

| Channel | Purpose | First release requirement |
|---|---|---|
| pip and uv | Lowest friction for Python users | Publish signed, reproducible wheels; verify a clean install from a fresh environment |
| Homebrew | Native installation on macOS and Linux | Maintain a versioned formula with SHA-256 checks and an automated release test |
| GitHub Releases | Cross-platform binaries without a language runtime | Build Linux x86_64 and ARM64, macOS ARM64, and Windows x64; sign or attest each artifact |
| GitHub Action | CI integration and social distribution | Keep the Action a thin wrapper around a pinned binary; support read-only and disposable-runner modes |
| pre-commit | Diagnose hook failures without modifying staged files | Implement only after an audit proves no staged-file mutation |
| MCP server | Optional agent integration | Remain read-only initially; never grant shell execution or repository-write authority |

Every release should produce provenance, a software bill of materials, signed or checksummed artifacts, and a test that installs the published artifact on a clean machine. Supply-chain controls must be treated as part of the product, not as infrastructure overhead.

## 5. The 90-day plan should kill weak hypotheses early rather than accumulate growth theater

**The plan must be organized around three decision points: technical validity, execution safety, and real adoption.** A single star total cannot distinguish progress from popularity. Each gate must be measurable and independent.

| Phase | Dates | Deliverables | Go gate | No-go consequence |
|---|---|---|---|---|
| 0: Scope and guardrails | Days 1–14 | Threat model, captured environment schema, oracle contract, read-only harness, 10 planted fixtures | At least 8/10 fixtures run safely in a sandbox without secrets or host writes | Redefine the supported failure class; do not proceed with autonomous execution |
| 1: Technical proof | Days 15–35 | Deterministic delta search, repeat handling, cost estimator, JSON and Markdown reports, public replayable fixtures | Recover the planted factor in ≥90% of planted cases; 95% of successful searches use ≤50 runs | Publish the failure analysis; stop positioning the tool as causal |
| 2: Distribution and first users | Days 36–60 | pip or uv build, Homebrew formula, signed binaries, GitHub Action, one integration test, three design partners | Three independent teams run culprit on a real failure; at least two produce a useful report | Narrow to read-only diagnostics or pause until a viable runner exists |
| 3: Evidence-led growth | Days 61–90 | Blog posts, recorded demo, benchmarks, security audit, contributor guide, versioned corpus | At least 50% of surveyed users understand the scope limitation; a published corpus reaches ≥80% recovery | Do not generalize the claim or invest in growth marketing |
| 4: Go/no-go review | Day 90 | Public evaluation, incident or limitation log, adoption and cost data, security assessment | ≥80% recovery on a frozen, independently authored corpus; ≥2 external teams use culprit weekly; ≥90% of result reports include successful replications; no critical unmitigated safety defect | Kill broad distribution, retain the codebase as a research artifact, or limit it to a read-only diagnostic |

### Go/no-go gates must remain independent

**A recovery-rate failure cannot be rescued by strong distribution.** A distribution failure cannot be obscured by impressive technical benchmarks. Each gate must be evaluated on its own evidence.

- **Validity gate:** recovery rate, reproducibility, false-positive behavior, and search cost.
- **Safety gate:** runner isolation, secret handling, command logging, privilege boundaries, and vulnerability findings.
- **Adoption gate:** external teams, recurring usage, comprehensibility, and time-to-first-result.
- **Operational gate:** packaging, installation, provenance, and multi-platform release quality.

No social-media success should override a failed validity gate. Conversely, excellent benchmarks cannot compensate for a product that nobody can install or trust.

## 6. Culprit should not be built if it cannot outperform a static diff at a defensible cost

**The strongest argument against culprit is not that delta debugging is invalid. It is that controlled experiments may not justify their expense for the available problem space.** Most environment failures are already diagnosed by comparing a few obvious differences: runtime versions, environment variables, PATH entries, package manifests, or CI and local configurations.

If culprit requires dozens of command executions, an isolated runner, and a carefully constructed oracle to rediscover what a short diff already shows, it is a more expensive way to reach the same conclusion. A static diff has near-zero runtime cost and is easy to understand. Culprit must demonstrate a category of failures where intervention materially improves the answer.

**The second argument is safety.** Unlike read-only diff tools, culprit must execute commands. Even with safeguards, it becomes part of the user’s execution trust boundary. That responsibility increases maintenance burden, support risk, supply-chain obligations, and enterprise friction. If the execution surface is necessary for the claimed benefit, the safeguards must be demonstrably proportionate.

The relevant question is not whether full isolation is possible in some configurations. It is whether a broad user base will use the tool safely by default.

**The third argument is problem scarcity.** A generic code-debugging CLI may attract a large audience, but culprit’s causal claim requires a reproducible command and a meaningful oracle. Many failures do not satisfy those conditions. Without a sufficient population of tractable failures, the project may become a technically interesting demo with little recurring usage.

**The fourth argument is attribution inflation.** Delta debugging identifies conditions associated with a tested outcome. Engineers still have to determine whether those conditions reflect an environment defect, a code defect, an interaction, or a test-design problem. If culprit presents an intervention as “the root cause,” users may apply changes that silence a symptom rather than fix a design weakness. This risk is acute for flaky tests, where masking the failure can make the underlying problem harder to detect.

**The fifth argument is competitive overlap.** EnvFixer already ranks environment differences. envdiff already compares snapshots. DevRepro Doctor already performs diagnostics. Tracebox already captures and compares run traces. A new project that merely improves their ranking or visualization will look like duplication. The only justified differentiator is controlled counterfactual search, and that claim must be demonstrated repeatedly.

### The evidence that would change this verdict

| Argument against | Evidence required to proceed |
|---|---|
| Controlled experiments are not worth the cost | A public study showing that intervention changes the actionable diagnosis in at least 50% of independently authored cases where a static diff left material ambiguity |
| The tool is too dangerous to execute commands | A reproducible isolation harness with independently audited guarantees, no critical findings, and a documented failure-open policy |
| The addressable audience is too narrow | Three unrelated organizations reporting weekly use for at least four consecutive weeks, with at least two different supported failure classes |
| The claim is scientifically overstated | A frozen corpus and protocol demonstrating at least 80% recovery, plus explicit counterexamples where culprit correctly reports ambiguity |
| The project duplicates existing tools | Before-and-after cases showing that culprit changes the action taken, not merely the presentation of the same information |
| It cannot operate without expensive infrastructure | A low-friction local mode that supports the majority of demonstrated use cases without containers, virtual machines, or privileged runners |

The negative case remains strong until these conditions are met. The correct decision is therefore not to commit to a star target, but to run a 90-day causal and safety experiment and let the evidence decide whether the product should expand, narrow, or stop.

## 7. The final recommendation is conditional: build the experiment, but do not manufacture a category

**Culprit should be built only as a conservative, evidence-first CLI.** Its strongest differentiator is real: it tests whether changing an environment factor changes the command outcome, while the supplied prior art primarily observes, compares, ranks, diagnoses, records, reproduces, or contracts. That is a meaningful technical position.

The necessary product response is equally clear. Culprit must be explicit about its 1-minimal causal scope, probabilistic outcomes, interaction limitations, and experimental cost. It must refuse unsafe defaults and make every command visible before execution.

A 105,000-star target should be removed from the decision framework. The comparable skills repositories are not evidence that a narrowly scoped CLI can attract the same attention. Star counts are not forecastable, and the conditions required for a breakout are largely outside the engineering team’s control.

The best version of culprit would be a trusted experimental debugger that changes how engineers resolve environment-dependent command failures. If it cannot demonstrate that benefit under controlled gates, the most valuable result will be an honest explanation of why the approach did not generalize.

## Source excerpts

[1] https://pypi.org/project/culprit
> "Root-cause analysis for a PR or branch: classify feature vs bugfix, find the introducing commit (suspect set) or the blast radius."

[2] https://juejin.cn/post/7697952294365380662
> "The same run also exposed a redaction leak in my own report, which is fixed."

[3] https://www.st.cs.uni-saarland.de/publications/files/zeller-ieee-2001.pdf
> "The trade-off is that, unlike conventional debugging, Delta Debugging always produces a set of relevant failure-inducing circumstances."

[4] https://www.cs.umd.edu/~atif/zeller.pdf
> "Partial state replacement can induce new behavior that was not present in either of the original executions."

[5] https://github.com/GBerghoff/envdiff
> "envdiff takes a snapshot of both environments, diffs them, and tells you the most likely culprit first."

[6] https://devfolio.co/projects/envdiff-32bd
> "If an AI is going to automatically fix a developer’s environment, it absolutely cannot break their machine in the process."

[7] https://github.com/webdevsamran/devrepro-doctor
> "Does DevRepro Doctor change anything on my machine? No, not without an explicit per-action confirmation."

[8] https://github.com/peccatos/tracebox
> "Tracebox captures a command and its evidence."

[9] https://skills.cat/skills/bdfinst/agentic-dev-team/ci-debugging
> "Never push a speculative fix without reproducing locally first."

[10] https://reprozip.readthedocs.io/en/stable/packing.html
> "You should not change any file that the experiment used before packing it."

[11] https://users.rust-lang.org/t/drifti-v0-1-capability-drift-detection-for-ai-agents-built-in-rust/143441
> "Drifti does not attempt to provide process isolation."

[12] https://github.com/limzei89/dynobox
> "DynoBox is a cross-platform toolkit for unpacking, modifying, re-signing, and repacking Android firmware and OTA packages."

[13] https://dev.to/zaydmulani09/i-built-a-tool-that-finds-the-minimal-cause-of-a-browser-bug-by-replaying-it-3odg
> "The report is a single offline HTML file with a causal graph."

[14] https://buildwithaitoday.com/wiki/delta-debugging
> "The ddmin algorithm keeps a granularity n, starting at 2."

[15] https://sekin.in/how-to-find-the-minimal-cause-of-a-browser-bug-by-replaying-it
> "A 1-minimal result means that removing any one remaining element makes the failure disappear."

[16] https://www.reprozip.org/about.html
> "ReproZip works in two steps: tracing and packing."

[17] https://aiagentskills.net/skill/tjboudreaux-cc-thinking-skills-thinking-thought-experiment
> "Run a controlled counterfactual: isolate one variable, fix conditions, trace the mechanistic chain."

[18] https://virtuslab.com/blog/ai/sandboxing-llm-coding-agents-part1/
> "Most don’t isolate the network at all."

[19] https://aclig.dev/safety
> "An agent acts on inference and can be wrong or adversarially steered."

[20] https://dev.to/alexander_iwizard/no-run-command-how-do-you-prove-a-cli-will-not-execute-an-agent-5986
> "Refusal is a product feature."
