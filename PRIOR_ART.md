# Prior art and the novelty boundary

**Verdict:** no *located* tool performs active causal minimisation over
environment factors under a user-supplied oracle. That is a bounded-search
result, **not** a claim that the idea has never existed anywhere. Three earlier
candidate directions were killed by this search. The full survey with links is
in [`docs/research/prior_art_agent_report.md`](docs/research/prior_art_agent_report.md).

## Search boundaries

Four search rounds were run over GitHub, npm, PyPI and secondary indexes, with
queries covering: documentation drift, claim verification, `AGENTS.md` /
`CLAUDE.md` linting, convention mining, false-green / no-op detection, command
side-effect receipts, agent-run replay, environment snapshot diffing, and
causal/delta debugging. Some search results were secondary aggregators rather
than canonical repositories; repository URLs and star figures in the full
report are approximate captures, not audited measurements. Absence of a hit in
these rounds does not establish global novelty.

## Candidate A — documentation / claim drift (killed)

| Tool | Checks |
| --- | --- |
| `@pietro-falco/verity` | Explicit `file_exists` / `file_matches` / `git_committed` / `command` claims, offline, deterministic |
| `stale-cli` | Script drift, port drift, file-reference drift, dependency drift, git staleness, comment staleness |
| `driftmd` | Internal links, dir trees, badges, file refs, CLI flags, env vars, signatures |
| `docverity` | Reference checker, LLM prose claims, undocumented-flag coverage, MCP server |
| `@ctxlint/ctxlint` | Context-file lint: stale refs, dead commands, secrets, token bloat, SARIF, `slim` auto-fix |
| `agents-lint` / `agenteval-cli` | `AGENTS.md`/`CLAUDE.md` path and script validation, contradictions, token budget |
| `codeconscience` / `conventions-cli` / `Alembic` | Mine implicit conventions, export rules, source-anchored recipes |
| `Sintesi`, `SnakeMD` | Generate docs; drift check via AI/RAG |
| `lychee`, `markdown-link-check` | URL and mail-address liveness |
| `mdBook`, `rustdoc`, doctest, `embedme`, `actionlint`, `check-jsonschema`, `Taplo` | Executable examples, embedded-code sync, workflow/schema validation |

## Candidate B — side effects / false green (killed)

`falsegreen` (Python/pytest, JS/TS, Robot Framework), `testrot`, False-Green
Detector (FGD), `Prove the Check Can Fail`, `dynobox`, `reelier`, `Drifti`,
`agentlie`, `provenance-recorder`, `Tracebox`, `Hawkeye`, `ProcDrift`,
`dsh-driftwatch`, `Drifti`.

## Candidate C — environment diagnosis (killed)

| Tool | Mechanism | Missing piece |
| --- | --- | --- |
| `EnvFixer` | Compares two env snapshots, ranks likely causes | No intervention; treats oracle as authoritative |
| `envdiff` | Snapshot + ranked diff, secret masking | No counterfactual re-run |
| `DevRepro Doctor` | Read-only cross-platform diagnostics | Diagnostic, not experimental |
| `AIHostCheck` | Read-only host evidence JSON | No replay |
| `Tracebox` | Records and diffs run traces | Comparison, not minimisation |
| `ci-debugging` skill | Hypothesis-first human checklist | Delegates execution to a person |
| `ReproZip` | Packs an experiment for reproduction | Preserves provenance, does not shrink causes |
| `Qodo`, `Greptile`, `Unblocked`, `CodeRabbit` | Learn review conventions from PR history | Different problem space |

Also relevant: `lychee`, `Repomix`, `Gitingest`, `Semgrep`, `CodeQL`,
`dependency-cruiser`, `ArchUnit`, `import-linter` — each validates one artifact
or one policy, none correlates a *counterfactual intervention* with a supplied
outcome oracle.

## The defensible claim

> counterfact applies delta debugging to the **environment** and re-runs the
> command to find a 1-minimal tested causal set, under a supplied oracle,
> runner and captured states.

It does **not** claim: first tool to verify claims, first tool to detect
documentation drift, first tool to diff environments, first tool to use ddmin,
first tool to replay a command, or a unique root cause.

## Naming

`Verity` was rejected because `@pietro-falco/verity` and an MCP hallucination
checker already use it. `culprit` was rejected because a PyPI package already
uses that name. `counterfact` was chosen: it names the mechanism
(counterfactual intervention), not the ambition.

## Falsification

If a tool is located that performs the same intervention loop, the novelty
claim is withdrawn. If [`BENCHMARK.md`](BENCHMARK.md) drops below a 90%
recovery rate or a static diff performs equally well on independent cases,
the *value* claim is falsified even if the novelty claim survives. See
[`ADOPTION.md`](ADOPTION.md).
