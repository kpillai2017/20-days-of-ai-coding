"""Headless interaction tests click actual controls and enforce privacy curtains."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from concurrent.futures import Future
from unittest.mock import patch
import pygame
from engine import Phase
from ui import MastermindApp
from main import parse_args


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = MastermindApp(42)

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def click(self, command):
        self.app.render()
        rect = next(r for r, c in self.app.buttons if c == command)
        pos = tuple(
            round(rect.center[i] * self.app.scale + self.app.offset[i]) for i in (0, 1)
        )
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def finish_flight(self):
        if self.app.animation:
            animation = self.app.animation
            with patch(
                "pygame.time.get_ticks", return_value=animation.last_tick + 4000
            ):
                self.app.update()

    def key(self, key, **extra):
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, **extra))

    def start_humans(self):
        self.app.computers = [False, False]
        self.click("start")
        self.assertEqual("maker_ready", self.app.modal)
        self.click("ready")

    def test_all_controller_combinations(self):
        for first, second in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            self.app.computers = [first, second]
            self.app.start()
            self.assertEqual([first, second], [p.is_ai for p in self.app.match.players])
            self.assertEqual(None if first else "maker_ready", self.app.modal)

    def test_private_handoffs_secret_lock_feedback_and_round_swap(self):
        self.start_humans()
        self.app.draft = [0, 1, 2, 3]
        self.click("submit")
        self.finish_flight()
        self.assertEqual("breaker_ready", self.app.modal)
        self.app.render()
        self.assertEqual([], self.app.holes)
        self.assertEqual([None] * 4, self.app.draft)
        self.click("ready")
        self.app.draft = [0, 1, 2, 3]
        self.click("submit")
        self.finish_flight()
        self.assertEqual(Phase.ROUND_OVER, self.app.match.phase)
        self.assertEqual(1, self.app.match.players[0].score)
        self.click("next")
        self.assertEqual(1, self.app.match.maker)
        self.assertEqual("maker_ready", self.app.modal)

    def test_incomplete_row_disabled_and_keyboard_rejected(self):
        self.start_humans()
        self.app.render()
        self.assertFalse(any(c == "submit" for _, c in self.app.buttons))
        self.key(pygame.K_RETURN)
        self.assertEqual(Phase.SETTING, self.app.match.phase)
        self.assertIn("four", self.app.notice)

    def test_keyboard_palette_place_focus_and_clear(self):
        self.start_humans()
        self.key(pygame.K_6)
        self.key(pygame.K_SPACE)
        self.assertEqual(5, self.app.draft[0])
        self.assertEqual(1, self.app.active_hole)
        self.key(pygame.K_LEFT)
        self.key(pygame.K_BACKSPACE)
        self.assertIsNone(self.app.draft[0])
        self.app.draft = [1, 2, 3, 4]
        self.click("clear")
        self.assertEqual([None] * 4, self.app.draft)

    def test_modal_help_and_quit_preserve_breaker_privacy(self):
        self.start_humans()
        self.app.draft = [0, 1, 2, 3]
        self.click("submit")
        self.finish_flight()
        self.app.dispatch("help")
        self.click("close")
        self.assertEqual("breaker_ready", self.app.modal)
        self.key(pygame.K_ESCAPE)
        self.assertEqual("quit", self.app.modal)
        self.click("close")
        self.assertEqual("breaker_ready", self.app.modal)
        self.assertTrue(self.app.running)

    def test_window_close_requires_confirmation(self):
        self.app.event(pygame.event.Event(pygame.QUIT))
        self.assertTrue(self.app.running)
        self.assertEqual("quit", self.app.modal)
        self.click("quit_confirm")
        self.assertFalse(self.app.running)

    def test_name_edit_unicode_and_duplicate_validation(self):
        self.click("name:0")
        self.app.event(pygame.event.Event(pygame.TEXTINPUT, text="Émile"))
        self.click("name_save")
        self.assertEqual("Émile", self.app.names[0])
        self.app.names[1] = "ÉMILE"
        self.click("start")
        self.assertIsNone(self.app.match)
        self.assertIn("different", self.app.notice)

    def test_resized_letterbox_click_hits_correct_hole(self):
        self.start_humans()
        self.app.event(pygame.event.Event(pygame.VIDEORESIZE, w=800, h=650))
        self.app.render()
        rect, index = self.app.holes[2]
        pos = tuple(
            round(rect.center[i] * self.app.scale + self.app.offset[i]) for i in (0, 1)
        )
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
        self.assertEqual(self.app.selected, self.app.draft[index])
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=pos))
        self.assertIsNone(self.app.draft[index])

    def test_computer_maker_uses_seed_and_human_curtain(self):
        self.app.computers = [True, False]
        self.app.start()
        self.app.ai_after = 0
        self.app.update()
        self.finish_flight()
        self.assertEqual(Phase.GUESSING, self.app.match.phase)
        self.assertEqual("breaker_ready", self.app.modal)
        self.assertEqual((5, 0, 0, 5), self.app.match.secret)

    def test_worker_receives_no_secret_and_new_match_discards_future(self):
        self.app.computers = [True, True]
        self.app.start()
        self.app.match.set_secret((5, 4, 3, 2))
        self.app.ai_after = 0
        future = Future()
        with patch.object(self.app.executor, "submit", return_value=future) as submit:
            self.app.update()
        task = submit.call_args.args[0]
        self.assertNotIn("match", task.__code__.co_freevars)
        self.app.dispatch("new_confirm")
        self.assertTrue(future.cancelled())
        self.assertIsNone(self.app.future)
        self.assertIsNone(self.app.match)

    def test_ready_curtain_blocks_ai_application(self):
        self.start_humans()
        self.app.draft = [0, 0, 1, 1]
        self.app.commit()
        future = Future()
        future.set_result((self.app.generation, (0, 0, 1, 1)))
        self.app.future = future
        self.app.update()
        self.assertEqual([], self.app.match.guesses)

    def test_cli_defaults_and_negative_frames(self):
        self.assertEqual(0, parse_args([]).frames)
        with self.assertRaises(SystemExit):
            parse_args(["--frames", "-1"])


if __name__ == "__main__":
    unittest.main()
