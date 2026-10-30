"""Independent rule examples: expected scores do not come from the scorer."""

import unittest
from collections import Counter
from dataclasses import FrozenInstanceError
from engine import Game, Tile, Placed, PREMIUMS, LETTER_COUNTS, LETTER_VALUES


class RulesTests(unittest.TestCase):
    """Artificial small racks make scoring examples deterministic and readable."""

    def game(
        self,
        words=(
            "AT",
            "CAT",
            "CATS",
            "DOG",
            "TO",
            "ON",
            "NO",
            "AN",
            "IT",
            "IN",
            "AA",
            "AX",
            "OX",
            "QI",
            "ZA",
            "RATE",
            "RATES",
            "RETAINS",
            "TRAIN",
        ),
    ):
        g = Game([("Alice", False), ("Bob", False)], set(words), 42)
        g.current = 0
        return g

    def rack(self, g, letters):
        g.players[g.current].rack = [Tile(letter) for letter in letters]

    def plan(self, word, row=7, col=7, vertical=False):
        return {
            (row + i if vertical else row, col if vertical else col + i): (i, letter)
            for i, letter in enumerate(word)
        }

    def test_distribution_is_exactly_one_hundred(self):
        self.assertEqual(100, sum(LETTER_COUNTS.values()))
        self.assertEqual(2, LETTER_COUNTS["?"])
        self.assertEqual(12, LETTER_COUNTS["E"])
        self.assertEqual(10, LETTER_VALUES["Q"])

    def test_premium_counts_and_centre(self):
        self.assertEqual(
            Counter({1: 24, 2: 12, 3: 17, 4: 8}), Counter(PREMIUMS.values())
        )
        self.assertEqual(3, PREMIUMS[7, 7])
        self.assertEqual(2, PREMIUMS[5, 5])
        self.assertEqual(1, PREMIUMS[6, 6])

    def test_premiums_have_both_reflection_symmetries(self):
        for (r, c), premium in PREMIUMS.items():
            self.assertEqual(premium, PREMIUMS[14 - r, c])
            self.assertEqual(premium, PREMIUMS[r, 14 - c])
            self.assertEqual(premium, PREMIUMS[c, r])

    def test_tile_immutable_and_blank_zero(self):
        tile = Tile("?")
        self.assertEqual(0, Placed(tile, "Z").value)
        with self.assertRaises(FrozenInstanceError):
            tile.letter = "Z"
        with self.assertRaises(ValueError):
            Tile("!")

    def test_all_player_counts_and_initial_inventory(self):
        for count in (2, 3, 4):
            g = Game([(str(i), False) for i in range(count)], {"AT"}, 3)
            inventory = Counter(t.letter for t in g.bag)
            for p in g.players:
                inventory.update(t.letter for t in p.rack)
            self.assertEqual(LETTER_COUNTS, dict(inventory))
            self.assertEqual(100 - 7 * count, len(g.bag))
        for count in (0, 1, 5):
            with self.assertRaises(ValueError):
                Game([("A", False)] * count, {"AT"})

    def test_seed_is_reproducible(self):
        a, b = self.game(), self.game()
        self.assertEqual(a.starting_draws, b.starting_draws)
        self.assertEqual(a.players, b.players)
        self.assertEqual(a.bag, b.bag)

    def test_starting_draw_alphabetical_not_point_value(self):
        g = self.game()

        class Draw:
            def sample(self, bag, count):
                return [Tile("B"), Tile("E")]

        g.rng = Draw()
        self.assertEqual(0, g._starting_player())

    def test_starting_draw_tie_redraws_only_tied_seats(self):
        g = self.game()

        class Draw:
            def __init__(self):
                self.n = 0

            def sample(self, bag, count):
                self.n += 1
                return [Tile("A"), Tile("A")] if self.n == 1 else [Tile("Z"), Tile("?")]

        g.rng = Draw()
        self.assertEqual(1, g._starting_player())

    def test_opening_centre_double_word(self):
        g = self.game()
        self.rack(g, "CAT")
        result = g.preview(self.plan("CAT"))
        self.assertEqual(10, result.score)
        self.assertEqual([("CAT", 10)], result.words)

    def test_preview_has_no_side_effects(self):
        g = self.game()
        self.rack(g, "CAT")
        before = repr(g.players), dict(g.board), list(g.bag), list(g.log), g.current
        g.preview(self.plan("CAT"))
        self.assertEqual(
            before,
            (repr(g.players), dict(g.board), list(g.bag), list(g.log), g.current),
        )

    def test_play_refills_and_advances_once(self):
        g = self.game()
        self.rack(g, "CATXXXX")
        before = len(g.bag)
        self.assertEqual(10, g.play(self.plan("CAT")))
        self.assertEqual(1, g.current)
        self.assertEqual(7, len(g.players[0].rack))
        self.assertEqual(before - 3, len(g.bag))

    def test_opening_must_touch_star(self):
        g = self.game()
        self.rack(g, "AT")
        with self.assertRaises(ValueError):
            g.preview(self.plan("AT", 0, 0))

    def test_single_letter_not_word_even_if_in_dictionary(self):
        g = self.game(("A",))
        self.rack(g, "A")
        with self.assertRaises(ValueError):
            g.preview({(7, 7): (0, "A")})

    def test_new_tiles_one_axis(self):
        g = self.game()
        self.rack(g, "CAT")
        with self.assertRaises(ValueError):
            g.preview({(7, 7): (0, "C"), (7, 8): (1, "A"), (8, 8): (2, "T")})

    def test_no_empty_gap(self):
        g = self.game()
        self.rack(g, "AT")
        with self.assertRaises(ValueError):
            g.preview({(7, 7): (0, "A"), (7, 9): (1, "T")})

    def test_existing_tiles_bridge_new_placements(self):
        g = self.game()
        g.board[7, 8] = Placed(Tile("A"), "A")
        self.rack(g, "CT")
        result = g.preview({(7, 7): (0, "C"), (7, 9): (1, "T")})
        self.assertEqual(10, result.score)

    def test_disconnected_word_rejected(self):
        g = self.game()
        g.board[7, 7] = Placed(Tile("A"), "A")
        self.rack(g, "AT")
        with self.assertRaises(ValueError):
            g.preview(self.plan("AT", 0, 0))

    def test_cannot_overwrite_or_reuse_rack_index(self):
        g = self.game()
        self.rack(g, "AT")
        g.board[7, 7] = Placed(Tile("C"), "C")
        with self.assertRaises(ValueError):
            g.preview(self.plan("AT"))
        with self.assertRaises(ValueError):
            g.preview({(7, 8): (0, "A"), (7, 9): (0, "A")})

    def test_nonblank_cannot_change_letter(self):
        g = self.game()
        self.rack(g, "AT")
        with self.assertRaises(ValueError):
            g.preview({(7, 7): (0, "C"), (7, 8): (1, "T")})

    def test_bad_coordinates_and_indices(self):
        for pos in ((-1, 7), (15, 7), (7.0, 7), (True, 7), (7,)):
            g = self.game()
            self.rack(g, "AT")
            with self.assertRaises(ValueError):
                g.preview({pos: (0, "A")})
        for index in (-1, 7, True, "0"):
            g = self.game()
            self.rack(g, "AT")
            with self.assertRaises(ValueError):
                g.preview({(7, 7): (index, "A")})

    def test_invalid_word_atomic(self):
        g = self.game()
        self.rack(g, "ZZ")
        before = repr(g.players), dict(g.board), list(g.bag), g.current
        with self.assertRaises(ValueError):
            g.play(self.plan("ZZ"))
        self.assertEqual(
            before, (repr(g.players), dict(g.board), list(g.bag), g.current)
        )

    def test_blank_assignment_stays_zero(self):
        g = self.game()
        self.rack(g, "?AT")
        self.assertEqual(
            4, g.play({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        )
        self.assertTrue(g.board[7, 7].blank)
        self.assertEqual("C", g.board[7, 7].letter)

    def test_old_premium_not_reused(self):
        g = self.game()
        g.board = {
            (7, 7): Placed(Tile("C"), "C"),
            (7, 8): Placed(Tile("A"), "A"),
            (7, 9): Placed(Tile("T"), "T"),
        }
        self.rack(g, "S")
        self.assertEqual(6, g.preview({(7, 10): (0, "S")}).score)

    def test_one_tile_two_words(self):
        g = self.game(("AT", "TO"))
        g.board = {(7, 6): Placed(Tile("A"), "A"), (8, 7): Placed(Tile("O"), "O")}
        self.rack(g, "T")
        result = g.preview({(7, 7): (0, "T")})
        self.assertEqual(8, result.score)
        self.assertEqual({"AT", "TO"}, {w for w, s in result.words})

    def test_invalid_cross_word_rejects_entire_move(self):
        g = self.game(("AT",))
        g.board = {(7, 6): Placed(Tile("A"), "A"), (8, 7): Placed(Tile("O"), "O")}
        self.rack(g, "T")
        with self.assertRaises(ValueError):
            g.preview({(7, 7): (0, "T")})

    def test_letter_premium_counts_in_main_and_cross(self):
        g = self.game(("AT", "TO"))
        g.board = {(6, 5): Placed(Tile("A"), "A"), (7, 6): Placed(Tile("O"), "O")}
        self.rack(g, "T")
        result = g.preview({(6, 6): (0, "T")})
        self.assertEqual(6, result.score)  # two (1 + 2×1) words

    def test_bingo_fifty_for_seven_new_tiles(self):
        g = self.game()
        self.rack(g, "RETAINS")
        result = g.preview(self.plan("RETAINS", 7, 4))
        self.assertEqual(64, result.score)

    def test_exchange_requires_seven_in_bag(self):
        g = self.game()
        g.bag = g.bag[:6]
        before = list(g.players[0].rack)
        with self.assertRaises(ValueError):
            g.exchange([0])
        self.assertEqual(before, g.players[0].rack)

    def test_exchange_draws_before_returning(self):
        g = self.game()
        self.rack(g, "ZZZZZZZ")
        g.bag = [Tile("A")] * 7
        g.exchange([0, 1])
        self.assertEqual(["Z"] * 5 + ["A"] * 2, [t.letter for t in g.players[0].rack])
        self.assertEqual(7, len(g.bag))
        self.assertEqual(1, g.current)

    def test_exchange_rejects_duplicates(self):
        g = self.game()
        for indices in ([], [0, 0], [-1], [99], [True]):
            with self.assertRaises(ValueError):
                g.exchange(indices)

    def test_six_scoreless_turns_end_and_deduct_racks(self):
        g = self.game()
        g.players[0].rack = [Tile("Q")]
        g.players[1].rack = [Tile("Z")]
        for _ in range(6):
            g.pass_turn()
        self.assertEqual("gameover", g.phase)
        self.assertEqual([-10, -10], [p.score for p in g.players])
        self.assertEqual([0, 1], g.winner)

    def test_positive_play_resets_scoreless(self):
        g = self.game()
        g.scoreless_turns = 5
        self.rack(g, "AT")
        g.play(self.plan("AT"))
        self.assertEqual(0, g.scoreless_turns)
        self.assertEqual("play", g.phase)

    def test_rack_out_transfers_opponents_tile_values(self):
        g = self.game()
        self.rack(g, "AT")
        g.bag = []
        g.players[1].rack = [Tile("Q"), Tile("?")]
        g.play(self.plan("AT"))
        self.assertEqual("gameover", g.phase)
        self.assertEqual([14, -10], [p.score for p in g.players])
        self.assertEqual([0], g.winner)

    def test_finish_is_idempotent_and_live_commands_rejected(self):
        g = self.game()
        g.finish()
        scores = [p.score for p in g.players]
        g.finish()
        self.assertEqual(scores, [p.score for p in g.players])
        for function in (g.pass_turn, g.shuffle_rack):
            with self.assertRaises(ValueError):
                function()


if __name__ == "__main__":
    unittest.main()
