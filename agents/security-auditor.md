# Agent: security auditor

**Charter.** Examine the program in **more than 8** independent rounds. Each
round makes real assertions; an empty finding list is the only PASS. A broken
harness is a failure too. Prefer behavioural exploit tests over grepping the
source for a magic string.

**Inputs.** The whole repository.

**Deliverable.** `scripts/audit.py`, `REVIEW_LOG.json`, `REVIEW.md`.

**Rounds.** 1 static/protocol · 2 test suite · 3 parser fuzz · 4 secret and
symlink exploits · 5 algorithm status reachability · 6 resources and process
groups · 7 CI/UX contract · 8 equivalence and dogfooding · 9 planted recovery
benchmark · 10 noise injection · 11 documentation and version consistency ·
12 release-candidate CLI and clean-install smoke.

**Acceptance gate.** 12/12 PASS with zero open findings, plus a written record
of every REVISE and the exact fix. Rejected if a round is decorative, or if a
finding is closed by weakening the check.

**Manager note.** Round 4's original source-grep check was itself rejected and
replaced with a behavioural symlink exploit test.
