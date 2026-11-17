# Changelog

## 0.1.0 — initial evidence-first release

- `capture`, `compare`, `plan`, `run --yes`, `demo` subcommands.
- Counterfactual environment search (ddmin) with sufficiency, stability and
  necessity verification.
- Fingerprint oracle; `UNRESOLVED` for timeouts, launcher errors and unmatched
  failures.
- Bounded JSON parsing, environment denylist, secret redaction, private
  sandboxes, process-group termination and resource caps.
- Text, JSON, SARIF 2.1.0 and GitHub annotation renderers.
- 58 unit/integration/adversarial tests; 12-round automated review harness;
  planted-fixture recovery benchmark (100% on 20 deterministic cases).
- Architecture deepening behind a byte-identical behaviour-equivalence gate.
- Design doc, prior-art survey, adoption critique, threat model, glossary,
  ADRs, workflow and agent charters.
- `setup.py` compatibility shim so offline installs on setuptools < 61 produce
  a correctly named distribution (found by review round 12).

### Known limitations

- Not a security sandbox; use a container/VM for untrusted commands.
- "Offline" applies to counterfact, not to the replayed command.
- Uncaptured state (kernel, network, wall clock, system libraries) can cause
  `NO_REPRODUCTION`.
- The published benchmark corpus is planted in-repo, not independently
  authored.
- 1-minimality is claimed only over the configurations actually tested.
