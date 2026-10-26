/* Pure quaternion regressions require no browser or graphics dependencies. */
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const {
  Camera,
  unit,
  multiply,
  rotate,
  trackball,
  between,
} = require("../camera.js");
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
test("identity rotation preserves points", () =>
  assert.deepEqual(rotate([1, 2, 3], [0, 0, 0, 1]), [1, 2, 3]));
test("normalisation and composition preserve lengths", () => {
  const q = unit([1, 2, 3, 4]);
  close(Math.hypot(...q), 1);
  close(Math.hypot(...rotate([3, 4, 5], q)), Math.sqrt(50));
  const identity = multiply(q, [-q[0], -q[1], -q[2], q[3]]);
  identity.slice(0, 3).forEach((v) => close(v, 0));
  close(identity[3], 1);
});
test("trackball works inside and outside sphere", () => {
  for (const p of [
    [0, 0],
    [0.2, 0.3],
    [1, 1],
    [-8, 3],
  ])
    close(Math.hypot(...trackball(...p)), 1);
});
test("opposite direction rotation remains finite", () => {
  const q = between([1, 0, 0], [-1, 0, 0]);
  const p = rotate([1, 0, 0], q);
  close(p[0], -1);
  close(Math.hypot(...q), 1);
});
test("camera supports all drag directions and exact reset", () => {
  const camera = new Camera(),
    initial = camera.q.slice();
  for (const [x, y] of [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
    [2, 2],
    [-2, -2],
  ]) {
    camera.reset();
    camera.begin(0, 0);
    camera.drag(x, y);
    camera.end();
    assert.notDeepEqual(camera.q, initial);
    close(Math.hypot(...camera.q), 1);
    assert.ok(camera.project([2, 5, 1]).every(Number.isFinite));
  }
  camera.reset();
  assert.deepEqual(camera.q, initial);
});
test("drag is based on initial pose rather than event count", () => {
  const a = new Camera(),
    b = new Camera();
  a.begin(0, 0);
  b.begin(0, 0);
  a.drag(0.2, 0.1);
  a.drag(0.4, 0.3);
  b.drag(0.4, 0.3);
  assert.deepEqual(a.q, b.q);
  a.end();
  const before = a.q.slice();
  a.drag(0.9, 0.9);
  assert.deepEqual(a.q, before);
});
test("repeated drags never lose unit-length rotation", () => {
  const c = new Camera();
  for (let i = 0; i < 500; i++) {
    c.begin(0.1, 0);
    c.drag(Math.sin(i), Math.cos(i));
    c.end();
  }
  close(Math.hypot(...c.q), 1);
  const p = rotate([2, 3, 4], c.q);
  close(Math.hypot(...p), Math.sqrt(29));
});
