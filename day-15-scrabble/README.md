# Day 15 — Scrabble

An original Python + Pygame tabletop implementation for **2–4 local players in
any human/computer combination**, with private human racks, move previews,
computer opponents and hints. It runs offline after installing pygame.

**Rules boundary:** classic English board geometry, tiles and scoring are
implemented, but this is not a claim of perfect official-edition compatibility.
The bundled CC0 dictionary is **not Collins or NWL**, invalid words are rejected
automatically (no challenge penalties), and six consecutive scoreless turns end
the game. See [RULES.md](RULES.md) before comparing a physical edition.

## Install and run

Python **3.9–3.13** and pygame **2.6.1**:

```sh
cd day-15-scrabble
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows PowerShell: `.venv\Scripts\Activate.ps1`. Use `python` if your platform
has no `python3` command. No API keys, accounts or telemetry. Gameplay, validation and definition lookup are offline. No runtime network
requests are made when clicking words.

```sh
python main.py --seed 42                # reproducible tile draws
python main.py --demo                   # four computer players
python main.py --demo --frames 10       # exit after 10 frames, NOT 10 FPS
python main.py --dictionary mywords.txt # your legally obtained word list
```

A custom dictionary contains one word per line. Only ASCII letters A–Z of
length 2–15 are loaded, case-insensitively. Empty dictionaries fail with a clear
error. Word validity is always against the selected file, never an online API.
The bundled Letterpress list contains obscure and potentially offensive words;
no child-safe filter or official tournament validity is promised.

## Board and interface

The board follows the familiar classic premium arrangement and red/pink/blue
premium scheme, with full premium labels, a centre star and coordinates. Wooden
square tiles sit on a visible seven-tile rack. Scores, controller type, move
validation and actions have separate panels. Filled action dots mean enabled;
hollow dots and muted styling mean unavailable. Hover over a disabled control
for an explanation. Original graphics are not copies of commercial artwork.
See [DESIGN.md](DESIGN.md) for the design principles, references and checks.

## Start a game

Click each of four seats to cycle **Human → Computer → Off**. Choose at least
two active seats. Each Human seat has an **edit name** button. Enter a distinct
name (1–20 characters), then **Save name** or press Enter. Escape/Cancel keeps
the previous name. Unicode input is supported where the system font has glyphs;
Ctrl/Cmd+A selects all and Backspace edits. Names persist while cycling a seat's
controller during this session. Computer seats retain their numbered names.
Start the game; chosen names appear in scores, handoffs and the journal. The closest alphabetical starting draw wins
(blank before A), ties redraw, and the remaining seats stay in clockwise order.
Each player then receives seven tiles.

At every human turn a **Pass the screen** overlay hides the rack until that
player clicks **I am … · show my rack**. This is hot-seat privacy, not online
multiplayer or protection against somebody looking over your shoulder. Computer
racks are never displayed. All-human and all-computer tables are supported.

## Place and score a word

1. Click a tile in your rack, then an empty board square. Repeat for the word.
2. A blank asks you to select A–Z. It retains that letter and scores zero.
3. Click a provisional board tile to put it back, or **Recall draft** to undo
   the whole draft without using a turn. Existing committed tiles cannot move.
4. The first word must cover the star. Later words connect to the existing board.
   All new tiles lie in one row/column, with no unfilled gaps. Existing letters
   can bridge the new tiles.
5. The right panel shows every newly formed word and its score, or explains why
   the draft is invalid. **Play · N pts** enables only for a valid draft.
6. Play commits the whole move, fills the rack if possible and changes turns.
   There is no partial commitment or second turn advance in the UI.

**DL/TL:** double/triple a newly placed tile's value. **DW/TW:** multiply a whole
formed word. Occupied premiums never apply again. A tile can count in two words
on the same turn; premiums apply to each of those words. Seven newly placed
tiles earn a **50-point bonus**. A green dot identifies an assigned blank.

The persistent **Last play** strip at the bottom shows who played, every word
formed (including cross-words), individual word scores and the move total.
It retains the last word play after a pass/exchange and also labels that latest
turn, so a skipped turn does not erase the word you were reviewing.

## Word meanings and human score calculations

Click any **committed board letter** to inspect its complete word. At an
intersection, **Other crossing word** switches between horizontal and vertical
words. The CC0 list stays the gameplay dictionary; it contains no definitions.

Meanings load **automatically from the bundled local dictionary**. No online
lookup or consent button is needed. The file indexes all 270,652 gameplay words;
249,527 (92.2%) have sourced glosses or documented form references, and 21,125
explicitly report no local definition. Some glosses are references such as
“plural of …”, not standalone explanations; available source-recorded lemma
meanings are shown too. Nothing is guessed or generated to fill missing entries.

Definitions come from Wiktionary via Kaikki and are **CC BY-SA 4.0**, separately
from the CC0 gameplay list. The panel displays source/licence attribution. See
[definition provenance and exact coverage](words/DEFINITIONS_NOTICE.md), including
how to rebuild the approximately 74 MiB local SQLite file. Definitions can include
archaic, offensive or capitalisation-specific senses and are not context-aware.

For every valid human draft, the preview shows the points sum. **Show step-by-step
calculation** opens the exact scoring trace: tile values (blank = 0), new DL/TL,
letter subtotal, new DW/TW multipliers, each main/cross-word score, seven-tile
bonus and total. **Next calculation** covers every word formed on that turn.
Inspecting either panel pauses computer play and does not commit the draft.

## Drag-and-drop

- **Within the rack:** hold a tile and drag it onto another rack slot to move
  it into that position; intervening tiles shift. Draft tile references stay
  attached to their correct physical tiles after the rack order changes.
- **Rack → board:** drag onto an empty square to stage a tile. A blank still
  asks for its declared letter before placement.
- **Within the board:** move only your current, uncommitted draft tiles. Drop
  onto another draft tile to swap them. Committed tiles remain fixed.
- **Board → rack:** drag a draft tile onto a rack slot to recall and reposition
  it. Returning an assigned blank to the rack removes its provisional assignment.
- **Cancel:** release outside a valid target, press Escape during the drag, or
  switch away from the window. No tile is lost and no turn is consumed.

A small movement threshold distinguishes a drag from a click. Ordinary
click-to-select/place and click-a-draft-to-recall still work. Dragging is disabled
for computers, hidden racks, dialogs, searches and exchange selection mode.
A floating tile and highlighted target show the current drag destination.

## Animated word plays

After any human or computer commits a legal word, its new tiles fly from their
rack slots to the board **one at a time**, in board order. Each flight takes
about **650 ms**, followed by a **140 ms** landing pause. A curved path and
smooth easing make each placement easy to follow. Committed existing tiles
never move; passes and exchanges do not fabricate a word-placement animation.

Only played tiles are revealed during a computer animation; unused rack tiles
remain hidden. Human handoff appears after the last tile lands. Turn controls
are locked during playback, dialogs pause it, and starting a new game discards
old flights. Rules and scores commit once before playback: animation cannot
score twice or consume a second turn.

## Other controls

- **Exchange tiles:** enabled with at least seven tiles in the bag. Enter
  exchange mode, click the rack tiles to return, then **Confirm exchange**.
  The new tiles are drawn before the returned tiles re-enter the bag. This
  consumes a turn. **Recall draft** cancels exchange mode.
- **Pass turn:** asks for confirmation; recalls a draft and consumes a turn.
- **Shuffle rack:** recalls the draft and rearranges the current rack; no turn.
- **Find a hint:** searches in the background and stages a suggested draft.
  You still choose Play or Recall. It is a best-found move, not a proven optimum.
- **Help / F1:** instructions. **New game:** asks before abandoning a table.
- **Escape:** dismiss a dialog, otherwise ask before quitting. During a private
  handoff, it opens a safe quit dialog rather than exposing the rack.
- Window close also asks. Use Save game before closing; there is no autosave.

AI and hints use a prefix tree and cross-word checks with a roughly 1.4-second
search budget. The window stays responsive. Closing may wait briefly for an
already-running worker to finish; old results cannot mutate a new game.
The logical canvas is 1180×920, uniformly scaled/letterboxed when resized.

## Ending

When a player empties their rack with an empty bag, all opponents lose the value
of tiles they retain and the finisher gains that total. Six consecutive scoreless
turns (pass, exchange or zero-point play) also end the chosen rules profile;
all rack values are then subtracted without a finisher bonus. Highest score wins;
equal final scores are reported as tied winners. See edition limits in RULES.md.

## Learn the code

| File | Purpose |
|---|---|
| `engine.py` | Immutable tiles, board premiums, validation, scoring and turn accounting |
| `ai.py` | Dictionary loading, prefix tree and legal move search |
| `ui.py` | Original graphics, drafts, privacy dialogs and background worker orchestration |
| `main.py` | CLI, dictionary selection and launch |
| `tests/` | Independent scoring, complete AI games and real Pygame interactions |
| `definitions.py` | Read-only local definition lookup, without runtime network access |
| `tools/build_definitions.py` | Reproducible filtering of a downloaded Wiktionary extract |
| `words/NOTICE.md` | Gameplay-list source and CC0 licence |
| `words/DEFINITIONS_NOTICE.md` | Definition attribution, CC BY-SA licence and measured coverage |

Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md) for a step-by-step code tour and
[REFERENCES.md](REFERENCES.md) for rules, programming resources and rights notes.
All application methods are commented/docstringed for learners.

## Tests

```sh
python -m unittest discover -s tests -v
```

Headless smoke run on Linux/macOS:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --demo --frames 10
```

Tests cover geometry, cross-words, premium reuse, blanks, inventory conservation,
private-rack handoffs, actual click routing and complete computer games. Tests
are evidence, not proof of flawless implementation of every official edition.

## Rights

Scrabble is a trademark of Hasbro in the US/Canada and Mattel in other territories.
This independent project is not affiliated with or endorsed by either. No
commercial board scans, logos, tile artwork, official dictionaries or sound
recordings are bundled. Graphics are original geometric drawings. Original
code/prose use the root MIT licence; the gameplay word data uses **CC0** and the definition database uses
**CC BY-SA 4.0** with attribution/share-alike obligations; pygame has separate LGPL terms. MIT does not grant trademark or
other third-party rights. See root THIRD_PARTY_NOTICES.md and words/NOTICE.md.

### Game log
Click **Game log** to see every completed turn, for humans and computers. Filter
by player or choose All players. Each entry lists all words and their individual
scores, any seven-tile bonus, the move total and that player's running total.
Passes and exchanges appear as zero-point turns without revealing rack tiles.
Use Previous/Next, the mouse wheel, or arrow/Page Up/Page Down keys to navigate;
Close or Escape returns to play. Opening the log pauses tile flights and prevents
the next computer turn from starting. Drafts and rejected moves are not logged.
At game end, final scores are shown separately from turn totals because leftover
rack deductions (and the going-out award) are end-game adjustments.

### Save and resume a game
Use **Save game** in the top-right header, then confirm. **Load game** is
available both in the lobby and during a game; confirm before replacing your
current session. There is one save slot: `day-15-scrabble/saves/game.json`,
resolved relative to the program rather than your terminal's working directory.
Saving again replaces that slot. Copy the file elsewhere for additional backups.

The save includes the committed board (including blanks' assigned letters),
player names/controllers/scores, private racks, ordered bag, active player,
scoreless-turn counter, full turn log and random-generator state. Unplayed
drafts, hints, open dialogs and animation progress are not saved. A move already
committed during a tile animation is included; loading shows its finished board.
The next human must confirm their identity before their rack is revealed.

Saves are **plain JSON, not encrypted**: do not share them mid-game. The saves
folder is excluded from Git. Keep the same dictionary: loading rejects a
different word set. Invalid or unreadable files show an error without replacing
your live game. There is no autosave; save before closing.
