#!/usr/bin/env python

import argparse
import logging

from dungeon_fx11 import D24, D30

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
    }
    if known_args.post30:
        D30(**dungeon_args)
    else:
        D24(**dungeon_args)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--post24",
        action="store_true",
        default=True,
        help="Generate a Dungeon using the Post24 Grammar",
    )
    parser.add_argument(
        "--post30",
        action="store_true",
        help="Generate a Dungeon using the Post30 Grammar",
    )
    parser.add_argument("--seed", default=None, type=int, help="Seed for the dungeon")
    parser.add_argument(
        "--maxnodes", default=300, type=int, help="Maximum number of nodes to include"
    )
    parser.add_argument(
        "--maxiter", default=200, type=int, help="Maximum number of iterations to perform"
    )
    parser.add_argument("--show-graph", action="store_true", help="Shows graph on generation")
    parser.add_argument("--debug", action="store_true", help="Debug information")
    known_args, other_args = parser.parse_known_args()

    main(known_args)
