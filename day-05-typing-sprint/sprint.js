/* Typing rules are ordinary JavaScript, independent of HTML and real clocks.
   Tests supply timestamps; the browser supplies performance.now(). This makes
   boundary cases reproducible without waiting a whole minute per test. */
(() => {
  "use strict";
  const DURATION_MS = 60_000;
  // Original, single-line ASCII passages: no quotation rights or remote fetches.
  // Frozen records prevent accidentally changing a shared practice passage.
  const PASSAGES = Object.freeze([
    Object.freeze({ id: "small-steps", title: "Small steps", text: "A small step can change the shape of a day. Open the window, stretch your hands, and choose one useful thing to do. Work at a steady pace rather than a hurried one. When a mistake appears, pause and correct it. Progress grows from patient practice, not from a perfect first attempt." }),
    Object.freeze({ id: "garden", title: "The quiet garden", text: "Beyond the gate, a narrow path winds between herbs and bright flowers. A little bird waits on the fence while rain gathers on the leaves. Someone has left a blue watering can beside the bench. Sit for a moment, notice the sounds around you, and let the busy afternoon become a little quieter." }),
    Object.freeze({ id: "build", title: "Build and learn", text: "Start with a clear question and a simple plan. Build the smallest version that can answer it, then try it with real examples. Read the result carefully and explain what happened in your own words. Good tools help us explore, but understanding comes from asking questions, testing ideas, and trying again." })
  ]);

  function requireTarget(target) {
    if (typeof target !== "string" || target.length === 0) {
      throw new TypeError("target must be a nonempty string");
    }
  }

  function requireTime(value, name) {
    if (!Number.isFinite(value) || value < 0) {
      throw new RangeError(`${name} must be a finite nonnegative number`);
    }
  }

  /** Compare by POSITION, including spaces, case and punctuation. This isn't
      edit-distance matching: inserting a character shifts later comparisons.
      JavaScript length/indexing counts UTF-16 units. Our ASCII passages avoid
      a unit-versus-visible-character mismatch; arbitrary Unicode may not. */
  function analyzeText(target, input) {
    requireTarget(target);
    if (typeof input !== "string") throw new TypeError("input must be a string");
    let correct = 0;
    for (let index = 0; index < input.length; index++) {
      if (input[index] === target[index]) correct += 1;
    }
    const typed = input.length;
    return { correct, incorrect: typed - correct, typed,
      accuracy: typed === 0 ? 100 : correct / typed * 100,
      complete: input === target };
  }

  /** A conventional typing 'word' is FIVE characters, not a dictionary word.
      Count matching characters only. At zero elapsed time speed is undefined,
      so show 0 rather than Infinity. The very first live WPM can be unstable. */
  function calculateStats(target, input, elapsedMs) {
    requireTime(elapsedMs, "elapsedMs");
    const analysis = analyzeText(target, input);
    return { ...analysis, elapsedMs,
      remainingMs: Math.max(0, DURATION_MS - elapsedMs),
      wpm: elapsedMs === 0 ? 0 : (analysis.correct / 5) / (elapsedMs / 60_000) };
  }

  class Session {
    constructor(target, durationMs = DURATION_MS) {
      requireTarget(target);
      requireTime(durationMs, "durationMs");
      if (durationMs === 0) throw new RangeError("durationMs must be positive");
      this.target = target;
      this.durationMs = durationMs;
      this.reset();
    }

    /** null means 'not started'; 0 is a perfectly valid starting timestamp. */
    reset() {
      this.input = "";
      this.startedAt = null;
      this.finishedAt = null;
      this.state = "ready";
      this.reason = null;
      this.lastNow = null;
    }

    checkNow(now) {
      requireTime(now, "now");
      if (this.lastNow !== null && now < this.lastNow) {
        throw new RangeError("time must not move backwards");
      }
    }

    /** Resolve expiry BEFORE accepting input. A background tab might not call
        us until much later: the deadline, not the callback, is the finish time. */
    tick(now) {
      this.checkNow(now);
      this.lastNow = now;
      if (this.state === "running" && now >= this.startedAt + this.durationMs) {
        this.state = "finished";
        this.reason = "timeout";
        this.finishedAt = this.startedAt + this.durationMs;
      }
      return this.snapshot(now);
    }

    update(input, now) {
      if (typeof input !== "string") throw new TypeError("input must be a string");
      this.tick(now);
      if (this.state === "finished") return this.snapshot(now);
      // Focusing or deleting an already-empty field does not start a session.
      if (this.state === "ready" && input.length > 0) {
        this.startedAt = now;
        this.state = "running";
      }
      this.input = input;
      if (this.state === "running" && input === this.target) {
        this.state = "finished";
        this.reason = "completed";
        this.finishedAt = now;
      }
      return this.snapshot(now);
    }

    /** Reading a snapshot never advances state. Call tick() to resolve expiry.
        Finished results remain frozen even if read several minutes later. */
    snapshot(now) {
      this.checkNow(now);
      const end = this.finishedAt === null ? now : this.finishedAt;
      const elapsedMs = this.startedAt === null ? 0
        : Math.min(this.durationMs, end - this.startedAt);
      return { state: this.state, reason: this.reason, input: this.input,
        ...calculateStats(this.target, this.input, elapsedMs),
        remainingMs: Math.max(0, this.durationMs - elapsedMs) };
    }
  }

  // Browser classic scripts and Node's require() exercise the SAME model.
  const api = { DURATION_MS, PASSAGES, analyzeText, calculateStats, Session };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  globalThis.TypingSprint = api;
})();
