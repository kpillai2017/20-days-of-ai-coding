"""Exercise real pygame rendering and synthetic events without a desktop.

If pygame isn't installed, skip these and still run the pure-Python rule tests.
Never run a visible game window in the same process: dummy SDL is intentional.
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import pygame
    import main
    from game import Game
except ModuleNotFoundError as error:
    if error.name != "pygame":
        raise
    pygame = None


@unittest.skipIf(pygame is None, "pygame not installed; model tests still work")
class WindowTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_renders_all_states(self):
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((800, 600))
        fonts = tuple(pygame.font.Font(None, size) for size in (20, 26, 52))
        game = Game()
        for state in ("ready", "playing", "won", "game_over"):
            with self.subTest(state=state):
                game.state = state
                main.draw_game(screen, game, fonts)
        main.draw_game(screen, game, fonts, paused=True)
        self.assertEqual(screen.get_size(), (800, 600))

    def test_actual_loop_smoke_and_cleanup(self):
        main.run(max_frames=3)
        self.assertFalse(pygame.display.get_init())

    def test_controls_pause_focus_restart_and_quit(self):
        game = Game()
        observed = []
        # One event batch per frame lets us inspect state BETWEEN user actions.
        def batch(key=None, event_type=None):
            def events():
                observed.append(game.state)
                if event_type is not None:
                    return [pygame.event.Event(event_type)]
                return [pygame.event.Event(pygame.KEYDOWN, key=key)]
            return events
        batches = iter([
            batch(pygame.K_SPACE),
            batch(pygame.K_p),
            batch(pygame.K_p),
            batch(event_type=pygame.WINDOWFOCUSLOST),
            batch(pygame.K_r),
            batch(pygame.K_ESCAPE),
        ])
        pauses = []
        real_draw = main.draw_game
        def record_draw(screen, current, fonts, paused):
            pauses.append(paused)
            real_draw(screen, current, fonts, paused)
        with patch.object(main, "Game", return_value=game), \
             patch.object(pygame.event, "get", side_effect=lambda: next(batches)()), \
             patch.object(main, "draw_game", side_effect=record_draw):
            main.run(max_frames=10)
        self.assertEqual(observed, ["ready", "playing", "playing", "playing", "playing", "ready"])
        self.assertEqual(pauses, [False, True, False, True, False])
        self.assertEqual((game.state, game.score, game.lives), ("ready", 0, 3))

    def test_window_close_exits(self):
        with patch.object(pygame.event, "get", return_value=[pygame.event.Event(pygame.QUIT)]):
            main.run(max_frames=2)
        self.assertFalse(pygame.display.get_init())


if __name__ == "__main__":
    unittest.main()
