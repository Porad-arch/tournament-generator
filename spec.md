# Spec

How the program meets the requirements in `problem.md`. Updated each round.

## Round 1

### Shape of the code

| File | Holds | Tested |
|---|---|---|
| `tournament.py` | All rules: competitors, the draw, byes, results, the champion | Yes |
| `storage.py` | Reading and writing the save file | Yes |
| `main.py` | Argument parsing and printing only | No — presentation |
| `tests/` | One test file per module, each test named for a requirement ID | — |

`tournament.py` never opens a file, never prints, and never calls `random`
directly: anything that shuffles takes an `rng`, so a test passes
`random.Random(7)` and gets the same bracket every run. `main.py` holds no
rules.

### How each requirement is met

- **R1** — `Tournament(name)` stores the name, collapsing extra whitespace, and
  raises `ValueError` if it is empty or only spaces.
- **R2** — `add_competitor(name)` appends one competitor. It refuses a blank
  name, a repeat (compared ignoring case, so `ann` cannot join `Ann`), and
  anyone added after the bracket is drawn.
- **R3** — `start(rng)` shuffles the competitors and calls `draw_first_round`.
  Single elimination: `pair_winners` builds each later round from the winners of
  the one before, so the field halves every round until one is left.
- **R4** — the bracket size is the next power of two at or above the number of
  competitors, and the leftover slots become byes. Byes go to the competitors
  drawn first, which, because the draw is already shuffled, is the same as
  handing them out at random. A bye has `away = None` and its winner is set the
  moment it is drawn, so the organizer is never asked to decide it. See
  `docs/decisions/0001-byes-go-to-the-first-names-drawn.md`.
- **R5** — `round(n)` returns that round's matches, each with a `label()` that
  reads `Ann vs Bob` or `Ann (bye)`. `current_round_number()` is the earliest
  round still waiting on a result, and `pending_matches()` lists exactly what
  the organizer still has to enter.
- **R6** — `record_result(round, match, winner)` sets the winner. The name has
  to be one of the two in that match, which stops a typo inventing a competitor;
  capitalisation does not matter. Recording the same match twice, recording a
  bye, or naming a match that is not in the round are all refused. When the last
  match of a round is decided, the next round is built immediately.
- **R7** — `champion` is the winner of the final once the last round has one
  decided match, and `None` until then. `is_complete` says the same thing as a
  yes or no.
- **R8** — `storage.save(tournament, path)` writes the whole thing as JSON and
  `storage.load(path)` reads it back, including part-played rounds. `main.py`
  loads before each command and saves after anything that changes.

### Worked example: five competitors

Five names need a bracket of **8**, so there are **3 byes**.

| Round | Matches | Of which byes |
|---|---|---|
| 1 | 4 | 3 |
| 2 | 2 | 0 |
| 3 (final) | 1 | 0 |

Round 1 has four matches because a bracket of 8 has four first-round slots. Three
are byes, decided on the spot, so the organizer enters **one** result in round 1,
then two in round 2, then the final. The same arithmetic holds at every size:
round 1 always has `bracket_size / 2` matches and `bracket_size - competitors`
of them are byes.

### Running it

    python3 main.py new "Autumn Cup" -c Ann -c Bob -c Cy
    python3 main.py start
    python3 main.py show
    python3 main.py result 1 2 Bob
    python3 -m pytest

### Out of scope in round 1

- Double elimination, round robin, Swiss, or group stages.
- Seeding or ranking competitors; the draw is purely random.
- Scores or game counts: a match records who won, not by how much.
- Editing or undoing a result once entered.
- More than one tournament in a save file at a time.
- Any web page, graphics, or printed bracket diagram.
