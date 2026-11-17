# Protocol: brainstorming (adapted)

Source: `obra/superpowers` → `skills/brainstorming/SKILL.md`
Full vendored text: `skills/vendor/brainstorming.SKILL.md`

## Why it exists
The brief ("build a program that gets 105k stars and does not exist yet") is a
wish, not a spec. The hardest failure in building is discovering that the
request was thinner than it sounded.

## Hard rules applied here
1. **Independent generation before exposure.** Candidate product directions were
   generated privately before any prior-art search, so the evidence base could
   not anchor the ideation round.
2. **Label every claim**: `idea` / `assumption` / `prediction` /
   `located evidence` / `decision`. These are never blurred.
3. **Search after the independent round, then reopen ideation.** We did three
   search rounds and reopened generation after each kill.
4. **Adversarial review by someone who did not originate the idea.** A separate
   research agent wrote `adoption_and_grill.md` with a "why this should not be
   built" section.
5. **Do not auto-select a winner.** Scores are decision aids; feasibility and
   ethics gates remain controlling.
6. **Absence from a bounded search is not novelty.** We record search
   boundaries and say "no direct evidence located", never "never built".

## Gate
The upstream skill has a HARD-GATE requiring human approval of a design doc
before implementation. The operator explicitly waived it in the original
request ("start working until the work is done", "you are the boss and manager").
Per the skill's own exception, the gate goes with the opt-out. `PLAN.md` is the
written design doc and decision log in its place.

## Output produced
`PLAN.md` — independent candidate round, labelled claims, three evidence-backed
kills, decision matrix with raw scores and dissent, and the final design.
