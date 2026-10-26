/* Pure quaternion camera: drag across a virtual trackball in any direction.
 * Quaternions avoid the pole-locking and abrupt flips of clamped yaw/pitch.
 * This is an orthographic 3D view: solid geometry has depth, but no perspective
 * foreshortening with distance. There is no external 3D library or asset. */
(() => {
  "use strict";

  /** Normalise a 3D/4D vector, guarding tiny round-off denominators. */
  function unit(vector) {
    const length = Math.hypot(...vector);
    return length < 1e-12
      ? vector.map((_, i) => (i === vector.length - 1 ? 1 : 0))
      : vector.map((v) => v / length);
  }

  /** Hamilton product: compose rotations, not component-by-component addition. */
  function multiply(a, b) {
    const [x, y, z, w] = a,
      [u, v, t, s] = b;
    return [
      w * u + x * s + y * t - z * v,
      w * v - x * t + y * s + z * u,
      w * t + x * v - y * u + z * s,
      w * s - x * u - y * v - z * t,
    ];
  }

  /** Rotate a point using q*v*conjugate(q); unit q preserves lengths. */
  function rotate(point, q) {
    return multiply(multiply(q, [...point, 0]), [
      -q[0],
      -q[1],
      -q[2],
      q[3],
    ]).slice(0, 3);
  }

  /** A virtual sphere extends smoothly outside its circular screen footprint. */
  function trackball(x, y) {
    const r2 = x * x + y * y;
    return unit([x, y, r2 <= 0.5 ? Math.sqrt(1 - r2) : 0.5 / Math.sqrt(r2)]);
  }

  /** Shortest rotation taking one unit direction to another. */
  function between(a, b) {
    const dot = a.reduce((sum, v, i) => sum + v * b[i], 0);
    if (dot < -0.999999) {
      const axis = Math.abs(a[0]) < 0.8 ? [0, -a[2], a[1]] : [-a[1], a[0], 0];
      return [...unit(axis), 0];
    }
    return unit([
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0],
      1 + dot,
    ]);
  }

  /** State belongs to the 3D camera only. View toggles never reset local time. */
  class Camera {
    constructor() {
      this.reset();
    }
    /** A slight turn reveals case thickness while keeping the face readable. */
    reset() {
      this.q = unit([-0.055, 0.16, 0, 0.985]);
      this.dragStart = null;
    }
    /** Save the initial quaternion so pointer event frequency cannot add drift. */
    begin(x, y) {
      this.dragStart = { point: trackball(x, y), q: this.q.slice() };
    }
    /** Apply a trackball delta in camera space; unconstrained axes permit rolls. */
    drag(x, y) {
      if (!this.dragStart) return;
      this.q = unit(
        multiply(
          between(this.dragStart.point, trackball(x, y)),
          this.dragStart.q,
        ),
      );
    }
    /** Pointer cancellation/release ends the gesture, never changes the clock. */
    end() {
      this.dragStart = null;
    }
    /** Orthographic projection in logical 860×1120 canvas coordinates. */
    project(point) {
      const p = rotate(point, this.q);
      return [430 + p[0] * 86, 560 - p[1] * 86, p[2]];
    }
  }
  const api = Object.freeze({
    unit,
    multiply,
    rotate,
    trackball,
    between,
    Camera,
  });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else globalThis.ClockCamera = api;
})();
