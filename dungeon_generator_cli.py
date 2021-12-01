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
        D30(seed=known_args.seed)
    else:
        D24(seed=known_args.seed)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--post24", action="store_true", default=True)
    parser.add_argument("--post30", action="store_true")
    parser.add_argument("--seed", default=None)
    known_args, pipeline_args = parser.parse_known_args()

    main(known_args, pipeline_args)
