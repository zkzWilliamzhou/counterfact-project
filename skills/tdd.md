# Protocol: TDD / red-green (adapted)

Sources: `mattpocock/skills` → `skills/engineering/tdd/SKILL.md`,
`skills/engineering/code-review/SKILL.md`; `obra/superpowers` →
`skills/writing-plans/SKILL.md`
Full vendored texts in `skills/vendor/`.

## Applied here
- **Red first.** `tests/` was written against the intended contract before the
  audit gate ran. The first full run produced **3 real failures**:
  truncation detection, secret leakage in JSON, and cross-machine `PATH`
  validation. Those failures were fixed, not explained away.
- **Green.** 58 tests pass.
- **Refactor only behind an equivalence gate.** The architecture deepening was
  not allowed to start until `equivalence.py --record` had frozen behaviour, and
  it cannot land until `--check` passes.
- **Review by a fresh reader.** `scripts/audit.py` runs 8 independent rounds;
  a round that finds anything is `REVISE`, never `PASS`.

## Non-negotiable review rules
1. A timeout is an observation, never a failure.
2. A flaky command never yields a confirmed result.
3. Every emitted string is redacted and control-character free.
4. Untrusted values never become argv, shell strings, regexes or paths outside
   the sandbox.
