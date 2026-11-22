# tournament-generator

A command-line single-elimination tournament manager. Standing rules for every
session in this repo.

## Read these first

`problem.md` (the problem and the numbered requirements), `spec.md` (how the code
meets them), `docs/decisions/` (why things are the way they are), and the newest
`handoff-round-<N>.md` if one exists.

## Commands

    python3 main.py --help     # the subcommands
    python3 -m pytest          # run the tests

## How this repo works

- **Requirements come first.** `problem.md` holds numbered requirements R1, R2,
  … Numbers are never reused. A changed requirement keeps its number and says
  what changed; a removed one stays in the file, marked removed.
- **Rules are separate from input and output.** Everything testable lives in
  `tournament.py` as plain objects and functions. `storage.py` only reads and
  writes the save file. `main.py` only parses arguments and prints. Do not put a
  rule in `main.py`.
- **Randomness is injectable.** Anything that shuffles takes an optional `rng`,
  so a test can pass `random.Random(seed)` and get the same bracket every time.
  Never call `random` directly inside a rule.
- **Every requirement is named in a test.** Test names start with the
  requirement ID, for example `test_r4_...`. When a requirement changes, its
  tests change with it in the same round.
- **Tests must actually run.** A skipped test has not passed. Nothing may be
  added that cannot run with `python3 -m pytest`.
- **No API keys, no logins, no paid services, no network.** Everything is local
  files and the terminal.

## Commits

- Small steps, one change per commit.
- The message says what changed and why. Never `update`, `fix`, or `wip`.
- **Never undo or amend a commit**, and never force-push.
- Push at the end of each working session.

## Never commit

Saved tournaments (`tournament.json`), transcripts (`.jsonl`), API keys or
passwords, `.venv`, `__pycache__`, `node_modules`, or personal information. This
repository is public.

## Each round

Requirements into `problem.md` first and pushed before anything else. Then
update `spec.md`, write tests for every new or changed requirement, implement
until all tests pass including the old ones, and add a decision record in
`docs/decisions/` as a Y-statement for a decision that had real alternatives.
