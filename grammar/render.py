"""Renders the combined grammar (grammar/combined.py) as a single PNG sheet using Graphviz

Each variant is rendered as a small PNG with `dot`, then all of them are assembled into rule
cards inside one HTML-like Graphviz table, together with the legend and the size statistics.

Usage:
    python -m grammar.render [--output refs/combined.png] [--runs 5000]
"""

import argparse
import html
import subprocess
import tempfile
from pathlib import Path

from grammar.combined import GRAMMAR, PRESETS, size_stats

FONT = "DejaVu Sans"

NODE_STYLE = {
    "prev": {"fillcolor": "#7b8cde", "label": ""},
    "next": {"fillcolor": "#7fd6d6", "label": ""},
    "nt": {"fillcolor": "#e8735a"},
    "room": {"fillcolor": "#7cc98f"},
    "item": {"fillcolor": "#56b4e9"},
    "switch": {"fillcolor": "#e39ac8"},
    "special": {"fillcolor": "#f0d24a"},
}

EDGE_STYLE = {
    "both": 'dir=both color="#555555"',
    "one": 'dir=forward color="#111111" penwidth=2',
    "lock": 'dir=both color="#c0601a" fontcolor="#c0601a" penwidth=2',
    "state": 'dir=both color="#b34d8f" fontcolor="#b34d8f" penwidth=2',
    "on": 'dir=both color="#b34d8f" fontcolor="#b34d8f" penwidth=2',
    "off": 'dir=both color="#b34d8f" fontcolor="#b34d8f" penwidth=2 style=dashed',
    "secret": 'dir=both color="#888888" fontcolor="#666666" style=dashed',
}

# Sheet layout: rule cards per column (the size table goes between the 2nd and 3rd group)
COLUMNS = (("Start", "E", "R", "S"), ("L",), ("GB", "H"), ("K", "SW", "TG", "IG", "BK"))


def object_label(var, oid):
    return var["objects"][oid][1]


def edge_label(var, kind, oids):
    names = [object_label(var, oid) for oid in oids]
    if kind == "lock":
        return f"[{names[0]}]"
    if kind == "state":
        return "[" + " + ".join(names) + "]"
    if kind in ("on", "off"):
        return f"[{names[0]} {kind.upper()}]"
    if kind == "secret":
        return "secret"
    return ""


def variant_dot(symbol, var):
    """DOT source for one variant diagram"""
    anchors = ("START", "GOAL") if symbol == "Start" else (None, None)
    lines = [
        "digraph G {",
        "rankdir=LR; bgcolor=transparent; nodesep=0.15; ranksep=0.35; pad=0.05;",
        f'node [shape=box style="rounded,filled" fontname="{FONT}" fontsize=11 height=0.3 width=0.45 penwidth=0];',
        f'edge [arrowsize=0.6 fontname="{FONT}" fontsize=9];',
    ]
    used = {nid for edge in var["edges"] for nid in edge[:2]}
    for anchor, special in zip(("prev", "next"), anchors):
        if anchor not in used:
            continue
        if special:
            lines.append(
                f'{anchor} [label="{special}" fillcolor="{NODE_STYLE["special"]["fillcolor"]}"];'
            )
        else:
            style = NODE_STYLE[anchor]
            lines.append(f'{anchor} [label="" fillcolor="{style["fillcolor"]}" width=0.35];')
    for nid, kind, label in var["nodes"]:
        if kind == "nt":
            text = f"{label}()"
        elif kind in ("item", "switch"):
            text = object_label(var, label)
        else:
            text = label
        lines.append(f'{nid} [label="{text}" fillcolor="{NODE_STYLE[kind]["fillcolor"]}"];')
    for src, dst, kind, *oids in var["edges"]:
        label = edge_label(var, kind, oids)
        label_attr = f' label="{label}"' if label else ""
        lines.append(f"{src} -> {dst} [{EDGE_STYLE[kind]}{label_attr}];")
    lines.append("}")
    return "\n".join(lines)


def run_dot(source, target):
    subprocess.run(
        ["dot", "-Tpng", "-Gdpi=110", "-o", str(target)], input=source.encode(), check=True
    )


def range_text(var, preset):
    span = var["ranges"].get(preset)
    if not span:
        return "—"
    return str(span[0]) if span[0] == span[1] else f"{span[0]}-{span[1]}"


def font(content, size=10, color="#000000", bold=False):
    """HTML-like text with size and color"""
    content = f"<B>{content}</B>" if bold else content
    return f'<FONT POINT-SIZE="{size}" COLOR="{color}">{content}</FONT>'


def card_open(padding=5):
    return f'<TABLE BORDER="1" COLOR="#d0d0d0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="{padding}" BGCOLOR="white">'


def card_header(title, subtitle="", colspan=1):
    """Dark title row of a card"""
    content = font(title, 14, "white", bold=True) + (
        font(f"  {subtitle}", 11, "#cfd6df") if subtitle else ""
    )
    return f'<TR><TD COLSPAN="{colspan}" ALIGN="LEFT" BGCOLOR="#2f3640">{content}</TD></TR>'


def rule_card(symbol, images):
    rule = GRAMMAR[symbol]
    kind = " · dead end" if rule["branch"] else ""
    preset_cells = "".join(f"<TD>{font(preset, 9, '#777777')}</TD>" for preset in PRESETS)
    rows = [
        card_open(),
        card_header(f"{symbol}()", html.escape(rule["desc"]) + kind, colspan=5),
        f"<TR>{preset_cells}<TD></TD><TD></TD></TR>",
    ]
    for idx, var in enumerate(rule["variants"]):
        bg = "#f6f7f9" if idx % 2 else "white"
        cells = "".join(
            f'<TD BGCOLOR="{bg}"><FONT POINT-SIZE="10">{range_text(var, preset)}</FONT></TD>'
            for preset in PRESETS
        )
        rows.append(
            f"<TR>{cells}"
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT">{font(html.escape(var["name"]), 9, "#555555")}</TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT"><IMG SRC="{images[(symbol, idx)]}"/></TD></TR>'
        )
    rows.append("</TABLE>")
    return "".join(rows)


def legend_card():
    swatches = (
        ("prev", "previous node (incoming anchor)"),
        ("next", "next node (outgoing anchor)"),
        ("nt", "non-terminal: expand with its rule"),
        ("room", "room (terminal): n e t p c em eb gb"),
        ("item", "pickup: small key, boss key, dungeon item"),
        ("switch", "switch / lever (sets a state)"),
        ("special", "START, GOAL, extra entrance"),
    )
    edges = (
        ("—", "#555555", "two-way path"),
        ("→", "#111111", "one-way path (drop, ledge)"),
        ("[key]", "#c0601a", "locked: needs that object"),
        ("[switch]", "#b34d8f", "state gate: open when all switches hit"),
        ("[lever ON/OFF]", "#b34d8f", "toggle gate: open in that lever position"),
        ("secret", "#666666", "hidden path (bombable wall)"),
    )
    rooms = "n nothing · e enemy · t trap · p puzzle · c challenge · em mini-boss · eb boss · gb bonus goal"
    rows = [
        card_open(4),
        card_header("Legend", colspan=2),
    ]
    for kind, text in swatches:
        rows.append(
            f'<TR><TD BGCOLOR="{NODE_STYLE[kind]["fillcolor"]}" WIDTH="34"> </TD>'
            f'<TD ALIGN="LEFT"><FONT POINT-SIZE="10">{text}</FONT></TD></TR>'
        )
    for symbol, color, text in edges:
        rows.append(
            f'<TR><TD><FONT POINT-SIZE="10" COLOR="{color}"><B>{html.escape(symbol)}</B></FONT></TD>'
            f'<TD ALIGN="LEFT"><FONT POINT-SIZE="10">{text}</FONT></TD></TR>'
        )
    rows.append(
        f'<TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#555555">{rooms}</FONT></TD></TR>'
    )
    rows.append("</TABLE>")
    return "".join(rows)


def instructions_card():
    text = (
        "1. Pick a size preset: S, M or L. Its column gives the d20 ranges.",
        "2. Start with Start(): START and GOAL are its anchors.",
        "3. While red nodes remain: pick one, roll d20, replace it with the diagram of its range.",
        "    Blue = node before it, teal = node after it. Edges keep their direction.",
        "4. Objects (keys, switches, levers, item) are new per application of a rule.",
        "5. Finally merge contiguous n / e / p rooms joined by plain two-way paths.",
        "",
        "Why it stays small and solvable:",
        "• Only L() and S() recurse. Every other rule expands once into a fixed shape.",
        "• Each lock rule places its key on a branch that forks before the lock.",
        "• No caps: odds alone keep the expected size finite (spectral radius below 1).",
    )
    rows = [
        card_open(3),
        card_header("How to use"),
    ]
    rows += [
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{html.escape(line) or " "}</FONT></TD></TR>'
        for line in text
    ]
    rows.append("</TABLE>")
    return "".join(rows)


def stats_card(runs):
    header = ("preset", "ρ", "mean", "p10", "median", "p90", "max")
    rows = [
        card_open(),
        card_header("Expected size", f"rooms before merge, {runs} runs", colspan=len(header)),
        "<TR>"
        + "".join(f'<TD><FONT POINT-SIZE="10" COLOR="#777777">{h}</FONT></TD>' for h in header)
        + "</TR>",
    ]
    for preset in PRESETS:
        stats = size_stats(preset, runs)
        values = (
            preset,
            f"{stats['rho']:.2f}",
            f"{stats['mean']:.1f}",
            stats["p10"],
            stats["median"],
            stats["p90"],
            stats["max"],
        )
        rows.append(
            "<TR>" + "".join(f'<TD><FONT POINT-SIZE="11">{v}</FONT></TD>' for v in values) + "</TR>"
        )
    rows.append(
        f'<TR><TD COLSPAN="{len(header)}" ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#555555">'
        "ρ: spectral radius of the expected-offspring matrix. Below 1 = finite expected size.</FONT></TD></TR>"
    )
    rows.append("</TABLE>")
    return "".join(rows)


def column(cards):
    cells = "".join(f'<TR><TD ALIGN="LEFT" VALIGN="TOP">{card}</TD></TR>' for card in cards)
    return f'<TABLE BORDER="0" CELLSPACING="14" CELLPADDING="0">{cells}</TABLE>'


def render(output, runs):
    with tempfile.TemporaryDirectory() as tmp:
        images = {}
        for symbol, rule in GRAMMAR.items():
            for idx, var in enumerate(rule["variants"]):
                target = Path(tmp) / f"{symbol}_{idx}.png"
                run_dot(variant_dot(symbol, var), target)
                images[(symbol, idx)] = target

        columns = [
            [instructions_card(), legend_card()] + [rule_card(s, images) for s in COLUMNS[0]]
        ]
        columns.append(
            [rule_card(s, images) for s in COLUMNS[1]]
            + [stats_card(runs)]
            + [rule_card(s, images) for s in COLUMNS[2]]
        )
        columns.append([rule_card(s, images) for s in COLUMNS[3]])

        title = (
            '<TR><TD COLSPAN="3" ALIGN="LEFT"><FONT POINT-SIZE="24"><B>Combined Zelda dungeon grammar</B></FONT>'
            + font("   Post30 structure + Post24 locks · size presets S / M / L", 13, "#555555")
            + "</TD></TR>"
        )
        # Each column is rendered on its own so cards keep their natural height
        column_images = []
        for idx, cards in enumerate(columns):
            target = Path(tmp) / f"column_{idx}.png"
            run_dot(
                f'digraph c {{ bgcolor=transparent; pad=0; node [shape=plaintext fontname="{FONT}"]; '
                f"c [label=<{column(cards)}>]; }}",
                target,
            )
            column_images.append(target)
        body = "".join(f'<TD VALIGN="TOP"><IMG SRC="{image}"/></TD>' for image in column_images)
        sheet = (
            "digraph sheet {\n"
            f'bgcolor="#eef0f3"; pad=0.3; node [shape=plaintext fontname="{FONT}"];\n'
            f'sheet [label=<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="6">{title}<TR>{body}</TR></TABLE>>];\n'
            "}\n"
        )
        run_dot(sheet, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="refs/combined.png", help="PNG file to write")
    parser.add_argument(
        "--runs", default=5000, type=int, help="Simulated dungeons per preset for the size table"
    )
    args = parser.parse_args()
    render(Path(args.output), args.runs)
