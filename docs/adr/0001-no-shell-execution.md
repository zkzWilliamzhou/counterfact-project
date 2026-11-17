# ADR-0001: never use a shell

**Status:** accepted. Do not re-litigate in architecture reviews.

## Context

counterfact must replay an arbitrary developer command many times while
applying untrusted snapshot values. A shell string would let a value such as
`$(...)`, `;`, `|`, backticks or a newline become additional command
execution. Escaping is not a reliable defence because the target program may
re-parse the value as an option.

## Decision

Commands are parsed once into a typed `argv` tuple and passed with
`shell=False`. No `sh -c`, `bash -c`, `cmd /c`, `os.system` or equivalent.
Snapshot values never become argv elements; they only become validated
environment variables or validated tool paths. Options and operands are
validated before use.

## Consequences

- Shell pipelines, globs, redirects and environment-variable expansion in the
  command are not supported. Operators who need them must wrap them in an
  explicit script — and that script is itself a reviewed executable.
- The `Runner` has exactly one process entry point, in `counterfact/process.py`.
- Any future proposal to add a "convenience shell mode" must be a new ADR, not
  a refactor.
