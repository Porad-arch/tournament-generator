"""Tests for the save file.

R8. Save and load tournament progress using local files.

`tmp_path` is a fresh empty directory pytest hands each test, so these never
touch a real tournament.json.
"""

import json
import random

import pytest

import storage
from tournament import Tournament


def drawn(count=5, seed=1, name="Autumn Cup"):
    event = Tournament(name)
    for number in range(1, count + 1):
        event.add_competitor(f"P{number}")
    event.start(random.Random(seed))
    return event


def test_r8_loading_a_file_that_is_not_there_returns_nothing(tmp_path):
    assert storage.load(tmp_path / "no-such-file.json") is None


def test_r8_saving_then_loading_gives_back_the_same_tournament(tmp_path):
    path = tmp_path / "tournament.json"
    original = drawn()
    storage.save(original, path)
    assert storage.load(path) == original


def test_r8_the_name_and_competitors_survive_the_round_trip(tmp_path):
    path = tmp_path / "tournament.json"
    storage.save(drawn(name="Friday Night Smash"), path)
    reloaded = storage.load(path)
    assert reloaded.name == "Friday Night Smash"
    assert sorted(reloaded.competitors) == ["P1", "P2", "P3", "P4", "P5"]


def test_r8_byes_come_back_as_byes(tmp_path):
    path = tmp_path / "tournament.json"
    original = drawn(5)
    storage.save(original, path)
    reloaded = storage.load(path)
    assert reloaded.byes == 3
    assert len([m for m in reloaded.round(1) if m.is_bye]) == 3
    assert all(m.winner == m.home for m in reloaded.round(1) if m.is_bye)


def test_r8_a_part_played_tournament_comes_back_part_played(tmp_path):
    path = tmp_path / "tournament.json"
    event = drawn(4)
    first = event.round(1)[0]
    event.record_result(1, first.number, first.home)
    storage.save(event, path)

    reloaded = storage.load(path)
    assert reloaded.round(1)[0].winner == first.home
    assert reloaded.round(1)[1].winner is None
    assert reloaded.current_round_number() == 1
    assert len(reloaded.pending_matches()) == 1


def test_r8_the_bracket_can_be_carried_on_after_reloading(tmp_path):
    path = tmp_path / "tournament.json"
    event = drawn(4)
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    storage.save(event, path)

    reloaded = storage.load(path)
    reloaded.record_result(1, second.number, second.home)
    assert reloaded.round_count == 2
    (final,) = reloaded.round(2)
    reloaded.record_result(2, final.number, final.home)
    assert reloaded.champion == final.home


def test_r8_a_finished_tournament_comes_back_with_its_champion(tmp_path):
    path = tmp_path / "tournament.json"
    event = drawn(4)
    first, second = event.round(1)
    event.record_result(1, first.number, first.home)
    event.record_result(1, second.number, second.home)
    (final,) = event.round(2)
    event.record_result(2, final.number, final.away)
    storage.save(event, path)

    reloaded = storage.load(path)
    assert reloaded.is_complete
    assert reloaded.champion == final.away


def test_r8_saving_an_undrawn_tournament_keeps_the_competitors(tmp_path):
    path = tmp_path / "tournament.json"
    event = Tournament("Early Days")
    event.add_competitor("Ann")
    event.add_competitor("Bob")
    storage.save(event, path)

    reloaded = storage.load(path)
    assert reloaded.has_started is False
    assert reloaded.competitors == ["Ann", "Bob"]
    reloaded.start(random.Random(1))
    assert len(reloaded.round(1)) == 1


def test_r8_the_save_file_is_plain_readable_json(tmp_path):
    path = tmp_path / "tournament.json"
    storage.save(drawn(4, name="Autumn Cup"), path)
    data = json.loads(path.read_text())
    assert data["version"] == storage.FORMAT_VERSION
    assert data["name"] == "Autumn Cup"
    assert len(data["rounds"]) == 1
    assert len(data["rounds"][0]) == 2


def test_r8_saving_leaves_no_temporary_file_behind(tmp_path):
    storage.save(drawn(), tmp_path / "tournament.json")
    storage.save(drawn(), tmp_path / "tournament.json")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["tournament.json"]


def test_r8_refuses_a_file_that_is_not_json(tmp_path):
    path = tmp_path / "tournament.json"
    path.write_text("this is not json at all")
    with pytest.raises(ValueError):
        storage.load(path)


def test_r8_refuses_a_save_whose_winner_is_not_in_the_match(tmp_path):
    path = tmp_path / "tournament.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "name": "Rigged Cup",
                "competitors": ["Ann", "Bob"],
                "rounds": [
                    [{"number": 1, "home": "Ann", "away": "Bob", "winner": "Nobody"}]
                ],
            }
        )
    )
    with pytest.raises(ValueError):
        storage.load(path)


def test_r8_refuses_a_save_with_no_tournament_name(tmp_path):
    path = tmp_path / "tournament.json"
    path.write_text(json.dumps({"version": 1, "competitors": [], "rounds": []}))
    with pytest.raises(ValueError):
        storage.load(path)
