# Day 07 · Engine Explorer

A rotatable **3D cutaway animation** of two-stroke and four-stroke spark-ignition engines, written in HTML, CSS and JavaScript. Switch the engine type, follow moving components and timed arrows, pause a stage, and rotate to inspect it.

No dependencies, installation, external assets, WebGL or build step. This is a small **software 3D renderer**: actual XYZ geometry is projected onto a native 2D canvas, not a movie or a flat image rotated with CSS.

## 1. Run

Open `day-07-engine-explorer/index.html` in a modern browser, keeping the files together. Or from the repository root:

```sh
cd day-07-engine-explorer
python3 -m http.server 8000 --bind 127.0.0.1
```

Windows: use `py` instead of `python3`. Visit **http://localhost:8000**; Ctrl+C stops the server. If 8000 is occupied, choose another port and update the URL. Python serves files; JavaScript does all animation in the browser. Node.js 20+ is optional for tests, not viewing.

Update a clone with `git pull`, or download/extract the latest repository ZIP.

## 2. Controls

| Control | Action |
| --- | --- |
| 4-stroke / 2-stroke | Switch mechanism, reset cycle angle to zero; preserve camera/play state |
| Play / Pause | Run or freeze crank motion and animated flow dots |
| Step 15° | Pause, then advance fifteen crank degrees |
| Reset cycle | Pause and return to zero; leave camera alone |
| Scrub slider | Pause and inspect any whole degree in the cycle |
| Stage buttons | Pause and jump to a representative stage |
| Speed | 0.1–2×; default **1× = one crank revolution per four seconds** |
| Drag/swipe viewport | Orbit the 3D camera |
| Arrow keys | Orbit **when the canvas is focused**; click/Tab into it first |
| On-screen arrows | Orbit using buttons, including on touch devices |
| Mouse wheel / + / − | Zoom within limits |
| Reset view | Restore camera orientation and zoom, not cycle state |

Four-stroke repeats after 720°; two-stroke after 360°. The timeline excludes the duplicate endpoint (719/359 is the final slider value). Stage buttons mark broad teaching stages; the live caption also distinguishes transfer-closed/exhaust-open and ignition subphases.

Motion starts automatically unless `prefers-reduced-motion` is enabled, in which case it starts paused. Turning reduced motion on also pauses an active animation. No audio, storage, network, tracking or AI API. Time in hidden tabs is not caught up: stalled frames are clamped/skipped to keep teaching motion readable.

## 3. What to look for

- **Silver piston/connecting rod:** the crank pin rotates; the piston can only slide up/down.
- **Rear half-cylinder:** retained shell. The front half is deliberately removed, not a real running opening. Rotate behind it to see occlusion.
- **Blue:** incoming fresh air–fuel mixture.
- **Green:** two-stroke transfer from crankcase into the cylinder.
- **Red:** burnt-gas exhaust.
- **Gold:** spark, compression or expansion/force cues; use the fixed stroke caption and side explanation to distinguish them.

A fixed caption beside the piston names the stroke (Intake, Compression, Power or Exhaust in four-stroke mode). In two-stroke mode it names the combined downstroke/upstroke processes; the detailed side panel explains the current port subphase. On small screens the caption sits above the mechanism to avoid covering it. Fixed captions explicitly name “Intake valve open”, “Exhaust valve open” or “Both valves closed”. Two-stroke captions instead identify exhaust/transfer ports and the crankcase reed inlet as open or closed. Short event captions below it explain “Air–fuel mixture enters”, “Spark ignites the charge”, expansion, exhaust and two-stroke crankcase transfer/filling at the appropriate angles. It stays still when the piston moves or the camera orbits; moving arrows and component points carry no text labels.

Arrows are always-visible teaching overlays, not depth-occluded physical objects or calculated fluid trajectories. The travelling dots demonstrate direction, not measured flow speed. A translucent cylinder fill cues the phase; it is not a pressure/temperature field.

**Four-stroke:** ideal head-valve timing shows intake, compression, power and exhaust over two revolutions. **Two-stroke:** a particular crankcase-scavenged, reed-inlet, piston-ported gasoline-style mechanism over one revolution. It is not a two-stroke diesel or a universal design for every two-stroke engine.

## 4. Read and learn

- [How the engines work](HOW_ENGINES_WORK.md): labelled diagrams, stroke sequences, port timings and explicit simplifications.
- [Beginner learning guide](LEARNING_GUIDE.md): model/view separation, slider-crank math, 3D camera/projection, events and exercises.

```text
day-07-engine-explorer/
├── index.html            # Labelled controls, canvas and textual state panel
├── style.css             # Responsive layout, focus and legend
├── engine.js             # Pure geometry/cycle state; Node and browser exports
├── renderer.js           # 3D mesh generation, camera, projection and drawing
├── app.js                # Controls, pointer/keyboard events and animation time
├── README.md
├── HOW_ENGINES_WORK.md
├── LEARNING_GUIDE.md
└── tests/
    └── engine.test.cjs   # Built-in Node runner; no dependencies
```

### Model API

`EngineModel.getState('four'|'two', angle)` returns phase, caption, cycle angle/length, piston/crank geometry, motion direction, valve/port/reed states, spark and qualitative charge/burn cues. Angles wrap, including negative inputs. Invalid modes/non-finite angles throw.

`crankPosition(angle)` returns `{x,y}`. `pistonPosition(angle)` returns piston-pin Y. `cycleDegrees(mode)` returns 720 or 360. `getEventCaptions(mode, angle)` returns the short phase-specific event captions. `getStages(mode)` returns independent copies of `{angle,title,...}` stage records. `normalizedAngle(angle, period=360)` wraps into a positive period.

Units are arbitrary: crank radius 0.6, connecting rod length 1.8. The pin travels from Y=2.4 (top) to Y=1.2 (bottom). The rendered piston crown is 0.25 above the pin. See the mechanics guide before treating these as dimensional engineering values.

## 5. Tests

From the repository root:

```sh
node --check day-07-engine-explorer/engine.js
node --check day-07-engine-explorer/renderer.js
node --check day-07-engine-explorer/app.js
node --test day-07-engine-explorer/tests/engine.test.cjs
```

From this folder: `node --test tests/engine.test.cjs`. Tests cover rod length, dead centres, actual piston direction, phase/valve boundaries, symmetric port heights, remaining exhaust-open interval, periodicity and validation. CI runs these alongside earlier projects.

### Browser checklist

1. Pause and drag/press arrow keys: geometry must change viewpoint without changing crank angle.
2. Reset view: original orientation returns; cycle stays unchanged.
3. Four-stroke: jump through each stage; check intake/exhaust states and labelled arrows.
4. Two-stroke: scrub 110° (blowdown), 150° (transfer and exhaust), 245° (transfer closed, exhaust open), 290° (both cylinder ports closed, crankcase inlet open).
5. Step, scrub, reset and change speed; confirm play/pause behavior above.
6. Try narrow/mobile screens and reduced-motion preference. Controls stay available and captions remain textual.

## 6. Limitations and troubleshooting

This is **kinematic teaching**, not combustion physics or engineering design. No gas dynamics, RPM-dependent timing, real pressure/temperature, camshaft drive, lubrication, cooling or inertia calculation. Valve/reed travel is schematic. Actual valve advance/overlap and port/reed timing vary by engine. Constant crank speed is imposed, not generated by the coloured combustion cue.

The painter's algorithm sorts triangles by average camera depth. Transparent/intersecting faces may show artifacts; it lacks a WebGL depth buffer. The crankshaft uses separate front/rear main journals and webs joined by an offset crank pin. The rod runs between those webs and meets the offset pin through its big-end bearing; there is no straight central shaft cutting through the rod plane at bottom dead centre. The crankcase/ducts are simplified shapes, and the cutaway intentionally removes material. Meshes are not manufacturing drawings.

- **Nothing moves:** click Play; reduced motion may have started paused. Enable JavaScript and check the Console for errors.
- **Arrow keys scroll:** focus the canvas or use on-screen camera buttons. Range sliders keep native arrow-key behavior when focused.
- **Inside obscured after orbit:** you may be behind the retained shell; Reset view returns to the cutaway side.
- **Slow device:** pause/scrub or use a smaller viewport; the renderer is intentionally simple CPU-side JavaScript.

Canvas is not a native accessible 3D widget. All controls have keyboard access, and stage captions/state are available as HTML, but the whole spatial diagram is not automatically screen-reader navigable.

## References and licence

Original code, shapes, arrows and prose created with AI coding assistance. No third-party libraries, images, models, fonts or audio bundled.

- [Four-stroke engine](https://en.wikipedia.org/wiki/Four-stroke_engine)
- [Two-stroke engine](https://en.wikipedia.org/wiki/Two-stroke_engine)
- [Slider-crank linkage](https://en.wikipedia.org/wiki/Slider-crank_linkage)
- [MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- [MDN requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
- [MDN Pointer events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)

Own code/docs: [MIT licence](../LICENSE). Linked references retain their authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
