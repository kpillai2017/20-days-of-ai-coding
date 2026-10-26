/* Verify meshing constraints, not merely that wheel angles change. */
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const { build, angles } = require("../gears.js");
const TAU = Math.PI * 2;
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-7, `${a} != ${b}`);
test("one common module makes every tooth pitch identical", () => {
  const train = build();
  for (const gear of train) close(gear.r / gear.n, 2);
});
test("successive pitch circles meet, unrelated wheels do not overlap", () => {
  const train = build();
  for (let i = 0; i < train.length; i++)
    for (let j = i + 1; j < train.length; j++) {
      const a = train[i],
        b = train[j],
        d = Math.hypot(a.x - b.x, a.y - b.y);
      if (j === i + 1) close(d, a.r + b.r);
      else assert.ok(d > a.r + b.r + 6);
    }
});
test("contact pitch velocities match with opposite rotation", () => {
  const train = build();
  for (let i = 1; i < train.length; i++) {
    close(train[i - 1].speed * train[i - 1].r, -train[i].speed * train[i].r);
    assert.notEqual(Math.sign(train[i - 1].speed), Math.sign(train[i].speed));
  }
});
test("teeth and gaps remain complementary at every contact over time", () => {
  const train = build();
  for (const t of [0, 0.1, 1, 5, 23, 100, 1770000000]) {
    const rotation = angles(t);
    for (let i = 1; i < train.length; i++) {
      const a = train[i - 1],
        b = train[i],
        phi = Math.atan2(b.y - a.y, b.x - a.x);
      const combined =
        (a.n * (phi - rotation[i - 1]) + b.n * (phi + Math.PI - rotation[i])) /
        TAU;
      close(((combined % 1) + 1) % 1, 0.25); // 1.25 modulo 1 for 3/8-crown-centred profiles.
    }
  }
});
test("all wheels visibly rotate and a four-root-turn cycle closes", () => {
  const train = build(),
    a = angles(1),
    b = angles(1.25),
    cycle = (TAU * 4) / 0.28;
  for (let i = 0; i < train.length; i++) {
    assert.ok(Math.abs(b[i] - a[i]) > 0.05);
    close(Math.sin(angles(1 + cycle)[i]), Math.sin(a[i]));
    close(Math.cos(angles(1 + cycle)[i]), Math.cos(a[i]));
  }
});
test("invalid times rejected and returned layouts independent", () => {
  for (const t of [NaN, Infinity, undefined])
    assert.throws(() => angles(t), RangeError);
  const a = build();
  a[0].r = 99;
  assert.equal(build()[0].r, 40);
});
