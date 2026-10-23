"""Enigma Lab: configure an Enigma I, press a key, and follow the signal.

python main.py opens the interactive window. --frames N limits a smoke test;
SDL_VIDEODRIVER=dummy selects headless mode separately. No audio is needed.
"""
import argparse
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from enigma import ALPHABET, Enigma

WIDTH, HEIGHT = 1080, 860
BG, PANEL, INK = (13, 19, 28), (24, 34, 48), (237, 243, 250)
MUTED, GREEN, GOLD = (166, 184, 202), (143, 235, 188), (255, 209, 124)
# Configuration order is LEFT to RIGHT. These controls use the same order.
FIELDS = [
    ("rotors", "Rotors L M R", pygame.Rect(24, 95, 210, 42)),
    ("positions", "Start L M R", pygame.Rect(250, 95, 150, 42)),
    ("rings", "Rings L M R", pygame.Rect(416, 95, 150, 42)),
    ("plugboard", "Plug pairs (max 10)", pygame.Rect(582, 95, 322, 42)),
]
APPLY = pygame.Rect(924, 95, 132, 42)
RESET = pygame.Rect(872, 174, 184, 42)
CLEAR_FOCUS = pygame.Rect(24, 174, 212, 42)
# Historical-style staggered rows, but not an exact photograph of a machine.
KEY_ROWS = ("QWERTZUIO", "ASDFGHJK", "PYXCVBNML")


def key_rects(y):
    """Compute clickable key locations, shared by drawing and mouse hit tests."""
    result = {}
    for row, letters in enumerate(KEY_ROWS):
        start = (WIDTH - len(letters) * 56) // 2
        for col, letter in enumerate(letters):
            result[letter] = pygame.Rect(start + col * 56, y + row * 46, 46, 38)
    return result


class Lab:
    """UI state is separate from cipher state. Draft settings don't affect the
    live machine until Apply succeeds, avoiding half-valid configurations.
    """
    def __init__(self):
        self.fields = {"rotors": "I II III", "positions": "AAA", "rings": "AAA", "plugboard": ""}
        self.active_field = None
        self.machine = Enigma()
        self.plain = self.cipher = ""
        self.lamp = None
        self.message = "Ready. Click a key or type A-Z. Educational only: not secure encryption."

    def apply(self):
        try:
            # Construct first. Failed validation must not replace the old machine
            # or erase its transcript; assignment happens only after success.
            machine = Enigma(rotors=self.fields["rotors"].upper().split(),
                             positions=self.fields["positions"], rings=self.fields["rings"],
                             plugboard=self.fields["plugboard"])
        except ValueError as error:
            self.message = f"Settings error: {error}"
            return False
        self.machine = machine
        self.fields.update(rotors=" ".join(machine.rotor_names), positions=machine.initial_positions,
                           rings=machine.rings, plugboard=machine.plugboard_pairs)
        self.restart()
        self.message = "Settings applied. Transcript cleared; machine is at its new initial positions."
        self.active_field = None
        return True

    def restart(self):
        self.machine.reset()
        self.plain = self.cipher = ""
        self.lamp = None
        self.message = "Reset to APPLIED initial positions. To decrypt, type the ciphertext from the start."

    def press(self, letter):
        # One transcript entry corresponds to exactly one actual rotor step.
        # Refuse when full instead of silently losing old history.
        if len(self.plain) >= 500:
            self.message = "500-letter transcript limit reached. Reset to start a new message."
            return
        output = self.machine.encode_letter(letter)
        self.plain += letter.upper()
        self.cipher += output
        self.lamp = output  # Last lamp stays lit until another key or reset.
        self.message = f"{letter.upper()} -> {output}. Windows now {self.machine.positions}. Reset before decrypting."


def handle_event(event, lab):
    """Return False to quit. Text-field focus and machine typing are exclusive:
    editing 'AAA' must NOT accidentally encrypt three A's on the live machine.
    """
    if event.type == pygame.QUIT:
        return False
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for name, _, rect in FIELDS:
            if rect.collidepoint(event.pos):
                lab.active_field = name
                lab.message = "Editing settings: Ctrl+A replaces this field; Enter applies; Tab changes fields."
                return True
        if APPLY.collidepoint(event.pos):
            lab.apply()
        elif RESET.collidepoint(event.pos):
            lab.restart()
            lab.active_field = None
        elif CLEAR_FOCUS.collidepoint(event.pos):
            lab.active_field = None
        else:
            lab.active_field = None
            for letter, rect in key_rects(542).items():
                if rect.collidepoint(event.pos):
                    lab.press(letter)
                    break
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            if lab.active_field is not None:
                lab.active_field = None
            else:
                return False
        elif event.key == pygame.K_TAB:
            names = [field[0] for field in FIELDS]
            if lab.active_field is None:
                lab.active_field = names[0]
            else:
                offset = -1 if event.mod & pygame.KMOD_SHIFT else 1
                lab.active_field = names[(names.index(lab.active_field) + offset) % len(names)]
        elif lab.active_field is not None:
            if event.key == pygame.K_RETURN:
                lab.apply()
            elif event.key == pygame.K_BACKSPACE:
                lab.fields[lab.active_field] = lab.fields[lab.active_field][:-1]
            elif event.key == pygame.K_a and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META):
                # This lightweight field has no selection/cursor: clear to replace.
                lab.fields[lab.active_field] = ""
            elif not event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_ALT):
                text = getattr(event, "unicode", "")
                allowed = ALPHABET + ALPHABET.lower() + " "
                if text and all(char in allowed for char in text) and len(lab.fields[lab.active_field]) + len(text) <= 40:
                    lab.fields[lab.active_field] += text.upper()
        elif not event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_ALT):
            text = getattr(event, "unicode", "")
            if len(text) == 1 and text in ALPHABET + ALPHABET.lower():
                lab.press(text)
    return True


def text(screen, font, value, pos, color=INK):
    screen.blit(font.render(value, True, color), pos)


def wrapped(screen, font, value, x, y, width, lines=2, color=INK):
    """Wrap words by measured pixel width; keep drawing inside a fixed panel."""
    rows, current = [], ""
    for word in value.split():
        trial = f"{current} {word}".strip()
        if current and font.size(trial)[0] > width:
            rows.append(current)
            current = word
        else:
            current = trial
    if current:
        rows.append(current)
    for row, line in enumerate(rows[:lines]):
        text(screen, font, line, (x, y + row * 22), color)


def grouped_tail(value, groups=11):
    """Show the most recent five-letter groups. Full transcript stays in memory."""
    chunks = [value[i:i + 5] for i in range(0, len(value), 5)]
    return " ".join(chunks[-groups:]) or "(none yet)"


def draw(screen, lab, fonts):
    small, normal, large = fonts
    screen.fill(BG)
    text(screen, small, "DAY 06 / ENIGMA LAB / ENIGMA I + REFLECTOR B", (24, 14), GREEN)
    text(screen, large, "A keypress. A moving alphabet.", (24, 36))
    for name, label, rect in FIELDS:
        text(screen, small, label, (rect.x, rect.y - 20), MUTED)
        pygame.draw.rect(screen, PANEL, rect, border_radius=5)
        pygame.draw.rect(screen, GOLD if lab.active_field == name else MUTED, rect, width=2, border_radius=5)
        text(screen, normal, lab.fields[name], (rect.x + 8, rect.y + 10))
    for rect, label in ((APPLY, "Apply + reset"), (RESET, "Reset message"), (CLEAR_FOCUS, "Keyboard mode")):
        pygame.draw.rect(screen, (41, 62, 72), rect, border_radius=5)
        text(screen, normal, label, (rect.x + 8, rect.y + 11), GREEN)
    for index, name in enumerate(lab.machine.rotor_names):
        x = 365 + index * 112
        text(screen, small, f"{'LMR'[index]}: {name}", (x, 153), MUTED)
        pygame.draw.rect(screen, PANEL, (x, 177, 76, 50), border_radius=5)
        text(screen, large, lab.machine.positions[index], (x + 25, 185), GOLD)
    wrapped(screen, small, lab.message, 24, 238, 1030, lines=2, color=GOLD)
    text(screen, small, "LAMPBOARD - last output remains lit", (24, 287), MUTED)
    for letter, rect in key_rects(315).items():
        pygame.draw.ellipse(screen, GOLD if letter == lab.lamp else PANEL, rect)
        text(screen, normal, letter, (rect.x + 15, rect.y + 9), BG if letter == lab.lamp else MUTED)
    text(screen, small, "IN   " + grouped_tail(lab.plain), (24, 468), MUTED)
    text(screen, small, "OUT  " + grouped_tail(lab.cipher), (24, 494), GREEN)
    text(screen, small, "KEYBOARD - click or type A-Z (Backspace does not rewind)", (24, 517), MUTED)
    for letter, rect in key_rects(542).items():
        pygame.draw.rect(screen, PANEL, rect, border_radius=6)
        pygame.draw.rect(screen, MUTED, rect, width=1, border_radius=6)
        text(screen, normal, letter, (rect.x + 15, rect.y + 9))
    text(screen, small, "LAST SIGNAL - post-step windows; contact labels use A=0 ... Z=25", (24, 687), MUTED)
    trace = lab.machine.last_trace
    for index, (label, letter) in enumerate(trace):
        col, row = index % 5, index // 5
        x, y = 24 + col * 210, 712 + row * 30
        text(screen, small, f"{label}: {letter}", (x, y), GREEN if index == len(trace) - 1 else INK)
    text(screen, small, "Tab: edit fields | Enter: apply | Esc: leave field / quit | No modern security, save, or network", (24, 825), MUTED)


def run(max_frames=None):
    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Day 06 - Enigma Lab | 20 Days of AI Coding")
        pygame.key.set_repeat()  # One press = one rotor step; no auto-repeat.
        fonts = tuple(pygame.font.Font(None, size) for size in (21, 24, 34))
        lab, clock = Lab(), pygame.time.Clock()
        frames, running = 0, True
        while running:
            clock.tick(30)
            for event in pygame.event.get():
                if not handle_event(event, lab):
                    running = False
                    break
            if not running:
                break
            draw(screen, lab, fonts)
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
    finally:
        pygame.quit()


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=positive_int, help="quit after N frames for smoke tests")
    run(parser.parse_args().frames)
