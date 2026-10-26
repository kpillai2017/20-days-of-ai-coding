/* Original procedural Web Audio: short noise ticks and inharmonic bell tones.
 * Browsers require a user gesture to start/resume AudioContext. No samples,
 * recordings, music files or third-party assets are fetched. */
(() => {
  "use strict";
  class ClockAudio {
    /** One master gain lets mute/volume affect already-sounding notes too. */
    constructor() {
      this.context = null;
      this.master = null;
      this.enabled = false;
      this.volume = 0.35;
      this.sources = new Set();
      this.tickBuffer = null;
    }

    /** Called ONLY from the Enable sound button's click gesture. */
    async enable() {
      const Audio = globalThis.AudioContext || globalThis.webkitAudioContext;
      if (!Audio)
        throw new Error("Web Audio is not available in this browser.");
      if (!this.context) {
        this.context = new Audio();
        this.master = this.context.createGain();
        this.master.gain.value = this.volume;
        this.master.connect(this.context.destination);
        // Deterministic noise avoids a sample download and remains original.
        this.tickBuffer = this.context.createBuffer(
          1,
          Math.floor(this.context.sampleRate * 0.035),
          this.context.sampleRate,
        );
        const data = this.tickBuffer.getChannelData(0);
        let seed = 13;
        for (let i = 0; i < data.length; i++) {
          seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
          data[i] =
            ((seed / 2 ** 32) * 2 - 1) * Math.exp(-i / (data.length * 0.13));
        }
      }
      await this.context.resume();
      if (this.context.state !== "running")
        throw new Error("Audio remains blocked; try Enable sound again.");
      this.enabled = true;
      this.master.gain.setValueAtTime(this.volume, this.context.currentTime);
    }

    /** Stop all scheduled nodes: mute/hidden tabs must not leave a chime queue. */
    silence() {
      for (const source of this.sources) {
        try {
          source.stop();
        } catch {
          /* Already ended. */
        }
      }
      this.sources.clear();
    }

    /** Mute is immediate and cancels scheduled notes, rather than waiting. */
    mute() {
      this.enabled = false;
      this.silence();
      if (this.master)
        this.master.gain.setValueAtTime(0, this.context.currentTime);
    }

    /** Track nodes until they finish, avoiding an ever-growing list in a long tab. */
    track(source) {
      this.sources.add(source);
      source.onended = () => this.sources.delete(source);
    }

    /** Volume is clamped because browser range controls are not the only caller. */
    setVolume(value) {
      this.volume = Math.max(0, Math.min(1, value));
      if (this.master)
        this.master.gain.setTargetAtTime(
          this.enabled ? this.volume : 0,
          this.context.currentTime,
          0.02,
        );
    }

    /** Alternating tick/tock have distinct pitches at the pendulum's endpoints. */
    tick(tock = false) {
      if (!this.enabled || this.context.state !== "running") return;
      const now = this.context.currentTime;
      const source = this.context.createBufferSource();
      source.buffer = this.tickBuffer;
      const filter = this.context.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.value = tock ? 950 : 1500;
      filter.Q.value = 0.7;
      const gain = this.context.createGain();
      gain.gain.setValueAtTime(0.7, now);
      source.connect(filter).connect(gain).connect(this.master);
      this.track(source);
      source.start(now);
    }

    /** Bell partials are deliberately inharmonic: a struck bell is not a sine.
     * Exponential fades avoid clicks; zero is forbidden for exponential ramps.
     */
    bell(note, start) {
      for (const [multiple, level, decay] of [
        [1, 0.24, 1],
        [2.71, 0.1, 0.65],
        [4.13, 0.045, 0.4],
      ]) {
        const osc = this.context.createOscillator(),
          gain = this.context.createGain();
        osc.type = "sine";
        osc.frequency.value = note.frequency * multiple;
        gain.gain.setValueAtTime(0.0001, start);
        gain.gain.exponentialRampToValueAtTime(level, start + 0.008);
        gain.gain.exponentialRampToValueAtTime(
          0.0001,
          start + note.duration * decay,
        );
        osc.connect(gain).connect(this.master);
        this.track(osc);
        osc.start(start);
        osc.stop(start + note.duration * decay + 0.03);
      }
    }

    /** A new phrase replaces the old queue (including manual preview). */
    chime(notes) {
      if (!this.enabled || this.context.state !== "running") return;
      this.silence();
      const start = this.context.currentTime + 0.03;
      for (const note of notes) this.bell(note, start + note.at);
    }
  }
  globalThis.ClockAudio = ClockAudio;
})();
