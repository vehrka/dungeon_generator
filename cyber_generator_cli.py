#!/usr/bin/env python

import argparse
import logging

from cyberpuzze import Cyber


def main(known_args: argparse.Namespace) -> None:
    """Generates a cyber dungeon with the command line arguments"""
    logging.getLogger().setLevel(logging.DEBUG if known_args.debug else logging.INFO)
    cyber_args = {
        'seed': known_args.seed,
        'show_graph': known_args.show_graph,
        'debug': known_args.debug,
        'maxiter': known_args.maxiter,
        'maxnodes': known_args.maxnodes,
        'reduce': not known_args.no_reduce,
    }
    Cyber(**cyber_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=None, type=int, help="Seed for the dungeon")
    parser.add_argument(
        "--maxnodes", default=300, type=int, help="Maximum number of nodes to include"
    )
    parser.add_argument(
        "--maxiter", default=200, type=int, help="Maximum number of iterations to perform"
    )
    parser.add_argument("--show-graph", action="store_true", help="Shows graph on generation")
    parser.add_argument(
        "--no-reduce", action="store_true", help="Does not reduce n,e,p adjacent elements"
    )
    parser.add_argument("--debug", action="store_true", help="Debug information")
    known_args, other_args = parser.parse_known_args()

    main(known_args)
