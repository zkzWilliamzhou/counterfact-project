# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes |

## Reporting a vulnerability

Open a private security advisory on the repository, or email the maintainers
with a reproducible case. Please include the version, platform, the snapshot
(if safe to share — redact secrets first), and the smallest command that
demonstrates the issue. Do not paste real tokens into a public issue.

## What this project will and will not do

counterfact repeatedly executes a command supplied by the operator. It is a
**bounded runner**, not a security sandbox. It reduces accidental damage,
untrusted-data injection and noisy false conclusions. It does not provide a
security boundary against a determined local user with the same UID, and it
does not prevent the replayed command from making network calls.

If you need to analyse a command you do not trust, run counterfact inside a
container or VM with no credentials and no network. This is the documented
recommendation, not an optional nicety.

## Safe usage checklist

1. Run `counterfact plan` first. It executes nothing.
2. Use `--expect-fail-text` so unrelated crashes cannot be mistaken for the
   target failure.
3. Keep `--timeout`, `--max-runs` and `--max-total` small.
4. Review snapshots before sharing; capture is an allowlist, but operator-added
   `--factor` keys are your responsibility.
5. Do not use `--yes` on a command that writes outside a disposable tree.
6. Treat `PROBABLE`, `INCONCLUSIVE`, `FLAKY` and `BUDGET_EXCEEDED` as "no
   conclusion", not as a near-miss.

## Controls verified in CI

`scripts/audit.py` runs 12 independent review rounds, including adversarial
parser fuzzing, a behavioural symlink exploit test, secret-leak checks,
process-group termination, resource bounds, and a clean-install smoke test.
See [`REVIEW.md`](REVIEW.md) and [`THREAT_MODEL.md`](THREAT_MODEL.md).
