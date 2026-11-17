# Threat model (condensed)

Full reasoning-based assessment:
[`docs/research/threat_model_agent_report.md`](docs/research/threat_model_agent_report.md).
That report is explicitly labelled "reasoning-based"; it does not claim to be an
independent security audit. `REVIEW.md` records the machine-checked controls.

## Assets and trust boundaries

**Assets:** credentials/tokens, identity and privilege, user and project data,
filesystem integrity, CPU/memory/disk/PID resources, experimental integrity
(exit codes, output, timing), and the user's trust in a printed conclusion.

**Three compartments:**
1. **Operator** — the human invocation. Trusted to choose what may run, not
   assumed to have audited a malicious snapshot.
2. **Imported state** — snapshots, config, workdir filenames, tool paths.
   Untrusted data, always.
3. **Child execution** — the user-supplied command and all descendants.
   Potentially hostile even when authorised.

**Attacker models:** malicious repository, malicious CI snapshot JSON,
malicious command, malicious config, local unprivileged user, flaky command,
and network-reachable resources if the command reaches out.

## Safe-by-design checklist

| Control | Implementation | Default |
| --- | --- | --- |
| Explicit execution opt-in | `run` requires `--yes`; `plan` is inert | refuse |
| No shell | argv list, `shell=False`, no `sh -c` | always |
| Executable selection | absolute validated path or trusted-PATH lookup | always |
| No snapshot → argv interpolation | snapshot values only become env vars / tool paths | always |
| Constructed environment | `SAFE_BASE_ENV`, never inherits the parent | always |
| Dangerous env vars | `DENIED_ENV` covers loader, interpreter, shell, allocator, locale-data and home/tmp vars | refuse |
| PATH factor | structural validation: absolute, no `..`, no control chars | allow (validated) |
| Bounded parsing | UTF-8 JSON, 256 KiB, depth 12, 5000 nodes, 4096-char strings, duplicate keys rejected | always |
| No YAML / pickle / user regex | not used anywhere | always |
| Filesystem | private 0700 workspace, `O_NOFOLLOW`, symlinks skipped, containment checks, bounded copies | always |
| Resources | wall timeout, CPU, RLIMIT_FSIZE, RLIMIT_NOFILE, output cap, max runs, max total time | always |
| Process termination | `start_new_session`, SIGTERM → SIGKILL on the process group | always |
| Secrets | allowlist capture, name/shape redaction in every renderer | always |
| Output | ANSI/control stripping, unicode-dash normalisation, truncation recorded | always |
| Oracle | timeout/error/unmatched failure → `UNRESOLVED`, never `FAIL` | always |
| Causal integrity | anchors, 1-minimality, stability with cache disabled | always |
| Report writes | refuse symlink destinations and missing parents | always |
| Verification | independent re-runs; `FLAKY` / `INCONCLUSIVE` never exit 0 | always |

## Attack scenarios

| # | Scenario | Impact | Mitigation |
| --- | --- | --- | --- |
| 1 | Snapshot sets `LD_PRELOAD` | Loads attacker library into child | denylist refusal |
| 2 | Snapshot sets `PYTHONPATH` / `BASH_ENV` | Import/startup code execution | denylist refusal |
| 3 | Command string contains `; curl … \| sh` | Additional command execution | argv list, no shell |
| 4 | Filename `--output=/etc/cron.d/x` | Option injection into a tool | `validate_relpath` rejects leading dashes and metacharacters |
| 5 | Unicode dash in a path | Normalises into an option | unicode-dash rejection/normalisation |
| 6 | Symlink in workdir escapes sandbox | Reads/writes outside workspace | symlinks skipped, containment check |
| 7 | TOCTOU swap of a baseline file | Corrupted oracle | bounded read, copied workspace, no re-open by name |
| 8 | Deeply nested JSON | RecursionError / memory exhaustion | depth + node + byte limits, RecursionError caught |
| 9 | Duplicate JSON keys | Conflicting safety settings | `object_pairs_hook` rejects |
| 10 | 500 MB stdout | Terminal/disk/memory exhaustion | RLIMIT_FSIZE + output cap + truncation flag |
| 11 | Fork bomb / orphan children | Host DoS | process group SIGTERM→SIGKILL, bounded escalation |
| 12 | Interactive command reads stdin | Hangs | `stdin=DEVNULL`, wall timeout |
| 13 | Secret printed by the child | Leaks into report | name/shape redaction in all renderers |
| 14 | Report path is a symlink to a config file | Overwrites user data | symlink refusal |
| 15 | Flaky command | Convincing false causal claim | stability baseline + `FLAKY` status |
| 16 | Pickle/YAML in a config file | Arbitrary object construction | formats not supported |
| 17 | Huge PATH / relative PATH entry | PATH hijack | structural PATH validation; argv[0] always absolute |
| 18 | `curl` in the target command reaches the network | Exfiltration while "offline" | documented: offline applies to counterfact, not to the command; use a container adapter |

## Residual risks (disclosed, not hidden)

- counterfact is **not a security sandbox**. It is a bounded runner against
  accidental damage and untrusted data, not against a determined local
  adversary with the same UID. Use a container/VM for untrusted commands.
- "Offline" means counterfact makes no network calls; the replayed command may.
- `RLIMIT_AS` is deliberately not set (it breaks legitimate interpreters).
- A command that mutates state outside its workspace is not prevented by
  process limits.
- Snapshots from a different machine can carry a PATH whose directories do not
  exist locally; PATH is a factor, not a security boundary, because argv[0] is
  always resolved to a validated absolute executable.

## Exit-code contract

`0` confirmed/probable · `1` inconclusive/flaky/no-reproduction/budget ·
`2` usage/config · `3` safety refusal · `4` internal · `130` interrupted.
Documented in [`README.md`](README.md) and enforced in `counterfact/errors.py`.

## Reporting a vulnerability

See [`SECURITY.md`](SECURITY.md).
