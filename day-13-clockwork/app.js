/* Controller: local Date drives hands, requestAnimationFrame draws the scene,
 * and a separate polling interval checks sound boundaries. No timer is used
 * to increment the clock: that would drift when frames or callbacks are late. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const model = globalThis.Clockwork;
  const canvas = $("clock");
  const renderer = new globalThis.ClockRenderer(canvas);
  const camera = new globalThis.ClockCamera.Camera();
  const renderer3d = new globalThis.ClockRenderer3D(canvas, camera);
  let view = "2d"; // Preserve the v0.1 experience as the initial view.
  let pointerId = null;
  const audio = new globalThis.ClockAudio();
  const scheduler = model.createScheduler();
  let lastText = "",
    lastBeat = null,
    enabled = false,
    enabling = false;
  let motionFrozen = null;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  $("motion").checked = !reduced.matches;

  /** Match canvas backing pixels to device density without changing scene units.
   * Bound density at two so a very high-DPI display does not allocate huge art.
   */
  function resize() {
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = 860 * ratio;
    canvas.height = 1120 * ratio;
    renderer.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  /** Display local civil time as text, independently of canvas accessibility. */
  function text(date) {
    const value = date.toLocaleTimeString([], {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    if (value === lastText) return;
    lastText = value;
    $("time").textContent = value;
    $("time").dateTime = date.toISOString();
    $("date").textContent = date.toLocaleDateString([], {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    $("zone").textContent =
      Intl.DateTimeFormat().resolvedOptions().timeZone ||
      "Device local timezone";
  }

  /** Re-arm from now after enable, visibility changes or a manual resync.
   * There is no catch-up replay of missed ticks/chimes. */
  function rearm() {
    const date = new Date();
    scheduler.reset(date);
    lastBeat = null;
    lastText = "";
    text(date);
  }

  /** One display loop. Motion freeze affects gears/pendulum, never time hands. */
  function frame() {
    const date = new Date();
    text(date);
    const state = model.state(date, $("sweep").checked);
    if (!$("motion").checked) {
      if (!motionFrozen)
        motionFrozen = {
          pendulum: state.pendulum,
          escapement: state.escapement,
          elapsed: state.elapsed,
        };
      Object.assign(state, motionFrozen);
    } else motionFrozen = null;
    (view === "3d" ? renderer3d : renderer).draw(state, {
      glass: $("glass").checked,
      labels: $("labels").checked,
    });
    requestAnimationFrame(frame);
  }

  /** Poll against wall time instead of assuming interval callbacks are punctual.
   * Tick instants at .5/1.5/... seconds alternate tick/tock once per second,
   * in phase with the two-second pendulum endpoints. Late beats are dropped.
   */
  function poll() {
    const date = new Date();
    if (!enabled || document.hidden) {
      scheduler.reset(date);
      lastBeat = null;
      return;
    }
    const shifted = date.getTime() - 500;
    const beat = Math.floor(shifted / 1000);
    if (
      lastBeat !== null &&
      beat === lastBeat + 1 &&
      ((shifted % 1000) + 1000) % 1000 < 180 &&
      $("ticks").checked
    )
      audio.tick(beat % 2 === 1);
    lastBeat = beat;
    const events = scheduler.poll(date);
    if ($("chimes").checked) {
      for (const event of events) {
        audio.chime(model.score(event));
        $("audio-status").textContent = event.strikes
          ? `Hour chime and ${event.strikes} bell strikes.`
          : `Quarter chime: ${event.groups} phrase${event.groups === 1 ? "" : "s"}.`;
      }
    }
    if (audio.context && audio.context.state !== "running")
      $("audio-status").textContent =
        "Audio was suspended by the browser. Mute, then Enable sound to resume.";
  }

  /** Only this click can start the audio context, complying with autoplay rules. */
  async function toggleSound() {
    if (enabling) return;
    if (enabled) {
      audio.mute();
      enabled = false;
      $("sound").textContent = "Enable sound";
      $("audio-status").textContent = "Muted. Scheduled notes cancelled.";
      return;
    }
    enabling = true;
    $("sound").disabled = true;
    try {
      await audio.enable();
      enabled = true;
      rearm();
      $("sound").textContent = "Mute sound";
      $("audio-status").textContent =
        "Sound enabled. Use previews to listen without waiting for a quarter hour.";
    } catch (problem) {
      $("audio-status").textContent = problem.message;
    } finally {
      enabling = false;
      $("sound").disabled = false;
    }
  }

  /** Preview is labelled, separate from scheduled boundaries and never changes time. */
  function preview(hour) {
    if (!enabled) {
      $("audio-status").textContent =
        "Enable sound first, then try the preview.";
      return;
    }
    const strikes = hour ? new Date().getHours() % 12 || 12 : 0;
    audio.chime(
      model.score({ quarter: hour ? 0 : 1, groups: hour ? 4 : 1, strikes }),
    );
    $("audio-status").textContent = hour
      ? `Preview: four phrases and ${strikes} hour strikes.`
      : "Preview: one quarter-hour phrase.";
  }

  /** Trackball coordinates use the CSS rectangle, not backing pixel density. */
  function pointerPoint(event) {
    const rect = canvas.getBoundingClientRect();
    const radius = Math.min(rect.width, rect.height) / 2;
    return [
      (event.clientX - rect.left - rect.width / 2) / radius,
      -(event.clientY - rect.top - rect.height / 2) / radius,
    ];
  }

  /** Toggle only presentation: audio queues, hand time and frozen state survive. */
  function switchView() {
    finishDrag();
    view = view === "2d" ? "3d" : "2d";
    $("view-toggle").textContent =
      view === "2d" ? "Switch to 3D" : "Switch to 2D · v0.1";
    $("view-name").textContent = view === "2d" ? "2D · v0.1" : "3D · v0.2";
    $("reset-view").disabled = view !== "3d";
    canvas.classList.toggle("orbit", view === "3d");
    canvas.setAttribute(
      "aria-label",
      view === "3d"
        ? "Rotatable solid 3D clock. Left-drag to orbit; arrow keys also rotate; Home resets view."
        : "Original v0.1 analog clock illustration. Current time appears beside it.",
    );
  }

  /** Release capture on all exit paths, including toggling during a drag. */
  function finishDrag() {
    camera.end();
    if (pointerId !== null && canvas.hasPointerCapture(pointerId))
      canvas.releasePointerCapture(pointerId);
    pointerId = null;
    canvas.classList.remove("dragging");
  }

  canvas.addEventListener("pointerdown", (event) => {
    if (view !== "3d" || event.button !== 0 || pointerId !== null) return;
    pointerId = event.pointerId;
    canvas.setPointerCapture(pointerId);
    camera.begin(...pointerPoint(event));
    canvas.classList.add("dragging");
    canvas.focus();
    event.preventDefault();
  });
  canvas.addEventListener("pointermove", (event) => {
    if (event.pointerId === pointerId) camera.drag(...pointerPoint(event));
  });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) {
    canvas.addEventListener(name, (event) => {
      if (event.pointerId === pointerId) finishDrag();
    });
  }
  canvas.addEventListener("keydown", (event) => {
    if (view !== "3d") return;
    if (event.key === "Home") {
      camera.reset();
      event.preventDefault();
      return;
    }
    const direction = {
      ArrowLeft: [-0.14, 0],
      ArrowRight: [0.14, 0],
      ArrowUp: [0, 0.14],
      ArrowDown: [0, -0.14],
    }[event.key];
    if (direction) {
      camera.begin(0, 0);
      camera.drag(...direction);
      camera.end();
      event.preventDefault();
    }
  });
  $("view-toggle").addEventListener("click", switchView);
  $("reset-view").addEventListener("click", () => {
    finishDrag();
    camera.reset();
  });

  $("sound").addEventListener("click", toggleSound);
  $("preview-quarter").addEventListener("click", () => preview(false));
  $("preview-hour").addEventListener("click", () => preview(true));
  $("volume").addEventListener("input", () => {
    audio.setVolume(Number($("volume").value) / 100);
    $("volume-value").value = `${$("volume").value}%`;
  });
  $("chimes").addEventListener("change", () => {
    audio.silence();
    rearm();
  });
  $("sync-now").addEventListener("click", () => {
    audio.silence();
    rearm();
    $("audio-status").textContent =
      "Refreshed from the device clock; no missed sounds replayed.";
  });
  document.addEventListener("visibilitychange", () => {
    audio.silence();
    rearm();
  });
  window.addEventListener("pagehide", () => audio.mute());
  window.addEventListener("pageshow", () => {
    enabled = false;
    $("sound").textContent = "Enable sound";
    audio.mute();
    rearm();
  });
  window.addEventListener("resize", resize);
  resize();
  rearm();
  requestAnimationFrame(frame);
  setInterval(poll, 50);
})();
