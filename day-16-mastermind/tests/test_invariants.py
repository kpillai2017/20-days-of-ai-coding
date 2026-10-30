"""Independent scoring oracle, atomic validation and complete match regression."""

import itertools
import random
import unittest
from engine import Match, score, Phase
from ai import all_codes, choose_guess, filter_candidates


class RuleInvariants(unittest.TestCase):
    def test_feedback_against_remove_matched_pegs_oracle(self):
        # Independent algorithm: remove exact positions, then consume one peg
        # at a time. Compare every pair over a smaller three-colour alphabet.
        codes = list(itertools.product(range(3), repeat=4))
        for secret in codes:
            for guess in codes:
                black = sum(a == b for a, b in zip(secret, guess))
                remaining = [a for a, b in zip(secret, guess) if a != b]
                white = 0
                for a, b in zip(secret, guess):
                    if a != b and b in remaining:
                        remaining.remove(b)
                        white += 1
                self.assertEqual((black, white), score(secret, guess))

    def test_awards_failure_tenth_solution_highest_total_and_once(self):
        match = Match([("Alice", False), ("Bot", True)])
        match.set_secret((0, 0, 0, 0))
        for _ in range(10):
            match.submit_guess((1, 1, 1, 1))
        self.assertEqual(11, match.players[0].score)
        with self.assertRaises(ValueError):
            match.submit_guess((0, 0, 0, 0))
        self.assertEqual(11, match.players[0].score)
        match.next_round()
        match.set_secret((0, 0, 0, 0))
        for _ in range(9):
            match.submit_guess((1, 1, 1, 1))
        match.submit_guess((0, 0, 0, 0))
        self.assertEqual(10, match.players[1].score)
        match.next_round()
        self.assertEqual([0], match.winner)
        self.assertEqual([11, 10], [p.score for p in match.players])

    def test_invalid_codes_atomic_and_mutable_input_frozen(self):
        match = Match([("A", False), ("B", False)])
        for invalid in ((True, 0, 0, 0), (0, 1, 2), None, (0, 1, 2, 6)):
            with self.assertRaises(ValueError):
                match.set_secret(invalid)
            self.assertIsNone(match.secret)
        draft = [0, 1, 2, 3]
        match.set_secret(draft)
        draft[0] = 5
        self.assertEqual((0, 1, 2, 3), match.secret)
        with self.assertRaises(ValueError):
            match.submit_guess((0, 0, None, 0))
        self.assertEqual([], match.guesses)

    def test_player_validation(self):
        for names, rounds in (
            ([("A", False)], 1),
            ([("A", False), ("a", True)], 1),
            ([("A", False), ("B", True)], True),
            ([("A", False), ("B", True)], 0),
            ([("A", False), ("B", True)], 6),
        ):
            with self.assertRaises(ValueError):
                Match(names, rounds_per_player=rounds)

    def test_seeded_computer_matches_equal_roles_and_public_filter(self):
        rng = random.Random(42)
        for _ in range(4):
            match = Match([("Copper", True), ("Brass", True)], rounds_per_player=2)
            while match.phase != Phase.MATCH_OVER:
                match.set_secret(tuple(rng.randrange(6) for _ in range(4)))
                candidates = all_codes()
                while match.phase == Phase.GUESSING:
                    guess = choose_guess(candidates, match.guesses)
                    feedback = match.submit_guess(guess)
                    candidates = filter_candidates(candidates, guess, feedback)
                    self.assertIn(match.secret, candidates)
                self.assertTrue(match.solved)
                match.next_round()
            self.assertEqual(4, len(match.history))
            self.assertEqual([0, 1, 0, 1], [r["maker"] for r in match.history])
            self.assertEqual(
                sum(r["points"] for r in match.history),
                sum(p.score for p in match.players),
            )


if __name__ == "__main__":
    unittest.main()
