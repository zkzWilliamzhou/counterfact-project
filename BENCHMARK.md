# Benchmark: recovery on planted environment failures

Deterministic seed `20261114`, 20 cases, real child processes (no mocks).

| Metric | Result | Gate | Verdict |
| --- | --- | --- | --- |
| Recovery rate | 100% (20/20) | >= 90% | PASS |
| Searches under 50 executions | 100% (20/20) | >= 95% | PASS |
| Max / median executions | 37 / 23 | report | — |
| Wall clock | 5.72 s | report | — |

**Overall: PASS**

Each case plants 1–3 causal factors among 6 candidate keys, plus 3 harmless decoy differences (`TZ`, `CI`, `@UMASK`). The failing script exits non-zero only when every planted factor is present, so the failure predicate is monotone and ddmin's assumptions hold.

## Per-case detail

| # | Planted | Found | Status | Executions | Recovered |
| --- | --- | --- | --- | --- | --- |
| 0 | F1 | F1 | CONFIRMED | 11 | yes |
| 1 | F1, F3, F4 | F1, F3, F4 | CONFIRMED | 26 | yes |
| 2 | F0, F3 | F0, F3 | CONFIRMED | 25 | yes |
| 3 | F3 | F3 | CONFIRMED | 11 | yes |
| 4 | F0, F1, F3 | F0, F1, F3 | CONFIRMED | 37 | yes |
| 5 | F3, F4, F5 | F3, F4, F5 | CONFIRMED | 23 | yes |
| 6 | F2, F5 | F2, F5 | CONFIRMED | 23 | yes |
| 7 | F1 | F1 | CONFIRMED | 11 | yes |
| 8 | F1, F4 | F1, F4 | CONFIRMED | 24 | yes |
| 9 | F1, F2, F5 | F1, F2, F5 | CONFIRMED | 27 | yes |
| 10 | F2, F3 | F2, F3 | CONFIRMED | 24 | yes |
| 11 | F0, F1, F2 | F0, F1, F2 | CONFIRMED | 19 | yes |
| 12 | F3 | F3 | CONFIRMED | 11 | yes |
| 13 | F0, F1, F3 | F0, F1, F3 | CONFIRMED | 37 | yes |
| 14 | F1 | F1 | CONFIRMED | 11 | yes |
| 15 | F2 | F2 | CONFIRMED | 12 | yes |
| 16 | F1, F2, F5 | F1, F2, F5 | CONFIRMED | 27 | yes |
| 17 | F1, F2 | F1, F2 | CONFIRMED | 13 | yes |
| 18 | F3 | F3 | CONFIRMED | 11 | yes |
| 19 | F1, F2, F4 | F1, F2, F4 | CONFIRMED | 27 | yes |

## What this does not prove

It does not prove recovery on real-world flaky commands, on failures caused by un-captured state (kernel, network, wall clock), or on non-monotone multi-factor interactions. It is a lower bound on the algorithm under controlled conditions, not a real-world accuracy claim.
