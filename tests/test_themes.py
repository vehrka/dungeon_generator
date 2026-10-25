"""Tests for the themes of the Combined grammar (grammar/themes.py)

Run with: python -m pytest tests
"""

import logging

import pytest

from dungeon_fx11 import DCombined
from grammar.combined import GRAMMAR, REWARDS
from grammar.themes import DEFAULT_THEME, THEMES, get_theme, reward_variant
from tests import test_dungeon_render
from tests.test_dungeon_json import GOAL, START, graph
from utils.dungeon_json import dungeon_json
from utils.dungeon_key import dungeon_key
from utils.dungeon_render import dungeon_dot

logging.disable(logging.CRITICAL)

SEEDS = range(1, 101)
OBJECT_TYPES = {
    otype
    for rule in GRAMMAR.values()
    for var in rule["variants"]
    for otype, _ in var["objects"].values()
}


@pytest.mark.parametrize("name", THEMES)
def test_rewards_cover_d20(name: str) -> None:
    rewards = THEMES[name]["rewards"]

    covered = sorted(roll for _, lo, hi in rewards for roll in range(lo, hi + 1))

    assert covered == list(range(1, 21))


@pytest.mark.parametrize("name", THEMES)
def test_objects_are_grammar_object_types(name: str) -> None:
    assert set(THEMES[name]["objects"]) <= OBJECT_TYPES


def test_default_theme_is_the_grammar() -> None:
    assert THEMES[DEFAULT_THEME]["rewards"] == REWARDS
    assert [reward_variant(THEMES[DEFAULT_THEME], roll) for roll in range(1, 21)] == [
        next(
            var
            for var in GRAMMAR["GB"]["variants"]
            if var["ranges"]["M"][0] <= roll <= var["ranges"]["M"][1]
        )
        for roll in range(1, 21)
    ]


def test_get_theme_falls_back_to_default() -> None:
    assert get_theme(None) is THEMES[DEFAULT_THEME]
    assert get_theme("spam") is THEMES[DEFAULT_THEME]
    assert get_theme("cyber") is THEMES["cyber"]


def test_unknown_theme_fails() -> None:
    with pytest.raises(KeyError):
        DCombined(seed=42, theme="spam")


@pytest.mark.parametrize("name", THEMES)
def test_theme_keeps_the_layout(name: str) -> None:
    for seed in SEEDS:
        default = DCombined(seed=seed, size="L").get_graph()
        themed = DCombined(seed=seed, size="L", theme=name).get_graph()

        types = [t.split(":")[0] for t in default.vs["type"]]
        assert types == [t.split(":")[0] for t in themed.vs["type"]], f"seed {seed}"
        assert default.get_edgelist() == themed.get_edgelist(), f"seed {seed}"


@pytest.mark.parametrize("name", ["cyber", "tor-barrow", "tor-dwarf"])
def test_theme_names_objects_and_rewards(name: str) -> None:
    theme = THEMES[name]
    rewards = {f"gb: {label}" for label, _, _ in theme["rewards"]}
    names, bonus = set(), set()
    for seed in SEEDS:
        g = DCombined(seed=seed, size="L", theme=name).get_graph()
        names |= {obj.name.rsplit(" ", 1)[0] for v in g.vs for obj in (v["objects"] or [])}
        bonus |= {t for t in g.vs["type"] if t.startswith("gb")}

    assert names == set(theme["objects"].values())
    assert bonus and bonus <= rewards


def test_key_uses_the_theme_rooms() -> None:
    g = graph(
        [START, GOAL, ("e", "e", None), ("gb: paydata", "gb: paydata", None)],
        [(0, 2), (2, 1), (2, 3)],
    )

    lines = dungeon_key(dungeon_json(g, {"theme": "cyber"})).splitlines()

    assert "1. **Jack-in point (START)**. Exits: 2" in lines
    assert "2. **ICE**. Exits: 1, 3, 4" in lines
    assert "3. **Data core (GOAL)**. Exits: 2" in lines
    assert "4. **Data cache: paydata**. Exits: 2" in lines
    assert any("theme cyber" in line for line in lines)


def test_legend_uses_the_theme_rooms() -> None:
    g = test_dungeon_render.graph(
        [("st", "#f0e442", "START"), ("gl", "#e69f00", "GOAL"), ("e", "#009e73", "e")],
        [(0, 2), (2, 1)],
    )

    assert "ICE" in dungeon_dot(g, "Spam", rooms=THEMES["cyber"]["rooms"])
    assert "ICE" not in dungeon_dot(g, "Spam")
