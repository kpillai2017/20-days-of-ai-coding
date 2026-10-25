"""
Sudoku solver, puzzle generator, and interactive session manager.
Pure stdlib Python 3.9+ using unittest and standard libraries only.
"""

from dataclasses import dataclass, field as dc_field
from typing import Optional, Set, Tuple, Dict, List
from copy import deepcopy
import random


# ============================================================================
# TYPE DEFINITIONS AND CONSTANTS
# ============================================================================

# Board: 9x9 grid of ints 0-9, where 0 = empty, 1-9 = given/filled
Board = List[List[int]]

# Coordinates: (row, col) tuples
Coord = Tuple[int, int]


# ============================================================================
# VALIDATION AND BASIC BOARD OPERATIONS
# ============================================================================

def validate_board(board: Board) -> Board:
    """
    Validate board shape and values, return independent deep copy.
    
    Raises ValueError if:
      - Board is not 9x9
      - Any value is not an int in range 0-9
    
    Returns: Deep copy of validated board (caller cannot affect original)
    
    Note: Does NOT check for conflicts (duplicate values in rows/cols/boxes).
          Use conflicts() for that.
    """
    # Check board is list of lists
    if not isinstance(board, list) or len(board) != 9:
        raise ValueError("Board must be a list of 9 rows")
    
    for row_idx, row in enumerate(board):
        # Each row must be a list/sequence of exactly 9 elements
        if not isinstance(row, (list, tuple)) or len(row) != 9:
            raise ValueError(f"Row {row_idx} must have exactly 9 columns")
        
        # Each element must be an int 0-9
        for col_idx, val in enumerate(row):
            if type(val) is not int or val < 0 or val > 9:
                raise ValueError(
                    f"Invalid value {val} at ({row_idx}, {col_idx}): "
                    f"must be int 0-9"
                )
    
    # Return a deep copy so caller's changes don't affect our copy
    return [list(row) for row in board]


def conflicts(board: Board) -> Set[Coord]:
    """
    Return set of (row, col) coordinates for every nonzero cell that is
    in a duplicate row, column, or 3x3 box.
    
    A cell is "in conflict" if:
      - Its value appears elsewhere in same row, OR
      - Its value appears elsewhere in same column, OR
      - Its value appears elsewhere in same 3x3 box
    
    Empty cells (0) are never in conflict.
    Returns empty set if board is valid/conflict-free.
    """
    board = validate_board(board)
    conflict_cells: Set[Coord] = set()
    
    # Check each cell
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            # Skip empty cells
            if val == 0:
                continue
            
            # Check if this value appears elsewhere in its row
            for c2 in range(9):
                if c2 != c and board[r][c2] == val:
                    conflict_cells.add((r, c))
                    break
            
            # Check if this value appears elsewhere in its column
            for r2 in range(9):
                if r2 != r and board[r2][c] == val:
                    conflict_cells.add((r, c))
                    break
            
            # Check if this value appears elsewhere in its 3x3 box
            box_r, box_c = (r // 3) * 3, (c // 3) * 3
            for br in range(box_r, box_r + 3):
                for bc in range(box_c, box_c + 3):
                    if (br, bc) != (r, c) and board[br][bc] == val:
                        conflict_cells.add((r, c))
                        break
    
    return conflict_cells


def candidates(board: Board, row: int, col: int) -> Set[int]:
    """
    Return set of possible values (1-9) that can be placed in an empty cell.
    
    For empty cells (board[row][col] == 0):
      - Return set of ints 1-9 that don't appear in same row, col, or box
    
    For filled cells (nonzero):
      - Return empty set (no candidates)
    
    Raises ValueError if:
      - Coordinates are out of bounds (0-8)
      - board is invalid shape
    """
    # Validate coordinates
    if type(row) is not int or type(col) is not int or not (0 <= row < 9 and 0 <= col < 9):
        raise ValueError(f"Coordinates ({row}, {col}) out of bounds [0-8]")
    
    board = validate_board(board)
    return _candidates(board, row, col)


def _candidates(board: Board, row: int, col: int) -> Set[int]:
    """Internal hot path: callers already validated their working board."""
    # If cell is filled, no candidates
    if board[row][col] != 0:
        return set()
    
    # Start with all possible values 1-9
    possible = set(range(1, 10))
    
    # Remove values already in row
    for c in range(9):
        possible.discard(board[row][c])
    
    # Remove values already in column
    for r in range(9):
        possible.discard(board[r][col])
    
    # Remove values already in 3x3 box
    box_r, box_c = (row // 3) * 3, (col // 3) * 3
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            possible.discard(board[r][c])
    
    return possible


# ============================================================================
# SOLVING ENGINE: BACKTRACKING WITH MRV HEURISTIC
# ============================================================================

def solve(board: Board) -> Optional[Board]:
    """
    Solve a Sudoku puzzle using backtracking with Minimum Remaining Values
    (MRV) heuristic for efficient search.
    
    Args:
        board: 9x9 grid with 0 for empty cells, 1-9 for given values
    
    Returns:
        - Deep copy of solved board if solution exists
        - None if no solution exists (unsatisfiable)
    
    Does NOT mutate the input board.
    """
    # Validate and create working copy
    try:
        working_board = validate_board(board)
    except ValueError:
        return None
    
    # Check for conflicts in initial state
    if conflicts(working_board):
        return None
    
    # Recursive backtracking solver
    def backtrack() -> bool:
        """Try to fill remaining empty cells. Returns True if solved."""
        
        # Find empty cell with minimum remaining values (MRV heuristic)
        min_candidates = None
        best_cell = None
        
        for r in range(9):
            for c in range(9):
                if working_board[r][c] == 0:
                    cands = _candidates(working_board, r, c)
                    # If any cell has zero candidates, board is unsolvable
                    if not cands:
                        return False
                    # Track cell with minimum candidates (MRV heuristic)
                    if min_candidates is None or len(cands) < len(min_candidates):
                        min_candidates = cands
                        best_cell = (r, c)
        
        # No empty cells found = solved!
        if best_cell is None:
            return True
        
        r, c = best_cell
        # Try each candidate value for this cell
        for value in sorted(min_candidates):
            working_board[r][c] = value
            
            if backtrack():
                return True
            
            # Backtrack: undo this choice
            working_board[r][c] = 0
        
        return False
    
    # Attempt to solve
    if backtrack():
        return working_board
    else:
        return None


def count_solutions(board: Board, limit: int = 2) -> int:
    """
    Count the number of solutions to a puzzle, stopping at 'limit'.
    
    Args:
        board: 9x9 grid with 0 for empty cells
        limit: Stop counting after reaching this many solutions (must be > 0)
    
    Returns:
        Number of distinct solutions found (0 to limit)
    
    Raises:
        ValueError if limit is not a positive int
    
    Does NOT mutate the input board.
    Useful for verifying puzzle uniqueness (limit=2 means unique if == 1).
    """
    # Validate limit
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit must be a positive integer")
    
    # Validate and create working copy
    try:
        working_board = validate_board(board)
    except ValueError:
        return 0
    
    # Check for initial conflicts
    if conflicts(working_board):
        return 0
    
    # Counter for solutions found
    solution_count = [0]  # Use list to allow modification in nested function
    
    def backtrack() -> None:
        """Recursively count solutions without storing them."""
        
        # Early exit if we've found enough solutions
        if solution_count[0] >= limit:
            return
        
        # Find empty cell with MRV heuristic
        min_candidates = None
        best_cell = None
        
        for r in range(9):
            for c in range(9):
                if working_board[r][c] == 0:
                    cands = _candidates(working_board, r, c)
                    if not cands:
                        return  # Dead end
                    if min_candidates is None or len(cands) < len(min_candidates):
                        min_candidates = cands
                        best_cell = (r, c)
        
        # No empty cells = found a complete solution
        if best_cell is None:
            solution_count[0] += 1
            return
        
        r, c = best_cell
        # Try each candidate
        for value in sorted(min_candidates):
            working_board[r][c] = value
            backtrack()
            working_board[r][c] = 0
    
    backtrack()
    return solution_count[0]


# ============================================================================
# PUZZLE GENERATION
# ============================================================================

@dataclass
class Puzzle:
    """
    A generated Sudoku puzzle with complete solution.
    
    Fields:
        board: 9x9 grid with clues (given values), 0 for empty
        solution: 9x9 grid with complete solved puzzle
        difficulty: 'easy', 'medium', or 'hard'
        clues: number of given values in board
    """
    board: Board
    solution: Board
    difficulty: str
    clues: int


def generate_puzzle(
    difficulty: str = 'easy',
    seed: Optional[int] = None
) -> Puzzle:
    """
    Generate a unique Sudoku puzzle at specified difficulty level.
    
    Args:
        difficulty: 'easy' (40-44 clues), 'medium' (33-37), or 'hard' (27-31)
        seed: Optional random seed for deterministic generation
    
    Returns:
        Puzzle dataclass with board, solution, difficulty, and clue count
    
    Raises:
        ValueError if difficulty not recognized
        RuntimeError if cannot generate puzzle in target band after 12 retries
    
    Difficulty bands are defined by clue count only, not logical rating.
    Uses randomized backtracking to generate solution, then greedily removes
    clues while maintaining unique solution.
    """
    # Validate and normalize difficulty
    if not isinstance(difficulty, str):
        raise ValueError("difficulty must be easy, medium or hard")
    difficulty = difficulty.lower()
    if difficulty == 'easy':
        target_clues = 42  # Acceptable: 40-44
        clue_band = (40, 44)
    elif difficulty == 'medium':
        target_clues = 35  # Acceptable: 33-37
        clue_band = (33, 37)
    elif difficulty == 'hard':
        target_clues = 29  # Acceptable: 27-31
        clue_band = (27, 31)
    else:
        raise ValueError(
            f"difficulty must be 'easy', 'medium', or 'hard', got '{difficulty}'"
        )
    
    # A private RNG keeps generation deterministic without changing global random.
    rng = random.Random(seed)
    
    # Generate puzzle with retry limit
    for attempt in range(12):
        # Generate a complete solution using randomized backtracking
        solution = _generate_solution(rng)
        
        # Create puzzle by removing clues greedily
        puzzle_board = [row[:] for row in solution]  # Start with full solution
        clue_count = 81
        
        # Collect all cell positions and shuffle
        cells = [(r, c) for r in range(9) for c in range(9)]
        rng.shuffle(cells)
        
        # Try to remove each clue while keeping unique solution
        for r, c in cells:
            removed_value = puzzle_board[r][c]
            puzzle_board[r][c] = 0
            clue_count -= 1
            
            # Check if still uniquely solvable
            if count_solutions(puzzle_board, limit=2) != 1:
                # Removing this clue breaks uniqueness, restore it
                puzzle_board[r][c] = removed_value
                clue_count += 1
            
            # Stop if we've reached target clues
            if clue_count <= target_clues:
                break
        
        # Check if final clue count is in acceptable band
        if clue_band[0] <= clue_count <= clue_band[1]:
            return Puzzle(
                board=puzzle_board,
                solution=solution,
                difficulty=difficulty,
                clues=clue_count
            )
    
    # Failed to hit band after retries
    raise RuntimeError(
        f"Could not generate {difficulty} puzzle in band "
        f"{clue_band[0]}-{clue_band[1]} after 12 attempts"
    )


def _generate_solution(rng) -> Board:
    """
    Generate a random complete valid Sudoku solution.
    Uses randomized backtracking to create diversity.
    Internal helper for generate_puzzle.
    """
    board = [[0] * 9 for _ in range(9)]
    
    def backtrack() -> bool:
        """Fill board with random valid placement using backtracking."""
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    # Get possible values and shuffle for randomness
                    cands = list(_candidates(board, r, c))
                    rng.shuffle(cands)
                    
                    for val in cands:
                        board[r][c] = val
                        if backtrack():
                            return True
                        board[r][c] = 0
                    
                    return False
        
        return True  # All cells filled
    
    backtrack()
    return board


# ============================================================================
# INTERACTIVE SESSION MANAGER
# ============================================================================

@dataclass
class Session:
    """
    Interactive Sudoku session for solving puzzles with undo/hint support.
    
    Attributes:
        puzzle (property): The original Puzzle object
        board: Working copy of puzzle board (can be modified)
        notes: Dict mapping (r,c) to set of candidate marks (for empty cells)
        selected: (row, col) of currently selected cell, default (0, 0)
        note_mode: bool, if True enter() adds/removes candidate marks
        assisted: bool, True if solve_current() or hint() was used
        history: Stack of board/notes/assisted states for undo
        _puzzle: The original Puzzle (backing for puzzle property)
        _givens: Set of (r, c) with original given values (immutable)
    """
    _puzzle: Puzzle = dc_field(default=None)
    board: Board = dc_field(default_factory=lambda: [[0]*9 for _ in range(9)])
    notes: Dict[Coord, Set[int]] = dc_field(default_factory=dict)
    selected: Coord = dc_field(default=(0, 0))
    note_mode: bool = dc_field(default=False)
    assisted: bool = dc_field(default=False)
    history: List[Tuple[Board, Dict, bool]] = dc_field(default_factory=list)
    _givens: Set[Coord] = dc_field(default_factory=set)
    
    def __init__(self, puzzle: Puzzle):
        """Initialize session from a Puzzle."""
        self._puzzle = deepcopy(puzzle)
        self.board = validate_board(puzzle.board)
        self.notes = {}
        self.selected = (0, 0)
        self.note_mode = False
        self.assisted = False
        self.history = []
        # Record which cells have given values (cannot be changed)
        self._givens = {(r, c) for r in range(9) for c in range(9)
                        if puzzle.board[r][c] != 0}
    
    @property
    def puzzle(self) -> Puzzle:
        """Return the original puzzle (read-only)."""
        return deepcopy(self._puzzle)
    
    def select(self, row: int, col: int) -> None:
        """
        Select a cell by coordinates. Updates selected without history.
        Validates coordinates are in range [0-8].
        """
        if type(row) is not int or type(col) is not int or not (0 <= row < 9 and 0 <= col < 9):
            raise ValueError(f"Coordinates ({row}, {col}) out of bounds")
        self.selected = (row, col)
    
    def is_given(self, row: int, col: int) -> bool:
        """Check if a cell contains a given value (immutable)."""
        if type(row) is not int or type(col) is not int or not (0 <= row < 9 and 0 <= col < 9):
            raise ValueError("Coordinates out of bounds")
        return (row, col) in self._givens
    
    def enter(self, value: int) -> bool:
        """
        Enter a value in the selected cell, or manage candidate marks.
        
        Behavior depends on cell state and note_mode:
        
        If note_mode is False (number entry):
          - If value == 0: Erase the cell (set to 0)
          - If value in 1-9: Place/overwrite value
          - If cell is given (immutable): No change, return False
          - If cell is already filled with same value: No change, return True
          - If new value conflicts: Allow (conflicts are detected, not prevented)
          - If change made: Save history, return True
        
        If note_mode is True (candidate marking):
          - If cell is not empty: Return False (notes only on empty cells)
          - If value in 1-9: Toggle candidate mark (add if not present, remove if present)
          - If value == 0: Clear all marks for this cell
          - If change made: Save history, return True
        
        Returns: True if change was made, False otherwise
        """
        r, c = self.selected
        
        # Validate value
        if type(value) is not int or value < 0 or value > 9:
            raise ValueError(f"Value must be int 0-9, got {value}")
        
        if self.note_mode:
            # Candidate marking mode
            # Only works on empty cells
            if self.board[r][c] != 0:
                return False
            
            cell_key = (r, c)
            if value == 0:
                # Clear all notes
                if cell_key in self.notes:
                    # Save history before change
                    self._save_history()
                    del self.notes[cell_key]
                    return True
                return False
            elif 1 <= value <= 9:
                # Snapshot BEFORE mutation so Undo can restore the old notes.
                self._save_history()
                marks = self.notes.setdefault(cell_key, set())
                if value in marks:
                    marks.remove(value)
                    if not marks:
                        self.notes.pop(cell_key)
                else:
                    marks.add(value)
                return True
        else:
            # Number entry mode
            
            # Cannot modify given cells
            if self.is_given(r, c):
                return False
            
            # If value is 0, erase
            if value == 0:
                if self.board[r][c] != 0:
                    self._save_history()
                    self.board[r][c] = 0
                    # Clear notes for this cell when erased
                    self.notes.pop((r, c), None)
                    return True
                return False
            
            # Place value (1-9)
            if self.board[r][c] != value:
                self._save_history()
                self.board[r][c] = value
                # Clear notes when filling cell
                self.notes.pop((r, c), None)
                return True
            
            return False
    
    def note_mode_toggle(self) -> None:
        """Toggle between number entry and candidate marking modes."""
        self.note_mode = not self.note_mode
    
    def undo(self) -> bool:
        """
        Undo the last action (enter, solve_current, or hint).
        Returns True if undo was successful, False if history is empty.
        """
        if not self.history:
            return False
        
        # Pop and restore previous state (doesn't save current state)
        prev_board, prev_notes, prev_assisted = self.history.pop()
        self.board = prev_board
        self.notes = prev_notes
        self.assisted = prev_assisted
        return True
    
    def reset(self) -> None:
        """
        Reset board to original puzzle state and clear all state.
        - Restores board to original puzzle
        - Clears notes
        - Clears history
        - Resets assisted flag
        - Keeps selected cell (UI state, not part of puzzle state)
        """
        self.board = deepcopy(self._puzzle.board)
        self.notes = {}
        self.history = []
        self.assisted = False
    
    def hint(self) -> bool:
        """
        Reveal the correct value in the selected cell if it's editable,
        or find and reveal the first editable blank/wrong cell (row-major).
        
        Behavior:
        - If selected cell is editable (not given) and empty or wrong:
          Reveal correct value from solution into selected cell
        - Otherwise: Find first empty/wrong editable cell in row-major order,
          reveal its correct value
        - Clears candidate marks in revealed cell
        - Sets assisted = True
        - Saves to history for undo
        
        Returns: True if a hint was revealed, False if no editable cell found
        """
        r, c = self.selected
        
        # Check if selected cell is editable and needs help
        if not self.is_given(r, c):
            correct_val = self._puzzle.solution[r][c]
            # If selected is empty or has wrong value
            if self.board[r][c] != correct_val:
                self._save_history()
                self.board[r][c] = correct_val
                self.notes.pop((r, c), None)
                self.assisted = True
                return True
        
        # Find first editable empty/wrong cell in row-major order
        for row in range(9):
            for col in range(9):
                if not self.is_given(row, col):
                    correct_val = self._puzzle.solution[row][col]
                    if self.board[row][col] != correct_val:
                        self._save_history()
                        self.board[row][col] = correct_val
                        self.notes.pop((row, col), None)
                        self.assisted = True
                        return True
        
        return False
    
    def solve_current(self) -> bool:
        """
        Attempt to solve the current board state using the solver.
        
        Behavior:
        - Uses solve() on current board to find complete solution
        - If solvable: Replaces board with solution, sets assisted=True
        - If unsolvable (conflicts): No change to board, return False
        - Clears all candidate marks
        - Saves to history for undo
        
        Returns: True if board was solved, False if unsolvable
        
        Note: For a generated puzzle with user-entered values, if those
        entries conflict with the unique solution, solve_current() will
        return False (unsolvable) and board remains unchanged.
        """
        # Attempt to solve current board state
        solved = solve(self.board)
        
        if solved is None:
            # No solution exists (invalid/unsolvable state)
            return False
        
        self.apply_solution(solved)
        return True

    def apply_solution(self, solved: Board) -> None:
        """Apply a background solver result on the main thread, undoably.

        Validate the result rather than trusting every caller to be the solver.
        Filled entries are constraints: never silently overwrite them.
        """
        result = validate_board(solved)
        if any(0 in row for row in result) or conflicts(result):
            raise ValueError("A complete valid solution is required")
        if any(self.board[r][c] and self.board[r][c] != result[r][c]
               for r in range(9) for c in range(9)):
            raise ValueError("Solution must preserve current entries")
        self._save_history()
        self.board = result
        self.notes = {}
        self.assisted = True

    @property
    def complete(self) -> bool:
        """
        Check if puzzle is completely solved with no conflicts.
        Returns True if all cells filled and no duplicates in rows/cols/boxes.
        """
        # Check all cells are filled
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    return False
        
        # Check no conflicts
        return len(conflicts(self.board)) == 0
    
    def _save_history(self) -> None:
        """Internal: Save current state to history stack before making change."""
        # Deep copy board and notes
        saved_board = deepcopy(self.board)
        saved_notes = deepcopy(self.notes)
        saved_assisted = self.assisted
        
        self.history.append((saved_board, saved_notes, saved_assisted))
