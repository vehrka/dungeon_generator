"""Tests for the Graphviz dungeon renderer

Run with: python -m pytest tests
"""

import logging
import shutil

import igraph
import pytest

from dungeon_fx11 import D24, D30, DCombined
from utils.color_utils import (
    color_blue,
    color_cyan,
    color_green,
    color_orange,
    color_pink,
    color_yellow,
)
from utils.dot_utils import run_dot
from utils.dungeon_render import dungeon_dot

logging.disable(logging.CRITICAL)


def graph(vertices, edges, oneway=None):
    """Graph from (type, color, name) vertices and (source, target) edges"""
    g = igraph.Graph(directed=True)
    g.add_vertices(len(vertices))
    g.vs["type"], g.vs["color"], g.vs["name"] = (list(attr) for attr in zip(*vertices))
    g.add_edges(edges)
    if oneway is not None:
        g.es["oneway"] = oneway
    return g


START = ("st", color_yellow, "START")
GOAL = ("gl", color_orange, "GOAL")
LOCK = ("lock", color_blue, "Use spam key 1")


def test_gate_with_one_way_in_and_out_is_an_edge_label():
    g = graph([START, GOAL, LOCK], [(0, 2), (2, 1)])

    dot = dungeon_dot(g, "Spam")

    assert "v2 [" not in dot
    assert 'v0 -> v1 [dir=none color="#c0601a"' in dot
    assert 'label="[spam key 1]"' in dot


def test_gate_with_several_exits_stays_a_node():
    eggs = ("n", color_green, "n")
    g = graph([START, GOAL, LOCK, eggs], [(0, 2), (2, 1), (2, 3)])

    dot = dungeon_dot(g, "Spam")

    assert 'v2 [label="Use spam key 1" shape=octagon' in dot


def test_only_one_way_edges_get_an_arrow():
    g = graph([START, GOAL, ("e", color_green, "e")], [(0, 2), (2, 1)], oneway=[True, False])

    dot = dungeon_dot(g, "Spam")

    assert "v0 -> v2 [dir=forward" in dot
    assert "v2 -> v1 [dir=none" in dot


def test_legend_lists_only_present_elements():
    rooms = [("gb: spam", color_green, "gb: spam"), ("key", color_cyan, "Get spam key 1")]
    g = graph([START, GOAL, *rooms], [(0, 2), (2, 3), (2, 1)])

    dot = dungeon_dot(g, "Spam", "Lovely!")

    assert "bonus goal" in dot and "pickup" in dot
    assert "trap" not in dot and "switch / lever" not in dot and "locked" not in dot
    assert "Lovely! · 4 rooms" in dot


def test_switch_and_state_gate_roles():
    switch = ("switch", color_pink, "switch 1")
    gate = ("gate", color_pink, "Check switch 1 OFF")
    g = graph([START, GOAL, switch, gate], [(0, 2), (0, 3), (3, 1)])

    dot = dungeon_dot(g, "Spam")

    assert 'v2 [label="switch 1" shape=hexagon' in dot
    assert 'label="[switch 1 OFF]"' in dot and "style=dashed" in dot


def test_run_dot_rejects_unknown_format(tmp_path):
    with pytest.raises(ValueError, match="Unsupported output format"):
        run_dot("digraph {}", tmp_path / "spam.txt")


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz not installed")
@pytest.mark.parametrize("cls", [D24, D30, DCombined])
def test_generated_dungeons_render(cls, tmp_path):
    for seed in range(1, 31):
        output = tmp_path / f"{cls.NAME}_{seed}.svg"
        cls(seed=seed, output=output)
        assert output.stat().st_size > 0
