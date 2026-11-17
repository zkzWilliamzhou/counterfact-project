# Review log — 12 rounds

`scripts/audit.py` runs **twelve** independent review rounds (the brief asked
for "over 8"). Each round makes real assertions; an empty finding list is the
only PASS condition. A harness that crashes is recorded as a failure, not a
pass. Machine-readable evidence: [`REVIEW_LOG.json`](REVIEW_LOG.json).

## Summary

| Run | Result | Action |
| --- | --- | --- |
| First full audit (8 rounds) | **3/8 PASS**, 9 findings | sent back, revised |
| Second audit (8 rounds) | **7/8 PASS**, 1 finding | harness itself rejected, replaced |
| Third audit (8 rounds) | **8/8 PASS** | baseline frozen |
| Extended audit (12 rounds) | **11/12 PASS**, 1 finding | packaging defect fixed, harness strengthened |
| Final audit (12 rounds) | **12/12 PASS** | accepted |

## Round-by-round

| # | Focus | What it actually asserts |
| --- | --- | --- |
| 1 | Static / supply chain / protocols | Banned constructs (`shell=True`, `eval`, pickle, YAML load, network imports) absent from live code; `compileall` clean; all vendored protocol docs present |
| 2 | Test suite | 58 tests green; test count sanity |
| 3 | Adversarial parser fuzzing | 420 fuzz cases; deep JSON cannot crash the parser; `bool` rejected as a schema version; no unhandled exception leaks |
| 4 | Security controls and secret hygiene | Behavioural symlink exploit on `--save-experiments`; denylist completeness; a token-shaped secret must not appear in any of four renderers |
| 5 | Algorithm / status reachability | `PROBABLE` reachable; 30 random monotone ddmin cases recover the planted set; anchors refuse to invent a cause |
| 6 | Resources and process groups | No leaked sandbox dirs after 20 runs; a spawned descendant does not survive timeout; no fd growth |
| 7 | CI / UX contract | `plan` stdout is pure JSON; missing args exit 2; SARIF parses; every `--flag` in the README exists in the CLI |
| 8 | Equivalence / packaging / dogfooding | Byte-identical frozen behaviour; packaging metadata; `capture` → `compare` clean empty diff |
| 9 | Planted recovery benchmark | 20 real-process cases, >= 90% recovery and 95% under 50 executions; a wrong `CONFIRMED` set is a failure |
| 10 | Noise injection | 18 seeds with 18% `UNRESOLVED` noise; never confirm a factor set other than the true cause |
| 11 | Documentation / version consistency | Every relative markdown link resolves; exit codes match `errors.py`; `__version__` matches `pyproject.toml`; every module imports |
| 12 | Release candidate | CLI exit-code matrix (0/1/2/3), `demo` confirms, clean offline `pip install --target` + import smoke, version sanity |

## Findings from the first run and their revisions

| Round | Finding | Revision |
| --- | --- | --- |
| 1 | Harness flagged the word "pickle" in a docstring | Fixed the harness to flag real usage (`import pickle` / `pickle.load`), not prose. **Harness defect**, not a program defect. |
| 3 | `RecursionError` leaked from `json.loads` on 1500-deep input | `loads_bounded` now catches `RecursionError` and raises `SafetyError` |
| 3 | `True` accepted as `schema_version == 1` (bool is an int subclass) | Explicit `isinstance(version, bool)` rejection in `snapshot_from_obj` |
| 4 | `--save-experiments` had no symlink guard | Added shared `_write_report` refusing symlink destinations and missing parents |
| 4 | A token-shaped secret leaked via `render_text`'s oracle line | Oracle values redacted in the human renderer too |
| 5 | `STATUS_PROBABLE` was unreachable — strong-but-imperfect evidence collapsed into `INCONCLUSIVE` | `proof.verify` now distinguishes `partial`, `not necessary`, `strong` and `full stability`; added a unit test for reachability |
| 7 | `plan` appended a human comment to stdout, breaking `jq` pipelines | Commentary moved to stderr; stdout is pure JSON |

Second run, round 4 still failed: the check grepped `cli.py` for a literal
string instead of testing behaviour. **The manager rejected the harness**, and
it was replaced with an actual symlink exploit test that asserts exit code 3
and an untouched link target.

### Extended audit (rounds 9–12)

| Round | Finding | Revision |
| --- | --- | --- |
| 12 | Clean offline install produced `UNKNOWN-0.0.0` and the installed package could not be imported: the build host's setuptools 59.6.0 ignores PEP 621 `[project]` metadata when `--no-build-isolation` is used | Added `setup.py` as a metadata-identical compatibility shim for setuptools < 61. Round 11 now also asserts the shim's version and console entry point cannot drift. Re-verified: `counterfact_cli-0.1.0.dist-info`, import returns `0.1.0` |

This is a genuine defect found by the extra rounds, not a harness artifact. It
is the reason "over 8 rounds" was worth doing rather than treating 8/8 as
final.

## Third-party agent work, also reviewed

- Prior-art report — accepted after checking that every tool lists its non-goals.
- Adoption critique — **first attempt rejected**: the research channel returned
  no sources and the agent refused to fabricate; re-tasked with a narrower
  brief. Second attempt accepted, with the "why not to build" section preserved.
- Threat model — accepted as explicitly **reasoning-based**, not as an audit.
- `minimize.py` first draft — **rejected** for an invalid placeholder import;
  rewritten from scratch.
- First test run — **3/58 failures rejected back to implementation**:
  truncation never observable (RLIMIT_FSIZE equal to the report cap), secret
  leakage in JSON, and `PATH` validation demanding directories that exist on
  the local machine. Fixed with a one-byte headroom, redaction at the machine
  output boundary, and structural-only `PATH` validation.

## Residual risks (not closed by a green audit)

- counterfact is not a security sandbox; use a container/VM for untrusted
  commands.
- "Offline" applies to counterfact, not to the replayed command.
- The benchmark corpus is planted in-repo, not independently authored.
- Uncaptured state can produce `NO_REPRODUCTION`.
- A 1-minimal set is claimed only over configurations actually tested.

See [`THREAT_MODEL.md`](THREAT_MODEL.md) and [`SECURITY.md`](SECURITY.md).
