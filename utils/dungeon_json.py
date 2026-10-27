"""Exports a generated dungeon graph as JSON, the base for any consumer (e.g. a FoundryVTT module)

Every vertex is a node, gates included: a gate sits between the rooms it connects and lists the
objects it requires. Edges are two-way unless oneway is set. Objects list where they are found
and which gates they open. Rooms carry the number of the GM key (breadth first from START) and a
label from the theme of the dungeon (grammar/themes.py), with the defaults below for the types
the theme leaves out.

Schema versions: 2 adds number and label to rooms.
"""

import json
from pathlib import Path
from typing import Any

import igraph

from grammar.themes import get_theme
from utils.dungeon_render import ROOM_STYLE
from utils.graph_utils import GATE_TYPES, _objects, unsolvable_reasons

SCHEMA_VERSION = 2

SPECIAL_ROOMS = {
    "st": "Entrance (START)",
    "gl": "Dungeon goal (GOAL)",
    "exit": "Extra entrance (EXIT)",
}


def _capitalize(text: str) -> str:
    return text[0].upper() + text[1:]


def _label(node: dict[str, Any], rooms: dict[str, str]) -> str:
    """Themed label of the room: short description of what it holds

    Arguments:
        node dict: Room node of the JSON export
        rooms dict: Theme descriptions of room types, override the defaults
    """
    rtype, name = node["type"], node["name"]
    if rtype in rooms:
        return _capitalize(rooms[rtype])
    if rtype in SPECIAL_ROOMS:
        return SPECIAL_ROOMS[rtype]
    if rtype.startswith("gb: "):
        return f"{_capitalize(rooms.get('gb', 'bonus goal'))}: {rtype[4:]}"
    if name.startswith("Get "):
        return f"Pickup: {name[4:]}"
    if rtype == "switch":
        return f"Switch: {name}"
    if rtype == "lever":
        return f"Lever: {name} (starts OFF)"
    if rtype in ROOM_STYLE:
        return _capitalize(ROOM_STYLE[rtype][2])
    return name


def _walks(data: dict[str, Any]) -> dict[int, list[tuple[int, bool]]]:
    """Walkable neighbours of each node: (node id, edge is one-way)"""
    walks: dict[int, list[tuple[int, bool]]] = {node["id"]: [] for node in data["nodes"]}
    for edge in data["edges"]:
        walks[edge["source"]].append((edge["target"], edge["oneway"]))
        if not edge["oneway"]:
            walks[edge["target"]].append((edge["source"], False))
    return walks


def _exits(data: dict[str, Any]) -> dict[int, dict[int, tuple[tuple[int, ...], bool]]]:
    """Exits of each room: room id -> {room id: (gate ids crossed, one-way)}

    Walks from the room through any chain of gates until it reaches another room. When several
    paths lead to the same room, the first one found is kept.
    """
    nodes = data["nodes"]
    walks = _walks(data)
    exits = {}
    for node in nodes:
        if node["kind"] != "room":
            continue
        found: dict[int, tuple[tuple[int, ...], bool]] = {}
        stack: list[tuple[int, tuple[int, ...], bool]] = [(node["id"], (), False)]
        seen = {node["id"]}
        while stack:
            vid, gates, oneway = stack.pop()
            for nxt, one in sorted(walks[vid]):
                if nxt in seen:
                    continue
                seen.add(nxt)
                if nodes[nxt]["kind"] == "room":
                    found.setdefault(nxt, (gates, oneway or one))
                else:
                    stack.append((nxt, gates + (nxt,), oneway or one))
        exits[node["id"]] = found
    return exits


def _numbers(
    data: dict[str, Any], exits: dict[int, dict[int, tuple[tuple[int, ...], bool]]]
) -> dict[int, int]:
    """Room id -> number, breadth first from START (by node id among siblings)"""
    linked = {rid: set(targets) for rid, targets in exits.items()}
    for rid, targets in exits.items():
        for target in targets:
            linked[target].add(rid)
    order = [data["start"]]
    for rid in order:
        order.extend(nxt for nxt in sorted(linked[rid]) if nxt not in order)
    # rooms out of reach, e.g. behind a dead end of the legacy grammars
    order.extend(rid for rid in exits if rid not in order)
    return {rid: number for number, rid in enumerate(order, 1)}


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
    data = {
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
    descriptions = get_theme(data.get("theme"))["rooms"]
    for rid, number in _numbers(data, _exits(data)).items():
        nodes[rid].update(number=number, label=_label(nodes[rid], descriptions))
    return data


def write_dungeon_json(
    graph: igraph.Graph, target: str | Path, meta: dict[str, Any] | None = None
) -> Path:
    """Writes the JSON export of the dungeon graph to the target file"""
    target = Path(target)
    target.write_text(json.dumps(dungeon_json(graph, meta), indent=2) + "\n")
    return target
