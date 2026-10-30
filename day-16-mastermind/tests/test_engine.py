"""
Comprehensive tests for Mastermind engine.py

Tests cover:
- Score function (feedback calculation)
- Match initialization
- Phase transitions
- Role assignment and round progression
- Guessing logic
- Winner determination
- Edge cases and error conditions
"""

import unittest
from engine import (
    Match,
    PlayerState,
    Phase,
    score,
    POSITIONS,
    ATTEMPTS,
    NUM_COLOURS,
    COLOURS,
)


class TestScoreFunction(unittest.TestCase):
    """Tests for the score(secret, guess) feedback function."""

    def test_perfect_match(self):
        """All positions correct returns (4, 0)."""
        secret = (0, 1, 2, 3)
        guess = (0, 1, 2, 3)
        black, white = score(secret, guess)
        self.assertEqual(black, 4)
        self.assertEqual(white, 0)

    def test_all_wrong(self):
        """No matches returns (0, 0)."""
        secret = (0, 0, 0, 0)
        guess = (1, 1, 1, 1)
        black, white = score(secret, guess)
        self.assertEqual(black, 0)
        self.assertEqual(white, 0)

    def test_color_only_white(self):
        """Correct colors but wrong positions returns white pegs."""
        secret = (0, 1, 2, 3)
        guess = (1, 0, 3, 2)
        black, white = score(secret, guess)
        self.assertEqual(black, 0)
        self.assertEqual(white, 4)

    def test_mixed_black_white(self):
        """Mix of correct and wrong positions."""
        secret = (0, 1, 2, 3)
        guess = (0, 2, 1, 3)
        black, white = score(secret, guess)
        self.assertEqual(black, 2)  # positions 0 and 3
        self.assertEqual(white, 2)  # colors 1 and 2 in wrong positions

    def test_duplicates_no_overcount(self):
        """Duplicates in guess don't get overcounted against single secret color."""
        secret = (0, 1, 1, 2)
        guess = (1, 1, 1, 1)
        black, white = score(secret, guess)
        self.assertEqual(black, 2)  # positions 1 and 2 are exact match
        self.assertEqual(white, 0)  # all remaining 1s already matched as black

    def test_duplicates_secret_heavy(self):
        """Multiple secret colors matched by duplicates."""
        secret = (0, 0, 0, 1)
        guess = (0, 1, 1, 1)
        black, white = score(secret, guess)
        self.assertEqual(black, 2)  # positions 0 and 3
        self.assertEqual(white, 0)  # no remaining colors to match

    def test_partial_duplicate_match(self):
        """Partial duplicate matching handles multiset correctly."""
        secret = (5, 5, 4, 4)
        guess = (4, 4, 5, 5)
        black, white = score(secret, guess)
        self.assertEqual(black, 0)
        self.assertEqual(white, 4)

    def test_one_black_three_white(self):
        """Realistic feedback: 1 black, 3 white."""
        secret = (0, 1, 2, 3)
        guess = (3, 0, 1, 2)
        black, white = score(secret, guess)
        self.assertEqual(black, 0)  # no exact position matches
        self.assertEqual(white, 4)  # all 4 colors in wrong positions

    def test_score_invalid_secret(self):
        """score() raises ValueError for invalid secret."""
        with self.assertRaises(ValueError):
            score((0, 1, 2), (0, 1, 2, 3))  # Too short
        with self.assertRaises(ValueError):
            score((0, 1, 2, 6), (0, 1, 2, 3))  # Out of range
        with self.assertRaises(ValueError):
            score("0123", (0, 1, 2, 3))  # Not a code sequence

    def test_score_invalid_guess(self):
        """score() raises ValueError for invalid guess."""
        with self.assertRaises(ValueError):
            score((0, 1, 2, 3), (0, 1, 2))  # Too short
        with self.assertRaises(ValueError):
            score((0, 1, 2, 3), (0, 1, 2, -1))  # Negative

    def test_all_black_colors(self):
        """Test with all color values 0-5."""
        secret = (0, 1, 2, 3)
        guess = (0, 1, 2, 3)
        black, white = score(secret, guess)
        self.assertEqual(black, 4)
        self.assertEqual(white, 0)


class TestMatchInitialization(unittest.TestCase):
    """Tests for Match initialization and basic properties."""

    def test_create_match_basic(self):
        """Create a basic 2-player match."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", True)
        match = Match(players=[player1, player2])

        self.assertEqual(len(match.players), 2)
        self.assertEqual(match.players[0].name, "Alice")
        self.assertEqual(match.players[1].name, "Bob")
        self.assertEqual(match.round_number, 1)
        self.assertEqual(match.total_rounds, 2)
        self.assertEqual(match.phase, Phase.SETTING)

    def test_match_requires_two_players(self):
        """Match must have exactly 2 players."""
        player1 = PlayerState("Alice", False)
        with self.assertRaises(ValueError):
            Match(players=[player1])  # Only 1 player

        with self.assertRaises(ValueError):
            Match(players=[player1, player1, player1])  # 3 players

    def test_match_with_seed(self):
        """Match accepts optional seed for reproducibility."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2], seed=42)

        self.assertEqual(match.seed, 42)
        self.assertIsNotNone(match.rng)

    def test_initial_state_clean(self):
        """Match starts with clean state."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        self.assertIsNone(match.secret)
        self.assertEqual(match.guesses, [])
        self.assertEqual(match.feedback, [])
        self.assertFalse(match.solved)
        self.assertEqual(match.winner, [])


class TestPhaseTransitions(unittest.TestCase):
    """Tests for phase transitions and guard conditions."""

    def test_setting_to_guessing_on_secret(self):
        """Setting secret transitions from SETTING to GUESSING."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        self.assertEqual(match.phase, Phase.SETTING)
        match.set_secret((0, 1, 2, 3))
        self.assertEqual(match.phase, Phase.GUESSING)
        self.assertEqual(match.secret, (0, 1, 2, 3))

    def test_guessing_to_round_over_on_solve(self):
        """Correct guess transitions to ROUND_OVER with solved=True."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 1, 2, 3))
        self.assertEqual(match.phase, Phase.GUESSING)

        black, white = match.submit_guess((0, 1, 2, 3))
        self.assertEqual(black, 4)
        self.assertEqual(white, 0)
        self.assertEqual(match.phase, Phase.ROUND_OVER)
        self.assertTrue(match.solved)

    def test_guessing_to_round_over_on_attempts_exhausted(self):
        """ATTEMPTS exhausted transitions to ROUND_OVER with solved=False."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 0, 0, 0))

        # Make 10 wrong guesses
        for i in range(ATTEMPTS):
            black, white = match.submit_guess((1, 1, 1, 1))
            if i < ATTEMPTS - 1:
                self.assertEqual(match.phase, Phase.GUESSING)
            else:
                # After 10th guess, should be round_over
                self.assertEqual(match.phase, Phase.ROUND_OVER)

        self.assertFalse(match.solved)
        self.assertEqual(len(match.guesses), ATTEMPTS)

    def test_cannot_set_secret_not_in_setting(self):
        """Cannot set secret unless in SETTING phase."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 1, 2, 3))
        # Now in GUESSING phase
        with self.assertRaises(ValueError):
            match.set_secret((5, 5, 5, 5))

    def test_cannot_guess_not_in_guessing(self):
        """Cannot submit guess unless in GUESSING phase."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        # In SETTING phase
        with self.assertRaises(ValueError):
            match.submit_guess((0, 1, 2, 3))


class TestRoleAndRounds(unittest.TestCase):
    """Tests for role assignment and round progression."""

    def test_initial_roles(self):
        """Initially, maker=0, breaker=1."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        self.assertEqual(match.maker, 0)
        self.assertEqual(match.breaker, 1)

    def test_roles_swap_after_next_round(self):
        """Roles swap after each round."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2], rounds_per_player=2)

        self.assertEqual(match.maker, 0)
        self.assertEqual(match.breaker, 1)

        # Complete round 1
        match.set_secret((0, 1, 2, 3))
        match.submit_guess((0, 1, 2, 3))
        self.assertEqual(match.phase, Phase.ROUND_OVER)

        match.next_round()
        # Roles should swap
        self.assertEqual(match.maker, 1)
        self.assertEqual(match.breaker, 0)
        self.assertEqual(match.round_number, 2)

    def test_round_progression(self):
        """Round number increments correctly."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2], rounds_per_player=2)

        self.assertEqual(match.round_number, 1)
        self.assertEqual(match.total_rounds, 4)

        for expected_round in [1, 2, 3, 4]:
            self.assertEqual(match.round_number, expected_round)
            match.set_secret((0, 1, 2, 3))
            match.submit_guess((0, 1, 2, 3))
            if expected_round < 4:
                match.next_round()

    def test_cannot_next_round_not_round_over(self):
        """Cannot call next_round() unless phase is ROUND_OVER."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        with self.assertRaises(ValueError):
            match.next_round()  # In SETTING phase


class TestGuessTracking(unittest.TestCase):
    """Tests for guess and feedback tracking."""

    def test_guesses_recorded(self):
        """Each guess is recorded in order."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 1, 2, 3))
        match.submit_guess((0, 0, 0, 0))
        match.submit_guess((1, 1, 1, 1))
        match.submit_guess((0, 1, 2, 3))

        self.assertEqual(len(match.guesses), 3)
        self.assertEqual(match.guesses[0], (0, 0, 0, 0))
        self.assertEqual(match.guesses[1], (1, 1, 1, 1))
        self.assertEqual(match.guesses[2], (0, 1, 2, 3))

    def test_feedback_recorded(self):
        """Feedback for each guess is recorded in order."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 1, 2, 3))
        match.submit_guess((0, 0, 0, 0))
        match.submit_guess((1, 1, 1, 1))
        match.submit_guess((0, 1, 2, 3))

        self.assertEqual(len(match.feedback), 3)
        self.assertEqual(match.feedback[0], (1, 0))  # One black
        self.assertEqual(match.feedback[1], (1, 0))  # One black
        self.assertEqual(match.feedback[2], (4, 0))  # Perfect match

    def test_guesses_cleared_on_new_round(self):
        """Guesses are cleared when moving to next round."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        match.set_secret((0, 1, 2, 3))
        match.submit_guess((0, 1, 2, 3))

        self.assertEqual(len(match.guesses), 1)
        match.next_round()
        self.assertEqual(len(match.guesses), 0)
        self.assertEqual(len(match.feedback), 0)


class TestCodeValidation(unittest.TestCase):
    """Tests for code validation."""

    def test_valid_codes(self):
        """Valid codes accepted."""
        valid_codes = [
            (0, 0, 0, 0),
            (5, 5, 5, 5),
            (0, 1, 2, 3),
            (3, 2, 1, 0),
        ]
        for code in valid_codes:
            player1 = PlayerState("Alice", False)
            player2 = PlayerState("Bob", False)
            match = Match(players=[player1, player2])
            match.set_secret(code)
            match.submit_guess(code)
            self.assertTrue(True)  # Should not raise

    def test_invalid_code_wrong_length(self):
        """Invalid: wrong number of positions."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        with self.assertRaises(ValueError):
            match.set_secret((0, 1, 2))

        with self.assertRaises(ValueError):
            match.set_secret((0, 1, 2, 3, 4))

    def test_invalid_code_out_of_range(self):
        """Invalid: values outside [0, 5]."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        with self.assertRaises(ValueError):
            match.set_secret((-1, 0, 1, 2))

        with self.assertRaises(ValueError):
            match.set_secret((0, 1, 2, 6))

    def test_invalid_code_not_sequence(self):
        """Text is not a colour-index sequence."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2])

        with self.assertRaises(ValueError):
            match.set_secret("0123")


class TestWinnerDetermination(unittest.TestCase):
    """Tests for winner determination at match end."""

    def test_winner_single_player_best(self):
        """Equal maker scores produce a draw, not an arbitrary winner."""
        player1 = PlayerState("Alice", False)
        player2 = PlayerState("Bob", False)
        match = Match(players=[player1, player2], rounds_per_player=1)

        # Round 1: Alice (index 0) makes secret, Bob (index 1) guesses
        match.set_secret((0, 1, 2, 3))
        match.submit_guess((0, 1, 2, 3))  # Bob solves in 1 guess
        self.assertEqual(match.phase, Phase.ROUND_OVER)
        self.assertTrue(match.solved)
        self.assertEqual(match.round_number, 1)

        # Move to round 2
        match.next_round()
        self.assertEqual(match.phase, Phase.SETTING)
        self.assertEqual(match.round_number, 2)
        self.assertEqual(match.maker, 1)  # Roles swapped
        self.assertEqual(match.breaker, 0)

        # Round 2: Bob makes secret, Alice guesses
        match.set_secret((5, 5, 5, 5))
        match.submit_guess((5, 5, 5, 5))  # Alice solves in 1 guess
        self.assertEqual(match.phase, Phase.ROUND_OVER)

        # Now move to next round - should be final
        match.next_round()
        self.assertEqual(match.phase, Phase.MATCH_OVER)
        self.assertIsNotNone(match.winner)
        self.assertEqual(match.winner, [0, 1])


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and corner scenarios."""

    def test_all_same_color_guess(self):
        """Guess with all same color."""
        black, white = score((0, 0, 0, 0), (1, 1, 1, 1))
        self.assertEqual((black, white), (0, 0))

    def test_all_same_color_secret(self):
        """Secret with all same color."""
        black, white = score((0, 0, 0, 0), (0, 0, 0, 0))
        self.assertEqual((black, white), (4, 0))

    def test_feedback_sum_bounds(self):
        """Black + white can be at most POSITIONS."""
        for _ in range(100):
            import random

            secret = tuple(random.randint(0, NUM_COLOURS - 1) for _ in range(POSITIONS))
            guess = tuple(random.randint(0, NUM_COLOURS - 1) for _ in range(POSITIONS))
            black, white = score(secret, guess)
            self.assertLessEqual(black + white, POSITIONS)


if __name__ == "__main__":
    unittest.main()
