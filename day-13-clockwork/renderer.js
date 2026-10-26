/* Original Canvas artwork: walnut case, brass cutaway movement and pendulum.
 * This is layered 2D/2.5D illustration, not Clock3D models or a physics solver.
 * The logical canvas is 860×1120; the controller handles device-pixel scaling. */
(() => {
  "use strict";
  const TAU = Math.PI * 2;
  const ROMAN = [
    "XII",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
  ];

  /** Keep all drawing helpers with a single context rather than global state. */
  class Renderer {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      // One constrained train supplies both views: common tooth pitch, exact
      // contact centres and derived phases rather than independent rotations.
      this.gears = globalThis.ClockGears.build();
    }

    /** Circular bevels are concentric fills, not imported texture images. */
    circle(x, y, r, fill, stroke, width = 1) {
      const c = this.ctx;
      c.beginPath();
      c.arc(x, y, r, 0, TAU);
      if (fill) {
        c.fillStyle = fill;
        c.fill();
      }
      if (stroke) {
        c.strokeStyle = stroke;
        c.lineWidth = width;
        c.stroke();
      }
    }

    /** Rounded panels work in browsers without the newer roundRect API. */
    round(x, y, w, h, r, fill, stroke) {
      const c = this.ctx;
      c.beginPath();
      c.moveTo(x + r, y);
      c.arcTo(x + w, y, x + w, y + h, r);
      c.arcTo(x + w, y + h, x, y + h, r);
      c.arcTo(x, y + h, x, y, r);
      c.arcTo(x, y, x + w, y, r);
      c.closePath();
      c.fillStyle = fill;
      c.fill();
      if (stroke) {
        c.strokeStyle = stroke;
        c.lineWidth = 2;
        c.stroke();
      }
    }

    /** One short stroked segment, with no persistent path to leak into a dial. */
    line(x1, y1, x2, y2, color, width = 1) {
      const c = this.ctx;
      c.beginPath();
      c.moveTo(x1, y1);
      c.lineTo(x2, y2);
      c.strokeStyle = color;
      c.lineWidth = width;
      c.stroke();
    }

    /** System serif/sans fonts avoid downloading assets and font licensing. */
    text(value, x, y, size = 16, color = "#d6b77a", family = "serif") {
      const c = this.ctx;
      c.font = `${size}px ${family}`;
      c.fillStyle = color;
      c.textAlign = "center";
      c.textBaseline = "middle";
      c.fillText(value, x, y);
    }

    /** Draw a hollow, spoked gear in local coordinates, then rotate as a unit. */
    gear(gear, angle) {
      const c = this.ctx,
        { x, y, r, n } = gear;
      c.save();
      c.translate(x, y);
      c.rotate(angle);
      c.shadowColor = "#0009";
      c.shadowBlur = 10;
      c.shadowOffsetY = 4;
      const brass = c.createLinearGradient(-r, -r, r, r);
      brass.addColorStop(0, "#f4d793");
      brass.addColorStop(0.3, "#bc8b3d");
      brass.addColorStop(0.58, "#f6db94");
      brass.addColorStop(1, "#785020");
      c.beginPath();
      // Four corners per tooth: root, rising flank, crown, falling flank.
      for (let i = 0; i < n * 4; i++) {
        const angle = (i / (n * 4)) * TAU;
        const radius = r + ([0, 1, 1, 0][i % 4] ? 3 : -3);
        const px = Math.cos(angle) * radius,
          py = Math.sin(angle) * radius;
        if (i === 0) c.moveTo(px, py);
        else c.lineTo(px, py);
      }
      c.closePath();
      c.fillStyle = brass;
      c.fill();
      c.strokeStyle = "#e9cb87";
      c.lineWidth = 1;
      c.stroke();
      c.shadowBlur = 0;
      c.shadowOffsetY = 0;
      this.circle(0, 0, r - 10, "#182421", "#5a421e", 2);
      // Curved spokes cross the hollow ring and meet the central axle.
      for (let i = 0; i < 5; i++) {
        c.save();
        c.rotate((i * TAU) / 5);
        c.beginPath();
        c.moveTo(7, -5);
        c.quadraticCurveTo(r * 0.6, -r * 0.25, r - 11, -5);
        c.lineTo(r - 11, 5);
        c.quadraticCurveTo(r * 0.6, r * 0.05, 7, 5);
        c.closePath();
        c.fillStyle = brass;
        c.fill();
        c.restore();
      }
      this.circle(0, 0, 12, brass, "#65471e", 2);
      this.circle(0, 0, 4, "#20282b", "#f6dca3");
      // One dark index dot makes each wheel's own rotation easy to follow.
      this.circle(r - 15, 0, 2.5, "#533c20", "#f8dda1");
      c.restore();
    }

    /** A shaped clock hand rotates around twelve o'clock, not three o'clock. */
    hand(angle, length, width, color, counter = 22) {
      const c = this.ctx;
      c.save();
      c.translate(430, 288);
      c.rotate(angle);
      c.shadowColor = "#0004";
      c.shadowBlur = 5;
      c.shadowOffsetY = 3;
      c.beginPath();
      c.moveTo(-width * 0.5, counter);
      c.lineTo(-width * 0.65, -length * 0.58);
      c.quadraticCurveTo(-width * 1.4, -length * 0.76, 0, -length);
      c.quadraticCurveTo(
        width * 1.4,
        -length * 0.76,
        width * 0.65,
        -length * 0.58,
      );
      c.lineTo(width * 0.5, counter);
      c.closePath();
      c.fillStyle = color;
      c.fill();
      c.restore();
    }

    /** Scene layers: case → pendulum/weights → movement → dial → glass highlights. */
    draw(state, options = {}) {
      const c = this.ctx;
      c.clearRect(0, 0, 860, 1120);
      const wood = c.createLinearGradient(90, 0, 770, 0);
      wood.addColorStop(0, "#271713");
      wood.addColorStop(0.15, "#75462b");
      wood.addColorStop(0.34, "#3e251c");
      wood.addColorStop(0.72, "#75462f");
      wood.addColorStop(1, "#291a16");
      c.shadowColor = "#0008";
      c.shadowBlur = 30;
      c.shadowOffsetY = 12;
      this.round(136, 30, 588, 1055, 62, wood, "#b98e52");
      c.shadowBlur = 0;
      c.shadowOffsetY = 0;
      // Thin irregular grain lines suggest timber without a texture download.
      c.save();
      c.beginPath();
      c.rect(147, 85, 566, 937);
      c.clip();
      for (let i = 0; i < 75; i++) {
        c.beginPath();
        const x = 150 + i * 7.6;
        for (let y = 70; y < 1080; y += 15) {
          const xx =
            x + Math.sin(y * 0.013 + i) * 3 + Math.sin(y * 0.033 + i) * 1.5;
          if (y === 70) c.moveTo(xx, y);
          else c.lineTo(xx, y);
        }
        c.strokeStyle = i % 2 ? "#e5ab5b13" : "#10080328";
        c.lineWidth = 1;
        c.stroke();
      }
      c.restore();
      this.round(175, 80, 510, 954, 42, "#111c1c", "#b49053");
      this.round(187, 94, 486, 925, 33, "#152223", "#3f4f45");
      // Pediment, cornice and stepped plinth make this a designed case, not a box.
      const metal = c.createLinearGradient(0, 0, 800, 600);
      metal.addColorStop(0, "#f0d495");
      metal.addColorStop(0.5, "#9f783a");
      metal.addColorStop(1, "#e2bd70");
      this.round(116, 1013, 628, 35, 9, wood, "#c79e61");
      this.round(103, 1046, 654, 39, 9, wood, "#a37c4b");
      this.round(230, 14, 400, 38, 14, wood, "#c19a61");
      this.circle(430, 22, 14, metal, "#6b4e29");
      for (const x of [158, 702]) {
        this.round(x - 8, 118, 16, 864, 7, wood, "#a7804d");
        this.round(x - 12, 108, 24, 20, 3, metal);
        this.round(x - 12, 974, 24, 20, 3, metal);
      }
      // Two visual driving weights hang behind the pendulum. Their fixed height
      // is decorative: power reserve/unwinding is not physically simulated.
      for (const x of [282, 578]) {
        this.line(x, 482, x, 877, "#a38859", 2);
        const weight = c.createLinearGradient(x - 19, 0, x + 19, 0);
        weight.addColorStop(0, "#705027");
        weight.addColorStop(0.4, "#eed09a");
        weight.addColorStop(1, "#8b652d");
        this.round(x - 18, 843, 36, 115, 10, weight, "#c9aa70");
        for (let y = 850; y < 950; y += 9)
          this.line(x - 15, y, x + 15, y, "#30241335");
      }
      // The pendulum follows analytic time. Even after a suspended tab resumes,
      // the next frame is in phase rather than integrating accumulated error.
      c.save();
      c.translate(430, 631);
      c.rotate(state.pendulum);
      c.shadowColor = "#0008";
      c.shadowBlur = 10;
      this.round(-5, 0, 10, 300, 3, metal, "#e4c88f");
      this.circle(0, 303, 66, metal, "#72552d", 3);
      this.circle(0, 303, 57, null, "#f6dda7", 2);
      const bob = c.createRadialGradient(-18, 282, 3, 0, 303, 57);
      bob.addColorStop(0, "#f8e5b6");
      bob.addColorStop(0.5, "#c7a05a");
      bob.addColorStop(1, "#8e642d");
      this.circle(0, 303, 52, bob);
      this.circle(0, 303, 8, "#e9c987", "#81602e", 2);
      this.line(-7, 986 - 631, 7, 986 - 631, "#ddbc7d", 4);
      c.restore();
      // Brass bridge plates reveal the wheel train through shaped openings.
      this.round(322, 526, 217, 240, 18, "#2d3831", "#a48a51");
      this.round(334, 537, 193, 218, 14, "#101b1c", "#74613b");
      const angles = globalThis.ClockGears.angles(state.elapsed);
      this.gears.forEach((gear, i) => this.gear(gear, angles[i]));
      // Anchor rocks above the escape wheel, illustrating alternating release.
      c.save();
      c.translate(466, 685);
      c.rotate(state.escapement);
      c.beginPath();
      c.moveTo(-34, 20);
      c.lineTo(-23, -9);
      c.lineTo(23, -9);
      c.lineTo(34, 20);
      c.strokeStyle = "#c4cdd0";
      c.lineWidth = 7;
      c.lineJoin = "round";
      c.stroke();
      c.restore();
      for (const [x, y] of [
        [331, 533],
        [531, 533],
        [331, 761],
        [531, 761],
      ]) {
        this.circle(x, y, 5, "#d7b577", "#5b431e");
        this.line(x - 3, y, x + 3, y, "#4b351c");
      }
      this.circle(430, 631, 8, metal, "#846534", 2);
      // Dial bezel: warm ivory, engraved chapter ring and crisp Roman numerals.
      this.circle(430, 288, 224, "#211b17", "#cdab69", 4);
      this.circle(430, 288, 217, metal, "#f0d393", 2);
      const ivory = c.createRadialGradient(380, 230, 10, 430, 288, 207);
      ivory.addColorStop(0, "#fff9e8");
      ivory.addColorStop(1, "#cdbd9b");
      this.circle(430, 288, 207, ivory, "#746044", 2);
      this.circle(430, 288, 195, null, "#8c7753");
      this.circle(430, 288, 160, null, "#ac956c");
      for (let i = 0; i < 60; i++) {
        const a = (i * TAU) / 60,
          r = i % 5 ? 185 : 178;
        this.line(
          430 + Math.sin(a) * r,
          288 - Math.cos(a) * r,
          430 + Math.sin(a) * 193,
          288 - Math.cos(a) * 193,
          "#4d4639",
          i % 5 ? 1 : 2.8,
        );
      }
      ROMAN.forEach((number, i) => {
        const a = (i * TAU) / 12;
        this.text(
          number,
          430 + Math.sin(a) * 168,
          288 - Math.cos(a) * 168,
          28,
          "#3a3931",
        );
      });
      this.text("HOROLOGIUM", 430, 227, 17, "#665538");
      this.text("LOCAL TIME • DAY XIII", 430, 343, 10, "#796543", "sans-serif");
      this.hand(state.hour, 108, 11, "#24353a", 20);
      this.hand(state.minute, 151, 7, "#253b43", 27);
      c.save();
      c.translate(430, 288);
      c.rotate(state.second);
      this.line(0, 37, 0, -169, "#994b39", 2);
      this.circle(0, 31, 8, null, "#994b39", 2);
      c.restore();
      this.circle(430, 288, 8, metal, "#3e3c31", 2);
      if (options.glass) {
        c.save();
        c.beginPath();
        c.arc(430, 288, 204, 0, TAU);
        c.clip();
        const glass = c.createLinearGradient(250, 100, 620, 480);
        glass.addColorStop(0, "#ffffff00");
        glass.addColorStop(0.35, "#ffffff19");
        glass.addColorStop(0.4, "#ffffff05");
        glass.addColorStop(1, "#ffffff00");
        c.fillStyle = glass;
        c.fillRect(210, 65, 440, 440);
        c.restore();
        this.line(207, 810, 207, 987, "#d1ecdf28", 2);
        this.line(215, 810, 215, 900, "#d1ecdf14", 3);
      }
      this.round(346, 987, 168, 22, 3, metal, "#775a32");
      this.text("TEMPUS • ARTIS", 430, 999, 11, "#3d3020");
      if (options.labels) {
        this.text("WHEEL TRAIN", 608, 590, 12, "#ddc38e", "sans-serif");
        this.line(537, 587, 560, 587, "#ddc38e");
        this.text("ANCHOR", 605, 695, 12, "#ddc38e", "sans-serif");
        this.line(510, 692, 560, 692, "#ddc38e");
        this.text("PENDULUM", 430, 1024, 11, "#d7ba7d", "sans-serif");
      }
    }
  }
  globalThis.ClockRenderer = Renderer;
})();
