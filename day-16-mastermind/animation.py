"""Presentation-only peg flights: committing rules and drawing are separate."""

import math


class PegFlight:
    """One peg flies for 650 ms, followed by a 140 ms landing pause.

    `concealed` means computer secret pegs must use neutral backs, not their
    actual colour. Timelines never decide scores, change secrets or add turns.
    """

    def __init__(self, code, kind, row, now, concealed=False):
        self.code = tuple(code)
        self.kind = kind
        self.row = row
        self.concealed = concealed
        self.flight_ms = 650
        self.step_ms = 790
        self.elapsed = 0
        self.last_tick = now

    def advance(self, now, paused=False):
        delta = max(0, now - self.last_tick)
        self.last_tick = now
        if not paused:
            self.elapsed += delta

    @property
    def done(self):
        return self.elapsed >= 4 * self.step_ms

    def landed(self, index):
        return self.elapsed >= index * self.step_ms + self.flight_ms

    def flying(self):
        if self.done:
            return None
        index = int(self.elapsed // self.step_ms)
        local = self.elapsed % self.step_ms
        if local >= self.flight_ms:
            return None
        t = local / self.flight_ms
        eased = t * t * (3 - 2 * t)
        # Concealed secrets launch from a neutral rack, independent of colour.
        start = (647 + (index if self.concealed else self.code[index]) * 79, 592)
        end = (170 + index * 72, 170 if self.kind == "secret" else 752 - self.row * 54)
        x = start[0] + (end[0] - start[0]) * eased
        y = start[1] + (end[1] - start[1]) * eased - 85 * math.sin(math.pi * t)
        return index, x, y, round(23 - 7 * eased)
