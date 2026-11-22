# 0001. Byes go to the first names drawn

Date: 2026-11-21

## Status

Accepted.

## Decision

In the context of **a single-elimination bracket whose competitor count is not a
power of two**,
facing **the need to fill the leftover slots so that every later round halves a
full field**,
we decided for **sizing the bracket to the next power of two, then giving a bye
to each of the first competitors in the shuffled draw**,
and neglected **padding the field with placeholder "BYE" competitors** and
**awarding byes to the highest seeds**,
to achieve **a bracket where every round after the first is exactly half the
one before, and where byes are already decided so the organizer is never asked
to enter them**,
accepting **that byes are handed out at random rather than as a reward for
ranking, and that round 1 contains matches that need no result**.

## Why not placeholder competitors

The obvious fix is to pad the competitor list with fake entrants called `BYE`
until it reaches a power of two, then draw normally. It makes the draw code
simpler — every match has two sides. It was rejected because the fakes then leak
everywhere else: `competitors` would contain names nobody entered, the display
has to special-case printing `Ann vs BYE`, `record_result` has to refuse a
result where the winner is a placeholder, and a saved file would contain
competitors that do not exist. One simplification in the draw would be paid for
in four other places.

Representing a bye as `away = None` keeps it honest: the match genuinely has one
side, `is_bye` says so, and `label()` prints `Ann (bye)`.

## Why not seeded byes

In real tournaments a bye is usually a reward: the strongest competitors sit out
the first round. That requires seeding, and R3 says the bracket is **randomized**
— there is no ranking in the program to seed from. Inventing one would be adding
a requirement nobody asked for. Because the draw is shuffled before byes are
handed out, "the first names drawn" is already random, so this is the simplest
thing that satisfies R3 and R4 together.

If a later round adds seeding, this record is the one to revisit: the bye
assignment is a single slice in `draw_first_round` and would become a seeded
pick.

## Consequences

- `bracket_size` is always a power of two, and `byes` is always
  `bracket_size - len(competitors)`. A test asserts this at every size from 2 to
  17.
- Byes are always fewer than half the bracket, so round 1 can never consist only
  of byes. `_advance_if_round_finished` loops anyway, which keeps `start()`
  correct if the draw ever changes.
- A bye's winner is set when the bracket is drawn, so `pending_matches()` only
  ever lists matches a human has to decide.
- Round 1 holds `bracket_size / 2` matches, some of which need no action. That
  is visible in the display, which marks them "bye, straight through".
