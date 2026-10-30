# References, edition notes and provenance

Links identify background sources, not imported assets or endorsements.

## Rules and history

- [Mastermind overview](https://en.wikipedia.org/wiki/Mastermind_(board_game)?oldformat=true):
  secondary reference describing four positions, six colours, repeated colours,
  duplicate-safe black/white feedback, traditional maker scoring and edition
  variation. Successfully retrieved on 30 October 2026. Its historical account
  credits Israeli telecommunications expert **Mordecai Meirowitz** with the
  modern game around 1970 and Invicta Plastics with commercial development and
  release around 1971–72. It developed from older Bulls and Cows-style deduction
  games. Dates and packaging differ by market; this project does not reproduce
  a specific original box or assert a uniquely original ten-row specification.
- [Hasbro instruction catalogue](https://instructions.hasbro.com/en-us/all-instructions?search=mastermind):
  official publisher catalogue, successfully retrieved on 30 October 2026.
  It contains multiple products/variants, including multiplayer versions; use
  the rule sheet for your own product rather than assuming all are identical.
  Direct guessed legacy PDF/slug URLs returned 404 and are not used as evidence
  that an exact ten-row original rulebook was verified.
- [UltraBoardGames rules](https://www.ultraboardgames.com/mastermind/game-rules.php):
  accessible secondary reproduction, checked 30 October 2026. Its text uses
  **nine attempts and nine points for failure**, illustrating why we explicitly
  document our ten-attempt, additional-failure-point variant instead of claiming
  all published instructions agree. It is not the authority for our chosen
  traditional scoring.

The implementation uses ten attempts and maker points per guess plus one for
failure, as described in the traditional overview. This is an explicit scope
choice; **perfect compatibility with every historical edition is not claimed**.
No rulebook text, illustrations or downloaded reference files are bundled.

## Algorithms and programming

- Donald E. Knuth, *The Computer as Master Mind*, Journal of Recreational
  Mathematics **9 (1976–77), 1–6**. Historical reference for minimax deduction.
  Our candidate-only search is independently written and does not claim its
  five-guess guarantee. General minimax selection here is a heuristic, not a
  claim of globally optimal average play.
- [Python Counter](https://docs.python.org/3/library/collections.html#collections.Counter):
  count intersection implements duplicate-safe colour overlap.
- [itertools.product](https://docs.python.org/3/library/itertools.html#itertools.product):
  enumerate the Cartesian product of colour choices.
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html):
  worker-thread search, stale result invalidation, explicit cleanup.
- [Pygame drawing](https://www.pygame.org/docs/ref/draw.html),
  [events](https://www.pygame.org/docs/ref/event.html) and
  [fonts](https://www.pygame.org/docs/ref/font.html).
- [Nielsen Norman Group usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/):
  visible state, error prevention, recognition and clear recovery.

## Rights and asset inventory

All project code, prose and procedurally drawn artwork are original AI-assisted
work under the root MIT licence. No commercial board photos, logo, lid artwork,
fonts, scans, models, samples or third-party game engine are included. Pygame
2.6.1 is installed separately; see root notices for LGPL/default-font/native
library details. Installed system fonts are used locally, never redistributed.

Mastermind is a third-party game name/trademark associated with its publishers,
including Hasbro products. This independent project is not affiliated, endorsed
or officially certified. MIT covers our original work, not third-party marks or
commercial presentation rights. We do not assert that game rules, all related
materials or the trademark are public domain, nor that education creates blanket
fair-use permission.
