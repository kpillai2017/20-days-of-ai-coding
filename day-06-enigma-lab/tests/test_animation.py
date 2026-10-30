"""Animation clocks must never change cipher results or add rotor steps."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
import pygame
import main


class AnimationTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((main.WIDTH, main.HEIGHT))
        self.fonts = tuple(pygame.font.Font(None, s) for s in (21, 24, 34))
        self.lab = main.Lab()

    def tearDown(self):
        pygame.quit()

    def down(self, letter, repeat=False):
        main.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=ord(letter.lower()),
                unicode=letter.lower(),
                mod=0,
                repeat=repeat,
            ),
            self.lab,
        )

    def test_key_hold_release_glow_and_no_extra_steps(self):
        with patch("pygame.time.get_ticks", return_value=100):
            self.down("A")
        self.assertEqual("AAB", self.lab.machine.positions)
        self.assertEqual("B", self.lab.lamp)
        self.assertEqual("AAA", self.lab.old_positions)
        progress, down, light = self.lab.animation(220)
        self.assertEqual(0.5, progress)
        self.assertTrue(down)
        self.assertEqual(1, light)
        main.draw(self.screen, self.lab, self.fonts)
        self.assertEqual("AAB", self.lab.machine.positions)
        with patch("pygame.time.get_ticks", return_value=300):
            main.handle_event(
                pygame.event.Event(pygame.KEYUP, key=pygame.K_a), self.lab
            )
        self.assertFalse(self.lab.animation(310)[1])
        self.assertGreater(self.lab.animation(400)[2], 0)
        self.assertEqual(0, self.lab.animation(600)[2])
        self.assertEqual("B", self.lab.lamp)  # last result survives visually fading

    def test_mouse_key_depress_and_release(self):
        rect = main.key_rects(542)["Q"]
        main.handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center),
            self.lab,
        )
        self.assertTrue(self.lab.held)
        self.assertEqual("Q", self.lab.pressed_key)
        main.handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0)), self.lab
        )
        self.assertFalse(self.lab.held)

    def test_repeat_and_focus_loss(self):
        self.down("A")
        self.down("A", repeat=True)
        self.assertEqual("A", self.lab.plain)
        main.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST), self.lab)
        self.assertFalse(self.lab.held)

    def test_double_step_windows_animate_actual_movement(self):
        self.lab.fields.update(rotors="III II I", positions="ADO")
        self.lab.apply()
        for expected in ("ADP", "ADQ", "AER", "BFS"):
            before = self.lab.machine.positions
            self.down("A")
            self.assertEqual(before, self.lab.old_positions)
            self.assertEqual(expected, self.lab.machine.positions)
        self.assertEqual("AER", self.lab.old_positions)

    def test_rapid_typing_and_reset_clear_motion(self):
        with patch("pygame.time.get_ticks", return_value=100):
            for char in "HELLOWORLD":
                self.down(char)
        self.assertEqual("ILBDAAMTAZ", self.lab.cipher)
        self.assertEqual("AAJ", self.lab.old_positions)
        self.assertEqual("AAK", self.lab.machine.positions)
        self.lab.restart()
        self.assertEqual((1, False, 0), self.lab.animation(200))
        self.assertEqual("AAA", self.lab.old_positions)
        self.assertIsNone(self.lab.pressed_key)

    def test_settings_typing_does_not_trigger_animation(self):
        self.lab.active_field = "positions"
        self.down("B")
        self.assertIsNone(self.lab.pressed_key)
        self.assertEqual("AAA", self.lab.machine.positions)

    def test_render_animation_frames_is_read_only(self):
        self.down("Z")
        before = (
            self.lab.machine.positions,
            self.lab.cipher,
            list(self.lab.machine.last_trace),
        )
        for offset in (0, 60, 120, 240, 600):
            with patch(
                "pygame.time.get_ticks", return_value=self.lab.press_time + offset
            ):
                main.draw(self.screen, self.lab, self.fonts)
        self.assertEqual(
            before,
            (self.lab.machine.positions, self.lab.cipher, self.lab.machine.last_trace),
        )


if __name__ == "__main__":
    unittest.main()
