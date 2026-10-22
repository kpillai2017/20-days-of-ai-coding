"""
Maze Explorer: Generate and solve mazes using randomized DFS and BFS pathfinding.

A maze is represented as a graph of passages connecting cells. This module
provides maze generation using depth-first search and solving using breadth-
first search. Perfect mazes (spanning trees) ensure all cells are reachable.
"""

from random import Random
from collections import deque
from typing import Dict, Set, Tuple, List, Optional


# Direction vectors for maze navigation
DIRECTIONS = {
    'up': (-1, 0),
    'right': (0, 1),
    'down': (1, 0),
    'left': (0, -1),
}


class Maze:
    """
    Generate and manage a perfect maze using randomized depth-first search.

    A perfect maze is a spanning tree where all cells are reachable with no
    cycles. Passages connect adjacent cells and are symmetric (bidirectional).

    Attributes:
        rows (int): Number of rows in the maze (1-50)
        cols (int): Number of columns in the maze (1-50)
        seed (Optional[int]): Seed for reproducible maze generation
        start (Tuple[int, int]): Starting cell (0, 0)
        goal (Tuple[int, int]): Goal cell (rows-1, cols-1)
        passages (Dict): Symmetric adjacency mapping of connected cells
    """

    def __init__(self, rows: int = 15, cols: int = 15, seed: Optional[int] = None):
        """
        Initialize a maze with given dimensions and generate it.

        Args:
            rows: Number of rows (1-50, inclusive). Must be positive integer.
            cols: Number of columns (1-50, inclusive). Must be positive integer.
            seed: Random seed for reproducible generation. None for non-deterministic.

        Raises:
            ValueError: If rows or cols not positive integers or exceed 50.
            TypeError: If rows, cols, or seed have wrong types.
        """
        # Validate and store dimensions
        if type(rows) is not int or type(cols) is not int:
            raise TypeError("rows and cols must be integers")
        if rows <= 0 or cols <= 0 or rows > 50 or cols > 50:
            raise ValueError("rows and cols must be positive integers <= 50")

        # Validate seed if provided
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be an integer or None")

        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.start = (0, 0)
        self.goal = (rows - 1, cols - 1)

        # Initialize empty passages dictionary
        self.passages: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}

        # Generate the maze using randomized DFS
        self._generate_maze()

    def _generate_maze(self) -> None:
        """
        Generate a perfect maze using iterative randomized depth-first search.

        Algorithm:
        1. Initialize all cells with empty passage sets
        2. Start DFS from (0, 0) using a stack
        3. For each cell, shuffle directions and visit unvisited neighbors
        4. Add symmetric passages between visited and current cells
        5. Backtrack when no unvisited neighbors remain

        Result: A spanning tree with (rows*cols - 1) passages connecting all cells.
        """
        # Private Random instance to avoid affecting global state
        rng = Random(self.seed)

        # Initialize passages for all cells (empty sets)
        for row in range(self.rows):
            for col in range(self.cols):
                self.passages[(row, col)] = set()

        # Track visited cells
        visited = set()

        # DFS using explicit stack (iterative approach)
        stack = [(0, 0)]
        visited.add((0, 0))

        while stack:
            current_cell = stack[-1]
            row, col = current_cell

            # Generate shuffled directions for random neighbor selection
            direction_names = list(DIRECTIONS.keys())
            rng.shuffle(direction_names)

            # Track if we found an unvisited neighbor
            found_unvisited = False

            for direction_name in direction_names:
                # Calculate neighbor cell coordinates
                drow, dcol = DIRECTIONS[direction_name]
                neighbor_row = row + drow
                neighbor_col = col + dcol
                neighbor_cell = (neighbor_row, neighbor_col)

                # Check if neighbor is in bounds and unvisited
                if (0 <= neighbor_row < self.rows and
                    0 <= neighbor_col < self.cols and
                    neighbor_cell not in visited):

                    # Create symmetric passage between current and neighbor
                    self.passages[current_cell].add(neighbor_cell)
                    self.passages[neighbor_cell].add(current_cell)

                    # Mark neighbor as visited and push to stack
                    visited.add(neighbor_cell)
                    stack.append(neighbor_cell)
                    found_unvisited = True
                    break  # Process this neighbor next

            # If no unvisited neighbors found, backtrack
            if not found_unvisited:
                stack.pop()

    def neighbors(self, cell: Tuple[int, int]) -> Tuple[Tuple[int, int], ...]:
        """
        Return connected neighbors of a cell in deterministic order.

        Order is always: up, right, down, left (following DIRECTIONS keys order).
        This ensures consistent neighbor traversal regardless of generation.

        Args:
            cell: Tuple (row, col) representing the cell.

        Returns:
            Tuple of neighbor cells connected by passages, in deterministic order.

        Raises:
            ValueError: If cell is not a valid tuple of ints or out of bounds.
        """
        # Validate cell format
        if not isinstance(cell, tuple) or len(cell) != 2:
            raise ValueError("cell must be a tuple (row, col)")

        row, col = cell

        # Validate cell coordinates are integers
        if type(row) is not int or type(col) is not int:
            raise ValueError("cell coordinates must be integers")

        # Validate cell is in bounds
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"cell ({row}, {col}) out of bounds")

        # Membership in a set is fast; examine just the four possible cells.
        # DIRECTIONS preserves insertion order, so BFS tie-breaking is stable.
        return tuple(
            (row + drow, col + dcol)
            for drow, dcol in DIRECTIONS.values()
            if (row + drow, col + dcol) in self.passages[cell]
        )
    def solve(self, start: Optional[Tuple[int, int]] = None,
              goal: Optional[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """
        Find shortest path from start to goal using breadth-first search.

        BFS guarantees the shortest path in an unweighted graph. Returns the
        path as a list of cells from start (inclusive) to goal (inclusive),
        or an empty list if no path exists or cells are disconnected.

        Args:
            start: Starting cell. Defaults to self.start.
            goal: Goal cell. Defaults to self.goal.

        Returns:
            List of cells forming the shortest path, or [] if unreachable.
            Path includes both start and goal endpoints.
        """
        # Use default start and goal if not provided
        if start is None:
            start = self.start
        if goal is None:
            goal = self.goal

        # Validate BOTH endpoints even if they are equal or unreachable.
        self.neighbors(start)
        self.neighbors(goal)

        # Handle 1x1 maze case
        if start == goal:
            return [start]

        # BFS using deque for efficient queue operations
        queue = deque([start])
        visited = {start}
        parent = {start: None}

        while queue:
            current = queue.popleft()

            # Goal found: reconstruct path by following parent pointers
            if current == goal:
                path = []
                node = goal
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return list(reversed(path))

            # Explore neighbors (in deterministic order from neighbors())
            for neighbor in self.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        # No path found
        return []


class MazeGame:
    """
    Interactive maze game with movement, solution tracking, and restart capability.

    The player starts at the maze start position and navigates using directional
    commands to reach the goal. The game tracks visited cells, move count, and
    provides solution hints.

    Attributes:
        maze (Maze): The underlying maze object
        position (Tuple[int, int]): Current player position
        visited (Set): Set of visited cells (including current)
        moves (int): Count of valid moves made
        show_solution (bool): Whether to display the solution
        won (bool property): True when position equals goal
        solution (property): Current shortest path to goal
    """

    def __init__(self, rows: int = 15, cols: int = 15, seed: Optional[int] = None):
        """
        Initialize a new maze game.

        Args:
            rows: Maze rows (1-50). Defaults to 15.
            cols: Maze columns (1-50). Defaults to 15.
            seed: Random seed for reproducible mazes. None for random.
        """
        self.maze = Maze(rows=rows, cols=cols, seed=seed)
        self.position = self.maze.start
        self.visited = {self.maze.start}
        self.moves = 0
        self.show_solution = False

    @property
    def won(self) -> bool:
        """
        Check if player has reached the goal.

        Returns:
            True if current position equals the goal cell.
        """
        return self.position == self.maze.goal

    @property
    def solution(self) -> List[Tuple[int, int]]:
        """
        Get the shortest path from current position to goal.

        Computed on demand using BFS. Does not mutate game state.

        Returns:
            List of cells forming the shortest path, or [] if unreachable.
        """
        return self.maze.solve(start=self.position, goal=self.maze.goal)

    def move(self, direction: str) -> bool:
        """
        Move the player in the specified direction.

        Only moves if:
        - Direction is a valid string (one of: up, right, down, left)
        - Player has not won yet
        - There is a passage connecting to the neighbor in that direction

        Args:
            direction: Direction to move ('up', 'right', 'down', 'left').

        Returns:
            True if move was successful, False otherwise.

        Raises:
            ValueError: If direction is not a valid direction string.
        """
        # Validate direction
        if not isinstance(direction, str) or direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {list(DIRECTIONS.keys())}")

        # Cannot move after winning
        if self.won:
            return False

        # Calculate neighbor position
        drow, dcol = DIRECTIONS[direction]
        neighbor_row = self.position[0] + drow
        neighbor_col = self.position[1] + dcol
        neighbor = (neighbor_row, neighbor_col)

        # Check if passage exists to neighbor
        if neighbor in self.maze.passages[self.position]:
            # Move is valid: update position, visited set, and move counter
            self.position = neighbor
            self.visited.add(neighbor)
            self.moves += 1
            return True

        return False

    def restart(self) -> None:
        """
        Reset game state while keeping the same maze.

        Resets position to start, clears visited cells (keeping only start),
        resets move counter, and hides solution hint.
        Maze object and configuration remain unchanged.
        """
        self.position = self.maze.start
        self.visited = {self.maze.start}
        self.moves = 0
        self.show_solution = False

    def new_maze(self, seed: Optional[int] = None) -> None:
        """
        Generate a new maze with the same dimensions.

        Creates a fresh maze using the provided seed (or non-deterministic if
        None). Automatically calls restart() to reset game state.

        Args:
            seed: Seed for new maze generation. None for random generation.
        """
        # Create new maze with same dimensions but new seed
        self.maze = Maze(rows=self.maze.rows, cols=self.maze.cols, seed=seed)
        # Reset game state
        self.restart()
