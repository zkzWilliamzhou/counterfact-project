# Agent: implementer

**Charter.** Build the typed modules exactly as designed. No shell, no
inherited environment, no untrusted value in argv, no unbounded read, no
silent fallback that turns a safety check into a pass.

**Inputs.** `PLAN.md`, `GLOSSARY.md`, ADR-0001…0004, the threat model.

**Deliverable.** `counterfact/` — safety, state, plan, composition, workspace,
process, runner, oracle, minimize, proof, report, cli.

**Acceptance gate.** Compile clean; every module has one clear responsibility;
`minimize` and `proof` depend on the `Observer` interface rather than on
`Runner`; every emitted string redacted. Rejected for placeholder imports,
dead code, or a control that exists only in a comment.

**Manager note.** The first `minimize.py` contained an invalid placeholder
import and was rejected outright and rewritten.
