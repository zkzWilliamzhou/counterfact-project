# Agent: threat modeller

**Charter.** Model a tool that repeatedly executes arbitrary commands while
importing untrusted snapshot state. Prioritise causal integrity as well as
confidentiality and availability.

**Inputs.** The proposed replay loop and factor taxonomy.

**Deliverable.** `docs/research/threat_model_agent_report.md`: assets, trust
boundaries, attacker models, vulnerability classes with mitigations, a
safe-by-design checklist, at least 12 concrete attack scenarios, and an exit
code / error contract.

**Acceptance gate.** Must cover command injection, argument injection, env
poisoning, symlink/TOCTOU, resource exhaustion, secret leakage, unsafe
deserialisation, ReDoS, and flaky-command false causality. If sources are
unavailable, label the report "reasoning-based" rather than fabricating
citations. Rejected if it treats a temporary directory as a sandbox.

**Result.** Directly shaped `counterfact/safety.py`, `workspace.py`,
`process.py`, `THREAT_MODEL.md` and review rounds 3, 4 and 6.
