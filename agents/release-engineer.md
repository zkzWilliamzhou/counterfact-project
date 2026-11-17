# Agent: release engineer

**Charter.** Make the repository installable, CI-checkable and shippable without
introducing a runtime dependency or a network requirement.

**Inputs.** The finished code, docs and gates.

**Deliverable.** `pyproject.toml` (console script), `LICENSE`, `README.md`,
`CONTRIBUTING.md`, `CHANGELOG.md`, `.gitignore`, `action.yml` (composite GitHub
Action skeleton), `.github/workflows/ci.yml`, and the final zip archive.

**Acceptance gate.** A clean `pip install --no-deps --no-build-isolation
--target <tmp>` must succeed and the installed package must import offline
(checked in audit round 12). CI must run tests, equivalence, benchmark and
audit. Every documented flag must exist in the CLI (round 7). Every markdown
link must resolve (round 11). Rejected if packaging requires a network fetch
or if a documented file is missing.

**Final gate.** 12/12 audit PASS, equivalence OK, benchmark gates PASS, then
package.
