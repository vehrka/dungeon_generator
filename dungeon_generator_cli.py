#!/usr/bin/env python

import argparse
import logging

from dungeon_fx11 import D24, D30

logging.getLogger().setLevel(logging.DEBUG)


def main(known_args, pipeline_args):
    """TODO: Docstring for main.
    :returns: TODO

    """
    if known_args.post30:
        D30(seed=known_args.seed, debug=known_args.debug)
    else:
        D24(seed=known_args.seed, debug=known_args.debug)


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
    parser.add_argument("--debug", action="store_true", help="Debug information")
    known_args, pipeline_args = parser.parse_known_args()

    main(known_args, pipeline_args)
