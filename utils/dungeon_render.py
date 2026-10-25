"""Renders a generated dungeon graph as Graphviz DOT

Rooms are laid out top to bottom, from START to GOAL. Gates (locks, state gates, secrets) with
a single way in and out are drawn as labelled edges, as in the grammar sheet (grammar/render.py).
The legend only lists the elements present in the dungeon.
"""

import html

import igraph

from utils.color_utils import (
    color_black,
    color_blue,
    color_cyan,
    color_green,
    color_orange,
    color_red,
    color_yellow,
)
from utils.dot_utils import (
    EDGE_COLOR,
    EDGE_STYLE,
    FONT,
    NODE_STYLE,
    card,
    card_header,
    font,
)

# Room type (first word of the vertex type): (fill color, font color, description)
ROOM_STYLE = {
    "n": ("#e3e6ea", "#000000", "nothing / explore"),
    "e": ("#f4b6a6", "#000000", "enemy"),
    "m": ("#f4b6a6", "#000000", "monster"),
    "em": ("#e8735a", "#000000", "mini-boss"),
    "eb": ("#a93226", "#ffffff", "boss"),
    "t": ("#f5c07a", "#000000", "trap"),
    "p": ("#b8a9e3", "#000000", "puzzle"),
    "c": ("#d7c49e", "#000000", "challenge (skill check)"),
    "gb": ("#a8dba8", "#000000", "bonus goal"),
}
ROOM_FALLBACK = ("#ffffff", "#000000", "room")

# Role: (fill color, node attributes, legend label, legend description)
ROLE_STYLE = {
    "special": (
        NODE_STYLE["special"]["fillcolor"],
        'shape=box style="rounded,filled,bold" penwidth=1.5',
        "START",
        "start, goal, extra entrance (EXIT)",
    ),
    "nt": (
        "#ffffff",
        'shape=box style="rounded,dashed,filled" '
        f'color="{NODE_STYLE["nt"]["fillcolor"]}" penwidth=1.5',
        "L",
        "unexpanded rule (limits reached)",
    ),
    "item": (
        NODE_STYLE["item"]["fillcolor"],
        "shape=ellipse style=filled",
        "Get",
        "pickup: key, boss key, item",
    ),
    "switch": (
        NODE_STYLE["switch"]["fillcolor"],
        "shape=hexagon style=filled",
        "switch",
        "switch / lever (sets a state)",
    ),
    "lock": (
        "#f2c6a0",
        f'shape=octagon style=filled color="{EDGE_COLOR["lock"]}" penwidth=1.5',
        "Use",
        "locked door: needs that object",
    ),
    "gate": (
        "#f3cfe4",
        f'shape=octagon style=filled color="{EDGE_COLOR["state"]}" penwidth=1.5',
        "Check",
        "state gate: needs switches / lever",
    ),
    "secret": (
        "#ffffff",
        'shape=box style="rounded,dashed,filled" color="#888888" penwidth=1.5',
        "secret",
        "hidden path (bombable wall)",
    ),
}

# Edge kind: (legend symbol, legend description)
EDGE_LEGEND = {
    "both": ("—", "two-way path"),
    "one": ("→", "one-way path (drop, ledge)"),
    "lock": ("[key]", "locked: needs that object"),
    "state": ("[switch]", "state gate: open when all switches hit"),
    "on": ("[lever ON]", "toggle gate: open in that lever position"),
    "off": ("[lever OFF]", "toggle gate: open in that lever position"),
    "secret": ("secret", "hidden path (bombable wall)"),
}

GATE_ROLES = ("lock", "gate", "secret")


def vertex_role(vertex: igraph.Vertex) -> str:
    """Role of a vertex, from its color and name (the vertex types differ between grammars)"""
    color, name = vertex["color"], vertex["name"]
    if color in (color_yellow, color_orange):
        return "special"
    if color == color_red:
        return "nt"
    if color == color_black:
        return "secret"
    if color == color_green:
        return "room"
    if name.startswith("Use ") or color == color_blue:
        return "lock"
    if name.startswith("Check ") or name == "and":
        return "gate"
    if color == color_cyan:
        return "item"
    return "switch"


def gate_kind(vertex: igraph.Vertex, role: str) -> str:
    """Edge kind of a gate vertex drawn as an edge"""
    if role != "gate":
        return role
    if vertex["name"].endswith(" ON"):
        return "on"
    if vertex["name"].endswith(" OFF"):
        return "off"
    return "state"


def gate_label(vertex: igraph.Vertex, kind: str) -> str:
    """Edge label of a gate vertex drawn as an edge: the objects it needs"""
    if kind == "secret":
        return "secret"
    name = vertex["name"]
    for prefix in ("Use ", "Check "):
        name = name.removeprefix(prefix)
    return f"[{name}]"


def collapsible(graph: igraph.Graph, vertex: igraph.Vertex) -> bool:
    """True if the gate vertex has a single way in and out and can be drawn as an edge"""
    ins = graph.incident(vertex.index, "in")
    outs = graph.incident(vertex.index, "out")
    if len(ins) != 1 or len(outs) != 1:
        return False
    return graph.es[ins[0]].source != graph.es[outs[0]].target


def quote(text: str) -> str:
    """Escapes the text for a quoted DOT string"""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def node_line(vertex: igraph.Vertex, role: str) -> str:
    """DOT node for a vertex"""
    if role == "room":
        fill, color, _ = ROOM_STYLE.get(vertex["type"].split(":")[0], ROOM_FALLBACK)
        attrs = f'shape=box style="rounded,filled" fillcolor="{fill}" fontcolor="{color}"'
    else:
        fill, attrs, _, _ = ROLE_STYLE[role]
        attrs = f'{attrs} fillcolor="{fill}"'
    return f'v{vertex.index} [label="{quote(vertex["name"])}" {attrs}];'


def edge_line(src: int, dst: int, kind: str, oneway: bool, label: str = "") -> str:
    """DOT edge between two vertex indexes. Only one-way paths get an arrow"""
    if oneway and kind == "both":
        kind = "one"
    direction = "forward" if oneway else "none"
    label_attr = f' label="{quote(label)}"' if label else ""
    return f"v{src} -> v{dst} [dir={direction} {EDGE_STYLE[kind]}{label_attr}];"


def legend_cells(swatch: str, label: str, text: str) -> str:
    """Legend entry cells: swatch, label and description, followed by a gap"""
    label = font(html.escape(label), bold=True) if label else ""
    return (
        f'{swatch}<TD ALIGN="LEFT">{label}</TD><TD ALIGN="LEFT">{font(html.escape(text))}</TD>'
        '<TD WIDTH="16"></TD>'
    )


def legend_card(
    title: str,
    subtitle: str,
    room_types: set[str],
    roles: set[str],
    edge_kinds: set[str],
    rooms: dict[str, str] | None = None,
) -> str:
    """Title and legend of the elements present in the dungeon

    rooms overrides the description of room types (theme, grammar/themes.py).
    """
    rooms = rooms or {}
    room_rows = [
        (f'<TD BGCOLOR="{fill}" WIDTH="28"> </TD>', code, rooms.get(code, text))
        for code, (fill, _, text) in ROOM_STYLE.items()
        if code in room_types
    ]
    room_rows += [
        ('<TD BORDER="1" WIDTH="28"> </TD>', code, rooms.get(code, ROOM_FALLBACK[2]))
        for code in sorted(room_types - ROOM_STYLE.keys())
    ]
    role_rows = [
        (f'<TD BGCOLOR="{fill}" BORDER="1" WIDTH="28"> </TD>', label, text)
        for role, (fill, _, label, text) in ROLE_STYLE.items()
        if role in roles
    ]
    edge_rows = [
        (f'<TD>{font(html.escape(symbol), color=EDGE_COLOR[kind], bold=True)}</TD>', "", text)
        for kind, (symbol, text) in EDGE_LEGEND.items()
        if kind in edge_kinds
    ]
    sections = [
        (name, rows)
        for name, rows in (("Rooms", room_rows), ("Nodes", role_rows), ("Paths", edge_rows))
        if rows
    ]
    # Single table with 4 columns per section, so rows keep the same height in every section
    titles = "".join(
        f'<TD COLSPAN="4" ALIGN="LEFT">{font(name, 10, "#777777", bold=True)}</TD>'
        for name, _ in sections
    )
    lines = [f"<TR>{titles}</TR>"]
    for idx in range(max(len(rows) for _, rows in sections)):
        cells = "".join(
            legend_cells(*rows[idx]) if idx < len(rows) else '<TD COLSPAN="4"></TD>'
            for _, rows in sections
        )
        lines.append(f"<TR>{cells}</TR>")
    return card(card_header(title, subtitle, colspan=4 * len(sections)), lines, padding=3)


def dungeon_dot(
    graph: igraph.Graph, title: str, subtitle: str = "", rooms: dict[str, str] | None = None
) -> str:
    """DOT source of the dungeon graph, with the title and the legend on top

    Arguments:
        graph igraph.Graph: Dungeon graph (vertex attributes: type, color, name; optional
            edge attribute oneway)
        title str: Title of the plot
        subtitle str: Text next to the title
        rooms dict: Legend description of room types, overrides the defaults (theme)
    """
    oneway = graph.es["oneway"] if "oneway" in graph.es.attributes() else [False] * graph.ecount()
    roles = {vertex.index: vertex_role(vertex) for vertex in graph.vs}
    collapsed = {
        vertex.index
        for vertex in graph.vs
        if roles[vertex.index] in GATE_ROLES and collapsible(graph, vertex)
    }

    nodes, edges, edge_kinds = [], [], set()
    for vertex in graph.vs:
        if vertex.index not in collapsed:
            nodes.append(node_line(vertex, roles[vertex.index]))
    for edge in graph.es:
        if edge.source in collapsed or edge.target in collapsed:
            continue
        edges.append(edge_line(edge.source, edge.target, "both", oneway[edge.index]))
        edge_kinds.add("one" if oneway[edge.index] else "both")
    for vidx in sorted(collapsed):
        vertex = graph.vs[vidx]
        in_eid = graph.incident(vidx, "in")[0]
        kind = gate_kind(vertex, roles[vidx])
        edges.append(
            edge_line(
                graph.es[in_eid].source,
                graph.es[graph.incident(vidx, "out")[0]].target,
                kind,
                oneway[in_eid],
                gate_label(vertex, kind),
            )
        )
        edge_kinds.add(kind)

    drawn = [vertex for vertex in graph.vs if vertex.index not in collapsed]
    room_types = {v["type"].split(":")[0] for v in drawn if roles[v.index] == "room"}
    legend = legend_card(
        title,
        " · ".join(part for part in (subtitle, f"{len(drawn)} rooms") if part),
        room_types,
        {roles[v.index] for v in drawn} - {"room"},
        edge_kinds,
        rooms,
    )
    ranks = [
        f"{{rank={rank}; v{v.index};}}"
        for rank, name in (("min", "START"), ("max", "GOAL"))
        for v in graph.vs.select(name_eq=name)
    ]
    return "\n".join(
        [
            "digraph dungeon {",
            'rankdir=TB; bgcolor="#eef0f3"; pad=0.3; nodesep=0.3; ranksep=0.45;',
            f"labelloc=t; labeljust=l; fontname=\"{FONT}\"; label=<{legend}>;",
            f'node [fontname="{FONT}" fontsize=11 height=0.35 width=0.5 penwidth=0 '
            'margin="0.1,0.04"];',
            f'edge [fontname="{FONT}" fontsize=9 arrowsize=0.7];',
            *nodes,
            *edges,
            *ranks,
            "}",
        ]
    )
