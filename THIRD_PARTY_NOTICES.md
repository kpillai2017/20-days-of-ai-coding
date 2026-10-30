# Third-party notices and project provenance

## Scope of the repository licence

The [MIT licence](LICENSE) applies to this repository's own code and documentation. It does **not** relicense third-party software, fonts, brands, or linked reference material. Dependencies retain their upstream licences.

These projects were created with AI coding assistance and subsequently reviewed and tested. They are small educational implementations of established ideas, not official versions of the games they reference. AI assistance and passing tests are not guarantees of correctness or legal clearance.

## Day 01: Pixel Life

- Implements the rules of **Conway's Game of Life**, devised by **John Horton Conway**. The [Day 01 guide](day-01-pixel-life/README.md#references-and-attribution) links to background, pattern descriptions and browser documentation.
- Uses browser APIs and no third-party runtime JavaScript libraries.
- Does not bundle third-party artwork, fonts, audio or tutorial source code. References are links for further reading, not content relicensed by this repository.

## Day 02: Breakout

- An educational paddle-and-bricks game inspired by the classic **Breakout**, originally released by Atari. It is not affiliated with or endorsed by Atari; no original game source, artwork or sound is included.
- Depends on **pygame 2.6.1**, installed separately using `requirements.txt`. pygame identifies its licence as **LGPL**; see [pygame 2.6.1's LGPL 2.1 licence text](https://github.com/pygame/pygame/blob/2.6.1/docs/LGPL.txt) and [upstream repository](https://github.com/pygame/pygame).
- pygame wheels can include native libraries and assets with their own notices, including the default font used by `pygame.font.Font(None, size)`. That font comes from the installed pygame package, not this Git repository; it is not covered by our MIT licence.
- This repository does not vendor or redistribute pygame, its font file, or its native libraries. If you package or redistribute the application together with those dependencies, review and preserve their upstream notices and comply with their licences; the repository's MIT licence alone is not sufficient for that bundle.
- [The Day 02 guide](day-02-breakout/README.md#8-references-and-attribution) lists learning references. Linked articles and documentation remain the property of their respective authors.

## Day 03: Pocket Tasks

- An original educational task tracker using browser APIs only; no third-party runtime libraries, fonts, images, audio or analytics are bundled.
- Uses `localStorage` for same-browser persistence; task data is not sent to GitHub or a backend.
- The [Day 03 guide](day-03-pocket-tasks/README.md#references-and-licence) links to documentation for forms, safe DOM rendering, browser storage and tests. Linked material retains its authors' rights.
- Its own source and documentation are covered by the repository's MIT licence.

## Day 04: Maze Explorer

- Original educational maze generation and navigation code, using standard depth-first and breadth-first search algorithms; references appear in [the guide](day-04-maze-explorer/README.md#references-and-licence).
- Uses **pygame 2.6.1**, installed separately. The same LGPL and bundled-font/native-library considerations described under Day 02 apply; no pygame code or font files are vendored here.
- No third-party game artwork, audio, tutorial source or runtime AI service is bundled. Own source and documentation are covered by the repository's MIT licence; linked references retain their authors' rights.

## Day 05: Typing Sprint

- Original educational typing-practice code and three original practice passages created with AI coding assistance. No third-party literary excerpts, runtime libraries, remote fonts, analytics or other assets are bundled.
- Uses browser APIs only and does not store or upload attempts. Pasting is allowed; this is not a verified competitive typing benchmark.
- Own code, passages and documentation are covered by the repository's MIT licence. The [Day 05 guide](day-05-typing-sprint/README.md#references-and-licence) links to learning references, which retain their authors' rights.

## Day 06: Enigma Lab

- Original educational simulator/prose created with AI coding assistance; historical rotor/reflector wiring and stepping are attributed to [Crypto Museum](https://www.cryptomuseum.com/crypto/enigma/wiring.htm). No museum prose, photos, historical message facsimiles or third-party source code is bundled.
- Uses **pygame 2.6.1**, installed separately; the LGPL, default-font and native-library considerations under Day 02 apply here too.
- A temporary development comparison used **py-enigma 1.0.2**, separately installed under its own terms. It is not vendored, imported by the application/tests or listed as a runtime dependency. [Validation notes](day-06-enigma-lab/VALIDATION.md) describe the comparison.
- History and mechanics references retain their authors' rights. The simulator's own code/documentation are MIT-licensed. It is a historical teaching tool, not modern secure encryption or an endorsement of the regimes that used the machines.

## Day 07: Engine Explorer

- Original code, procedural 3D shapes, flow overlays and explanatory prose created with AI coding assistance; no third-party libraries, meshes, artwork, fonts or sound are bundled.
- Browser-native Canvas2D draws a software-projected 3D cutaway. Mechanics references in [the day guide](day-07-engine-explorer/README.md#references-and-licence) retain their authors' rights.
- Own code and documentation are MIT-licensed. Cycle timings and flow cues are illustrative; the app is not validated engineering design software or a universal model of every engine type.

## Day 08: Koan Garden

- Original, AI-assisted code, writing ingredients and educational documentation. No third-party koan translations, literary excerpts, libraries, fonts, images or audio are bundled.
- Uses browser APIs and local English keyword/template rules, not a runtime AI service. Entries are not stored or uploaded by the app.
- Koan-inspired creative prompts are not traditional Zen cases, formal Buddhist instruction or counselling. Background references in [the day guide](day-08-koan-garden/ABOUT_KOANS.md) retain their authors' rights and imply no endorsement.
- Own code and prose are covered by the repository's MIT licence.

## Day 09: Vector Tanks

- Original Battlezone-inspired educational tank game; code, procedural wireframe meshes, scenery and synthesised sound were created for this project with AI coding assistance. No Atari ROMs, source, artwork, logos, model data, fonts or recordings are bundled.
- Battlezone and Atari names identify historical inspiration. Third-party brand and original-game rights remain with their respective owners; no affiliation or endorsement is implied. The repository MIT licence covers our own implementation, not those rights.
- Uses separately installed **pygame 2.6.1**; the LGPL, bundled default-font and native-library notes under Day 02 also apply here. No packaged executable or vendored dependency is distributed.
- Historical and technical reference links in [the guide](day-09-vector-tanks/README.md#references-and-licence) retain their authors' rights. No reference text or manual scans are reproduced.

## Day 10: Sudoku Studio

- Original AI-assisted Python source, puzzle generator and educational prose. Puzzles are generated locally; no third-party puzzle collection or solver implementation is bundled.
- Uses separately installed **pygame 2.6.1**; the Day 02 LGPL, bundled-default-font and native-library notes also apply. No additional font files, images, sounds or executable packages are distributed.
- Own implementation and documentation use the repository MIT licence. Background and technical links in [the README](day-10-sudoku-studio/README.md#references-origins-and-licence) retain their authors' rights. No article prose or historical puzzle scans are reproduced.

## Day 11: Clockwork Chess

- Clear Python rewrite inspired by selected algorithms in Richard Allbert / Bluefever Software's [VICE11 source](https://github.com/bluefeversoft/vice/tree/main/Vice11/src). Upstream MIT copyright **2022 bluefeversoft** and permission/disclaimer are retained in full in [VICE_LICENSE.txt](day-11-clockwork-chess/VICE_LICENSE.txt). See [source mapping](day-11-clockwork-chess/SOURCE_NOTES.md) for reviewed files, differences and scope. Root MIT does not supersede the upstream notice.
- Original Python implementation, procedural piece meshes, animated effects, generated PCM sounds and educational prose were created with AI assistance. No VICE binaries/books, commercial Battle Chess sprites/models/sound recordings or logos are bundled. Third-party names identify inspiration; no affiliation or endorsement is claimed.
- Uses separately installed **pygame 2.6.1**; Day 02's LGPL, default-font and native-library notes apply. Linked publications retain their own rights. No packaged executable or vendored dependency is distributed.

## Day 12: Sort Lab

- Original AI-assisted HTML/CSS/JavaScript, diagrams and educational prose implementing standard sorting techniques. No third-party algorithm source, libraries, fonts, images or datasets are bundled.
- Uses browser DOM/generator/animation APIs; no runtime AI, external requests, analytics or persistent entries. Own implementation and prose use the root MIT licence.
- Background links in [the README](day-12-sort-lab/README.md#references-and-licence) retain their authors' rights; no article text is reproduced. Numeric test-oracle sorting uses JavaScript's native sort only in tests, not in the nine implementations.

## Day 13: Horologium

- Original AI-assisted Canvas artwork, code and synthesised ticks/bell tones; no downloaded models, textures, icons, samples or fonts. Own work uses the repository MIT licence.
- The requested [Clock3D reference](https://github.com/OetkenPurveyorOfCode/Clock3D) was reviewed as visual inspiration only. As reviewed on 26 October 2026, its README says GPLv3 but its root LICENSE contains AGPLv3, and its model/sound/icon credits have separate terms. No reference source/assets were copied, ported or bundled; this project does not rely on or resolve that discrepancy. See [provenance notes](day-13-clockwork/README.md#reference-project-and-rights).
- Uses native Canvas/Web Audio APIs only; no third-party runtime libraries, network time service, analytics or stored entries. Linked publications retain their authors' rights and imply no endorsement.

## Day 14: Monopoly

- Original AI-assisted Python/Pygame implementation, geometric board artwork and didactic prose studying classic British Monopoly (London edition). Property names, stations and rent values are from the classic British London edition. No commercial board/card scans, logos, mascot, token models, recorded sounds or third-party game engine code are bundled.
- Monopoly is a Hasbro trademark. London place names identify the British board; no exclusive ownership of ordinary place names is asserted. This project is independent and is not affiliated with, endorsed by or licensed by Hasbro. The repository MIT licence covers our original implementation/prose only, not rights in third-party marks, game presentation or linked rulebooks. Educational purpose is not asserted to provide universal permission; no legal clearance claim is made.
- Uses separately installed pygame 2.6.1; the Day 02 LGPL, default-font and native-library notes apply. The Hasbro instruction catalogue and a supplemental official US rulebook are linked as references, not redistributed. See [references](day-14-monopoly/REFERENCES.md) and [edition/implementation limits](day-14-monopoly/RULES.md).

## Day 15: Scrabble

- Original AI-assisted Python/Pygame tile-game engine, trie search, interface graphics and teaching prose. No commercial board scans, logos, tile textures, recorded sounds or official Scrabble dictionaries are bundled. Our original code/prose use MIT; that does not grant rights in third-party trademarks or game presentation.
- Scrabble is a trademark of Hasbro in the US/Canada and Mattel in other territories. No affiliation, endorsement or official rules certification is claimed. Educational intent is not asserted as universal legal permission.
- Bundled English word data: Loren Brichter's **Words / Letterpress** list, pinned commit `f4976d6a6d34beb431dec8d4b443a138f4dc8bee`, under its explicit **CC0 1.0** dedication. Full licence is preserved in [words/CC0-1.0.txt](day-15-scrabble/words/CC0-1.0.txt); exact sources, checksum and limitations are in [words/NOTICE.md](day-15-scrabble/words/NOTICE.md). This is not Collins/CSW or NWL. The initially considered ENABLE mirror is not bundled. Offline definitions are an adapted English Wiktionary/Kaikki extract under **CC BY-SA 4.0**, NOT MIT or CC0. Full licence and attribution, source checksums, transformations and measured coverage are preserved in [words/DEFINITIONS_NOTICE.md](day-15-scrabble/words/DEFINITIONS_NOTICE.md) and [CC-BY-SA-4.0.html](day-15-scrabble/words/CC-BY-SA-4.0.html). Retain attribution and share-alike terms for definition data. No runtime definition network service is used.
- Uses separately installed pygame 2.6.1; Day 02 LGPL, font and native-library notes apply. Installed system fonts are used through Pygame with a bundled default-font fallback; no system font files are copied here. See [references](day-15-scrabble/REFERENCES.md) and [rules boundary](day-15-scrabble/RULES.md).

## Day 16: Mastermind

- Original AI-assisted Python/Pygame engine, candidate-only minimax codebreaker, procedural plastic-style board/peg artwork and teaching prose, under the repository MIT licence. No commercial board scans, logo, packaging, models, fonts, recorded sounds or game source are bundled.
- Mastermind is a third-party game name/trademark, including Hasbro products. This independent educational project is not affiliated, endorsed or officially certified. MIT covers original work, not third-party marks or presentation rights; educational use is not asserted as blanket legal permission.
- Uses separately installed pygame 2.6.1; the Day 02 LGPL/default-font/native-library notes apply. Installed system fonts are used locally, not redistributed. Rules references are linked, not copied. See [references](day-16-mastermind/REFERENCES.md), [edition boundary](day-16-mastermind/RULES.md) and [design](day-16-mastermind/DESIGN.md).

## Development tools

Python, Node.js, GitHub Actions and their actions are external tools/services used for development and testing. Their implementations are not included in this repository; they retain their own terms and licences. See [the workflow](.github/workflows/tests.yml) for action versions.

## Day 06 optional 3D renderer

- PyOpenGL 3.1.10 is separately installed for the optional Pygame/OpenGL view,
  under its [BSD-style licence](https://github.com/mcfletch/pyopengl/blob/master/license.txt).
  OpenGL/GLU drivers/system libraries are supplied by the user's platform.
- The wooden-case model, key/lamp geometry, rotor rings and 2D physical-view art
  are original procedural artwork under the root MIT licence. No third-party
  models, photographs, historical insignia, textures or font files are bundled.
  This is an Enigma-inspired illustration, not a certified historical replica.
