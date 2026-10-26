/* Pure clock model: local civil time for hands, epoch time for event identity.
 * No timers, canvas or audio here, so tricky time boundaries can be tested.
 * All artwork/audio in this project is original; Clock3D is inspiration only. */
(() => {
  "use strict";
  const TAU = Math.PI * 2;

  /** Reject invalid Dates instead of propagating NaN through drawing/audio. */
  function valid(date) {
    if (!(date instanceof Date) || !Number.isFinite(date.getTime()))
      throw new RangeError("A valid Date is required.");
  }

  /** Angles start at twelve, clockwise. Local getters respect the OS timezone.
   * A second hand can jump once a second while hour/minute hands interpolate. */
  function state(date, sweep = false) {
    valid(date);
    const seconds = date.getSeconds() + date.getMilliseconds() / 1000;
    const minutes = date.getMinutes() + seconds / 60;
    const hours = (date.getHours() % 12) + minutes / 60;
    const elapsed = date.getTime() / 1000;
    return {
      hour: (hours / 12) * TAU,
      minute: (minutes / 60) * TAU,
      second: ((sweep ? seconds : Math.floor(seconds)) / 60) * TAU,
      // A two-second oscillation: alternating one-second beats are decorative
      // escapement cues, not a physically coupled pendulum/gear simulation.
      pendulum: Math.sin(elapsed * Math.PI) * 0.19,
      escapement: Math.sin(elapsed * TAU) * 0.13,
      seconds,
      elapsed,
    };
  }

  /** Describe an exact local quarter boundary. Date matching is not based on
   * UTC minutes: some timezones have offsets that are not whole hours. */
  function chimeAt(date) {
    valid(date);
    if (
      date.getSeconds() !== 0 ||
      date.getMilliseconds() !== 0 ||
      date.getMinutes() % 15 !== 0
    )
      return null;
    const quarter = date.getMinutes() / 15;
    return {
      quarter,
      groups: quarter || 4,
      strikes: quarter === 0 ? date.getHours() % 12 || 12 : 0,
      key: date.getTime(),
    };
  }

  /** Original four-note phrases (not a recording of a commercial clock).
   * Each additional quarter adds a phrase; the hour adds one bell per hour.
   * Return descriptors: audio engine decides whether/when sound is enabled. */
  function score(event) {
    if (
      !event ||
      ![0, 1, 2, 3].includes(event.quarter) ||
      event.groups !== (event.quarter || 4) ||
      !Number.isInteger(event.strikes) ||
      (event.quarter === 0
        ? event.strikes < 1 || event.strikes > 12
        : event.strikes !== 0)
    ) {
      throw new RangeError("Invalid chime event.");
    }
    const phrases = [
      [659.25, 523.25, 587.33, 392],
      [523.25, 587.33, 659.25, 523.25],
      [587.33, 392, 523.25, 659.25],
      [392, 587.33, 523.25, 392],
    ];
    const notes = [];
    for (let group = 0; group < event.groups; group++) {
      phrases[group].forEach((frequency, i) =>
        notes.push({
          at: group * 2.6 + i * 0.55,
          frequency,
          duration: 2,
          type: "chime",
        }),
      );
    }
    for (let i = 0; i < event.strikes; i++)
      notes.push({
        at: event.groups * 2.6 + 0.7 + i * 1.4,
        frequency: 196,
        duration: 3,
        type: "strike",
      });
    return notes;
  }

  /** Polling scheduler with no catch-up storm after sleep/tab hiding/time jumps.
   * reset arms from NOW, never sounds a boundary just because the page opened.
   * Seen epoch boundaries avoid replay if the system clock moves backward.
   * A DST repeated civil hour has distinct epoch boundaries, so it can chime.
   */
  function createScheduler() {
    let previous = null;
    const seen = new Set();
    return {
      reset(date) {
        valid(date);
        previous = date.getTime();
      },
      poll(date) {
        valid(date);
        const now = date.getTime(),
          old = previous;
        previous = now;
        if (old === null || now <= old || now - old > 3000) return [];
        const boundary = new Date(date);
        boundary.setSeconds(0, 0);
        const ms = boundary.getTime();
        if (ms <= old || ms > now || now - ms > 1500 || seen.has(ms)) return [];
        const event = chimeAt(boundary);
        if (!event) return [];
        seen.add(ms);
        // Bound memory on long-running tabs; this is not persistent storage.
        if (seen.size > 192) seen.delete(seen.values().next().value);
        return [event];
      },
    };
  }

  const api = Object.freeze({ state, chimeAt, score, createScheduler });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else globalThis.Clockwork = api;
})();
