"""Peg timing, secret privacy and real pointer-driven swaps."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
from concurrent.futures import Future
import pygame
from animation import PegFlight
from engine import Phase
from ui import MastermindApp, COLOUR_RGB


class TimelineTests(unittest.TestCase):
    def test_sequential_landings_and_pause(self):
        flight = PegFlight((0, 1, 2, 3), "guess", 0, 100)
        self.assertEqual((0, 647, 592, 23), flight.flying())
        flight.advance(750)
        self.assertTrue(flight.landed(0))
        self.assertFalse(flight.landed(1))
        self.assertIsNone(flight.flying())
        flight.advance(890)
        self.assertEqual(1, flight.flying()[0])
        flight.advance(5000, paused=True)
        self.assertEqual(790, flight.elapsed)
        flight.advance(5100)
        self.assertEqual(890, flight.elapsed)
        flight.advance(9000)
        self.assertTrue(flight.done)
        self.assertIsNone(flight.flying())

    def test_computer_secret_paths_do_not_encode_colour(self):
        a = PegFlight((0, 0, 0, 0), "secret", 0, 0, True)
        b = PegFlight((5, 4, 3, 2), "secret", 0, 0, True)
        for t in (0, 250, 800, 1500, 2500):
            a.advance(t)
            b.advance(t)
            self.assertEqual(a.flying(), b.flying())


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.app = MastermindApp(42)
        self.app.computers = [False, False]
        self.app.start()
        self.app.dispatch("ready")
        self.app.match.set_secret((0, 1, 2, 3))
        self.app.draft = [0, 1, 2, 3]
        self.app.render()

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def at(self, i):
        self.app.render()
        rect = next(r for r, n in self.app.holes if n == i)
        return tuple(
            round(rect.center[n] * self.app.scale + self.app.offset[n]) for n in (0, 1)
        )

    def drag(self, source, target=None, outside=False):
        start = self.at(source)
        end = (30, 850) if outside else self.at(target)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start))
        self.app.event(
            pygame.event.Event(
                pygame.MOUSEMOTION, pos=end, rel=(50, 0), buttons=(1, 0, 0)
            )
        )
        self.app.render()
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=end))

    def finish(self):
        with patch(
            "pygame.time.get_ticks", return_value=self.app.animation.last_tick + 4000
        ):
            self.app.update()

    def test_swaps_occupied_moves_empty_and_cancels_outside(self):
        self.drag(0, 2)
        self.assertEqual([2, 1, 0, 3], self.app.draft)
        self.app.draft[1] = None
        self.drag(2, 1)
        self.assertEqual([2, 0, None, 3], self.app.draft)
        before = self.app.draft[:]
        self.drag(0, outside=True)
        self.assertEqual(before, self.app.draft)
        self.assertEqual([], self.app.match.guesses)

    def test_secret_entry_can_swap_too(self):
        self.app.start()
        self.app.dispatch("ready")
        self.app.draft = [0, 1, 2, 3]
        self.drag(0, 3)
        self.assertEqual([3, 1, 2, 0], self.app.draft)
        self.assertIsNone(self.app.match.secret)

    def test_drag_cancel_escape_focus_and_short_click(self):
        for event in (
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0),
            pygame.event.Event(pygame.WINDOWFOCUSLOST),
        ):
            start = self.at(0)
            self.app.event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start)
            )
            self.app.event(
                pygame.event.Event(
                    pygame.MOUSEMOTION,
                    pos=(start[0] + 12, start[1]),
                    rel=(12, 0),
                    buttons=(1, 0, 0),
                )
            )
            self.app.event(event)
            self.assertIsNone(self.app.drag)
            self.assertEqual([0, 1, 2, 3], self.app.draft)
            self.assertIsNone(self.app.modal)
        self.app.selected = 5
        start = self.at(0)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start))
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=start))
        self.assertEqual(5, self.app.draft[0])

    def test_scaled_dragging(self):
        self.app.event(pygame.event.Event(pygame.VIDEORESIZE, w=800, h=650))
        self.drag(1, 3)
        self.assertEqual([0, 3, 2, 1], self.app.draft)

    def test_guess_commits_once_blocks_input_and_defers_results(self):
        self.app.begin_flight(self.app.draft)
        self.assertEqual(1, len(self.app.match.guesses))
        self.assertFalse(self.app.human_entry())
        self.app.begin_flight(self.app.draft)
        self.assertEqual(1, len(self.app.match.guesses))
        self.app.render()
        self.assertFalse(any(c == "next" for _, c in self.app.buttons))
        self.assertEqual([], self.app.holes)
        self.finish()
        self.assertIsNone(self.app.animation)
        self.app.render()
        self.assertTrue(any(c == "next" for _, c in self.app.buttons))
        self.assertEqual(1, self.app.match.players[0].score)

    def test_board_hides_unlanded_pegs_and_feedback(self):
        self.app.begin_flight(self.app.draft)
        with patch.object(self.app, "peg", wraps=self.app.peg) as peg:
            self.app.render_board()
        self.assertEqual([], peg.call_args_list)
        self.app.animation.elapsed = 650
        with patch.object(self.app, "peg", wraps=self.app.peg) as peg:
            self.app.render_board()
        self.assertEqual(1, len(peg.call_args_list))
        self.app.animation.elapsed = 3050
        with patch.object(self.app, "peg", wraps=self.app.peg) as peg:
            self.app.render_board()
        self.assertEqual(4, len(peg.call_args_list))  # no feedback or secret yet

    def test_modal_pause_and_new_match_cancellation(self):
        self.app.begin_flight(self.app.draft)
        self.app.dispatch("help")
        with patch(
            "pygame.time.get_ticks", return_value=self.app.animation.last_tick + 2000
        ):
            self.app.update()
        self.assertEqual(0, self.app.animation.elapsed)
        self.app.dispatch("close")
        self.assertIsNone(self.app.modal)
        self.finish()
        self.app.start()
        self.assertIsNone(self.app.animation)

    def test_previous_rows_are_not_drag_targets(self):
        self.app.match.submit_guess((0, 0, 0, 0))
        self.app.render()
        self.assertEqual(4, len(self.app.holes))
        # All editable holes belong to row 2, not committed row 1.
        self.assertTrue(all(rect.centery == 698 for rect, _ in self.app.holes))
        pos = (170, 752)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
        self.assertIsNone(self.app.drag)
        self.assertEqual([(0, 0, 0, 0)], self.app.match.guesses)

    def test_new_confirmation_discards_motion_cleanly(self):
        self.app.begin_flight(self.app.draft)
        self.app.dispatch("new")
        self.app.dispatch("new_confirm")
        self.assertIsNone(self.app.animation)
        self.assertIsNone(self.app.drag)
        self.assertIsNone(self.app.match)
        self.app.render()

    def test_computer_guess_uses_same_flight_path(self):
        self.app.match.players[self.app.match.breaker].is_ai = True
        future = Future()
        future.set_result((self.app.generation, (0, 0, 1, 1)))
        self.app.future = future
        self.app.update()
        self.assertIsNotNone(self.app.animation)
        self.assertEqual((0, 0, 1, 1), self.app.animation.code)
        self.assertEqual(1, len(self.app.match.guesses))

    def test_computer_secret_neutral_draw_and_private_handoff(self):
        self.app.computers = [True, False]
        self.app.start()
        self.app.ai_after = 0
        self.app.update()
        self.assertTrue(self.app.animation.concealed)
        with patch.object(self.app, "peg", wraps=self.app.peg) as peg:
            self.app.render_motion()
        self.assertTrue(peg.called)
        self.assertEqual((101, 91, 78), peg.call_args.args[1])
        self.finish()
        self.assertEqual("breaker_ready", self.app.modal)
        self.assertFalse(self.app.human_entry())


if __name__ == "__main__":
    unittest.main()
