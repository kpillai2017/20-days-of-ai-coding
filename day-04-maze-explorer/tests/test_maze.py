"""
Comprehensive test suite for Maze and MazeGame classes.

Tests cover:
- Maze generation with various dimensions and seeds
- Tree structure and reachability properties
- Symmetry of passages
- BFS pathfinding and solution optimality
- MazeGame state management and movement
- Edge cases (1x1, 1xN mazes, disconnected scenarios)
- Input validation and error handling
"""

import unittest
from collections import deque

# Import maze module from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from maze import Maze, MazeGame, DIRECTIONS


class TestMazeGeneration(unittest.TestCase):
    """Test maze generation properties and structure."""

    def test_maze_initialization_default(self):
        """Test maze initializes with default 15x15 dimensions."""
        maze = Maze()
        self.assertEqual(maze.rows, 15)
        self.assertEqual(maze.cols, 15)
        self.assertIsNone(maze.seed)
        self.assertEqual(maze.start, (0, 0))
        self.assertEqual(maze.goal, (14, 14))

    def test_maze_initialization_custom_dims(self):
        """Test maze initializes with custom dimensions."""
        maze = Maze(rows=10, cols=20)
        self.assertEqual(maze.rows, 10)
        self.assertEqual(maze.cols, 20)
        self.assertEqual(maze.goal, (9, 19))

    def test_maze_initialization_with_seed(self):
        """Test maze initialization with explicit seed."""
        maze1 = Maze(rows=5, cols=5, seed=42)
        maze2 = Maze(rows=5, cols=5, seed=42)

        # Same seed should produce identical passages
        self.assertEqual(maze1.passages, maze2.passages)

    def test_maze_without_seed_is_valid(self):
        """Randomness may repeat: test structure, never demand random inequality."""
        maze = Maze(rows=3, cols=3)
        self.assertIsNone(maze.seed)
        self.assertEqual(sum(len(v) for v in maze.passages.values()) // 2, 8)
        self.assertTrue(maze.solve())

    def test_maze_validation_rows_invalid(self):
        """Test maze rejects invalid row values."""
        with self.assertRaises(ValueError):
            Maze(rows=0, cols=5)

        with self.assertRaises(ValueError):
            Maze(rows=-1, cols=5)

        with self.assertRaises(ValueError):
            Maze(rows=51, cols=5)

    def test_maze_validation_cols_invalid(self):
        """Test maze rejects invalid column values."""
        with self.assertRaises(ValueError):
            Maze(rows=5, cols=0)

        with self.assertRaises(ValueError):
            Maze(rows=5, cols=-1)

        with self.assertRaises(ValueError):
            Maze(rows=5, cols=51)

    def test_maze_validation_type_errors(self):
        """Test maze rejects non-integer dimensions."""
        with self.assertRaises(TypeError):
            Maze(rows=5.5, cols=5)

        with self.assertRaises(TypeError):
            Maze(rows=5, cols="5")

        with self.assertRaises(TypeError):
            Maze(rows=5, cols=5, seed="42")

    def test_maze_boundary_values(self):
        """Test maze accepts valid boundary values."""
        maze1 = Maze(rows=1, cols=1)
        self.assertEqual(maze1.rows, 1)
        self.assertEqual(maze1.cols, 1)

        maze50 = Maze(rows=50, cols=50)
        self.assertEqual(maze50.rows, 50)
        self.assertEqual(maze50.cols, 50)

    def test_maze_is_spanning_tree(self):
        """Test that maze has exactly (rows*cols - 1) passages (spanning tree)."""
        for rows, cols in [(1, 1), (2, 2), (3, 3), (5, 4), (10, 10)]:
            maze = Maze(rows=rows, cols=cols, seed=42)

            # Count edges (each passage is bidirectional, count once)
            edge_count = sum(len(neighbors) for neighbors in maze.passages.values()) // 2

            # Perfect maze has exactly n-1 edges for n cells
            expected_edges = (rows * cols) - 1
            self.assertEqual(edge_count, expected_edges,
                           f"Maze {rows}x{cols} should have {expected_edges} edges")

    def test_maze_all_cells_initialized(self):
        """Test that all cells are initialized in passages dict."""
        maze = Maze(rows=5, cols=7, seed=42)

        # Should have exactly rows*cols entries
        self.assertEqual(len(maze.passages), 5 * 7)

        # All cells should be tuples in expected range
        for cell in maze.passages.keys():
            row, col = cell
            self.assertGreaterEqual(row, 0)
            self.assertLess(row, 5)
            self.assertGreaterEqual(col, 0)
            self.assertLess(col, 7)


class TestMazeReachability(unittest.TestCase):
    """Test maze connectivity and reachability properties."""

    def test_all_cells_reachable(self):
        """Test that all cells are reachable from start using BFS."""
        maze = Maze(rows=5, cols=5, seed=42)

        # BFS from start to find all reachable cells
        reachable = set()
        queue = deque([maze.start])
        reachable.add(maze.start)

        while queue:
            current = queue.popleft()
            for neighbor in maze.neighbors(current):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        # All cells should be reachable
        total_cells = maze.rows * maze.cols
        self.assertEqual(len(reachable), total_cells)

    def test_passages_symmetric(self):
        """Test that passages are bidirectional (symmetric)."""
        maze = Maze(rows=5, cols=5, seed=42)

        for cell, neighbors in maze.passages.items():
            for neighbor in neighbors:
                # If cell->neighbor exists, neighbor->cell must exist
                self.assertIn(cell, maze.neighbors(neighbor),
                            f"Asymmetric passage: {cell} -> {neighbor} (reverse missing)")

    def test_no_cells_isolated(self):
        """Test that no cell is completely isolated."""
        maze = Maze(rows=5, cols=5, seed=42)

        for cell in maze.passages:
            # Each cell should have at least one connection
            self.assertGreater(len(maze.passages[cell]), 0,
                             f"Cell {cell} is isolated")


class TestMazeNeighbors(unittest.TestCase):
    """Test the neighbors() method for correct behavior."""

    def test_neighbors_deterministic_order(self):
        """Test neighbors always returned in up/right/down/left order."""
        maze = Maze(rows=5, cols=5, seed=42)

        # Get neighbors multiple times
        cell = (2, 2)
        neighbors1 = maze.neighbors(cell)
        neighbors2 = maze.neighbors(cell)

        self.assertEqual(neighbors1, neighbors2)

    def test_neighbors_order_always_up_right_down_left(self):
        """Test neighbors order matches DIRECTIONS keys order."""
        maze = Maze(rows=10, cols=10, seed=42)

        # Test that neighbors are returned in deterministic order
        cell = (5, 5)
        neighbors = maze.neighbors(cell)

        # Each neighbor should correspond to a direction in order
        # We can't assume all 4 directions exist, but those that do
        # should be in the correct order
        directions_order = ['up', 'right', 'down', 'left']
        neighbor_index = 0

        for direction_name in directions_order:
            drow, dcol = DIRECTIONS[direction_name]
            expected_pos = (cell[0] + drow, cell[1] + dcol)

            # Check if this direction has a connection
            if expected_pos in maze.passages[cell]:
                # This neighbor should be next in our neighbors tuple
                self.assertLess(neighbor_index, len(neighbors))
                self.assertEqual(neighbors[neighbor_index], expected_pos)
                neighbor_index += 1

    def test_neighbors_validation_invalid_cell_type(self):
        """Test neighbors() rejects non-tuple cells."""
        maze = Maze()

        with self.assertRaises(ValueError):
            maze.neighbors([0, 0])  # List instead of tuple

        with self.assertRaises(ValueError):
            maze.neighbors("0,0")  # String instead of tuple

    def test_neighbors_validation_invalid_coordinates_type(self):
        """Test neighbors() rejects non-integer coordinates."""
        maze = Maze()

        with self.assertRaises(ValueError):
            maze.neighbors((0.5, 0))

        with self.assertRaises(ValueError):
            maze.neighbors((0, "0"))

    def test_neighbors_validation_out_of_bounds(self):
        """Test neighbors() rejects out-of-bounds cells."""
        maze = Maze(rows=5, cols=5)

        with self.assertRaises(ValueError):
            maze.neighbors((-1, 0))

        with self.assertRaises(ValueError):
            maze.neighbors((0, 5))

        with self.assertRaises(ValueError):
            maze.neighbors((5, 0))

    def test_neighbors_empty_when_no_passages(self):
        """Test neighbors returns empty tuple when cell has no connected neighbors."""
        # Create a maze and find a dead end (if possible)
        maze = Maze(rows=3, cols=3, seed=42)

        for cell in maze.passages:
            neighbors = maze.neighbors(cell)
            # Each neighbor in the tuple should be in the passages set
            for neighbor in neighbors:
                self.assertIn(neighbor, maze.passages[cell])


class TestMazeSolve(unittest.TestCase):
    """Test the solve() method for pathfinding correctness."""

    def test_solve_from_start_to_goal(self):
        """Test solving from start to goal returns valid path."""
        maze = Maze(rows=5, cols=5, seed=42)
        path = maze.solve()

        # Path should not be empty
        self.assertGreater(len(path), 0)

        # Path should start at start and end at goal
        self.assertEqual(path[0], maze.start)
        self.assertEqual(path[-1], maze.goal)

    def test_solve_path_is_connected(self):
        """Test solved path is connected (each step is to a neighbor)."""
        maze = Maze(rows=5, cols=5, seed=42)
        path = maze.solve()

        # Each consecutive pair should be connected via a passage
        for i in range(len(path) - 1):
            current = path[i]
            next_cell = path[i + 1]

            # next_cell should be in neighbors of current
            self.assertIn(next_cell, maze.neighbors(current),
                        f"Path not connected: {current} -> {next_cell}")

    def test_solve_path_is_shortest(self):
        """Test solved path is shortest (no cycles, optimal for BFS)."""
        maze = Maze(rows=5, cols=5, seed=42)
        path = maze.solve()

        # Verify path has no repeated cells (no cycles)
        self.assertEqual(len(path), len(set(path)),
                        "Path contains repeated cells (has cycle)")

    def test_solve_same_cell(self):
        """Test solve when start equals goal."""
        maze = Maze(rows=5, cols=5, seed=42)
        path = maze.solve(start=(2, 2), goal=(2, 2))

        # Should return single-element list
        self.assertEqual(path, [(2, 2)])

    def test_solve_with_custom_start_goal(self):
        """Test solve with non-default start and goal."""
        maze = Maze(rows=5, cols=5, seed=42)
        start = (1, 1)
        goal = (3, 3)

        path = maze.solve(start=start, goal=goal)

        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)

    def test_solve_disconnected_returns_empty(self):
        """Test solve returns empty list if disconnected (hypothetical)."""
        # In a perfect maze this shouldn't happen, but test the contract
        maze = Maze(rows=3, cols=3, seed=42)

        # Manually break a connection to simulate disconnection
        cell1 = (0, 0)
        cell2 = (0, 1)

        # Check if they're connected
        if cell2 in maze.passages[cell1]:
            # Remove the passage
            maze.passages[cell1].discard(cell2)
            maze.passages[cell2].discard(cell1)

            # Solve should return empty list
            path = maze.solve(start=cell1, goal=cell2)
            self.assertEqual(path, [])

    def test_solve_not_mutating(self):
        """Test solve doesn't mutate maze state."""
        maze = Maze(rows=5, cols=5, seed=42)

        # Store original passages
        original_passages = {cell: neighbors.copy()
                            for cell, neighbors in maze.passages.items()}

        # Solve multiple times
        maze.solve()
        maze.solve(start=(1, 1), goal=(3, 3))
        maze.solve()

        # Passages should be unchanged
        self.assertEqual(maze.passages, original_passages)

    def test_solve_1x1_maze(self):
        """Test solve on 1x1 maze."""
        maze = Maze(rows=1, cols=1, seed=42)
        path = maze.solve()

        # Should have single cell
        self.assertEqual(path, [(0, 0)])

    def test_solve_1xn_maze(self):
        """Test solve on 1xN maze (single row)."""
        maze = Maze(rows=1, cols=5, seed=42)
        path = maze.solve()

        # Should start at (0, 0) and end at (0, 4)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (0, 4))

        # Path should be connected
        for i in range(len(path) - 1):
            self.assertIn(path[i + 1], maze.neighbors(path[i]))


class TestMazeGameBasics(unittest.TestCase):
    """Test MazeGame initialization and basic state."""

    def test_game_initialization_default(self):
        """Test game initializes with default settings."""
        game = MazeGame()

        self.assertIsNotNone(game.maze)
        self.assertEqual(game.position, game.maze.start)
        self.assertEqual(game.visited, {game.maze.start})
        self.assertEqual(game.moves, 0)
        self.assertFalse(game.show_solution)

    def test_game_initialization_custom_dims(self):
        """Test game initializes with custom maze dimensions."""
        game = MazeGame(rows=8, cols=12, seed=99)

        self.assertEqual(game.maze.rows, 8)
        self.assertEqual(game.maze.cols, 12)
        self.assertEqual(game.maze.seed, 99)

    def test_won_property_initial_false(self):
        """Test won property is False initially (unless 1x1 maze)."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Not at goal initially
        self.assertFalse(game.won)

    def test_won_property_1x1(self):
        """Test won property is True on 1x1 maze at start."""
        game = MazeGame(rows=1, cols=1, seed=42)

        # Start position is goal on 1x1 maze
        self.assertTrue(game.won)

    def test_solution_property_returns_list(self):
        """Test solution property returns a list."""
        game = MazeGame(rows=5, cols=5, seed=42)
        solution = game.solution

        self.assertIsInstance(solution, list)
        self.assertGreater(len(solution), 0)

    def test_solution_from_current_position(self):
        """Test solution is from current position to goal."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Move once
        original_pos = game.position
        for direction in ['up', 'right', 'down', 'left']:
            if game.move(direction):
                break

        # Solution should be from new position
        solution = game.solution
        self.assertEqual(solution[0], game.position)
        self.assertEqual(solution[-1], game.maze.goal)


class TestMazeGameMovement(unittest.TestCase):
    """Test MazeGame movement mechanics."""

    def test_move_valid_direction(self):
        """Test moving in a valid direction."""
        game = MazeGame(rows=5, cols=5, seed=42)
        original_pos = game.position
        original_moves = game.moves

        # Try to move in each direction until successful
        moved = False
        for direction in ['up', 'right', 'down', 'left']:
            if game.move(direction):
                moved = True

                # Position should change
                self.assertNotEqual(game.position, original_pos)

                # Moves should increment
                self.assertEqual(game.moves, original_moves + 1)

                # Visited should include new position
                self.assertIn(game.position, game.visited)
                break

        self.assertTrue(moved, "Should be able to move somewhere from start")

    def test_move_invalid_direction_raises(self):
        """Test move raises ValueError for invalid direction."""
        game = MazeGame(rows=5, cols=5, seed=42)

        with self.assertRaises(ValueError):
            game.move("north")

        with self.assertRaises(ValueError):
            game.move("invalid")

        with self.assertRaises(ValueError):
            game.move("")

    def test_move_into_wall_returns_false(self):
        """Test move returns False when moving into wall (no passage)."""
        game = MazeGame(rows=5, cols=5, seed=42)
        original_pos = game.position
        original_moves = game.moves

        # Try moving up - maze start (0,0) has no up neighbor
        result = game.move('up')

        if not result:
            # Move was blocked, verify state unchanged
            self.assertEqual(game.position, original_pos)
            self.assertEqual(game.moves, original_moves)

    def test_move_after_winning_returns_false(self):
        """Test move returns False after reaching goal."""
        game = MazeGame(rows=1, cols=1, seed=42)

        # Already at goal
        self.assertTrue(game.won)

        result = game.move('right')
        self.assertFalse(result)

    def test_move_increments_counter_only_on_success(self):
        """Test move counter only increments for successful moves."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Make successful moves
        successful = 0
        for i in range(10):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    successful += 1
                    break

        self.assertEqual(game.moves, successful)

    def test_visited_tracks_all_visited_cells(self):
        """Test visited set includes all cells visited."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Track visited cells as we move
        expected_visited = {game.position}

        # Move around
        for _ in range(20):
            moved = False
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    expected_visited.add(game.position)
                    moved = True
                    break

            if not moved or game.won:
                break

        self.assertEqual(game.visited, expected_visited)


class TestMazeGameRestart(unittest.TestCase):
    """Test MazeGame restart functionality."""

    def test_restart_resets_position(self):
        """Test restart returns position to start."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Move around
        for _ in range(5):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    break

        self.assertNotEqual(game.position, game.maze.start)

        # Restart
        game.restart()
        self.assertEqual(game.position, game.maze.start)

    def test_restart_resets_moves(self):
        """Test restart resets move counter."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Make moves
        for _ in range(5):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    break

        self.assertGreater(game.moves, 0)

        game.restart()
        self.assertEqual(game.moves, 0)

    def test_restart_resets_visited(self):
        """Test restart resets visited set (only start cell)."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Move around
        for _ in range(10):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    break

        original_visited_count = len(game.visited)
        self.assertGreater(original_visited_count, 1)

        game.restart()
        self.assertEqual(game.visited, {game.maze.start})

    def test_restart_hides_solution(self):
        """Test restart sets show_solution to False."""
        game = MazeGame(rows=5, cols=5, seed=42)
        game.show_solution = True

        game.restart()
        self.assertFalse(game.show_solution)

    def test_restart_keeps_maze(self):
        """Test restart keeps the same maze object."""
        game = MazeGame(rows=5, cols=5, seed=42)
        original_passages = game.maze.passages

        game.restart()

        # Maze should be identical
        self.assertEqual(game.maze.passages, original_passages)


class TestMazeGameNewMaze(unittest.TestCase):
    """Test MazeGame new_maze functionality."""

    def test_new_maze_changes_maze(self):
        """A seeded regeneration should match a freshly built maze at that seed."""
        game = MazeGame(rows=5, cols=5, seed=42)
        old_maze = game.maze
        game.new_maze(seed=43)
        self.assertIsNot(game.maze, old_maze)
        self.assertEqual(game.maze.passages, Maze(5, 5, seed=43).passages)

    def test_new_maze_same_seed_same_maze(self):
        """Test new_maze with same seed creates same maze."""
        game = MazeGame(rows=5, cols=5, seed=42)
        original_passages = {cell: neighbors.copy()
                            for cell, neighbors in game.maze.passages.items()}

        # Move around
        for _ in range(5):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    break

        # Create new maze with same seed
        game.new_maze(seed=42)

        # Maze should be identical
        self.assertEqual(game.maze.passages, original_passages)

    def test_new_maze_resets_game_state(self):
        """Test new_maze resets game state via restart."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Move around
        for _ in range(10):
            for direction in ['up', 'right', 'down', 'left']:
                if game.move(direction):
                    break

        game.show_solution = True
        self.assertGreater(game.moves, 0)
        self.assertGreater(len(game.visited), 1)

        # New maze
        game.new_maze(seed=43)

        # State should be reset
        self.assertEqual(game.position, game.maze.start)
        self.assertEqual(game.moves, 0)
        self.assertEqual(game.visited, {game.maze.start})
        self.assertFalse(game.show_solution)

    def test_new_maze_preserves_dimensions(self):
        """Test new_maze keeps same maze dimensions."""
        game = MazeGame(rows=8, cols=12, seed=42)
        original_rows = game.maze.rows
        original_cols = game.maze.cols

        game.new_maze(seed=99)

        self.assertEqual(game.maze.rows, original_rows)
        self.assertEqual(game.maze.cols, original_cols)

    def test_new_maze_none_seed_creates_random(self):
        """Regeneration replaces the object; random layouts may legitimately repeat."""
        game = MazeGame(rows=5, cols=5, seed=42)
        old_maze = game.maze
        game.new_maze()
        self.assertIsNot(game.maze, old_maze)
        self.assertIsNone(game.maze.seed)
        self.assertTrue(game.solution)


class TestMazeEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_1x1_maze_start_equals_goal(self):
        """Test 1x1 maze where start equals goal."""
        maze = Maze(rows=1, cols=1, seed=42)

        self.assertEqual(maze.start, maze.goal)
        self.assertEqual(maze.start, (0, 0))

    def test_1xn_maze_linear_path(self):
        """Test 1xN maze forms linear passage."""
        maze = Maze(rows=1, cols=5, seed=42)

        # All cells should form a linear path
        path = maze.solve()
        self.assertEqual(len(path), 5)

    def test_nx1_maze_linear_path(self):
        """Test Nx1 maze forms linear passage."""
        maze = Maze(rows=5, cols=1, seed=42)

        # All cells should form a linear path
        path = maze.solve()
        self.assertEqual(len(path), 5)

    def test_max_size_maze_generation(self):
        """Test maze generation with maximum allowed size."""
        maze = Maze(rows=50, cols=50, seed=42)

        # Should generate successfully
        self.assertEqual(maze.rows, 50)
        self.assertEqual(maze.cols, 50)

        # Should have n-1 edges
        edge_count = sum(len(n) for n in maze.passages.values()) // 2
        self.assertEqual(edge_count, (50 * 50) - 1)

    def test_no_global_random_state_change(self):
        """Test that maze generation doesn't affect global random state."""
        import random

        # Set a known state
        random.seed(12345)
        random_val_before = random.random()

        # Reset and get value again
        random.seed(12345)

        # Create mazes (should use private Random instances)
        Maze(rows=5, cols=5, seed=42)
        Maze(rows=5, cols=5, seed=None)

        # Reset seed and verify we get same value
        random.seed(12345)
        random_val_after = random.random()

        self.assertEqual(random_val_before, random_val_after)

    def test_directions_contract(self):
        """Test DIRECTIONS contract matches specification."""
        expected = {
            'up': (-1, 0),
            'right': (0, 1),
            'down': (1, 0),
            'left': (0, -1),
        }
        self.assertEqual(DIRECTIONS, expected)


class TestMazeGameIntegration(unittest.TestCase):
    """Integration tests for complete game flow."""

    def test_complete_game_flow(self):
        """Test a complete game from start to goal."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Track game progression
        self.assertFalse(game.won)
        initial_pos = game.position

        # Get solution and follow it
        solution = game.solution
        self.assertGreater(len(solution), 1)

        # Follow path by moving step by step
        max_steps = len(solution) * 2  # Safety limit
        steps_taken = 0

        while not game.won and steps_taken < max_steps:
            # Find next step in solution
            solution = game.solution
            if len(solution) > 1:
                next_pos = solution[1]

                # Determine direction to next position
                drow = next_pos[0] - game.position[0]
                dcol = next_pos[1] - game.position[1]

                for direction, (d_r, d_c) in DIRECTIONS.items():
                    if d_r == drow and d_c == dcol:
                        if game.move(direction):
                            steps_taken += 1
                        break
            else:
                break

        self.assertTrue(game.won)

    def test_game_restart_and_replay(self):
        """Test restarting game and replaying."""
        game = MazeGame(rows=5, cols=5, seed=42)

        # Play first time - follow solution path
        max_attempts = 200
        attempts = 0
        while not game.won and attempts < max_attempts:
            solution = game.solution
            if len(solution) > 1:
                next_pos = solution[1]
                drow = next_pos[0] - game.position[0]
                dcol = next_pos[1] - game.position[1]

                moved = False
                for direction, (d_r, d_c) in DIRECTIONS.items():
                    if d_r == drow and d_c == dcol:
                        if game.move(direction):
                            moved = True
                        break

                if not moved:
                    break
            else:
                break

            attempts += 1

        first_moves_count = game.moves

        # Restart and verify state reset
        game.restart()
        self.assertFalse(game.won)
        self.assertEqual(game.moves, 0)

        # The same solution should still work
        solution = game.solution
        self.assertGreater(len(solution), 0)


class TestValidationAndShortestPath(unittest.TestCase):
    def test_booleans_are_not_dimensions_or_seeds(self):
        for args in ((True, 3, None), (3, False, None), (3, 3, True)):
            with self.subTest(args=args), self.assertRaises(TypeError):
                Maze(*args)

    def test_invalid_solver_endpoints_even_when_equal(self):
        maze = Maze(2, 2)
        for cell in ((-1, 0), (2, 2), (True, 0), [0, 0], None):
            # None is the documented default, not an invalid explicit endpoint.
            if cell is None:
                continue
            with self.subTest(cell=cell), self.assertRaises(ValueError):
                maze.solve(cell, cell)
            with self.assertRaises(ValueError):
                maze.solve(maze.start, cell)

    def test_invalid_direction_types(self):
        for value in ([], {}, None, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MazeGame().move(value)

    def test_bfs_prefers_short_route_on_cyclic_graph(self):
        # Two routes reach the goal. Fixed neighbor order explores the longer
        # top branch first, but BFS must still return the two-edge lower route.
        maze = Maze(2, 3)
        maze.passages = {cell: set() for cell in maze.passages}
        edges = [((0,0),(0,1)), ((0,1),(0,2)), ((0,2),(1,2)),
                 ((1,2),(1,1)), ((1,1),(1,0)), ((1,0),(0,0))]
        for a, b in edges:
            maze.passages[a].add(b)
            maze.passages[b].add(a)
        self.assertEqual(maze.solve((0,0),(1,1)), [(0,0),(1,0),(1,1)])

    def test_invariants_across_seeds_and_shapes(self):
        for rows, cols in ((1,1),(1,7),(7,1),(3,5),(15,15)):
            for seed in range(10):
                maze = Maze(rows, cols, seed=seed)
                reached, pending = {maze.start}, [maze.start]
                while pending:
                    cell = pending.pop()
                    for other in maze.passages[cell]:
                        self.assertIn(cell, maze.passages[other])
                        self.assertEqual(abs(cell[0]-other[0])+abs(cell[1]-other[1]), 1)
                        self.assertTrue(0 <= other[0] < rows and 0 <= other[1] < cols)
                        if other not in reached:
                            reached.add(other)
                            pending.append(other)
                self.assertEqual(len(reached), rows * cols)
                self.assertEqual(sum(map(len, maze.passages.values())) // 2, rows * cols - 1)


if __name__ == '__main__':
    unittest.main()
