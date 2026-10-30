# Day 16 — Mastermind: The code table

A local, two-player Python/Pygame code-breaking game with original, shaded
plastic-style artwork: a brown moulded tray, recessed sockets, six coloured
code pegs, small black/white feedback pins and a shielded secret compartment.

**Edition:** four positions, six colours, repeats allowed, ten guesses, no empty
holes as a seventh colour. Maker scoring is guesses used plus one for an
unsolved code. These are the traditional rules selected for this implementation,
**not a claim of perfect compatibility with every commercial edition**. See
[RULES.md](RULES.md): published boards differ in row counts and scoring.

## Install and run

Python **3.9+** and a graphical desktop are required. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, use `python` instead of `python3` if appropriate. If Pygame cannot
open a display, run locally in a desktop session, not a bare remote shell.

```sh
python main.py --seed 42              # reproducible computer secrets
python main.py --demo                 # two computer controllers
python main.py --demo --frames 10     # automated launch check, not a full match
python -m unittest discover -s tests -v
```

No network connection, downloads or API keys are needed at runtime. The root
`.gitignore` excludes virtual environments and bytecode. There is no save/load,
network multiplayer, audio or commercial artwork bundled.

## Set up your table

- Exactly **two seats**, independently Human or Computer. Human/Human,
  Human/Computer, Computer/Human and Computer/Computer all work.
- Click a name to edit it (up to 24 printable characters). Names must differ.
- Choose **1–5 maker rounds per player**. The default is two rounds total.
- Seat 1 is maker first. Roles alternate, so every player has equal opportunity
  before cumulative scores are compared. Round transitions are explicit even
  in the computer demo: click Next round / Show match result.

## Controls

| Action | Control |
|---|---|
| Select a colour | Click a palette peg or press **1–6** |
| Place a peg | Click one of the four active holes, or press **Space** |
| Move keyboard hole focus | **Left / Right** |
| Remove a peg | Right-click its hole; **Backspace / Delete** removes focused peg |
| Lock secret / submit full guess | Button or **Enter** |
| Empty the draft row | **Clear row** |
| Confirm private handoff | **Ready** or **Enter** |
| Help | **F1** or Help button |
| Close | **Escape** or window close, then confirm |

Colour indices are **1 Red, 2 Yellow, 3 Green, 4 Blue, 5 White, 6 Black**.
Small letter marks R/Y/G/B/W/K distinguish colours (K means black). Feedback
pins are smaller and grouped separately: **black = exact**, **white = colour
only**. Their order does **not** identify which code positions matched.

Rows run from **01 at the bottom to 10 at the top**. Only the active row can be
edited; previous guesses are permanent. Submit is disabled until all four holes
are filled. The secret is revealed only when the round finishes.

### Hot-seat privacy

When a human makes a code, ask the breaker to look away. A Ready curtain appears
before entry and another curtain covers the board before the breaker takes over.
Help/close confirmations preserve the curtain. This is shared-screen etiquette,
not encryption: anyone watching over the maker's shoulder can see the secret.
Computer makers choose a uniformly random code; computer breakers receive only
public guesses and feedback. The full model necessarily stores the secret to
score it, but it is not passed to the solver.

## Learn how it works

Read [rules and examples](RULES.md), then the
[beginner code tour](LEARNING_GUIDE.md),
[visual/interaction design](DESIGN.md) and [references](REFERENCES.md).

| File | Responsibility |
|---|---|
| `engine.py` | Valid codes, duplicate-safe feedback, phases and maker scores |
| `ai.py` | Candidate filtering and candidate-only minimax |
| `ui.py` | Original artwork, input, privacy curtains and background search |
| `main.py` | Arguments and launch |
| `tests/` | Rules, solver and headless interaction tests |

## Rights

Original implementation, procedural artwork and prose use the repository's
[MIT licence](../LICENSE). Pygame is a separately installed LGPL dependency.
System fonts have their own terms and are not redistributed; Pygame's bundled
font is a fallback. Mastermind is a third-party game name/trademark; this is an
independent educational implementation, not an official product. No commercial
board scans, logos, packaging, recorded samples or game code are copied.
Educational purpose is not a claim of universal legal permission.

## Peg flights and drag swapping
Computer guesses fly from the colour bank to the board
**one peg at a time**: 650 ms per flight and 140 ms landing pause (about 3.2
seconds for four pegs). The move commits once; feedback and any round result
wait until the last landing. Entry controls are locked during flight. Help and
confirmation dialogs pause the timeline without skipping ahead on resume.

Human placements commit in place without a second flight. Computer secret pegs use neutral backs and fixed source
slots, disappear beneath the closed shield and never expose colours or repeats.

Drag a placed **draft peg in the active row** to another hole: occupied targets
swap colours; empty targets move the peg. This also works while a human maker
is choosing a secret. Drops outside the row cancel. Escape or loss of window
focus cancels a drag without changing the draft. Committed previous guesses
cannot be moved. A short click still replaces a peg with the selected colour.

### Drag from the colour bank
Press a bank peg, drag it to any active hole and release to place or replace a
draft peg. The bank remains available for repeats. Dropping outside the active
row cancels; a short click simply selects the colour. Within the row, drag to
swap occupied holes or move into an empty one. Human draft pegs are already on
the board, so Submit/Lock commits them **without another flying animation**.
Feedback appears immediately after a human guess. Computer turns retain slow,
sequential flights and delayed feedback. Existing mouse/keyboard placement still
works and also commits in place. Previous submitted rows cannot be edited.
