/* Shared, kinematically constrained spur-gear train for both clock views.
 * A common module (pitch diameter / tooth count) keeps tooth spacing equal.
 * This is prescribed gearing, not a force/contact or involute-tooth solver. */
(() => {
  "use strict";
  const TAU = Math.PI * 2;
  // A U-shaped path leaves clearance between ALL non-engaged wheel pairs.
  // Coordinates use the original illustrator's canvas units (y downward).
  const layout = [
    { x: 360, y: 560, r: 40, n: 20 },
    { x: 432, y: 560, r: 32, n: 16 },
    { x: 496, y: 560, r: 32, n: 16 },
    { x: 496, y: 632, r: 40, n: 20 },
    { x: 496, y: 712, r: 40, n: 20 },
    { x: 424, y: 712, r: 32, n: 16 },
  ];

  /** Derive phase AND angular velocity from each preceding engaged wheel.
   * At the contact direction, a tooth crown must meet the other wheel's gap.
   * Our four-vertex teeth have crown centres at 3/8 of a tooth period; the
   * combined contact phases must differ by half a pitch. Changing direction
   * between contacts therefore requires more than alternating a fixed offset.
   */
  function build() {
    return layout.reduce((result, wheel, i) => {
      if (!i) result.push({ ...wheel, phase: 0, speed: 0.28 });
      else {
        const parent = result[i - 1];
        const contact = Math.atan2(wheel.y - parent.y, wheel.x - parent.x);
        const phase =
          (parent.n * contact +
            wheel.n * (contact + Math.PI) -
            TAU * 1.25 -
            parent.n * parent.phase) /
          wheel.n;
        result.push({
          ...wheel,
          phase,
          speed: (-parent.speed * parent.n) / wheel.n,
        });
      }
      return result;
    }, []);
  }

  /** Reduce time by the whole train's exact four-root-turn cycle to avoid huge angles.
   * A 20-tooth root and 16-tooth followers repeat jointly every four root turns.
   * All speeds share the same elapsed time, so they cannot drift independently.
   */
  function angles(seconds) {
    if (!Number.isFinite(seconds))
      throw new RangeError("Finite elapsed seconds required");
    const cycle = (TAU * 4) / 0.28;
    const time = ((seconds % cycle) + cycle) % cycle;
    return build().map((wheel) => wheel.phase + wheel.speed * time);
  }

  const api = Object.freeze({ build, angles });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else globalThis.ClockGears = api;
})();
