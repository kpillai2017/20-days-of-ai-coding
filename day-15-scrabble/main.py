#!/usr/bin/env python3
"""Launch the local game; a frame limit supports automated headless checks."""

import argparse
from pathlib import Path
from ai import Lexicon
from ui import ScrabbleApp


def parse_args(argv=None):
    """Keep a seed, dictionary and demo mode explicit and reproducible."""
    parser = argparse.ArgumentParser(description="Day 15: classic-English Scrabble")
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--dictionary", type=Path, default=Path(__file__).parent / "words" / "words.txt"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Start four computer players"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="Exit after N frames, not a frame-rate setting",
    )
    args = parser.parse_args(argv)
    if args.frames < 0:
        parser.error("--frames must be nonnegative")
    return args


def main(argv=None):
    """Load the dictionary once; share its immutable trie across games."""
    args = parse_args(argv)
    try:
        lexicon = Lexicon(args.dictionary)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Cannot load dictionary: {error}")
    ScrabbleApp(lexicon, args.seed, args.demo).run(args.frames)


if __name__ == "__main__":
    main()
