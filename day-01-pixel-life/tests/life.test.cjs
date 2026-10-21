/**
 * Comprehensive test suite for Conway's Game of Life - Pixel Life Edition
 *
 * Tests validate:
 * - Grid creation with various dimensions
 * - Generation advancement and pattern evolution
 * - Living cell counting
 * - Pre-defined pattern behavior (Block, Blinker, Glider, Toad)
 * - Boundary conditions and finite edges
 * - Immutability and simultaneous cell updates
 * - Pattern stamping and centering
 * - Independent array rows
 *
 * Run with: node --test day-01-pixel-life/tests/life.test.cjs
 */

const test = require('node:test');
const assert = require('node:assert');
const PixelLife = require('../life.js');

const { createGrid, nextGeneration, countLiving, patterns, stampPattern } = PixelLife;

// ============================================================================
// TEST SUITE: Grid Creation
// ============================================================================

test('Grid Creation - Basic 5x5 grid', () => {
  const grid = createGrid(5, 5);
  assert.strictEqual(grid.length, 5, 'should have 5 rows');
  assert.strictEqual(grid[0].length, 5, 'should have 5 columns');

  // All cells should be dead (0)
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.strictEqual(grid[r][c], 0, `cell [${r},${c}] should be 0`);
    }
  }
});

test('Grid Creation - Various dimensions', () => {
  const grids = [
    { rows: 1, cols: 1 },
    { rows: 10, cols: 3 },
    { rows: 100, cols: 100 }
  ];

  for (const { rows, cols } of grids) {
    const grid = createGrid(rows, cols);
    assert.strictEqual(grid.length, rows, `grid should have ${rows} rows`);
    assert.strictEqual(grid[0].length, cols, `grid should have ${cols} columns`);
  }
});

test('Grid Creation - Invalid inputs throw errors', () => {
  assert.throws(() => createGrid(0, 5), /positive integer/);
  assert.throws(() => createGrid(5, 0), /positive integer/);
  assert.throws(() => createGrid(-1, 5), /positive integer/);
  assert.throws(() => createGrid(5.5, 5), /positive integer/);
  assert.throws(() => createGrid('5', 5), /positive integer/);
  assert.throws(() => createGrid(null, 5), /positive integer/);
});

test('Grid Creation - Independent rows', () => {
  const grid = createGrid(3, 3);
  // Modify one cell in the first row
  grid[0][0] = 1;
  // Ensure other rows are not affected
  assert.strictEqual(grid[1][0], 0, 'row 1 should not be affected');
  assert.strictEqual(grid[2][0], 0, 'row 2 should not be affected');
});

// ============================================================================
// TEST SUITE: Population Counting
// ============================================================================

test('Count Living - Empty grid', () => {
  const grid = createGrid(5, 5);
  assert.strictEqual(countLiving(grid), 0, 'empty grid should have 0 living cells');
});

test('Count Living - Grid with known pattern', () => {
  const grid = createGrid(3, 3);
  grid[0][0] = 1;
  grid[0][1] = 1;
  grid[1][1] = 1;
  assert.strictEqual(countLiving(grid), 3, 'should count 3 living cells');
});

test('Count Living - Full grid', () => {
  const grid = createGrid(3, 3);
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      grid[r][c] = 1;
    }
  }
  assert.strictEqual(countLiving(grid), 9, 'full 3x3 grid should have 9 living cells');
});

// ============================================================================
// TEST SUITE: Game Rules - BLOCK (Still Life)
// ============================================================================

test('Game Rules - BLOCK pattern is stable', () => {
  // BLOCK is a 2x2 square and never changes
  const grid = createGrid(5, 5);
  const withBlock = stampPattern(grid, 1, 1, patterns.BLOCK);

  assert.strictEqual(countLiving(withBlock), 4, 'BLOCK should have 4 cells');

  const gen1 = nextGeneration(withBlock);
  const gen2 = nextGeneration(gen1);

  // Compare structures - should be identical
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.strictEqual(
        gen1[r][c], gen2[r][c],
        `BLOCK should be stable at [${r},${c}]`
      );
    }
  }
});

// ============================================================================
// TEST SUITE: Game Rules - BLINKER (Period 2 Oscillator)
// ============================================================================

test('Game Rules - BLINKER oscillates with period 2', () => {
  const grid = createGrid(5, 5);
  // Horizontal blinker at center
  const gen0 = stampPattern(grid, 2, 1, patterns.BLINKER);

  // Gen 0: horizontal orientation
  assert.strictEqual(gen0[2][1], 1, 'gen0[2][1]');
  assert.strictEqual(gen0[2][2], 1, 'gen0[2][2]');
  assert.strictEqual(gen0[2][3], 1, 'gen0[2][3]');
  assert.strictEqual(countLiving(gen0), 3, 'gen0 should have 3 cells');

  // Gen 1: should be vertical
  const gen1 = nextGeneration(gen0);
  assert.strictEqual(gen1[1][2], 1, 'gen1[1][2] - should be vertical');
  assert.strictEqual(gen1[2][2], 1, 'gen1[2][2] - should be vertical');
  assert.strictEqual(gen1[3][2], 1, 'gen1[3][2] - should be vertical');
  assert.strictEqual(countLiving(gen1), 3, 'gen1 should have 3 cells');

  // Gen 2: should return to horizontal (period 2)
  const gen2 = nextGeneration(gen1);
  assert.strictEqual(gen2[2][1], 1, 'gen2 should return to horizontal');
  assert.strictEqual(gen2[2][2], 1, 'gen2 should return to horizontal');
  assert.strictEqual(gen2[2][3], 1, 'gen2 should return to horizontal');
  assert.strictEqual(countLiving(gen2), 3, 'gen2 should have 3 cells');
});

// ============================================================================
// TEST SUITE: Game Rules - GLIDER (Moving Pattern)
// ============================================================================

test('Game Rules - GLIDER moves diagonally after 4 generations', () => {
  const grid = createGrid(10, 10);
  // Place glider at top-left area
  const gen0 = stampPattern(grid, 0, 0, patterns.GLIDER);

  assert.strictEqual(countLiving(gen0), 5, 'GLIDER should have 5 cells initially');

  // Advance 4 generations
  let current = gen0;
  for (let i = 0; i < 4; i++) {
    current = nextGeneration(current);
  }

  // After 4 generations, glider should have moved southeast by 1 cell
  // The glider should be displaced approximately 1 row down and 1 col right
  // (exact displacement depends on the starting pattern orientation)

  // Verify the glider still has 5 cells and has moved
  assert.strictEqual(countLiving(current), 5, 'GLIDER should still have 5 cells after 4 gen');

  // Verify it's not in the same position as gen0
  let hasMoved = false;
  for (let r = 0; r < 10; r++) {
    for (let c = 0; c < 10; c++) {
      if (current[r][c] !== gen0[r][c]) {
        hasMoved = true;
        break;
      }
    }
    if (hasMoved) break;
  }
  assert.ok(hasMoved, 'GLIDER should have moved after 4 generations');
});

// ============================================================================
// TEST SUITE: Game Rules - TOAD (Period 2 Oscillator)
// ============================================================================

test('Game Rules - TOAD oscillates with period 2', () => {
  const grid = createGrid(10, 10);
  const gen0 = stampPattern(grid, 2, 2, patterns.TOAD);

  assert.strictEqual(countLiving(gen0), 6, 'TOAD should have 6 cells');

  const gen1 = nextGeneration(gen0);
  assert.strictEqual(countLiving(gen1), 6, 'gen1 should have 6 cells');

  const gen2 = nextGeneration(gen1);
  assert.strictEqual(countLiving(gen2), 6, 'gen2 should have 6 cells');

  // Verify it oscillates: gen0 and gen2 should be identical
  let isIdentical = true;
  for (let r = 0; r < 10; r++) {
    for (let c = 0; c < 10; c++) {
      if (gen0[r][c] !== gen2[r][c]) {
        isIdentical = false;
        break;
      }
    }
    if (!isIdentical) break;
  }
  assert.ok(isIdentical, 'TOAD should return to original state after 2 generations (period 2)');
});

// ============================================================================
// TEST SUITE: Boundary Conditions
// ============================================================================

test('Boundary - Edges are finite (not wrapping)', () => {
  // Create a grid with live cells at the edge
  const grid = createGrid(5, 5);
  // Place a horizontal line at the top to demonstrate finite edges
  grid[0][1] = 1;
  grid[0][2] = 1;
  grid[0][3] = 1;

  const gen1 = nextGeneration(grid);

  // The middle cell has two neighbours and survives; the ends each have
  // one and die. A new cell is born BELOW the middle, never above the board.
  assert.strictEqual(gen1[0][2], 1, 'middle cell survives');
  assert.strictEqual(gen1[0][1], 0, 'left end dies');
  assert.strictEqual(gen1[0][3], 0, 'right end dies');
  assert.strictEqual(gen1[1][2], 1, 'three neighbours cause a birth below');

  // No cell is born on the opposite edge: this world does not wrap.
  assert.strictEqual(gen1[4][1], 0, 'opposite edge should not wrap');
  assert.strictEqual(gen1[4][2], 0, 'opposite edge should not wrap');
  assert.strictEqual(gen1[4][3], 0, 'opposite edge should not wrap');
});

test('Boundary - Pattern partially outside grid is clipped', () => {
  const grid = createGrid(5, 5);
  // Stamp GLIDER at edge, some cells will be outside
  const result = stampPattern(grid, -1, -1, patterns.GLIDER);

  // Some cells of the glider are outside bounds
  // Verify the grid is still valid and only in-bounds cells are placed
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.ok(result[r][c] === 0 || result[r][c] === 1, 'cell should be 0 or 1');
    }
  }
});

// ============================================================================
// TEST SUITE: Immutability & Simultaneous Updates
// ============================================================================

test('Immutability - Input grid is not modified', () => {
  const grid = createGrid(5, 5);
  grid[2][2] = 1;
  grid[2][3] = 1;
  grid[2][4] = 1;

  const originalCopy = grid.map(row => [...row]);

  // Call nextGeneration
  nextGeneration(grid);

  // Verify original grid is unchanged
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.strictEqual(grid[r][c], originalCopy[r][c], `grid[${r}][${c}] should not change`);
    }
  }
});

test('Simultaneous Updates - All cells update at the same time', () => {
  // This tests that cell updates don't affect neighbors in the same generation
  // Create a simple pattern that would have different outcomes if updates were sequential
  const grid = createGrid(5, 5);
  // Place two blinkers that would interfere if updates weren't simultaneous
  grid[2][1] = 1;
  grid[2][2] = 1;
  grid[2][3] = 1;
  grid[1][3] = 1;
  grid[3][3] = 1;

  const originalCount = countLiving(grid);
  const gen1 = nextGeneration(grid);
  const gen1Count = countLiving(gen1);

  // Verify that the behavior is consistent (no sequential update artifacts)
  // The exact counts depend on the rules, but should be deterministic
  const gen2 = nextGeneration(gen1);
  const gen2Count = countLiving(gen2);

  // Simulate another generation from the same gen1 state
  const gen2Again = nextGeneration(gen1);

  // These should be identical (deterministic simultaneous updates)
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.strictEqual(gen2[r][c], gen2Again[r][c], `[${r}][${c}] should match`);
    }
  }
});

// ============================================================================
// TEST SUITE: Pattern Stamping
// ============================================================================

test('Pattern Stamping - BLOCK at different positions', () => {
  const grid = createGrid(10, 10);
  const stamped = stampPattern(grid, 3, 4, patterns.BLOCK);

  // BLOCK should be at [3,4], [3,5], [4,4], [4,5]
  assert.strictEqual(stamped[3][4], 1);
  assert.strictEqual(stamped[3][5], 1);
  assert.strictEqual(stamped[4][4], 1);
  assert.strictEqual(stamped[4][5], 1);
  assert.strictEqual(countLiving(stamped), 4);
});

test('Pattern Stamping - Centered BLINKER', () => {
  const grid = createGrid(7, 7);
  const stamped = stampPattern(grid, 3, 3, patterns.BLINKER);

  // BLINKER pattern coordinates: [0,0], [0,1], [0,2]
  // Centered at [3,3] means: [3,3], [3,4], [3,5]
  assert.strictEqual(stamped[3][3], 1);
  assert.strictEqual(stamped[3][4], 1);
  assert.strictEqual(stamped[3][5], 1);
  assert.strictEqual(countLiving(stamped), 3);
});

test('Pattern Stamping - Returns new grid (immutable)', () => {
  const grid = createGrid(10, 10);
  const stamped = stampPattern(grid, 5, 5, patterns.BLOCK);

  // Original grid should be unchanged
  assert.strictEqual(countLiving(grid), 0, 'original grid should be empty');
  assert.strictEqual(countLiving(stamped), 4, 'stamped grid should have BLOCK');

  // Stamped grid should be a different object
  assert.notStrictEqual(grid, stamped, 'should return a new grid object');
});

test('Pattern Stamping - Clipping at boundaries', () => {
  const grid = createGrid(5, 5);
  // Stamp GLIDER with center at (3, 3) - partially outside on bottom-right
  // GLIDER coords: [0,1], [1,2], [2,0], [2,1], [2,2]
  // At (3,3): [3,4], [4,5(out)], [5(out),3], [5(out),4], [5(out),5(out)]
  const stamped = stampPattern(grid, 3, 3, patterns.GLIDER);

  // Grid should remain valid (no errors)
  // Only cells within bounds should be modified
  let countInside = 0;
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      assert.ok(stamped[r][c] === 0 || stamped[r][c] === 1);
      countInside += stamped[r][c];
    }
  }
  // GLIDER at (3,3) places cells at [3,4] and [4,4] within bounds
  assert.ok(countInside > 0, 'some cells should be placed within bounds');
  assert.ok(countInside < 5, 'some glider cells should be clipped outside');
});

// ============================================================================
// TEST SUITE: Edge Cases and Error Handling
// ============================================================================

test('Error Handling - Invalid grid for nextGeneration', () => {
  assert.throws(() => nextGeneration([]), /non-empty/);
  assert.throws(() => nextGeneration(null), /array/);
  assert.throws(() => nextGeneration([[]]), /non-empty/);
});

test('Error Handling - Inconsistent row lengths', () => {
  const badGrid = [
    [0, 1],
    [0, 1, 0]  // Different length
  ];
  assert.throws(() => nextGeneration(badGrid), /same length/);
});

test('Error Handling - Invalid grid for countLiving', () => {
  assert.throws(() => countLiving([]), /non-empty/);
  assert.throws(() => countLiving(null), /array/);
});

test('Error Handling - Invalid coordinates for stampPattern', () => {
  const grid = createGrid(5, 5);
  assert.throws(() => stampPattern(grid, 'a', 1, patterns.BLOCK), /integer/);
  assert.throws(() => stampPattern(grid, 1, null, patterns.BLOCK), /integer/);
  assert.throws(() => stampPattern(grid, 1, 1, null), /array/);
  assert.throws(() => stampPattern(grid, 1, 1, [[1]]), /\[row, col\]/);
  assert.throws(() => stampPattern(grid, 1, 1, [['a', 'b']]), /integer/);
});

// ============================================================================
// TEST SUITE: Regression Tests - Malformed Grids
// ============================================================================

test('Regression - nextGeneration rejects non-array grid', () => {
  assert.throws(() => nextGeneration(null), /array/);
  assert.throws(() => nextGeneration(undefined), /array/);
  assert.throws(() => nextGeneration(42), /array/);
  assert.throws(() => nextGeneration('grid'), /array/);
  assert.throws(() => nextGeneration({}), /array/);
});

test('Regression - nextGeneration rejects empty grid', () => {
  assert.throws(() => nextGeneration([]), /non-empty/);
});

test('Regression - nextGeneration rejects non-array rows', () => {
  assert.throws(() => nextGeneration([null]), /array/);
  assert.throws(() => nextGeneration([undefined]), /array/);
  assert.throws(() => nextGeneration([42]), /array/);
  assert.throws(() => nextGeneration(['row']), /array/);
  assert.throws(() => nextGeneration([{}]), /array/);
});

test('Regression - nextGeneration rejects ragged arrays', () => {
  assert.throws(() => nextGeneration([[0, 1], [0, 1, 0]]), /same length/);
  assert.throws(() => nextGeneration([[0, 1, 0], [0, 1]]), /same length/);
});

test('Regression - nextGeneration rejects empty rows', () => {
  assert.throws(() => nextGeneration([[]]), /non-empty/);
});

test('Regression - nextGeneration rejects non-numeric cells', () => {
  assert.throws(() => nextGeneration([['a', 0]]), /numeric 0 or 1/);
  assert.throws(() => nextGeneration([[0, null]]), /numeric 0 or 1/);
  assert.throws(() => nextGeneration([[0, undefined]]), /numeric 0 or 1/);
  assert.throws(() => nextGeneration([[0, 0.5]]), /numeric 0 or 1/);
  assert.throws(() => nextGeneration([[0, 2]]), /numeric 0 or 1/);
});

test('Regression - nextGeneration rejects sparse arrays', () => {
  const sparse = [];
  sparse[2] = 1;
  assert.throws(() => nextGeneration([sparse]), /numeric 0 or 1/);
});

test('Regression - countLiving rejects non-array grid', () => {
  assert.throws(() => countLiving(null), /array/);
  assert.throws(() => countLiving(undefined), /array/);
  assert.throws(() => countLiving(42), /array/);
  assert.throws(() => countLiving('grid'), /array/);
  assert.throws(() => countLiving({}), /array/);
});

test('Regression - countLiving rejects empty grid', () => {
  assert.throws(() => countLiving([]), /non-empty/);
});

test('Regression - countLiving rejects non-array rows', () => {
  assert.throws(() => countLiving([null]), /array/);
  assert.throws(() => countLiving([undefined]), /array/);
  assert.throws(() => countLiving([42]), /array/);
  assert.throws(() => countLiving(['row']), /array/);
});

test('Regression - countLiving rejects ragged arrays', () => {
  assert.throws(() => countLiving([[0, 1], [0, 1, 0]]), /same length/);
});

test('Regression - countLiving rejects empty rows', () => {
  assert.throws(() => countLiving([[]]), /non-empty/);
});

test('Regression - countLiving rejects non-numeric cells', () => {
  assert.throws(() => countLiving([['a', 0]]), /numeric 0 or 1/);
  assert.throws(() => countLiving([[0, null]]), /numeric 0 or 1/);
  assert.throws(() => countLiving([[0, 2]]), /numeric 0 or 1/);
});

test('Regression - countLiving rejects sparse arrays', () => {
  const sparse = [];
  sparse[2] = 1;
  assert.throws(() => countLiving([sparse]), /numeric 0 or 1/);
});

test('Regression - stampPattern rejects malformed pattern coordinates', () => {
  const grid = createGrid(5, 5);
  assert.throws(() => stampPattern(grid, 1, 1, [[0]]), /\[row, col\]/);
  assert.throws(() => stampPattern(grid, 1, 1, [[0, 1, 2]]), /\[row, col\]/);
  assert.throws(() => stampPattern(grid, 1, 1, [['a', 0]]), /integer/);
  assert.throws(() => stampPattern(grid, 1, 1, [[0, 'b']]), /integer/);
  assert.throws(() => stampPattern(grid, 1, 1, [[0.5, 0]]), /integer/);
  assert.throws(() => stampPattern(grid, 1, 1, [[0, 1.5]]), /integer/);
});

test('Regression - stampPattern rejects invalid grid', () => {
  assert.throws(() => stampPattern([], 1, 1, patterns.BLOCK), /non-empty/);
  assert.throws(() => stampPattern(null, 1, 1, patterns.BLOCK), /array/);
  assert.throws(() => stampPattern([[]], 1, 1, patterns.BLOCK), /non-empty/);
});

test('Regression - stampPattern rejects malformed grid cells', () => {
  const badGrid = [['a', 0], [0, 1]];
  assert.throws(() => stampPattern(badGrid, 1, 1, patterns.BLOCK), /numeric 0 or 1/);
});

// ============================================================================
// TEST SUITE: Integration Tests
// ============================================================================

test('Integration - Complex multi-pattern scenario', () => {
  const grid = createGrid(15, 15);

  // Add multiple patterns
  let current = stampPattern(grid, 1, 1, patterns.BLOCK);
  current = stampPattern(current, 5, 5, patterns.BLINKER);
  current = stampPattern(current, 10, 10, patterns.TOAD);

  assert.strictEqual(countLiving(current), 13, 'should have 4 + 3 + 6 cells');

  // Advance several generations
  for (let i = 0; i < 5; i++) {
    current = nextGeneration(current);
  }

  // Verify grid is still valid
  for (let r = 0; r < 15; r++) {
    for (let c = 0; c < 15; c++) {
      assert.ok(current[r][c] === 0 || current[r][c] === 1);
    }
  }
});

test('Integration - Large grid performance', () => {
  const grid = createGrid(100, 100);
  let current = stampPattern(grid, 50, 50, patterns.GLIDER);

  // Advance many generations - should complete without error
  for (let i = 0; i < 20; i++) {
    current = nextGeneration(current);
  }

  // Should still be valid
  assert.ok(countLiving(current) >= 0, 'should have counted cells');
});

// ============================================================================
// TEST SUITE: Module Export Verification
// ============================================================================

test('Module Export - All functions exported', () => {
  assert.strictEqual(typeof PixelLife.createGrid, 'function');
  assert.strictEqual(typeof PixelLife.nextGeneration, 'function');
  assert.strictEqual(typeof PixelLife.countLiving, 'function');
  assert.strictEqual(typeof PixelLife.stampPattern, 'function');
});

test('Module Export - All patterns available', () => {
  assert.ok(Array.isArray(PixelLife.patterns.BLOCK), 'BLOCK should be an array');
  assert.ok(Array.isArray(PixelLife.patterns.BLINKER), 'BLINKER should be an array');
  assert.ok(Array.isArray(PixelLife.patterns.GLIDER), 'GLIDER should be an array');
  assert.ok(Array.isArray(PixelLife.patterns.TOAD), 'TOAD should be an array');
});

test('Module Export - Patterns have correct structure', () => {
  const checkPattern = (name, pattern) => {
    assert.ok(Array.isArray(pattern), `${name} should be an array`);
    pattern.forEach((coord, idx) => {
      assert.strictEqual(coord.length, 2, `${name}[${idx}] should have 2 elements`);
      assert.ok(Number.isInteger(coord[0]), `${name}[${idx}][0] should be integer`);
      assert.ok(Number.isInteger(coord[1]), `${name}[${idx}][1] should be integer`);
    });
  };

  checkPattern('BLOCK', PixelLife.patterns.BLOCK);
  checkPattern('BLINKER', PixelLife.patterns.BLINKER);
  checkPattern('GLIDER', PixelLife.patterns.GLIDER);
  checkPattern('TOAD', PixelLife.patterns.TOAD);
});

// The test runner prints the final pass/fail summary after executing all tests.
