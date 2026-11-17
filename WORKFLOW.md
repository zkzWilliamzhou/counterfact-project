# Workflow and agent roster

The operator asked for a workflow, specialised agents, and a **strict manager**
that rejects low-quality, incomplete or fabricated work and sends it back. This
document is the control record. Each agent has a charter in
[`agents/`](agents/README.md) with inputs, outputs and acceptance gates.

## The agents actually used

Four research agents were dispatched during this build. They were not cosmetic:

| Agent | Task | Outcome |
| --- | --- | --- |
| Prior-art researcher | Survey adjacent OSS tooling for candidate A | `docs/research/prior_art_agent_report.md` — killed candidate A |
| Adoption critic (first attempt) | Star-count and positioning research | **FAILED**: research channel returned no sources; the agent refused to fabricate. Manager rejected the empty result instead of accepting it. |
| Threat modeller | Security and safety threat model | `docs/research/threat_model_agent_report.md` — reasoning-based, explicitly labelled |
| Adoption critic (second attempt, narrowed) | Adversarial critique + go/no-go gates | `docs/research/adoption_grill_agent_report.md` — "why this should not be built" preserved |

The failed agent run is recorded here rather than hidden. Its replacement was
re-tasked with a narrower, source-bounded brief.

## Pipeline

```
   [1] Product strategist        -> independent ideation, labelled claims
   [2] Prior-art researcher      -> kills candidates with located evidence
   [3] Adversarial critic        -> "why not to build", falsification gates
   [4] Threat modeller           -> assets, boundaries, attack table
   [5] Spec writer               -> PLAN.md, GLOSSARY.md, ADRs
   [6] Implementer               -> typed modules, no ad-hoc shortcuts
   [7] Test engineer             -> red/green tests before promotion
   [8] Security auditor          -> 12 review rounds, exploit tests
   [9] Architecture reviewer     -> deepening behind equivalence gate
  [10] Release engineer          -> packaging, CI, docs, zip
        ^
        | every hand-off passes through the MANAGER gate
```

Each hand-off is a **gate**, not a notification. The manager inspects the
artifact against the charter; a missing part, a fabricated number, an
unlabelled inference, or a claim without evidence sends the work back.

## Manager rejection log (real, from this build)

| # | Artifact | Defect found | Action |
| --- | --- | --- | --- |
| 1 | Adoption research report | Empty sources; agent correctly refused to invent citations | Rejected, re-tasked with a narrower brief and explicit "no fabrication" constraint |
| 2 | Initial `minimize.py` | Contained an invalid placeholder import (`STATUS_BUDGET if False else None`) | Sent back; rewritten from scratch |
| 3 | First full test run (58 tests) | 3 failures: truncation never observable, token leaked into JSON, cross-machine `PATH` validation too strict | Sent back; three fixes; re-run green |
| 4 | First 8-round audit | 5 of 8 rounds REVISE (9 concrete findings) | Sent back; see [`REVIEW.md`](REVIEW.md) for each revision |
| 5 | Second audit | Round 4 used a fragile source-grep instead of a behavioural test | Harness revised into a real symlink exploit test |
| 6 | Name `culprit` | Existing PyPI package with the same name | Killed; renamed `counterfact` |
| 7 | Architecture review | Risk of changing program function | Blocked until `equivalence.py --record` froze behaviour; `--check` required to land |

## Strictness rules

1. **No evidence, no claim.** A number without a source or a measurement is
   deleted, not softened.
2. **Absence of a hit is not novelty.** Search boundaries are recorded.
3. **A failed round is REVISE.** A broken harness is a failure, not a pass.
4. **Tests before promotion.** 58 unit/integration tests gate every release.
5. **Refactor behind a frozen gate.** Byte-identical observable behaviour is
   the only acceptable result.
6. **Scope notice everywhere.** Text, JSON, SARIF and GitHub renderers.
7. **Honest failure states.** `FLAKY`, `INCONCLUSIVE`, `BUDGET_EXCEEDED` and
   `NO_REPRODUCTION` are first-class results, not errors to hide.

## Skills installed from GitHub

Fetched over HTTPS tarballs (direct `git clone` was blocked):
`anthropics/skills`, `mattpocock/skills`, `vercel-labs/skills`,
`obra/superpowers`, `hardikpandya/stop-slop`. 86 `SKILL.md` files were
retrieved; the protocols applied to this build are in
[`skills/`](skills/README.md). Additional project-relevant protocols loaded
for the work: scientific brainstorming, scientific critical thinking, and
`archify`. Honest scope: these were fetched, read and applied as working
protocols; they were not registered as runtime skills in the build
environment.

## Final gate

`python scripts/audit.py` must report **12/12 PASS** and
`python scripts/equivalence.py --check` must report `EQUIVALENCE OK` before
the repository is packaged. Both results are recorded in
[`REVIEW.md`](REVIEW.md) and [`EQUIVALENCE.md`](EQUIVALENCE.md).
