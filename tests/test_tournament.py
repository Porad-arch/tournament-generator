"""Tests for the rules in tournament.py.

Each test name begins with the requirement it checks, so a failure points
straight at the requirement in problem.md that is no longer met.

Every draw is made with `random.Random(seed)` so the bracket is the same on
every run. A test that depended on real randomness would pass or fail by luck.
"""

import random

import pytest

from tournament import (
    Match,
    Tournament,
    draw_first_round,
    next_power_of_two,
    pair_winners,
)


def tournament_of(count, name="Autumn Cup"):
    """A tournament with `count` competitors named P1..Pn, not yet drawn."""
    event = Tournament(name)
    for number in range(1, count + 1):
        event.add_competitor(f"P{number}")
    return event


def drawn(count, seed=1, name="Autumn Cup"):
    """A tournament with the bracket already drawn from a fixed seed."""
    event = tournament_of(count, name)
    event.start(random.Random(seed))
    return event


def play_out(event, seed=0):
    """Decide every match until there is a champion. Winners picked by seed."""
    chooser = random.Random(seed)
    guard = 0
    while not event.is_complete:
        guard += 1
        assert guard < 100, "the tournament never finished"
        number = event.current_round_number()
        for match in list(event.pending_matches()):
            event.record_result(number, match.number, chooser.choice(match.names))
    return event


# --- R1. Allow the organizer to create a tournament with a custom name. ---


def test_r1_a_tournament_keeps_the_name_it_was_given():
    assert Tournament("Friday Night Smash").name == "Friday Night Smash"


def test_r1_the_name_has_its_whitespace_tidied():
    assert Tournament("  Spring   Open  ").name == "Spring Open"


def test_r1_refuses_a_name_that_is_empty_or_only_spaces():
    with pytest.raises(ValueError):
        Tournament("")
    with pytest.raises(ValueError):
        Tournament("   ")


# --- R2. Allow the organizer to add competitors to the tournament. ---


def test_r2_adds_competitors_and_keeps_the_order_entered():
    event = Tournament("Cup")
    event.add_competitor("Ann")
    event.add_competitor("Bob")
    assert event.competitors == ["Ann", "Bob"]


def test_r2_tidies_whitespace_in_a_competitor_name():
    event = Tournament("Cup")
    assert event.add_competitor("  Ann   Lee ") == "Ann Lee"
    assert event.competitors == ["Ann Lee"]


def test_r2_refuses_a_competitor_with_no_name():
    with pytest.raises(ValueError):
        Tournament("Cup").add_competitor("   ")


def test_r2_refuses_the_same_competitor_twice_whatever_the_capitals():
    event = Tournament("Cup")
    event.add_competitor("Ann")
    with pytest.raises(ValueError):
        event.add_competitor("ann")
    assert event.competitors == ["Ann"]


def test_r2_refuses_a_competitor_once_the_bracket_is_drawn():
    event = drawn(4)
    with pytest.raises(ValueError):
        event.add_competitor("Latecomer")


# --- R3. Generate a randomized single-elimination bracket. ---


def test_r3_every_competitor_appears_exactly_once_in_round_one():
    names = [f"P{n}" for n in range(1, 8)]
    first_round = draw_first_round(names, random.Random(3))
    drawn_names = [name for match in first_round for name in match.names]
    assert sorted(drawn_names) == sorted(names)


def test_r3_round_one_fills_half_the_bracket():
    for count in range(2, 18):
        event = drawn(count, seed=count)
        assert len(event.round(1)) == next_power_of_two(count) // 2


def test_r3_the_same_seed_draws_the_same_bracket():
    names = [f"P{n}" for n in range(1, 9)]
    first = [m.label() for m in draw_first_round(names, random.Random(7))]
    second = [m.label() for m in draw_first_round(names, random.Random(7))]
    assert first == second


def test_r3_different_seeds_draw_different_brackets():
    names = [f"P{n}" for n in range(1, 9)]
    openers = {
        draw_first_round(names, random.Random(seed))[0].label() for seed in range(30)
    }
    assert len(openers) > 1


def test_r3_refuses_a_tournament_with_fewer_than_two_competitors():
    with pytest.raises(ValueError):
        tournament_of(1).start(random.Random(1))
    with pytest.raises(ValueError):
        tournament_of(0).start(random.Random(1))


def test_r3_refuses_to_draw_the_bracket_twice():
    event = drawn(4)
    with pytest.raises(ValueError):
        event.start(random.Random(2))


def test_r3_a_knockout_halves_the_field_each_round():
    event = play_out(drawn(8))
    assert [len(matches) for matches in event.rounds] == [4, 2, 1]


# --- R4. Automatically assign byes when the bracket is not full. ---


def test_r4_a_full_bracket_needs_no_byes():
    for count in (2, 4, 8, 16):
        event = drawn(count, seed=count)
        assert event.byes == 0
        assert [m for m in event.round(1) if m.is_bye] == []


def test_r4_five_competitors_get_three_byes():
    event = drawn(5)
    assert event.bracket_size == 8
    assert event.byes == 3
    assert len([m for m in event.round(1) if m.is_bye]) == 3


def test_r4_the_number_of_byes_fills_the_bracket_at_every_size():
    for count in range(2, 18):
        event = drawn(count, seed=count)
        assert event.byes == next_power_of_two(count) - count
        assert len([m for m in event.round(1) if m.is_bye]) == event.byes


def test_r4_a_bye_is_already_won_by_whoever_got_it():
    event = drawn(3)
    (bye,) = [m for m in event.round(1) if m.is_bye]
    assert bye.is_decided
    assert bye.winner == bye.home


def test_r4_a_bye_has_no_result_to_enter():
    event = drawn(3)
    (bye,) = [m for m in event.round(1) if m.is_bye]
    with pytest.raises(ValueError):
        event.record_result(1, bye.number, bye.home)


def test_r4_a_bye_is_not_waiting_on_the_organizer():
    event = drawn(5)
    assert all(not match.is_bye for match in event.pending_matches())


# --- R5. Display the matchups for each round. ---


def test_r5_a_round_lists_its_matchups():
    event = drawn(4)
    matchups = event.round(1)
    assert len(matchups) == 2
    assert all(match.away is not None for match in matchups)
    assert [match.number for match in matchups] == [1, 2]


def test_r5_a_matchup_reads_as_two_names():
    assert Match(1, "Ann", "Bob").label() == "Ann vs Bob"


def test_r5_a_bye_says_so():
    assert Match(1, "Ann").label() == "Ann (bye)"


def test_r5_asking_for_a_round_that_does_not_exist_is_refused():
    event = drawn(4)
    with pytest.raises(ValueError):
        event.round(2)
    with pytest.raises(ValueError):
        event.round(0)


def test_r5_asking_for_a_round_before_the_draw_is_refused():
    with pytest.raises(ValueError):
        tournament_of(4).round(1)


def test_r5_the_current_round_is_the_first_one_still_undecided():
    event = drawn(4)
    assert event.current_round_number() == 1
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    assert event.current_round_number() == 1, "one match is still open"
    event.record_result(1, second.number, second.home)
    assert event.current_round_number() == 2


def test_r5_a_finished_tournament_has_no_current_round():
    event = play_out(drawn(4))
    assert event.current_round_number() is None
    assert event.pending_matches() == []


# --- R6. Enter match results and advance winners to the next round. ---


def test_r6_recording_a_result_sets_the_winner():
    event = drawn(4)
    match = event.round(1)[0]
    event.record_result(1, match.number, match.away)
    assert match.winner == match.away
    assert match.is_decided


def test_r6_the_winners_make_up_the_next_round():
    event = drawn(4)
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    event.record_result(1, second.number, second.away)
    assert event.round_count == 2
    (final,) = event.round(2)
    assert final.names == [first.home, second.away]


def test_r6_the_next_round_waits_until_the_round_is_finished():
    event = drawn(4)
    first = event.round(1)[0]
    event.record_result(1, first.number, first.home)
    assert event.round_count == 1


def test_r6_refuses_a_winner_who_is_not_in_that_match():
    event = drawn(4)
    match = event.round(1)[0]
    with pytest.raises(ValueError):
        event.record_result(1, match.number, "Someone Else")
    assert match.winner is None


def test_r6_accepts_the_winner_however_it_is_capitalised():
    event = drawn(4)
    match = event.round(1)[0]
    event.record_result(1, match.number, match.home.lower())
    assert match.winner == match.home


def test_r6_refuses_to_record_the_same_match_twice():
    event = drawn(4)
    match = event.round(1)[0]
    event.record_result(1, match.number, match.home)
    with pytest.raises(ValueError):
        event.record_result(1, match.number, match.away)
    assert match.winner == match.home


def test_r6_refuses_a_match_number_that_is_not_in_the_round():
    event = drawn(4)
    with pytest.raises(ValueError):
        event.record_result(1, 99, "P1")


def test_r6_pairing_an_unfinished_round_is_refused():
    with pytest.raises(ValueError):
        pair_winners([Match(1, "Ann", "Bob"), Match(2, "Cy", "Di")])


# --- R7. Display the tournament champion once all matches are completed. ---


def test_r7_there_is_no_champion_before_the_draw():
    assert tournament_of(4).champion is None


def test_r7_there_is_no_champion_while_matches_are_open():
    event = drawn(4)
    assert event.champion is None
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    event.record_result(1, second.number, second.home)
    assert event.round_count == 2
    assert event.champion is None, "the final has not been played"
    assert event.is_complete is False


def test_r7_the_champion_is_whoever_wins_the_final():
    event = drawn(4)
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    event.record_result(1, second.number, second.home)
    (final,) = event.round(2)
    event.record_result(2, final.number, final.away)
    assert event.champion == final.away
    assert event.is_complete is True


def test_r7_every_size_plays_through_to_exactly_one_champion():
    for count in range(2, 18):
        event = play_out(drawn(count, seed=count), seed=count)
        assert event.champion in event.competitors
        assert len(event.rounds[-1]) == 1


def test_r7_the_number_of_rounds_matches_the_bracket_size():
    expected = {2: 1, 3: 2, 4: 2, 5: 3, 8: 3, 9: 4, 16: 4, 17: 5}
    for count, rounds in expected.items():
        event = play_out(drawn(count, seed=count), seed=count)
        assert event.round_count == rounds, f"{count} competitors"
