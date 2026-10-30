"""Scoring explanations and word meanings are independent of word legality."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
import pygame
from ai import Lexicon
from engine import Tile, Placed
from ui import ScrabbleApp
from definitions import lookup


class ExplanationTests(unittest.TestCase):
    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["CAT", "AT", "TO", "RETAINS"]), 42)
        self.app.start([("Alice", False), ("Bob", False)])
        self.app.game.current = 0
        self.app.dispatch("ready")
        self.app.game.players[0].rack = [Tile(c) for c in "CATXXXX"]

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        self.app.definition_executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def test_opening_trace_matches_actual_score(self):
        result = self.app.game.preview(
            {(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")}
        )
        part = result.breakdown[0]
        self.assertEqual(["C[3]", "A[1]", "T[1]"], part["terms"])
        self.assertEqual(
            (5, 2, 10), (part["subtotal"], part["multiplier"], part["score"])
        )
        self.assertEqual(["DW ×2"], part["word_bonuses"])
        self.assertEqual(
            result.score, sum(p["score"] for p in result.breakdown) + result.bingo
        )

    def test_blank_and_bingo_explanations(self):
        game = self.app.game
        game.players[0].rack = [Tile(c) for c in "?AT"]
        result = game.preview({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        self.assertEqual("C[blank=0]", result.breakdown[0]["terms"][0])
        game.players[0].rack = [Tile(c) for c in "RETAINS"]
        result = game.preview({(7, 4 + i): (i, c) for i, c in enumerate("RETAINS")})
        self.assertEqual(50, result.bingo)
        self.assertEqual(64, result.score)

    def test_clicking_committed_tile_loads_local_meaning_without_network(self):
        game = self.app.game
        game.board = {(7, 7 + i): Placed(Tile(c), c) for i, c in enumerate("CAT")}
        self.app.render()
        with patch(
            "urllib.request.urlopen", side_effect=AssertionError("No runtime network")
        ):
            rect = self.app.cells[7, 8]
            self.app.event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1)
            )
            self.assertEqual("word", self.app.modal)
            self.app.definition_jobs["CAT"].result(timeout=2)
            self.app.update()
            self.app.render()
        self.assertTrue(self.app.definition_cache["CAT"]["entries"])
        self.assertNotIn(
            "lookup_definition", [command for rect, command in self.app.buttons]
        )

    def test_intersection_lists_both_words(self):
        game = self.app.game
        game.board = {
            (7, 6): Placed(Tile("A"), "A"),
            (7, 7): Placed(Tile("T"), "T"),
            (8, 7): Placed(Tile("O"), "O"),
        }
        self.app.inspect_word((7, 7))
        self.assertEqual(["AT", "TO"], self.app.inspected_words)
        self.app.dispatch("inspect_next")
        self.assertEqual(1, self.app.word_index)

    def test_local_lookup_is_automatic_and_cached(self):
        game = self.app.game
        game.board = {(7, 7): Placed(Tile("A"), "A"), (7, 8): Placed(Tile("T"), "T")}
        result = {
            "status": "Offline Wiktionary definitions",
            "entries": [
                {
                    "text": "A location indicator.",
                    "part": "preposition",
                    "sources": ["https://example.org/at"],
                    "license": {"name": "CC BY-SA"},
                }
            ],
        }
        with patch("ui.lookup", return_value=result) as local:
            self.app.inspect_word((7, 7))
            self.app.definition_jobs["AT"].result(timeout=2)
            self.app.update()
            self.app.inspect_word((7, 8))
            self.assertEqual(1, local.call_count)
        self.assertEqual(result, self.app.definition_cache["AT"])
        self.assertEqual(0, game.players[0].score)

    def test_score_dialog_does_not_commit_draft(self):
        self.app.pending = {(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")}
        self.app.render()
        self.assertIn("score_details", [cmd for rect, cmd in self.app.buttons])
        self.app.dispatch("score_details")
        self.app.render()
        self.assertFalse(self.app.game.board)
        self.assertEqual(0, self.app.game.players[0].score)
        self.assertEqual("score", self.app.modal)

    def test_local_definition_preserves_attribution(self):
        result = lookup("CAT")
        self.assertTrue(result["entries"])
        entry = result["entries"][0]
        self.assertIn("en.wiktionary.org/wiki/", entry["sources"][0])
        self.assertEqual("CC BY-SA 4.0", entry["license"]["name"])

    def test_last_play_survives_pass_and_endgame(self):
        game = self.app.game
        game.play({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        self.assertIn("Alice — CAT (10) = 10 points", self.app.last_play_text())
        game.pass_turn()
        text = self.app.last_play_text()
        self.assertIn("CAT (10)", text)
        self.assertIn("Bob passes", text)
        game.finish()
        self.assertIn("CAT (10)", self.app.last_play_text())

    def test_last_play_records_all_crosswords(self):
        game = self.app.game
        game.board = {(7, 6): Placed(Tile("A"), "A"), (8, 7): Placed(Tile("O"), "O")}
        game.players[0].rack = [Tile("T")]
        game.play({(7, 7): (0, "T")})
        self.assertEqual(
            {"AT", "TO"}, {word for word, score in game.last_play["words"]}
        )
        self.assertIn("AT (4)", self.app.last_play_text())
        self.assertIn("TO (4)", self.app.last_play_text())

    def test_missing_word_does_not_invent_definition(self):
        result = lookup("ABATTU")
        self.assertEqual([], result["entries"])
        self.assertEqual("missing", result["match"])


if __name__ == "__main__":
    unittest.main()
