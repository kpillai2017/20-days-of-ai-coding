# Learn the implementation, one turn at a time

## 1. Run it before reading it

Play a short word across the star. Try an invalid disconnected word, then Recall.
Try a blank, an exchange and a hint. A variable is much easier to understand
when you can relate it to a thing you just clicked.

Read files in this order: `engine.py` → `ai.py` → `main.py` → `ui.py` → `tests/`.
The engine imports no Pygame. That separation is the most reusable lesson here.

## 2. Physical identity is not the same as displayed letter

`Tile` is a frozen dataclass: its letter is A–Z or `?`. `Placed` contains that
physical tile plus the displayed/declared letter. For a blank assigned Q:

```python
from engine import Tile, Placed
blank = Placed(Tile('?'), 'Q')
print(blank.letter)   # Q
print(blank.value)    # 0, NOT 10
print(blank.blank)    # True
```

Never calculate a blank's score using `LETTER_VALUES[blank.letter]`: that would
mistake its assignment for its physical value. The distinction also lets us
count the original 100 physical tiles after many moves.

The board is a dictionary: `(row, column) → Placed`. An absent key is empty.
Rows/columns are zero-based 0–14 in code; the board labels columns 1–15 for play.
The centre star is `(7, 7)`.

## 3. A draft is a transaction plan

A placement dictionary maps a square to `(rack index, assigned letter)`:

```python
from engine import Game, Tile

game = Game([('You', False), ('Computer', True)], {'CAT', 'AT'}, seed=42)
game.current = 0                       # test arrangement, not UI practice
game.players[0].rack = [Tile(c) for c in 'CATXXXX']
plan = {(7,7): (0,'C'), (7,8): (1,'A'), (7,9): (2,'T')}
result = game.preview(plan)
print(result.words, result.score)       # [('CAT', 10)] 10
print(game.board)                       # still empty!
game.play(plan)                        # commit after validating everything
```

The UI never writes letters directly to `game.board`. `pending` is a separate
view-only draft. `preview()` checks bounds, occupied cells, unique rack indices,
tile identity, blank assignments, one-axis placement, gaps, connection and all
formed words. An invalid move raises `ValueError` **before** changing anything.
`play()` previews again, then commits. That is atomic validation: all or nothing.

## 4. Find complete words, not just the new tiles

`_word()` walks backwards to a contiguous run's first tile, then forwards until
an empty square. This finds `CATS` when you merely add S to CAT. For each new tile,
we inspect horizontal and vertical runs and deduplicate their coordinate tuples.
Only runs of at least two tiles are words. A one-tile play can create two words.

Geometry and vocabulary are independent checks. A straight connected placement
can still create an invalid perpendicular cross-word, so all runs must validate.

## 5. Score in the correct order

For every formed word:

1. Read each physical tile's value.
2. Apply DL/TL only if that tile is newly placed.
3. Accumulate DW/TW multipliers only at new squares.
4. Multiply the letter subtotal by the product of word multipliers.
5. Sum all words, then add 50 if exactly seven rack tiles were newly placed.

The centre star is DW, not an extra special-case bonus. Blanks are zero even on
TL, but their DW/TW square still multiplies the word. Old premiums never recur.
Tests use hand-calculated results: CAT opening 10; blank-C opening 4; extending
committed CAT to CATS on plain squares 6.

## 6. Turn order and inventory are invariants

The engine advances the seat **once** after a legal play/pass/exchange. UI code
must not advance it again. Starting draws compare alphabetical order, not point
value: B starts before E even though B is worth more points.

Exchange draws replacements before returning selected tiles. Otherwise the
player could immediately draw their own returned tiles, contrary to this rule.
Seven tiles must already be in the bag, even if exchanging just one.

Useful invariants after any committed action:

```text
bag tiles + rack tiles + board physical tiles = original 100 tiles
all board coordinates are inside 0..14
all racks have at most seven tiles
only the engine changes committed scores and board state
```

An empty bag does not itself finish play. Someone must go out, or the chosen
scoreless-ending rule must trigger. Remaining racks affect final scores.

## 7. A prefix tree makes computer search practical

`Lexicon` loads words once and builds a trie. CAT and CATS share C→A→T, with an
end-of-word marker at T and another at S. Searching the trie rejects impossible
prefixes immediately instead of trying every dictionary word everywhere.

`find_move()` identifies **anchors**: empty squares next to existing tiles, or
the centre on an empty board. It walks possible horizontal/vertical starts,
consuming rack indices at empty cells and following fixed letters at occupied
cells. A blank branches over allowed letters. Perpendicular **cross-checks**
filter letters that would form invalid side words.

Every candidate still goes through `game.preview()`. The AI is not allowed to
bypass rules. A monotonic deadline limits search time; the best found score is
not guaranteed to be the theoretical best. The search sees only the current
rack and public board, not opponents' racks or future bag order.

## 8. Keep the event loop responsive and racks private

`ScrabbleApp.run()` repeats events → update → render → frame cap. AI/hints run in
a `ThreadPoolExecutor`; update checks `future.done()` rather than blocking the
window on `future.result()`. A snapshot isolates the board/racks. A generation
number rejects results belonging to an abandoned game.

Pygame drawing stays on the main thread. Closing shuts down workers, which may
wait briefly for an already-running bounded search. The GIL means threads do not
magically parallelise CPU work; this design is about responsive orchestration.

A handoff dialog is not merely decorative. `rack_revealed` is an explicit
permission reset at every turn. Only the Ready button grants it. Closing another
dialog must not accidentally bypass privacy. Computer racks stay hidden.

The fixed logical drawing surface is scaled and letterboxed. Mouse coordinates
undo that same scale and offset before looking up shared tile/button rectangles.
The original geometric tiles use no commercial art. Font bytes stay in memory
to avoid leaking OS file handles when many sizes/UI tests are created.

### Dragging without corrupting rack identities

A drag has a press point, source rack index, optional source board coordinate,
current pointer and `active` flag. Movement of six logical pixels activates it;
shorter movement keeps ordinary click behaviour. Pressing never removes a tile.
Only a valid release changes the draft or rack order. Escape and focus loss
simply discard the drag state, so cancellation cannot lose physical tiles.

`reorder_rack()` builds an old-index → new-index map and applies it to every
pending placement. Without that remapping, moving rack slots would silently
change which physical tile a draft uses. Draft-to-draft drops swap references;
assigned blanks keep their declaration while moved on the board. Returning a
blank to the rack drops its draft assignment. Existing board tiles never move.

`render_drag()` draws a floating tile and target outline above the table; this
is presentation only. Press, motion and release all undo the same window scale.
Tests send real mouse-down/motion/up sequences, including at a resized window.

### Explain scoring from the same calculation, not a second scorer

`MoveResult.breakdown` records the scorer's letter terms, subtotal, word
multipliers and word total; `bingo` records the separate seven-tile bonus. The
UI renders that trace rather than reimplementing the arithmetic. Tests assert
that the trace sum plus bonus equals the actual committed score.

Board-word inspection walks both axes through a committed square. Meanings
are not gameplay validity: `definitions.py` queries a read-only local SQLite
index. Compressed JSON rows preserve part of speech, source and licence.
A background worker keeps file reads separate from rendering; no network is used.
Every gameplay word has a row, but missing definitions are explicit. Sourced
`form_of` links can add one base-word explanation, with bounded traversal to
prevent cycles. No suffix stripping or AI-generated guesses fill coverage gaps.
`tools/build_definitions.py` demonstrates reproducible streaming extraction of a
large compressed source into a much smaller indexed dataset. See its separate
CC BY-SA provenance notice before modifying or redistributing definition data.

### Animate presentation without re-running rules

`animation.py` contains `TileFlight`, a pure elapsed-time timeline. A committed
move snapshots only played tile identities and their rack/board coordinates.
The engine commits once, then the renderer temporarily hides not-yet-landed
new tiles. One 650 ms flight and 140 ms landing pause run per tile. Smoothstep
easing and a sine arc create a readable path; no blocking sleeps are used.

During playback, human actions and new AI searches are locked. A dialog pauses
elapsed time, so closing it does not skip the remaining flights. The next human
handoff waits until completion. AI snapshots never contain unused rack faces.
Timeline tests advance synthetic timestamps rather than sleeping in real time.

## 9. Tests should challenge the implementation

```sh
python -m unittest discover -s tests -v
```

The standard-library discovery command must actually report a nonzero test
count. Do not mistake a successful “Ran 0 tests” for verified functionality.

Tests here arrange small racks and dictionaries, independently calculate scores,
send real Pygame mouse events and run complete AI games conserving all 100 tiles.
They test rejected moves leave state unchanged and stale worker results cannot
change a new table. Tests are evidence, not proof of every official-edition rule.

## Exercises

1. Add a move-history overlay without exposing future bag order or private racks.
2. Highlight all cross-words in a preview while keeping the engine unchanged.
3. Improve AI rack-leave strategy instead of always chasing immediate points.
4. Implement one specific edition's challenge rules with rollback tests.
5. Add a tournament clock only after documenting the chosen penalty rules.
6. Extend the versioned save system with named slots or a file chooser.

Always read [RULES.md](RULES.md) before treating a digital convenience as a
universal official rule. The dictionary and its separate licence are documented
in [words/NOTICE.md](words/NOTICE.md).

## A public turn history
`Game.turn_history` stores structured snapshots, rather than trying to parse the
human-readable event messages. `_record_turn()` runs once after a legal play or
pass/exchange, before advancing the active player or applying final rack
adjustments. It copies word scores into a tuple and records the mover's running
total. No rack letters or drafts are included.

The interface's `log_entries()` filters these records by player;
`render_turn_log()` shows four turns per page. Pagination is clamped to valid
bounds and resets when a different player is selected. The modal prevents
background board clicks and pauses animation without committing another move.
A new `Game` starts with an empty history. History is included in the JSON saved-game snapshot.

## Persistence: taking a snapshot without running it
`persistence.py` serialises model data into versioned JSON, never `pickle`,
`eval()` or executable code. `snapshot()` deliberately excludes UI drafts and
worker futures. A SHA-256 fingerprint of the sorted word set prevents resuming
with changed word-adjudication rules. Bag order and the PRNG state preserve
future tile draws and exchanges; computer searches remain time-budgeted, so
future AI choices are not guaranteed identical.

Loading builds and validates a separate model first: player counts, coordinates,
physical tile inventory, assigned blanks, turn scores and random state are
checked before the current game is replaced. `Game.__new__` avoids dealing
new racks during restoration. JSON arrays become tuples where required by
`random.setstate()`. This catches corruption, not deliberate cheating: saves
are editable and contain private information.

Writing uses a temporary file in the destination directory, flush + fsync, then
`os.replace` to avoid truncating the previous save on a failed write. Loading
invalidates outstanding AI results, clears drafts, and re-enters the normal
private handoff. Tests cover successful round trips and failures.
