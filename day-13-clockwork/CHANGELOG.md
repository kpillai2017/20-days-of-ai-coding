# Horologium versions

## v0.2 — Solid 3D exhibition view

- Refined both views with one shared, phase-locked gear train: common tooth module, exact pitch contacts, alternating tooth-count speeds and non-overlapping unrelated wheels. This updates the original 2D motion/layout while retaining its artwork.

- Added procedural solid case rails, dial cylinder, extruded toothed gears, spokes, axles, weights, anchor and pendulum.
- Added unrestricted quaternion trackball rotation by left-drag/touch, keyboard arrow rotation and Home/reset button.
- Added a view toggle, preserving time/audio and the original v0.1 illustration as the initial view.
- Reused our own painted dial as a planar texture on a solid face, rather than rotating the entire flat picture.
- Added camera unit tests and browser checks for geometry, dragging, reset and view switching.

## v0.1 — Original 2D illustration

- Walnut case, ivory dial, brass cutaway movement and pendulum illustration.
- Device-local time, original synthesised tick/tock, quarter phrases and hourly strikes.
- Audio opt-in/previews, volume, motion/reflection/label controls and reduced-motion support.

These are project feature labels, not Git tags or separate published releases. Both renderers are shipped in the same application. The v0.1 drawing implementation remains in `renderer.js`; shared controls may evolve without changing its artwork.
