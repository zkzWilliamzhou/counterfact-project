# Protocol: stop-slop (adapted)

Source: `hardikpandya/stop-slop` (fetched from GitHub)
Full vendored text: `skills/vendor/stop-slop.SKILL.md` and
`skills/vendor/stop-slop.README.md`

## Applied to this repository
All user-facing prose (README, docs, reports, commit messages) is checked
against this list before it ships:

- No "revolutionary", "game-changing", "seamless", "effortless", "cutting-edge",
  "empower", "unleash", "in today's fast-paced world".
- No throat-clearing ("In this document we will…", "It is important to note
  that…"). Lead with the claim.
- No vague intensity ("powerful", "robust", "truly make a difference") without
  a number, a mechanism, or a falsifiable statement next to it.
- No fake certainty. "Proves", "guarantees", "100%", "never fails" are replaced
  with the measurable claim and its scope boundary.
- No bullet lists of three adjectives where one verb would do.
- No stock conclusion ("the future looks bright"). End with a limitation or a
  next action.
- Every marketing sentence about causality is followed by the scope notice.

## Concrete outcomes in this repo
- README opens with a mechanism, not a superlative, and states the epistemic
  boundary in the first ten lines.
- The scope notice is printed in **every** renderer, including SARIF and JSON.
- The 105k-star target is explicitly reframed as an aspiration, not a spec.
- `REVIEW.md` reports failures and revisions rather than a victory lap.
