# Day 01 · Pixel Life

An interactive **Conway’s Game of Life** made with HTML, CSS and JavaScript. Draw a pattern, press Play, and watch a tiny set of rules create unexpected behaviour.

This is an AI-assisted **coding** project, not an AI model: it uses no AI service, API key, account, build tool or runtime library.

## 1. Install and run

### Easiest: open the file

Download the repository from GitHub (**Code → Download ZIP**) and extract it. Open `day-01-pixel-life/index.html` in a modern browser. That's it! Keep the HTML, CSS and JavaScript files together.

If you use Git, you can instead run:

```sh
git clone https://github.com/kpillai2017/20-days-of-ai-coding.git
cd 20-days-of-ai-coding
```

### Optional: use a local web server

From the repository folder:

```sh
cd day-01-pixel-life
python3 -m http.server 8000 --bind 127.0.0.1
```

On Windows, replace `python3` with `py`. Open **http://localhost:8000**. Leave the terminal running; press **Ctrl+C** to stop the server. Python is only serving the files; it does not run the simulation. Use another port, such as 8001, if 8000 is occupied.

**Requirements:** a modern Chrome, Edge, Firefox or Safari browser. Python 3 is optional for serving; Node.js 20+ is optional for testing. No `npm install` is needed to use the app or run its unit tests.

## 2. Try it

The board starts paused with a five-cell **glider** in its centre.

| Control | Behaviour |
| --- | --- |
| Play / Pause | Start or stop automatic generations. |
| Step | Pause and advance exactly one generation. |
| Clear | Empty the board, pause and reset generation to zero. |
| Random | Replace the board with roughly 28% living cells; pause and reset. |
| Pattern selector + Load pattern | Replace the board with the selected centred pattern; pause and reset. |
| Speed slider | Choose 1–20 generations per second; starts at 8. |
| Click / tap | Toggle a cell; editing pauses the simulation. |
| Drag | Paint living cells if you started on a dead cell, or erase if you started on a live cell. |

**Keyboard:** Tab to the board. A gold outline marks the selected cell. Arrow keys move the selection; Space or Enter toggles it and pauses. Buttons and selectors also support standard keyboard controls. The selected cell’s position and state are announced to screen readers, though canvas is not a full accessible spreadsheet of every cell.

The status shows the generation number and living-cell population. Drawing edits the current generation; only Clear, Random and Load pattern reset the counter. Nothing is saved when you reload the page.

## 3. The four rules

A cell is either alive (`1`) or dead (`0`). Its neighbours are the eight cells surrounding it, including diagonals. The cell itself is **not** a neighbour.

1. A living cell with fewer than two living neighbours dies: underpopulation.
2. A living cell with two or three living neighbours survives.
3. A living cell with more than three living neighbours dies: overpopulation.
4. A dead cell with exactly three living neighbours becomes alive: reproduction.

The board is **40 columns × 28 rows**. Cells outside its boundaries are dead. Edges **do not wrap**: a glider eventually hits the boundary, unlike one on an infinite mathematical board.

## 4. Find your way through the files

```text
day-01-pixel-life/
├── index.html           # Content, controls and canvas; loads scripts in order
├── style.css            # Colours, layout, responsive sizing and focus indicators
├── life.js              # Pure simulation functions; no browser interaction
├── app.js               # Mutable app state, controls, drawing and animation
├── tests/
│   └── life.test.cjs     # Automated tests using Node’s built-in test runner
└── README.md            # You are here
```

Start with `index.html`, then `life.js`, then `app.js`. Read `style.css` when you want to change the appearance. Source comments explain design decisions as well as syntax.

### `life.js`: data and rules

A **two-dimensional array** is an array of rows, each containing an array of cells. `grid[row][col]` starts at zero, so the top-left cell is `grid[0][0]`.

```js
const board = PixelLife.createGrid(5, 5);
board[2][1] = 1;
board[2][2] = 1;
board[2][3] = 1; // A horizontal blinker.
const next = PixelLife.nextGeneration(board);
console.log(PixelLife.countLiving(next)); // 3, now vertical.
```

The script exports `PixelLife` on `globalThis` for browsers and through `module.exports` for Node tests. Both environments exercise the same implementation.

| Function | Purpose |
| --- | --- |
| `createGrid(rows, cols)` | Make a fresh rectangular grid of numeric zeroes. Each row is an independent array. Dimensions must be positive integers. |
| `nextGeneration(grid)` | Return a **new** grid by applying the rules to every cell. Do not modify the input. |
| `countLiving(grid)` | Count the total living population, **not** the neighbours of one cell. |
| `stampPattern(grid, startRow, startCol, coordinates)` | Return a copy of the grid with a pattern added at a top-left offset; existing cells remain, and off-board cells are clipped. |
| `countNeighbors(grid, row, col)` | Internal helper that counts up to eight neighbours, checking bounds. Not part of the public API. |

`PixelLife.patterns` provides `BLOCK`, `BLINKER`, `GLIDER` and `TOAD`. Each pattern is an array of relative `[row, col]` pairs. For example:

```js
PixelLife.patterns.BLOCK; // [[0, 0], [0, 1], [1, 0], [1, 1]]
const blockBoard = PixelLife.stampPattern(
  PixelLife.createGrid(6, 6), 2, 2, PixelLife.patterns.BLOCK
);
```

**Why make a new grid?** Each cell must see the same unchanged old generation. If we overwrite cells as we scan, later cells would see a mixture of old and new values. Keeping an old grid and a new grid is often called **double buffering**. This refers to simulation data, not a special canvas rendering feature.

Each generation scans every cell and checks at most eight neighbours. Its work grows in proportion to `rows × columns` (written **O(rows × columns)**). The new grid also uses O(rows × columns) memory. The public grid contract is a non-empty rectangular array containing only numeric 0 or 1 values.

### `app.js`: from input to pixels

The app is enclosed in a function so its changing variables don't leak into the global namespace.

- `grid`, `generation` and `playing` hold the current state.
- `setPlaying(value)` updates the play state, button text and timing.
- `advance()` calls `nextGeneration`, increments the counter and redraws.
- `reset(nextGrid)` pauses, replaces the grid and resets the counter.
- `loadPattern()` measures a pattern’s bounding box and calculates a centred top-left offset before stamping it onto a blank grid.
- `render()` redraws the canvas from the grid and updates the counters.
- `eventCell(event)` converts a pointer position into a row and column.
- `paintTo(cell)` fills a line between pointer samples so a fast drag doesn't leave gaps.
- `animate(timestamp)` requests another browser frame and advances when a generation is due.

**Trace one click:** `pointerdown` → convert screen position to cell → pause → choose paint/erase → change the grid → `render()`.

**Trace one tick:** `requestAnimationFrame` → check elapsed time against `1000 / speed` milliseconds → `advance()` → create the next grid → redraw → schedule another frame.

The animation requests browser frames, but only redraws when state changes. It skips missed generations rather than catching up after a slow frame or hidden tab. The speed is a target, not a real-time guarantee.

The canvas drawing buffer stays 800 × 560 pixels. CSS scales it to fit the page, so pointer coordinates are converted using its displayed size. Pointer events unify mouse, touch and pen input. Pointer capture lets a stroke end cleanly even when released outside the board.

### `index.html` and `style.css`: interface

HTML provides semantic headings, labelled controls, a focusable canvas and a no-JavaScript message. `defer` waits until the HTML is parsed and preserves script order: `life.js` must load before `app.js`.

CSS variables define the palette in one place. Flexbox arranges controls; a media query stacks sections on small screens. Focus indicators remain visible for keyboard navigation.

## 5. Test what you learn

From the project folder, with **Node.js 20 or newer** installed:

```sh
node --test tests/life.test.cjs
```

Or from the repository root:

```sh
node --test day-01-pixel-life/tests/life.test.cjs
```

Tests cover independent rows, population counts, finite boundaries, clipping, input immutability, simultaneous updates and classic patterns. GitHub Actions runs the same suite on pushes and pull requests.

### Check the interface yourself

1. Load **Block**. Step repeatedly: the four cells stay still.
2. Load **Blinker**. Step once: it turns vertical. Step again: it returns.
3. Load **Glider**. Step four times: it moves one cell down and right.
4. Load **Toad**. Two steps return it to its starting arrangement.
5. Press Play, then draw: the app pauses. Drag quickly: no gaps in the stroke.
6. Press Step during playback: exactly one more generation, then paused.
7. Clear: generation and population both show zero.
8. Tab to the canvas, use arrows, then Space: the highlighted cell toggles.
9. Narrow the browser window or try a phone: controls should remain usable.

## 6. Troubleshooting

- **Blank board or unresponsive controls:** ensure all four app files are together, JavaScript is enabled, and inspect Developer Tools → Console for errors. A blank board after Clear is normal!
- **Cannot find the file:** check your terminal’s current folder. The commands above name the folder they expect.
- **`python3` not found:** open the HTML directly, install Python 3, or use `py` on Windows.
- **`node` not found / tests unavailable:** install a current Node.js LTS release. Node is not needed to play.
- **Port already in use:** replace 8000 with 8001 in both the server command and URL.
- **A glider disappears:** this board has finite dead boundaries. Load it again to restart.
- **Touch drawing scrolls the page:** start your gesture inside the canvas, not in its margin.

## 7. Small exercises

Try one change at a time, rerun tests, and inspect the result:

1. Change the live-cell colour in `render()` and the accent CSS variable.
2. Change the Random density from `0.28` to `0.15`. What happens?
3. Add another pattern, then add its selector option and test.
4. Add a reset-to-start button. Remember to copy each row of the saved grid.
5. Add an optional wrap-around world. Keep dead-edge mode and test both.
6. Save and restore a board with `localStorage` (a browser storage API).

## References and attribution

These are references for learning; this project is an original small implementation, not a copy of a tutorial.

- [Conway’s Game of Life: rules and history](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
- [LifeWiki: Block](https://conwaylife.com/wiki/Block), [Blinker](https://conwaylife.com/wiki/Blinker), [Glider](https://conwaylife.com/wiki/Glider), [Toad](https://conwaylife.com/wiki/Toad)
- [MDN: JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [MDN: Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- [MDN: requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
- [MDN: Pointer events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)
- [Node.js: test runner](https://nodejs.org/api/test.html)

Game of Life was devised by John Horton Conway. No third-party images, fonts or sounds are bundled.
