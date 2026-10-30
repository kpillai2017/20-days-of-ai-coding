"""Classic Mastermind rules, independent of Pygame and computer strategy.

The maker earns MORE points for a harder secret. Two equal-role rounds form
one match cycle. Keeping these rules outside the interface makes them testable.
"""

import random
from collections import Counter
from dataclasses import dataclass
from enum import Enum

POSITIONS = 4
ATTEMPTS = 10
COLOURS = ("Red", "Yellow", "Green", "Blue", "White", "Black")
NUM_COLOURS = len(COLOURS)


class Phase(str, Enum):
    """Named phases prevent entering a guess before a secret has been locked."""

    SETTING = "setting"
    GUESSING = "guessing"
    ROUND_OVER = "round_over"
    MATCH_OVER = "match_over"


@dataclass
class PlayerState:
    """Controller and cumulative maker score; no score belongs to a colour."""

    name: str
    is_ai: bool
    score: int = 0


def validate_code(code):
    """Freeze exactly four colour indices; bool is deliberately not an integer."""
    if not isinstance(code, (tuple, list)) or len(code) != POSITIONS:
        raise ValueError("Fill all four holes with colours 1–6.")
    if any(type(c) is not int or not 0 <= c < NUM_COLOURS for c in code):
        raise ValueError(
            "Fill all four holes using one of the six colours for each peg."
        )
    return tuple(code)


def score(secret, guess):
    """Return (exact black pins, colour-only white pins), never position hints.

    The total colour overlap is the sum of the smaller counts for each colour.
    Exact matches are already part of that overlap: subtract them ONCE to get
    white pins. This avoids awarding two pins for the same physical peg.
    Example: R R G B versus R G R Y gives one black and two white pins.
    """
    secret, guess = validate_code(secret), validate_code(guess)
    black = sum(a == b for a, b in zip(secret, guess))
    overlap = sum((Counter(secret) & Counter(guess)).values())
    return black, overlap - black


class Match:
    """Two seats, any human/computer combination, with alternating maker roles.

    A completed round awards its maker one point per guess, plus one if the
    code survived all ten guesses. The highest cumulative maker score wins.
    Finishing a round is separate from advancing it, so the UI can reveal the
    secret and explain the score before clearing the physical-looking board.
    """

    def __init__(self, names=None, seed=None, rounds_per_player=1, *, players=None):
        # `players` is an explicit convenience for non-graphical examples/tests.
        names = names if names is not None else players
        if not isinstance(names, (list, tuple)) or len(names) != 2:
            raise ValueError("Mastermind needs exactly two players.")
        if type(rounds_per_player) is not int or not 1 <= rounds_per_player <= 5:
            raise ValueError("Choose one to five maker rounds per player.")
        self.players = []
        for entry in names:
            if isinstance(entry, PlayerState):
                name, is_ai = entry.name, entry.is_ai
            else:
                if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                    raise ValueError("A player needs a name and controller.")
                name, is_ai = entry
            if (
                not isinstance(name, str)
                or not name.strip()
                or len(name.strip()) > 24
                or any(not c.isprintable() for c in name)
            ):
                raise ValueError("Use a printable player name of 1–24 characters.")
            if type(is_ai) is not bool:
                raise ValueError("A controller must be human or computer.")
            self.players.append(PlayerState(name.strip(), is_ai))
        if self.players[0].name.casefold() == self.players[1].name.casefold():
            raise ValueError("Give the players different names.")
        self.seed = seed
        self.rng = random.Random(seed)
        self.total_rounds = 2 * rounds_per_player
        self.round_number = 1
        self.maker, self.breaker = 0, 1
        self.phase = Phase.SETTING
        self.secret = None
        self.guesses = []
        self.feedback = []
        self.solved = False
        self.winner = []
        self.history = []

    def set_secret(self, code):
        """Lock an immutable copy so later UI edits cannot change the secret."""
        if self.phase != Phase.SETTING:
            raise ValueError("The secret can only be set at the start of a round.")
        self.secret = validate_code(code)
        self.phase = Phase.GUESSING

    def submit_guess(self, code):
        """Validate first, then commit a guess and at most one round award."""
        if self.phase != Phase.GUESSING:
            raise ValueError("This round is not accepting guesses.")
        code = validate_code(code)
        feedback = score(self.secret, code)
        self.guesses.append(code)
        self.feedback.append(feedback)
        self.solved = feedback[0] == POSITIONS
        if self.solved or len(self.guesses) == ATTEMPTS:
            self.phase = Phase.ROUND_OVER
            points = len(self.guesses) + (0 if self.solved else 1)
            self.players[self.maker].score += points
            self.history.append(
                {
                    "round": self.round_number,
                    "maker": self.maker,
                    "attempts": len(self.guesses),
                    "solved": self.solved,
                    "points": points,
                }
            )
        return feedback

    def next_round(self):
        """Only equal maker opportunities produce a final winner; ties stand."""
        if self.phase != Phase.ROUND_OVER:
            raise ValueError("Finish this round before advancing.")
        if self.round_number == self.total_rounds:
            self.phase = Phase.MATCH_OVER
            highest = max(p.score for p in self.players)
            self.winner = [i for i, p in enumerate(self.players) if p.score == highest]
            return
        self.round_number += 1
        self.maker, self.breaker = self.breaker, self.maker
        self.phase = Phase.SETTING
        self.secret = None
        self.guesses, self.feedback = [], []
        self.solved = False
