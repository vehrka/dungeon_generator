#!/usr/bin/env python

import argparse
import logging

logging.getLogger().setLevel(logging.DEBUG)


def main(known_args, pipeline_args):
    """TODO: Docstring for main.
    :returns: TODO

    """
    pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--post24', type=bool, default=True)
    parser.add_argument('--post30', type=bool, default=False)
    known_args, pipeline_args = parser.parse_known_args()

    main(known_args, pipeline_args)
