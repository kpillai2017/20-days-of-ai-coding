"""Headless pygame checks: rendering, actual input handlers and loop cleanup.

SDL's dummy driver creates surfaces without a visible desktop. It proves the
code runs, not that every real monitor/keyboard behaves identically.
"""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# This project is tested in its own process so its main.py cannot collide with
# Breakout's main.py in Python's module cache. CI discovers each day separately.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import pygame
    import main
    from maze import MazeGame, DIRECTIONS
except ModuleNotFoundError as error:
    if error.name != "pygame":
        raise
    pygame = None


@unittest.skipIf(pygame is None, "pygame not installed; model tests still run")
class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy"})
        cls.environment.start()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.environment.stop()

    def tearDown(self):
        pygame.quit()

    def key(self, key, game):
        return main.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key), game)

    def test_arrow_and_wasd_inputs_follow_passages(self):
        for key, direction in main.MOVE_KEYS.items():
            with self.subTest(key=key):
                game = MazeGame(3, 3, seed=42)
                game.position = (1, 1)
                dr, dc = DIRECTIONS[direction]
                target = (1 + dr, 1 + dc)
                # Use a controlled passage to test the UI mapping independently
                # of which openings a particular random maze happens to have.
                game.maze.passages[game.position].add(target)
                game.maze.passages[target].add(game.position)
                self.assertTrue(self.key(key, game))
                self.assertEqual(game.position, target)
                self.assertEqual(game.moves, 1)

    def test_hint_restart_and_new(self):
        game = MazeGame(seed=42)
        self.key(pygame.K_h, game)
        self.assertTrue(game.show_solution)
        old_maze = game.maze
        self.key(pygame.K_r, game)
        self.assertIs(game.maze, old_maze)
        self.assertFalse(game.show_solution)
        self.assertEqual(game.moves, 0)
        self.key(pygame.K_n, game)
        self.assertIsNot(game.maze, old_maze)
        self.assertEqual(game.position, game.maze.start)
        # A random maze is allowed to match a previous layout: don't demand it differ.

    def test_quit_and_ignored_events(self):
        game = MazeGame()
        self.assertFalse(self.key(pygame.K_ESCAPE, game))
        self.assertFalse(main.handle_event(pygame.event.Event(pygame.QUIT), game))
        self.assertTrue(self.key(pygame.K_SPACE, game))
        self.assertTrue(main.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT), game))
        self.assertEqual(game.moves, 0)

    def test_render_normal_hint_won_and_single_cell(self):
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((main.WIDTH, main.HEIGHT))
        fonts = tuple(pygame.font.Font(None, n) for n in (20, 25, 46))
        for rows, cols in ((15, 15), (1, 1), (1, 5), (50, 50)):
            game = MazeGame(rows, cols, seed=42)
            for hint in (False, True):
                game.show_solution = hint
                main.draw_game(screen, game, fonts)
            game.position = game.maze.goal
            main.draw_game(screen, game, fonts)
        self.assertEqual(screen.get_size(), (720, 820))
        self.assertEqual(main.cell_center((0, 0), 40, 40), (80, 160))

    def test_real_loop_frame_limit_and_cleanup(self):
        main.run(seed=42, max_frames=3)
        self.assertFalse(pygame.display.get_init())

    def test_real_loop_close_event(self):
        with patch.object(pygame.event, "get", return_value=[pygame.event.Event(pygame.QUIT)]):
            main.run(max_frames=3)
        self.assertFalse(pygame.display.get_init())

    def test_positive_frame_limit(self):
        import argparse
        self.assertEqual(main.positive_int("5"), 5)
        for value in ("0", "-1"):
            with self.assertRaises(argparse.ArgumentTypeError):
                main.positive_int(value)


if __name__ == "__main__":
    unittest.main()
