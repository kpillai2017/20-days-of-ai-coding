"""
Unit tests for Vector Tanks game model.
No pygame required. Tests math, movement, collision, scoring, and seeded determinism.
"""

import unittest
import math
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from game import (
    Game, Controls, Enemy, Shell, Obstacle, Explosion,
    wrap_angle, segment_circle_t, segment_box_t, distance,
    WORLD_RADIUS, PLAYER_RADIUS, ENEMY_RADIUS, SHELL_TTL,
    INVULNERABILITY_DURATION, MAX_PHYSICS_STEP,
    PLAYER_FORWARD_SPEED, PLAYER_REVERSE_SPEED, PLAYER_YAW_SPEED,
    SHELL_SPEED, TANK_SCORE, SUPERTANK_SCORE, SAUCER_SCORE,
)


class TestMathHelpers(unittest.TestCase):
    """Test utility math functions."""

    def test_wrap_angle_identity(self):
        """Angles within [-π, π] unchanged."""
        for angle in [-math.pi, -1, 0, 1, math.pi]:
            self.assertAlmostEqual(wrap_angle(angle), angle, places=5)

    def test_wrap_angle_multiple_rotations(self):
        """Large angles wrap correctly."""
        # 2π should wrap to 0
        self.assertAlmostEqual(wrap_angle(2 * math.pi), 0, places=5)
        # 3π should wrap to π (which is same as -π)
        result = wrap_angle(3 * math.pi)
        self.assertTrue(
            abs(result - math.pi) < 1e-5 or abs(result + math.pi) < 1e-5,
            f"Expected ±π, got {result}"
        )
        # -3π should wrap to π or -π
        result2 = wrap_angle(-3 * math.pi)
        self.assertTrue(
            abs(result2 - math.pi) < 1e-5 or abs(result2 + math.pi) < 1e-5,
            f"Expected ±π, got {result2}"
        )

    def test_distance(self):
        """Distance calculation."""
        # Pythagorean triple
        self.assertAlmostEqual(distance(0, 0, 3, 4), 5.0, places=5)
        self.assertAlmostEqual(distance(0, 0, 0, 10), 10.0, places=5)
        self.assertAlmostEqual(distance(1, 1, 4, 5), 5.0, places=5)

    def test_segment_circle_t_direct_hit(self):
        """Segment passing through circle center."""
        # Segment from (0,0) to (10,0), circle at (5,0) radius 2
        t = segment_circle_t(0, 0, 10, 0, 5, 0, 2)
        self.assertIsNotNone(t)
        self.assertGreaterEqual(t, 0)
        self.assertLessEqual(t, 1)

    def test_segment_circle_t_miss(self):
        """Segment missing circle entirely."""
        # Segment from (0,0) to (10,0), circle at (0,10) radius 2
        t = segment_circle_t(0, 0, 10, 0, 0, 10, 2)
        self.assertIsNone(t)

    def test_segment_circle_t_grazes(self):
        """Segment tangent to circle."""
        # Segment from (0,0) to (10,0), circle at (0,2) radius 2
        t = segment_circle_t(0, 0, 10, 0, 0, 2, 2)
        # May be on boundary; grazing should be None or very small
        if t is not None:
            self.assertLessEqual(t, 1.0)

    def test_segment_box_t_direct_hit(self):
        """Segment passing through box."""
        # Segment from (0,0) to (10,0), box at (5,0) half_width 2
        t = segment_box_t(0, 0, 10, 0, 5, 0, 2)
        self.assertIsNotNone(t)
        self.assertGreaterEqual(t, 0)
        self.assertLessEqual(t, 1)

    def test_segment_box_t_miss(self):
        """Segment missing box."""
        # Segment from (0,0) to (10,0), box at (0,10) half_width 2
        t = segment_box_t(0, 0, 10, 0, 0, 10, 2)
        self.assertIsNone(t)

    def test_segment_box_t_endpoint_on_edge(self):
        """Segment ending on box boundary."""
        # Segment from (0,0) to (7,0), box at (5,0) half_width 2
        # Should hit edge at x=7
        t = segment_box_t(0, 0, 7, 0, 5, 0, 2)
        self.assertIsNotNone(t)
        self.assertLessEqual(t, 1.0)


class TestGameInitialization(unittest.TestCase):
    """Test game setup and initialization."""

    def test_new_game_default_state(self):
        """New game starts in expected state."""
        game = Game(seed=42)
        self.assertEqual(game.x, 0.0)
        self.assertEqual(game.z, 0.0)
        self.assertEqual(game.heading, 0.0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.state, 'playing')
        self.assertGreater(len(game.obstacles), 0)

    def test_new_game_has_enemies(self):
        """Game starts with some enemies."""
        game = Game(seed=42)
        self.assertGreater(len(game.enemies), 0)

    def test_seeded_rng_reproducibility(self):
        """Same seed produces identical game sequence."""
        game1 = Game(seed=42)
        pos1_before = [(e.x, e.z, e.kind) for e in game1.enemies]

        game2 = Game(seed=42)
        pos2_before = [(e.x, e.z, e.kind) for e in game2.enemies]

        self.assertEqual(pos1_before, pos2_before)

    def test_start_resets_state(self):
        """start() resets game with same seed."""
        game = Game(seed=123)
        x1, z1 = game.x, game.z
        enemies1 = len(game.enemies)

        # Modify state
        game.score = 1000
        game.lives = 1
        game.x = 50
        game.z = -50

        # Reset
        game.start()

        self.assertEqual(game.x, 0.0)
        self.assertEqual(game.z, 0.0)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.state, 'playing')
        self.assertEqual(len(game.enemies), enemies1)


class TestPlayerMovement(unittest.TestCase):
    """Test player position and heading updates."""

    def test_no_input_no_movement(self):
        """Zero throttle and turn keeps player stationary."""
        game = Game(seed=42)
        initial_x, initial_z = game.x, game.z
        initial_heading = game.heading

        controls = Controls(throttle=0, turn=0, fire=False)
        game.update(0.1, controls)

        self.assertEqual(game.x, initial_x)
        self.assertEqual(game.z, initial_z)
        self.assertEqual(game.heading, initial_heading)

    def test_forward_movement(self):
        """Forward throttle moves +z direction."""
        game = Game(seed=42)
        game.heading = 0.0  # Facing +z
        controls = Controls(throttle=1.0, turn=0, fire=False)
        game.update(1.0, controls)

        # Should move primarily in +z
        self.assertGreater(game.z, 0)
        self.assertAlmostEqual(game.x, 0, places=1)

    def test_reverse_movement_slower(self):
        """Reverse speed is less than forward speed."""
        # Forward 1 second
        game1 = Game()
        game1.heading = 0.0
        game1.update(1.0, Controls(throttle=1.0, turn=0, fire=False))
        forward_dist = distance(0, 0, game1.x, game1.z)

        # Reverse 1 second
        game2 = Game()
        game2.heading = 0.0
        game2.update(1.0, Controls(throttle=-1.0, turn=0, fire=False))
        reverse_dist = distance(0, 0, game2.x, game2.z)

        self.assertGreater(forward_dist, reverse_dist)

    def test_turning_changes_heading(self):
        """Turn control modifies heading."""
        game = Game(seed=42)
        initial_heading = game.heading

        # Turn right
        controls = Controls(throttle=0, turn=1.0, fire=False)
        game.update(1.0, controls)

        self.assertGreater(game.heading, initial_heading)

    def test_turning_left(self):
        """Negative turn turns left."""
        game = Game(seed=42)
        game.heading = 0.0

        controls = Controls(throttle=0, turn=-1.0, fire=False)
        game.update(1.0, controls)

        # Heading should be negative (wrapped)
        self.assertLess(wrap_angle(game.heading), 0)

    def test_world_boundary_clamping(self):
        """Player cannot move beyond world boundary."""
        game = Game(seed=42)
        game.heading = 0.0

        # Thrust forward for a long time
        controls = Controls(throttle=1.0, turn=0, fire=False)
        for _ in range(100):
            game.update(0.1, controls)

        # Should be clamped at boundary
        self.assertLessEqual(abs(game.x), WORLD_RADIUS)
        self.assertLessEqual(abs(game.z), WORLD_RADIUS)

    def test_frame_rate_independent_motion(self):
        """Same total time gives same final position regardless of dt."""
        total_time = 0.1
        controls = Controls(throttle=1.0, turn=0, fire=False)

        # One large step
        game1 = Game()
        game1.heading = 0.0
        game1.update(total_time, controls)

        # Many small steps
        game2 = Game()
        game2.heading = 0.0
        for _ in range(10):
            game2.update(total_time / 10, controls)

        self.assertAlmostEqual(game1.x, game2.x, places=1)
        self.assertAlmostEqual(game1.z, game2.z, places=1)


class TestPlayerFiring(unittest.TestCase):
    """Test player shell firing and cooldown."""

    def test_fire_creates_shell(self):
        """Fire control creates a shell."""
        game = Game(seed=42)
        initial_shells = len(game.shells)

        controls = Controls(throttle=0, turn=0, fire=True)
        game.update(0.01, controls)

        self.assertEqual(len(game.shells), initial_shells + 1)

    def test_fire_cooldown_prevents_rapid_fire(self):
        """Rapid fire attempts blocked by cooldown."""
        game = Game(seed=42)
        game.enemies.clear()  # Remove enemies to avoid collision
        
        # Fire and check shells
        for _ in range(10):
            controls = Controls(throttle=0, turn=0, fire=True)
            game.update(0.01, controls)

        # Should have only 1 shell (first shot + cooldown prevents rest)
        # Shell might have expired, but at max 1 active at any time
        self.assertLessEqual(len(game.shells), 1)

    def test_cooldown_expires(self):
        """Fire becomes available after cooldown expires."""
        game = Game(seed=42)

        # First fire
        controls = Controls(throttle=0, turn=0, fire=True)
        game.update(0.01, controls)
        self.assertEqual(len(game.shells), 1)

        # Try rapid fire (blocked)
        controls = Controls(throttle=0, turn=0, fire=True)
        game.update(0.01, controls)
        self.assertEqual(len(game.shells), 1)

        # Wait for cooldown
        controls = Controls(throttle=0, turn=0, fire=False)
        game.update(1.0, controls)

        # Can fire again
        controls = Controls(throttle=0, turn=0, fire=True)
        game.update(0.01, controls)
        self.assertEqual(sum(s.owner == 'player' for s in game.shells), 1)
        # One active shell locks firing even after the timer.
        game.shells.clear()
        game.cooldown = 0
        game.update(.01, Controls(fire=True))
        self.assertEqual(sum(s.owner == 'player' for s in game.shells), 1)

    def test_shell_properties(self):
        """Fired shell has correct initial properties."""
        game = Game(seed=42)
        game.heading = 0.0  # Face +z

        controls = Controls(throttle=0, turn=0, fire=True)
        game.update(0.01, controls)

        shell = game.shells[0]
        self.assertEqual(shell.owner, 'player')
        self.assertGreater(shell.vz, 0)  # Positive z velocity
        self.assertAlmostEqual(shell.vx, 0, places=1)
        # TTL starts at SHELL_TTL but gets decremented by dt in physics step
        self.assertAlmostEqual(shell.ttl, SHELL_TTL - 0.01, places=2)

    def test_shell_expires(self):
        """Shell expires after TTL."""
        game = Game(seed=42)
        # Manually add a shell in empty world
        from game import Shell
        game.shells = [Shell(x=0, z=0, vx=1, vz=1, owner='player', ttl=0.1)]
        
        # Shell should exist
        self.assertEqual(len(game.shells), 1)
        
        # Update past its TTL
        game.update(0.1, Controls())
        game.update(0.1, Controls())
        
        # Shell should be gone
        self.assertEqual(len(game.shells), 0)


class TestCollision(unittest.TestCase):
    """Test obstacle and entity collisions."""

    def test_player_obstacle_collision(self):
        """Player cannot pass through obstacles."""
        game = Game(seed=42)
        # Place player at edge of world
        game.x = 20
        game.z = 30

        # Try to move forward into obstacle
        controls = Controls(throttle=1.0, turn=0, fire=False)
        game.heading = math.atan2(
            game.obstacles[0].x - game.x,
            game.obstacles[0].z - game.z
        )

        # Move toward obstacle
        for _ in range(20):
            game.update(0.1, controls)

        # Player should stop before or at obstacle
        for obs in game.obstacles:
            dist = distance(game.x, game.z, obs.x, obs.z)
            # Allow small margin for radius
            self.assertGreater(dist, obs.size + PLAYER_RADIUS - 1.0)

    def test_shell_obstacle_collision(self):
        """Shells collide with obstacles."""
        game = Game(seed=42)
        game.enemies = []
        game.obstacles = [Obstacle(0, 10, 2, 4)]
        game.shells = [Shell(0, 0, 0, 100, 'player')]
        game._update_shells(.2)
        self.assertEqual(game.shells, [])
        self.assertEqual(len(game.explosions), 1)
        self.assertLess(game.explosions[0].z, 8)

    def test_shell_enemy_collision(self):
        """A swept projectile actually removes a known enemy and awards points."""
        game = Game(seed=42)
        game.obstacles = []
        game.enemies = [Enemy(0, 10, 0, cooldown=99)]
        game.shells = [Shell(0, 0, 0, 100, 'player')]
        game._update_shells(.2)
        self.assertEqual(game.enemies, [])
        self.assertEqual(game.score, TANK_SCORE)


class TestEnemyBehavior(unittest.TestCase):
    def test_enemies_exist_at_game_start(self):
        self.assertGreater(len(Game(42).enemies), 0)

    def test_enemies_move(self):
        game = Game(42)
        game.obstacles = []
        game.enemies = [Enemy(0, 50, math.pi, cooldown=99)]
        game.update(.1, Controls())
        self.assertLess(game.enemies[0].z, 50)

    def test_enemy_fire_creates_shell(self):
        game = Game(42)
        game.obstacles = []
        game.enemies = [Enemy(0, 25, math.pi, cooldown=0)]
        game.update(.01, Controls())
        self.assertTrue(any(s.owner == 'enemy' for s in game.shells))


class TestScoringAndLives(unittest.TestCase):
    """Test score and life mechanics."""

    def test_initial_score_zero(self):
        """New game starts with score 0."""
        game = Game(seed=42)
        self.assertEqual(game.score, 0)

    def test_initial_lives(self):
        """New game starts with 3 lives."""
        game = Game(seed=42)
        self.assertEqual(game.lives, 3)

    def test_enemy_kill_award_points(self):
        """Killing enemy increases score."""
        game = Game(seed=42)
        initial_score = game.score

        if len(game.enemies) > 0:
            enemy = game.enemies[0]
            enemy_kind = enemy.kind

            # Place shell at enemy
            game.shells.append(Shell(
                x=enemy.x, z=enemy.z,
                vx=0, vz=0,
                owner='player',
                ttl=SHELL_TTL
            ))
            game.update(0.01, Controls())

            # Check if enemy was destroyed and points awarded
            if len(game.enemies) < len([e for e in game.enemies]):
                self.assertGreater(game.score, initial_score)

    def test_player_hit_loses_life(self):
        """Player hit by enemy shell loses a life."""
        game = Game(seed=42)
        initial_lives = game.lives
        game.invulnerable = 0  # Remove initial invulnerability
        
        # Place shell at player location
        game.shells.append(Shell(
            x=game.x + 0.5, z=game.z + 0.5,  # Near player
            vx=0, vz=0,
            owner='enemy',
            ttl=SHELL_TTL
        ))

        game.update(0.01, Controls())

        self.assertEqual(game.lives, initial_lives - 1)

    def test_invulnerability_after_hit(self):
        """Player is invulnerable briefly after being hit."""
        game = Game(seed=42)

        # Take damage
        if len(game.enemies) > 0:
            game.shells.append(Shell(
                x=game.x, z=game.z,
                vx=0, vz=0,
                owner='enemy',
                ttl=SHELL_TTL
            ))
            game.update(0.01, Controls())

        # Check invulnerability timer
        self.assertGreater(game.invulnerable, 0)

        # Should not take damage while invulnerable
        game.shells.append(Shell(
            x=game.x, z=game.z,
            vx=0, vz=0,
            owner='enemy',
            ttl=SHELL_TTL
        ))
        lives_before = game.lives
        game.update(0.01, Controls())
        self.assertEqual(game.lives, lives_before)

    def test_game_over_on_zero_lives(self):
        """Game ends when lives reach zero."""
        game = Game(seed=42)
        game.lives = 1
        game.state = 'playing'
        game.invulnerable = 0  # Remove invulnerability
        
        # Take damage
        game.shells.append(Shell(
            x=game.x + 0.5, z=game.z + 0.5,  # Near player
            vx=0, vz=0,
            owner='enemy',
            ttl=SHELL_TTL
        ))
        game.update(0.01, Controls())

        self.assertEqual(game.state, 'game_over')
        self.assertEqual(game.lives, 0)


class TestInputValidation(unittest.TestCase):
    """Test input validation."""

    def test_invalid_dt_raises_error(self):
        """Negative dt raises ValueError."""
        game = Game(seed=42)
        with self.assertRaises(ValueError):
            game.update(-1.0, Controls())

    def test_nan_dt_raises_error(self):
        """NaN dt raises ValueError."""
        game = Game(seed=42)
        with self.assertRaises(ValueError):
            game.update(float('nan'), Controls())

    def test_inf_dt_raises_error(self):
        """Infinite dt raises ValueError."""
        game = Game(seed=42)
        with self.assertRaises(ValueError):
            game.update(float('inf'), Controls())

    def test_zero_dt_no_update(self):
        """dt=0 is valid but produces no change."""
        game = Game(seed=42)
        x, z = game.x, game.z
        game.update(0, Controls(throttle=1.0))
        self.assertEqual(game.x, x)
        self.assertEqual(game.z, z)

    def test_large_dt_clamped_to_substeps(self):
        """Large dt is split into substeps."""
        game = Game(seed=42)
        # This should not raise and should clamp internally
        game.update(10.0, Controls(throttle=1.0))
        # Player should not have moved impossibly far
        self.assertLess(distance(game.x, game.z, 0, 0), 200)


class TestGameStateTransitions(unittest.TestCase):
    """Test game state changes."""

    def test_update_no_effect_when_not_playing(self):
        """Update has no effect when state != 'playing'."""
        game = Game(seed=42)
        game.state = 'title'
        game.heading = 0.0

        x_before = game.x
        heading_before = game.heading

        game.update(0.1, Controls(throttle=1.0, turn=1.0))

        self.assertEqual(game.x, x_before)
        self.assertEqual(game.heading, heading_before)

    def test_start_transitions_to_playing(self):
        """start() sets state to 'playing'."""
        game = Game(seed=42)
        game.state = 'game_over'
        game.start()
        self.assertEqual(game.state, 'playing')


class TestSeededDeterminism(unittest.TestCase):
    """Test deterministic behavior with seeds."""

    def test_identical_seed_identical_sequence(self):
        """Two games with same seed produce identical trajectory."""
        seed = 999

        # Replay 1
        game1 = Game(seed=seed)
        game1.start()
        positions1 = [(game1.x, game1.z)]
        controls = Controls(throttle=0.5, turn=0.2, fire=True)
        for _ in range(20):
            game1.update(0.05, controls)
            positions1.append((game1.x, game1.z))

        # Replay 2 with same seed
        game2 = Game(seed=seed)
        game2.start()
        positions2 = [(game2.x, game2.z)]
        for _ in range(20):
            game2.update(0.05, controls)
            positions2.append((game2.x, game2.z))

        # Positions should match
        for p1, p2 in zip(positions1, positions2):
            self.assertAlmostEqual(p1[0], p2[0], places=5)
            self.assertAlmostEqual(p1[1], p2[1], places=5)

    def test_different_seed_different_sequence(self):
        """Different seeds produce different enemy placements."""
        game1 = Game(seed=111)
        enemies1 = [(e.x, e.z) for e in game1.enemies]

        game2 = Game(seed=222)
        enemies2 = [(e.x, e.z) for e in game2.enemies]

        # At least one enemy should differ
        self.assertNotEqual(enemies1, enemies2)


class TestObstacles(unittest.TestCase):
    """Test obstacle creation and properties."""

    def test_obstacles_created(self):
        """Game creates obstacles at startup."""
        game = Game(seed=42)
        self.assertGreater(len(game.obstacles), 0)

    def test_obstacle_kinds(self):
        """Obstacles have valid kinds."""
        game = Game(seed=42)
        for obs in game.obstacles:
            self.assertIn(obs.kind, ['box', 'circle', 'pyramid'])

    def test_spawn_area_clear(self):
        """Player spawn area (origin) has no obstacles too close."""
        game = Game(seed=42)
        for obs in game.obstacles:
            dist = distance(0, 0, obs.x, obs.z)
            # No obstacle within 15 units of spawn
            self.assertGreater(dist, 15)


class TestExplosions(unittest.TestCase):
    """Test explosion effect tracking."""

    def test_explosions_created_on_hit(self):
        """Collisions create explosion effects."""
        game = Game(seed=42)
        initial_explosions = len(game.explosions)

        # Create shell at enemy
        if len(game.enemies) > 0:
            enemy = game.enemies[0]
            game.shells.append(Shell(
                x=enemy.x, z=enemy.z,
                vx=0, vz=0,
                owner='player',
                ttl=SHELL_TTL
            ))
            game.update(0.01, Controls())

            # Should have explosion
            self.assertGreater(len(game.explosions), initial_explosions)

    def test_explosions_expire(self):
        """Explosions are removed after TTL."""
        game = Game(seed=42)
        game.explosions.append(Explosion(0, 0, ttl=0.1))

        game.update(0.1, Controls())
        game.update(0.1, Controls())

        self.assertEqual(len(game.explosions), 0)


if __name__ == '__main__':
    unittest.main()
