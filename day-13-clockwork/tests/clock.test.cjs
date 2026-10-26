/* Pure-time tests need no canvas/audio or installed packages. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { state, chimeAt, score, createScheduler } = require("../clock.js");
const TAU = Math.PI * 2;
/** Construct LOCAL dates so the tests do not assume the test runner's timezone. */
const date = (h, m = 0, s = 0, ms = 0) => new Date(2026, 9, 26, h, m, s, ms);
const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);

for (const hour of [0, 1, 3, 6, 9, 12, 15, 23]) {
  test(`hands at local hour ${hour}`, () => {
    const s = state(date(hour));
    close(s.hour, ((hour % 12) / 12) * TAU);
    close(s.minute, 0);
    close(s.second, 0);
  });
  test(`hour ${hour} has correct strike count`, () => {
    const e = chimeAt(date(hour));
    assert.equal(e.strikes, hour % 12 || 12);
    assert.equal(e.groups, 4);
    assert.equal(e.quarter, 0);
  });
}
test("hands interpolate minute/hour but seconds optionally jump", () => {
  const d = date(3, 30, 15, 500),
    s = state(d),
    smooth = state(d, true);
  close(s.hour, ((3 + (30 + 15.5 / 60) / 60) / 12) * TAU);
  close(s.minute, ((30 + 15.5 / 60) / 60) * TAU);
  close(s.second, (15 / 60) * TAU);
  close(smooth.second, (15.5 / 60) * TAU);
});
test("pendulum has two-second period and one-second-separated extremes", () => {
  close(state(date(1, 0, 0, 500)).pendulum, 0.19);
  close(state(date(1, 0, 1, 500)).pendulum, -0.19);
  // Epoch multiplication can lose tiny precision; visual values remain periodic.
  assert.ok(Math.abs(state(date(1, 0, 2, 500)).pendulum - 0.19) < 1e-8);
});
for (const [minute, groups] of [
  [15, 1],
  [30, 2],
  [45, 3],
]) {
  test(`quarter ${minute}: shorter phrase with no hour strikes`, () => {
    const e = chimeAt(date(10, minute));
    assert.equal(e.groups, groups);
    assert.equal(e.strikes, 0);
    assert.equal(score(e).length, groups * 4);
    assert.ok(score(e).every((n) => n.type === "chime"));
  });
}
test("non-boundaries never chime", () => {
  for (const d of [
    date(1, 14, 59),
    date(1, 15, 0, 1),
    date(1, 15, 1),
    date(1, 1),
  ])
    assert.equal(chimeAt(d), null);
});
test("hour score has ordered finite tones followed by strikes", () => {
  const notes = score(chimeAt(date(12)));
  assert.equal(notes.length, 28);
  assert.equal(notes.filter((n) => n.type === "strike").length, 12);
  notes.forEach((n, i) => {
    assert.ok(n.at >= 0 && n.frequency > 0 && n.duration > 0);
    if (i) assert.ok(n.at > notes[i - 1].at);
  });
  assert.equal(
    notes.slice(0, 16).every((n) => n.type === "chime"),
    true,
  );
});
test("scheduler arms silently and detects a crossed boundary once", () => {
  const s = createScheduler();
  s.reset(date(10, 14, 59, 800));
  assert.equal(s.poll(date(10, 15, 0, 50)).length, 1);
  assert.deepEqual(s.poll(date(10, 15, 0, 100)), []);
});
test("opening at an exact boundary is silent", () => {
  const s = createScheduler();
  assert.deepEqual(s.poll(date(10, 15)), []);
  assert.deepEqual(s.poll(date(10, 15, 0, 100)), []);
});
test("resume/jump drops catch-up chimes", () => {
  const s = createScheduler();
  s.reset(date(10, 14, 59));
  assert.deepEqual(s.poll(date(10, 30, 0, 20)), []);
  s.reset(date(10, 44, 59));
  assert.deepEqual(s.poll(date(10, 45, 4)), []);
});
test("late ordinary callback can still sound a just-crossed boundary", () => {
  const s = createScheduler();
  s.reset(date(10, 14, 59, 900));
  assert.equal(s.poll(date(10, 15, 1)).length, 1);
});
test("backward clock correction cannot replay a seen epoch boundary", () => {
  const s = createScheduler();
  s.reset(date(10, 14, 59, 900));
  assert.equal(s.poll(date(10, 15, 0, 50)).length, 1);
  assert.deepEqual(s.poll(date(10, 14, 59, 900)), []);
  assert.deepEqual(s.poll(date(10, 15, 0, 50)), []);
});
test("rearming preserves de-duplication history", () => {
  const s = createScheduler();
  s.reset(date(10, 14, 59, 900));
  s.poll(date(10, 15, 0, 50));
  s.reset(date(10, 14, 59, 950));
  assert.deepEqual(s.poll(date(10, 15, 0, 50)), []);
});
test("polling a non-quarter minute produces no event", () => {
  const s = createScheduler();
  s.reset(date(10, 13, 59, 900));
  assert.deepEqual(s.poll(date(10, 14, 0, 50)), []);
});
test("local dates roll over midnight and hour twelve correctly", () => {
  const s = createScheduler();
  s.reset(date(23, 59, 59, 900));
  const e = s.poll(new Date(2026, 9, 27, 0, 0, 0, 50))[0];
  assert.equal(e.strikes, 12);
});
test("invalid dates and scores are rejected", () => {
  for (const d of [new Date(NaN), null, 0, "today"]) {
    assert.throws(() => state(d), RangeError);
    assert.throws(() => chimeAt(d), RangeError);
    assert.throws(() => createScheduler().poll(d), RangeError);
  }
  assert.throws(() => score({ quarter: 4 }), RangeError);
});
