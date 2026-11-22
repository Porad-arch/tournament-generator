"""The command line.

This file holds no rules. It parses arguments, loads the save file, calls
tournament.py, saves, and prints. That is why there are no tests for it:
everything worth testing lives in tournament.py and storage.py.

    python3 main.py new "Autumn Cup" -c Ann -c Bob -c Cy
    python3 main.py start
    python3 main.py show
    python3 main.py result 1 2 Bob
"""

import argparse
import os
import random
import sys

import storage
from tournament import Tournament


class Failure(Exception):
    """Something the person can fix, reported without a stack trace."""


# --- printing ---


def describe_match(match):
    if match.is_bye:
        state = "bye, straight through"
    elif match.is_decided:
        state = f"won by {match.winner}"
    else:
        state = "to play"
    return f"  {match.number}. {match.label():<34} {state}"


def describe_round(event, number):
    print(f"Round {number} of {event.round_count}")
    for match in event.round(number):
        print(describe_match(match))


def show(event, every_round=False):
    """R5, R7. Print where the tournament stands."""
    print(event.name)
    if not event.competitors:
        print("No competitors yet. Add some with: add <name> [<name> ...]")
        return
    print(
        f"{len(event.competitors)} competitors, "
        f"bracket of {event.bracket_size}, "
        f"{event.byes} bye{'' if event.byes == 1 else 's'}"
    )

    if not event.has_started:
        for position, name in enumerate(event.competitors, start=1):
            print(f"  {position}. {name}")
        print("\nBracket not drawn yet. Draw it with: start")
        return

    print()
    current = event.current_round_number()
    numbers = range(1, event.round_count + 1) if every_round else [current or event.round_count]
    for number in numbers:
        describe_round(event, number)

    if event.is_complete:
        print(f"\nChampion: {event.champion}")
    else:
        waiting = len(event.pending_matches())
        print(
            f"\n{waiting} match{'' if waiting == 1 else 'es'} to play. "
            "Record one with: result <round> <match> <winner>"
        )


# --- the subcommands ---


def command_new(args):
    """R1, R2. Start a new tournament."""
    if os.path.exists(args.file) and not args.force:
        raise Failure(
            f"{args.file} already holds a tournament. "
            "Pass --force to replace it, or --file to use another file."
        )
    event = Tournament(args.name)
    for name in args.competitor:
        event.add_competitor(name)
    storage.save(event, args.file)
    print(f"Created {event.name!r} in {args.file}")
    show(event)


def command_add(args):
    """R2. Add competitors."""
    event = load_or_fail(args.file)
    for name in args.name:
        print(f"Added {event.add_competitor(name)}")
    storage.save(event, args.file)
    show(event)


def command_start(args):
    """R3, R4. Draw the bracket."""
    event = load_or_fail(args.file)
    rng = random.Random(args.seed) if args.seed is not None else None
    event.start(rng)
    storage.save(event, args.file)
    print(f"Bracket drawn for {event.name!r}.\n")
    show(event)


def command_show(args):
    """R5, R7."""
    show(load_or_fail(args.file), every_round=args.all)


def command_result(args):
    """R6. Record one match result."""
    event = load_or_fail(args.file)
    match = event.record_result(args.round, args.match, " ".join(args.winner))
    storage.save(event, args.file)
    print(f"Round {args.round} match {args.match}: {match.winner} wins.\n")
    show(event)


def load_or_fail(path):
    event = storage.load(path)
    if event is None:
        raise Failure(f'No tournament saved at {path}. Start one with: new "My Cup"')
    return event


# --- wiring ---


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python3 main.py",
        description="Run a single-elimination tournament from the command line.",
    )
    parser.add_argument(
        "--file",
        default=storage.DEFAULT_PATH,
        help=f"where the tournament is saved (default: {storage.DEFAULT_PATH})",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new", help="start a new tournament")
    new.add_argument("name", help="what the tournament is called")
    new.add_argument(
        "-c", "--competitor", action="append", default=[], help="add a competitor (repeatable)"
    )
    new.add_argument("--force", action="store_true", help="replace an existing save file")
    new.set_defaults(run=command_new)

    add = commands.add_parser("add", help="add competitors")
    add.add_argument("name", nargs="+", help="one or more competitor names")
    add.set_defaults(run=command_add)

    start = commands.add_parser("start", help="draw the bracket")
    start.add_argument("--seed", type=int, help="draw the same bracket every time")
    start.set_defaults(run=command_start)

    show_command = commands.add_parser("show", help="show where things stand")
    show_command.add_argument("--all", action="store_true", help="show every round")
    show_command.set_defaults(run=command_show)

    result = commands.add_parser("result", help="record a match result")
    result.add_argument("round", type=int)
    result.add_argument("match", type=int)
    result.add_argument("winner", nargs="+", help="the winner's name")
    result.set_defaults(run=command_result)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.run(args)
    except (Failure, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
