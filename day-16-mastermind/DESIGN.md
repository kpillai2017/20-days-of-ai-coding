# Tabletop presentation and interaction design

## Visual language

The board evokes a classic moulded brown Mastermind tray without copying a
commercial photograph or exact packaging. Rounded outer walls, a highlighted
rim, recessed wells, corner screw details and raised rails create depth. Rows
run from the player's end (01, bottom) toward the shield (10, top). Four large
code holes are separated from a 2×2 group of small feedback holes.

Code pegs use a darker stem/base, coloured domed head, cast shadow and small
upper-left reflection. Feedback pins use the same drawing routine at a smaller
scale. The closed secret shield covers the entire code row; at round end it is
removed to expose the four pegs. This is procedural **2D shading**, not a 3D
mesh, exact replica, draggable physical peg model or simulation of light.

A dark slate background and warm ivory type separate controls from the brown
board. Serif headings give a tactile tabletop feel; sans-serif body labels keep
rules and instructions readable. Font fallbacks use installed families and
Pygame's default; no fonts are downloaded or copied into the repository.

## Visible state and layout

- An outlined gold row shows the active attempt; previous rows are immutable.
- A gold focus ring marks the keyboard hole and selected palette colour.
- Submit is disabled until all four positions are filled. Disabled buttons have
  subdued styling and no active hit target.
- Two score cards always show cumulative maker points. Current roles, round and
  instructions are separated above the palette.
- Feedback groups carry counts, never arrows aligning them to guessed positions.
- Letter marks R/Y/G/B/W/K supplement colours. Black uses K so B remains blue.
  They are an aid, not a claim of certified colour-blind or screen-reader access.
- Modals shade the background AND remove its hit targets. Privacy curtains are
  preserved when help/quit confirmation covers them.
- Escape/window close asks before discarding progress. There is no autosave.

## Resolution and input

Design coordinates are 1180×920. The scene scales proportionally with letterbox
margins; mouse coordinates are transformed back before hit testing. The minimum
window request is 590×460, where text and targets become smaller; desktop-size
use is recommended. Pygame is not a native semantic accessibility interface.

## Architecture

`engine.py`: validated codes and a four-phase match state machine. `ai.py`:
candidate filtering and candidate-only minimax. `ui.py`: rendering and input,
plus a worker executor for search. `main.py`: CLI options and launch.

Search gets immutable copies of only public candidates and previous guesses,
not the match or secret. A generation counter discards results from an abandoned
match. Modal pages pause applying AI results; no additional guess occurs behind
a curtain. All Pygame drawing stays on the main thread. The worker is shut down
on exit. Computer makers use the model's seeded random generator.

## Motion and manipulation
Four sequential curved peg flights use smoothstep interpolation and a gentle
arc, with visible landing pauses. Feedback waits until all pegs land. Human-placed pegs commit in place; only computer turns replay a flight. Secret computer flights are neutral-backed
and originate independently of code colours, disappearing under the shield.
Modals pause motion. Draft-row drag/drop swaps occupied holes, moves into empty
holes, highlights a valid target, and cancels outside the row or on focus loss.
No committed row is editable; click-to-replace is retained below a six-pixel
drag threshold. There is currently no speed slider or reduced-motion toggle.

### Drag from the colour bank
Press a bank peg, drag it to any active hole and release to place or replace a
draft peg. The bank remains available for repeats. Dropping outside the active
row cancels; a short click simply selects the colour. Within the row, drag to
swap occupied holes or move into an empty one. Human draft pegs are already on
the board, so Submit/Lock commits them **without another flying animation**.
Feedback appears immediately after a human guess. Computer turns retain slow,
sequential flights and delayed feedback. Existing mouse/keyboard placement still
works and also commits in place. Previous submitted rows cannot be edited.
