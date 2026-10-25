"""Regression tests for boundaries, undo snapshots and headless UI actions."""
import os
from pathlib import Path
import random
import sys
import time
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from sudoku import Session, candidates, conflicts, count_solutions, generate_puzzle, validate_board
from main import App, GRID, main


class Regressions(unittest.TestCase):
    def test_booleans_are_not_digits_or_limits(self):
        board=[[0]*9 for _ in range(9)]
        board[0][0]=True
        with self.assertRaises(ValueError): validate_board(board)
        with self.assertRaises(ValueError): count_solutions([[0]*9 for _ in range(9)],True)

    def test_coordinates_and_shapes(self):
        for coords in [(True,0),(1.2,0),(-1,0),(0,9)]:
            with self.assertRaises(ValueError): candidates([[0]*9 for _ in range(9)],*coords)
        with self.assertRaises(ValueError): candidates([],0,0)
        with self.assertRaises(ValueError): conflicts([])

    def test_generator_does_not_touch_global_rng(self):
        state=random.getstate()
        generate_puzzle('hard',42)
        self.assertEqual(random.getstate(),state)

    def test_multiple_seed_bands_unique_and_preserve_solution(self):
        for difficulty,lo,hi in [('easy',40,44),('medium',33,37),('hard',27,31)]:
            for seed in range(5):
                puzzle=generate_puzzle(difficulty,seed)
                self.assertLessEqual(lo,puzzle.clues)
                self.assertLessEqual(puzzle.clues,hi)
                self.assertEqual(count_solutions(puzzle.board),1)
                self.assertEqual(puzzle.clues,sum(bool(v) for row in puzzle.board for v in row))
                self.assertFalse(conflicts(puzzle.solution))
                for r in range(9):
                    for c in range(9):
                        self.assertIn(puzzle.board[r][c],(0,puzzle.solution[r][c]))

    def test_note_undo_restores_before_change(self):
        session=Session(generate_puzzle(seed=42))
        r,c=next((r,c) for r in range(9) for c in range(9) if not session.is_given(r,c))
        session.select(r,c); session.note_mode=True
        session.enter(3); self.assertEqual(session.notes[(r,c)],{3})
        session.undo(); self.assertEqual(session.notes,{})
        session.enter(3); session.enter(3)
        self.assertNotIn((r,c),session.notes)
        session.undo(); self.assertEqual(session.notes[(r,c)],{3})
        session.enter(0); session.undo(); self.assertEqual(session.notes[(r,c)],{3})

    def test_original_snapshot_protected(self):
        puzzle=generate_puzzle(seed=42)
        session=Session(puzzle)
        before=session.puzzle.board
        puzzle.board[0][0]=0
        snapshot=session.puzzle; snapshot.board[0][0]=9
        self.assertEqual(session.puzzle.board,before)
        session.reset(); self.assertEqual(session.board,before)

    def test_apply_bad_solution_rejected_without_history(self):
        session=Session(generate_puzzle(seed=42))
        with self.assertRaises(ValueError): session.apply_solution([[0]*9 for _ in range(9)])
        self.assertEqual(session.history,[])


class UI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init();pygame.font.init();pygame.display.set_mode((1040,790))
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def wait(self,app):
        end=time.monotonic()+15
        while app.busy and time.monotonic()<end:
            app.poll();time.sleep(.001)
        self.assertFalse(app.busy,'worker did not finish')

    def test_board_workflow_and_custom_solver(self):
        app=App(42)
        try:
            self.wait(app)
            self.assertIsNotNone(app.session)
            image=app.draw();self.assertEqual(image.get_size(),(1040,790))
            r,c=next((r,c) for r in range(9) for c in range(9) if not app.session.is_given(r,c))
            app.click((float(GRID.x+c*70+35),float(GRID.y+r*70+35)))
            self.assertEqual(app.session.selected,(r,c))
            app.action('notes');app.enter(2)
            self.assertEqual(app.session.notes[(r,c)],{2})
            app.action('undo');self.assertEqual(app.session.notes,{})
            app.action('notes');app.action('hint');self.assertTrue(app.session.assisted)
            app.action('undo');self.assertFalse(app.session.assisted)
            app.action('solve');self.wait(app);self.assertTrue(app.session.complete)
            app.action('undo');self.assertFalse(app.session.complete)
            app.action('pause');old=[row[:] for row in app.session.board]
            app.enter(8);self.assertEqual(app.session.board,old)
            app.draw();app.action('pause')
            for level in ('medium','hard'):
                app.action(level);self.wait(app)
                self.assertEqual(app.session.puzzle.difficulty,level)
            app.action('custom');self.assertEqual(app.session.puzzle.clues,0)
            app.enter(1);app.session.select(0,1);app.enter(1)
            app.action('solve');self.wait(app)
            self.assertIn('No solution',app.message)
            self.assertFalse(app.session.complete)
            app.action('reset');app.enter(5)
            app.action('hint');self.assertIn('Custom boards',app.message)
            app.action('solve');self.wait(app);self.assertTrue(app.session.complete)
            self.assertEqual(app.session.board[0][1],5)
            app.draw()
        finally: app.close()

    def test_keyboard_events(self):
        app=App(42)
        try:
            self.wait(app);app.action('custom')
            app.key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_7,unicode='7',mod=0))
            self.assertEqual(app.session.board[0][0],7)
            app.key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT,unicode='',mod=0))
            self.assertEqual(app.session.selected,(0,1))
            app.key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_KP3,unicode='',mod=0))
            self.assertEqual(app.session.board[0][1],3)
        finally:app.close()

    def test_real_loop(self):
        self.assertEqual(main(['--seed','42','--frames','3']),0)
        pygame.display.init();pygame.font.init();pygame.display.set_mode((1040,790))


if __name__=='__main__': unittest.main()
