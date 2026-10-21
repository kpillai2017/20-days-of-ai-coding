"""Rule tests need no pygame, display, sound device or third-party test runner.

We deliberately place balls just BEFORE a collision, not already embedded in a
paddle. Test arrangements should describe reachable gameplay situations.
"""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from game import Game, Rect, WIDTH, HEIGHT


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_rect_properties_and_edge_contact(self):
        rect = Rect(10, 20, 30, 40)
        self.assertEqual((rect.left, rect.right, rect.top, rect.bottom), (10, 40, 20, 60))
        self.assertEqual((rect.centerx, rect.centery), (25, 40))
        self.assertTrue(rect.intersects(Rect(39, 20, 5, 5)))
        self.assertFalse(rect.intersects(Rect(40, 20, 5, 5)))

    def test_initial_state_and_level_layout(self):
        g = self.game
        self.assertEqual((g.state, g.score, g.lives, len(g.bricks)), ("ready", 0, 3, 50))
        self.assertEqual(g.ball.centerx, g.paddle.centerx)
        self.assertEqual(g.ball.bottom, g.paddle.top)
        for brick in g.bricks:
            self.assertGreaterEqual(brick.top, 90)
            self.assertLess(brick.bottom, g.paddle.top)
            self.assertGreaterEqual(brick.left, 0)
            self.assertLessEqual(brick.right, WIDTH)

    def test_ready_paddle_moves_and_ball_follows(self):
        g = self.game
        start = g.paddle.x
        g.update(0.1, 1)
        self.assertAlmostEqual(g.paddle.x - start, 46)
        self.assertAlmostEqual(g.ball.centerx, g.paddle.centerx)
        self.assertEqual(g.state, "ready")

    def test_paddle_clamps_both_edges(self):
        g = self.game
        for direction, expected in ((-1, 0), (1, WIDTH - g.paddle.width)):
            for _ in range(30):
                g.update(0.1, direction)
            self.assertAlmostEqual(g.paddle.x, expected)

    def test_launch_and_repeat_launch(self):
        g = self.game
        g.launch()
        self.assertEqual(g.state, "playing")
        self.assertLess(g.vy, 0)
        self.assertAlmostEqual(math.hypot(g.vx, g.vy), 340)
        g.update(0.02)
        position = (g.ball.x, g.ball.y)
        g.launch()
        self.assertEqual((g.ball.x, g.ball.y), position)

    def test_wall_bounces_and_corner(self):
        for x, y, vx, vy, expected_x, expected_y in (
            (0, 300, -200, 0, 1, 0),
            (WIDTH - 12, 300, 200, 0, -1, 0),
            (400, 0, 0, -200, 0, 1),
            (0, 0, -200, -200, 1, 1),
        ):
            with self.subTest(position=(x, y)):
                g = Game()
                g.state = "playing"
                g.ball.x, g.ball.y, g.vx, g.vy = x, y, vx, vy
                g.update(0.01)
                self.assertEqual((g.vx > 0) - (g.vx < 0), expected_x)
                self.assertEqual((g.vy > 0) - (g.vy < 0), expected_y)
                self.assertGreaterEqual(g.ball.left, 0)
                self.assertGreaterEqual(g.ball.top, 0)
                self.assertLessEqual(g.ball.right, WIDTH)

    def test_paddle_top_bounce_angle_and_constant_speed(self):
        for offset in (-40, 0, 40):
            with self.subTest(offset=offset):
                g = Game()
                g.state = "playing"
                g.ball.x = g.paddle.centerx + offset - g.ball.width / 2
                g.ball.y = g.paddle.top - g.ball.height - 1
                g.vx, g.vy = 0, 200
                g.update(0.02)
                self.assertLess(g.vy, 0)
                self.assertEqual((g.vx > 0) - (g.vx < 0), (offset > 0) - (offset < 0))
                self.assertAlmostEqual(math.hypot(g.vx, g.vy), 340)
                self.assertLessEqual(g.ball.bottom, g.paddle.top)

    def test_paddle_does_not_rescue_already_missed_ball(self):
        for y, vy in ((551, 100), (565, -100)):
            g = Game()
            g.state = "playing"
            g.ball.y, g.vx, g.vy = y, 0, vy
            g.update(0.02)
            self.assertEqual(g.vy, vy)

    def test_moving_paddle_intercepts(self):
        g = self.game
        g.state = "playing"
        g.ball.x = g.paddle.right + 2
        g.ball.y = g.paddle.top - g.ball.height - 10
        g.vx, g.vy = 0, 200
        g.update(0.08, 1)
        self.assertLess(g.vy, 0)

    def test_brick_all_four_sides_score_once(self):
        for side in ("top", "bottom", "left", "right"):
            with self.subTest(side=side):
                g = Game()
                brick = Rect(300, 250, 68, 20)
                g.bricks = [brick, Rect(600, 100, 68, 20)]
                g.state = "playing"
                g.ball.x, g.ball.y = brick.centerx - 6, brick.centery - 6
                g.vx = g.vy = 0
                if side == "top":
                    g.ball.y, g.vy = brick.top - 13, 200
                elif side == "bottom":
                    g.ball.y, g.vy = brick.bottom + 1, -200
                elif side == "left":
                    g.ball.x, g.vx = brick.left - 13, 200
                else:
                    g.ball.x, g.vx = brick.right + 1, -200
                old_velocity = (g.vx, g.vy)
                g.update(0.02)
                self.assertNotIn(brick, g.bricks)
                self.assertEqual(g.score, 10)
                self.assertEqual((g.vx, g.vy), (-old_velocity[0], -old_velocity[1]))
                g.update(0.02)
                self.assertEqual(g.score, 10)

    def test_adjacent_brick_seam_no_double_reflection(self):
        g = self.game
        g.bricks = [Rect(300, 250, 68, 20), Rect(376, 250, 68, 20)]
        g.state = "playing"
        g.ball.x, g.ball.y = 366, 237
        g.vx, g.vy = 0, 200
        g.update(0.02)
        self.assertEqual(g.score, 10)
        self.assertLess(g.vy, 0)

    def test_life_loss_preserves_progress_and_relaunches(self):
        g = self.game
        g.bricks.pop()
        g.score = 10
        for lives in (2, 1, 0):
            g.launch()
            g.ball.y = HEIGHT + 1
            g.vy = 340  # A missed ball is descending, not a fresh upward serve.
            g.update(0.1)
            self.assertEqual(g.lives, lives)
            self.assertEqual((g.score, len(g.bricks)), (10, 49))
            self.assertEqual(g.state, "ready" if lives else "game_over")
        g.update(0.1)
        self.assertEqual(g.lives, 0)

    def test_ball_partly_visible_does_not_cost_life(self):
        g = self.game
        g.state = "playing"
        g.ball.x, g.ball.y, g.vx, g.vy = 0, HEIGHT - 1, 0, 0
        g.update(0.01)
        self.assertEqual(g.lives, 3)

    def test_last_brick_wins_and_stops(self):
        g = self.game
        g.bricks = [Rect(300, 250, 68, 20)]
        g.state = "playing"
        g.ball.x, g.ball.y, g.vx, g.vy = 320, 237, 0, 200
        g.update(0.02)
        self.assertEqual((g.state, g.score), ("won", 10))
        before = (g.ball.x, g.ball.y, g.paddle.x)
        g.update(0.1, 1)
        g.launch()
        self.assertEqual((g.ball.x, g.ball.y, g.paddle.x), before)

    def test_full_restart_resets_everything(self):
        for state in ("won", "game_over", "playing"):
            g = Game()
            g.state, g.score, g.lives = state, 200, 0
            g.bricks.clear()
            g.paddle.x = 0
            g.reset()
            self.assertEqual((g.state, g.score, g.lives, len(g.bricks)), ("ready", 0, 3, 50))
            self.assertEqual(g.paddle.centerx, WIDTH / 2)
            self.assertEqual((g.vx, g.vy), (0, 0))

    def test_dt_validation_zero_and_long_pause(self):
        for invalid in (-1, math.inf, -math.inf, math.nan):
            with self.subTest(dt=invalid), self.assertRaises(ValueError):
                self.game.update(invalid)
        for invalid in (math.inf, math.nan):
            with self.assertRaises(ValueError):
                self.game.update(0.1, invalid)
        start = self.game.paddle.x
        self.game.update(0, 1)
        self.assertEqual(self.game.paddle.x, start)
        self.game.update(100, 1)
        self.assertAlmostEqual(self.game.paddle.x, start + 46)

    def test_frame_rate_independent_motion(self):
        a, b = Game(), Game()
        a.launch()
        b.launch()
        a.update(0.1, 1)
        for _ in range(10):
            b.update(0.01, 1)
        self.assertAlmostEqual(a.ball.x, b.ball.x)
        self.assertAlmostEqual(a.ball.y, b.ball.y)
        self.assertAlmostEqual(a.paddle.x, b.paddle.x)

    def test_independent_instances(self):
        self.game.bricks.clear()
        self.assertEqual(len(Game().bricks), 50)


if __name__ == "__main__":
    unittest.main()
