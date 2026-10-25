# Learn how Clockwork Chess works

This is a small teaching engine, not a grandmaster program. Follow one move through the files before trying to understand the entire search tree. Source comments explain the tricky boundaries; this guide connects them.

## Before reading: Python notation used in the source

Every application function/class now has a nearby docstring explaining its job, with inline notes at the less obvious steps. A docstring is the triple-quoted string immediately inside a definition; `help(Position.legal_moves)` can display it in Python. A `#` comment explains the adjacent implementation but does not execute.

- `self` is the current object: `self.board` belongs to one Position, not every game.
- `None` means no result/square/pending job; it is different from square index `0` (a1). Use `is None`, not a truth test, when zero is valid.
- A tuple such as `(file, rank)` groups coordinates; unpacking gives each a name.
- A comprehension builds a list/set from matching items. Read it as a compact loop; the surrounding comments identify what is being filtered.
- `yield` emits a candidate lazily; `return` finishes a function. Move generation materialises its generator before temporarily changing the board.
- `try/finally` guarantees cleanup even on timeout, while `try/except` handles an error. That distinction is crucial in recursive make/unmake.
- Nested search helpers close over the search's local position/deadline; `nonlocal nodes` permits updating the shared node counter.
- A `Future` is a handle to worker work. Calling `done()` checks without waiting; calling `result()` before completion would block.

Start with the smaller `animation.py`, then the controller's click/preview/commit path, then legal rules, then search. Run the tests before and after an experiment. This readability pass changed comments/docstrings/formatting only: executable syntax trees were compared with the previous revision after removing docstrings.

## 1. Three responsibilities

```text
engine.py    rules, game state and computer choice (no Pygame)
graphics.py  original character meshes / 2D icons → screen
animation.py pure elapsed-time choreography, shared by both views
main.py      clicks → move preview → commit → computer turn
```

Separating these means legal moves can be tested without a monitor, and animation cannot accidentally change the rules. A chess board is not the same object as the picture of a board.

## 2. A flat list represents 64 squares

`board[0]` is a1, `board[7]` h1, `board[56]` a8. Convert with:

```text
file = square % 8
rank = square // 8
square = rank * 8 + file
```

Uppercase letters are White, lowercase Black; `.` is empty. N means knight because K already means king. Moves are frozen dataclasses: source, destination, optional promotion, en-passant flag and castle flag. `e7e8q` means promote to queen; this coordinate notation is not algebraic chess notation.

VICE uses a larger mailbox board with off-board sentinels. We instead check file/rank bounds explicitly. That is easy to inspect but costs more Python work. Avoid treating a one-dimensional +1 as always “right”: h1+1 is a2, not a legal horizontal step.

## 3. FEN is a snapshot, not a whole game

FEN records piece layout, side to move, castling rights, en-passant target, halfmove counter and move number. Digits are runs of empty squares. FEN starts with rank 8, unlike our list starting at a1.

A position also needs history for undo and repetition. FEN alone cannot reconstruct how often a board occurred. The parser rejects malformed layouts and implausible special metadata, but is not a proof that every accepted arrangement can be reached from the initial position.

## 4. Attacks, candidate moves and legal moves

These are three different questions:

1. **Attack:** does this side control a square? Pawns attack diagonally even if the square is empty.
2. **Pseudo-legal move:** does movement geometry and occupancy permit this move?
3. **Legal move:** after it, is the moving side's king still safe?

A pinned piece still attacks squares for king safety, even though it may not legally move. Therefore `is_attacked` cannot simply call `legal_moves`: that would both confuse rules and recurse forever.

Sliding pieces walk along directional rays until blocked. Knights jump using eight offsets. Pawns have special forward, double-step, diagonal-capture and promotion rules. Kings are never capture targets; a checked king must escape, block or capture the checking piece legally.

`legal_moves` materialises candidates, pushes each temporarily, checks the mover's king, then pops it in `finally`. `finally` restores state even if checking throws an exception. Never leave the board one move deeper after a failed test.

## 5. Special moves need extra state

### Castling

The king and correct rook must still have rights and be on home squares. The intervening squares must be empty; the king cannot start in check or cross/land on an attacked square. Moving a king/rook or capturing a home rook removes the corresponding rights. Moving back does not restore them; Undo does.

### En passant

A pawn can capture behind the opponent's immediately preceding double-step. The removed pawn is **not on the destination square**. Removing both pawns can uncover a rook attack on the king, so ordinary post-move king checking remains essential.

A nominal en-passant square matters for repetition only if a legal capture exists. `key()` temporarily tests the board change directly, without calling push/key recursively, and restores the squares in `finally`.

### Promotion

Each promoting move has four versions, Q/R/B/N. The UI lets the human choose; the engine must not silently queen every pawn. Promotion changes the sculpture when the preview commits.

## 6. Undo a complete state, not just a piece

`push` stores board, side, castling, en-passant, counters and whether it appended a repetition key. `pop` restores them. Copying a 64-square list is slower than VICE's incremental bookkeeping but much clearer for a first engine.

Legal-move probing uses `record=False`: temporary legality tests are not real game repetitions. Search uses recorded moves because repetition inside a candidate line can be a draw. Every search push is paired with a pop even when cancelled.

Checkmate/stalemate must be tested before draw counters. Our friendly app auto-claims threefold and fifty-move draws; official claim rules and fivefold/75-move automatic draws differ. Material-only draws are intentionally conservative. Read the README before assuming tournament-complete adjudication.

## 7. Computer play: negamax

Evaluation returns a score in **centipawns from the current side's perspective**. Roughly 100 equals a pawn. We add material plus small centrality and pawn-advance terms; these are heuristics, not a judgement of the position's truth.

If a child position is good for the opponent, it is bad for us:

```text
score(move) = -search(position after move)
best        = maximum score
```

That symmetry is **negamax**. A ply is one player's move; depth 3 is three plies, not three full turns. Mate scores dominate material and include distance so faster mates are preferred.

### Alpha–beta

Alpha is the best value already assured to us; beta is the opponent's cutoff bound. If a branch cannot improve the decision, stop searching it. With correct bounds this changes work, not the minimax answer at the searched depth.

Ordering captures by high-value victim/low-value attacker makes useful cutoffs more likely. Ordering is not a legality test, and greedily taking the biggest piece is not the whole search.

### Quiescence

Stopping on a queen capture before seeing the recapture is misleading. At ordinary depth zero, continue tactical moves—captures and promotions. If in check, search evasions rather than pretending a static position is safe. The extension is capped at eight extra plies to avoid runaway checking sequences; this is a playing-strength compromise.

### Iterative deepening and cancellation

Search depth 1, then 2, then 3, keeping only the best result from a **completed** iteration. A legal fallback exists if time expires before depth 1. The recursive functions check a monotonic deadline and stop Event; try/finally restores the board when interruption unwinds recursion. Search clones its input, so even a cancelled worker cannot corrupt the displayed position.

We omit transposition tables, opening books, null-move pruning and many VICE optimisations. Copying fewer lines does not mean matching VICE's strength.

## 8. Pygame without a 3D package

Meshes are polygons built from original coordinates. `lathe` spins a radius/height outline into rings. Coloured solids form armoured pawns, mounted riders, robed staff-bearers and crowned royalty; the rook remains a moving siege tower. Small arm, foot, ram and body transforms make them more expressive without importing skeletal animation.

2D uses hand-drawn Staunton-style vector silhouettes with stepped bases, mitres, crowns and a king cross, not a font-dependent chess glyph. `App.view` is either `2d` or `3d`. `project` and `square_at` dispatch through that same mode; drawing and hit testing must never disagree. The View button / V changes only this presentation field, not the position, search or animation time.

For board-relative u/v and height z:

```text
rotated_u = u × cos(yaw) - v × sin(yaw)
rotated_v = u × sin(yaw) + v × cos(yaw)
screen_x = centre_x + (rotated_v - rotated_u) × 46 × zoom
screen_y = centre_y + (rotated_u + rotated_v) × 46 × tilt × zoom - z × 49 × zoom
```

Before projection, the camera rotates the board-plane coordinates by yaw using sine/cosine. Zoom multiplies the drawing scale; tilt changes ground foreshortening. The inverse mouse transform first removes scale/tilt, then applies the inverse yaw, and finally removes the board flip. Keep these operations in reverse order or clicks will drift from the pieces. Tilt is clamped away from zero, where the inverse would become singular.

This is an adjustable **parallel projection**, not perspective: distant pieces do not shrink. Projected depth sorts pieces rear-to-front; simple face shading varies their colours. This painter approach has overlap limitations and is not a GPU depth buffer.

Clicking reverses the board-plane equations and rounds to the containing square. It deliberately selects square bases rather than potentially overlapping piece heads. Flipping negates u/v consistently in drawing and hit testing.

## 9. An animation is a preview, not a move yet

`animate` stores a legal Move, before-board, victim square and timer. Pure `animation.pose` returns a presentation description: interpolated file/rank, lift, facing, attack strength, victim fall and named phase. It cannot edit the chess position.

```text
normal move: smooth travel + step/bob (knight: larger hop)
capture: approach → wind-up → impact → recovery onto victim square
```

Smoothing uses `p² × (3 - 2p)` to slow the ends. Captures approach to 72% of the path, stay short during the strike, and finish after the victim starts falling. The impact is at 60% of duration; it triggers one sound and starts victim collapse. `STYLES` maps each attacker to a name, duration and sound. Shield bash, mounted charge, spell, ram, lightning and sword effects are original procedural designs, not extracted Battle Chess sequences.

The renderer applies pose fields to either an icon or a character. Spell/lightning effects use a jagged line and ring; sword/charge use arcs; physical strikes use shock rings. Both views draw the same elapsed state. No view toggle can restart a move or trigger a second capture sound. All victims currently share the same fall; adding 36 unique pair-specific fights would be a much larger art project.

Castling interpolates the rook as well. En-passant uses its actual captured square. At the end the controller pushes the Move **once**, refreshes rules and starts the other turn. Undo cancels a preview; in AI mode it also rewinds an already committed human move when needed.

## 10. Thread ownership and sound

Only the main thread changes the app and draws Pygame. One executor worker receives a cloned position and returns a SearchResult. New, undo, side and mode changes set its cancellation Event and discard its future, preventing a stale reply from entering a fresh game.

A recipe per piece/attack specifies frequency, duration, sweep, noise and pulses; the tests verify these generated sample buffers differ. Audio uses signed 16-bit samples in `array('h')`, combining sine waves and seeded noise with a fading envelope. Generated samples are original; no commercial recordings are loaded. A missing device is handled without stopping the game. `--mute` skips initialisation entirely.

### Hints reuse search without making a move

The Hint button / H submits the same cloned-position search with `search_kind="hint"`. When it finishes, the controller records `hint_move` and selects its source, but never calls `animate` or `push`. The renderer outlines both squares in gold in either view. A normal AI result instead starts an animation. Separate result handling prevents a hint from accidentally playing your turn. Cancellation/new-game rules apply to both job kinds; duplicate requests and requests during moves/promotions are ignored. The suggested move can be weaker at a short search budget, so the UI does not promise it is best.

## 11. Test rules, not just a playable demo

**Perft** counts every legal leaf after a fixed number of plies. Known exact counts expose subtle castling, pin and pawn bugs. Never change a published expectation merely because an implementation returns a nearby number.

The tests verify exact start/Kiwipete/endgame counts, special moves, key restoration, checkmate, draw policy, timeout fallback, AI hand-off, animation commits and undo. Headless rendering tests use SDL's dummy driver; they cannot certify appearance on all screens or playing strength.

Exercises:

1. Follow e2e4 through selection, preview, push and pop; print its FEN each step.
2. Add perft depth 4 from the start: the expected count is 197,281. Measure it outside routine UI tests.
3. Construct a pinned en-passant position and explain why a pseudo-legal capture is rejected.
4. Count nodes with capture ordering enabled/disabled without changing rule tests.
5. Add a new original capture effect in the renderer and pose table. Prove the final FEN stays identical.
6. Add a transposition table only after tests cover side, castling, legal en-passant and draw context in position keys.

Source and rights references are in [SOURCE_NOTES](SOURCE_NOTES.md) and [README](README.md#references-and-rights).

### Click versus drag

A left press on the 3D board delays selection until release. Movement below five logical pixels counts as hand jitter; larger movement starts an orbit and suppresses the click. After crossing the threshold, each motion event applies its incremental delta, giving continuous yaw/tilt. Focus loss cancels the gesture. Buttons and 2D clicks keep their normal immediate behaviour. The 2D clipping rectangle starts above its top edge (y=94) so it cannot hide the back rank.
