# Classic tabletop presentation and GUI design

## What “match the original” means here

The board matches the **classic English-language game's functional layout**:
15×15 cells; 8 triple-word, 17 double-word including the centre, 12 triple-letter
and 24 double-letter squares; red/pink word premiums, blue letter premiums and
a clear centre star. Premiums use full three-line labels, with a legend below.

The supporting physical metaphors are a green board frame, warm wooden square
tiles, lower-right point values and a seven-tile wooden-style rack. An unassigned
blank has no printed letter; once assigned, its declared letter has zero value
and a persistent small marker. Players, scores and rack privacy remain explicit.
The computer never displays an opponent's private rack.

Commercial editions vary in materials, colours and graphics. This is **not a
pixel-identical replica** or a claim to reproduce licensed branding. All graphics
are original Pygame geometry: no official logo, board scan, textures or tile art.
Matching the familiar physical arrangement does not resolve dictionary/challenge
compatibility limits; see RULES.md separately.

## Applied usability principles

Public references reviewed on 30 October 2026:

- Nielsen Norman Group, [Ten usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/):
  visibility of status, consistency, user control, recognition rather than recall.
- W3C, [Minimum contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
  relative-luminance checks for core text pairs. This web guidance is useful here,
  but does not certify an entire desktop Pygame app as WCAG compliant.

| UI choice | Why |
|---|---|
| Current-turn panel above scorecards | Answers whose action is needed before presenting controls |
| Controller labels and selected-player stripe | Turn/player identity does not depend on colour alone |
| Full premium text and separate legend | Recognisable physical board; abbreviations are explained |
| Square tiles on a visible rack | Makes tile selection and tile point values familiar |
| Separate move-preview card | Errors and valid word scores do not compete with player scores |
| Consistent enabled button fill | Optional actions are not mistaken for disabled actions |
| Filled/hollow state indicator | Additional availability signal besides colour |
| Hover/pressed outline | Immediate feedback for interactive controls |
| Disabled-reason hint | Explains why Play or Exchange is unavailable |
| Draft tint, selection border and Recall | Shows what is provisional and makes cancellation easy |
| Confirmation and privacy dialogs | Prevents accidental pass/quit and avoids exposing next rack |
| Final result replaces preview | No overlapping endgame and ordinary turn messages |

## Drawing architecture

`render_board()` uses the exact `PREMIUMS` data that scoring uses; drawing cannot
silently drift to a different board. `cells` and `rack_rects` are shared by
drawing and click routing. Font-independent polygon geometry draws the centre
star, so it does not depend on a Unicode star glyph being available.

`tile()`, `button()`, `panel()`, `fit()` and `wrap()` are reusable presentation
helpers. No helper changes rules. Shadows and grain are small primitive drawings,
not imported assets. Typography pairs bold **Georgia / Palatino / DejaVu Serif**
headings with **Avenir Next / Trebuchet MS / DejaVu Sans / Arial** body text
(the first installed family wins). The serif gives titles and the current
player's name a bookish tabletop character; the sans-serif keeps instructions,
buttons and scores legible. Tile letters use a separate bold sans-serif role.
Titles of 24 px or larger use the heading role; wrapped prose always stays in
the body role. Fitted labels retain their font family while shrinking.

Font bytes are cached by `(size, role)` with Pygame's bundled default as a
fallback. No font files are added to the repository and no network requests
are needed. Font appearance therefore varies slightly between operating systems.

The fixed logical canvas remains **1180×920**, uniformly scaled/letterboxed on
resize. Coordinates are shown outside the playable grid. Very small windows
still shrink text; this is a desktop layout, not a responsive mobile reflow.
Use a reasonably large window for comfortable premium-label reading.

## Direct manipulation

Human tiles support rack reordering and drag-and-drop between rack and draft
board. A six-logical-pixel threshold preserves click behaviour. The source is
not destroyed during dragging, a floating tile follows the pointer, and valid
targets are outlined. Invalid releases, Escape and window focus loss cancel
without changing committed state. Draft tiles can swap; committed tiles cannot
move. Exchange mode keeps click-based multi-selection instead of ambiguous drag
semantics. See tests/test_drag.py for scaled input and physical tile identity.

## Verification and remaining limitations

`tests/test_design.py` checks premium/star rendering, square rack tiles,
non-overlapping controls, disabled explanations, final-result replacement and
core contrast pairs. Existing tests cover all 225 cell targets, resized input,
blank assignment, privacy and actual moves. Screenshots were also inspected.

Committed word plays now use sequential 650 ms tile flights with 140 ms landing
pauses, on a separate non-blocking presentation timeline. Only played AI tiles
are exposed; the rest of the rack stays private. There is no screen-reader
integration, comprehensive keyboard focus traversal, text-scale setting or sound. Mouse controls and F1/Escape are the
current interaction model. Those limits should not be disguised by calling the
interface universally accessible or by claiming that tests prove visual quality.

### Public game log
A persistent Game log button sits beside New game and Help. A modal page provides
All players / per-player filters, four readable turn cards per page, explicit
Close and Previous/Next controls, plus wheel and keyboard navigation. Word scores,
bonus, turn score and running total have separate visual roles. No private tiles
are exposed. End-of-game rack adjustments are distinguished from turn totals.

### Save / Load
Compact labelled header buttons remain available in the lobby and during play
(Save is disabled until a game exists). Confirmation dialogs disclose the single
local slot, overwrite behaviour, unfinished-draft boundary and private-data risk.
Loading never reveals a human rack automatically. Errors leave the live game
intact; no file chooser or network service is required.
