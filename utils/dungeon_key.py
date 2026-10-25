"""Writes a GM key of a generated dungeon in Markdown, built on its JSON export
(utils/dungeon_json.py)

Room numbers and labels come from the JSON export. Gates are not rooms: they show up as
conditions on the exits that cross them. The key table lists, for each object, the rooms where it
is found and the doors (pairs of rooms) it opens.
"""

from pathlib import Path
from typing import Any

import igraph

from utils.dungeon_json import _exits, dungeon_json


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
    exits = _exits(data)
    numbers = {rid: nodes[rid]["number"] for rid in exits}
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
        lines.append(f"{numbers[rid]}. **{nodes[rid]['label']}**. Exits: {exit_text}")

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
