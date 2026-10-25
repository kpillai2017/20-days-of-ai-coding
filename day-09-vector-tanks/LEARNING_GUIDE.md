# From coordinates to a wireframe battlefield

This guide assumes you know very little Python. Read the commented source alongside it, run the game, then change **one thing at a time**. Keep a working copy so you can undo an experiment.

## 1. A game is a repeating conversation

```text
keyboard → Controls(throttle, turn, fire)
                    ↓
          Game.update(seconds, controls)
                    ↓
        positions / shells / lives / score
                    ↓
       Renderer.draw(game) → screen image
```

`main.py` repeats this about 60 times per second. `clock.tick(60)` limits frame rate and measures elapsed milliseconds. Dividing by 1000 gives seconds. Moving `speed * seconds` rather than a fixed distance per frame avoids making faster computers drive faster.

A single frame is capped at 0.1 second. A long pause must not suddenly advance several seconds of combat. The model subdivides accepted time into steps of at most 1/60 second. Time beyond the cap is **discarded**, not simulated later; this is a deliberate responsiveness choice, not perfect physical timekeeping.

## 2. A model that cannot open a window

`game.py` imports only Python's standard library. A **dataclass** is a compact way to describe a record:

```python
Controls(throttle=1, turn=0, fire=False)
```

This means full forward, no turning, no firing. Positive turn is right. `Enemy`, `Shell`, `Obstacle` and `Explosion` group the values that each entity needs. Frozen Controls and Obstacle records cannot be changed after construction; enemy positions and projectile timers must change, so those records are mutable.

`Game` owns the world lists, player coordinates, state and timers. Its constructor prepares a playing world; the desktop controller changes it to `title` until Enter is pressed. `start()` resets the run. `update()` does nothing outside `playing`, but rejects negative or nonfinite elapsed time.

## 3. Moving on a flat map

The simulation uses two coordinates, **x** (right) and **z** (forward), while rendering adds **y** (height).

```text
                 +z (heading 0)
                      ↑
                      |
       -x  ←----------+----------→ +x (heading π/2)
                      |
                      ↓ -z
```

For heading angle θ and speed v:

```text
vx = sin(θ) × v
vz = cos(θ) × v
x += vx × dt
z += vz × dt
```

At θ=0, sin is 0 and cos is 1, so you travel along +z. Angles use **radians**: π is half a turn, 2π a full turn. `wrap_angle` keeps heading differences near zero, so an enemy takes the short turn across the -π/π boundary.

Track controls are reduced to two numbers:

```text
throttle = (left_track + right_track) / 2
turn     = (left_track - right_track) / 2
```

Both tracks +1 mean forward. Left +1, right -1 means no forward motion and a right pivot. One track +1 and the other 0 gives a half-speed forward turn. It is an intuitive approximation: no suspension, wheel contact or inertia is simulated.

## 4. How a wireframe tank becomes 3D

`renderer.py` describes a mesh as **vertices** (3D points) and **edges** (pairs of vertex indexes). `box()` needs eight corners and twelve edges. The tank combines track boxes, hull, turret and barrel; the saucer uses two polygon rings.

First rotate a mesh around its local y axis, then translate it to its world x/z position. Then subtract the camera position and rotate by **minus the player's heading**. This converts world coordinates into camera coordinates: what is right, up and forward relative to your eye?

```text
world → subtract eye position → undo eye rotation → camera space
```

The player's eye height is 1.55 units. The projection is:

```text
screen_x = centre_x + focal_length × camera_x / camera_z
screen_y = horizon  - focal_length × camera_y / camera_z
```

Distant points have a larger denominator and look smaller. Minus on screen_y matters: world y goes up, but screen pixels increase downward. The focal length is in screen pixels, not a camera lens specification.

## 5. The near-plane trap

Dividing by zero depth crashes; dividing by negative depth flips objects behind your head onto the screen. A line can cross the eye plane even if one endpoint is visible.

```text
behind eye       near plane             visible
  A ----------- X ------------------------ B
                ↑ replace A with X
```

`project_segment` discards lines entirely behind depth 0.35. If only one endpoint is behind, linear interpolation finds the crossing and replaces that endpoint. Perspective division is safe after this. `Rect.clipline` clips projected segments to the cockpit viewport too. This is **clipping**, not hidden-surface removal: rear wireframe edges remain visible.

## 6. Don't let bullets teleport through tanks

A projectile moves along a segment during each update. Checking only its destination can miss a target between the old and new positions. This is called **tunnelling**.

```text
old shell -------- enemy -------- new shell
              hit here, even if endpoint is beyond
```

`segment_circle_t` solves where that segment first enters a target circle. It returns a fraction t between 0 and 1, or None. Starting inside returns 0, including stationary shells. The quadratic comes from substituting the segment into the circle equation.

`segment_box_t` intersects the allowed x/z intervals (the slab method). Boxes/pyramids use square footprints; cylinders use circles. Shells and tanks expand an obstacle footprint by their own collision radius, so the centre does not enter a wall before the edge notices it.

For a shell, compare all obstacle and target hit fractions and use the **smallest**. Otherwise a wall behind a target could incorrectly absorb a shot that already hit the target first. The square-expanded box corners are conservative, not exact rounded geometry.

Movement collides with cover and arena edges. Tank-versus-tank body collisions are not modelled. Shots ignore other shots; enemy shots do not hit other enemies. These simplifications belong in documentation, not hidden behind the word “physics.”

## 7. Enemy decisions are rules, not intelligence

Each enemy computes distance and bearing to the player. Tanks approach when far away, turn away when too close, and aim near their standoff distance. A shot needs a sufficiently small heading error and a clear line through cover. Supertanks move faster; saucers are moving bonus targets without guns.

Obstacle detection stops movement, but there is no path search or clever route around cover. The current AI may stay stuck. Difficulty nudges speed, spawn mix and shot cooldown as kills grow, with a maximum of three enemies.

A seeded `random.Random` instance belongs to the model. Audio noise uses another generator so making sound cannot change enemy spawns. Identical seeds alone are not enough for identical play: inputs and time steps also need to match.

## 8. Life, time and state

A player hit consumes one life, moves the player to the clear origin and starts an invulnerability timer. Other incoming shells during that timer are absorbed without another lost life. At zero lives the model becomes `game_over`; remaining physics substeps stop.

The renderer reads model state but does not change it. Pause belongs to the controller: it simply stops calling update. Focus loss also pauses. Holding fire is safe because the model enforces both a cooldown and the one-active-player-shell rule.

## 9. Sound without audio files

The optional mixer receives signed 16-bit samples stored in Python's `array('h')`. A sine wave supplies a tone; a little seeded noise adds texture. A fading envelope softens the end. The engine loop uses integer cycles to join its endpoints smoothly. This is original sound synthesis, not a reconstruction of the original arcade circuit.

Audio can fail on a headless machine. The code catches Pygame's device error and continues silently. `--mute` skips audio setup altogether.

## 10. Test before you tweak

From the day folder:

```sh
python -m unittest discover -s tests -v
```

Model tests construct known worlds rather than hoping random gameplay happens to produce a hit. Rendering tests use SDL's dummy video driver; they verify geometry and that an image can be drawn, not that an actual monitor looks correct. Play testing is still necessary for difficulty and feel.

Try these exercises:

1. Change forward speed. Explain why reverse speed remains different.
2. Draw a box on paper, number its corners, and find the twelve edges in `box()`.
3. Change camera eye height from 1.55 to 3. What happens to the horizon and nearby tanks?
4. Add a stationary enemy directly ahead and a wall behind it. Write a test proving the nearer enemy gets hit first.
5. Change the near plane and approach cover. Explain the effect without dividing by zero.
6. Add proper obstacle avoidance: first make a test where a tank must go around a box.
7. Add tank-body collision tests before implementing that feature.

## References

The [README](README.md#references-and-licence) links Pygame, Python, perspective-projection resources and licensing information. [History](HISTORY.md) separates the original arcade game from this educational tribute.
