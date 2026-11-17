# ADR-0003: capture is an allowlist, not a snapshot of everything

**Status:** accepted.

## Context

A full `os.environ` capture is the obvious implementation and the obvious
secret-leak vector: tokens, cloud credentials and session keys would be written
to a JSON file that users share with teammates and upload to CI artifacts.

## Decision

`counterfact capture` records only `CAPTURE_ENV_KEYS` (locale/TZ, CI flags,
thread counts, hash seeds), `PATH`, `@UMASK`, and explicitly named `--factor`
keys / `--tool` paths. Dangerous loader and interpreter variables are refused
on load as well as on capture. Operator-added keys remain the operator's
responsibility and are documented as such.

Metadata (platform, Python version, capture time) is descriptive only and is
never replayed as a Factor; differing metadata produces a scope warning.

## Consequences

Uncaptured state (kernel, network, wall clock, installed system libraries) can
cause "no reproduction". That is reported honestly rather than guessed. An
explicit `--factor` is how an operator widens the experiment deliberately.
