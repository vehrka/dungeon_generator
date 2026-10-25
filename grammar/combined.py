"""Combined Zelda-like dungeon grammar (Post24 + Post30)

Single source of truth for the grammar: used by the PNG renderer (grammar/render.py),
the size simulator (simulate/expected_counts) and the DCombined generator (dungeon_fx11.py).

Design:
    * Post30 structure: L() layout chooser and R() room chooser, loops, one-way paths,
      secret paths and extra entrances.
    * Post24 locks: small keys, boss key, dungeon item behind a mini-boss, switches,
      toggle levers and bonus goals.
    * Only L() and S() are recursive. Every lock rule creates its key on a branch that forks
      before the lock, inside the same rule, so every dungeon is solvable. No caps needed.
    * Size is controlled by the d20 ranges of each preset (S, M, L). Recursion is
      subcritical (spectral radius < 1) for every preset.

Data model:
    Rule: {"desc": str, "branch": bool, "variants": [variant, ...]}
        branch=True means the rule is a dead end (no "next" anchor).
    Variant: {"name", "ranges", "objects", "nodes", "edges"}
        ranges: {preset: (lo, hi)} d20 range per preset (missing preset = never chosen)
        objects: {oid: (type, name)} objects created when the variant is applied
        nodes: [(nid, kind, label)] kind in NODE_KINDS. "prev" and "next" are the anchors.
            For "item" and "switch" nodes the label is the object id.
        edges: [(src, dst, kind, *oids)] kind in EDGE_KINDS, written in progression order.
"""

import random
from typing import TypedDict

# d20 range (lo, hi)
Span = tuple[int, int]
# (nid, kind, label)
Node = tuple[str, str, str]
# (src, dst, kind, *oids)
Edge = tuple[str, ...]


class Variant(TypedDict):
    """Variant of a grammar rule (see Data model)"""

    name: str
    ranges: dict[str, Span]
    objects: dict[str, tuple[str, str]]
    nodes: list[Node]
    edges: list[Edge]


class Rule(TypedDict):
    """Grammar rule (see Data model)"""

    desc: str
    branch: bool
    variants: list[Variant]


PRESETS = ("S", "M", "L")

# nt: non-terminal (expanded), room: terminal room, item: pickup of an object,
# switch: switch or lever writing a state, special: start/goal/extra entrance
NODE_KINDS = ("nt", "room", "item", "switch", "special")
ROOM_KINDS = ("room", "item", "switch", "special")

# both: two-way path, one: one-way path, lock: needs object, state: needs all switches on,
# on/off: needs lever in that position, secret: hidden path
EDGE_KINDS = ("both", "one", "lock", "state", "on", "off", "secret")
GATE_KINDS = ("lock", "state", "on", "off", "secret")

# Bonus goal table (label, d20 lo, d20 hi). Themes (grammar/themes.py) swap it
Reward = tuple[str, int, int]
REWARDS: list[Reward] = [
    ("heart piece", 1, 4),
    ("rupees", 5, 12),
    ("bombs", 13, 16),
    ("arrows", 17, 20),
]

# Non-recursive variant of each recursive rule, used to finish the expansion when the
# generator limits are hit: the remaining lock rules still get their keys
FINISH = {"L": "room", "S": "end"}


def rng(
    s: Span | None = None,
    m: Span | None = None,
    l: Span | None = None,  # noqa: E741
) -> dict[str, Span]:
    """d20 ranges per preset"""
    ranges = {"S": s, "M": m, "L": l}
    return {preset: span for preset, span in ranges.items() if span}


def always(lo: int = 1, hi: int = 20) -> dict[str, Span]:
    """Same d20 range for every preset"""
    return rng(s=(lo, hi), m=(lo, hi), l=(lo, hi))


def chain(*nids: str) -> list[Edge]:
    """Two-way edges between consecutive nodes"""
    return [(a, b, "both") for a, b in zip(nids, nids[1:])]


def variant(
    name: str,
    ranges: dict[str, Span],
    nodes: list[Node],
    edges: list[Edge],
    objects: dict[str, tuple[str, str]] | None = None,
) -> Variant:
    return {
        "name": name,
        "ranges": ranges,
        "objects": objects or {},
        "nodes": nodes,
        "edges": edges,
    }


def room_variant(name: str, ranges: dict[str, Span], label: str) -> Variant:
    """Single terminal room between the anchors"""
    return variant(name, ranges, [("r", "room", label)], chain("prev", "r", "next"))


def reward_variants(rewards: list[Reward]) -> list[Variant]:
    """GB variants of a bonus goal table: one dead-end room per reward"""
    return [
        variant(label, always(lo, hi), [("gb", "room", f"gb: {label}")], chain("prev", "gb"))
        for label, lo, hi in rewards
    ]


GRAMMAR: dict[str, Rule] = {
    "Start": {
        "desc": "Dungeon start (prev = START, next = GOAL)",
        "branch": False,
        "variants": [
            variant(
                "key wing",
                rng(s=(1, 12), m=(1, 4)),
                [("k", "nt", "K"), ("bk", "nt", "BK")],
                chain("prev", "k", "bk", "next"),
            ),
            variant(
                "item",
                rng(s=(13, 20), m=(5, 16), l=(1, 8)),
                [("e", "nt", "E"), ("ig", "nt", "IG"), ("bk", "nt", "BK")],
                chain("prev", "e", "ig", "bk", "next"),
            ),
            variant(
                "item + wing",
                rng(m=(17, 20), l=(9, 20)),
                [("e", "nt", "E"), ("ig", "nt", "IG"), ("l", "nt", "L"), ("bk", "nt", "BK")],
                chain("prev", "e", "ig", "l", "bk", "next"),
            ),
        ],
    },
    "E": {
        "desc": "Entrance",
        "branch": False,
        "variants": [
            variant(
                "single",
                rng(s=(1, 18), m=(1, 15), l=(1, 12)),
                [("l", "nt", "L")],
                chain("prev", "l", "next"),
            ),
            variant(
                "extra entrance",
                rng(s=(19, 20), m=(16, 20), l=(13, 20)),
                [("l", "nt", "L"), ("h", "nt", "R"), ("l2", "nt", "L"), ("x", "special", "EXIT")],
                chain("prev", "l", "h", "next") + chain("h", "l2", "x"),
            ),
        ],
    },
    "L": {
        "desc": "Layout chooser (only recursive structure)",
        "branch": False,
        "variants": [
            variant(
                "room",
                rng(s=(1, 12), m=(1, 9), l=(1, 7)),
                [("r", "nt", "R")],
                chain("prev", "r", "next"),
            ),
            variant(
                "linear",
                rng(s=(13, 15), m=(10, 12), l=(8, 10)),
                [("s", "nt", "S")],
                chain("prev", "s", "next"),
            ),
            variant(
                "small key",
                rng(s=(16, 17), m=(13, 14), l=(11, 12)),
                [("k", "nt", "K")],
                chain("prev", "k", "next"),
            ),
            variant(
                "switch",
                rng(s=(18, 18), m=(15, 15), l=(13, 14)),
                [("w", "nt", "SW")],
                chain("prev", "w", "next"),
            ),
            variant(
                "toggle",
                rng(m=(16, 16), l=(15, 15)),
                [("t", "nt", "TG")],
                chain("prev", "t", "next"),
            ),
            variant(
                "hook",
                rng(s=(19, 19), m=(17, 17), l=(16, 16)),
                [("h", "nt", "H")],
                chain("prev", "h", "next"),
            ),
            variant(
                "loop",
                rng(s=(20, 20), m=(18, 19), l=(17, 18)),
                [("a", "nt", "R"), ("l1", "nt", "L"), ("l2", "nt", "L"), ("b", "nt", "R")],
                chain("prev", "a", "l1", "b", "next") + chain("a", "l2", "b"),
            ),
            variant(
                "one-way loop",
                rng(m=(20, 20), l=(19, 20)),
                [("a", "nt", "R"), ("l", "nt", "L"), ("b", "nt", "R")],
                chain("prev", "a")
                + [("a", "l", "one"), ("l", "b", "one"), ("b", "a", "one")]
                + chain("b", "next"),
            ),
        ],
    },
    "R": {
        "desc": "Room chooser (terminal content)",
        "branch": False,
        "variants": [
            room_variant("nothing", always(1, 3), "n"),
            room_variant("enemy", always(4, 8), "e"),
            room_variant("trap", always(9, 11), "t"),
            room_variant("puzzle", always(12, 16), "p"),
            room_variant("challenge", always(17, 20), "c"),
        ],
    },
    "S": {
        "desc": "Linear sequence",
        "branch": False,
        "variants": [
            variant(
                "end",
                rng(s=(1, 17), m=(1, 16), l=(1, 15)),
                [("r", "nt", "R")],
                chain("prev", "r", "next"),
            ),
            variant(
                "continue",
                rng(s=(18, 20), m=(17, 20), l=(16, 20)),
                [("r", "nt", "R"), ("s", "nt", "S")],
                chain("prev", "r", "s", "next"),
            ),
        ],
    },
    "GB": {
        "desc": "Bonus goal",
        "branch": True,
        "variants": reward_variants(REWARDS),
    },
    "H": {
        "desc": "Hook: side bonus goal",
        "branch": False,
        "variants": [
            variant(
                "open",
                always(1, 12),
                [("a", "nt", "R"), ("gb", "nt", "GB")],
                chain("prev", "a", "next") + chain("a", "gb"),
            ),
            variant(
                "secret",
                always(13, 20),
                [("a", "nt", "R"), ("gb", "nt", "GB")],
                chain("prev", "a", "next") + [("a", "gb", "secret")],
            ),
        ],
    },
    "K": {
        "desc": "Small key lock",
        "branch": False,
        "variants": [
            variant(
                "key in wing",
                always(1, 12),
                [("h", "room", "n"), ("l", "nt", "L"), ("key", "item", "k"), ("r", "nt", "R")],
                chain("prev", "h")
                + chain("h", "l", "key")
                + [("h", "r", "lock", "k")]
                + chain("r", "next"),
                objects={"k": ("key", "small key")},
            ),
            variant(
                "guarded key",
                always(13, 20),
                [("h", "room", "n"), ("r", "nt", "R"), ("key", "item", "k"), ("l", "nt", "L")],
                chain("prev", "h")
                + chain("h", "r", "key")
                + [("h", "l", "lock", "k")]
                + chain("l", "next"),
                objects={"k": ("key", "small key")},
            ),
        ],
    },
    "SW": {
        "desc": "Switch lock",
        "branch": False,
        "variants": [
            variant(
                "one switch",
                rng(s=(1, 14), m=(1, 13), l=(1, 12)),
                [("h", "nt", "R"), ("l", "nt", "L"), ("sw", "switch", "s1")],
                chain("prev", "h") + chain("h", "l", "sw") + [("h", "next", "state", "s1")],
                objects={"s1": ("switch", "switch")},
            ),
            variant(
                "two switches (and)",
                rng(s=(15, 20), m=(14, 20), l=(13, 20)),
                [
                    ("h", "nt", "R"),
                    ("l1", "nt", "L"),
                    ("sw1", "switch", "s1"),
                    ("l2", "nt", "L"),
                    ("sw2", "switch", "s2"),
                ],
                chain("prev", "h")
                + chain("h", "l1", "sw1")
                + chain("h", "l2", "sw2")
                + [("h", "next", "state", "s1", "s2")],
                objects={"s1": ("switch", "switch"), "s2": ("switch", "switch")},
            ),
        ],
    },
    "TG": {
        "desc": "Toggle lever: ON opens the way, OFF opens a bonus",
        "branch": False,
        "variants": [
            variant(
                "toggle",
                always(1, 20),
                [
                    ("h", "room", "n"),
                    ("l", "nt", "L"),
                    ("lv", "switch", "t"),
                    ("m", "nt", "R"),
                    ("gb", "nt", "GB"),
                ],
                chain("prev", "h")
                + chain("h", "l", "lv")
                + [("h", "m", "on", "t"), ("h", "gb", "off", "t")]
                + chain("m", "next"),
                objects={"t": ("lever", "lever")},
            ),
        ],
    },
    "IG": {
        "desc": "Dungeon item gate: mini-boss guards the item that opens the way",
        "branch": False,
        "variants": [
            variant(
                "item",
                always(1, 10),
                [
                    ("h", "room", "n"),
                    ("l", "nt", "L"),
                    ("em", "room", "em"),
                    ("it", "item", "i"),
                    ("m", "nt", "L"),
                ],
                chain("prev", "h")
                + chain("h", "l", "em", "it")
                + [("h", "m", "lock", "i")]
                + chain("m", "next"),
                objects={"i": ("item", "dungeon item")},
            ),
            variant(
                "item + backtrack bonus",
                always(11, 20),
                [
                    ("h", "room", "n"),
                    ("l", "nt", "L"),
                    ("em", "room", "em"),
                    ("it", "item", "i"),
                    ("m", "nt", "L"),
                    ("gb", "nt", "GB"),
                ],
                chain("prev", "h")
                + chain("h", "l", "em", "it")
                + [("h", "m", "lock", "i"), ("h", "gb", "lock", "i")]
                + chain("m", "next"),
                objects={"i": ("item", "dungeon item")},
            ),
        ],
    },
    "BK": {
        "desc": "Boss key: opens the boss room",
        "branch": False,
        "variants": [
            variant(
                "boss key in wing",
                always(1, 12),
                [("h", "room", "n"), ("l", "nt", "L"), ("bkey", "item", "b"), ("eb", "room", "eb")],
                chain("prev", "h")
                + chain("h", "l", "bkey")
                + [("h", "eb", "lock", "b")]
                + chain("eb", "next"),
                objects={"b": ("bosskey", "boss key")},
            ),
            variant(
                "boss key behind small key",
                always(13, 20),
                [("h", "room", "n"), ("k", "nt", "K"), ("bkey", "item", "b"), ("eb", "room", "eb")],
                chain("prev", "h")
                + chain("h", "k", "bkey")
                + [("h", "eb", "lock", "b")]
                + chain("eb", "next"),
                objects={"b": ("bosskey", "boss key")},
            ),
        ],
    },
}


# Pacing of the R room chooser in the generator: d20 ranges by progress, the position of the room
# between START (0) and the boss room (1). Easy rooms early, traps and challenges near the end.
# The middle tier is the R ranges of the presets, which simulate and the renderer use.
# Rooms up to NEAR_BOSS steps away from a BOSS_ROOMS room use the last tier.
PACING: tuple[tuple[float, dict[str, Span]], ...] = (
    (
        1 / 3,
        {
            "nothing": (1, 5),
            "enemy": (6, 11),
            "trap": (12, 12),
            "puzzle": (13, 18),
            "challenge": (19, 20),
        },
    ),
    (2 / 3, {var["name"]: var["ranges"]["M"] for var in GRAMMAR["R"]["variants"]}),
    (
        1,
        {
            "nothing": (1, 1),
            "enemy": (2, 6),
            "trap": (7, 11),
            "puzzle": (12, 13),
            "challenge": (14, 20),
        },
    ),
)
BOSS_ROOMS = ("em", "eb")
NEAR_BOSS = 2


def choose_variant(symbol: str, preset: str, roll: int) -> Variant:
    """Returns the variant of the symbol whose d20 range for the preset contains the roll"""
    for var in GRAMMAR[symbol]["variants"]:
        span = var["ranges"].get(preset)
        if span and span[0] <= roll <= span[1]:
            return var
    raise ValueError(f"No variant for {symbol} preset {preset} roll {roll}")


def finish_variant(symbol: str, preset: str, roll: int) -> Variant:
    """Like choose_variant, but recursive rules take their FINISH variant so the expansion ends"""
    if symbol in FINISH:
        return next(var for var in GRAMMAR[symbol]["variants"] if var["name"] == FINISH[symbol])
    return choose_variant(symbol, preset, roll)


def paced_room_variant(progress: float, roll: int) -> Variant:
    """Returns the R variant for a room at the progress (0 to 1) with the d20 roll"""
    ranges = next(tier for top, tier in PACING if progress <= top)
    name = next(name for name, (lo, hi) in ranges.items() if lo <= roll <= hi)
    return next(var for var in GRAMMAR["R"]["variants"] if var["name"] == name)


def variant_children(var: Variant) -> list[str]:
    """Non-terminal symbols produced by a variant"""
    return [label for _, kind, label in var["nodes"] if kind == "nt"]


def variant_rooms(var: Variant) -> int:
    """Terminal rooms produced by a variant"""
    return sum(1 for _, kind, _ in var["nodes"] if kind in ROOM_KINDS)


def variant_probability(var: Variant, preset: str) -> float:
    span = var["ranges"].get(preset)
    return (span[1] - span[0] + 1) / 20 if span else 0.0


def mean_matrix(preset: str) -> dict[str, dict[str, float]]:
    """M[a][b] = expected number of b symbols produced by one expansion of a"""
    matrix = {}
    for symbol, rule in GRAMMAR.items():
        row = {other: 0.0 for other in GRAMMAR}
        for var in rule["variants"]:
            prob = variant_probability(var, preset)
            for child in variant_children(var):
                row[child] += prob
        matrix[symbol] = row
    return matrix


def spectral_radius(preset: str, iterations: int = 500) -> float:
    """Largest eigenvalue of the mean matrix (power iteration)

    Below 1 the grammar terminates with small dungeons.
    """
    matrix = mean_matrix(preset)
    vec = {symbol: 1.0 for symbol in GRAMMAR}
    radius = 0.0
    for _ in range(iterations):
        new = {b: sum(vec[a] * matrix[a][b] for a in GRAMMAR) for b in GRAMMAR}
        radius = max(new.values())
        if radius == 0:
            return 0.0
        vec = {symbol: value / radius for symbol, value in new.items()}
    return radius


def simulate(preset: str, seed: int | None = None, max_expansions: int = 10000) -> tuple[int, int]:
    """Expands the grammar without building a graph. Returns (rooms, expansions)"""
    rand = random.Random(seed)
    stack = ["Start"]
    rooms = 2  # START and GOAL anchors
    expansions = 0
    while stack and expansions < max_expansions:
        symbol = stack.pop()
        var = choose_variant(symbol, preset, rand.randint(1, 20))
        expansions += 1
        rooms += variant_rooms(var)
        stack.extend(variant_children(var))
    return rooms, expansions


def size_stats(preset: str, runs: int = 5000) -> dict[str, float]:
    """Room count statistics for a preset (before reduction)"""
    results = [simulate(preset, seed) for seed in range(runs)]
    rooms = sorted(r for r, _ in results)
    expansions = max(e for _, e in results)

    def pct(q: float) -> int:
        return rooms[min(len(rooms) - 1, int(q * len(rooms)))]

    return {
        "rho": spectral_radius(preset),
        "mean": sum(rooms) / len(rooms),
        "p10": pct(0.10),
        "median": pct(0.50),
        "p90": pct(0.90),
        "max": rooms[-1],
        "max_expansions": expansions,
    }


if __name__ == "__main__":
    for size in PRESETS:
        print(size, {k: round(v, 2) for k, v in size_stats(size).items()})
