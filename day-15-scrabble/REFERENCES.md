# References, edition choices and rights

## Rules

- Hasbro, [Scrabble instructions (2003 PDF)](https://www.hasbro.com/common/instruct/Scrabble_(2003).pdf).
  Verified reachable on 30 October 2026. A physical-game reference for classic
  movement, premiums, tile values and scoring. Not every digital choice here
  matches that edition: see RULES.md for dictionaries, challenges, endings/ties.
- [Hasbro instruction catalogue](https://instructions.hasbro.com/): find the
  product/edition for your physical set when comparing rules. No single manual
  establishes universal rules for all countries and tournament organisations.

The board uses the standard English 100-tile distribution and classic premium
layout. Rules explanations are original prose; no rulebook PDF is redistributed.

## Bundled word data

- Loren Brichter, [Words](https://github.com/lorenbrichter/Words), the Letterpress
  word list. Source pinned to commit `f4976d6a6d34beb431dec8d4b443a138f4dc8bee`.
- Explicit [CC0 licence at that commit](https://raw.githubusercontent.com/lorenbrichter/Words/f4976d6a6d34beb431dec8d4b443a138f4dc8bee/LICENSE),
  also included locally in `words/CC0-1.0.txt`.
- Full provenance, checksum, filtering and compatibility limits:
  [words/NOTICE.md](words/NOTICE.md).

This is NOT Collins/CSW, NWL or a licensed official Scrabble lexicon. It contains
US/UK/Australian variants and may include obscure/offensive words. A legally
obtained custom list can be loaded with `--dictionary`; its own terms apply.
No official dictionary is bundled or downloaded automatically.

## Offline definitions

English Wiktionary contributors, extracted by Tatu Ylönen / Wiktextract via
[Kaikki](https://kaikki.org/dictionary/English/index.html), under CC BY-SA 4.0.
The filtered, adapted SQLite database and full licence are bundled locally.
See [complete attribution, transformations, checksums and coverage](words/DEFINITIONS_NOTICE.md).
All word inspection is offline; the previous dictionaryapi.dev lookup was removed.
The game list remains CC0; definitions are not relicensed CC0/MIT.

## Programming and algorithms

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html):
  immutable physical tiles and declared board letters.
- [Python collections.Counter](https://docs.python.org/3/library/collections.html#collections.Counter):
  tile-inventory invariants in complete-game tests.
- [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html):
  bounded background searches and non-blocking future polling.
- [Python time.monotonic](https://docs.python.org/3/library/time.html#time.monotonic):
  deadlines unaffected by wall-clock adjustments.
- [Python unittest](https://docs.python.org/3/library/unittest.html):
  standard-library test discovery, fixtures and assertions.
- [Pygame documentation](https://www.pygame.org/docs/): display, events, fonts,
  drawing and scaled coordinate handling.
- [Trie overview](https://en.wikipedia.org/wiki/Trie): a conceptual reference for
  shared-prefix search. Search code here is original, not ported from an engine.

## Rights and provenance boundary

Scrabble is a trademark of Hasbro in the US/Canada and Mattel in other territories.
No affiliation or endorsement is claimed. No commercial artwork, official logo,
board scan, tile texture, music, recorded sound or official dictionary is bundled.
Original graphics use Pygame primitives and installed system fonts with a default
font fallback; no system font files are copied into the repository.

Our original Python code and documentation use the root MIT licence. The word
list is separately CC0; pygame is separately LGPL-licensed, including relevant
font/native-library terms. MIT is not a grant of third-party trademark or game
presentation rights, and educational intent is not claimed as universal legal
permission. See the root THIRD_PARTY_NOTICES.md before redistributing a package.
