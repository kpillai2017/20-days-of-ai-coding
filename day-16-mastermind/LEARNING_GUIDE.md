# A beginner's tour: from a peg to a deduction

## 1. Run before reading

Install and launch using the README. Try a human maker against a computer,
then swap roles. Predict the feedback before submitting repeated-colour guesses.
The program is separated into rules, strategy and graphics so each idea can be
studied without understanding the whole application at once.

## 2. Represent a physical board with data

Colours are integer indices 0–5. A code is a tuple such as `(0, 0, 2, 3)`:
Red, Red, Green, Blue. The interface labels colours 1–6 for people, but subtracts
one for Python's zero-based indices. An unfinished UI row contains `None` for
empty holes; that is NOT a legal colour. `validate_code()` rejects it.

Tuples cannot be edited in place. `set_secret()` freezes a copy of the UI draft,
so later clicking a palette cannot change the already locked code. Players are
small dataclass records containing a name, controller and cumulative score.

## 3. Feedback without double counting

In `engine.score()`, `zip` pairs positions and `sum(a == b ...)` counts exact
matches. `Counter` counts colours. Intersecting counters keeps the smaller
count of each colour. Their sum is the total overlap; subtract exact matches to
obtain white pins. This is why guessing four reds against two reds cannot earn
four red matches. Black and white pins are counts only, never position clues.

Exercise: compute secret R R G B versus R G R Y by hand. Trace the two Counters,
their intersection, black count and white count. Then write another unit test.

## 4. State machines prevent illegal actions

A match moves through **setting → guessing → round_over**. Advancing either
starts another setting phase with roles swapped or enters **match_over**.
Only `submit_guess()` appends a guess. It validates BEFORE mutation, then awards
maker points only when ending a round. Calling submit again in round_over raises
an error, preventing duplicate scoring. A first-guess solution awards one maker
point; ten failed guesses award eleven. Highest total wins after equal roles.

The interface stores temporary selection separately. `commit()` calls the
engine and displays a useful message if a draft is incomplete. Button disabling
helps the user, but engine validation is still essential for tests/other callers.

## 5. Teach a computer using elimination

`all_codes()` uses `itertools.product`: 6 × 6 × 6 × 6 = 1,296 possibilities.
After a guess, `filter_candidates()` asks of each hypothetical secret: would
it give exactly this public feedback? If not, discard it. The actual secret is
never an argument to `choose_guess()`.

The first guess is R R Y Y. Later, candidate-only minimax tries each remaining
candidate as a possible guess, groups hypothetical secrets by feedback and
measures the largest group. Prefer the guess with the smallest worst group.
Ties use deterministic colour ordering. The inner loop stops early when a guess
cannot beat the best already seen. This is not a full Knuth implementation and
has no claimed five-guess guarantee. It trades a little strategy sophistication
for transparent, small code.

Exercise: change the deterministic tie break, then measure guesses across seeded
secrets. Do not let a solver read `match.secret`: that would be cheating, not AI.

## 6. Make flat circles look like plastic

Read `ui.peg()`. A shadow shifted downward suggests height. A dark base suggests
a stem. Several nested lighter circles create a rounded head; a tiny bright
ellipse suggests a light reflection. `socket()` reverses lighting: a dark centre
looks recessed, with a lighter lower rim. Small pins and large pegs reuse these
ideas at different sizes. No textures or imported images are necessary.

`render_board()` maps row r to `y = 752 - r*54`, so later attempts go upward.
It paints committed guesses from the engine and the current draft from the UI.
The secret is drawn only while its human maker is entering it or after the round
ends; otherwise the code compartment is covered by the shield.

## 7. Events, resizing and privacy

The event loop polls input, calls `update()`, draws, then caps at 60 frames/sec.
Rendering does not change the rules. Window positions are mapped into the fixed
design coordinates by undoing scale and letterbox offsets. Modal screens remove
background buttons and holes so a click cannot pass through the shade.

Human-maker Ready and breaker Ready curtains protect hot-seat handoff. Help and
quit overlays remember which curtain was covered. This is visual privacy only;
a shared-screen observer or debugger is not a secure adversary.

## 8. Keep expensive search off the drawing thread

A `ThreadPoolExecutor` runs minimax on copies of candidates and guesses. The
main thread checks whether the Future is done and only then commits a result.
The generation counter distinguishes old abandoned matches. No Pygame calls run
inside the worker. Threads keep the event loop responsive but are not a promise
of faster CPU computation in Python. `finally` shuts the worker/display down.

## 9. Test small facts and real interactions

Run `python -m unittest discover -s tests -v`. Rules tests need no Pygame. UI tests
set SDL dummy drivers before initialising Pygame, click actual button rectangles
and check privacy/phase changes. Headless rendering catches API errors but does
not replace a human visual review on a real display.

Useful extensions: named save files, optional texture-free sound effects,
separate edition presets with documented scoring, or compare candidate-only
minimax with full-space minimax. Add tests before changing rule assumptions.

## Presentation clocks and reversible dragging
`animation.PegFlight` stores elapsed presentation time, independently of rules.
`begin_flight()` commits once and snapshots the played code; rendering reveals
only landed pegs and delays feedback/results. Modal time is excluded by updating
the last tick while paused. `finish_flight()` opens any required private handoff.
Neutral computer-secret flights must not encode colours even in their origins.

A drag starts with source index, pointer origin and an activation flag. Six
logical pixels distinguish a drag from a click. The draft is untouched until a
valid drop; swapping two list entries atomically handles both occupied and empty
targets. Outside drops, Escape and focus loss therefore require no rollback.
Scaled mouse positions use the same logical-coordinate mapping as clicks.

### Drag from the colour bank
Press a bank peg, drag it to any active hole and release to place or replace a
draft peg. The bank remains available for repeats. Dropping outside the active
row cancels; a short click simply selects the colour. Within the row, drag to
swap occupied holes or move into an empty one. Human draft pegs are already on
the board, so Submit/Lock commits them **without another flying animation**.
Feedback appears immediately after a human guess. Computer turns retain slow,
sequential flights and delayed feedback. Existing mouse/keyboard placement still
works and also commits in place. Previous submitted rows cannot be edited.
