"""Tests for the JSON export of utils/dungeon_json.py

Run with: python -m pytest tests
"""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import igraph
import pytest

from dungeon_fx11 import D24, D30, DCombined
from utils.dungeon_json import dungeon_json
from utils.graph_utils import Dungeon

logging.disable(logging.CRITICAL)

KEY = SimpleNamespace(uid="spam", type="key", name="spam key 1")
LEVER = SimpleNamespace(uid="eggs", type="lever", name="lever 1")


def graph(
    vertices: list[tuple[Any, ...]],
    edges: list[tuple[int, int]],
    oneway: list[bool] | None = None,
) -> igraph.Graph:
    """Graph from (type, name, objects) vertices and (source, target) edges"""
    g = igraph.Graph(directed=True)
    g.add_vertices(len(vertices))
    g.vs["type"], g.vs["name"], g.vs["objects"] = (list(attr) for attr in zip(*vertices))
    g.add_edges(edges)
    if oneway is not None:
        g.es["oneway"] = oneway
    return g


START = ("st", "START", None)
GOAL = ("gl", "GOAL", None)


def test_lock_requires_the_key_found_before_it() -> None:
    g = graph(
        [START, GOAL, ("lock", "Use spam key 1", [KEY]), ("key", "Get spam key 1", [KEY])],
        [(0, 3), (0, 2), (2, 1)],
    )

    data = dungeon_json(g, {"seed": 42})

    assert data["seed"] == 42 and data["start"] == 0 and data["goal"] == 1
    assert data["solvable"] is True and data["unsolvable_reasons"] == []
    assert data["nodes"][2] == {
        "id": 2,
        "type": "lock",
        "name": "Use spam key 1",
        "kind": "gate",
        "gate": "lock",
        "requires": ["spam"],
    }
    assert data["nodes"][3]["kind"] == "room" and data["nodes"][3]["objects"] == ["spam"]
    assert data["objects"] == [
        {"id": "spam", "type": "key", "name": "spam key 1", "found_in": [3], "opens": [2]}
    ]


def test_lever_gates_keep_their_position() -> None:
    g = graph(
        [
            START,
            GOAL,
            ("lever", "lever 1", [LEVER]),
            ("gate", "Check lever 1 ON", [LEVER]),
            ("gate", "Check lever 1 OFF", [LEVER]),
            ("s", "secret", None),
        ],
        [(0, 2), (0, 3), (3, 1), (0, 4), (4, 5), (5, 1)],
    )

    nodes = dungeon_json(g)["nodes"]

    assert [node.get("gate") for node in nodes] == [None, None, None, "on", "off", "secret"]
    assert nodes[2]["kind"] == "room"


def test_edges_keep_one_way() -> None:
    g = graph([START, GOAL, ("e", "e", None)], [(0, 2), (2, 1)], oneway=[True, False])

    edges = dungeon_json(g)["edges"]

    assert edges == [
        {"source": 0, "target": 2, "oneway": True},
        {"source": 2, "target": 1, "oneway": False},
    ]


def test_unsolvable_dungeon_is_reported() -> None:
    g = graph([START, GOAL, ("lock", "Use spam key 1", [KEY])], [(0, 2), (2, 1)])

    data = dungeon_json(g)

    assert data["solvable"] is False
    assert data["unsolvable_reasons"] == ["GOAL unreachable", "Use spam key 1 needs spam key 1"]
    assert data["objects"][0]["found_in"] == []


def test_combined_dungeon_export(tmp_path: Path) -> None:
    target = tmp_path / "spam.json"

    DCombined(seed=15143, size="M", json=target)
    data = json.loads(target.read_text())

    assert data["grammar"] == "Combined" and data["seed"] == 15143 and data["size"] == "M"
    assert data["solvable"] is True
    ids = {node["id"] for node in data["nodes"]}
    assert all(edge["source"] in ids and edge["target"] in ids for edge in data["edges"])
    for obj in data["objects"]:
        assert obj["found_in"], f"{obj['name']} has no pickup"
        for gid in obj["opens"]:
            assert obj["id"] in data["nodes"][gid]["requires"]


@pytest.mark.parametrize("cls", [D24, D30, DCombined])
def test_generated_dungeons_export(cls: type[Dungeon], tmp_path: Path) -> None:
    for seed in range(1, 31):
        target = tmp_path / f"{cls.NAME}_{seed}.json"
        cls(seed=seed, json=target)
        assert json.loads(target.read_text())["grammar"] == cls.NAME
