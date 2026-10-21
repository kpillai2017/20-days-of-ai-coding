# Day 02 · Breakout

A one-level paddle-and-bricks game in **Python + pygame**. Move the paddle, bounce the ball, and clear 50 colourful bricks before losing three lives. Each brick is worth 10 points; clearing the wall earns 500.

No downloaded artwork, sound, AI API, accounts or network access are needed while playing. This is an AI-assisted coding project, not an AI-powered game.

## 1. Install

Use **Python 3.9–3.13** and pygame 2.6.1. Python 3.12 is a good choice for a fresh setup. Start in this project's folder, not the repository root:

```sh
cd 20-days-of-ai-coding/day-02-breakout
```

If you cloned the repository previously, use `git pull` from its root first to download Day 02. If you downloaded a ZIP, download and extract the updated repository.

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

These Windows commands use the environment's Python directly, so PowerShell activation permissions are not an obstacle. On macOS/Linux you can similarly use `.venv/bin/python main.py` without activating.

**What is a virtual environment?** A project-local Python installation area: packages installed there don't interfere with other projects. It is ignored by Git. `requirements.txt` records the dependency so another person can recreate the environment. Run `deactivate` when you finish using an activated environment.

## 2. Play

| Key | Action |
| --- | --- |
| Left / Right or A / D | Move paddle; opposite directions cancel |
| Space | Launch when ready, including after losing a life |
| P | Pause or resume during gameplay |
| R | Restart the entire game from any state |
| Esc or close window | Quit |

The ball starts attached to the paddle. You can move before launching. Hitting near the paddle's edges sends the ball sideways; hitting the centre sends it straight up. Losing a life keeps your score and cleared bricks. Restart resets score, bricks, paddle and all three lives. Switching away from the window automatically pauses active gameplay; press P when you return.

The window is fixed at **800 × 600**. This is a desktop keyboard game, not a browser or touch game. There is one level, no sound, no power-ups and no saved high score.

## 3. Files and reading order

```text
day-02-breakout/
├── README.md
├── requirements.txt       # pygame version
├── game.py                # Geometry, rules and state; no pygame import
├── main.py                # Window, keyboard, timing and drawing
└── tests/
    ├── test_game.py       # Standard-library rule tests
    └── test_window.py     # pygame headless rendering and event checks
```

Read `game.py` first, then follow `main.py`'s game loop. Comments explain decisions, not just syntax.

### The coordinate system

`(0, 0)` is the window's **top-left** corner. X increases to the right; Y increases **downwards**. An upward-moving ball therefore has a negative Y velocity.

The `Rect` dataclass stores `x`, `y`, `width` and `height` as numbers. Properties calculate `right`, `bottom` and the centre. The ball is a **12 × 12 square** for both drawing and collision detection, not a circle with hidden rectangular hitboxes.

### The model: `game.py`

`Game` owns a paddle, ball, list of bricks, X/Y velocities, score, lives and a state string:

```text
ready --Space--> playing --last brick--> won
                   |
                   +--miss, lives remain--> ready
                   +--miss, no lives------> game_over

R from any state: reset everything and return to ready
```

#### Authoritative gameplay constants

`game.py` defines shared gameplay and brick-layout values as module-level constants to prevent disagreement between the model and renderer:

- **Gameplay**: `BALL_SPEED` (340 px/sec), `PADDLE_SPEED` (460 px/sec), `BALL_SIZE` (12×12 square), `INITIAL_LIVES` (3), `POINTS_PER_BRICK` (10).
- **Physics timing**: `MAX_FRAME_DT` (0.1 sec cap), `MAX_PHYSICS_STEP` (1/240 sec substep).
- **Brick layout**: `BRICK_ROWS` (5), `BRICK_COLS` (10), `BRICK_WIDTH` (68), `BRICK_HEIGHT` (20), `BRICK_TOP` (90), `BRICK_GAP_X` (8), `BRICK_GAP_Y` (8), and computed `BRICK_START_X` for horizontal centering.

`main.py` imports `BRICK_TOP`, `BRICK_HEIGHT`, `BRICK_GAP_Y` to compute brick row colours consistently with the model's layout.

#### Game methods

- `reset()` creates a fresh level and restores three lives and zero score.
- `_prepare_serve()` resets only the ball, preserving your progress after a miss. A leading underscore conventionally means an internal helper.
- `launch()` gives the ready ball an upward-right velocity.
- `update(dt, direction)` moves the paddle and advances the rules; direction is -1, 0 or +1.
- `_physics_step(dt)` moves the ball and handles walls, misses, paddle and bricks.
- `_check_paddle_collision()` accepts only a downward crossing of the paddle's top.
- `_resolve_paddle_collision()` changes the bounce angle based on where the ball hit.
- `_check_brick_collisions()` removes a hit brick, awards `POINTS_PER_BRICK` and reverses the appropriate velocity component.

### Delta time and small steps

Velocity is measured in **pixels per second**, not pixels per frame:

```python
position += velocity * seconds_elapsed
```

`clock.tick(60)` targets 60 display frames per second and returns elapsed milliseconds. Dividing by 1000 produces `dt` in seconds. This means a slower computer doesn't deliberately move the ball slower, although frame stalls still affect responsiveness.

A long update could jump over a thin brick. The model splits each update into slices no larger than **1/240 second**, moving both paddle and ball in those slices. It clamps elapsed time to 0.1 seconds so a stalled window doesn't fast-forward through a large backlog. Negative or non-finite time is rejected; zero does nothing. At the game's 340 px/sec ball speed, a slice moves at most about 1.42 pixels.

This is **small-step AABB collision detection**, not a continuous physics engine. Arbitrarily increasing speed or shrinking bricks can cause tunnelling and needs better collision handling or smaller steps.

### Collisions: overlap is only the first question

AABB means **axis-aligned bounding box**: rectangles stay parallel to the screen edges. Two rectangles overlap if their horizontal and vertical ranges overlap. Edge contact alone isn't penetration.

For bricks, previous ball position identifies which side it approached. Resolve the overlap by placing the ball outside that side, then reverse X velocity for a side hit or Y for a top/bottom hit. Process at most one brick per physics slice so a seam doesn't reverse the ball twice.

For the paddle, require a **downward crossing of its top**. A plain overlap test would let a paddle rescue a ball that had already fallen past it. Paddle impact offset controls horizontal speed. The vertical speed follows Pythagoras (`vx² + vy² = speed²`) to keep the total speed at 340 px/sec and avoid nearly horizontal endless bounces.

### The interface: `main.py`

The loop follows **events → update → draw**:

1. Read close/keyboard/focus events. Space launches; P pauses; R resets.
2. Read held keys for smooth paddle motion.
3. Call `game.update(dt, direction)` unless paused.
4. `draw_game()` draws rectangles, counters and state prompts.
5. `pygame.display.flip()` presents the completed frame.

The model retains floating-point positions for smooth motion; drawing rounds to whole pixels. `draw_text()` renders text to an image surface and **blits** (copies) it to the window. `draw_body()` is a helper that converts a model `Rect` (with float coordinates) to a pygame `Rect` (with integer pixel coordinates) and draws it with rounded corners. Fonts come from pygame, not your filesystem. Only display/font modules are initialised because the game doesn't need audio. A `finally` block closes pygame even if an error occurs.

Brick row colours are determined by each brick's Y position and the shared layout constants (`BRICK_TOP`, `BRICK_HEIGHT`, `BRICK_GAP_Y`), so colour assignments remain consistent with the model's brick layout even after bricks are removed.

The `if __name__ == "__main__"` guard means importing `main.py` for tests won't open a window.

## 4. Tests

From `day-02-breakout`, run the model tests with Python alone:

```sh
python -m unittest discover -s tests -p test_game.py -v
```

After installing pygame, run **all tests**, including headless window/control tests:

```sh
python -m unittest discover -s tests -v
```

Use your environment's Python path on Windows as above. The window tests set SDL's dummy video driver and create no visible window. They check drawing every state and synthetic control events; they don't replace trying the game with your own eyes and keyboard.

An additional smoke check runs the real game loop for five frames:

```sh
# macOS/Linux, from the project directory
SDL_VIDEODRIVER=dummy python main.py --frames 5
```

PowerShell equivalent:

```powershell
$env:SDL_VIDEODRIVER = "dummy"
.\.venv\Scripts\python.exe main.py --frames 5
Remove-Item Env:SDL_VIDEODRIVER
```

`--frames` is optional and only for unattended checks. Normal play is `python main.py`. GitHub Actions tests Day 01 and Day 02 on every push/pull request.

### Manual acceptance checklist

- Move before launching: ball follows paddle and stops at both screen edges.
- Launch and bounce; different paddle impact positions change the angle.
- Hit a brick: it disappears and score rises by 10.
- Miss three times: score/bricks persist between lives, then Game over appears.
- Clear all bricks: Wall cleared appears.
- Press R from either outcome: 50 bricks, three lives and zero score return.
- Pause and switch apps: nothing advances while paused.
- Press Esc or close the window: the process exits cleanly.

## 5. Troubleshooting

- **`No module named pygame`:** install requirements with the exact Python interpreter you use to run the game. Activating a virtual environment changes which `python` command is used.
- **`python`/`python3` not found:** install Python from [python.org](https://www.python.org/downloads/); on Windows try `py`.
- **Install tries to compile pygame:** use Python 3.12 or 3.13 with a current pip (`python -m pip install --upgrade pip`). Newer Python versions may not have wheels for the pinned pygame release.
- **No video device:** the desktop app needs a graphical session. Use the dummy-driver commands only for tests; they intentionally show no window.
- **No window after a headless check:** unset `SDL_VIDEODRIVER` before normal play.
- **Keys do nothing:** click the game window to focus it. Space launches; arrows/A/D move; P resumes after focus loss.
- **Window seems frozen:** it may be paused. Check the on-screen prompt.
- **Can't find `main.py`:** run commands from `day-02-breakout`, not the repository root.

## 6. Tuning the game

Shared gameplay parameters live at the top of `game.py`; paddle geometry is defined in `Game.__init__()`. Because `main.py` imports layout constants, changes to brick size or spacing update both model and renderer automatically:

- **Ball and paddle**: Increase `BALL_SPEED` for a harder game; increase `PADDLE_SPEED` for easier control. Larger `BALL_SIZE` makes collisions easier to see.
- **Difficulty and scoring**: Fewer `INITIAL_LIVES` make the game harder. `POINTS_PER_BRICK` changes the score, not the difficulty.
- **Layout**: Adjust `BRICK_ROWS`, `BRICK_COLS`, `BRICK_WIDTH`, `BRICK_HEIGHT`, `BRICK_GAP_X`, `BRICK_GAP_Y` and the gaps around the paddle.
- **Physics**: Decrease `MAX_PHYSICS_STEP` (e.g., to 1/480) if higher speeds tunnel through thin bricks. Keep `MAX_FRAME_DT` small: raising it adds catch-up work after a stall.
- **Tests**: Some acceptance tests intentionally encode the default game settings. When changing the design, update those expectations as well as rerunning the suite.

Always run the test suite after tuning to ensure the model and renderer still agree on positions and timing.

## 7. Try a small change

1. Change the five row colours in `main.py`.
2. Change the paddle width, then test that its centre and edge clamps still work.
3. Add a second brick layout and tests for its size and score.
4. Add a session high score. Decide whether R resets it before coding.
5. Add sound later; initialise the mixer only when you need it.

## 8. References and attribution

This is an original educational implementation inspired by the classic Breakout game, not a reproduction of its source or artwork.

**Architecture notes:**

- Constants in `game.py` prevent the model and renderer disagreeing on speed, size, scoring or layout. This pattern scales to larger games.
- Previous position (`_prev_ball_x`, `_prev_ball_y`) detects collision entry direction without per-frame flags or separate broad/narrow phases.
- Small physics steps (1/240 sec) and a clamped frame delta avoid tunnelling without a full continuous-collision-detection system.
- String states (`"ready"`, `"playing"`, etc.) stay readable; enums add type safety but not simplicity for a small game.

- [pygame: Getting Started](https://www.pygame.org/docs/)
- [pygame: a basic game loop](https://www.pygame.org/docs/ref/pygame.html#quick-start)
- [pygame.time.Clock.tick](https://www.pygame.org/docs/ref/time.html#pygame.time.Clock.tick)
- [pygame event reference](https://www.pygame.org/docs/ref/event.html)
- [Python virtual environments](https://docs.python.org/3/library/venv.html)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [MDN: 2D collision detection](https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection)
- [Fix Your Timestep! — further reading on simulation timing](https://gafferongames.com/post/fix_your_timestep/)

## 9. Licence and dependencies

This project's own code and documentation are covered by the repository's [MIT licence](../LICENSE).

pygame is distributed under LGPL; see [its versioned LGPL 2.1 licence text](https://github.com/pygame/pygame/blob/2.6.1/docs/LGPL.txt). Its default font and other bundled components retain their upstream licences; they are installed with pygame, not stored in this repository. Our MIT licence does not relicense those dependencies. If distributing a packaged executable, review the licences and notices of everything included in that package. See [Third-party notices and project provenance](../THIRD_PARTY_NOTICES.md).

Breakout was originally released by Atari. This educational implementation is not affiliated with or endorsed by Atari.
