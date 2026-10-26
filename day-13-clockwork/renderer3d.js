/* Real procedural 3D solids, projected and painter-sorted onto Canvas 2D.
 * The v0.1 artist supplies only the dial's painted surface, mapped onto a solid
 * cylinder. The case, gears, pendulum and weights have independent geometry;
 * this is NOT a CSS rotation of the flat clock image. No WebGL/assets required.
 */
(() => {
  "use strict";
  const TAU = Math.PI * 2;

  class Renderer3D {
    /** Cache static solids and an offscreen copy of the original dial painter. */
    constructor(canvas, camera) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.camera = camera;
      this.dialCanvas = document.createElement("canvas");
      this.dialCanvas.width = 860;
      this.dialCanvas.height = 1120;
      this.dialPainter = new globalThis.ClockRenderer(this.dialCanvas);
      this.staticFaces = [];
      this.faces = [];
      const wood = "#70452f",
        trim = "#bc9258";
      // An open-backed exhibition case makes rear inspection interesting.
      this.box(-2.9, 0, 0, 0.3, 5.65, 0.66, wood, this.staticFaces);
      this.box(2.9, 0, 0, 0.3, 5.65, 0.66, wood, this.staticFaces);
      this.box(0, 5.55, 0, 3.2, 0.26, 0.76, wood, this.staticFaces);
      this.box(0, -5.55, 0, 3.4, 0.28, 0.83, wood, this.staticFaces);
      this.box(0, -5.96, 0, 3.58, 0.16, 0.91, wood, this.staticFaces);
      this.box(0, 5.94, 0, 2.1, 0.15, 0.72, wood, this.staticFaces);
      for (const x of [-2.53, 2.53])
        this.box(x, 0, 0.69, 0.045, 5.3, 0.035, trim, this.staticFaces);
      this.box(0, 0.32, -0.35, 1.35, 0.1, 0.18, trim, this.staticFaces);
      this.box(0, -2.25, -0.35, 1.35, 0.1, 0.18, trim, this.staticFaces);
      // Convert the SAME 2D pitch geometry into world units; flip y so up
      // is positive. Angles must reverse sign with that coordinate reflection.
      this.gears = globalThis.ClockGears.build().map((g) => ({
        ...g,
        x: (g.x - 430) / 90,
        y: (560 - g.y) / 90 - 0.05,
        r: g.r / 90,
      }));
    }

    /** Add a coloured polygon; no projection yet, so depth sorting stays 3D. */
    face(points, color, list = this.faces) {
      list.push({ points, color });
    }

    /** Axis-aligned box specified by centre and half-extents. */
    box(x, y, z, rx, ry, rz, color, list = this.faces) {
      const p = [
        [-rx, -ry, -rz],
        [rx, -ry, -rz],
        [rx, ry, -rz],
        [-rx, ry, -rz],
        [-rx, -ry, rz],
        [rx, -ry, rz],
        [rx, ry, rz],
        [-rx, ry, rz],
      ].map((v) => [v[0] + x, v[1] + y, v[2] + z]);
      for (const indexes of [
        [0, 3, 2, 1],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
      ])
        this.face(
          indexes.map((i) => p[i]),
          color,
          list,
        );
    }

    /** A z-axis cylinder: solid sides/end caps, useful for dial and metal hubs. */
    cylinder(x, y, z, r, depth, color, n = 40) {
      const front = [],
        back = [];
      for (let i = 0; i < n; i++) {
        const a = (i * TAU) / n,
          px = x + Math.cos(a) * r,
          py = y + Math.sin(a) * r;
        front.push([px, py, z + depth / 2]);
        back.push([px, py, z - depth / 2]);
      }
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        this.face([back[i], back[j], front[j], front[i]], color);
      }
      this.face(front, color);
      this.face(back.slice().reverse(), color);
    }

    /** Extruded toothed annulus with real holes and five separate solid spokes. */
    gear(g, angle) {
      const { x, y, r, n } = g,
        z = 0.12,
        depth = 0.12,
        inner = r * 0.7;
      const point = (radius, a, zz) => [
        x + Math.cos(a) * radius,
        y + Math.sin(a) * radius,
        zz,
      ];
      for (let i = 0; i < n * 4; i++) {
        const j = (i + 1) % (n * 4),
          a = angle - (i * TAU) / (n * 4),
          b = angle - ((i + 1) * TAU) / (n * 4);
        const ra = r + ([0, 1, 1, 0][i % 4] ? 0.028 : -0.025),
          rb = r + ([0, 1, 1, 0][j % 4] ? 0.028 : -0.025);
        const af = point(ra, a, z + depth),
          bf = point(rb, b, z + depth),
          ab = point(ra, a, z - depth),
          bb = point(rb, b, z - depth);
        const ia = point(inner, a, z + depth),
          ib = point(inner, b, z + depth),
          iab = point(inner, a, z - depth),
          ibb = point(inner, b, z - depth);
        this.face([af, bf, ib, ia], "#d8b56b");
        this.face([ab, iab, ibb, bb], "#9e773b");
        this.face([ab, bb, bf, af], "#b18b45");
        this.face([ia, ib, ibb, iab], "#87622e");
      }
      for (let i = 0; i < 5; i++) {
        const a = angle + (i * TAU) / 5,
          perp = 0.045;
        const p = (radius, offset, zz) => [
          x + Math.cos(a) * radius - Math.sin(a) * offset,
          y + Math.sin(a) * radius + Math.cos(a) * offset,
          zz,
        ];
        const ring = [
          p(0.05, -perp, z + depth),
          p(inner, -perp, z + depth),
          p(inner, perp, z + depth),
          p(0.05, perp, z + depth),
        ];
        this.face(ring, "#ddbc78");
        this.face(
          ring.map((v) => [v[0], v[1], z - depth]).reverse(),
          "#a47c3d",
        );
        for (let k = 0; k < 4; k++) {
          const l = (k + 1) % 4;
          this.face(
            [
              ring[k],
              ring[l],
              [ring[l][0], ring[l][1], z - depth],
              [ring[k][0], ring[k][1], z - depth],
            ],
            "#ad8747",
          );
        }
      }
      this.cylinder(x, y, z, 0.13, 0.38, "#c8a864", 12);
      this.cylinder(x, y, -0.25, 0.055, 0.7, "#778285", 8);
    }

    /** Rotate a group about its pivot, allowing an actual 3D swinging assembly. */
    swing(faces, angle, pivot) {
      const c = Math.cos(angle),
        s = Math.sin(angle);
      return faces.map((face) => ({
        ...face,
        points: face.points.map(([x, y, z]) => {
          const dx = x - pivot[0],
            dy = y - pivot[1];
          return [pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c, z];
        }),
      }));
    }

    /** Shade each solid face from its camera-space normal with a fixed lamp. */
    shade(points, color) {
      const [a, b, c] = points,
        ux = b[0] - a[0],
        uy = b[1] - a[1],
        uz = b[2] - a[2],
        vx = c[0] - a[0],
        vy = c[1] - a[1],
        vz = c[2] - a[2];
      const nx = uy * vz - uz * vy,
        ny = uz * vx - ux * vz,
        nz = ux * vy - uy * vx;
      const length = Math.hypot(nx, ny, nz) || 1;
      const light =
        0.57 + 0.37 * Math.abs((nx * -0.35 + ny * 0.45 + nz * 0.82) / length);
      const hex = color.slice(1);
      return `rgb(${[0, 2, 4].map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) * light)).join(",")})`;
    }

    /** Build the dynamic solids, sort far-to-near, then paint each polygon.
     * Average-depth painter sorting is approximate for intersecting objects;
     * it has no z-buffer. The model is intentionally spread into depth layers.
     */
    draw(state, options = {}) {
      const c = this.ctx;
      c.clearRect(0, 0, 860, 1120);
      this.faces = this.staticFaces.slice();
      this.cylinder(0, 3.08, 0, 2.48, 0.55, "#b58c4d", 80);
      this.cylinder(0, 3.08, 0.3, 2.35, 0.1, "#e8dab7", 80);
      for (const x of [-1.85, 1.85]) {
        this.box(x, -2.0, -0.08, 0.013, 2.9, 0.013, "#b5a371");
        this.cylinder(x, -4.25, -0.08, 0.22, 0.4, "#c7a364", 16);
        // Upright weight as a long cylinder represented by a bevelled box.
        this.box(x, -4.25, -0.08, 0.21, 0.65, 0.18, "#b99a59");
      }
      const angles = globalThis.ClockGears.angles(state.elapsed);
      this.gears.forEach((g, i) => this.gear(g, -angles[i]));
      const start = this.faces.length;
      this.box(0, -3.2, 0.43, 0.035, 1.4, 0.045, "#d6bd82");
      this.cylinder(0, -4.55, 0.43, 0.73, 0.17, "#d8b567", 48);
      this.cylinder(0, -4.55, 0.54, 0.63, 0.08, "#bd9752", 40);
      const pendulum = this.faces.splice(start);
      this.faces.push(...this.swing(pendulum, state.pendulum, [0, -1.8]));
      // Rocking anchor comprises separate steel solids above the escape wheel.
      const anchorStart = this.faces.length;
      this.box(0.36, -1.3, 0.39, 0.35, 0.035, 0.045, "#a8b1b3");
      for (const x of [0.05, 0.67])
        this.box(x, -1.42, 0.39, 0.035, 0.16, 0.045, "#a8b1b3");
      this.faces.push(
        ...this.swing(
          this.faces.splice(anchorStart),
          state.escapement,
          [0.36, -1.3],
        ),
      );
      // The ORIGINAL v0.1 dial artwork becomes a texture on the solid's front.
      this.dialPainter.draw(state, { glass: options.glass, labels: false });
      const dial = [
        [-2.35, 5.43, 0.365],
        [2.35, 5.43, 0.365],
        [2.35, 0.73, 0.365],
        [-2.35, 0.73, 0.365],
      ];
      this.faces.push({ points: dial, texture: true });
      const projected = this.faces
        .map((face) => {
          const points = face.points.map((p) => this.camera.project(p));
          return {
            ...face,
            points,
            depth: points.reduce((sum, p) => sum + p[2], 0) / points.length,
          };
        })
        .sort((a, b) => a.depth - b.depth);
      for (const face of projected) {
        const p = face.points;
        if (face.texture) {
          // The dial is a planar parallelogram under parallel projection, so
          // an affine canvas transform maps its image exactly (no billboard).
          const normal = globalThis.ClockCamera.rotate(
            [0, 0, 1],
            this.camera.q,
          );
          if (normal[2] <= 0) continue; // Do not see the face through the case back.
          c.save();
          c.beginPath();
          c.moveTo(p[0][0], p[0][1]);
          p.slice(1).forEach((v) => c.lineTo(v[0], v[1]));
          c.closePath();
          c.clip();
          c.transform(
            (p[1][0] - p[0][0]) / 448,
            (p[1][1] - p[0][1]) / 448,
            (p[3][0] - p[0][0]) / 448,
            (p[3][1] - p[0][1]) / 448,
            p[0][0],
            p[0][1],
          );
          // Crop the circular bezel; transparent square corners must not carry case art.
          c.beginPath();
          c.arc(224, 224, 224, 0, TAU);
          c.clip();
          c.drawImage(this.dialCanvas, 206, 64, 448, 448, 0, 0, 448, 448);
          c.restore();
        } else {
          c.beginPath();
          c.moveTo(p[0][0], p[0][1]);
          p.slice(1).forEach((v) => c.lineTo(v[0], v[1]));
          c.closePath();
          c.fillStyle = this.shade(p, face.color);
          c.fill();
          c.strokeStyle = "#181b1960";
          c.lineWidth = 0.45;
          c.stroke();
        }
      }
      if (options.labels) {
        c.font = "16px system-ui";
        c.textAlign = "center";
        c.fillStyle = "#ead29f";
        for (const [label, point] of [
          ["Wheel train", [1.6, -0.7, 0.5]],
          ["Pendulum", [0, -5.45, 0.5]],
          ["Open-backed case", [0, 6.3, 0]],
        ]) {
          const p = this.camera.project(point);
          c.fillText(label, p[0], p[1]);
        }
      }
    }
  }
  globalThis.ClockRenderer3D = Renderer3D;
})();
