# Agent roster

Specialised agent charters used for this build. Each file states the charter,
required inputs, deliverables, and the **acceptance gate** the manager applies.
An artifact that fails its gate is sent back, not merged.

| Agent | Charter | Deliverable |
| --- | --- | --- |
| [manager.md](manager.md) | Strict gatekeeper; owns every hand-off | Rejection log, final gate |
| [product-strategist.md](product-strategist.md) | Independent ideation, labelled claims | Candidate directions |
| [prior-art-researcher.md](prior-art-researcher.md) | Kill ideas with located evidence | `docs/research/prior_art_agent_report.md` |
| [adversarial-critic.md](adversarial-critic.md) | Falsify the value proposition | `docs/research/adoption_grill_agent_report.md` |
| [threat-modeller.md](threat-modeller.md) | Assets, boundaries, attack table | `docs/research/threat_model_agent_report.md` |
| [spec-writer.md](spec-writer.md) | Design doc, glossary, ADRs | `PLAN.md`, `GLOSSARY.md`, `docs/adr/` |
| [implementer.md](implementer.md) | Typed modules, safe primitives | `counterfact/` |
| [test-engineer.md](test-engineer.md) | Red/green tests, planted fixtures | `tests/`, `scripts/benchmark.py` |
| [security-auditor.md](security-auditor.md) | 12 independent review rounds | `scripts/audit.py`, `REVIEW.md` |
| [architecture-reviewer.md](architecture-reviewer.md) | Deepening behind equivalence gate | `docs/architecture-review.html` |
| [release-engineer.md](release-engineer.md) | Packaging, CI, docs, zip | `pyproject.toml`, `action.yml`, `.github/` |

See [`WORKFLOW.md`](../WORKFLOW.md) for the pipeline and the real rejection log.
