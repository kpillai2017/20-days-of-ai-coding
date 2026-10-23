/* Pure mechanics and cycle state. No canvas, clock or DOM: tests can ask what
   happens at an exact crank angle without waiting for an animation to get there.
   This is an idealised teaching model, not a thermodynamic engine simulation. */
(() => {
  "use strict";
  const CRANK_RADIUS = 0.6;
  const ROD_LENGTH = 1.8;

  function finite(value) {
    if (!Number.isFinite(value)) throw new TypeError("angle must be a finite number");
  }
  function cycleDegrees(mode) {
    if (mode !== "four" && mode !== "two") throw new RangeError("mode must be four or two");
    return mode === "four" ? 720 : 360;
  }
  function normalizedAngle(angle, period = 360) {
    finite(angle);
    if (!Number.isFinite(period) || period <= 0) throw new RangeError("period must be positive");
    // JS remainder can be negative. A second remainder puts negatives in range.
    return ((angle % period) + period) % period;
  }
  function crankPosition(angle) {
    const theta = normalizedAngle(angle) * Math.PI / 180;
    return { x: CRANK_RADIUS * Math.sin(theta), y: CRANK_RADIUS * Math.cos(theta) };
  }
  function pistonPosition(angle) {
    const crank = crankPosition(angle);
    // Slider-crank constraint: rod length is constant, piston pin stays on x=0.
    // Solve x²+(pistonY-crankY)²=L² for the upper (positive) branch.
    return crank.y + Math.sqrt(ROD_LENGTH ** 2 - crank.x ** 2);
  }

  const FOUR = [
    { angle: 0, title: "Intake", caption: "Piston descends. The open intake valve admits fresh air–fuel mixture; the exhaust valve is closed." },
    { angle: 180, title: "Compression", caption: "Piston rises with both valves closed, squeezing the fresh charge. The spark is shown shortly before top dead centre." },
    { angle: 360, title: "Power", caption: "Combustion raises pressure; expanding gases push the piston down. Both valves stay closed. The crank carries motion onward." },
    { angle: 540, title: "Exhaust", caption: "Piston rises. The exhaust valve is open and pushes burnt gas out. One cycle needs two crank revolutions (720°)." }
  ];
  const TWO = [
    { angle: 0, title: "Power / crankcase compression" },
    { angle: 110, title: "Exhaust blowdown" },
    { angle: 150, title: "Transfer & scavenging" },
    { angle: 290, title: "Compression / crankcase filling" }
  ];
  function getStages(mode) {
    cycleDegrees(mode); // Reuse validation; return copies so callers can't edit shared definitions.
    return (mode === "four" ? FOUR : TWO).map(stage => ({ ...stage }));
  }

  function getState(mode, angleDegrees) {
    const period = cycleDegrees(mode);
    const angle = normalizedAngle(angleDegrees, period);
    const crankAngle = angle % 360;
    const atDeadCentre = Math.abs(crankAngle % 180) < 1e-8;
    const common = {
      mode, angle, cycleDegrees: period, crankAngle,
      pistonY: pistonPosition(angle), crank: crankPosition(angle),
      // Height DECREASES from 0° to 180°: that is DOWN, not up.
      pistonDirection: atDeadCentre ? "turning" : crankAngle < 180 ? "down" : "up",
      intakeOpen: false, exhaustOpen: false, transferOpen: false,
      crankcaseIntakeOpen: false, spark: false, burn: 0
    };
    if (mode === "four") {
      const index = Math.floor(angle / 180);
      return { ...common, phase: FOUR[index].title.toLowerCase(), stageIndex: index,
        title: FOUR[index].title, caption: FOUR[index].caption,
        intakeOpen: index === 0, exhaustOpen: index === 3,
        spark: angle >= 350 && angle < 370,
        burn: index === 2 ? Math.exp(-(angle - 360) / 65) : 0,
        charge: ["fresh", "compressed", "burnt", "exhaust"][index] };
    }
    // Illustrative piston-port opening angles, symmetric about bottom dead centre.
    // Exhaust closes 15° AFTER transfer, so effective compression begins at 255°,
    // not merely when the transfer port closes at 240°.
    const exhaustOpen = angle >= 105 && angle < 255;
    const transferOpen = angle >= 120 && angle < 240;
    let phase, title, caption, stageIndex;
    if (angle < 105) {
      phase = "power"; title = TWO[0].title; stageIndex = 0;
      caption = "Expanding hot gas drives the piston down. Below it, descending piston motion compresses fresh mixture in the crankcase; its reed inlet is closed.";
    } else if (angle < 120) {
      phase = "blowdown"; title = TWO[1].title; stageIndex = 1;
      caption = "The piston uncovers the higher exhaust port first. Burnt gas begins to escape (blowdown) before the transfer port opens.";
    } else if (angle < 240) {
      phase = "scavenging"; title = TWO[2].title; stageIndex = 2;
      caption = "Both ports are exposed. Fresh mixture transfers FROM THE CRANKCASE, entering upward to help sweep burnt gas toward the exhaust (scavenging). Flow arrows show a simplified net direction.";
    } else if (angle < 255) {
      phase = "exhaust-closing"; title = "Transfer closed; exhaust still open"; stageIndex = 3;
      caption = "The rising piston has covered the transfer port, but the exhaust remains exposed until 255°. Fully trapped-charge compression has not yet begun.";
    } else if (angle < 350) {
      phase = "compression"; title = TWO[3].title; stageIndex = 3;
      caption = "The rising piston covers both ports and compresses the cylinder charge. Below it, crankcase volume grows and a pressure-operated reed admits the next fresh mixture.";
    } else {
      phase = "ignition"; title = "Ignition near top dead centre"; stageIndex = 3;
      caption = "The spark is shown before top dead centre. Combustion is simplified as a colour cue; the next downstroke delivers power. A two-stroke cycle needs one revolution (360°).";
    }
    return { ...common, phase, title, caption, stageIndex, exhaustOpen, transferOpen,
      // Reed movement is pressure-driven, not an exact crank-timed valve in reality.
      crankcaseIntakeOpen: angle >= 190 && angle < 350,
      spark: angle >= 350 || angle < 10,
      burn: angle < 105 ? Math.exp(-angle / 50) : 0,
      charge: angle < 105 ? "burnt" : angle < 120 ? "exhaust"
        : angle < 255 ? "fresh" : "compressed" };
  }
  const api = { CRANK_RADIUS, ROD_LENGTH, cycleDegrees, normalizedAngle,
    crankPosition, pistonPosition, getState, getStages };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  globalThis.EngineModel = api;
})();
