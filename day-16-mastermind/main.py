#!/usr/bin/env python3
"""Start the table. --frames supports CI without changing gameplay timing."""

import argparse
from ui import MastermindApp


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Day 16: classic Mastermind")
    parser.add_argument("--seed", type=int, help="Reproducible computer secrets")
    parser.add_argument(
        "--demo", action="store_true", help="Start two computer players"
    )
    parser.add_argument(
        "--frames", type=int, default=0, help="Exit after N frames; 0 means unlimited"
    )
    args = parser.parse_args(argv)
    if args.frames < 0:
        parser.error("--frames must be nonnegative")
    return args


def main(argv=None):
    args = parse_args(argv)
    MastermindApp(args.seed, args.demo).run(args.frames)


if __name__ == "__main__":
    main()
