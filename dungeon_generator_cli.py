#!/usr/bin/env python

import argparse
import logging
from pathlib import Path

from dungeon_fx11 import D24, D30, DCombined
from utils.dot_utils import OUTPUT_FORMATS

logging.getLogger().setLevel(logging.DEBUG)


def main(known_args):
    """TODO: Docstring for main.
    :returns: TODO

    """
    dungeon_args = {
        'seed': known_args.seed,
        'show_graph': known_args.show_graph,
        'debug': known_args.debug,
        'maxiter': known_args.maxiter,
        'maxnodes': known_args.maxnodes,
        'reduce': not known_args.no_reduce,
        'output': known_args.output,
        'json': known_args.json,
    }
    if known_args.post24:
        D24(**dungeon_args)
    elif known_args.post30:
        D30(**dungeon_args)
    else:
        DCombined(size=known_args.size, **dungeon_args)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    grammar = parser.add_mutually_exclusive_group()
    grammar.add_argument(
        "--combined",
        action="store_true",
        help="Generate a Dungeon using the Combined Grammar (grammar/combined.py). Default",
    )
    grammar.add_argument(
        "--post24",
        action="store_true",
        help="Generate a Dungeon using the Post24 Grammar (legacy, may be unsolvable)",
    )
    grammar.add_argument(
        "--post30",
        action="store_true",
        help="Generate a Dungeon using the Post30 Grammar (legacy, may be unsolvable)",
    )
    parser.add_argument(
        "--size",
        default="M",
        type=str.upper,
        choices=["S", "M", "L"],
        help="Size preset for the Combined Grammar (case insensitive)",
    )
    parser.add_argument("--seed", default=None, type=int, help="Seed for the dungeon")
    parser.add_argument(
        "--maxnodes", default=300, type=int, help="Maximum number of nodes to include"
    )
    parser.add_argument(
        "--maxiter", default=200, type=int, help="Maximum number of iterations to perform"
    )
    parser.add_argument("--show-graph", action="store_true", help="Shows graph on generation")
    parser.add_argument(
        "--output", default=None, type=Path, help="Saves the graph to a file (.png, .svg or .pdf)"
    )
    parser.add_argument(
        "--json", default=None, type=Path, help="Saves the graph as JSON (rooms, gates, objects)"
    )
    parser.add_argument(
        "--no-reduce", action="store_true", help="Does not reduce n,e,p adjacent elements"
    )
    parser.add_argument("--debug", action="store_true", help="Debug information")
    known_args, other_args = parser.parse_known_args()
    if known_args.output and known_args.output.suffix.lstrip(".").lower() not in OUTPUT_FORMATS:
        parser.error(f"--output must end in one of: {', '.join(OUTPUT_FORMATS)}")

    main(known_args)
