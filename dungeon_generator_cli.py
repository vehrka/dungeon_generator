#!/usr/bin/env python

import argparse
import logging

from dungeon_fx11 import Dungeon

logging.getLogger().setLevel(logging.DEBUG)


def main(known_args, pipeline_args):
    """TODO: Docstring for main.
    :returns: TODO

    """
    if known_args.post30:
        type = "p30"
    else:
        type = "p24"
    Dungeon(type)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--post24", action="store_true", default=True)
    parser.add_argument("--post30", action="store_true")
    known_args, pipeline_args = parser.parse_known_args()

    main(known_args, pipeline_args)
