"""Tests for the Markdown GM key of utils/dungeon_key.py

Run with: python -m pytest tests
"""

import logging

import pytest

from dungeon_fx11 import D24, D30, DCombined
from tests.test_dungeon_json import GOAL, KEY, LEVER, START, graph
from utils.dungeon_json import dungeon_json
from utils.dungeon_key import dungeon_key

logging.disable(logging.CRITICAL)


def key_lines(g, meta=None):
    return dungeon_key(dungeon_json(g, meta)).splitlines()


def test_rooms_are_numbered_from_start_with_their_exits():
    g = graph(
        [
            START,
            GOAL,
            ("lock", "Use spam key 1", [KEY]),
            ("key", "Get spam key 1", [KEY]),
            ("e", "e", None),
        ],
        [(0, 3), (0, 4), (4, 2), (2, 1)],
    )

    lines = key_lines(g, {"grammar": "Combined", "seed": 42, "size": "S"})

    assert lines[0] == "# GM key: Combined dungeon"
    assert "Seed 42 · size S · 4 rooms · solvable" in lines
    assert "1. **Entrance (START)**. Exits: 2, 3" in lines
    assert "2. **Pickup: spam key 1**. Exits: 1" in lines
    assert "3. **Enemy**. Exits: 1, 4 (locked: spam key 1)" in lines
    assert "4. **Dungeon goal (GOAL)**. Exits: 3 (locked: spam key 1)" in lines
    assert "| spam key 1 | 2 | 3 ↔ 4 |" in lines


def test_one_way_and_secret_exits():
    g = graph(
        [START, GOAL, ("t", "t", None), ("s", "secret", None), ("gb: bombs", "gb: bombs", None)],
        [(0, 2), (2, 1), (0, 3), (3, 4)],
        oneway=[True, False, False, False],
    )

    lines = key_lines(g)

    assert "1. **Entrance (START)**. Exits: 2 (one-way), 3 (secret)" in lines
    assert "2. **Trap**. Exits: 4" in lines
    assert "3. **Bonus goal: bombs**. Exits: 1 (secret)" in lines
    assert "4. **Dungeon goal (GOAL)**. Exits: 2" in lines
    assert not any(line.startswith("| ") for line in lines)


def test_lever_opens_both_positions():
    g = graph(
        [
            START,
            GOAL,
            ("lever", "lever 1", [LEVER]),
            ("gate", "Check lever 1 ON", [LEVER]),
            ("gate", "Check lever 1 OFF", [LEVER]),
            ("gb: rupees", "gb: rupees", None),
        ],
        [(0, 2), (0, 3), (3, 1), (0, 4), (4, 5)],
    )

    lines = key_lines(g)

    assert (
        "1. **Entrance (START)**. Exits: 2 (lever 1 ON), 3, 4 (lever 1 OFF, open at start)" in lines
    )
    assert "3. **Lever: lever 1 (starts OFF)**. Exits: 1" in lines
    assert "| lever 1 | 3 | 1 ↔ 2 (ON), 1 ↔ 4 (OFF) |" in lines


def test_unsolvable_dungeon_is_flagged():
    g = graph([START, GOAL, ("lock", "Use spam key 1", [KEY])], [(0, 2), (2, 1)])

    lines = key_lines(g)

    assert "2 rooms · **unsolvable**" in lines
    assert "- GOAL unreachable" in lines
    assert "| spam key 1 | none | 1 ↔ 2 |" in lines


@pytest.mark.parametrize("cls", [D24, D30, DCombined])
def test_generated_dungeons_key(cls, tmp_path):
    for seed in range(1, 31):
        target = tmp_path / f"{cls.NAME}_{seed}.md"
        cls(seed=seed, key=target)
        text = target.read_text()
        rooms = [line for line in text.splitlines() if line[:1].isdigit()]
        assert text.startswith(f"# GM key: {cls.NAME} dungeon")
        assert all(f"{number}. " in line for number, line in enumerate(rooms, 1))
        assert all("Exits: " in line for line in rooms)
