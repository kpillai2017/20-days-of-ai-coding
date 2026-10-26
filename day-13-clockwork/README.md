# Day 13 · Horologium

An original **mechanical analog clock illustration**, drawn in Canvas with walnut casing, ivory dial, brass gears, an anchor, pendulum and hanging weights. Hands synchronise with your device's local time. Web Audio generates tick/tock, quarter-hour phrases and hour strikes from scratch.

## Run

Open `index.html` in a current Chrome, Firefox, Safari or Edge browser. No packages, account, build or network service is required. Alternatively, from the repository root:

```sh
cd day-13-clockwork
python3 -m http.server 8000 --bind 127.0.0.1
```

Visit **http://127.0.0.1:8000**; Ctrl+C stops the server. Windows can use `py`. Python is optional and only serves files. Read Markdown docs on GitHub or in an editor if local links display raw text/downloads.

## Versioned views

- **2D · v0.1** is the original illustration and remains the initial view. Its artwork stays in `renderer.js`.
- **3D · v0.2** is a separate solid-geometry renderer, not a CSS rotation of the original image. Select **Switch to 3D / Switch to 2D · v0.1** to toggle.
- In 3D, **left-click and drag in any direction** to rotate the whole clock: horizontal/vertical turns and roll are unconstrained. Touch dragging works too. Focus the canvas and use arrow keys as an alternative.
- **Reset 3D view** or **Home** restores the default three-quarter view. It does not reset time, mute audio, restart chimes or change motion preferences.
- Switching views preserves the camera until explicitly reset and shares one local-time/audio controller. The reset button is disabled in 2D; 2D remains a non-draggable illustration so touch scrolling stays normal there.

See [CHANGELOG](CHANGELOG.md). These labels do not create Git tags or separate releases.

## Controls and time

- **Enable sound / Mute sound:** opt in to audio; browsers prohibit automatic sound before a user gesture. Muting immediately cancels queued notes.
- **Volume:** applies to both ticks and bells, including notes already sounding.
- **Tick & tock / quarter-hour chimes:** select which automatic sounds play.
- **Preview quarter / Preview hour:** hear the sound without waiting. Sound must first be enabled; previews do not change time or scheduled boundary history. A new preview replaces any current chime queue.
- **Mechanism labels, glass reflections:** optional illustration details.
- **Sweep second hand:** continuous seconds rather than one-second jumps; hour/minute hands interpolate either way.
- **Animate mechanism:** freeze decorative gears/pendulum while hands continue to display the correct time. Reduced-motion preferences start with this off.
- **Sync / refresh time:** reread device time and rearm sound scheduling without replaying missed bells.

The OS/browser supplies local time and timezone, including changes such as daylight-saving time. The app does **not** query NTP, correct an inaccurate computer clock or set system time. No alarm/time-setting interface is provided. A tab is not a reliable background clock appliance: browser sleep, autoplay restrictions and timer throttling can suppress sound. Hidden tabs are silent and missed events are dropped, not replayed on return.

## Chime schedule

| Local time | Sound |
| --- | --- |
| :15 | One four-note phrase |
| :30 | Two four-note phrases |
| :45 | Three four-note phrases |
| :00 | Four phrases, then 1–12 strikes for the hour |

Midnight/noon strike twelve. The four phrases are original arrangements, not a claim of an exact Westminster/Big Ben sequence. Tick and tock alternate once per second at pendulum endpoints; the pendulum has a visual two-second period. Previews can replace a currently sounding automatic sequence; ticks may sound underneath chimes if enabled.

Scheduling recognises a recently crossed local boundary, tolerates small callback delays, skips long gaps/large corrections and remembers recent epoch boundaries to avoid duplicates after backward clock changes. A repeated DST hour has different epoch times and may chime again. Opening/enabling sound exactly at a boundary intentionally does not replay it. Audio missed while disabled is never queued.

## How mechanical is it?

The **v0.1 view** is a layered 2D/2.5D illustration. The **v0.2 view** uses real procedural 3D polygon coordinates: a solid open-backed exhibition case, extruded toothed annuli/spokes, dial cylinder, axles, weights and swinging pendulum. It uses an **orthographic camera**, Canvas polygon drawing and average-depth painter sorting, not WebGL, ray tracing or a z-buffer. Intersecting polygons can show sorting artifacts. The front dial reuses our own v0.1 painted surface, affinely mapped onto its solid face; the rest of the clock is independently constructed 3D geometry. The back is intentionally open, exposing the movement rather than a finished opaque rear panel.

Neither view is a physics simulation or manufacturing design. Adjacent illustrative gears reverse direction with pitch-radius-related speeds; decorative teeth approximate spur gears rather than involutes. Some overlapping wheel/bridge elements are artistic simplifications. System time drives the model, not the pendulum. Weights do not descend, hands are not mechanically geared from the train, and there is no winding/power reserve. Glass controls a dial highlight, not a full transparent/refractive case shell.

Read [the mechanism explanation](MECHANISM.md) and [beginner code tour](LEARNING_GUIDE.md).

## Files and tests

- `clock.js`: pure angles, boundary events, musical score descriptors and scheduler.
- `renderer.js`: preserved original v0.1 procedural illustration.
- `camera.js`: pure quaternion rotation, virtual trackball and projection.
- `renderer3d.js`: separate v0.2 solid geometry and depth-sorted drawing.
- `audio.js`: browser audio setup, synthesis, queue cancellation and volume.
- `app.js`: local Date sampling, controls, visibility and drawing loop.
- `tests/clock.test.cjs`: Node's built-in test runner; no npm packages.

From the repository root, Node.js 22+:

```sh
node --test day-13-clockwork/tests/*.cjs
node --check day-13-clockwork/clock.js
node --check day-13-clockwork/renderer.js
node --check day-13-clockwork/camera.js
node --check day-13-clockwork/renderer3d.js
node --check day-13-clockwork/audio.js
node --check day-13-clockwork/app.js
```

Manual checks: compare hands/digital time with the device clock, enable audio and preview each sequence, change volume, mute during a chime, hide/return to the tab, toggle mechanism motion toggle 2D/3D, drag to front/back/side/upside-down orientations, reset the camera, and try a narrow screen. Automated tests validate scheduling and browser execution, not the subjective timbre on your speakers.

## Reference project and rights

The requested example was [OetkenPurveyorOfCode/Clock3D](https://github.com/OetkenPurveyorOfCode/Clock3D). We reviewed its README and root licence as design context on 26 October 2026. **Its README says GPLv3, while its LICENSE file contains AGPLv3.** It also credits separately licensed model, tick sound and icon assets. This project neither resolves nor relies on that discrepancy: **no Clock3D source, models, meshes, texture, icon or recording is copied, ported or bundled**. Its C/raylib implementation is not the basis of our browser code.

All own code, procedural geometry/illustration, generated sound and educational prose are original AI-assisted work under the repository [MIT licence](../LICENSE). There are no third-party runtime libraries, fonts, downloaded art or samples. External references retain their authors' rights and imply no endorsement. See [notices](../THIRD_PARTY_NOTICES.md).

Further learning:

- [Britannica: pendulum](https://www.britannica.com/science/pendulum) and [escapement](https://www.britannica.com/technology/escapement).
- MDN: [Date](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date), [Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial), [Web Audio](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API), [autoplay guidance](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay), [Page Visibility](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).


### Gear-motion refinement

Both views now share `gears.js`: a common tooth module, exact pitch-circle contact distances, alternating directions and tooth-count-derived angular speeds. Contact-direction phases put each tooth crown against a neighbour's gap, including where the train turns a corner. A four-root-turn cycle bounds numeric angles without introducing a visual jump. All wheels remain driven by the same elapsed time; none runs an independent timer. The visible root speed is 0.28 radians/second for clarity, not a real clock reduction ratio.

The revised U-shaped layout avoids unrelated wheels overlapping. The 3D view reflects both y coordinates and tooth-angle direction consistently. This improves visual kinematic coherence but is still not an involute tooth-contact, force, friction or escapement simulation. Original v0.1 artwork remains the basis of the 2D view; its gear layout/motion received this correction in the combined app.
