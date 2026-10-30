"""Computer searches must produce ordinary legal moves and preserve inventory."""

import unittest
from collections import Counter
from pathlib import Path
from ai import Lexicon, find_move
from engine import Game, Tile, Placed, LETTER_COUNTS


class ComputerTests(unittest.TestCase):
    """Small dictionaries make algorithm tests deterministic and fast."""

    def test_loader_filters_punctuation_numbers_and_one_letter_words(self):
        lex = Lexicon(words=["cat", "AT", "a", "bad-word", "été", "123", "A" * 16])
        self.assertEqual({"CAT", "AT"}, lex.words)

    def test_opening_search_uses_multiple_tiles(self):
        lex = Lexicon(words=["CAT", "AT"])
        g = Game([("A", True), ("B", True)], lex, 1)
        g.players[g.current].rack = [Tile(c) for c in "CAT"]
        move = find_move(g, lex, 0.5)
        self.assertIsNotNone(move)
        self.assertGreaterEqual(len(move), 2)
        self.assertIn((7, 7), move)
        self.assertEqual(10, g.preview(move).score)

    def test_blank_search_and_no_mutation(self):
        lex = Lexicon(words=["QUIZ"])
        g = Game([("A", True), ("B", True)], lex, 1)
        g.players[g.current].rack = [Tile(c) for c in "?UIZ"]
        before = repr(g.players), dict(g.board), list(g.bag)
        move = find_move(g, lex, 0.5)
        self.assertIsNotNone(move)
        self.assertTrue(any(i == 0 and letter == "Q" for i, letter in move.values()))
        self.assertEqual(before, (repr(g.players), dict(g.board), list(g.bag)))

    def test_unplayable_rack_returns_none(self):
        lex = Lexicon(words=["CAT"])
        g = Game([("A", True), ("B", True)], lex, 1)
        g.players[g.current].rack = [Tile("Z")] * 7
        self.assertIsNone(find_move(g, lex, 0.1))

    def test_existing_word_can_be_extended(self):
        lex = Lexicon(words=["CAT", "CATS"])
        g = Game([("A", True), ("B", True)], lex, 1)
        g.board = {(7, 7 + i): Placed(Tile(c), c) for i, c in enumerate("CAT")}
        g.players[g.current].rack = [Tile("S")]
        move = find_move(g, lex, 0.5)
        self.assertEqual({(7, 10): (0, "S")}, move)

    def test_complete_games_all_counts_preserve_one_hundred_tiles(self):
        lex = Lexicon(Path(__file__).resolve().parents[1] / "words" / "words.txt")
        for count in (2, 3, 4):
            for seed in (1, 42):
                g = Game([(str(i), True) for i in range(count)], lex, seed)
                for turn in range(350):
                    if g.phase == "gameover":
                        break
                    move = find_move(g, lex, 0.06)
                    if move:
                        g.play(move)
                    elif len(g.bag) >= 7:
                        g.exchange(list(range(len(g.players[g.current].rack))))
                    else:
                        g.pass_turn()
                    inventory = Counter(tile.letter for tile in g.bag)
                    for player in g.players:
                        inventory.update(tile.letter for tile in player.rack)
                    inventory.update(placed.tile.letter for placed in g.board.values())
                    self.assertEqual(
                        LETTER_COUNTS, dict(inventory), (count, seed, turn)
                    )
                self.assertEqual("gameover", g.phase, (count, seed))
                self.assertTrue(g.winner)


if __name__ == "__main__":
    unittest.main()
