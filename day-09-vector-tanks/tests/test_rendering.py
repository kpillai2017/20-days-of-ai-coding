"""Headless graphics/control checks plus precise combat regression cases."""
import math
import os
from pathlib import Path
import sys
import unittest

# Select drivers BEFORE importing pygame; no real display/audio needed in CI.
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from game import Game, Controls, Enemy, Shell, Obstacle, segment_circle_t
from renderer import Renderer, camera_point, project_segment
from main import main, read_controls, Sounds


class CombatRegression(unittest.TestCase):
    def arena(self):
        game = Game(42)
        game.obstacles, game.enemies, game.shells = [], [], []
        game.invulnerable = 0
        return game

    def test_stationary_and_inside_segments(self):
        self.assertEqual(segment_circle_t(0,0,0,0,0,0,1),0)
        self.assertIsNone(segment_circle_t(2,0,2,0,0,0,1))
        self.assertEqual(segment_circle_t(0,0,3,0,0,0,1),0)

    def test_nearest_enemy_before_wall(self):
        game = self.arena()
        game.enemies = [Enemy(0,10,0)]
        game.obstacles = [Obstacle(0,20,2,4)]
        game.shells = [Shell(0,0,0,200,'player')]
        game._update_shells(.15)
        self.assertEqual(game.score,1000)
        self.assertEqual(game.enemies,[])

    def test_wall_before_enemy(self):
        game = self.arena()
        game.enemies = [Enemy(0,20,0)]
        game.obstacles = [Obstacle(0,10,2,4)]
        game.shells = [Shell(0,0,0,200,'player')]
        game._update_shells(.15)
        self.assertEqual(game.score,0)
        self.assertEqual(len(game.enemies),1)

    def test_nearest_enemy_not_list_order(self):
        game = self.arena()
        far, near = Enemy(0,20,0), Enemy(0,10,0)
        game.enemies = [far, near]
        game.shells = [Shell(0,0,0,300,'player')]
        game._update_shells(.1)
        self.assertEqual(game.enemies,[far])

    def test_swept_enemy_shell_hits_player(self):
        game = self.arena()
        game.shells = [Shell(0,-10,0,200,'enemy')]
        game._update_shells(.1)
        self.assertEqual(game.lives,2)
        self.assertEqual(game.shells,[])

    def test_grace_absorbs_additional_hit(self):
        game = self.arena()
        game.invulnerable = 2
        game.shells = [Shell(0,-10,0,200,'enemy')]
        game._update_shells(.1)
        self.assertEqual(game.lives,3)
        self.assertEqual(game.shells,[])

    def test_single_shot_even_after_cooldown(self):
        game = self.arena()
        game.shells = [Shell(20,20,0,0,'player')]
        game._update_player(.01, Controls(fire=True))
        self.assertEqual(len(game.shells),1)

    def test_saucer_does_not_fire(self):
        game = self.arena()
        game.enemies = [Enemy(0,25,math.pi,'saucer')]
        game._update_enemies(.1)
        self.assertEqual(game.shells,[])

    def test_cover_blocks_enemy_fire(self):
        game = self.arena()
        game.obstacles = [Obstacle(0,12,3,4)]
        game.enemies = [Enemy(0,25,math.pi,cooldown=0)]
        game._update_enemies(.01)
        self.assertEqual(game.shells,[])

    def test_long_frame_cap(self):
        game = self.arena()
        game.update(10,Controls(throttle=1))
        self.assertAlmostEqual(game.elapsed,.1)
        self.assertAlmostEqual(game.z,1.2)

    def test_spawns_clear_cover_and_player(self):
        for seed in range(100):
            game = Game(seed)
            for enemy in game.enemies:
                self.assertGreater(math.hypot(enemy.x-game.x,enemy.z-game.z),40)
                self.assertIsNone(game._check_collision_path(enemy.x,enemy.z,enemy.x,enemy.z,1.4))


class Graphics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((1000,750))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_camera_forward_and_right_turn(self):
        self.assertEqual(camera_point((0,1.55,10),0,0,0),(0,0,10))
        x,y,z = camera_point((10,1.55,0),0,0,math.pi/2)
        self.assertAlmostEqual(x,0)
        self.assertAlmostEqual(z,10)

    def test_projection_and_near_clipping(self):
        self.assertIsNone(project_segment((0,0,-2),(1,0,-1)))
        line = project_segment((0,0,-1),(0,0,10))
        self.assertEqual(line,((500,360),(500,360)))
        self.assertEqual(project_segment((0,0,10),(1,0,10)),((500,360),(562,360)))

    def test_draw_all_states(self):
        renderer = Renderer()
        game = Game(42)
        game.enemies = [Enemy(-6,30,math.pi), Enemy(0,40,math.pi,'supertank'), Enemy(8,35,0,'saucer')]
        for state in ('title','playing','game_over'):
            game.state = state
            image = renderer.draw(game)
            self.assertEqual(image.get_size(),(1000,750))
            self.assertGreater(len(pygame.image.tostring(image,'RGB').replace(b'\x00',b'')),1000)
        renderer.draw(game,True)

    def test_controls_and_tracks(self):
        class Keys:
            def __init__(self,*keys): self.keys=keys
            def __getitem__(self,key): return key in self.keys
        self.assertEqual(read_controls(Keys(pygame.K_w,pygame.K_d)),Controls(1,1,False))
        self.assertEqual(read_controls(Keys(pygame.K_t,pygame.K_u)),Controls(1,0,False))
        self.assertEqual(read_controls(Keys(pygame.K_t,pygame.K_j)),Controls(0,1,False))
        self.assertEqual(read_controls(Keys(pygame.K_g,pygame.K_u)),Controls(0,-1,False))
        self.assertEqual(read_controls(Keys(pygame.K_g,pygame.K_j)),Controls(-1,0,False))
        self.assertTrue(read_controls(Keys(pygame.K_SPACE)).fire)

    def test_synthesised_sound(self):
        sounds = Sounds(True)
        self.assertTrue(sounds.enabled)
        sounds.play('shot')
        sounds.motor(True,True)
        sounds.motor(False,False)

    def test_real_loop_smoke(self):
        self.assertEqual(main(['--seed','42','--demo','--frames','3','--mute']),0)
        # main quits all subsystems; restore them for remaining class tests.
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((1000,750))


if __name__ == '__main__':
    unittest.main()
