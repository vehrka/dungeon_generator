"""Tests for the legacy D24 and D30 generators

Run with: python -m pytest tests
"""

import re

import igraph
import pytest

from dungeon_fx11 import D24, D30
from utils.graph_utils import Dungeon

SEEDS = range(1, 101)
# External objects are brought from outside the dungeon: no room gives them
EXTERNAL = re.compile(r"external \d+")


def missing_objects(graph: igraph.Graph) -> list[str]:
    """Objects a "Use"/"Check" room needs that no room of the dungeon gives"""
    names = set(graph.vs["name"])
    needed = {m[2] for name in names if (m := re.match(r"(Use|Check) (.+)", name))}
    given = names | {m[2] for name in names if (m := re.match(r"(Get|Touch|Switch) (.+)", name))}
    return sorted(obj for obj in needed - given if not EXTERNAL.fullmatch(obj))


@pytest.mark.xfail(strict=True, reason="CAPS and _red_cleanup drop keys and switches (TODO 1)")
@pytest.mark.parametrize("dungeon", [D24, D30])
def test_legacy_dungeons_give_every_object(dungeon: type[Dungeon]) -> None:
    for seed in SEEDS:
        graph = dungeon(seed=seed, maxnodes=20, maxiter=10).get_graph()
        assert missing_objects(graph) == [], f"{dungeon.NAME} seed {seed}"
