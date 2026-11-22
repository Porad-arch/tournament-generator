"""Reading and writing the saved tournament (R8).

This file is the only place that touches the disk. It knows how to write a
Tournament down and read one back, and nothing about the terminal.

The file is plain JSON so you can open it in a text editor and see exactly what
the program is keeping.
"""

import json
import os

from tournament import Match, Tournament

DEFAULT_PATH = "tournament.json"
FORMAT_VERSION = 1


def to_dict(event):
    """The tournament as plain lists and dicts, ready for json.dump."""
    return {
        "version": FORMAT_VERSION,
        "name": event.name,
        "competitors": list(event.competitors),
        "rounds": [
            [
                {
                    "number": match.number,
                    "home": match.home,
                    "away": match.away,
                    "winner": match.winner,
                }
                for match in matches
            ]
            for matches in event.rounds
        ],
    }


def _match_from_row(row):
    """One saved match back into a Match, or ValueError saying what is wrong."""
    if not isinstance(row, dict):
        raise ValueError(f"a saved match is not a record: {row!r}")
    try:
        match = Match(
            number=int(row["number"]),
            home=row["home"],
            away=row.get("away"),
            winner=row.get("winner"),
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"a saved match is missing something: {row!r}") from None
    if match.winner is not None and match.winner not in match.names:
        raise ValueError(
            f"a saved match says {match.winner!r} won {match.label()!r}, "
            "but that name is not in it"
        )
    return match


def from_dict(data):
    """A saved file's contents back into a Tournament."""
    if not isinstance(data, dict):
        raise ValueError("the save file should hold a record, not a list or a number")
    if "name" not in data:
        raise ValueError("the save file has no tournament name")
    rounds = data.get("rounds") or []
    if not isinstance(rounds, list):
        raise ValueError("the saved rounds are not a list")
    return Tournament(
        name=data["name"],
        competitors=list(data.get("competitors") or []),
        rounds=[[_match_from_row(row) for row in matches] for matches in rounds],
    )


def save(event, path=DEFAULT_PATH):
    """Write the tournament to path. Returns the path written.

    It writes to a temporary file beside the real one and then renames it over
    the top. Renaming is a single step the operating system either does or does
    not do, so a crash halfway through cannot leave behind half a save file.
    """
    path = os.path.abspath(str(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(to_dict(event), handle, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
    return path


def load(path=DEFAULT_PATH):
    """Read the tournament back, or None when there is no save file yet."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from None
    return from_dict(data)
