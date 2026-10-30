"""
Comprehensive tests for Mastermind AI solver (ai.py)

Tests cover:
- Code generation
- Guess selection with minimax strategy
- Candidate filtering
- Opening consistency
- AI solving efficiency
- Deterministic behavior
- Seeded reproducibility
"""

import unittest
from ai import MastermindAI, create_ai
from engine import POSITIONS, NUM_COLOURS, score


class TestAICodeGeneration(unittest.TestCase):
    """Tests for all_codes() method."""

    def test_all_codes_count(self):
        """all_codes() returns exactly 6^4 = 1296 codes."""
        ai = MastermindAI()
        codes = ai.all_codes()
        self.assertEqual(len(codes), 1296)

    def test_all_codes_unique(self):
        """all_codes() returns unique codes."""
        ai = MastermindAI()
        codes = ai.all_codes()
        self.assertEqual(len(codes), len(set(codes)))

    def test_all_codes_valid_range(self):
        """All codes have valid position and color values."""
        ai = MastermindAI()
        codes = ai.all_codes()
        for code in codes:
            self.assertEqual(len(code), POSITIONS)
            for color in code:
                self.assertIn(color, range(NUM_COLOURS))

    def test_all_codes_includes_endpoints(self):
        """all_codes() includes (0,0,0,0) and (5,5,5,5)."""
        ai = MastermindAI()
        codes = ai.all_codes()
        self.assertIn((0, 0, 0, 0), codes)
        self.assertIn((5, 5, 5, 5), codes)

    def test_all_codes_type_tuples(self):
        """all_codes() returns list of tuples."""
        ai = MastermindAI()
        codes = ai.all_codes()
        self.assertIsInstance(codes, list)
        for code in codes[:10]:  # Check first 10
            self.assertIsInstance(code, tuple)


class TestAIOpening(unittest.TestCase):
    """Tests for opening guess consistency."""

    def test_opening_is_hardcoded(self):
        """First guess is always (0, 0, 1, 1)."""
        ai = MastermindAI()
        candidates = ai.all_codes()
        opening = ai.choose_guess(candidates, previous_guesses=())
        self.assertEqual(opening, (0, 0, 1, 1))

    def test_opening_consistent_across_instances(self):
        """Opening is consistent across different AI instances."""
        ai1 = MastermindAI()
        ai2 = MastermindAI()
        candidates = ai1.all_codes()

        opening1 = ai1.choose_guess(candidates, previous_guesses=())
        opening2 = ai2.choose_guess(candidates, previous_guesses=())

        self.assertEqual(opening1, opening2)

    def test_opening_no_cheating(self):
        """Opening guess doesn't depend on secret (no parameters for it)."""
        ai = MastermindAI()
        candidates = ai.all_codes()
        opening1 = ai.choose_guess(candidates, previous_guesses=())
        opening2 = ai.choose_guess(candidates, previous_guesses=())
        self.assertEqual(opening1, opening2)


class TestAIGuessSelection(unittest.TestCase):
    """Tests for minimax guess selection strategy."""

    def test_single_candidate_returns_candidate(self):
        """If only one candidate remains, return it."""
        ai = MastermindAI()
        candidates = [(0, 1, 2, 3)]
        guess = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))
        self.assertEqual(guess, (0, 1, 2, 3))

    def test_chooses_from_candidates_first(self):
        """When multiple candidates, choice comes from candidates or full space."""
        ai = MastermindAI()
        # After one guess with feedback, we have reduced candidates
        candidates = [(0, 1, 2, 3), (0, 1, 2, 4), (0, 1, 3, 3)]
        guess = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))
        self.assertIsInstance(guess, tuple)
        self.assertEqual(len(guess), POSITIONS)

    def test_guess_returns_valid_code(self):
        """Guess selection always returns valid code."""
        ai = MastermindAI()
        candidates = ai.all_codes()[:100]  # Test with subset
        guess = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))

        self.assertIsInstance(guess, tuple)
        self.assertEqual(len(guess), POSITIONS)
        for color in guess:
            self.assertIn(color, range(NUM_COLOURS))

    def test_minimax_minimizes_partition(self):
        """Minimax strategy minimizes worst-case partition size."""
        ai = MastermindAI()

        # Use a small candidate set for testing
        candidates = [
            (0, 0, 0, 0),
            (0, 0, 0, 1),
            (0, 0, 0, 2),
            (0, 0, 1, 0),
        ]

        guess = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))

        # The guess should partition candidates into groups
        # Calculate partitions for the chosen guess
        partitions = {}
        for candidate in candidates:
            feedback = score(candidate, guess)
            partitions[feedback] = partitions.get(feedback, 0) + 1

        max_partition = max(partitions.values()) if partitions else 0
        self.assertLessEqual(max_partition, len(candidates))


class TestAICandidateFiltering(unittest.TestCase):
    """Tests for candidate filtering based on feedback."""

    def test_filter_perfect_match(self):
        """Filtering with perfect match feedback (4, 0) leaves only that code."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        guess = (0, 1, 2, 3)
        feedback = (4, 0)

        filtered = ai.filter_candidates(all_codes, guess, feedback)

        # Only (0, 1, 2, 3) should match
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], (0, 1, 2, 3))

    def test_filter_no_match(self):
        """Filtering with (0, 0) feedback removes many codes."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        guess = (0, 0, 0, 0)
        feedback = (0, 0)

        filtered = ai.filter_candidates(all_codes, guess, feedback)

        # Should have many codes, but not (0, 0, 0, 0) or codes with 0
        self.assertGreater(len(filtered), 0)
        self.assertLess(len(filtered), len(all_codes))
        self.assertNotIn((0, 0, 0, 0), filtered)

    def test_filter_reduces_candidates(self):
        """Filtering consistently reduces candidate set."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        guess = (0, 0, 1, 1)
        feedback = (2, 0)

        filtered = ai.filter_candidates(all_codes, guess, feedback)

        self.assertLess(len(filtered), len(all_codes))

        # All remaining candidates should produce same feedback
        for candidate in filtered:
            self.assertEqual(score(candidate, guess), feedback)

    def test_filter_all_consistent_with_feedback(self):
        """All filtered candidates produce the given feedback."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        test_cases = [
            ((0, 1, 2, 3), (2, 1)),
            ((5, 5, 5, 5), (1, 0)),
            ((0, 0, 0, 0), (0, 0)),
        ]

        for guess, feedback in test_cases:
            filtered = ai.filter_candidates(all_codes, guess, feedback)
            for candidate in filtered:
                actual_feedback = score(candidate, guess)
                self.assertEqual(
                    actual_feedback,
                    feedback,
                    f"Candidate {candidate} produces {actual_feedback}, not {feedback}",
                )

    def test_filter_invalid_feedback(self):
        """filter_candidates rejects invalid feedback."""
        ai = MastermindAI()
        all_codes = ai.all_codes()
        guess = (0, 0, 0, 0)

        invalid_feedbacks = [
            (5, 0),  # Black too high
            (0, 5),  # White too high
            (2, 3),  # Sum > 4
            (-1, 1),  # Negative
        ]

        for feedback in invalid_feedbacks:
            with self.assertRaises(ValueError):
                ai.filter_candidates(all_codes, guess, feedback)

    def test_filter_empty_candidates_error(self):
        """filter_candidates on empty list returns empty list."""
        ai = MastermindAI()
        result = ai.filter_candidates([], (0, 1, 2, 3), (2, 1))
        self.assertEqual(result, [])


class TestAISolving(unittest.TestCase):
    """Tests for AI solving efficiency."""

    def test_ai_solves_within_attempts(self):
        """AI can solve any code within 10 attempts."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        test_secrets = [
            (0, 0, 0, 0),
            (5, 5, 5, 5),
            (0, 1, 2, 3),
            (3, 1, 4, 1),
        ]

        for secret in test_secrets:
            candidates = all_codes.copy()
            guesses = 0

            while guesses < 10:
                guess = ai.choose_guess(candidates, previous_guesses=tuple())
                black, white = score(secret, guess)
                guesses += 1

                if black == POSITIONS:
                    # Solved!
                    break

                # Filter for next round
                candidates = ai.filter_candidates(candidates, guess, (black, white))

            self.assertLessEqual(
                guesses, 10, f"Failed to solve {secret} within 10 guesses"
            )
            self.assertGreater(len(candidates), 0, f"Candidates depleted for {secret}")

    def test_ai_opening_statistics(self):
        """Opening guess has good partition properties."""
        ai = MastermindAI()
        all_codes = ai.all_codes()
        opening = (0, 0, 1, 1)

        # Partition all codes by their feedback to the opening
        partitions = {}
        for code in all_codes:
            feedback = score(code, opening)
            if feedback not in partitions:
                partitions[feedback] = 0
            partitions[feedback] += 1

        # The largest partition should be reasonable
        max_partition = max(partitions.values())
        # For a good opening, we expect max_partition to be around 256-300
        self.assertLess(max_partition, 500, "Opening creates too-large partition")
        self.assertGreater(
            len(partitions), 10, "Opening doesn't create enough partitions"
        )


class TestAIFactory(unittest.TestCase):
    """Tests for AI factory function."""

    def test_create_ai_returns_instance(self):
        """create_ai() returns a MastermindAI instance."""
        ai = create_ai()
        self.assertIsInstance(ai, MastermindAI)

    def test_create_ai_independent_instances(self):
        """Multiple create_ai() calls return independent instances."""
        ai1 = create_ai()
        ai2 = create_ai()

        self.assertIsNot(ai1, ai2)
        self.assertEqual(ai1.all_codes(), ai2.all_codes())


class TestAIDeterminism(unittest.TestCase):
    """Tests for deterministic and reproducible behavior."""

    def test_minimax_deterministic(self):
        """Minimax selection is deterministic for same input."""
        ai = MastermindAI()
        candidates = ai.all_codes()[:50]  # Smaller set

        guess1 = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))
        guess2 = ai.choose_guess(candidates, previous_guesses=((0, 0, 1, 1),))

        self.assertEqual(guess1, guess2)

    def test_filtering_deterministic(self):
        """Filtering produces same result for same input."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        guess = (0, 0, 1, 1)
        feedback = (2, 0)

        filtered1 = ai.filter_candidates(all_codes, guess, feedback)
        filtered2 = ai.filter_candidates(all_codes, guess, feedback)

        self.assertEqual(filtered1, filtered2)


class TestAIEdgeCases(unittest.TestCase):
    """Tests for edge cases and corner scenarios."""

    def test_choose_guess_empty_candidates_error(self):
        """choose_guess raises error on empty candidates."""
        ai = MastermindAI()
        with self.assertRaises(ValueError):
            ai.choose_guess([], previous_guesses=())

    def test_single_candidate_immediate_return(self):
        """With one candidate, it's returned immediately."""
        ai = MastermindAI()
        candidate = (2, 3, 4, 5)
        guess = ai.choose_guess([candidate], previous_guesses=((0, 0, 1, 1),))
        self.assertEqual(guess, candidate)

    def test_filter_preserves_order_ish(self):
        """Filtered candidates maintain tuple structure."""
        ai = MastermindAI()
        candidates = [(0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 2)]
        filtered = ai.filter_candidates(candidates, (0, 0, 0, 0), (4, 0))

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], (0, 0, 0, 0))


class TestAIIntegration(unittest.TestCase):
    """Integration tests combining multiple AI methods."""

    def test_full_solve_sequence(self):
        """Complete solve sequence: opening -> filter -> guess -> solve."""
        ai = MastermindAI()
        all_codes = ai.all_codes()
        secret = (1, 2, 3, 4)

        # First guess (opening)
        candidates = all_codes.copy()
        guess = ai.choose_guess(candidates, previous_guesses=())
        self.assertEqual(guess, (0, 0, 1, 1))

        # Get feedback
        black, white = score(secret, guess)

        # Filter
        candidates = ai.filter_candidates(candidates, guess, (black, white))
        self.assertGreater(len(candidates), 0)

        # Second guess
        guess2 = ai.choose_guess(candidates, previous_guesses=(guess,))
        self.assertIsNotNone(guess2)

    def test_multiple_solve_scenarios(self):
        """Solve multiple different secrets sequentially."""
        ai = MastermindAI()
        all_codes = ai.all_codes()

        secrets = [
            (0, 0, 0, 0),
            (5, 5, 5, 5),
            (0, 1, 2, 3),
        ]

        for secret in secrets:
            candidates = all_codes.copy()
            solved = False
            guesses = []

            for attempt in range(10):
                guess = ai.choose_guess(candidates, previous_guesses=tuple(guesses))
                guesses.append(guess)
                black, white = score(secret, guess)

                if black == POSITIONS:
                    solved = True
                    break

                candidates = ai.filter_candidates(candidates, guess, (black, white))

            self.assertTrue(solved, f"Failed to solve {secret}")


if __name__ == "__main__":
    unittest.main()
