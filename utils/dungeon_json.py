"""Exports a generated dungeon graph as JSON, the base for any consumer (e.g. a FoundryVTT module)

Every vertex is a node, gates included: a gate sits between the rooms it connects and lists the
objects it requires. Edges are two-way unless oneway is set. Objects list where they are found
and which gates they open.
"""

import json
from pathlib import Path
from typing import Any

import igraph

from utils.graph_utils import GATE_TYPES, _objects, unsolvable_reasons

SCHEMA_VERSION = 1


def _gate_kind(vertex: igraph.Vertex) -> str | None:
    """lock, state, on, off or secret for gates, None for rooms"""
    if vertex["type"] == "s":
        return "secret"
    if vertex["type"] not in GATE_TYPES:
        return None
    if vertex["type"] == "lock":
        return "lock"
    for position in ("ON", "OFF"):
        if vertex["name"].endswith(f" {position}"):
            return position.lower()
    return "state"


def _node(vertex: igraph.Vertex) -> dict[str, Any]:
    """Node of the vertex: rooms list the objects found in them, gates the objects they require"""
    gate = _gate_kind(vertex)
    uids = [obj.uid for obj in _objects(vertex)]
    node = {"id": vertex.index, "type": vertex["type"], "name": vertex["name"]}
    if gate:
        node.update(kind="gate", gate=gate, requires=uids)
    else:
        node.update(kind="room", objects=uids)
    return node


def dungeon_json(graph: igraph.Graph, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dict with the meta data, nodes, edges and objects of the dungeon graph

    Arguments:
        graph igraph.Graph: Generated dungeon graph
        meta dict: Extra fields of the dungeon (grammar, seed, size...)
    """
    nodes = [_node(vertex) for vertex in graph.vs]
    oneway = graph.es["oneway"] if "oneway" in graph.es.attributes() else [False] * graph.ecount()
    edges = [
        {"source": edge.source, "target": edge.target, "oneway": bool(one)}
        for edge, one in zip(graph.es, oneway)
    ]
    objects: dict[str, dict[str, Any]] = {}
    for vertex, node in zip(graph.vs, nodes):
        for obj in _objects(vertex):
            entry = objects.setdefault(
                obj.uid,
                {"id": obj.uid, "type": obj.type, "name": obj.name, "found_in": [], "opens": []},
            )
            entry["opens" if node["kind"] == "gate" else "found_in"].append(vertex.index)
    reasons = unsolvable_reasons(graph)
    return {
        "schema_version": SCHEMA_VERSION,
        **(meta or {}),
        "start": graph.vs.find(name="START").index,
        "goal": graph.vs.find(name="GOAL").index,
        "solvable": not reasons,
        "unsolvable_reasons": reasons,
        "nodes": nodes,
        "edges": edges,
        "objects": list(objects.values()),
    }


def write_dungeon_json(
    graph: igraph.Graph, target: str | Path, meta: dict[str, Any] | None = None
) -> Path:
    """Writes the JSON export of the dungeon graph to the target file"""
    target = Path(target)
    target.write_text(json.dumps(dungeon_json(graph, meta), indent=2) + "\n")
    return target
