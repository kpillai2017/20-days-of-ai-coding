# Day 09 · Vector Tanks

**An original Python/Pygame tribute to the look and feel of Atari's Battlezone (1980).** Drive a tank from a first-person view, hunt green wireframe enemies, read a rotating radar and shoot through a sparse battlefield of geometric obstacles.

This is a playable reimplementation of selected ideas, **not an emulator, ROM port or frame-accurate recreation**. No Atari code, ROMs, model data, artwork, logos, fonts or recordings are included. See [history and differences](HISTORY.md).

## Install and run

Use Python **3.9–3.13**. Python 3.12 or 3.13 is recommended for convenient wheels.

### macOS / Linux

From the repository root:

```sh
cd day-09-vector-tanks
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Windows PowerShell

```powershell
cd day-09-vector-tanks
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The virtual environment keeps this game's packages separate. On macOS/Linux you can also use `.venv/bin/python` without activation. `deactivate` exits an activated environment. Python/Pygame run locally; no accounts, API keys, cloud services or network play.

Optional flags:

```sh
python main.py --seed 42   # Repeatable initial random stream
python main.py --mute      # No audio-device setup
python main.py --demo --frames 180 --mute  # Three-second automated smoke run
```

A seed reproduces a run only with the same implementation, time steps and inputs. R restarts from that configured seed; without a seed it creates a fresh random stream. `--demo` is an automated test driver, not an intelligent attract-mode player.

## Controls

Press **Enter** on the title screen to deploy.

| Key | Action |
| --- | --- |
| Up / W | Forward |
| Down / S | Reverse, more slowly |
| Left / A, Right / D | Turn hull and gun together |
| Space (hold) | Fire whenever a shot becomes available |
| T / G | Left track forward / reverse |
| U / J | Right track forward / reverse |
| P or H | Pause / show basic help; press again to resume |
| Enter | Resume; start again after game over |
| R | Restart immediately |
| Esc / window close | Quit |

For cabinet-inspired dual-track control, hold **T+U** to drive forward, **G+J** to reverse, **T+J** to pivot right, or **G+U** to pivot left. One track by itself produces an arc. Any nonzero track input takes priority over arrow/WASD movement. These are a kinematic approximation, not simulated tracks with traction.

Losing window focus pauses play. Return to the window and explicitly resume. Resize the window freely: the logical 1000×750 view is letterboxed rather than stretched.

## How to play

- Find enemy blips on the radar, turn toward them, and align your sight. **Top of radar is your current heading**, not north. The fan indicates the approximate camera view; the sweeping line is a visual cue, not a sensor simulation.
- You have **three tanks/lives**. A hit uses one, respawns you in the clear centre and gives 2.5 seconds of protection. Brief red cracks indicate damage. Game over occurs at zero.
- Only **one player shell** may be active, plus a half-second minimum firing cooldown. A shell expires after three seconds or on impact. Holding Space fires again when both constraints allow it.
- Lead moving targets. The hull and gun turn together; there is no independent turret or mouse aiming.
- Boxes, cylinders and pyramid-shaped cover block movement and shots. Pyramids use conservative full square footprints; the collision model is 2D, so you cannot shoot over low cover.
- Regular tanks score **1,000**, faster supertanks with a mast score **3,000**, and saucers score **5,000**. Saucers move but do not shoot. Regular/supertanks approach, try to aim and fire with clear line of sight.
- One enemy starts the game; reinforcements gradually appear up to three active enemies. Speed and firing pressure increase with kills. There are no levels or final victory: survive and improve your score.
- The square arena is bounded at ±100 world units. Edges stop tanks; the mountain silhouette is decorative background, not a route out of the arena.

## Features and honest limits

Original procedural meshes, perspective projection, clipped wireframe lines, horizon mountains/volcano, radar, reticle, targeting cue, shot tracers, explosion spokes and optional synthesised engine/fire/impact audio aim for the early vector-arcade feel. Audio-device failure is nonfatal; use `--mute` if needed. Pygame rasterises the lines on a modern screen: this is not a vector CRT simulation.

AI uses simple distance/heading rules and obstacle stopping rather than route planning, and can become stuck behind cover. There is no exact arcade timing, missile enemy, cabinet periscope optics, original sound, ROM behaviour, bonus-life schedule or persistent high-score table. Wireframes are transparent: rear edges show through surfaces. The radar shows enemies within 100 units; enemies farther away can be off radar.

## Learn the code

| File | Purpose |
| --- | --- |
| `game.py` | Pygame-free model: positions, input values, movement, AI, projectile collisions, score and lives |
| `renderer.py` | Procedural 3D meshes, camera rotation, near-plane clipping, perspective and HUD |
| `main.py` | Keyboard mapping, window loop, pause/resize, optional synthesised sound |
| `tests/test_game.py` | Deterministic model tests without Pygame |
| `tests/test_rendering.py` | Geometry, headless drawing, controls and loop smoke tests |

Start with the [illustrated beginner guide](LEARNING_GUIDE.md). Read [history and fidelity notes](HISTORY.md) for what inspired this tribute.

## Tests

From this folder with Pygame installed:

```sh
python -m unittest discover -s tests -v
```

For headless macOS/Linux CI:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --seed 42 --demo --frames 30 --mute
```

In PowerShell, set `$env:SDL_VIDEODRIVER='dummy'` and `$env:SDL_AUDIODRIVER='dummy'` before running the Python commands. The model tests can run without Pygame via `python -m unittest discover -s tests -p test_game.py`.

## References and licence

- [Atari Battlezone arcade manual, archived at Internet Archive](https://archive.org/search?query=Atari+Battlezone+manual) — original controls and historical context; not bundled.
- [The Strong: Battlezone collection search](https://www.museumofplay.org/?s=Battlezone) — game-history starting point.
- [Pygame documentation](https://www.pygame.org/docs/) — Surface, draw, event, time and mixer APIs.
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html), [unittest](https://docs.python.org/3/library/unittest.html), [math](https://docs.python.org/3/library/math.html).
- [Scratchapixel: perspective projection](https://www.scratchapixel.com/lessons/3d-basic-rendering/perspective-and-orthographic-projection-matrix/perspective-matrix-in-practice.html) — further reading; this project uses its own small direct projection implementation.

Own code, procedural meshes, generated sounds and prose: repository [MIT licence](../LICENSE). **Battlezone** and **Atari** names identify the historical inspiration; no affiliation or endorsement is claimed. MIT covers our work, not third-party brands or original game material. Pygame is separately installed under its LGPL terms, and its bundled default font/native libraries have their own terms; see [third-party notices](../THIRD_PARTY_NOTICES.md). We do not redistribute a packaged executable here.
