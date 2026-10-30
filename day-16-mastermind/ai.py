"""A transparent computer codebreaker that only sees guesses and feedback.

This is candidate-only minimax, NOT a claim to reproduce Knuth's five-guess
algorithm (which can consider guesses outside the remaining candidate set).
"""

from collections import Counter
from itertools import product
from engine import NUM_COLOURS, POSITIONS, validate_code


def all_codes():
    """Cartesian product: six choices at each of four positions = 1,296 codes."""
    return list(product(range(NUM_COLOURS), repeat=POSITIONS))


def _feedback(secret, guess):
    """Hot-path equivalent of engine.score; callers already validated codes."""
    black = sum(a == b for a, b in zip(secret, guess))
    overlap = sum(min(secret.count(c), guess.count(c)) for c in range(NUM_COLOURS))
    return black, overlap - black


def filter_candidates(candidates, guess, feedback):
    """Keep only secrets that would have produced the public feedback received."""
    guess = validate_code(guess)
    if (
        not isinstance(feedback, (tuple, list))
        or len(feedback) != 2
        or any(type(n) is not int or n < 0 for n in feedback)
        or sum(feedback) > POSITIONS
    ):
        raise ValueError(
            "Feedback must be two nonnegative pin counts totalling at most four."
        )
    feedback = tuple(feedback)
    return [
        validate_code(c)
        for c in candidates
        if _feedback(validate_code(c), guess) == feedback
    ]


def choose_guess(candidates, previous_guesses=()):
    """Minimise the largest possible remaining bucket; deterministic tie-break.

    After opening R R Y Y, test each remaining candidate as a potential guess.
    Feedback divides possible secrets into buckets; prefer the guess whose
    largest bucket is smallest. Ties use lexicographic colour order. At least
    the guessed candidate disappears after an unsuccessful guess, so the
    candidate set strictly shrinks. No secret code is passed into this function.
    """
    candidates = sorted(set(validate_code(c) for c in candidates))
    if not candidates:
        raise ValueError("No secret is consistent with this feedback history.")
    opening = (0, 0, 1, 1)
    if not previous_guesses and len(candidates) == NUM_COLOURS**POSITIONS:
        return opening
    best_guess, best_size = candidates[0], len(candidates) + 1
    for guess in candidates:
        buckets = Counter()
        for secret in candidates:
            result = _feedback(secret, guess)
            buckets[result] += 1
            # Once this guess is no better than the current best, stop early.
            if buckets[result] >= best_size:
                break
        worst = max(buckets.values())
        if worst < best_size:
            best_guess, best_size = guess, worst
        if best_size == 1:
            break
    return best_guess


class MastermindAI:
    """Small facade for interactive experiments in a Python console."""

    all_codes = staticmethod(all_codes)
    choose_guess = staticmethod(choose_guess)
    filter_candidates = staticmethod(filter_candidates)


def create_ai():
    """No private state: the caller owns its candidate set and public history."""
    return MastermindAI()
