"""Renders the combined grammar (grammar/combined.py) as a single PNG sheet using Graphviz

Each variant is rendered as a small PNG with `dot`, then all of them are assembled into rule
cards inside one HTML-like Graphviz table, together with the legend and the size statistics.

Usage:
    python -m grammar.render [--output refs/combined.png] [--runs 5000]
"""

import argparse
import html
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from grammar.combined import GRAMMAR, PRESETS, Variant, size_stats
from utils.dot_utils import (
    EDGE_STYLE,
    FONT,
    NODE_STYLE,
    card,
    card_header,
    font,
    run_dot,
)

# Sheet layout: rule cards per column (the size table goes between the 2nd and 3rd group)
COLUMNS = (("Start", "E", "R", "S"), ("L",), ("GB", "H"), ("K", "SW", "TG", "IG", "BK"))


def object_label(var: Variant, oid: str) -> str:
    """Name of the object of the variant"""
    return var["objects"][oid][1]


def edge_label(var: Variant, kind: str, oids: list[str]) -> str:
    """Label of a variant edge: the objects it needs"""
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


def variant_dot(symbol: str, var: Variant) -> str:
    """DOT source for one variant diagram"""
    anchors = ("START", "GOAL") if symbol == "Start" else (None, None)
    lines = [
        "digraph G {",
        "rankdir=LR; bgcolor=transparent; nodesep=0.15; ranksep=0.35; pad=0.05;",
        f'node [shape=box style="rounded,filled" fontname="{FONT}" fontsize=11 height=0.3 '
        "width=0.45 penwidth=0];",
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
        direction = "forward" if kind == "one" else "both"
        lines.append(f"{src} -> {dst} [dir={direction} {EDGE_STYLE[kind]}{label_attr}];")
    lines.append("}")
    return "\n".join(lines)


def run_dots(jobs: dict[Path, str]) -> None:
    """Renders the {target: source} DOT jobs in parallel"""
    with ThreadPoolExecutor() as pool:
        list(pool.map(lambda job: run_dot(job[1], job[0]), jobs.items()))


def range_text(var: Variant, preset: str) -> str:
    """d20 range of the variant for the preset"""
    span = var["ranges"].get(preset)
    if not span:
        return "—"
    return str(span[0]) if span[0] == span[1] else f"{span[0]}-{span[1]}"


def rule_card(symbol: str, images: dict[tuple[str, int], Path]) -> str:
    """Card with the variants of a rule"""
    rule = GRAMMAR[symbol]
    kind = " · dead end" if rule["branch"] else ""
    preset_cells = "".join(f"<TD>{font(preset, 9, '#777777')}</TD>" for preset in PRESETS)
    rows = [f"<TR>{preset_cells}<TD></TD><TD></TD></TR>"]
    for idx, var in enumerate(rule["variants"]):
        bg = "#f6f7f9" if idx % 2 else "white"
        cells = "".join(
            f'<TD BGCOLOR="{bg}">{font(range_text(var, preset))}</TD>' for preset in PRESETS
        )
        rows.append(
            f"<TR>{cells}"
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT">{font(html.escape(var["name"]), 9, "#555555")}</TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT"><IMG SRC="{images[(symbol, idx)]}"/></TD></TR>'
        )
    return card(card_header(f"{symbol}()", html.escape(rule["desc"]) + kind, colspan=5), rows)


def legend_card() -> str:
    """Card with the legend of the sheet"""
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
    rooms = (
        "n nothing · e enemy · t trap · p puzzle · c challenge · em mini-boss · eb boss · "
        "gb bonus goal"
    )
    rows = [
        f'<TR><TD BGCOLOR="{NODE_STYLE[kind]["fillcolor"]}" WIDTH="34"> </TD>'
        f'<TD ALIGN="LEFT">{font(text)}</TD></TR>'
        for kind, text in swatches
    ]
    rows += [
        f'<TR><TD>{font(html.escape(symbol), color=color, bold=True)}</TD>'
        f'<TD ALIGN="LEFT">{font(text)}</TD></TR>'
        for symbol, color, text in edges
    ]
    rows.append(f'<TR><TD COLSPAN="2" ALIGN="LEFT">{font(rooms, 9, "#555555")}</TD></TR>')
    return card(card_header("Legend", colspan=2), rows, padding=4)


def instructions_card() -> str:
    """Card with the instructions to use the grammar by hand"""
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
    rows = [f'<TR><TD ALIGN="LEFT">{font(html.escape(line) or " ")}</TD></TR>' for line in text]
    return card(card_header("How to use"), rows, padding=3)


def stats_card(runs: int) -> str:
    """Card with the expected size of each preset"""
    header = ("preset", "ρ", "mean", "p10", "median", "p90", "max")
    rows = ["<TR>" + "".join(f"<TD>{font(h, color='#777777')}</TD>" for h in header) + "</TR>"]
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
        rows.append("<TR>" + "".join(f"<TD>{font(v, 11)}</TD>" for v in values) + "</TR>")
    note = "ρ: spectral radius of the expected-offspring matrix. Below 1 = finite expected size."
    rows.append(
        f'<TR><TD COLSPAN="{len(header)}" ALIGN="LEFT">{font(note, 9, "#555555")}</TD></TR>'
    )
    return card(
        card_header("Expected size", f"rooms before merge, {runs} runs", colspan=len(header)), rows
    )


def column(cards: list[str]) -> str:
    """Table stacking the cards"""
    cells = "".join(f'<TR><TD ALIGN="LEFT" VALIGN="TOP">{card}</TD></TR>' for card in cards)
    return f'<TABLE BORDER="0" CELLSPACING="14" CELLPADDING="0">{cells}</TABLE>'


def render(output: str | Path, runs: int) -> None:
    """Renders the grammar sheet to the output PNG"""
    with tempfile.TemporaryDirectory() as tmp:
        variants = [
            (symbol, idx, var)
            for symbol, rule in GRAMMAR.items()
            for idx, var in enumerate(rule["variants"])
        ]
        images = {(symbol, idx): Path(tmp) / f"{symbol}_{idx}.png" for symbol, idx, _ in variants}
        run_dots({images[(symbol, idx)]: variant_dot(symbol, var) for symbol, idx, var in variants})

        cards = [[rule_card(s, images) for s in group] for group in COLUMNS]
        columns = [
            [instructions_card(), legend_card()] + cards[0],
            cards[1] + [stats_card(runs)] + cards[2],
            cards[3],
        ]

        title = (
            '<TR><TD COLSPAN="3" ALIGN="LEFT">'
            '<FONT POINT-SIZE="24"><B>Combined Zelda dungeon grammar</B></FONT>'
            + font("   Post30 structure + Post24 locks · size presets S / M / L", 13, "#555555")
            + "</TD></TR>"
        )
        # Each column is rendered on its own so cards keep their natural height
        column_images = [Path(tmp) / f"column_{idx}.png" for idx in range(len(columns))]
        run_dots(
            {
                target: "digraph c { bgcolor=transparent; pad=0; "
                f'node [shape=plaintext fontname="{FONT}"]; '
                f"c [label=<{column(col)}>]; }}"
                for target, col in zip(column_images, columns)
            }
        )
        body = "".join(f'<TD VALIGN="TOP"><IMG SRC="{image}"/></TD>' for image in column_images)
        sheet = (
            "digraph sheet {\n"
            f'bgcolor="#eef0f3"; pad=0.3; node [shape=plaintext fontname="{FONT}"];\n'
            'sheet [label=<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="6">'
            f"{title}<TR>{body}</TR></TABLE>>];\n"
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
