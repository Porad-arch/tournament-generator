# tournament-generator

A command-line tool for running a small single-elimination tournament. Enter the
competitors, draw a random bracket, type in results as matches finish, and it
works out who plays next and who won the whole thing.

Byes are handled for you: if you have five competitors, it builds a bracket of
eight and gives three of them a free pass through round 1, so you never have to
work out the pairings by hand.

Everything is saved to a local JSON file. No accounts, no network, no sign-in.

## Run it

    python3 main.py --help

A whole tournament looks like this:

    python3 main.py new "Autumn Cup" -c Ann -c Bob -c "Cy Diaz" -c Dee
    python3 main.py add Eve
    python3 main.py start
    python3 main.py show
    python3 main.py result 1 4 Ann
    python3 main.py show --all

`show` prints the round you are on; `show --all` prints the whole bracket.
`result <round> <match> <winner>` takes the numbers printed next to each match.
Capitalisation of the winner's name does not matter, but it has to be someone
actually in that match.

Requires Python 3. Nothing to install.

## Run the tests

    python3 -m pytest

54 tests, each named for the requirement it checks, so a failure tells you which
requirement in `problem.md` is no longer met. Requires `pytest`
(`python3 -m pip install pytest`).

## The subcommands

| Command | What it does |
|---|---|
| `new NAME` | Start a tournament. `-c NAME` adds a competitor, repeatable. `--force` replaces an existing save |
| `add NAME...` | Add competitors, until the bracket is drawn |
| `start` | Shuffle and draw the bracket. `--seed N` draws the same one every time |
| `show` | The current round. `--all` for every round |
| `result R M WINNER` | Record the winner of match `M` in round `R` |

`--file PATH` puts the save somewhere other than `tournament.json`, which is
handy for running two tournaments or for trying things out.

## How it is laid out

- `tournament.py` — the rules: competitors, the draw, byes, results, the
  champion. No file access, no printing, and it never calls `random` directly.
- `storage.py` — the only file that touches the disk.
- `main.py` — the command line: argument parsing and printing, no rules.
- `tests/` — one test file per module; each test is named for the requirement
  it checks.
- `problem.md` — who this is for and the numbered requirements.
- `spec.md` — how the code meets them.
- `docs/decisions/` — why things are the way they are.

## One thing worth knowing

The bracket is always sized to a power of two — 2, 4, 8, 16 — and the leftover
slots become byes. That is what makes every round after the first exactly half
the one before it, so the tournament always ends with one final and one
champion. Seven competitors means a bracket of eight and one bye; nine means a
bracket of sixteen and seven byes. The reasoning, and the two approaches that
were rejected, is in
[docs/decisions/0001-byes-go-to-the-first-names-drawn.md](docs/decisions/0001-byes-go-to-the-first-names-drawn.md).
