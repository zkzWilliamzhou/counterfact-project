# GLOSSARY

Names for the domain concepts in counterfact. Architecture reviews use these
terms, plus the module/interface/depth/seam/adapter/leverage/locality
vocabulary from
[`skills/improve-codebase-architecture.md`](skills/improve-codebase-architecture.md).

| Term | Meaning |
| --- | --- |
| **Snapshot** | A captured, allowlisted, replayable environment state: typed factors plus descriptive metadata. Metadata is never a factor. |
| **Factor** | One difference between a passing Snapshot and a failing Snapshot. Kinds: `env`, `tool`, `umask`. |
| **Intervention** | Applying a subset of the bad-side values of Factors to the good-side state. |
| **Oracle** | The operator-supplied rule that classifies one observation as `PASS`, `FAIL` or `UNRESOLVED`. |
| **Observation** | A single Experiment result. An observation is evidence of an outcome, never proof of a cause. |
| **Anchor** | One of the two control runs: the good state must PASS, and applying all differences must reproduce FAIL. |
| **1-minimal tested causal set** | The smallest subset of Factors, among those actually tested, whose application still reproduces FAIL and from which no single Factor can be removed without losing FAIL. Explicitly not a unique or global cause. |
| **Replication** | Independent re-runs (cache disabled) of sufficiency, anchor stability and necessity. |
| **Scope notice** | The printed statement bounding every conclusion to the supplied oracle, runner and captured states. |
| **Composition** | The pure transformation from RunSpec + Factors + an intervention set into a fully resolved env/argv/umask triple. |
| **Observer** | The interface (`counterfact/ports.py`) through which `minimize` and `proof` request observations. The interface is the test surface. |
| **Adapter** | A module that owns one external dependency: `workspace` (filesystem), `process` (subprocess). Two adapters make the seam real. |
| **RunSpec** | A typed, immutable execution model: argv, base environment, good factors, tool paths, umask, workdir. |
| **Budget** | Bounds on runs, timeout, output bytes, total wall time and repeats. |
| **Inert plan** | The default state: a complete, auditable specification of what would be executed, with no execution. |
| **UNRESOLVED** | Timeout, launcher error, or a failure that does not match the oracle's signature. Treated as "not the target failure", never as FAIL. |
| **FLAKY** | The command changed outcome with no Factor changed. No causal conclusion is printed. |
| **PROBABLE** | Anchors held but 1-minimality or full stability did not. A weaker, explicitly labelled finding. |
| **Equivalence gate** | A frozen, normalised snapshot of observable behaviour that a refactor must match byte-for-byte. |
