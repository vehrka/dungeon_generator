"""Themes for the Combined grammar: room labels, object names and bonus goal rewards as data

A theme only changes text. Room type codes (n, e, t, p, c, em, eb, gb...) and object types stay
the same, so merging, pacing and rendering colors work for every theme, and a seed gives the same
layout with any theme.

Theme:
    rooms: {room type: description} shown in the GM key and the plot legend. Missing types use
        the default descriptions (utils/dungeon_render.py ROOM_STYLE, utils/dungeon_key.py
        SPECIAL_ROOMS). st, gl and exit describe START, GOAL and EXIT.
    objects: {object type: name} for the objects of grammar/combined.py (key, bosskey, item,
        switch, lever). Missing types keep the grammar name.
    rewards: [(label, lo, hi)] bonus goal table rolled with a d20; must cover 1-20.
"""

from typing import TypedDict

from grammar.combined import REWARDS, Reward, Variant, reward_variants


class Theme(TypedDict):
    """Theme of the Combined grammar (see module docstring)"""

    rooms: dict[str, str]
    objects: dict[str, str]
    rewards: list[Reward]


DEFAULT_THEME = "zelda"

THEMES: dict[str, Theme] = {
    "zelda": {"rooms": {}, "objects": {}, "rewards": list(REWARDS)},
    "cyber": {
        "rooms": {
            "st": "jack-in point (START)",
            "gl": "data core (GOAL)",
            "exit": "backdoor (EXIT)",
            "n": "empty node / scan",
            "e": "ICE",
            "t": "trace trap",
            "p": "encrypted lock (puzzle)",
            "c": "firewall (hacking check)",
            "em": "black ICE sentinel",
            "eb": "core AI",
            "gb": "data cache",
        },
        "objects": {
            "key": "access code",
            "bosskey": "root key",
            "item": "icebreaker",
            "switch": "relay",
            "lever": "breaker",
        },
        "rewards": [
            ("black-market program", 1, 4),
            ("paydata", 5, 12),
            ("credentials", 13, 16),
            ("crypto wallet", 17, 20),
        ],
    },
}


def get_theme(name: str | None) -> Theme:
    """Theme by name, the default theme for None or unknown names"""
    return THEMES.get(name or DEFAULT_THEME, THEMES[DEFAULT_THEME])


def reward_variant(theme: Theme, roll: int) -> Variant:
    """GB variant of the theme reward whose d20 range contains the roll"""
    return next(
        var
        for var, (_, lo, hi) in zip(reward_variants(theme["rewards"]), theme["rewards"])
        if lo <= roll <= hi
    )
