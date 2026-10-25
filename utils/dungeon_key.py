"""Writes a GM key of a generated dungeon in Markdown, built on its JSON export
(utils/dungeon_json.py)

Rooms are numbered breadth first from START. Gates are not rooms: they show up as conditions on
the exits that cross them. The key table lists, for each object, the rooms where it is found and
the doors (pairs of rooms) it opens. Room descriptions come from the theme of the dungeon
(grammar/themes.py), with the defaults below for the types the theme leaves out.
"""

from pathlib import Path
from typing import Any

import igraph

from grammar.themes import get_theme
from utils.dungeon_json import dungeon_json
from utils.dungeon_render import ROOM_STYLE

SPECIAL_ROOMS = {
    "st": "Entrance (START)",
    "gl": "Dungeon goal (GOAL)",
    "exit": "Extra entrance (EXIT)",
}


def _capitalize(text: str) -> str:
    return text[0].upper() + text[1:]


def _contents(node: dict[str, Any], rooms: dict[str, str]) -> str:
    """Short description of what the room holds

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


def _condition(gate: dict[str, Any], names: dict[str, str]) -> str:
    """Text of the condition to cross the gate"""
    needs = " + ".join(names[uid] for uid in gate["requires"])
    if gate["gate"] == "secret":
        return "secret"
    if gate["gate"] == "lock":
        return f"locked: {needs}"
    if gate["gate"] == "on":
        return f"{needs} ON"
    if gate["gate"] == "off":
        return f"{needs} OFF, open at start"
    return f"needs {needs}"


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


def _door(numbers: dict[int, int], source: int, target: int, oneway: bool) -> str:
    """Door between two rooms, by number"""
    a, b = numbers[source], numbers[target]
    return f"{a} → {b}" if oneway else f"{min(a, b)} ↔ {max(a, b)}"


def dungeon_key(data: dict[str, Any]) -> str:
    """Markdown GM key of the JSON export of a dungeon

    Arguments:
        data dict: JSON export of the dungeon (utils.dungeon_json.dungeon_json)
    """
    nodes = data["nodes"]
    names = {obj["id"]: obj["name"] for obj in data["objects"]}
    descriptions = get_theme(data.get("theme"))["rooms"]
    exits = _exits(data)
    numbers = _numbers(data, exits)
    rooms = sorted(exits, key=numbers.get)

    summary = [f"Seed {data['seed']}"] if "seed" in data else []
    summary += [f"size {data['size']}"] if "size" in data else []
    summary += [f"theme {data['theme']}"] if "theme" in data else []
    summary += [f"{len(rooms)} rooms", "solvable" if data["solvable"] else "**unsolvable**"]
    lines = [f"# GM key: {data.get('grammar', 'Generated')} dungeon", "", " · ".join(summary), ""]
    lines += [f"- {reason}" for reason in data["unsolvable_reasons"]]
    lines += [""] if data["unsolvable_reasons"] else []

    # gate id -> doors it guards
    doors: dict[int, dict[str, None]] = {}
    lines += ["## Rooms", ""]
    for rid in rooms:
        links = []
        for target in sorted(exits[rid], key=numbers.get):
            gates, oneway = exits[rid][target]
            tags = [_condition(nodes[gid], names) for gid in gates] + (
                ["one-way"] if oneway else []
            )
            links.append(f"{numbers[target]} ({', '.join(tags)})" if tags else str(numbers[target]))
            for gid in gates:
                doors.setdefault(gid, {}).setdefault(_door(numbers, rid, target, oneway), None)
        exit_text = ", ".join(links) or "none"
        lines.append(
            f"{numbers[rid]}. **{_contents(nodes[rid], descriptions)}**. Exits: {exit_text}"
        )

    if data["objects"]:
        lines += [
            "",
            "## Keys",
            "",
            "| Object | Found in | Opens |",
            "|--------|----------|-------|",
        ]
        for obj in data["objects"]:
            found = ", ".join(str(n) for n in sorted(numbers[rid] for rid in obj["found_in"]))
            opens = []
            for gid in obj["opens"]:
                gate = nodes[gid]
                if gate["gate"] in ("on", "off"):
                    suffix = f" ({gate['gate'].upper()})"
                elif len(gate["requires"]) > 1:
                    others = [names[uid] for uid in gate["requires"] if uid != obj["id"]]
                    suffix = f" (+ {' + '.join(others)})"
                else:
                    suffix = ""
                opens += [f"{door}{suffix}" for door in doors.get(gid, {})]
            lines.append(
                f"| {obj['name']} | {found or 'none'} | {', '.join(dict.fromkeys(opens))} |"
            )
    return "\n".join(lines) + "\n"


def write_dungeon_key(
    graph: igraph.Graph, target: str | Path, meta: dict[str, Any] | None = None
) -> Path:
    """Writes the Markdown GM key of the dungeon graph to the target file"""
    target = Path(target)
    target.write_text(dungeon_key(dungeon_json(graph, meta)))
    return target
