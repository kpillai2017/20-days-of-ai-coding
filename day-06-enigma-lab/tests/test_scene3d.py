"""Camera/picking tests run without OpenGL; fallback uses SDL dummy display."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import pygame
from scene3d import Camera, keys
from view3d import View, TOGGLE
from main import Lab


class CameraTests(unittest.TestCase):
    def test_all_26_keys_unique_and_front_key_pick(self):
        self.assertEqual(26, len(keys()))
        self.assertEqual(26, len(set(keys().values())))
        camera = Camera()
        viewport = (20, 225, 1040, 455)
        for letter in "PYXCVBNML":
            point = camera.project(keys()[letter], viewport)
            self.assertEqual(letter, camera.pick(point[:2], viewport))
        self.assertIsNone(camera.pick((-100, -100), viewport))

    def test_camera_bounds_reset_and_hidden_side_not_pickable(self):
        camera = Camera()
        camera.orbit(1000, 1000)
        self.assertEqual(85, camera.pitch)
        camera.zoom(1000)
        self.assertEqual(9, camera.distance)
        camera.zoom(-1000)
        self.assertEqual(25, camera.distance)
        camera.pitch = -30
        self.assertIsNone(camera.pick((540, 400), (20, 225, 1040, 455)))
        camera.reset()
        self.assertEqual((0, 49, 15), (camera.yaw, camera.pitch, camera.distance))


class AdapterTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.view = View((1080, 860))
        self.lab = Lab()

    def tearDown(self):
        # Test doubles below are not GPU resource owners.
        self.view.renderer = None
        pygame.quit()

    def fake3d(self):
        self.view.renderer = SimpleNamespace(
            camera=Camera(), viewport=(20, 225, 1040, 455)
        )

    def event(self, kind, **kwargs):
        return self.view.event(pygame.event.Event(kind, **kwargs), self.lab)

    def test_missing_opengl_or_context_falls_back_to_2d(self):
        self.view.toggle()
        self.assertIsNone(self.view.renderer)  # SDL dummy has no GL support
        self.assertIn("3D unavailable", self.view.note)
        self.assertEqual((1080, 860), self.view.window.get_size())

    def test_short_click_key_and_drag_does_not_type(self):
        self.fake3d()
        camera = self.view.renderer.camera
        point = camera.project(keys()["P"], self.view.renderer.viewport)[:2]
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=point)
        self.assertEqual("P", self.lab.plain)
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)
        self.event(pygame.MOUSEMOTION, pos=(point[0] + 50, point[1] + 10))
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=(point[0] + 50, point[1] + 10))
        self.assertEqual("P", self.lab.plain)
        self.assertNotEqual(0, camera.yaw)

    def test_settings_focus_blocks_key_and_focus_loss_cancels_drag(self):
        self.fake3d()
        self.lab.active_field = "positions"
        point = self.view.renderer.camera.project(
            keys()["P"], self.view.renderer.viewport
        )[:2]
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=point)
        self.assertEqual("", self.lab.plain)
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)
        self.event(pygame.WINDOWFOCUSLOST)
        self.assertIsNone(self.view.drag)

    def test_zoom_reset_and_toggle_preserve_cipher(self):
        self.fake3d()
        from view3d import RESET_VIEW

        self.lab.press("A")
        state = (self.lab.machine.positions, self.lab.cipher)
        self.event(pygame.MOUSEWHEEL, y=3)
        self.assertLess(self.view.renderer.camera.distance, 15)
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=RESET_VIEW.center)
        self.assertEqual(15, self.view.renderer.camera.distance)
        with patch.object(self.view, "toggle") as toggle:
            self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=TOGGLE.center)
        toggle.assert_called_once()
        self.assertEqual(state, (self.lab.machine.positions, self.lab.cipher))


if __name__ == "__main__":
    unittest.main()
