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
    "tor-barrow": {
        "rooms": {
            "st": "grass-grown portal (START)",
            "gl": "burial vault of the prince (GOAL)",
            "exit": "hidden cleft (EXIT)",
            "n": "silent crypt (Explore, Scan)",
            "e": "restless dead",
            "t": "sorcerous mist (Endurance loss)",
            "p": "rhyming portal (Riddle, Lore)",
            "c": "oath-rune seal (Lore, Song)",
            "em": "tomb sentinel",
            "eb": "barrow-wight lord",
            "gb": "royal grave-goods (Shadow: Greed)",
        },
        "objects": {
            "key": "bronze key",
            "bosskey": "rune-inscribed sigil",
            "item": "blessed censer",
            "switch": "gravestone catch",
            "lever": "counterweight stone",
        },
        "rewards": [
            ("treasure points", 1, 8),
            ("precious object", 9, 14),
            ("marvellous artefact", 15, 18),
            ("barrow-blade (famous weapon)", 19, 20),
        ],
    },
    "tor-dwarf": {
        "rooms": {
            "st": "silent threshold (START)",
            "gl": "despoiled throne hall (GOAL)",
            "exit": "choked flue (EXIT)",
            "n": "echoing hall (Explore, Scan)",
            "e": "orcs and goblins",
            "t": "fumes or shaft fall (Endurance loss)",
            "p": "ithildin seal (Riddle, Lore)",
            "c": "collapsed passage (Athletics, Explore)",
            "em": "orc-captain",
            "eb": "cave-troll or great orc",
            "gb": "sealed dwarf vault (Shadow: Greed)",
        },
        "objects": {
            "key": "iron key",
            "bosskey": "ring of the vault-keeper",
            "item": "dwarf mattock",
            "switch": "rune-tile",
            "lever": "sluice wheel",
        },
        "rewards": [
            ("treasure points", 1, 8),
            ("precious object", 9, 14),
            ("marvellous artefact", 15, 18),
            ("famous weapon or armour", 19, 20),
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
