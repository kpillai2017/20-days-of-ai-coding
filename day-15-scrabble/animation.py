"""A presentation-only, sequential tile-flight timeline.

Rules commit once before animation. This timeline controls which new tiles the
renderer reveals; it never changes scores, racks, turn order or board contents.
"""

import math


class TileFlight:
    """Fly one tile at a time, with a short landing pause between letters."""

    def __init__(self, items, player, now, flight_ms=650, pause_ms=140):
        if not items or flight_ms <= 0 or pause_ms < 0:
            raise ValueError("A flight needs tiles and valid timing.")
        self.items = items
        self.player = player
        self.flight_ms = flight_ms
        self.step_ms = flight_ms + pause_ms
        self.elapsed = 0
        self.last_tick = now

    def advance(self, now, paused=False):
        """Accumulate only active time; dialogs pause without a resume jump."""
        delta = max(0, now - self.last_tick)
        self.last_tick = now
        if not paused:
            self.elapsed += delta

    @property
    def done(self):
        """Finish after the last tile's landing pause, not at take-off."""
        return self.elapsed >= len(self.items) * self.step_ms

    def landed(self, index):
        """A board square becomes visible only after its own flight ends."""
        return self.elapsed >= index * self.step_ms + self.flight_ms

    def flying(self):
        """Return active tile index and smooth position/size, or None in pauses."""
        if self.done:
            return None
        index = int(self.elapsed // self.step_ms)
        local = self.elapsed - index * self.step_ms
        if local >= self.flight_ms:
            return None
        item = self.items[index]
        t = local / self.flight_ms
        eased = t * t * (3 - 2 * t)
        start, end = item["start"], item["end"]
        x = start[0] + (end[0] - start[0]) * eased
        y = start[1] + (end[1] - start[1]) * eased - 95 * math.sin(math.pi * t)
        size = 55 + (42 - 55) * eased
        return index, x, y, size
