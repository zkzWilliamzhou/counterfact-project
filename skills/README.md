# Vendored workflow protocols

These are the working protocols used to build this repository. The original
`SKILL.md` files were fetched from GitHub over HTTPS (direct `git clone` was
blocked in the build environment) and are preserved verbatim in `skills/vendor/`.

| Protocol | Upstream | Vendored file |
| --- | --- | --- |
| brainstorming | `obra/superpowers` | `vendor/brainstorming.SKILL.md`, `vendor/writing-plans.SKILL.md` |
| grilling / grill-me | `mattpocock/skills` | `vendor/grilling.SKILL.md`, `vendor/grill-me.SKILL.md` |
| stop-slop | `hardikpandya/stop-slop` | `vendor/stop-slop.SKILL.md`, `vendor/stop-slop.README.md` |
| improve-codebase-architecture | `mattpocock/skills` | `vendor/improve-codebase-architecture.SKILL.md` |
| tdd / code-review | `mattpocock/skills` | `vendor/tdd.SKILL.md`, `vendor/code-review.SKILL.md` |

Also fetched into the build workspace (not copied here, because they are
reference collections rather than protocols this repo executes):
`anthropics/skills`, `vercel-labs/skills`, `mattpocock/skills`,
`obra/superpowers`. 86 `SKILL.md` files were retrieved in total.

The adapted, project-specific instructions actually followed are in:

- `brainstorming.md` — independent ideation, labelled claims, decision log
- `grilling.md` — the full design tree and three evidence-backed kills
- `stop-slop.md` — prose quality gate applied to every user-facing string
- `improve-codebase-architecture.md` — deepening pass with an equivalence gate
- `tdd.md` — red/green, review discipline

**Honest scope:** these repos could not be *registered as runtime skills* in the
build environment. Their contents were fetched, read, and applied as working
protocols, and the resulting decisions are documented. No claim is made that a
third-party skill was installed into any runtime.
