/* The UI owns changing state. life.js knows nothing about buttons or canvas.
   Keeping these responsibilities separate makes the rules easy to test. */
(() => {
  "use strict";

  const { createGrid, nextGeneration, countLiving, stampPattern, patterns } = globalThis.PixelLife;
  const ROWS = 28;
  const COLS = 40;
  const board = document.getElementById("board");
  const context = board.getContext("2d");
  const playButton = document.getElementById("play");
  const speedInput = document.getElementById("speed");
  const cellStatus = document.getElementById("cell-status");
  const cellWidth = board.width / COLS;
  const cellHeight = board.height / ROWS;

  let grid = createGrid(ROWS, COLS);
  let generation = 0;
  let playing = false;
  let speed = Number(speedInput.value);
  let lastTick = null;
  let activePointer = null;
  let paintValue = 1;
  let previousCell = null;
  let keyboardFocus = false;
  let selectedRow = Math.floor(ROWS / 2);
  let selectedCol = Math.floor(COLS / 2);

  /** Redraw from the model: canvas is an output, never the source of truth. */
  function render() {
    context.fillStyle = "#0c141d";
    context.fillRect(0, 0, board.width, board.height);
    context.fillStyle = "#8df0bb";
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        if (grid[row][col]) {
          context.fillRect(col * cellWidth + 2, row * cellHeight + 2, cellWidth - 4, cellHeight - 4);
        }
      }
    }
    // Draw lines after cells so the grid stays visible even on a full board.
    context.strokeStyle = "#233142";
    context.lineWidth = 1;
    context.beginPath();
    for (let col = 0; col <= COLS; col++) {
      context.moveTo(col * cellWidth, 0);
      context.lineTo(col * cellWidth, board.height);
    }
    for (let row = 0; row <= ROWS; row++) {
      context.moveTo(0, row * cellHeight);
      context.lineTo(board.width, row * cellHeight);
    }
    context.stroke();
    if (keyboardFocus) {
      context.strokeStyle = "#ffce75";
      context.lineWidth = 2;
      context.strokeRect(selectedCol * cellWidth + 1, selectedRow * cellHeight + 1, cellWidth - 2, cellHeight - 2);
    }
    document.getElementById("generation").textContent = generation;
    document.getElementById("population").textContent = countLiving(grid);
  }

  function setPlaying(value) {
    playing = value;
    // Reset timing when resuming so a long pause never becomes a huge jump.
    lastTick = null;
    playButton.textContent = playing ? "Pause" : "Play";
    playButton.setAttribute("aria-pressed", String(playing));
    document.getElementById("mode").textContent = playing ? "Running" : "Paused";
  }

  function advance() {
    grid = nextGeneration(grid);
    generation += 1;
    render();
  }

  /** Replace the board, pause, and start a fresh generation count. */
  function reset(nextGrid) {
    setPlaying(false);
    // A toolbar action also ends any in-progress drawing gesture.
    activePointer = null;
    previousCell = null;
    grid = nextGrid;
    generation = 0;
    render();
  }

  function loadPattern() {
    const coordinates = patterns[document.getElementById("pattern").value];
    // Coordinates describe a pattern's bounding box, not its centre.
    const height = Math.max(...coordinates.map(([row]) => row)) + 1;
    const width = Math.max(...coordinates.map(([, col]) => col)) + 1;
    reset(stampPattern(createGrid(ROWS, COLS), Math.floor((ROWS - height) / 2), Math.floor((COLS - width) / 2), coordinates));
  }

  playButton.addEventListener("click", () => setPlaying(!playing));
  document.getElementById("step").addEventListener("click", () => {
    setPlaying(false);
    advance();
  });
  document.getElementById("clear").addEventListener("click", () => reset(createGrid(ROWS, COLS)));
  document.getElementById("random").addEventListener("click", () => {
    // About 28% density usually produces more interesting shapes than a full grid.
    reset(createGrid(ROWS, COLS).map(row => row.map(() => Math.random() < 0.28 ? 1 : 0)));
  });
  document.getElementById("load-pattern").addEventListener("click", loadPattern);
  speedInput.addEventListener("input", () => {
    speed = Number(speedInput.value);
    document.getElementById("speed-value").textContent = `${speed} generation${speed === 1 ? "" : "s"} / sec`;
    lastTick = null;
  });

  /** Convert viewport coordinates into a cell, accounting for CSS scaling. */
  function eventCell(event) {
    const rect = board.getBoundingClientRect();
    const row = Math.floor((event.clientY - rect.top) / rect.height * ROWS);
    const col = Math.floor((event.clientX - rect.left) / rect.width * COLS);
    if (row < 0 || row >= ROWS || col < 0 || col >= COLS) return null;
    return { row, col };
  }

  function announceCell() {
    cellStatus.textContent = `Row ${selectedRow + 1}, column ${selectedCol + 1}, ${grid[selectedRow][selectedCol] ? "alive" : "dead"}.`;
  }

  /** Join consecutive pointer samples so fast dragging doesn't leave holes.
      Interpolate along the longer axis; rounding maps each sample to a cell. */
  function paintTo(cell) {
    const start = previousCell || cell;
    const steps = Math.max(Math.abs(cell.row - start.row), Math.abs(cell.col - start.col));
    for (let i = 0; i <= steps; i++) {
      const fraction = steps === 0 ? 0 : i / steps;
      const row = Math.round(start.row + (cell.row - start.row) * fraction);
      const col = Math.round(start.col + (cell.col - start.col) * fraction);
      grid[row][col] = paintValue;
    }
    previousCell = cell;
    selectedRow = cell.row;
    selectedCol = cell.col;
    render();
  }

  board.addEventListener("pointerdown", event => {
    if (!event.isPrimary || event.button !== 0 || activePointer !== null) return;
    const cell = eventCell(event);
    if (!cell) return;
    event.preventDefault();
    setPlaying(false);
    board.focus({ preventScroll: true });
    keyboardFocus = false;
    activePointer = event.pointerId;
    previousCell = null;
    // A gesture consistently paints OR erases, rather than toggling repeatedly.
    paintValue = grid[cell.row][cell.col] ? 0 : 1;
    board.setPointerCapture(event.pointerId);
    paintTo(cell);
    announceCell();
  });
  board.addEventListener("pointermove", event => {
    if (event.pointerId !== activePointer) return;
    const cell = eventCell(event);
    if (cell) paintTo(cell);
    else previousCell = null; // Don't connect a stroke through off-board space.
  });
  function endStroke(event) {
    if (event.pointerId !== activePointer) return;
    activePointer = null;
    previousCell = null;
    announceCell();
  }
  board.addEventListener("pointerup", endStroke);
  board.addEventListener("pointercancel", endStroke);
  board.addEventListener("lostpointercapture", endStroke);

  board.addEventListener("focus", () => {
    keyboardFocus = true;
    announceCell();
    render();
  });
  board.addEventListener("blur", () => {
    keyboardFocus = false;
    render();
  });
  board.addEventListener("keydown", event => {
    const keys = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "Enter"];
    if (!keys.includes(event.key)) return;
    event.preventDefault(); // Arrows/Space should edit, not scroll the document.
    keyboardFocus = true;
    if (event.key === "ArrowUp") selectedRow = Math.max(0, selectedRow - 1);
    if (event.key === "ArrowDown") selectedRow = Math.min(ROWS - 1, selectedRow + 1);
    if (event.key === "ArrowLeft") selectedCol = Math.max(0, selectedCol - 1);
    if (event.key === "ArrowRight") selectedCol = Math.min(COLS - 1, selectedCol + 1);
    if ((event.key === " " || event.key === "Enter") && !event.repeat) {
      setPlaying(false);
      grid[selectedRow][selectedCol] = grid[selectedRow][selectedCol] ? 0 : 1;
    }
    announceCell();
    render();
  });

  /** requestAnimationFrame matches browser repaint timing. The timestamp gate
      controls generations per second, not frames per second. We intentionally
      skip missed ticks: returning to a hidden tab must not race through history. */
  function animate(timestamp) {
    if (playing) {
      if (lastTick === null) lastTick = timestamp;
      if (timestamp - lastTick >= 1000 / speed) {
        advance();
        lastTick = timestamp;
      }
    }
    window.requestAnimationFrame(animate);
  }
  document.addEventListener("visibilitychange", () => { lastTick = null; });

  loadPattern(); // Begin paused with a glider so the empty page isn't a puzzle.
  window.requestAnimationFrame(animate);
})();
