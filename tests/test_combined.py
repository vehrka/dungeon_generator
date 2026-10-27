"""Tests for the combined grammar and the DCombined generator

Run with: python -m pytest tests
"""

import random

import pytest

from dungeon_fx11 import DCombined
from grammar.combined import (
    GRAMMAR,
    PACING,
    PRESETS,
    Variant,
    paced_room_variant,
    simulate,
    spectral_radius,
)
from utils.graph_utils import progress, reachable

SEEDS = range(1, 301)


def room_label(var: Variant) -> str:
    """Label of the single room of an R variant"""
    return var["nodes"][0][2]


@pytest.mark.parametrize("preset", PRESETS)
def test_ranges_cover_d20(preset: str) -> None:
    for symbol, rule in GRAMMAR.items():
        covered = sorted(
            roll
            for var in rule["variants"]
            if var["ranges"].get(preset)
            for roll in range(var["ranges"][preset][0], var["ranges"][preset][1] + 1)
        )
        assert covered == list(range(1, 21)), f"{symbol} {preset}"


@pytest.mark.parametrize("preset", PRESETS)
def test_grammar_is_subcritical(preset: str) -> None:
    assert spectral_radius(preset) < 1


@pytest.mark.parametrize("preset", PRESETS)
def test_simulation_terminates(preset: str) -> None:
    for seed in SEEDS:
        _, expansions = simulate(preset, seed)
        assert expansions < 10000


@pytest.mark.parametrize("reduce", [True, False])
@pytest.mark.parametrize("preset", PRESETS)
def test_dungeons_are_solvable(preset: str, reduce: bool) -> None:
    for seed in SEEDS:
        graph = DCombined(
            seed=seed, size=preset, reduce=reduce, maxnodes=10000, maxiter=10000
        ).get_graph()
        assert not graph.vs.select(color_eq="#d55e00"), f"unexpanded vertices, seed {seed}"
        reached = reachable(graph)
        goal = graph.vs.find(name="GOAL").index
        assert goal in reached, f"GOAL unreachable, preset {preset} seed {seed}"
        pickups = [
            v.index for v in graph.vs if v["type"] in ("key", "bosskey", "item", "switch", "lever")
        ]
        assert set(pickups) <= reached, f"unreachable pickup, preset {preset} seed {seed}"


@pytest.mark.parametrize("reduce", [True, False])
@pytest.mark.parametrize("preset", PRESETS)
def test_limits_finish_the_expansion(preset: str, reduce: bool) -> None:
    for seed in SEEDS:
        graph = DCombined(seed=seed, size=preset, reduce=reduce, maxnodes=10, maxiter=3).get_graph()
        assert not graph.vs.select(color_eq="#d55e00"), f"unexpanded vertices, seed {seed}"
        assert graph.vs.find(name="GOAL").index in reachable(graph), f"seed {seed}"
        assert graph.vs.select(type_eq="eb"), f"boss room missing, seed {seed}"


@pytest.mark.parametrize("tier", range(len(PACING)))
def test_pacing_tiers_cover_d20(tier: int) -> None:
    names = [var["name"] for var in GRAMMAR["R"]["variants"]]
    _, ranges = PACING[tier]
    covered = sorted(roll for lo, hi in ranges.values() for roll in range(lo, hi + 1))
    assert covered == list(range(1, 21)) and set(ranges) == set(names)


def test_paced_rooms_get_harder() -> None:
    def share(progress: float, labels: str) -> int:
        rooms = [room_label(paced_room_variant(progress, roll)) for roll in range(1, 21)]
        return sum(room in labels for room in rooms)

    assert share(0, "tc") < share(0.5, "tc") < share(1, "tc")
    assert share(0, "n") > share(1, "n")


def test_generated_rooms_are_paced() -> None:
    early, late = [], []
    for seed in SEEDS:
        graph = DCombined(seed=seed, size="L", reduce=False).get_graph()
        for vertex in graph.vs.select(type_in=("n", "e", "t", "p", "c")):
            (late if progress(graph, vertex.index) > 2 / 3 else early).append(vertex["type"])
    hard = ("t", "c")
    assert sum(t in hard for t in late) / len(late) > sum(t in hard for t in early) / len(early)


def test_rolls_are_independent_d20() -> None:
    dungeon = DCombined(seed=42)
    rand = random.Random(42)

    assert dungeon._rolls == [rand.randint(1, 20) for _ in dungeon._rolls]


def test_same_seed_same_dungeon() -> None:
    first, second = (DCombined(seed=42, size="L").get_graph() for _ in range(2))

    assert first.vs["type"] == second.vs["type"]
    assert first.get_edgelist() == second.get_edgelist()


def test_seed_pins_the_dungeon() -> None:
    graph = DCombined(seed=42, size="S").get_graph()

    assert graph.vs["name"] == [
        "START",
        "GOAL",
        "n",
        "Get small key 1",
        "Use small key 1",
        "n",
        "Get boss key 1",
        "eb",
        "Use boss key 1",
        "e",
        "c",
    ]
    assert graph.get_edgelist() == [
        (0, 2),
        (2, 3),
        (2, 4),
        (4, 9),
        (5, 8),
        (5, 10),
        (7, 1),
        (8, 7),
        (9, 5),
        (10, 6),
    ]


def test_seed_zero_is_a_seed() -> None:
    dungeon = DCombined(seed=0)
    rand = random.Random(0)

    assert dungeon._seed == 0
    assert dungeon._rolls == [rand.randint(1, 20) for _ in dungeon._rolls]


def test_xs_dungeons_are_small() -> None:
    rooms = sorted(simulate("XS", seed)[0] for seed in SEEDS)

    assert rooms[0] == 6
    assert rooms[len(rooms) // 2] <= 8
