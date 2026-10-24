/* Run with Node's built-in runner: node --test path/to/koan.test.cjs.
 * These tests call the SAME model as the browser without needing a DOM. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { generate, normalizeInput, MAX_LENGTH, createSession } = require("../koan.js");

for (const [word, theme] of [
  ["control", "control"], ["changing", "change"], ["perfect", "perfection"],
  ["time", "time"], ["identity", "identity"], ["friend", "relationships"],
  ["uncertain", "uncertainty"], ["bicycle", "attention"]
]) {
  test(`selects ${theme} for ${word}`, () => {
    const story = generate(`A question about ${word}?`);
    assert.equal(story.theme, theme);
    assert.equal(story.matched, theme !== "attention");
  });
}

test("input whitespace is normalised without losing punctuation", () => {
  assert.equal(normalizeInput("  Why\n is\tthis?  "), "Why is this?");
});
for (const invalid of [undefined, null, 32, {}, [], true]) {
  test(`rejects non-string ${JSON.stringify(invalid)}`, () => assert.throws(() => generate(invalid), TypeError));
}
for (const blank of ["", " ", "\n\t", "\u00a0"]) {
  test(`rejects blank ${JSON.stringify(blank)}`, () => assert.throws(() => generate(blank), RangeError));
}
test("accepts exactly the length limit", () => assert.equal(generate("x".repeat(MAX_LENGTH)).context.length, MAX_LENGTH));
test("rejects excessive raw length before whitespace normalisation", () => {
  assert.throws(() => generate("x".repeat(MAX_LENGTH + 1)), RangeError);
  assert.throws(() => generate(" ".repeat(MAX_LENGTH) + "x"), RangeError);
});
test("UTF-16 limit agrees with HTML maxlength, not emoji count", () => {
  assert.equal(generate("🌱".repeat(300)).context.length, 600);
  assert.throws(() => generate("🌱".repeat(301)), RangeError);
});
test("matching ignores case and punctuation", () => assert.equal(generate("PERFECT! Perfect?").theme, "perfection"));
test("matches whole words, not substrings", () => assert.equal(generate("Sometimes a timeless friendship forms.").theme, "attention"));
test("Unicode letters do not expose English substrings", () => assert.equal(generate("étime 時time").theme, "attention"));
test("non-English and punctuation-only inputs receive fallback", () => {
  for (const text of ["人生とは？", "🌱", "???"]) assert.equal(generate(text).theme, "attention");
});
test("repeating a keyword does not inflate its score", () => assert.equal(generate("perfect perfect perfect plan outcome").theme, "control"));
test("distinct matches beat earlier themes", () => assert.equal(generate("control perfect mistakes").theme, "perfection"));
test("ties choose the first theme in declared order", () => assert.equal(generate("change control").theme, "control"));
test("negation is intentionally not understood", () => assert.equal(generate("I do not want control").theme, "control"));

test("does not echo the input in title, poem or interpretation", () => {
  for (const input of ['The cow jumped over the moon', '<script>alert("hello")</script>', 'Why must my work be perfect?']) {
    const story = generate(input);
    assert.equal(story.context, input);
    for (const output of [story.title, ...story.lines, story.reading]) assert.ok(!output.includes(input));
  }
});
test("every telling has a complete reflection package", () => {
  for (const word of ["control", "change", "perfect", "time", "identity", "friend", "uncertain", "bicycle"]) {
    for (let variant = 0; variant < generate(word).variantCount; variant++) {
      const story = generate(word, variant);
      assert.equal(story.lines.length, 3);
      assert.equal(story.questions.length, 3);
      for (const text of [story.title, ...story.lines, story.reading, ...story.questions, story.practice]) {
        assert.equal(typeof text, "string");
        assert.ok(text.trim().length > 0);
        assert.ok(!text.includes("undefined"));
      }
      assert.equal(story.variant, variant);
      assert.ok(!story.lines.join("\n").includes(`“${word}”`));
    }
  }
});
test("all compositions differ and wrap at the actual pool size", () => {
  const count = generate("perfect").variantCount;
  const stories = Array.from({length: count}, (_, n) => generate("perfect", n));
  assert.equal(new Set(stories.map(s => s.lines.join("\n"))).size, count);
  assert.deepEqual(generate("perfect", count), stories[0]);
  assert.deepEqual(generate("perfect", Number.MAX_SAFE_INTEGER), generate("perfect", Number.MAX_SAFE_INTEGER % count));
});
for (const variant of [-1, 1.5, NaN, Infinity, "1", null, Number.MAX_SAFE_INTEGER + 1]) {
  test(`rejects invalid variant ${String(variant)}`, () => assert.throws(() => generate("hello", variant), RangeError));
}
test("generation is deterministic", () => assert.deepEqual(generate("What is my purpose?", 2), generate("What is my purpose?", 2)));
test("returned data cannot corrupt subsequent generations", () => {
  const before = generate("time");
  const mutated = generate("time");
  mutated.lines[0] = "oops";
  mutated.questions.push("oops");
  mutated.context = "changed";
  assert.deepEqual(generate("time"), before);
});

const signature = story => JSON.stringify([story.title, story.lines]);
test("reported cow prompt selects sky imagery, not the old stone fallback", () => {
  const story = generate("The cow jumped over the moon");
  assert.equal(story.motif, "sky");
  assert.match(story.lines.join(" "), /moon|star/i);
  assert.doesNotMatch(story.lines.join(" "), /garden gate|smooth stone/);
});
test("different unfamiliar inputs select different starting compositions", () => {
  assert.notEqual(signature(generate("The violet cupboard")), signature(generate("Seven silent spoons")));
});
for (const [input, motif] of [["My cat sleeps", "animals"], ["Rain over the river", "water"], ["My bicycle", "paths"], ["Writing code", "work"], ["A flowering tree", "plants"]]) {
  test(`concrete imagery selects ${motif}`, () => assert.equal(generate(input).motif, motif));
}
test("same-theme questions do not repeat in a shared session", () => {
  const session = createSession();
  const results = ["Why must I be perfect?", "Must everything be perfect?", "Why must I be perfect?"] .map(input => signature(session.next(input)));
  assert.equal(new Set(results).size, results.length);
});
test("a session exhausts the pool without any exact repetition", () => {
  const session = createSession(); const count = generate("moon").variantCount;
  const results = Array.from({length: count}, () => signature(session.next("moon")));
  assert.equal(new Set(results).size, count);
  assert.throws(() => session.next("moon"), /All available tellings/);
  assert.throws(() => session.next("another moon question"), /All available tellings/);
});
test("clear starts fresh and independent sessions do not share history", () => {
  const session = createSession(); const first = signature(session.next("moon"));
  assert.equal(signature(createSession().next("moon")), first);
  assert.notEqual(signature(session.next("moon")), first);
  session.clear(); assert.equal(signature(session.next("moon")), first);
});
test("invalid input does not consume a session composition", () => {
  const session = createSession(); assert.throws(() => session.next(" "));
  assert.equal(signature(session.next("moon")), signature(generate("moon")));
});
