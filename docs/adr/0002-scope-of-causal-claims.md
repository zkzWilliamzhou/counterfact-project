# ADR-0002: the claim is a 1-minimal tested causal set, never a root cause

**Status:** accepted. Do not re-litigate in architecture reviews.

## Context

Delta debugging can establish that a tested configuration is 1-minimal with
respect to a supplied oracle. It cannot prove a unique global cause, the
underlying code defect, or behaviour outside the runner. A confident
"root cause found" from a flaky command is a safety defect, not a wording issue.

## Decision

- Every renderer prints the scope notice, including JSON and SARIF.
- Statuses: `CONFIRMED`, `PROBABLE`, `INCONCLUSIVE`, `FLAKY`,
  `BUDGET_EXCEEDED`, `NO_REPRODUCTION`.
- Only `CONFIRMED` and `PROBABLE` exit 0.
- A timeout, launcher error, or non-matching non-zero exit is `UNRESOLVED`.
- Anchors, stability and necessity are re-run with caching disabled.
- The words "root cause", "prove", "guarantee" are not used as product claims.

## Consequences

Marketing cannot outrun the benchmark. Feature requests to "just print the
most likely cause" are rejected; the correct output in that case is
`INCONCLUSIVE`.
