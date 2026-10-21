/**
 * Conway's Game of Life - Pixel Life Edition
 *
 * A classic cellular automaton implementation featuring:
 * - Grid creation and state management
 * - Generation advancement with standard rules
 * - Population counting
 * - Pre-defined life patterns (Block, Blinker, Glider, Toad)
 * - Pattern stamping onto grids
 *
 * The module is exposed as both a global object and CommonJS module export,
 * supporting browser scripts and Node.js environments alike.
 *
 * @module PixelLife
 */

/**
 * Rules of Life:
 * 1. A live cell with 2-3 live neighbors survives
 * 2. A dead cell with exactly 3 live neighbors becomes alive
 * 3. All other cells die or remain dead
 * 4. The board has finite dead edges (no wrapping)
 */

/**
 * Creates a new grid with specified dimensions.
 * All cells are initialized to 0 (dead).
 *
 * @param {number} rows - Number of rows in the grid (must be positive integer)
 * @param {number} cols - Number of columns in the grid (must be positive integer)
 * @returns {number[][]} A 2D array where each element is 0 (dead) or 1 (alive)
 * @throws {Error} If rows or cols is not a positive integer
 *
 * @example
 * const grid = createGrid(5, 5);
 * // Returns:
 * // [
 * //   [0, 0, 0, 0, 0],
 * //   [0, 0, 0, 0, 0],
 * //   [0, 0, 0, 0, 0],
 * //   [0, 0, 0, 0, 0],
 * //   [0, 0, 0, 0, 0]
 * // ]
 */
function createGrid(rows, cols) {
  // Validate input parameters
  if (!Number.isInteger(rows) || rows <= 0) {
    throw new Error('rows must be a positive integer');
  }
  if (!Number.isInteger(cols) || cols <= 0) {
    throw new Error('cols must be a positive integer');
  }

  // Create the grid as an array of arrays
  const grid = [];
  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      row.push(0); // Initialize all cells to dead
    }
    grid.push(row);
  }

  return grid;
}

/**
 * Counts the number of living neighbors for a cell at the given position.
 * Neighbors are the 8 surrounding cells. Edges beyond the grid are considered dead.
 *
 * @param {number[][]} grid - The current game state
 * @param {number} row - Row index of the cell to check
 * @param {number} col - Column index of the cell to check
 * @returns {number} Count of living neighbors (0-8)
 * @private
 */
function countNeighbors(grid, row, col) {
  let count = 0;

  // Check all 8 surrounding cells
  // The grid has a finite edge, so we check bounds
  for (let dr = -1; dr <= 1; dr++) {
    for (let dc = -1; dc <= 1; dc++) {
      // Skip the center cell (the cell we're examining)
      if (dr === 0 && dc === 0) continue;

      const newRow = row + dr;
      const newCol = col + dc;

      // Only count if within grid boundaries
      if (newRow >= 0 && newRow < grid.length &&
          newCol >= 0 && newCol < grid[0].length) {
        count += grid[newRow][newCol];
      }
      // Cells beyond the edge are implicitly dead (0), so we don't count them
    }
  }

  return count;
}

/**
 * Advances the grid by one generation using Conway's Game of Life rules.
 * The input grid remains unchanged (immutable operation).
 * All cells are updated simultaneously based on the current generation.
 *
 * Rules:
 * - A living cell with 2-3 living neighbors survives
 * - A dead cell with exactly 3 living neighbors becomes alive
 * - All other cells become/stay dead
 *
 * @param {number[][]} grid - The current game state (not modified)
 * @returns {number[][]} A new grid representing the next generation
 * @throws {Error} If grid is empty or rows have inconsistent lengths
 *
 * @example
 * // BLINKER pattern oscillates between horizontal and vertical
 * const gen0 = [[0,1,0],
 *               [0,1,0],
 *               [0,1,0]];
 * const gen1 = nextGeneration(gen0);
 * // gen1 will be:
 * // [[0,0,0],
 * //  [1,1,1],
 * //  [0,0,0]]
 */
function nextGeneration(grid) {
  // Validate grid
  if (!Array.isArray(grid) || grid.length === 0) {
    throw new Error('grid must be a non-empty array');
  }
  if (!Array.isArray(grid[0]) || grid[0].length === 0) {
    throw new Error('grid rows must be non-empty arrays');
  }

  // Verify all rows have the same length (rectangular grid)
  const expectedCols = grid[0].length;
  for (let i = 0; i < grid.length; i++) {
    if (grid[i].length !== expectedCols) {
      throw new Error('all rows must have the same length');
    }
  }

  const rows = grid.length;
  const cols = grid[0].length;
  const newGrid = createGrid(rows, cols);

  // Process each cell simultaneously
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const livingNeighbors = countNeighbors(grid, r, c);
      const isAlive = grid[r][c] === 1;

      // Apply Game of Life rules
      if (isAlive) {
        // Living cell: survives with 2-3 neighbors
        if (livingNeighbors === 2 || livingNeighbors === 3) {
          newGrid[r][c] = 1;
        } else {
          newGrid[r][c] = 0; // Dies (underpopulation or overpopulation)
        }
      } else {
        // Dead cell: becomes alive with exactly 3 neighbors
        if (livingNeighbors === 3) {
          newGrid[r][c] = 1;
        } else {
          newGrid[r][c] = 0; // Stays dead
        }
      }
    }
  }

  return newGrid;
}

/**
 * Counts the total number of living cells in the grid.
 *
 * @param {number[][]} grid - The game state to analyze
 * @returns {number} Total count of living cells (state === 1)
 * @throws {Error} If grid is invalid
 *
 * @example
 * const grid = [[0,1,0],
 *               [0,1,0],
 *               [0,1,0]];
 * countLiving(grid); // Returns 3
 */
function countLiving(grid) {
  // Validate grid
  if (!Array.isArray(grid) || grid.length === 0) {
    throw new Error('grid must be a non-empty array');
  }

  let count = 0;

  // Sum all living cells
  for (let r = 0; r < grid.length; r++) {
    if (!Array.isArray(grid[r])) {
      throw new Error('grid rows must be arrays');
    }
    for (let c = 0; c < grid[r].length; c++) {
      count += grid[r][c];
    }
  }

  return count;
}

/**
 * Pre-defined life patterns as coordinate pairs [row, col].
 * Each pattern is a set of relative coordinates that can be stamped onto a grid.
 *
 * @constant
 * @type {Object<string, number[][]>}
 */
const patterns = {
  /**
   * BLOCK: A 2x2 stable pattern (still life).
   * Never changes; the most basic stable configuration.
   */
  BLOCK: [
    [0, 0], [0, 1],
    [1, 0], [1, 1]
  ],

  /**
   * BLINKER: A 3-cell oscillator with period 2.
   * Alternates between horizontal and vertical orientation.
   */
  BLINKER: [
    [0, 0],
    [0, 1],
    [0, 2]
  ],

  /**
   * GLIDER: A 5-cell pattern that moves diagonally, period 4.
   * The smallest known spaceship; moves southeast 1 cell per 4 generations.
   */
  GLIDER: [
    [0, 1],
    [1, 2],
    [2, 0], [2, 1], [2, 2]
  ],

  /**
   * TOAD: A 6-cell oscillator with period 2.
   * Also called a "period-2 oscillator" or "2-cycle".
   */
  TOAD: [
    [0, 1], [0, 2], [0, 3],
    [1, 0], [1, 1], [1, 2]
  ]
};

/**
 * Stamps a pattern with its top-left reference point at the given coordinates.
 * The pattern's (0,0) offset is placed at (centerRow, centerCol).
 * Despite their names, these parameters specify an origin, not a centre;
 * app.js calculates the origin needed to centre a pattern on the board.
 * This function creates and returns a NEW grid with the pattern applied,
 * leaving all other cells unchanged.
 *
 * @param {number[][]} grid - The grid to stamp the pattern onto (not modified)
 * @param {number} centerRow - Grid row where pattern center is placed
 * @param {number} centerCol - Grid column where pattern center is placed
 * @param {number[][]} coordinates - Array of [row, col] pairs defining the pattern
 * @returns {number[][]} A new grid with the pattern stamped in
 * @throws {Error} If parameters are invalid
 *
 * @example
 * const grid = createGrid(5, 5);
 * const withBlock = stampPattern(grid, 1, 1, patterns.BLOCK);
 * // Results in a 2x2 block of live cells starting at [1,1]
 */
function stampPattern(grid, centerRow, centerCol, coordinates) {
  // Validate input
  if (!Array.isArray(grid) || grid.length === 0) {
    throw new Error('grid must be a non-empty array');
  }
  if (!Number.isInteger(centerRow) || !Number.isInteger(centerCol)) {
    throw new Error('centerRow and centerCol must be integers');
  }
  if (!Array.isArray(coordinates)) {
    throw new Error('coordinates must be an array');
  }

  const rows = grid.length;
  const cols = grid[0].length;

  // Create a deep copy of the grid to avoid modifying the input
  const newGrid = grid.map(row => [...row]);

  // Stamp each coordinate of the pattern
  for (let i = 0; i < coordinates.length; i++) {
    const coord = coordinates[i];
    if (!Array.isArray(coord) || coord.length !== 2) {
      throw new Error('each coordinate must be an array of [row, col]');
    }

    const patternRow = coord[0];
    const patternCol = coord[1];

    // Calculate the actual grid position
    const gridRow = centerRow + patternRow;
    const gridCol = centerCol + patternCol;

    // Only place the cell if it's within grid bounds
    if (gridRow >= 0 && gridRow < rows && gridCol >= 0 && gridCol < cols) {
      newGrid[gridRow][gridCol] = 1;
    }
  }

  return newGrid;
}

/**
 * Public API object containing all exported functions and constants.
 * This object is assigned to both globalThis (for browser scripts)
 * and module.exports (for Node.js require/CommonJS).
 *
 * @type {Object}
 */
const PixelLife = {
  createGrid,
  nextGeneration,
  countLiving,
  patterns,
  stampPattern
};

// Export for browser environments via global object
if (typeof globalThis !== 'undefined') {
  globalThis.PixelLife = PixelLife;
}

// Export for Node.js/CommonJS environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PixelLife;
}
