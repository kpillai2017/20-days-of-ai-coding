# Build a clock from time, paths and sound

Read the commented source alongside this guide. The project uses no framework, downloaded image or sound sample. Browser APIs provide drawing and audio, while a separate pure module makes time logic testable.

## 1. Responsibilities before details

```text
clock.js     Date → hand/pendulum angles, quarter events, note descriptions
renderer.js  angles/options → preserved v0.1 illustration
camera.js    pointer coordinates → quaternion rotation → projection
renderer3d.js angles/camera → v0.2 solid polygon scene
audio.js     note descriptions → oscillator/noise audio
app.js       controls + wall time + visibility → coordinate everything
```

Deferred script tags load in dependency order after the document is parsed. Each file uses a function wrapper to keep its helpers private. The model is a browser global and a CommonJS export for Node tests; rendering/audio are browser-only.

## 2. A Date is an instant; getters provide local civil time

`Date.getTime()` is milliseconds since the Unix epoch, independent of local timezone. `getHours/getMinutes/getSeconds` describe that instant using device-local timezone rules. Do not substitute UTC getters if the user expects local time.

A clock hand needs a fraction of a turn:

```text
seconds = second + milliseconds / 1000
minutes = minute + seconds / 60
hours   = (hour % 12) + minutes / 60
angle   = fraction × 2π
```

Include smaller units to keep the minute/hour hands moving smoothly. The optional stepped second hand uses `floor(seconds)`. Canvas rotates clockwise because its y coordinate grows downward; the hand artwork starts at twelve, so no extra quarter-turn correction is needed.

Do not increment a stored second once per callback. Browser callbacks can be late or suspended. Read a new Date when drawing; time correction and DST then follow the OS on the next frame. This cannot correct a wrong OS clock.

## 3. Two clocks: wall time and audio time

Calendar time belongs to Date; Web Audio uses `AudioContext.currentTime`, a monotonic timeline in seconds for scheduling nodes. Never pass epoch milliseconds directly into `oscillator.start()`.

The scheduler detects an event from wall time, then audio schedules its notes relative to `currentTime + .03`. Each descriptor contains offset, frequency, duration and type. Separating the score from sound hardware lets tests inspect hour-strike counts without speakers.

## 4. Detect a crossed boundary, not an exact callback

A 50 ms poll is unlikely to land exactly on 12:15:00.000. The model instead remembers the previous timestamp, rounds a copy of the new local Date down to the minute, and checks whether a quarter boundary was crossed recently.

Safety rules matter:

- Initial poll/reset arms silently from now.
- A backward or non-advancing clock produces no event.
- Gaps over three seconds skip catch-up; an event over 1.5 seconds late is dropped.
- An epoch-key Set prevents replaying recent boundaries after backward corrections.
- The Set is capped at 192 entries, not saved to disk.
- A repeated DST local hour has new epoch instants and can sound again.

Hiding a tab cancels current audio and resets scheduling. Reopening never queues a day of missed bells. These rules favour polite foreground behaviour over guaranteed background alarms.

## 5. Canvas is stateful—save and restore deliberately

`ctx.save()` preserves transforms, styles and clipping; `restore()` undoes them. A gear can translate to its centre, rotate locally, draw spokes and restore without rotating the dial afterward.

The canvas has logical scene units 860×1120. Its backing size is multiplied by devicePixelRatio (capped at 2), and `setTransform` restores logical coordinates. CSS scales the displayed canvas responsively. Changing width/height resets the drawing state, so resize must set the transform again.

Scene order is the painter's algorithm: case, weights/pendulum, movement, dial, hands and glass. Later fills hide earlier ones. Radial/linear gradients make brass/ivory/wood without image textures. Grain lines use sine curves, not random downloads. Roman numerals use a system serif font.

## 6. A gear is a local path

The tooth outline visits four points per tooth, alternating root/crown radius. A dark inner circle opens the ring; five curved spokes and a hub complete the shape. This is stylised illustration, not an involute gear generator.

Each wheel's angle derives from epoch time, an alternating sign and a radius ratio. Adjacent visual gears appear to exchange direction. The ratios do not mechanically drive the hands. Freezing motion stores the current decorative angle fields only; time hands still use current Date values.

Pendulum angle is analytic sine, so no numerical integration drifts. Its energy/friction are not simulated. Read [MECHANISM.md](MECHANISM.md) before interpreting the illustration as engineering.

## 7. Tick from noise; bell from partials

A short deterministic noise buffer passes through a band-pass filter; alternate centre frequencies make tick/tock distinct. Once-per-second cues coincide with alternating endpoints of the two-second visual swing. Late beats are dropped rather than burst-replayed.

A bell combines sine oscillators at 1×, 2.71× and 4.13× its nominal frequency with different decay rates. Real bells have inharmonic modes, so simple noninteger ratios suggest a bell better than a pure tone. These frequencies are an original timbre recipe, not a sampled instrument model.

A gain envelope starts near silence, rises quickly and decays exponentially. Exponential ramps cannot target zero, so use a tiny positive floor. Nodes stop after their decay and remove themselves from the tracked Set on `ended`. Mute stops all queued nodes, avoiding future notes after the user disables sound.

## 8. Browser permission is a feature, not a bug

Construct/resume AudioContext from the sound button's user gesture, not page load. Failure is displayed in a polite status. The master GainNode controls all audio, including currently sounding tones. Mute and visibility cancellation clear the queue; manual previews replace existing queued chimes.

Reduced-motion preferences start the decorative mechanism still, but the correct time remains visible. The digital time element is a text alternative for canvas; it is not a per-second live announcement. Controls have labels and native keyboard behaviour. A beautiful canvas alone would not be enough to expose the clock's state.

## 9. Testing local time correctly

Tests construct `new Date(year, monthIndex, day, hour, minute, ...)` so boundaries are local to the test runner; don't assume every CI machine has your timezone. Expected strike counts use civil hours, while de-duplication uses epoch milliseconds.

Tests cover noon/midnight, fractional hand angles, short quarter scores, scheduler lateness, reset, backward corrections and invalid Dates. Browser checks must additionally validate canvas execution, audio permission/queue cancellation, toggles, responsive layout and no external requests. Automated audio-node checks do not establish what a human hears on real speakers.

## Experiments

1. Remove minute interpolation from the hour hand. Why is 3:30 then visually wrong?
2. Change pendulum period and move the tick-phase formula to match. What does that imply physically about effective length?
3. Add a gear with a matching pitch radius and reverse sign. Explain why that is still not a contact solver.
4. Add a quiet-hours option to the scheduler, with tests spanning midnight.
5. Add a selectable alternative original phrase while keeping hourly strike counts unchanged.
6. Try a custom timezone display carefully: local boundaries must then use that timezone, not just a reformatted digital label.

See [README](README.md#reference-project-and-rights) for the reference project's licence discrepancy, original-asset policy and API references.

## 10. A separate 3D renderer, not a flat-image trick

`renderer3d.js` constructs polygons in x/y/z. Boxes form the case, cylinders the dial/hubs, annular tooth segments the gears, and groups of faces the pendulum/anchor. Each frame rotates/project vertices through `Camera.project`, sorts faces by average camera depth and fills them with simple normal-based shading. This is real solid geometry rendered in software, with the known limitations of painter sorting rather than a z-buffer.

Our own v0.1 artist paints the dial onto an offscreen canvas. A crop of that dial is mapped to a planar face of the 3D cylinder using an affine transform. Under orthographic projection a rectangle stays a parallelogram, so that mapping is exact for a plane. The face is hidden when its normal points away. The casing/gears/pendulum are **not** textures cut from the flat clock.

### Why a quaternion trackball?

Clamping a yaw/pitch camera can prevent rolling and lock near its poles. A virtual trackball maps pointer x/y onto a unit sphere (smoothly continued outside it). The shortest rotation between the starting and current directions is a quaternion. Compose it with the quaternion saved at pointer-down, then normalise. Pointer event frequency does not accumulate drift because each move starts from the same saved pose.

A quaternion stores four rotation components; rotate a point with `q × [x,y,z,0] × conjugate(q)`. Unit quaternions preserve lengths. The tests check that invariant, opposite-direction edge cases, unrestricted drag directions and exact reset.

### Keep interaction independent of clock state

Pointer capture keeps a drag active when the pointer leaves the canvas. Release/cancel/lost capture all end it. CSS disables touch scrolling only on the 3D canvas; the original view still allows normal page scroll. Coordinates use the displayed CSS rectangle, not high-DPI backing pixels.

Switching views changes only which renderer consumes the same clock state. The camera quaternion, sound queue and time are not recreated. Reset restores only the camera quaternion. Version labels are feature labels in CHANGELOG, not repository tags. No Clock3D source or models enter either renderer.


### Gear-motion refinement

Both views now share `gears.js`: a common tooth module, exact pitch-circle contact distances, alternating directions and tooth-count-derived angular speeds. Contact-direction phases put each tooth crown against a neighbour's gap, including where the train turns a corner. A four-root-turn cycle bounds numeric angles without introducing a visual jump. All wheels remain driven by the same elapsed time; none runs an independent timer. The visible root speed is 0.28 radians/second for clarity, not a real clock reduction ratio.

The revised U-shaped layout avoids unrelated wheels overlapping. The 3D view reflects both y coordinates and tooth-angle direction consistently. This improves visual kinematic coherence but is still not an involute tooth-contact, force, friction or escapement simulation. Original v0.1 artwork remains the basis of the 2D view; its gear layout/motion received this correction in the combined app.
