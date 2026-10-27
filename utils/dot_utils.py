"""Graphviz styles and helpers shared by the grammar sheet (grammar/render.py) and the dungeon
plots (utils/dungeon_render.py)"""

import subprocess
from collections.abc import Iterable
from pathlib import Path

FONT = "DejaVu Sans"

OUTPUT_FORMATS = ("png", "svg", "pdf")

NODE_STYLE = {
    "prev": {"fillcolor": "#7b8cde", "label": ""},
    "next": {"fillcolor": "#7fd6d6", "label": ""},
    "nt": {"fillcolor": "#e8735a"},
    "room": {"fillcolor": "#7cc98f"},
    "item": {"fillcolor": "#56b4e9"},
    "switch": {"fillcolor": "#e39ac8"},
    "special": {"fillcolor": "#f0d24a"},
}

# Direction (dir=...) is set by each renderer
EDGE_STYLE = {
    "both": 'color="#555555"',
    "one": 'color="#111111" penwidth=2',
    "lock": 'color="#c0601a" fontcolor="#c0601a" penwidth=2',
    "state": 'color="#b34d8f" fontcolor="#b34d8f" penwidth=2',
    "on": 'color="#b34d8f" fontcolor="#b34d8f" penwidth=2',
    "off": 'color="#b34d8f" fontcolor="#b34d8f" penwidth=2 style=dashed',
    "secret": 'color="#888888" fontcolor="#666666" style=dashed',
}

EDGE_COLOR = {"both": "#555555", "one": "#111111", "lock": "#c0601a", "secret": "#666666"}
EDGE_COLOR.update(dict.fromkeys(("state", "on", "off"), "#b34d8f"))


def run_dot(source: str, target: str | Path) -> Path:
    """Renders the DOT source to the target file, the format is taken from its suffix"""
    target = Path(target)
    fmt = target.suffix.lstrip(".").lower()
    if fmt not in OUTPUT_FORMATS:
        raise ValueError(
            f"Unsupported output format '{target.suffix}', use one of {OUTPUT_FORMATS}"
        )
    args = ["dot", f"-T{fmt}", "-o", str(target)]
    if fmt == "png":
        args.insert(1, "-Gdpi=110")
    subprocess.run(args, input=source.encode(), check=True)
    return target


def font(content: object, size: int = 10, color: str = "#000000", bold: bool = False) -> str:
    """HTML-like text with size and color"""
    content = f"<B>{content}</B>" if bold else content
    return f'<FONT POINT-SIZE="{size}" COLOR="{color}">{content}</FONT>'


def card(header: str, rows: Iterable[str], padding: int = 5) -> str:
    """White bordered card: header row followed by the rows"""
    return (
        '<TABLE BORDER="1" COLOR="#d0d0d0" CELLBORDER="0" CELLSPACING="0" '
        f'CELLPADDING="{padding}" BGCOLOR="white">' + header + "".join(rows) + "</TABLE>"
    )


def card_header(title: str, subtitle: str = "", colspan: int = 1) -> str:
    """Dark title row of a card"""
    content = font(title, 14, "white", bold=True) + (
        font(f"  {subtitle}", 11, "#cfd6df") if subtitle else ""
    )
    return f'<TR><TD COLSPAN="{colspan}" ALIGN="LEFT" BGCOLOR="#2f3640">{content}</TD></TR>'
