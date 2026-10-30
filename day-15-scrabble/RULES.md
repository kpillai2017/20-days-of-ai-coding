# Rules profile and edition boundaries

“Original rules perfectly” needs an edition and an agreed dictionary. Scrabble
has different dictionaries, challenge rules, scoreless-ending conventions and
tie-breaks across households, countries and tournament organisations. This
project implements the following **classic-English digital profile**, not every
historical or tournament edition. Read these choices before play.

## Implemented physical rules

- A 15×15 board, 100 English tiles including two blanks, and seven-tile racks.
  Exact counts and values are explicit in `engine.py` and independently tested.
- Premium squares: **8 TW, 17 DW including the centre, 12 TL and 24 DL**.
  Premiums are symmetric and only affect newly placed tiles. The centre is DW.
- Choose 2–4 players. Draw for first player: closest letter to A wins, blank
  before A. Only tied lowest seats redraw. Return those tiles before filling
  racks; preserve the other players' clockwise seat order.
- First word covers the centre. Every word has at least two letters. New tiles
  must occupy a single row or column, without gaps after existing tiles are
  included. Later moves connect orthogonally to the existing board. No diagonals.
- Each newly formed horizontal or vertical word must be in the selected lexicon.
  Extensions use the complete resulting word, not just the new suffix. A one-tile
  move may create and score two words; identical coordinate sequences count once.
- Count letter values, apply each new letter premium, then multiply all new
  word premiums together. Score all cross-words using the same rules. A blank
  always contributes zero, but its word premium still multiplies the word.
- An assigned blank keeps its letter for the remainder of play; it cannot be
  picked up and replaced by a matching letter from the rack.
- Seven **new** tiles on one turn add 50 points. A shorter final rack does not
  earn this bonus simply because it was emptied.
- After committing, draw up to seven while the bag has tiles. The UI never
  advances the turn a second time after the engine advances it.
- A player can exchange selected tiles only with at least **seven tiles already
  in the bag**. Draw replacements before returning the selected tiles; an
  exchange consumes a turn. A pass also consumes a turn. Rack shuffling does not.
- Empty-rack/empty-bag finish: opponents deduct their remaining tile values; the
  finisher gains the total opponents deducted. Blanks deduct zero.

## Deliberate digital choices and remaining compatibility limits

1. **Dictionary:** the bundled CC0 Letterpress list combines US, UK and Australian
   spellings and is not Collins/CSW, NWL or an official Scrabble dictionary.
   Accept/reject results will differ from those dictionaries. Supply your own
   legally obtained word-per-line dictionary with `--dictionary` to change it.
   A separate offline Wiktionary extract supplies meanings for 92.2% of the gameplay list, but never decides word legality. There is no proper-noun classifier or content filter.
   The selected file determines validity, including unusual or offensive entries.
2. **Automatic adjudication:** every formed word is checked before a move can be
   committed. Invalid drafts cost no turn. There is **no post-play challenge or
   challenge penalty**. This differs from physical editions where players may
   bluff a word and opponents may challenge, sometimes risking a turn.
3. **Stalled ending:** six consecutive scoreless turns end this profile. Passes,
   exchanges and zero-point plays count; a positive score resets the counter.
   All remaining rack values are deducted, with no finisher bonus. Some physical
   sets use “all possible plays have been made” or a different scoreless rule;
   a finite pass count is not an algorithmic proof that the board has no moves.
4. **Ties:** equal final adjusted scores yield joint winners. Some official rules
   break ties using pre-adjustment scores; that tie-break is not implemented.
5. **Timing:** there is no tournament clock, overtime penalty or tournament
   director. Hints are optional assistance, not a tournament-legal feature.
6. **AI strength:** the computer's time-limited trie search can miss a legal or
   higher-scoring move. If none is found, it exchanges when legal, otherwise
   passes. It cannot secretly see opponents' racks or draw preferred tiles.
7. **Convenience features:** local JSON save/load is available; no online multiplayer or undo after a
   committed move. These do not change score calculation but limit the product.

These differences mean the project must **not be described as “official rules
perfectly” or tournament-complete**. The move/scoring engine is separately tested
and designed for extensions. Adding challenge handling or a specific licensed
lexicon should start with the exact edition rules and new regression tests.

## Score examples

- `CAT` across the empty centre: `(3 + 1 + 1) × 2 = 10`.
- A blank representing C in that opening: `(0 + 1 + 1) × 2 = 4`.
- Extending that committed `CAT` to `CATS` on plain squares: `3 + 1 + 1 + 1 = 6`;
  the old centre's DW does not apply again.
- Two words crossing at a new double-letter T: its value is doubled separately
  within each word scored on that turn.
- `RETAINS`, all seven new tiles across the centre on plain-letter squares:
  `7 × 2 + 50 = 64`.
