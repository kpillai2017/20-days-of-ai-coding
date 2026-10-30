"""Public history and actual log controls, without exposing any private rack."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch

import pygame
from ai import Lexicon
from engine import Game, Placed, Tile
from ui import ScrabbleApp


class TurnHistoryTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(
            [("Alice", False), ("Robot", True)], {"CAT", "AT", "CATS", "TRAINER"}, 42
        )
        self.game.current = 0
        self.move = {(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")}
        self.game.players[0].rack = [Tile(c) for c in "CATXXXX"]

    def test_play_pass_exchange_record_player_score_and_total(self):
        g = self.game
        g.play(self.move)
        g.pass_turn()
        g.exchange([0, 1])
        self.assertEqual([1, 2, 3], [e["turn"] for e in g.turn_history])
        self.assertEqual([0, 1, 0], [e["player"] for e in g.turn_history])
        self.assertEqual([10, 0, 0], [e["score"] for e in g.turn_history])
        self.assertEqual([10, 0, 10], [e["total"] for e in g.turn_history])
        self.assertEqual((("CAT", 10),), g.turn_history[0]["words"])
        self.assertEqual("passes", g.turn_history[1]["action"])
        self.assertEqual("exchanges 2 tiles", g.turn_history[2]["action"])
        self.assertNotIn("rack", g.turn_history[2])

    def test_preview_and_invalid_move_do_not_create_history(self):
        self.game.preview(self.move)
        with self.assertRaises(ValueError):
            self.game.play({(0, 0): (0, "C")})
        self.assertEqual([], self.game.turn_history)

    def test_crosswords_record_all_words(self):
        g = self.game
        g.board = {(6, 7): Placed(Tile("A"), "A"), (6, 8): Placed(Tile("T"), "T")}
        g.players[0].rack = [Tile("A"), Tile("T")]
        # AT across row 7 and AT down column 8; AA is also formed at column 7.
        g.lexicon = {"AT", "AA", "TT"}
        move = {(7, 7): (0, "A"), (7, 8): (1, "T")}
        result = g.preview(move)
        g.play(move)
        self.assertEqual(tuple(result.words), g.turn_history[0]["words"])
        self.assertEqual(3, len(g.turn_history[0]["words"]))

    def test_bingo_and_final_adjustment_are_distinct(self):
        g = self.game
        g.players[0].rack = [Tile(c) for c in "TRAINER"]
        g.bag = []
        move = {(7, 4 + i): (i, c) for i, c in enumerate("TRAINER")}
        result = g.preview(move)
        g.play(move)
        entry = g.turn_history[0]
        self.assertEqual(50, entry["bingo"])
        self.assertEqual(result.score, entry["total"])
        self.assertEqual("gameover", g.phase)
        self.assertGreater(g.players[0].score, entry["total"])
        g.finish()
        self.assertEqual(1, len(g.turn_history))


class LogPageTests(unittest.TestCase):
    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["CAT", "AT"]), 42)
        self.app.start([("Alice", False), ("Robot", True)])
        self.app.game.current = 0
        self.app.dispatch("ready")

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        self.app.definition_executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def click(self, command):
        self.app.render()
        rect = next(r for r, cmd in self.app.buttons if cmd == command)
        pos = tuple(
            round(rect.center[i] * self.app.scale + self.app.offset[i]) for i in (0, 1)
        )
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))

    def populate(self):
        g = self.app.game
        # Long fixture bypasses the six-scoreless-turn end rule for pagination.
        for i in range(13):
            g.current = i % 2
            g._record_turn("passes")

    def test_button_empty_state_and_close_restore_human_turn(self):
        self.click("turn_log")
        self.assertEqual("log", self.app.modal)
        self.assertFalse(self.app.human_active())
        self.app.render()
        self.assertFalse(any(cmd in ("play", "pass") for _, cmd in self.app.buttons))
        self.click("close")
        self.assertTrue(self.app.human_active())

    def test_filters_pagination_and_keyboard_wheel_bounds(self):
        self.populate()
        self.click("turn_log")
        self.click("log_next")
        self.assertEqual(1, self.app.log_page)
        self.app.event(pygame.event.Event(pygame.MOUSEWHEEL, y=-1, x=0))
        self.assertEqual(2, self.app.log_page)
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.assertEqual(3, self.app.log_page)
        self.app.dispatch("log_next")
        self.assertEqual(3, self.app.log_page)
        self.click("log_filter:1")
        self.assertEqual(0, self.app.log_page)
        self.assertEqual(6, len(self.app.log_entries()))
        self.assertTrue(all(e["player"] == 1 for e in self.app.log_entries()))
        self.app.dispatch("log_previous")
        self.assertEqual(0, self.app.log_page)
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertNotEqual("log", self.app.modal)

    def test_log_pauses_flight_without_duplicate_history(self):
        self.app.game.players[0].rack = [Tile(c) for c in "CATXXXX"]
        self.app.commit_animated({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        self.click("turn_log")
        elapsed = self.app.animation.elapsed
        with patch(
            "pygame.time.get_ticks", return_value=self.app.animation.last_tick + 1000
        ):
            self.app.update()
        self.assertEqual(elapsed, self.app.animation.elapsed)
        self.assertEqual(1, len(self.app.game.turn_history))

    def test_closing_log_resumes_flight_before_human_handoff(self):
        self.app.game.players[1].is_ai = False
        self.app.game.players[0].rack = [Tile(c) for c in "CATXXXX"]
        self.app.commit_animated({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        self.click("turn_log")
        self.click("close")
        self.assertIsNone(self.app.modal)
        self.assertFalse(self.app.human_active())
        self.assertFalse(self.app.rack_revealed)
        self.assertIsNotNone(self.app.animation)

    def test_new_game_resets_history_filters_and_page(self):
        self.populate()
        self.app.log_filter = 1
        self.app.log_page = 2
        self.app.start([("Carol", False), ("Dave", False)])
        self.assertEqual([], self.app.game.turn_history)
        self.assertIsNone(self.app.log_filter)
        self.assertEqual(0, self.app.log_page)


if __name__ == "__main__":
    unittest.main()
