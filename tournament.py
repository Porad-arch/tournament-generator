"""The rules: competitors, the bracket draw, byes, results, and the champion.

Nothing in this file reads input, prints, opens a file, or touches the network.
Every rule is a method or function you can call from a test and look at what
comes back. The terminal interface lives in main.py and the save file in
storage.py.

Anything random takes an optional `rng`, so a test can hand it
`random.Random(7)` and get the same draw every time.
"""

import random
from dataclasses import dataclass, field

MINIMUM_COMPETITORS = 2


def clean_text(value):
    """Collapse the whitespace in something typed, so ' Ann  Lee ' is 'Ann Lee'."""
    return " ".join(str(value).split())


def next_power_of_two(count):
    """The smallest bracket size that holds `count` competitors: 5 -> 8."""
    if count < 1:
        raise ValueError("a bracket needs at least one competitor")
    size = 1
    while size < count:
        size *= 2
    return size


@dataclass
class Match:
    """One matchup. `away` is None when this is a bye.

    A bye is already decided the moment it is drawn, so its winner is set when
    the bracket is built and there is nothing for the organizer to enter.
    """

    number: int
    home: str
    away: str = None
    winner: str = None

    @property
    def is_bye(self):
        return self.away is None

    @property
    def is_decided(self):
        return self.winner is not None

    @property
    def names(self):
        """Who is in this match, one name for a bye and two otherwise."""
        return [self.home] if self.is_bye else [self.home, self.away]

    def label(self):
        """'Ann vs Bob', or 'Ann (bye)'."""
        return f"{self.home} (bye)" if self.is_bye else f"{self.home} vs {self.away}"


def draw_first_round(competitors, rng=None):
    """Shuffle the competitors and build round 1, byes included (R3, R4).

    The bracket size is the next power of two at or above the number of
    competitors. Whatever is left over becomes byes, and the byes go to the
    competitors drawn first. Because the draw is shuffled, that is the same as
    handing them out at random.
    """
    if len(competitors) < MINIMUM_COMPETITORS:
        raise ValueError(
            f"a tournament needs at least {MINIMUM_COMPETITORS} competitors, "
            f"and this one has {len(competitors)}"
        )
    order = list(competitors)
    (rng or random).shuffle(order)

    byes = next_power_of_two(len(order)) - len(order)
    matches = []
    # The competitors drawn first sit the round out and go straight through.
    for name in order[:byes]:
        matches.append(Match(number=len(matches) + 1, home=name, winner=name))
    # Everyone else is paired off two at a time.
    remaining = order[byes:]
    for first, second in zip(remaining[0::2], remaining[1::2]):
        matches.append(Match(number=len(matches) + 1, home=first, away=second))
    return matches


def pair_winners(previous_round):
    """Build the next round from the winners of the one before it."""
    names = [match.winner for match in previous_round]
    if any(name is None for name in names):
        raise ValueError("that round is not finished yet")
    return [
        Match(number=index + 1, home=first, away=second)
        for index, (first, second) in enumerate(zip(names[0::2], names[1::2]))
    ]


@dataclass
class Tournament:
    """A named tournament, its competitors, and its rounds once drawn."""

    name: str
    competitors: list = field(default_factory=list)
    rounds: list = field(default_factory=list)

    def __post_init__(self):
        # R1. A tournament has to be called something.
        self.name = clean_text(self.name)
        if not self.name:
            raise ValueError("the tournament needs a name")

    # --- competitors (R2) ---

    @property
    def has_started(self):
        return bool(self.rounds)

    def add_competitor(self, name):
        """Add one competitor. Refuses blanks, repeats, and late entries."""
        if self.has_started:
            raise ValueError("the bracket is already drawn, so nobody else can be added")
        name = clean_text(name)
        if not name:
            raise ValueError("a competitor needs a name")
        if any(existing.casefold() == name.casefold() for existing in self.competitors):
            raise ValueError(f"{name} is already in this tournament")
        self.competitors.append(name)
        return name

    # --- the draw (R3, R4) ---

    def start(self, rng=None):
        """Draw the bracket. Returns round 1."""
        if self.has_started:
            raise ValueError("the bracket has already been drawn")
        self.rounds = [draw_first_round(self.competitors, rng)]
        self._advance_if_round_finished()
        return self.rounds[0]

    @property
    def bracket_size(self):
        """The power of two this bracket was built to fill."""
        return next_power_of_two(len(self.competitors))

    @property
    def byes(self):
        """How many competitors got a free pass through round 1."""
        return self.bracket_size - len(self.competitors)

    # --- showing the bracket (R5) ---

    @property
    def round_count(self):
        return len(self.rounds)

    def round(self, number):
        """One round by its 1-based number."""
        if not self.has_started:
            raise ValueError("the bracket has not been drawn yet")
        if not 1 <= number <= len(self.rounds):
            raise ValueError(
                f"there is no round {number}; this tournament is on round "
                f"{len(self.rounds)}"
            )
        return self.rounds[number - 1]

    def current_round_number(self):
        """The earliest round still waiting on a result, or None when finished."""
        for index, matches in enumerate(self.rounds, start=1):
            if any(not match.is_decided for match in matches):
                return index
        return None

    def pending_matches(self):
        """Every match still waiting on a result, in the current round."""
        number = self.current_round_number()
        return [] if number is None else [m for m in self.round(number) if not m.is_decided]

    # --- results (R6) ---

    def record_result(self, round_number, match_number, winner):
        """Set the winner of one match and advance it. Returns the Match.

        The winner has to be one of the two names in that match, which is what
        stops a typo quietly creating a competitor who was never entered.
        """
        matches = self.round(round_number)
        for match in matches:
            if match.number == match_number:
                break
        else:
            raise ValueError(f"round {round_number} has no match {match_number}")

        if match.is_bye:
            raise ValueError(f"match {match_number} is a bye; {match.home} is already through")
        if match.is_decided:
            raise ValueError(
                f"match {match_number} is already recorded, won by {match.winner}"
            )

        wanted = clean_text(winner)
        for name in match.names:
            if name.casefold() == wanted.casefold():
                match.winner = name
                break
        else:
            raise ValueError(f"{wanted!r} is not in match {match_number}: {match.label()}")

        self._advance_if_round_finished()
        return match

    def _advance_if_round_finished(self):
        """Build the next round once the last one is fully decided.

        A loop rather than a single step: a round that arrived already decided
        would finish the next one immediately. That cannot happen with the
        current draw, because byes are always fewer than half the bracket, but
        it keeps this correct if the draw ever changes.
        """
        while len(self.rounds[-1]) > 1 and all(m.is_decided for m in self.rounds[-1]):
            self.rounds.append(pair_winners(self.rounds[-1]))

    # --- the champion (R7) ---

    @property
    def champion(self):
        """The winner of the final, or None while anything is undecided."""
        if not self.has_started:
            return None
        final = self.rounds[-1]
        if len(final) == 1 and final[0].is_decided:
            return final[0].winner
        return None

    @property
    def is_complete(self):
        return self.champion is not None
