"""Enigma Lab: configure an Enigma I, press a key, and follow the signal.

python main.py opens the interactive window. --frames N limits a smoke test;
SDL_VIDEODRIVER=dummy selects headless mode separately. No audio is needed.
"""

import argparse
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from enigma import ALPHABET, Enigma
import appearance

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
        self.fields = {
            "rotors": "I II III",
            "positions": "AAA",
            "rings": "AAA",
            "plugboard": "",
        }
        self.active_field = None
        self.machine = Enigma()
        self.plain = self.cipher = ""
        self.lamp = None
        self.pressed_key = None
        self.held = False
        self.press_time = 0
        self.release_time = None
        self.old_positions = self.machine.positions
        self.message = (
            "Ready. Click a key or type A-Z. Educational only: not secure encryption."
        )

    def apply(self):
        try:
            # Construct first. Failed validation must not replace the old machine
            # or erase its transcript; assignment happens only after success.
            machine = Enigma(
                rotors=self.fields["rotors"].upper().split(),
                positions=self.fields["positions"],
                rings=self.fields["rings"],
                plugboard=self.fields["plugboard"],
            )
        except ValueError as error:
            self.message = f"Settings error: {error}"
            return False
        self.machine = machine
        self.fields.update(
            rotors=" ".join(machine.rotor_names),
            positions=machine.initial_positions,
            rings=machine.rings,
            plugboard=machine.plugboard_pairs,
        )
        self.restart()
        self.message = "Settings applied. Transcript cleared; machine is at its new initial positions."
        self.active_field = None
        return True

    def restart(self):
        self.machine.reset()
        self.plain = self.cipher = ""
        self.lamp = None
        self.pressed_key = None
        self.held = False
        self.press_time = 0
        self.release_time = None
        self.old_positions = self.machine.positions
        self.message = "Reset to APPLIED initial positions. To decrypt, type the ciphertext from the start."

    def press(self, letter):
        # One transcript entry corresponds to exactly one actual rotor step.
        # Refuse when full instead of silently losing old history.
        if len(self.plain) >= 500:
            self.message = (
                "500-letter transcript limit reached. Reset to start a new message."
            )
            return
        before = self.machine.positions
        output = self.machine.encode_letter(letter)
        self.old_positions = before
        self.pressed_key = letter.upper()
        self.press_time = pygame.time.get_ticks()
        self.release_time = None
        self.held = False
        self.plain += letter.upper()
        self.cipher += output
        self.lamp = output  # Logical last output remains available in the transcript.
        self.message = f"{letter.upper()} -> {output}. Windows now {self.machine.positions}. Reset before decrypting."

    def release(self):
        """Release changes only the illustration, never the rotor/cipher state."""
        if self.pressed_key is not None:
            self.held = False
            self.release_time = pygame.time.get_ticks()

    def animation(self, now=None):
        """Return rotor progress, physical-key depression and lamp brightness.

        A 240 ms rotor scroll and a gentle lamp fade are illustrative. Physical
        Enigma current follows the key circuit; no timed animation determines
        ciphertext. A direct programmatic press gets a brief automatic pulse.
        """
        now = pygame.time.get_ticks() if now is None else now
        age = max(0, now - self.press_time)
        progress = min(1, age / 240)
        if self.pressed_key is None:
            return 1, False, 0
        depressed = self.held or (self.release_time is None and age < 160)
        if self.held:
            brightness = min(1, age / 55)
        else:
            release = (
                self.release_time
                if self.release_time is not None
                else self.press_time + 180
            )
            brightness = min(1, age / 55) * max(0, 1 - max(0, now - release) / 280)
        return progress, depressed, brightness


def handle_event(event, lab):
    """Return False to quit. Text-field focus and machine typing are exclusive:
    editing 'AAA' must NOT accidentally encrypt three A's on the live machine.
    """
    if event.type == pygame.KEYUP:
        if getattr(
            event, "unicode", ""
        ).upper() == lab.pressed_key or event.key == getattr(
            pygame, "K_" + (lab.pressed_key or "").lower(), None
        ):
            lab.release()
        return True
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        lab.release()
        return True
    if event.type == pygame.WINDOWFOCUSLOST:
        lab.release()
        return True
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
                    lab.held = True
                    break
    elif event.type == pygame.KEYDOWN:
        if getattr(event, "repeat", False):
            return True
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
                lab.active_field = names[
                    (names.index(lab.active_field) + offset) % len(names)
                ]
        elif lab.active_field is not None:
            if event.key == pygame.K_RETURN:
                lab.apply()
            elif event.key == pygame.K_BACKSPACE:
                lab.fields[lab.active_field] = lab.fields[lab.active_field][:-1]
            elif event.key == pygame.K_a and event.mod & (
                pygame.KMOD_CTRL | pygame.KMOD_META
            ):
                # This lightweight field has no selection/cursor: clear to replace.
                lab.fields[lab.active_field] = ""
            elif not event.mod & (
                pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_ALT
            ):
                text = getattr(event, "unicode", "")
                allowed = ALPHABET + ALPHABET.lower() + " "
                if (
                    text
                    and all(char in allowed for char in text)
                    and len(lab.fields[lab.active_field]) + len(text) <= 40
                ):
                    lab.fields[lab.active_field] += text.upper()
        elif not event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_ALT):
            text = getattr(event, "unicode", "")
            if len(text) == 1 and text in ALPHABET + ALPHABET.lower():
                lab.press(text)
                lab.held = True
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
    chunks = [value[i : i + 5] for i in range(0, len(value), 5)]
    return " ".join(chunks[-groups:]) or "(none yet)"


def draw(screen, lab, fonts):
    small, normal, large = fonts
    screen.fill(BG)
    text(screen, small, "DAY 06 / ENIGMA LAB / ENIGMA I + REFLECTOR B", (24, 14), GREEN)
    text(screen, large, "A keypress. A moving alphabet.", (24, 36))
    for name, label, rect in FIELDS:
        text(screen, small, label, (rect.x, rect.y - 20), MUTED)
        pygame.draw.rect(screen, PANEL, rect, border_radius=5)
        pygame.draw.rect(
            screen,
            GOLD if lab.active_field == name else MUTED,
            rect,
            width=2,
            border_radius=5,
        )
        text(screen, normal, lab.fields[name], (rect.x + 8, rect.y + 10))
    for rect, label in (
        (APPLY, "Apply + reset"),
        (RESET, "Reset message"),
        (CLEAR_FOCUS, "Keyboard mode"),
    ):
        pygame.draw.rect(screen, (41, 62, 72), rect, border_radius=5)
        text(screen, normal, label, (rect.x + 8, rect.y + 11), GREEN)
    # The study controls surround an original, physical-machine-inspired face.
    appearance.machine_case(screen, small)
    progress, depressed, brightness = lab.animation()
    for index, name in enumerate(lab.machine.rotor_names):
        appearance.rotor(
            screen,
            (408 + index * 112, 224),
            lab.old_positions[index],
            lab.machine.positions[index],
            progress,
            f"{'LMR'[index]}: {name}",
            fonts,
        )
    for letter, rect in key_rects(315).items():
        appearance.lamp(
            screen, rect, letter, brightness if letter == lab.lamp else 0, normal
        )
    for letter, rect in key_rects(542).items():
        appearance.key(
            screen, rect, letter, depressed and letter == lab.pressed_key, normal
        )
    # Side panels keep transcripts and explanations outside the machine's deck.
    wrapped(screen, small, lab.message, 24, 253, 190, lines=7, color=GOLD)
    text(screen, small, "WINDOWS L / M / R", (24, 442), MUTED)
    text(screen, large, lab.machine.positions, (24, 470), GOLD)
    text(screen, small, "LAST KEY / LAMP", (850, 265), MUTED)
    text(
        screen,
        large,
        f"{lab.plain[-1:] or '-'}  /  {lab.lamp or '-'}",
        (850, 294),
        GOLD,
    )
    wrapped(
        screen,
        small,
        "Hold a key: its lamp glows. Release: light fades. Rotors step before the signal.",
        850,
        352,
        204,
        lines=5,
    )
    text(screen, small, "IN", (268, 463), MUTED)
    text(screen, small, grouped_tail(lab.plain, 6), (305, 463), MUTED)
    text(screen, small, "OUT", (268, 487), GREEN)
    text(screen, small, grouped_tail(lab.cipher, 6), (305, 487), GREEN)
    text(
        screen,
        small,
        "LAST SIGNAL - post-step windows; contact labels use A=0 ... Z=25",
        (24, 700),
        MUTED,
    )
    trace = lab.machine.last_trace
    for index, (label, letter) in enumerate(trace):
        col, row = index % 5, index // 5
        x, y = 24 + col * 210, 730 + row * 30
        text(
            screen,
            small,
            f"{label}: {letter}",
            (x, y),
            GREEN if index == len(trace) - 1 else INK,
        )
    text(
        screen,
        small,
        "Tab: edit fields | Enter: apply | Esc: leave field / quit | No modern security, save, or network",
        (24, 825),
        MUTED,
    )


def run(max_frames=None, start_3d=False):
    pygame.display.init()
    pygame.font.init()
    try:
        from view3d import View

        view = View((WIDTH, HEIGHT))
        pygame.display.set_caption("Day 06 - Enigma Lab | 20 Days of AI Coding")
        pygame.key.set_repeat()  # One press = one rotor step; no auto-repeat.
        fonts = tuple(pygame.font.Font(None, size) for size in (21, 24, 34))
        lab, clock = Lab(), pygame.time.Clock()
        if start_3d:
            view.toggle()
            lab.message = view.note
        frames, running = 0, True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if view.event(event, lab):
                    continue
                if not handle_event(event, lab):
                    running = False
                    break
            if not running:
                break
            view.draw(lab, fonts, draw)
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
    finally:
        if "view" in locals():
            view.close()
        pygame.quit()


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--frames", type=positive_int, help="quit after N frames for smoke tests"
    )
    parser.add_argument(
        "--3d",
        dest="start_3d",
        action="store_true",
        help="start in OpenGL view, falling back to 2D if unavailable",
    )
    args = parser.parse_args()
    run(args.frames, args.start_3d)
