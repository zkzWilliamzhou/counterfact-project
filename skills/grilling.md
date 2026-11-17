# Protocol: grilling (adapted)

Sources: `mattpocock/skills` → `skills/productivity/grilling/SKILL.md` and
`skills/productivity/grill-me/SKILL.md`, `skills/engineering/grill-with-docs/SKILL.md`
Full vendored texts: `skills/vendor/grilling.SKILL.md`, `skills/vendor/grill-me.SKILL.md`

## The design tree, worked in rounds
The upstream protocol interviews the human in rounds until the frontier is
empty. Here the operator delegated the interview ("grilling yourself"), so the
manager agent plays both roles and records the whole tree.

**Round 1 frontier (settled facts first):**
- Q1: What does "does not exist" mean operationally? → *Decision*: no located
  tool provides the same function; bounded search is not global proof.
- Q2: Is a 105k-star target an engineering requirement? → *Decision*: no. It is
  an aspiration; quality gates replace it.
- Q3: Which domain has the largest unserved pain? → *Fact-finding delegated*:
  prior-art agent + web evidence.

**Round 2 frontier (after prior art returned):**
- Q4: Candidate A (docs/claim drift verifier) — novel? → **KILLED** by 8 located
  tools (`stale-cli`, `driftmd`, `docverity`, `ctxlint`, `agents-lint`,
  `agenteval`, `codeconscience`, `conventions-cli`).
- Q5: Candidate B (side-effect receipts / false-green) — novel? → **KILLED** by
  `falsegreen`, `testrot`, `FGD`, `dynobox`, `reelier`, `Drifti`, `agentlie`,
  `provenance-recorder`, `Hawkeye`, `ProcDrift`.
- Q6: Candidate C (env diff / diagnosis) — novel? → **KILLED** by `EnvFixer`,
  `envdiff`, `DevRepro Doctor`, `Tracebox`, `AIHostCheck`.

**Round 3 frontier (reopened ideation after evidence):**
- Q7: What do ALL killed candidates have in common? → They observe, diff, rank,
  record or reproduce. None **intervenes** and re-runs under a minimal set.
- Q8: What is the smallest defensible claim? → "1-minimal tested causal set
  under a supplied oracle", never "root cause".
- Q9: What would falsify it? → recovery rate < 90% on planted fixtures, or
  failure to outperform a static diff. Recorded as go/no-go gates.
- Q10: Is the name free? → **KILLED** `culprit` (existing PyPI package).
  *Decision*: rename to `counterfact`.

**Frontier empty.** All decisions logged in `PLAN.md`; no branch left silently
assumed. The adversarial agent's "why this should not be built" section is
reproduced in `ADOPTION.md`.
