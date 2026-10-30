"""Deterministic timeline and integration tests: no wall-clock sleeps."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
from concurrent.futures import Future
import pygame
from animation import TileFlight
from ai import Lexicon
from engine import Tile
from ui import ScrabbleApp


class TimelineTests(unittest.TestCase):
    def test_one_tile_at_a_time_and_landing_pause(self):
        items = [{"start": (100, 800), "end": (300, 300)}] * 3
        flight = TileFlight(items, 0, 100)
        self.assertEqual(0, flight.flying()[0])
        self.assertFalse(flight.landed(0))
        flight.advance(750)
        self.assertTrue(flight.landed(0))
        self.assertIsNone(flight.flying())
        flight.advance(890)
        self.assertEqual(1, flight.flying()[0])
        self.assertFalse(flight.landed(1))
        flight.advance(2470)
        self.assertTrue(flight.done)

    def test_dialog_pause_does_not_jump_after_resume(self):
        flight = TileFlight([{"start": (0, 0), "end": (100, 100)}], 0, 0)
        flight.advance(300)
        flight.advance(3000, paused=True)
        self.assertEqual(300, flight.elapsed)
        flight.advance(3100)
        self.assertEqual(400, flight.elapsed)
        self.assertFalse(flight.done)


class FlightIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["CAT", "AT"]), 42)
        self.app.start([("Alice", False), ("Computer 2", True)])
        self.app.game.current = 0
        self.app.dispatch("ready")
        self.app.game.players[0].rack = [Tile(c) for c in "CATXYZ?"]
        self.move = {(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")}

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        self.app.definition_executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def test_commit_once_then_lock_controls_until_finish(self):
        self.app.pending = dict(self.move)
        self.app.dispatch("play")
        self.assertEqual(10, self.app.game.players[0].score)
        self.assertEqual(1, self.app.game.current)
        self.assertFalse(self.app.human_active())
        self.app.dispatch("play")
        self.assertEqual(10, self.app.game.players[0].score)
        self.assertEqual(3, len(self.app.game.board))
        flight = self.app.animation
        with patch("pygame.time.get_ticks", return_value=flight.last_tick + 2370):
            self.app.update()
        self.assertIsNone(self.app.animation)
        self.assertIsNone(self.app.future)

    def test_board_reveals_only_landed_tiles(self):
        self.app.commit_animated(self.move)
        with patch.object(self.app, "tile", wraps=self.app.tile) as tile:
            self.app.render_board()
        self.assertEqual(0, tile.call_count)
        self.app.animation.elapsed = 650
        with patch.object(self.app, "tile", wraps=self.app.tile) as tile:
            self.app.render_board()
        self.assertEqual(1, tile.call_count)

    def test_ai_uses_same_animation_and_only_snapshots_played_tiles(self):
        self.app.game.players[0].is_ai = True
        self.app.rack_revealed = False
        future = Future()
        future.set_result(self.move)
        self.app.future = future
        self.app.search_kind = ("ai", self.app.generation, 0)
        self.app.update()
        self.assertIsNotNone(self.app.animation)
        self.assertEqual(
            ["C", "A", "T"],
            [item["placed"].letter for item in self.app.animation.items],
        )
        self.assertFalse(self.app.rack_revealed)
        self.assertTrue(all("rack" not in item for item in self.app.animation.items))

    def test_modal_pauses_and_new_game_cancels_flights(self):
        self.app.commit_animated(self.move)
        flight = self.app.animation
        self.app.modal = "quit"
        with patch("pygame.time.get_ticks", return_value=flight.last_tick + 5000):
            self.app.update()
        self.assertEqual(0, flight.elapsed)
        self.app.dispatch("new_confirm")
        self.assertIsNone(self.app.animation)
        self.assertIsNone(self.app.game)

    def test_invalid_play_starts_no_animation(self):
        self.app.pending = {(0, 0): (0, "C")}
        self.app.dispatch("play")
        self.assertIsNone(self.app.animation)
        self.assertFalse(self.app.game.board)


if __name__ == "__main__":
    unittest.main()
