# Engine Explorer: from crank angle to a 3D picture

Start with [setup and controls](README.md) and [the mechanics guide](HOW_ENGINES_WORK.md). This code tour connects ordinary JavaScript functions to a moving, rotatable machine.

## 1. Read in small steps

1. Pause and Step 15°. Watch the angle, piston direction and caption.
2. Read `crankPosition()` and `pistonPosition()` in `engine.js`.
3. Read `getState()` to see how one angle produces different two-/four-stroke states.
4. Read `app.js`: follow a stage button through pause → angle assignment → `paint()`.
5. Read `renderer.js`: `setupCamera()`, `project()`, then `build()` and `render()`.
6. Run a geometry test. Change a drawing colour before trying structural changes.

No 3D library is hidden here. The intentionally small renderer is less capable than a full graphics engine, but its entire coordinate path is available to study.

## 2. Separate data, pictures and events

```text
input / elapsed time (app.js)
              ↓
     mode + crank angle
              ↓
        getState()             engine.js: pure model
              ↓
    piston/ports/caption
              ↓
    build → project → paint    renderer.js: 3D view
              ↓
     canvas + HTML state       app.js updates text too
```

`getState()` reads arguments and returns a new object. It doesn't read a clock or draw anything. Tests can ask about exactly 245° and check that exhaust is open while transfer is closed.

`const` prevents rebinding a name, not mutation of its object. Internal shared stage definitions are returned as copies so callers don't accidentally edit the model's future results.

## 3. Model the linkage rather than guessing a sine wave

Crank angle is in degrees for people; `Math.sin` and `Math.cos` need radians:

```js
const theta = angle * Math.PI / 180;
```

The crank pin moves on a circle. The piston pin moves on a straight line. Fixed rod length connects them:

```js
const crankX = r * Math.sin(theta);
const crankY = r * Math.cos(theta);
const pistonY = crankY + Math.sqrt(L * L - crankX * crankX);
```

The positive square root selects the piston above the crank. With r=0.6, L=1.8, expect piston Y=2.4 at 0° and 1.2 at 180°. From 0→180 the height decreases: the piston moves **down**. Don't swap direction merely because angle is increasing.

A useful invariant is `hypot(crankX, pistonY-crankY) === L` within floating-point tolerance. Tests check it over many angles rather than just one screenshot.

## 4. One revolution isn't always one complete cycle

Four-stroke uses angle modulo 720; two-stroke modulo 360. Geometric crank position repeats every 360 in both cases. At four-stroke 0° and 360° the geometry matches, but valve/charge phase differs.

JavaScript `%` is a remainder, which can be negative. `((angle % period)+period)%period` wraps negative angles to the expected positive range. Validate finite numbers first; NaN shouldn't quietly become invisible geometry.

Port timing is an illustrative state rule. Roof heights use the same piston formula at 105° and 120°, so the drawing's port levels agree with the model's opening/closing angles. Cylinder compression isn't called fully trapped while exhaust remains exposed at 240–255°.

## 5. Real 3D needs three coordinates

A vertex is `[x,y,z]`:

- X: left/right in the engine frame.
- Y: vertical height.
- Z: front/back depth.

`box()` creates eight corner points and six rectangular faces. `quad()` splits a rectangle into two triangles. `tube()` makes round parts from short surface segments; arbitrary endpoints let the connecting rod tilt with the crank.

The crankshaft is built as two separated main-journal segments, two offset webs and a crank pin. The rod stays in the centre plane between the webs. A continuous on-axis tube across that plane would intersect the rod at bottom dead centre; tests inspect the actual emitted primitives to guard against this mistake.

The tube builder finds an axis, then two perpendicular vectors around that axis. Sine/cosine combine those vectors to create rings of vertices. A partial angular range leaves only the rear half-cylinder, creating a genuine opening instead of a fully opaque cylinder hiding the piston.

Increasing segment count makes round parts smoother but creates more triangles to sort and draw. More polygons are not free on a small CPU-side renderer.

## 6. Orbit the camera, don't deform the engine

`yaw` rotates the viewpoint around the vertical axis. `pitch` changes its elevation. The camera always looks toward a target near the mechanism's centre.

`setupCamera()` computes:

```text
forward = unit(target − eye)
right   = unit(cross(forward, worldUp))
up      = cross(right, forward)
```

- **unit:** normalize a vector to length 1.
- **dot:** measure how much one vector points along another.
- **cross:** create a vector perpendicular to two vectors.

Pitch is clamped to avoid looking exactly along worldUp, where the cross product would have zero length. Zoom changes a bounded projection scale. The mechanism's world coordinates stay unchanged while the camera changes.

## 7. Project into pixels

For a world point, subtract the camera eye and take dot products with the camera axes. Depth is its distance along forward. Perspective projection divides horizontal/vertical offsets by depth:

```text
screenX = canvasCentreX + cameraX × focal / depth
screenY = canvasCentreY − cameraY × focal / depth
```

The minus sign flips world-up to screen-down. Farther objects project smaller. This code uses vector formulas directly rather than building explicit 4×4 matrices; full graphics engines often express the same transformations with matrices.

The canvas drawing buffer scales with device-pixel ratio (capped at 2). The context transform lets drawing still use CSS pixels. Only resize the buffer when dimensions actually change: resizing every frame would unnecessarily clear/reallocate it.

## 8. Which face should cover another?

`render()` sorts triangles from far to near by average depth and paints in that order: the **painter's algorithm**. It is easy to understand, but not as robust as a depth buffer. Intersecting faces and translucent gas cues can sort imperfectly.

The scene deliberately avoids relying on exact transparency for its core visibility: the cylinder's front half is removed. Arrow overlays are drawn last so flow cues remain visible even when orbiting. Stroke text is a fixed HTML overlay beside the piston, not a label attached to moving geometry. This is intentional explanatory visibility, not physically correct occlusion.

## 9. Arrow timing and captions

The model returns flags such as `intakeOpen`, `transferOpen` and `spark`. `build()` only adds the appropriate arrows/geometry for those flags. Flow points are a list of XYZ coordinates; the last segment supplies the arrowhead direction.

An interpolated dot travels along the projected segments. Its motion reinforces direction, but is not a particle solver. Fixed event captions from `getEventCaptions()` name mixture entry, spark, expansion and gas exchange; they do not travel with arrows. The detailed captions explain the causal sequence in HTML while controls expose exact port/valve states.

The combustion fill is qualitative. A gold cylinder doesn't mean a measured temperature, and a force arrow doesn't calculate torque. Learn to distinguish model inputs, computed kinematics and illustrative overlays.

## 10. Events and time

A stage button pauses and sets a crank angle. Scrubbing does the same with a slider. Pointer events capture one drag so a release outside the canvas doesn't leave the camera stuck. Arrow keys are intercepted only while the canvas has focus; other controls keep their native keyboard behavior.

Animation uses `requestAnimationFrame` timestamps:

```text
dt = min(seconds since last frame, 0.05)
angle += dt × 90 × speed
```

At speed 1, 90°/s means four seconds per revolution. Time is not measured by counting frames. Hidden-tab visibility resets the timestamp; large stalls are not caught up. This is a readable teaching animation, not a real-time engine-performance measurement.

Reduced-motion preference starts playback paused. A paused scene doesn't continuously rebuild geometry; camera edits and resizes still redraw on demand. Piston position and flow-dot phase remain frozen until play/step/scrub changes state.

## 11. Tests and a debugging experiment

Run `node --test tests/engine.test.cjs` from this folder. No npm dependencies are required. Tests use Arrange→Act→Assert: choose mode/angle, compute state, compare to expected geometry or flags.

Try in Developer Tools Console:

```js
EngineModel.getState('four', 360); // power, piston at TDC
EngineModel.getState('two', 245);  // transfer closed; exhaust open
EngineModel.pistonPosition(0);    // 2.4 (floating-point tolerance applies)
```

These standalone calls don't change the UI. Set a breakpoint inside `paint()`, click a stage, and inspect `mode`, `angle` and `state`. Continue before trying to drag the view: a paused debugger cannot process pointer events normally.

## 12. Exercises with observable results

1. **Colour experiment:** change `C.piston` in renderer.js. Expect only the piston material colour to change; port timing tests should remain unchanged.
2. **Direction prediction:** compare 90° and 270°. Both are between dead centres, but one moves down and the other up. Verify with `getState()`.
3. **Timing experiment:** before editing exhaust opening, work out the symmetric closing angle `360-opening`, update the state rule and corresponding renderer roof height, and write boundary tests. Don't change only the caption.
4. **Better renderer:** add face-normal shading or a depth-buffer renderer. Preserve camera controls and document whether overlays still ignore occlusion.

References: [MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial), [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame), [Pointer events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events), [slider-crank linkage](https://en.wikipedia.org/wiki/Slider-crank_linkage).

Own code/docs: [MIT licence](../LICENSE). Linked material retains its authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
