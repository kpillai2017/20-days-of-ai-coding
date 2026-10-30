# The rules implemented here

## Edition boundary

Mastermind has multiple published rule sets. This project selects a traditional
**two-player, four-position, six-colour, ten-attempt** game with repeated colours
and traditional maker scoring. It does not present this particular combination
as the unique original release or claim official certification. Some editions
use 8, 9 or 12 attempts, other colours, empty holes or different scoring.
The linked UltraBoardGames reproduction, for example, says **nine attempts**
and no additional failure point: that is NOT the scoring variant used here.
See [source notes](REFERENCES.md).

## One round

1. The codemaker secretly fills four positions using Red, Yellow, Green, Blue,
   White and Black. Colours may repeat; all four positions must be filled.
2. The codebreaker fills the next row with a four-peg guess, then submits it.
3. Award one **black feedback pin** for each correct colour in its exact position.
4. Award one **white feedback pin** for each remaining correct colour in a wrong
   position. Each code peg and guess peg can contribute to at most one pin.
5. Feedback is a pair of counts, not a mapping to positions. Black pins are
   grouped before white pins for display; unfilled feedback holes mean nothing
   matched, not additional information about specific positions.
6. Four black pins end the round successfully. Otherwise the breaker continues
   until the tenth guess. No extra guesses, partial-row turns or editing old rows.
7. Reveal the code. Award the maker **one point per guess made**, plus **one point
   if the code was not solved**. A tenth-guess solution scores 10; failure scores
   11. A first-guess solution scores 1.

The program calculates feedback automatically even for a human maker. It does
not support intentional incorrect feedback, mis-scoring penalties, forfeits or
disputes between physical players. There is no extra hint penalty or solver
hint button. Repeated colours are always allowed, not an optional toggle.

## Duplicate examples

- Secret **R R G B**, guess **R G R Y** → **1 black, 2 white**.
  The first R is exact; the remaining R and G exchange positions.
- Secret **R R G B**, guess **R R R R** → **2 black, 0 white**.
  The extra guessed red pegs do not create extra red pegs in the secret.
- Secret **R Y G B**, guess **Y R B G** → **0 black, 4 white**.
- Secret **R R R R**, guess **Y Y Y Y** → **0 black, 0 white**.

For each colour, take the smaller of its secret count and guess count. Add
these overlaps; subtract the number of exact matches to get white pins.

## Match scoring

Exactly two seats, independently human or computer, alternate roles. Seat 1
makes first. Choose 1–5 maker rounds per player before starting; the default
is one maker round each (two rounds total). Round awards accumulate immediately
and exactly once when the round ends. **Highest maker total wins**, because a
harder secret takes the opponent more guesses. Equal totals are a draw.

Click Next round to swap roles. After the final round, Show match result
compares scores; it does not grant extra points. There is no automatic sudden
death: start another equal-role match if desired. Computer/Computer still
requires the round-transition button so the revealed code and award can be read.

## Computer play

A computer maker samples four independent colour indices, allowing duplicates.
A computer breaker begins with all 1,296 codes, uses public feedback to eliminate
inconsistent candidates and selects candidate-only minimax guesses. It never
reads the secret. This is **not** Knuth's complete five-guess algorithm, and no
five-guess or optimal-play guarantee is claimed. Human and computer guesses obey
the same ten-attempt limit and duplicate/scoring rules.
