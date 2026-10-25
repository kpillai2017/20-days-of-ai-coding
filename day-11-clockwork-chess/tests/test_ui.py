"""Headless tests for animation commits, input, AI hand-off and original audio."""

import os
from pathlib import Path
import sys
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from engine import Position, START_FEN, notation_to_sq
from graphics import project, square_at
from main import App, Sounds, main


class Presentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((1240, 800))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def finish(self, app):
        for _ in range(30):
            if not app.animation:
                break
            app.renderer.draw(app)
            app.update(0.1)
        self.assertIsNone(app.animation)

    def move(self, app, uci):
        app.animate(next(m for m in app.legal if m.uci() == uci))
        self.finish(app)

    def test_projection_inverse_every_square(self):
        for flipped in (False, True):
            for square in range(64):
                self.assertEqual(
                    square_at(
                        project(square % 8, square // 8, flipped=flipped), flipped
                    ),
                    square,
                )
        self.assertIsNone(square_at((-100, -100)))

    def test_click_move_and_commit_once(self):
        app = App(True, False)
        try:
            app.renderer.draw(app)
            for square in ("e2", "e4"):
                sq = notation_to_sq(square)
                app.click(project(sq % 8, sq // 8, flipped=app.flipped))
            self.assertIsNotNone(app.animation)
            self.assertEqual(app.position.fen(), START_FEN)
            self.finish(app)
            self.assertEqual(app.position.board[28], "P")
            self.assertEqual(len(app.position.history), 1)
            app.update(0.1)
            self.assertEqual(len(app.position.history), 1)
            app.action("undo")
            self.assertEqual(app.position.fen(), START_FEN)
        finally:
            app.close()

    def test_capture_frames_and_undo(self):
        app = App(True, False)
        try:
            self.move(app, "e2e4")
            self.move(app, "d7d5")
            before = app.position.fen()
            app.animate(next(m for m in app.legal if m.uci() == "e4d5"))
            self.assertEqual(app.animation["captured"], "p")
            for _ in range(12):
                app.update(0.1)
                app.renderer.draw(app)
            self.assertTrue(app.animation["impact"])
            self.finish(app)
            self.assertEqual(app.position.board[35], "P")
            app.action("undo")
            self.assertEqual(app.position.fen(), before)
        finally:
            app.close()

    def test_en_passant_animation_victim_square(self):
        app = App(True, False)
        try:
            app.position = Position("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
            app.refresh()
            app.animate(next(m for m in app.legal if m.uci() == "e5d6"))
            self.assertEqual(app.animation["capture_sq"], notation_to_sq("d5"))
            self.finish(app)
            self.assertEqual(app.position.board[35], ".")
        finally:
            app.close()

    def test_castling_animation(self):
        app = App(True, False)
        try:
            app.position = Position("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
            app.refresh()
            self.move(app, "e1g1")
            self.assertEqual(app.position.board[5], "R")
            self.assertEqual(app.position.board[6], "K")
        finally:
            app.close()

    def test_promotion_selection(self):
        app = App(True, False)
        try:
            app.position = Position("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
            app.refresh()
            app.renderer.draw(app)
            for square in (48, 56):
                app.click(project(square % 8, square // 8, flipped=app.flipped))
            self.assertEqual(len(app.promotion), 4)
            app.renderer.draw(app)
            app.key(pygame.K_n)
            self.finish(app)
            self.assertEqual(app.position.board[56], "N")
        finally:
            app.close()

    def test_ai_reply_and_undo_full_turn(self):
        app = App(True, True)
        app.level = "easy"
        try:
            self.move(app, "e2e4")
            end = time.monotonic() + 5
            while not app.animation and time.monotonic() < end:
                app.update(0.01)
                time.sleep(0.003)
            self.assertIsNotNone(app.animation)
            self.finish(app)
            self.assertEqual(len(app.position.history), 2)
            app.action("undo")
            self.assertEqual(app.position.fen(), START_FEN)
            self.assertEqual(app.moves, [])
        finally:
            app.close()

    def test_undo_ai_preview_rewinds_human_move(self):
        app = App(True, True)
        try:
            self.move(app, "e2e4")
            app.animate(app.legal[0])
            app.action("undo")
            self.assertEqual(app.position.fen(), START_FEN)
        finally:
            app.close()

    def test_new_cancels_worker_without_stale_reply(self):
        app = App(True, True)
        try:
            self.move(app, "e2e4")
            app.update(0.01)
            self.assertIsNotNone(app.future)
            app.action("new")
            for _ in range(4):
                app.update(0.02)
            self.assertEqual(app.position.fen(), START_FEN)
            self.assertIsNone(app.animation)
            app.action("side")
            self.assertEqual(app.human_side, "b")
            app.action("mode")
            self.assertFalse(app.ai_enabled)
            app.action("flip")
            app.renderer.draw(app)
        finally:
            app.close()

    def test_original_sound_and_toggle(self):
        sound = Sounds(False)
        self.assertTrue(sound.available)
        for name in ("move", "capture", "check", "end"):
            sound.play(name)
        sound.toggle()
        self.assertFalse(sound.enabled)

    def test_real_loop(self):
        self.assertEqual(main(["--mute", "--two-player", "--frames", "3"]), 0)
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((1240, 800))


if __name__ == "__main__":
    unittest.main()
