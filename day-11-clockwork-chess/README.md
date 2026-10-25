# Day 11 · Clockwork Chess

**Python/Pygame chess with a VICE-inspired engine, switchable 2D/3D views, original animated characters and synthesised sound.** Play against the computer or another person at the same computer.

This is an educational rewrite of selected chess-engine ideas from [Richard Allbert / Bluefever Software's VICE, `Vice11/src`](https://github.com/bluefeversoft/vice/tree/main/Vice11/src), not a Python wrapper around its C code. Read the [source and licence mapping](SOURCE_NOTES.md). The presentation evokes *Battle Chess* but uses no commercial sprites, models, recordings or logos.

## Install and run

Python **3.9–3.13**; Python 3.12/3.13 recommended for convenient wheels.

macOS/Linux, from the repository root:

```sh
cd day-11-clockwork-chess
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows PowerShell:

```powershell
cd day-11-clockwork-chess
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

No account, network, engine download or asset installation. Optional flags:

```sh
python main.py --mute           # Skip audio-device setup
python main.py --two-player     # Two people, one computer
python main.py --mute --frames 30  # Automated window-loop smoke run
```

## Play

- White starts. The human is White by default; choose **Human: White/Black** to change side and start a fresh game.
- Click the **base square** of a piece, then a green destination. Because the board is tilted, a tall piece's head may visually overlap another square; selection uses the board footprint, not the head.
- Ivory pieces are White, steel-blue pieces Black. Labels P/N/B/R/Q/K complement their silhouettes; N means knight.
- **Vs AI / two players** switches mode and starts a fresh game. **Tab** also switches.
- **AI level** cycles easy/medium/hard: maximum depths 2/3/5 plies with target budgets 0.35/1.1/2.5 seconds. These are search settings, **not Elo ratings**; pure Python strength is modest.
- Promotion offers **Q/R/B/N** buttons or keys. Castling and en passant are handled automatically when legal.
- **H / Hint button:** search for a suggested move and outline its source/destination in gold, without playing it. Available on human turns (either side in local two-player mode). Uses the selected AI level; it is a suggestion, not a guaranteed best move or a teaching explanation. A new move, undo, restart or level change clears the hint; view/flip preserves it.
- **U / Undo turn:** in two-player mode undo one move; in AI mode undo enough to let the human choose again. An uncommitted animation is cancelled first. Undo during an AI reply animation also rewinds the human move.
- **V / View button:** switch between a clear top-down 2D board and the isometric 3D-style scene at any time, including during a move, without changing game state.
- **3D camera:** mouse wheel, +/− or the compact Zoom buttons zoom in/out (65–150%). Left-drag the board horizontally to rotate and vertically to tilt; Left/Right arrows rotate and Up/Down arrows change tilt. Home / Reset view restores the default. A click without dragging still selects a piece; moving at least five logical pixels starts an orbit instead of a move. Rotate buttons are omitted; keyboard arrows remain available. These controls affect only 3D and preserve the game, hints and animation. At large zoom or steep tilt some edges can leave the clipped board viewport; zoom out/reset to see the whole board.
- **F:** flip the board. **M:** toggle available sound. **R:** fresh game. **Esc:** quit. During promotion, R selects rook rather than restarting.
- Recent moves use coordinate/UCI notation such as `e2e4` or `a7a8q`, not standard algebraic notation.

New/mode/side changes discard the game without confirmation. Nothing is saved to disk. Resizing letterboxes the same logical board and transforms mouse positions back into logical coordinates. The app has no chess clock, save/load, PGN, UCI protocol, network play, opening book or external tablebase.

## Animation and audio

**2D mode** uses original **Staunton-style vector pieces** (not Unicode fonts or downloaded artwork): stepped bases, a spherical pawn, horse-head knight, mitred bishop, battlement rook, coronet queen and cross-topped king on a top-down board. **3D mode** uses original procedural low-poly characters: helmeted shield-bearing pawns, mounted knights, staff-bearing bishops, siege-tower rooks, crowned queens and sword-bearing kings. Red cloth/ivory armour and blue cloth/steel armour distinguish the sides. Their shapes evoke a playful medieval chess set rather than copying commercial character designs.

Moves have stepping/bobbing motion; knights hop. Captures use a staged approach, wind-up, impact and recovery. The attacker stops short while striking, the victim topples/shrinks, and the attacker occupies the destination after the effect:

| Attacker | Original capture style | Effect / audio |
| --- | --- | --- |
| Pawn | Shield bash | Forward arm/shield thrust, impact ring, low thud |
| Knight | Mounted charge | Hop/charge, sweeping strike, pulsed metallic tone |
| Bishop | Staff spell | Staff gesture, violet energy, rising spell tone |
| Rook | Siege ram | Ram extension, shock ring, low rumble |
| Queen | Royal lightning | Recoil/cast, gold lightning, noisy high sweep |
| King | Sword salute | Arm/sword lunge, slash arc, metallic strike |

These are six **attacker-specific** styles, not 36 unique attacker/victim battles. A style uses the same timing in both views, so switching mid-capture preserves progress. The top-down icons share the motion and effects but do not articulate limbs. Castling moves both pieces; en passant targets the actual captured pawn square; promotion changes the figure when committed. Kings are never captured, although they can capture other pieces.

A legal move is previewed over a snapshot, then committed **once at the end**. Animation never decides legality. Search happens in a single background worker with a stop Event so restarting/undoing cannot apply a stale reply. Closing requests cancellation and waits for the worker.

The 3D-style view is a **2.5D software-rendered isometric scene**, with adjustable yaw, tilt and zoom—not a perspective GPU renderer. Painter sorting has limitations where shapes overlap. This does not reproduce Battle Chess's original character models, hand-authored fight choreography, skeletal animation, sampled voices or recordings. It aims for its humorous, characterful feel through small original procedural scenes, not a faithful audiovisual replica.

Move sounds vary by piece; six capture timbres plus check/game-over effects are synthesised locally from sine waves, frequency sweeps, pulses and seeded noise. No recordings or commercial assets are loaded. Audio-device failure is nonfatal. `--mute` skips initialisation; restart without it to enable audio later.

## Rules and draw policy

The engine implements legal moves, king safety, castling rights/path safety, en passant including discovered checks, all four promotions, checkmate and stalemate. Kings are never captured.

For a friendly local game, **threefold repetition and the fifty-move rule are automatically claimed**. Official tournament rules distinguish claims from automatic fivefold/75-move draws; that distinction is not implemented. Checkmate takes priority. Material-only draws are conservative: king versus king, king+one bishop/knight versus king, or bishops-only positions with every bishop on the same square colour. This is not a complete dead-position detector.

The engine uses a 64-square list rather than VICE's 120-square mailbox. Search uses iterative deepening, negamax alpha–beta, capture ordering and bounded quiescence, with simple material/centrality/pawn-advance evaluation. No transposition table, killer/history heuristic, null-move pruning, opening book or VICE threading framework is included. It is not equivalent in strength or features to VICE 1.1.

## Tests and learning

### Suggested first reading

The source is deliberately expanded for beginners: every function/class in the four application modules has a docstring, and inline comments explain non-obvious transitions rather than simply repeating statements. Dense semicolon-separated code has been expanded into conventional blocks; tests use the same readable formatting.

1. Read `animation.smooth` and `animation.pose` for a small pure-function example.
2. Follow `App.click` → `App.animate` → `App.update` to see one move preview and commit.
3. Read `Position.legal_moves`, `push` and `pop` to understand king safety and undo.
4. Read `search` last: its nested helpers share a working position and cancellation state.
5. Use the walkthrough below for camera maths, sound samples and the background worker.

Comments explain assumptions and limitations too: `push` trusts a legal move, material draws are conservative, camera rendering is approximate, and hints are suggestions rather than guarantees.


- [Beginner learning guide](LEARNING_GUIDE.md): board coordinates, attacks versus moves, make/unmake, search, projection, animation and sound.
- [VICE source notes](SOURCE_NOTES.md): algorithm mapping, differences and retained licence.
- `engine.py`: standard-library-only rules/search.
- `graphics.py`: original character meshes, 2D icons, both projections and combat effects.
- `animation.py`: pure time-based poses and six capture styles shared by both views.
- `main.py`: events, cancellable worker, animations and audio.

From the day folder:

```sh
python -m unittest discover -s tests -v
```

Model-only tests (no Pygame required):

```sh
python -m unittest discover -s tests -p test_engine.py -v
```

Headless macOS/Linux:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
SDL_VIDEODRIVER=dummy python main.py --mute --frames 30
```

PowerShell: set `$env:SDL_VIDEODRIVER='dummy'` and `$env:SDL_AUDIODRIVER='dummy'` first. Tests include exact perft counts, special moves, draws, AI cancellation, preview/commit/undo, both projection hit tests, all capture styles and headless drawing. Perft counts rule-tree leaves, not engine strength. These tests are not a formal proof of every chess position or tournament compliance.

## References and rights

- [VICE source](https://github.com/bluefeversoft/vice/tree/main/Vice11/src) and [tutorial playlist](https://www.youtube.com/playlist?list=PLZ1QII7yudbc-Ky058TEaOstZHVbT-2hg).
- [Chess Programming Wiki: Perft results](https://www.chessprogramming.org/Perft_Results), [alpha–beta](https://www.chessprogramming.org/Alpha-Beta), [quiescence](https://www.chessprogramming.org/Quiescence_Search).
- [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023) — official rules; our simplifications are stated above.
- [Pygame documentation](https://www.pygame.org/docs/), [Python concurrent futures](https://docs.python.org/3/library/concurrent.futures.html).

Our original Python rewrite, meshes, generated audio and prose use the root [MIT licence](../LICENSE). Upstream VICE's MIT notice is retained in full in [VICE_LICENSE.txt](VICE_LICENSE.txt), copyright 2022 bluefeversoft. This notice remains applicable to any upstream-derived portions; root MIT does not remove it. Pygame, its bundled default font and native dependencies have their own terms. Battle Chess and other third-party names identify inspiration only; no affiliation, endorsement or rights in commercial assets are claimed. See [notices](../THIRD_PARTY_NOTICES.md).
