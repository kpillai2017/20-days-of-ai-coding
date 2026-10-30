"""Direct bank placement is the motion; never replay it on human submit."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
import pygame
from ui import MastermindApp
from engine import Phase


class BankDragTests(unittest.TestCase):
    def setUp(self):
        self.app = MastermindApp(42)
        self.app.computers = [False, False]
        self.app.start()
        self.app.dispatch("ready")

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def position(self, point):
        return tuple(
            round(point[i] * self.app.scale + self.app.offset[i]) for i in (0, 1)
        )

    def bank_drag(self, colour, hole=None, outside=False, move=True):
        self.app.render()
        bank = next(r for r, c in self.app.buttons if c == f"color:{colour}")
        start = self.position(bank.center)
        target = (
            (20, 860)
            if outside
            else (
                next(r for r, i in self.app.holes if i == hole).center
                if hole is not None
                else bank.center
            )
        )
        end = self.position(target)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1))
        if move:
            self.app.event(
                pygame.event.Event(
                    pygame.MOUSEMOTION, pos=end, rel=(40, 0), buttons=(1, 0, 0)
                )
            )
            self.app.render()
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=end, button=1))

    def test_bank_places_replaces_and_supports_repeats(self):
        self.bank_drag(2, 0)
        self.bank_drag(2, 1)
        self.bank_drag(5, 0)
        self.assertEqual([5, 2, None, None], self.app.draft)
        self.assertEqual(5, self.app.selected)
        self.assertIsNone(self.app.drag)
        self.assertIsNone(self.app.match.secret)

    def test_outside_drop_cancel_and_short_click_selects_only(self):
        self.bank_drag(1, outside=True)
        self.assertEqual([None] * 4, self.app.draft)
        self.bank_drag(4, move=False)
        self.assertEqual(4, self.app.selected)
        self.assertEqual([None] * 4, self.app.draft)

    def test_secret_locks_in_place_and_preserves_handoff(self):
        for i in range(4):
            self.bank_drag(i, i)
        self.app.commit()
        self.assertIsNone(self.app.animation)
        self.assertEqual((0, 1, 2, 3), self.app.match.secret)
        self.assertEqual("breaker_ready", self.app.modal)
        self.assertEqual([None] * 4, self.app.draft)
        self.app.render()
        self.assertEqual([], self.app.holes)

    def test_human_guess_has_immediate_feedback_without_reflight(self):
        self.app.match.set_secret((0, 1, 2, 3))
        for i in range(4):
            self.bank_drag(i, i)
        self.app.commit()
        self.assertIsNone(self.app.animation)
        self.assertEqual(Phase.ROUND_OVER, self.app.match.phase)
        self.assertEqual([(4, 0)], self.app.match.feedback)
        self.assertEqual(1, self.app.match.players[0].score)
        self.app.commit()
        self.assertEqual(1, len(self.app.match.guesses))

    def test_resized_bank_drop_and_escape_cancel(self):
        self.app.event(pygame.event.Event(pygame.VIDEORESIZE, w=800, h=650))
        self.bank_drag(3, 2)
        self.assertEqual(3, self.app.draft[2])
        self.app.render()
        rect = next(r for r, c in self.app.buttons if c == "color:1")
        start = self.position(rect.center)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1))
        self.app.event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=(start[0] - 20, start[1]),
                rel=(-20, 0),
                buttons=(1, 0, 0),
            )
        )
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        self.assertIsNone(self.app.drag)
        self.assertIsNone(self.app.modal)
        self.assertEqual([None, None, 3, None], self.app.draft)

    def test_no_bank_drag_through_privacy_modal(self):
        self.app.modal = "maker_ready"
        self.app.render()
        self.assertFalse(any(c.startswith("color:") for _, c in self.app.buttons))
        self.assertEqual([], self.app.holes)


if __name__ == "__main__":
    unittest.main()
