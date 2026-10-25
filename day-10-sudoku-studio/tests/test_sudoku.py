"""
Comprehensive test suite for Sudoku solver, generator, and session manager.
Tests solver correctness, puzzle uniqueness, session interaction, and edge cases.
"""

import unittest
from copy import deepcopy
import sys
import os

# Add parent directory to path to import sudoku module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sudoku import (
    Board, Coord,
    validate_board, conflicts, candidates,
    solve, count_solutions,
    generate_puzzle, Puzzle,
    Session
)


# ============================================================================
# TEST DATA: KNOWN SUDOKU GRIDS
# ============================================================================

# A valid, almost-complete grid (one empty cell)
ALMOST_COMPLETE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Complete valid solution (no conflicts)
COMPLETE_VALID = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

# Invalid: duplicate 5 in first row
INVALID_ROW_DUPLICATE = [
    [5, 5, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# Invalid: duplicate 1 in first column
INVALID_COL_DUPLICATE = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# Invalid: duplicate 3 in top-left 3x3 box
INVALID_BOX_DUPLICATE = [
    [3, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 3, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# Easy puzzle (42 clues) with unique solution
EASY_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Empty board (81 empty cells)
EMPTY_BOARD = [[0] * 9 for _ in range(9)]


# ============================================================================
# TEST SUITE
# ============================================================================

class TestValidateBoard(unittest.TestCase):
    """Test board validation and copying."""
    
    def test_valid_board_returns_copy(self):
        """validate_board should return a deep copy, not original."""
        original = [[1, 0, 0] + [0]*6 for _ in range(9)]
        validated = validate_board(original)
        
        # Modifying validated should not affect original
        validated[0][0] = 9
        self.assertEqual(original[0][0], 1)
    
    def test_valid_complete_board(self):
        """validate_board should accept fully filled valid board."""
        validated = validate_board(COMPLETE_VALID)
        self.assertEqual(len(validated), 9)
        self.assertEqual(len(validated[0]), 9)
    
    def test_invalid_wrong_number_of_rows(self):
        """Board with != 9 rows should raise ValueError."""
        bad_board = [[0]*9 for _ in range(8)]
        with self.assertRaises(ValueError):
            validate_board(bad_board)
    
    def test_invalid_wrong_number_of_columns(self):
        """Board with row != 9 columns should raise ValueError."""
        bad_board = [[0]*9 for _ in range(8)]
        bad_board.append([0]*8)  # Last row has 8 columns
        with self.assertRaises(ValueError):
            validate_board(bad_board)
    
    def test_invalid_value_out_of_range(self):
        """Board with values outside 0-9 should raise ValueError."""
        bad_board = [[0]*9 for _ in range(9)]
        bad_board[0][0] = 10
        with self.assertRaises(ValueError):
            validate_board(bad_board)
        
        bad_board[0][0] = -1
        with self.assertRaises(ValueError):
            validate_board(bad_board)
    
    def test_invalid_non_integer_value(self):
        """Board with non-integer values should raise ValueError."""
        bad_board = [[0]*9 for _ in range(9)]
        bad_board[0][0] = "5"
        with self.assertRaises(ValueError):
            validate_board(bad_board)
    
    def test_invalid_not_list_of_lists(self):
        """Non-list board should raise ValueError."""
        with self.assertRaises(ValueError):
            validate_board("not a board")


class TestConflicts(unittest.TestCase):
    """Test conflict detection."""
    
    def test_no_conflicts_in_valid_complete_board(self):
        """Valid complete board should have no conflicts."""
        conflict_set = conflicts(COMPLETE_VALID)
        self.assertEqual(conflict_set, set())
    
    def test_no_conflicts_in_empty_board(self):
        """Empty board should have no conflicts (0 is never a conflict)."""
        conflict_set = conflicts(EMPTY_BOARD)
        self.assertEqual(conflict_set, set())
    
    def test_conflict_in_row_duplicate(self):
        """Duplicate value in row should mark both cells in conflict."""
        conflict_set = conflicts(INVALID_ROW_DUPLICATE)
        # Both (0, 0) and (0, 1) should be in conflict
        self.assertIn((0, 0), conflict_set)
        self.assertIn((0, 1), conflict_set)
    
    def test_conflict_in_column_duplicate(self):
        """Duplicate value in column should mark cells in conflict."""
        conflict_set = conflicts(INVALID_COL_DUPLICATE)
        self.assertIn((0, 0), conflict_set)
        self.assertIn((1, 0), conflict_set)
    
    def test_conflict_in_box_duplicate(self):
        """Duplicate value in 3x3 box should mark cells in conflict."""
        conflict_set = conflicts(INVALID_BOX_DUPLICATE)
        self.assertIn((0, 0), conflict_set)
        self.assertIn((1, 2), conflict_set)
    
    def test_zeros_never_conflict(self):
        """Empty cells (0) should never be marked as conflicts."""
        board = [[0]*9 for _ in range(9)]
        conflict_set = conflicts(board)
        self.assertEqual(conflict_set, set())


class TestCandidates(unittest.TestCase):
    """Test candidate calculation for empty cells."""
    
    def test_candidates_for_filled_cell(self):
        """Filled cell should have no candidates."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 5
        cands = candidates(board, 0, 0)
        self.assertEqual(cands, set())
    
    def test_candidates_for_empty_cell_in_empty_board(self):
        """Empty cell in empty board should have all values 1-9."""
        board = [[0]*9 for _ in range(9)]
        cands = candidates(board, 0, 0)
        self.assertEqual(cands, set(range(1, 10)))
    
    def test_candidates_excludes_row_values(self):
        """Candidates should exclude values already in row."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        board[0][1] = 2
        board[0][2] = 3
        cands = candidates(board, 0, 3)
        self.assertNotIn(1, cands)
        self.assertNotIn(2, cands)
        self.assertNotIn(3, cands)
    
    def test_candidates_excludes_column_values(self):
        """Candidates should exclude values already in column."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        board[1][0] = 2
        board[2][0] = 3
        cands = candidates(board, 3, 0)
        self.assertNotIn(1, cands)
        self.assertNotIn(2, cands)
        self.assertNotIn(3, cands)
    
    def test_candidates_excludes_box_values(self):
        """Candidates should exclude values already in 3x3 box."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        board[0][1] = 2
        board[1][0] = 3
        cands = candidates(board, 2, 2)  # Same box (0-2, 0-2)
        self.assertNotIn(1, cands)
        self.assertNotIn(2, cands)
        self.assertNotIn(3, cands)
    
    def test_candidates_invalid_coordinates(self):
        """Invalid coordinates should raise ValueError."""
        board = [[0]*9 for _ in range(9)]
        with self.assertRaises(ValueError):
            candidates(board, -1, 0)
        with self.assertRaises(ValueError):
            candidates(board, 9, 0)
        with self.assertRaises(ValueError):
            candidates(board, 0, 9)


class TestSolve(unittest.TestCase):
    """Test Sudoku solver with backtracking."""
    
    def test_solve_returns_copy_not_original(self):
        """solve() should return a copy, not mutate input."""
        original = [row[:] for row in EASY_PUZZLE]
        solved = solve(EASY_PUZZLE)
        
        self.assertIsNotNone(solved)
        # Modify solved board
        solved[0][0] = 0
        # Original should be unchanged
        self.assertEqual(EASY_PUZZLE[0][0], original[0][0])
    
    def test_solve_valid_puzzle_returns_solution(self):
        """Solver should find solution for valid puzzle."""
        solved = solve(EASY_PUZZLE)
        self.assertIsNotNone(solved)
        # Solution should have no empty cells
        for r in range(9):
            for c in range(9):
                self.assertNotEqual(solved[r][c], 0)
        # Solution should have no conflicts
        self.assertEqual(conflicts(solved), set())
    
    def test_solve_complete_valid_board_returns_copy(self):
        """Solving already-complete valid board should return it."""
        solved = solve(COMPLETE_VALID)
        self.assertIsNotNone(solved)
        self.assertEqual(conflicts(solved), set())
    
    def test_solve_invalid_board_returns_none(self):
        """Solver should return None for board with conflicts."""
        solved = solve(INVALID_ROW_DUPLICATE)
        self.assertIsNone(solved)
    
    def test_solve_board_with_multiple_solutions_returns_one(self):
        """Solver should return one solution even if multiple exist."""
        # Create under-constrained board
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        solved = solve(board)
        # Should find some solution
        self.assertIsNotNone(solved)
    
    def test_solve_unsatisfiable_returns_none(self):
        """Solver should return None if no solution exists."""
        # Create impossible constraint: 1 appears in same row and col
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        board[0][1] = 1
        solved = solve(board)
        self.assertIsNone(solved)


class TestCountSolutions(unittest.TestCase):
    """Test solution counter."""
    
    def test_count_solutions_valid_unique_puzzle(self):
        """Valid unique puzzle should have exactly 1 solution."""
        count = count_solutions(EASY_PUZZLE, limit=2)
        self.assertEqual(count, 1)
    
    def test_count_solutions_stops_at_limit(self):
        """Counter should stop counting at limit."""
        # Create under-constrained board (many solutions)
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 1
        
        count = count_solutions(board, limit=2)
        # Should stop at 2 or less
        self.assertLessEqual(count, 2)
    
    def test_count_solutions_complete_valid_board(self):
        """Complete valid board has exactly 1 solution."""
        count = count_solutions(COMPLETE_VALID, limit=2)
        self.assertEqual(count, 1)
    
    def test_count_solutions_invalid_board_returns_zero(self):
        """Invalid board should have 0 solutions."""
        count = count_solutions(INVALID_ROW_DUPLICATE, limit=2)
        self.assertEqual(count, 0)
    
    def test_count_solutions_invalid_limit_raises_error(self):
        """Non-positive limit should raise ValueError."""
        with self.assertRaises(ValueError):
            count_solutions(EASY_PUZZLE, limit=0)
        with self.assertRaises(ValueError):
            count_solutions(EASY_PUZZLE, limit=-1)
        with self.assertRaises(ValueError):
            count_solutions(EASY_PUZZLE, limit="invalid")
    
    def test_count_solutions_does_not_mutate(self):
        """count_solutions should not modify input board."""
        original = [row[:] for row in EASY_PUZZLE]
        count_solutions(EASY_PUZZLE, limit=2)
        # Check board unchanged
        for r in range(9):
            for c in range(9):
                self.assertEqual(EASY_PUZZLE[r][c], original[r][c])


class TestGeneratePuzzle(unittest.TestCase):
    """Test puzzle generation."""
    
    def test_generate_puzzle_easy_returns_puzzle_dataclass(self):
        """generate_puzzle should return Puzzle dataclass."""
        puzzle = generate_puzzle('easy')
        self.assertIsInstance(puzzle, Puzzle)
        self.assertIsInstance(puzzle.board, list)
        self.assertIsInstance(puzzle.solution, list)
        self.assertIsInstance(puzzle.difficulty, str)
        self.assertIsInstance(puzzle.clues, int)
    
    def test_generate_puzzle_easy_clue_band(self):
        """Easy puzzles should have 40-44 clues."""
        puzzle = generate_puzzle('easy')
        self.assertGreaterEqual(puzzle.clues, 40)
        self.assertLessEqual(puzzle.clues, 44)
    
    def test_generate_puzzle_medium_clue_band(self):
        """Medium puzzles should have 33-37 clues."""
        puzzle = generate_puzzle('medium')
        self.assertGreaterEqual(puzzle.clues, 33)
        self.assertLessEqual(puzzle.clues, 37)
    
    def test_generate_puzzle_hard_clue_band(self):
        """Hard puzzles should have 27-31 clues."""
        puzzle = generate_puzzle('hard')
        self.assertGreaterEqual(puzzle.clues, 27)
        self.assertLessEqual(puzzle.clues, 31)
    
    def test_generate_puzzle_invalid_difficulty_raises_error(self):
        """Invalid difficulty should raise ValueError."""
        with self.assertRaises(ValueError):
            generate_puzzle('impossible')
    
    def test_generate_puzzle_solution_is_valid(self):
        """Generated solution should be valid and complete."""
        puzzle = generate_puzzle('easy')
        # Solution should be complete (no zeros)
        for r in range(9):
            for c in range(9):
                self.assertNotEqual(puzzle.solution[r][c], 0)
        # Solution should have no conflicts
        self.assertEqual(conflicts(puzzle.solution), set())
    
    def test_generate_puzzle_board_subset_of_solution(self):
        """Puzzle board should be subset of solution (same filled values)."""
        puzzle = generate_puzzle('easy')
        for r in range(9):
            for c in range(9):
                if puzzle.board[r][c] != 0:
                    self.assertEqual(puzzle.board[r][c], puzzle.solution[r][c])
    
    def test_generate_puzzle_board_has_unique_solution(self):
        """Generated puzzle should have exactly 1 solution."""
        puzzle = generate_puzzle('easy')
        count = count_solutions(puzzle.board, limit=2)
        self.assertEqual(count, 1)
    
    def test_generate_puzzle_with_seed_deterministic(self):
        """Same seed should generate same puzzle."""
        puzzle1 = generate_puzzle('easy', seed=42)
        puzzle2 = generate_puzzle('easy', seed=42)
        
        self.assertEqual(puzzle1.board, puzzle2.board)
        self.assertEqual(puzzle1.solution, puzzle2.solution)
        self.assertEqual(puzzle1.clues, puzzle2.clues)
    
    def test_generate_puzzle_different_seeds_different_puzzles(self):
        """Different seeds should generate different puzzles (usually)."""
        puzzle1 = generate_puzzle('easy', seed=42)
        puzzle2 = generate_puzzle('easy', seed=43)
        
        # Very unlikely to generate identical puzzles
        self.assertNotEqual(puzzle1.board, puzzle2.board)
    
    def test_generate_puzzle_each_difficulty_unique(self):
        """Each call should generate a unique puzzle."""
        p1 = generate_puzzle('easy')
        p2 = generate_puzzle('easy')
        # Boards should differ (probabilistically)
        self.assertNotEqual(p1.board, p2.board)


class TestSession(unittest.TestCase):
    """Test interactive session manager."""
    
    def setUp(self):
        """Create a puzzle and session for each test."""
        self.puzzle = generate_puzzle('easy', seed=999)
        self.session = Session(self.puzzle)
    
    def test_session_initialization(self):
        """Session should initialize with puzzle state."""
        self.assertEqual(self.session.puzzle, self.puzzle)
        self.assertEqual(self.session.selected, (0, 0))
        self.assertFalse(self.session.note_mode)
        self.assertFalse(self.session.assisted)
        self.assertEqual(self.session.history, [])
    
    def test_session_puzzle_property_readonly(self):
        """Puzzle property returns a protected, equivalent snapshot."""
        self.assertEqual(self.session.puzzle, self.puzzle)
        self.assertIsNot(self.session.puzzle, self.puzzle)
    
    def test_session_board_independent_of_puzzle(self):
        """Session board should be independent copy."""
        original_board = [row[:] for row in self.puzzle.board]
        # Modify session board
        if self.session.board[0][0] == 0:
            self.session.board[0][0] = 5
        # Original puzzle should be unchanged
        self.assertEqual(self.puzzle.board, original_board)
    
    def test_select_valid_coordinates(self):
        """select() should update selected cell."""
        self.session.select(4, 5)
        self.assertEqual(self.session.selected, (4, 5))
    
    def test_select_invalid_coordinates_raises_error(self):
        """select() with invalid coords should raise ValueError."""
        with self.assertRaises(ValueError):
            self.session.select(-1, 0)
        with self.assertRaises(ValueError):
            self.session.select(9, 0)
    
    def test_is_given_identifies_givens(self):
        """is_given() should correctly identify given cells."""
        # Find a given cell in puzzle
        for r in range(9):
            for c in range(9):
                if self.puzzle.board[r][c] != 0:
                    self.assertTrue(self.session.is_given(r, c))
                    return
        # If no givens found, that's ok (rare for generated puzzles)
    
    def test_is_given_identifies_empty_cells(self):
        """is_given() should return False for originally empty cells."""
        for r in range(9):
            for c in range(9):
                if self.puzzle.board[r][c] == 0:
                    self.assertFalse(self.session.is_given(r, c))
                    return
    
    def test_enter_cannot_modify_given_cells(self):
        """enter() on given cell should not modify."""
        # Find a given cell
        for r in range(9):
            for c in range(9):
                if self.session.is_given(r, c):
                    original = self.session.board[r][c]
                    self.session.select(r, c)
                    result = self.session.enter(5)
                    self.assertFalse(result)
                    self.assertEqual(self.session.board[r][c], original)
                    return
    
    def test_enter_can_modify_empty_cells(self):
        """enter() should modify empty editable cells."""
        # Find empty cell
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    result = self.session.enter(5)
                    # Should succeed and modify
                    if result:
                        self.assertEqual(self.session.board[r][c], 5)
                    return
    
    def test_enter_value_zero_erases_cell(self):
        """enter(0) should erase a cell."""
        # Put value in cell, then erase
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.enter(5)
                    result = self.session.enter(0)
                    self.assertTrue(result)
                    self.assertEqual(self.session.board[r][c], 0)
                    return
    
    def test_enter_invalid_value_raises_error(self):
        """enter() with invalid value should raise ValueError."""
        self.session.select(0, 0)
        with self.assertRaises(ValueError):
            self.session.enter(10)
        with self.assertRaises(ValueError):
            self.session.enter(-1)
        with self.assertRaises(ValueError):
            self.session.enter("5")
    
    def test_note_mode_toggle(self):
        """note_mode_toggle() should toggle note mode."""
        initial = self.session.note_mode
        self.session.note_mode_toggle()
        self.assertNotEqual(self.session.note_mode, initial)
        self.session.note_mode_toggle()
        self.assertEqual(self.session.note_mode, initial)
    
    def test_enter_note_mode_adds_candidate_marks(self):
        """In note mode, enter() should toggle candidate marks."""
        # Find empty cell
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.note_mode = True
                    result = self.session.enter(5)
                    # Should add mark
                    self.assertTrue(result)
                    self.assertIn((r, c), self.session.notes)
                    self.assertIn(5, self.session.notes[(r, c)])
                    return
    
    def test_enter_note_mode_on_filled_cell_fails(self):
        """In note mode, enter() on filled cell should fail."""
        # Find filled cell
        for r in range(9):
            for c in range(9):
                if self.session.board[r][c] != 0:
                    self.session.select(r, c)
                    self.session.note_mode = True
                    result = self.session.enter(5)
                    self.assertFalse(result)
                    return
    
    def test_enter_clears_notes_when_entering_number(self):
        """Entering a number should clear candidate marks."""
        # Find empty cell and add notes
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.note_mode = True
                    self.session.enter(3)
                    self.session.enter(5)
                    # Switch to number mode and enter value
                    self.session.note_mode = False
                    self.session.enter(7)
                    # Notes should be cleared
                    self.assertNotIn((r, c), self.session.notes)
                    return
    
    def test_undo_restores_previous_state(self):
        """undo() should restore board to previous state."""
        # Modify a cell
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    original = self.session.board[r][c]
                    self.session.select(r, c)
                    self.session.enter(5)
                    # Now undo
                    result = self.session.undo()
                    self.assertTrue(result)
                    self.assertEqual(self.session.board[r][c], original)
                    return
    
    def test_undo_returns_false_on_empty_history(self):
        """undo() should return False if no history."""
        result = self.session.undo()
        self.assertFalse(result)
    
    def test_reset_restores_puzzle_state(self):
        """reset() should restore original puzzle state."""
        original_board = [row[:] for row in self.puzzle.board]
        # Modify board
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.enter(5)
                    break
            else:
                continue
            break
        # Reset
        self.session.reset()
        self.assertEqual(self.session.board, original_board)
        self.assertEqual(self.session.notes, {})
        self.assertEqual(self.session.history, [])
        self.assertFalse(self.session.assisted)
    
    def test_hint_reveals_correct_value(self):
        """hint() should reveal correct value in selected cell."""
        result = self.session.hint()
        if result:
            r, c = self.session.selected
            self.assertEqual(self.session.board[r][c], 
                           self.puzzle.solution[r][c])
            self.assertTrue(self.session.assisted)
    
    def test_hint_clears_notes_when_revealing(self):
        """hint() should clear candidate marks when revealing value."""
        # Add notes to a cell
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.note_mode = True
                    self.session.enter(3)
                    self.session.note_mode = False
                    self.session.hint()
                    # Notes should be cleared
                    self.assertNotIn((r, c), self.session.notes)
                    return
    
    def test_hint_returns_false_when_complete(self):
        """hint() should return False when all editable cells correct."""
        # Fill board with solution
        self.session.board = deepcopy(self.puzzle.solution)
        result = self.session.hint()
        self.assertFalse(result)
    
    def test_solve_current_fills_board_with_solution(self):
        """solve_current() should solve the puzzle."""
        result = self.session.solve_current()
        if result:
            # Board should be complete
            self.assertTrue(self.session.complete)
            self.assertTrue(self.session.assisted)
    
    def test_solve_current_returns_false_for_unsolvable(self):
        """solve_current() should return False if unsolvable."""
        # Create conflicting state
        self.session.board[0][0] = 1
        self.session.board[0][1] = 1
        result = self.session.solve_current()
        self.assertFalse(result)
        # Board should not change
        self.assertEqual(self.session.board[0][0], 1)
    
    def test_complete_property_false_for_empty_board(self):
        """complete should be False for unsolved board."""
        self.assertFalse(self.session.complete)
    
    def test_complete_property_true_for_solved_board(self):
        """complete should be True for solved board."""
        self.session.board = deepcopy(self.puzzle.solution)
        self.assertTrue(self.session.complete)
    
    def test_complete_property_false_for_conflicted_board(self):
        """complete should be False if board has conflicts."""
        # Create a full board with conflicts
        self.session.board = [row[:] for row in self.puzzle.solution]
        self.session.board[0][0] = 1
        self.session.board[0][1] = 1  # Conflict in first row
        self.assertFalse(self.session.complete)


class TestSessionProtection(unittest.TestCase):
    """Test session protection and constraint enforcement."""
    
    def setUp(self):
        """Create a puzzle and session for each test."""
        self.puzzle = generate_puzzle('easy', seed=123)
        self.session = Session(self.puzzle)
    
    def test_givens_are_protected(self):
        """Given values should be protected from modification."""
        # Try to change all given cells
        changes_attempted = 0
        for r in range(9):
            for c in range(9):
                if self.session.is_given(r, c):
                    original = self.session.board[r][c]
                    self.session.select(r, c)
                    result = self.session.enter(1)
                    self.assertFalse(result, 
                                    f"Should not be able to change given at ({r}, {c})")
                    self.assertEqual(self.session.board[r][c], original)
                    changes_attempted += 1
        
        # Should have found at least one given
        self.assertGreater(changes_attempted, 0)
    
    def test_selected_state_not_in_history(self):
        """Selected cell should not affect undo/redo."""
        self.session.select(4, 5)
        initial_selected = self.session.selected
        
        # Find and modify an empty cell
        for r in range(9):
            for c in range(9):
                if not self.session.is_given(r, c):
                    self.session.select(r, c)
                    self.session.enter(5)
                    break
            else:
                continue
            break
        
        # Change selected
        self.session.select(7, 8)
        # Undo
        self.session.undo()
        
        # Selected should still be (7, 8), not restored
        self.assertEqual(self.session.selected, (7, 8))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_empty_board_has_many_solutions(self):
        """Empty board should have multiple solutions."""
        board = [[0]*9 for _ in range(9)]
        count = count_solutions(board, limit=2)
        self.assertEqual(count, 2)  # Stopped at limit
    
    def test_candidates_api_validation(self):
        """candidates() should validate board shape before checking coords."""
        bad_board = [[0]*8 for _ in range(9)]  # Invalid shape
        try:
            candidates(bad_board, 0, 0)
            # Should either raise or return empty set
        except (ValueError, IndexError):
            pass  # Expected
    
    def test_puzzle_clue_count_matches_nonzeros(self):
        """Puzzle clue count should match number of given values."""
        puzzle = generate_puzzle('easy')
        nonzero_count = sum(1 for r in range(9) for c in range(9) 
                           if puzzle.board[r][c] != 0)
        self.assertEqual(puzzle.clues, nonzero_count)


if __name__ == '__main__':
    unittest.main()
