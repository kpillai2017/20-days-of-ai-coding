"""The two projections must share one game/animation and correct hit testing."""
import os
from pathlib import Path
import sys
import time
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from engine import Position,notation_to_sq
from graphics import project,square_at
from animation import STYLES,pose
from main import App,Sounds


class ViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init();pygame.font.init();pygame.display.set_mode((1240,800))
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def test_every_square_both_views_both_orientations(self):
        for view in ('2d','3d'):
            for flipped in (False,True):
                for sq in range(64):
                    pos=project(sq%8,sq//8,flipped=flipped,view=view)
                    self.assertEqual(square_at(pos,flipped,view),sq)
        for view in ('2d','3d'):self.assertIsNone(square_at((-100,500),view=view))
        self.assertGreater(project(0,0,flipped=True,view='2d')[1],project(0,7,flipped=True,view='2d')[1])

    def test_white_view_files_run_left_to_right_in_both_modes(self):
        app=App(True,False)
        try:
            self.assertTrue(app.flipped)  # Default White-facing orientation.
            for view in ('2d','3d'):
                for rank in range(8):
                    xs=[project(file,rank,flipped=app.flipped,view=view)[0] for file in range(8)]
                    self.assertEqual(xs,sorted(xs))
                    self.assertEqual(len(set(xs)),8)
                # Rank one stays nearer than rank eight after the correction.
                self.assertGreater(project(0,0,flipped=app.flipped,view=view)[1],
                                   project(0,7,flipped=app.flipped,view=view)[1])
        finally:app.close()

    def test_toggle_preserves_game_selection_and_animation(self):
        app=App(True,False)
        try:
            app.selected=12;before=app.position.fen()
            app.key(pygame.K_v);self.assertEqual(app.view,'2d')
            self.assertEqual(app.selected,12);self.assertEqual(app.position.fen(),before)
            app.renderer.draw(app)
            for name in ('e2','e4'):
                sq=notation_to_sq(name)
                app.click(project(sq%8,sq//8,flipped=app.flipped,view=app.view))
            app.update(.1);elapsed=app.animation['time']
            app.key(pygame.K_v);self.assertEqual(app.view,'3d')
            self.assertEqual(app.animation['time'],elapsed)
            app.renderer.draw(app)
            for _ in range(10):app.update(.1)
            self.assertIsNone(app.animation);self.assertEqual(len(app.position.history),1)
            app.action('view');app.action('undo')
            self.assertEqual(app.position.fen(),before)
        finally:app.close()

    def test_all_piece_capture_choreography_in_both_views(self):
        cases={
            'p':('4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1','e4d5'),
            'n':('4k3/8/8/3p4/8/4N3/8/4K3 w - - 0 1','e3d5'),
            'b':('4k3/8/8/3p4/8/5B2/8/4K3 w - - 0 1','f3d5'),
            'r':('4k3/8/8/3p4/8/8/8/3RK3 w - - 0 1','d1d5'),
            'q':('4k3/8/8/3p4/8/8/8/3QK3 w - - 0 1','d1d5'),
            'k':('7k/8/8/3p4/4K3/8/8/8 w - - 0 1','e4d5')}
        app=App(True,False)
        try:
            for kind,(fen,uci) in cases.items():
                app.position=Position(fen);app.refresh()
                move=next(m for m in app.legal if m.uci()==uci)
                app.animate(move)
                self.assertEqual(app.animation['duration'],STYLES[kind][1])
                for fraction in (0,.3,.5,.65,.8,.95):
                    app.animation['time']=fraction*app.animation['duration']
                    values=pose(app.animation)
                    self.assertTrue(0<=values['progress']<=1)
                    for view in ('2d','3d'):
                        app.view=view;app.renderer.draw(app)
                app.animation['time']=app.animation['duration']
                app.update(0)
                self.assertEqual(app.position.board[move.to_sq].lower(),kind)
                self.assertEqual(len(app.position.history),1)
        finally:app.close()

    def test_hint_highlights_without_playing_and_clears_on_move(self):
        app=App(True,False);app.level='easy'
        try:
            before=app.position.fen();keys=app.position.keys[:]
            app.renderer.draw(app)
            self.assertIn('hint',app.renderer.buttons)
            app.key(pygame.K_h)
            end=time.monotonic()+5
            while app.future and time.monotonic()<end:
                app.update(.01);time.sleep(.002)
            self.assertIsNone(app.future)
            self.assertIn(app.hint_move,app.legal)
            self.assertEqual(app.position.fen(),before)
            self.assertEqual(app.position.keys,keys)
            self.assertEqual(app.position.history,[])
            self.assertEqual(app.moves,[])
            self.assertIsNone(app.animation)
            self.assertEqual(app.selected,app.hint_move.from_sq)
            hint=app.hint_move
            for view in ('2d','3d'):
                app.view=view;app.renderer.draw(app)
                self.assertEqual(app.hint_move,hint)
            app.animate(hint);self.assertIsNone(app.hint_move)
        finally:app.close()

    def test_hint_cancel_and_terminal_guards(self):
        app=App(True,False)
        try:
            app.action('hint');self.assertIsNotNone(app.future)
            pending=app.future
            app.action('hint');self.assertIs(app.future,pending)
            app.action('new');app.update(.01)
            self.assertIsNone(app.hint_move);self.assertIsNone(app.future)
            app.position=Position('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1');app.refresh()
            app.action('hint');self.assertIsNone(app.future)
            app.new();app.animate(app.legal[0]);app.action('hint')
            self.assertIsNone(app.future)
        finally:app.close()

    def test_camera_projection_inverse_all_squares(self):
        for yaw in (0,.3,1.57,3.14,5.7):
            for zoom in (.65,1.,1.5):
                for tilt in (.28,.5,.85):
                    for flipped in (False,True):
                        for sq in range(64):
                            point=project(sq%8,sq//8,flipped=flipped,yaw=yaw,zoom=zoom,tilt=tilt)
                            self.assertEqual(square_at(point,flipped,yaw=yaw,zoom=zoom,tilt=tilt),sq)

    def test_camera_controls_bounds_and_game_invariance(self):
        app=App(True,False)
        try:
            before=app.position.fen()
            app.action('rotate_right');self.assertNotEqual(app.yaw,0)
            app.orbit(80,300);self.assertEqual(app.tilt,.85)
            app.orbit(0,-600);self.assertEqual(app.tilt,.28)
            for _ in range(50):app.action('zoom_in')
            self.assertEqual(app.zoom,1.5)
            for _ in range(50):app.action('zoom_out')
            self.assertEqual(app.zoom,.65)
            app.renderer.draw(app)
            sq=notation_to_sq('e2')
            app.click(project(sq%8,sq//8,flipped=app.flipped,yaw=app.yaw,zoom=app.zoom,tilt=app.tilt))
            self.assertEqual(app.selected,sq)
            self.assertEqual(app.position.fen(),before)
            saved=(app.yaw,app.zoom,app.tilt)
            app.action('view');app.action('zoom_in');app.orbit(20,20)
            self.assertEqual((app.yaw,app.zoom,app.tilt),saved)
            app.renderer.draw(app)
            app.action('view');app.key(pygame.K_HOME)
            self.assertEqual((app.yaw,app.zoom,app.tilt),(0.,1.,.5))
            for yaw in (0,1.2,2.8,4.7):
                app.yaw=yaw;app.renderer.draw(app)
        finally:app.close()

    def test_left_drag_rotates_without_selecting_or_moving(self):
        app=App(True,False)
        try:
            app.renderer.draw(app)
            point=project(4,3,flipped=app.flipped)
            before=app.position.fen()
            app.pointer_down(point)
            app.pointer_motion((point[0]+30,point[1]+12))
            first=app.yaw
            app.pointer_motion((point[0]+40,point[1]+15))
            self.assertAlmostEqual(app.yaw-first,.08)
            app.pointer_up((point[0]+40,point[1]+15))
            self.assertNotEqual(app.yaw,0)
            self.assertEqual(app.position.fen(),before)
            self.assertIsNone(app.selected)
            self.assertIsNone(app.animation)
            self.assertIsNone(app.pointer_start)
            self.assertNotIn('rotate_left',app.renderer.buttons)
            self.assertNotIn('rotate_right',app.renderer.buttons)
            self.assertLessEqual(app.renderer.buttons['camera_reset'].width,100)
            controls=[app.renderer.buttons[name] for name in ('zoom_out','zoom_in','camera_reset')]
            subtitle=app.renderer.small.render('DAY 11 / VICE-INSPIRED ENGINE / ORIGINAL ANIMATED ART',True,(255,255,255)).get_rect(topleft=(32,72))
            for rect in controls:
                self.assertFalse(rect.colliderect(subtitle))
                self.assertEqual(rect.centery,80)
                self.assertLess(rect.right,874)
            self.assertTrue(all(a.right<b.left for a,b in zip(controls,controls[1:])))
        finally:app.close()

    def test_small_left_click_still_selects_and_focus_cancel_does_not(self):
        app=App(True,False)
        try:
            app.renderer.draw(app)
            sq=notation_to_sq('e2');point=project(4,1,flipped=app.flipped)
            app.pointer_down(point)
            self.assertIsNone(app.selected)
            app.pointer_up((point[0]+1,point[1]+1))
            self.assertEqual(app.selected,sq)
            self.assertEqual(app.yaw,0)
            app.selected=None;app.pointer_down(point);app.pointer_cancel();app.pointer_up(point)
            self.assertIsNone(app.selected)
        finally:app.close()

    def test_2d_top_rank_not_clipped(self):
        app=App(True,False)
        try:
            app.view='2d'
            image=app.renderer.draw(app)
            # Inside the top square but above the old y=115 clipping boundary.
            point=(190,100)
            self.assertNotEqual(tuple(image.get_at(point)[:3]),(21,28,42))
            for flipped in (True,False):
                app.flipped=flipped;app.renderer.draw(app)
                for sq in range(64):
                    for poly_point in __import__('graphics').cell_polygon(sq,flipped,'2d'):
                        self.assertGreaterEqual(poly_point[1],90)
                        self.assertLessEqual(poly_point[1],743)
        finally:app.close()

    def test_sound_palette_has_distinct_samples(self):
        sounds=Sounds(False)
        keys=[style[2] for style in STYLES.values()]
        keys+=['move_'+kind for kind in 'pnbrqk']
        self.assertTrue(sounds.available)
        samples=[sounds.effects[key].get_raw() for key in keys]
        self.assertEqual(len(set(samples)),len(keys))
        for key in keys:sounds.play(key)


if __name__=='__main__':unittest.main()
