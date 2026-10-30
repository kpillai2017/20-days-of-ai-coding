"""Original procedural tabletop artwork and local hot-seat Pygame interface.

The rules know nothing about pixels. This module translates clicks into model
commands, and translates model state into circles, shadows, captions and pins.
No commercial board image, texture, model, logo or font file is bundled.
"""

import io
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pygame
from ai import all_codes, choose_guess, filter_candidates
from animation import PegFlight
from engine import ATTEMPTS, COLOURS, Match, Phase

WIDTH, HEIGHT = 1180, 920
BG = (22, 30, 34)
PANEL = (36, 46, 49)
INK = (243, 234, 213)
MUTED = (184, 189, 180)
GOLD = (233, 192, 111)
COLOUR_RGB = (
    (198, 48, 49),
    (240, 195, 48),
    (45, 145, 91),
    (47, 108, 197),
    (234, 231, 211),
    (35, 39, 42),
)
LETTERS = "RYGBWK"  # W=white and K=black avoid the two meanings of B.


def mix(a, b, amount):
    """Linear colour blending is enough for convincing small plastic highlights."""
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


class MastermindApp:
    """Two controllers can independently be human or computer, in either role."""

    def __init__(self, seed=None, demo=False):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Day 16 · Mastermind · The code table")
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.seed = seed
        self.fonts = {}
        self.match = None
        self.names = ["Player 1", "Player 2"]
        self.computers = [False, True]
        self.rounds = 1
        self.modal = None
        self.return_modal = None
        self.editing = 0
        self.name_draft = ""
        self.name_replace = False
        self.animation = None
        self.drag = None
        self.draft = [None] * 4
        self.selected = 0
        self.active_hole = 0
        self.buttons = []
        self.holes = []
        self.notice = "Choose controllers, then take turns making and breaking codes."
        self.running = True
        self.scale = 1
        self.offset = (0, 0)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.generation = 0
        self.candidates = all_codes()
        self.ai_after = 0
        if demo:
            self.computers = [True, True]
            self.names = ["Copper", "Brass"]
            self.start()

    def font(self, size, heading=False):
        """Cache installed fonts by role, with Pygame's default as a fallback."""
        key = size, heading
        if key not in self.fonts:
            family = (
                "georgia,dejavuserif"
                if heading
                else "avenirnext,trebuchetms,dejavusans,arial"
            )
            path = pygame.font.match_font(family, bold=heading)
            fallback = Path(pygame.__file__).parent / pygame.font.get_default_font()
            try:
                data = Path(path).read_bytes() if path else fallback.read_bytes()
            except OSError:
                data = fallback.read_bytes()
            self.fonts[key] = pygame.font.Font(io.BytesIO(data), size)
        return self.fonts[key]

    def text(self, message, x, y, size=19, color=INK, heading=False):
        self.surface.blit(
            self.font(size, heading).render(str(message), True, color), (x, y)
        )

    def fit(self, message, rect, size=20, color=INK, heading=False):
        """Shrink long user names rather than letting them overlap controls."""
        rect = pygame.Rect(rect)
        while size > 11 and self.font(size, heading).size(str(message))[0] > rect.width:
            size -= 1
        image = self.font(size, heading).render(str(message), True, color)
        self.surface.blit(image, (rect.x, rect.centery - image.get_height() // 2))

    def wrap(self, message, rect, size=18, color=MUTED):
        """Simple word wrapping; every caller allocates an explicit text region."""
        rect = pygame.Rect(rect)
        line, y = "", rect.y
        for word in str(message).split():
            test = (line + " " + word).strip()
            if line and self.font(size).size(test)[0] > rect.width:
                if y + size + 4 > rect.bottom:
                    return
                self.text(line, rect.x, y, size, color)
                y += size + 6
                line = word
            else:
                line = test
        if line and y + size + 4 <= rect.bottom:
            self.text(line, rect.x, y, size, color)

    def panel(self, rect, color=PANEL):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.surface, (10, 16, 18), rect.move(0, 4), border_radius=16)
        pygame.draw.rect(self.surface, color, rect, border_radius=16)
        pygame.draw.rect(self.surface, mix(color, INK, 0.12), rect, 1, border_radius=16)

    def button(self, rect, label, command, enabled=True, primary=False):
        """Disabled controls have neither a live hit area nor keyboard action."""
        rect = pygame.Rect(rect)
        color = (72, 97, 87) if primary else (59, 70, 71)
        if not enabled:
            color = (40, 47, 49)
        pygame.draw.rect(self.surface, color, rect, border_radius=9)
        pygame.draw.rect(
            self.surface,
            GOLD if primary and enabled else mix(color, INK, 0.18),
            rect,
            1,
            border_radius=9,
        )
        self.fit(label, rect.inflate(-20, 0), 18, INK if enabled else (117, 124, 123))
        if enabled:
            self.buttons.append((rect, command))
            mouse = self.logical(pygame.mouse.get_pos())
            if rect.collidepoint(mouse):
                pygame.draw.rect(self.surface, GOLD, rect, 2, border_radius=9)

    def peg(self, center, color, radius=20, label=None):
        """Draw a plastic peg: cast shadow, stem, bevel, dome and specular shine.

        Offset circles imitate overhead light. This is a 2D illustration, not
        a downloaded texture or physically accurate 3D lighting simulation.
        """
        x, y = map(round, center)
        pygame.draw.ellipse(
            self.surface,
            (39, 28, 22),
            (x - radius, y - radius + 8, radius * 2 + 5, radius * 2),
        )
        pygame.draw.circle(
            self.surface, mix(color, (0, 0, 0), 0.55), (x, y + 5), radius
        )
        pygame.draw.circle(self.surface, mix(color, (0, 0, 0), 0.22), (x, y), radius)
        pygame.draw.circle(self.surface, color, (x - 1, y - 2), radius - 2)
        pygame.draw.circle(
            self.surface,
            mix(color, (255, 255, 255), 0.18),
            (x - 3, y - 5),
            max(1, radius - 6),
        )
        pygame.draw.ellipse(
            self.surface,
            mix(color, (255, 255, 255), 0.65),
            (
                x - radius // 2,
                y - radius // 2 - 3,
                max(3, radius // 2),
                max(2, radius // 4),
            ),
        )
        if label:
            image = self.font(12).render(
                label, True, (20, 24, 25) if sum(color) > 420 else (250, 244, 224)
            )
            self.surface.blit(image, image.get_rect(center=(x, y + 3)))

    def socket(self, center, radius=22, selected=False):
        """Recessed holes invert the peg lighting: dark inside, lit lower rim."""
        x, y = map(round, center)
        pygame.draw.circle(self.surface, (166, 124, 83), (x, y + 2), radius + 2)
        pygame.draw.circle(self.surface, (49, 34, 26), (x, y), radius + 1)
        pygame.draw.circle(self.surface, (28, 24, 22), (x + 1, y - 1), radius - 3)
        if selected:
            pygame.draw.circle(self.surface, GOLD, (x, y), radius + 5, 2)

    def logical(self, pos):
        """Map resized/letterboxed window coordinates back into board coordinates."""
        return (
            (pos[0] - self.offset[0]) / self.scale,
            (pos[1] - self.offset[1]) / self.scale,
        )

    def start(self):
        """Create a fresh match; a running background calculation becomes stale."""
        try:
            match = Match(list(zip(self.names, self.computers)), self.seed, self.rounds)
        except ValueError as error:
            self.notice = str(error)
            return
        self.generation += 1
        if self.future:
            self.future.cancel()
        self.future = None
        self.match = match
        self.prepare_round()

    def prepare_round(self):
        """Never display a human maker's entry screen before a privacy handoff."""
        self.return_modal = None
        self.animation = None
        self.drag = None
        self.draft = [None] * 4
        self.active_hole = 0
        self.candidates = all_codes()
        self.ai_after = pygame.time.get_ticks() + 650
        self.notice = "The maker chooses a secret. Repeated colours are allowed."
        self.modal = (
            None if self.match.players[self.match.maker].is_ai else "maker_ready"
        )

    def human_entry(self):
        if not self.match or self.modal or self.future or self.animation:
            return False
        phase = self.match.phase
        return (
            phase == Phase.SETTING and not self.match.players[self.match.maker].is_ai
        ) or (
            phase == Phase.GUESSING and not self.match.players[self.match.breaker].is_ai
        )

    def place(self, hole):
        if self.human_entry():
            self.draft[hole] = self.selected
            self.active_hole = (hole + 1) % 4

    def commit(self):
        """The engine validates complete rows; partial rows never consume a turn."""
        if not self.human_entry():
            return
        try:
            # A human has already physically placed the draft pegs. Commit
            # them in place rather than replaying a second trip from the bank.
            if self.match.phase == Phase.SETTING:
                self.match.set_secret(self.draft)
                self.modal = "breaker_ready"
                self.notice = "Secret locked. Pass to the codebreaker."
            else:
                black, white = self.match.submit_guess(self.draft)
                self.after_guess()
                self.notice = f"Feedback: {black} exact, {white} colour only."
            self.drag = None
            self.draft = [None] * 4
            self.active_hole = 0
        except ValueError as error:
            self.notice = str(error)

    def begin_flight(self, code, secret=False):
        """Commit exactly once, then reveal pegs according to a separate clock."""
        if self.animation:
            return
        row = len(self.match.guesses)
        if secret:
            self.match.set_secret(code)
        else:
            self.match.submit_guess(code)
            self.after_guess()
        concealed = secret and self.match.players[self.match.maker].is_ai
        self.animation = PegFlight(
            code,
            "secret" if secret else "guess",
            row,
            pygame.time.get_ticks(),
            concealed,
        )
        self.drag = None
        self.notice = (
            "Placing the secret beneath its shield…"
            if concealed
            else "Placing pegs one at a time…"
        )

    def finish_flight(self):
        """Only after all landings may feedback or a new private handoff appear."""
        kind = self.animation.kind
        self.animation = None
        if kind == "secret":
            self.modal = (
                "breaker_ready"
                if not self.match.players[self.match.breaker].is_ai
                else None
            )
            self.notice = "Secret locked and shielded. The codebreaker may look."
        else:
            black, white = self.match.feedback[-1]
            self.notice = f"Feedback: {black} exact, {white} colour only."
        self.ai_after = pygame.time.get_ticks() + 650

    def finish_drag(self, pos):
        """A drop swaps draft values atomically; outside drops leave them alone."""
        drag, self.drag = self.drag, None
        if not drag or not self.human_entry():
            return
        if not drag["active"]:
            # Preserve the existing click-to-replace interaction.
            if drag.get("kind") != "bank":
                self.place(drag["source"])
            return
        for rect, target in self.holes:
            if rect.collidepoint(pos):
                if drag.get("kind") == "bank":
                    # The bank is a reusable colour supply, not a finite rack.
                    # Replacing a draft peg never moves or consumes bank stock.
                    self.draft[target] = drag["colour"]
                    self.active_hole = (target + 1) % 4
                    return
                source = drag["source"]
                self.draft[source], self.draft[target] = (
                    self.draft[target],
                    self.draft[source],
                )
                self.active_hole = target
                return

    def after_guess(self):
        """Filter using public feedback only; the AI never reads match.secret."""
        self.candidates = filter_candidates(
            self.candidates, self.match.guesses[-1], self.match.feedback[-1]
        )
        self.ai_after = pygame.time.get_ticks() + 1100

    def overlay(self, name):
        """Remember a privacy curtain when Help or a confirmation covers it."""
        if self.modal not in ("help", "quit", "new", "name"):
            self.return_modal = self.modal
        self.drag = None
        self.modal = name

    def dispatch(self, command):
        if command.startswith("controller:"):
            i = int(command.split(":")[1])
            self.computers[i] = not self.computers[i]
        elif command.startswith("name:"):
            self.editing = int(command.split(":")[1])
            self.name_draft = self.names[self.editing]
            self.name_replace = True
            self.modal = "name"
            pygame.key.start_text_input()
        elif command == "name_save":
            if self.name_draft.strip():
                self.names[self.editing] = self.name_draft.strip()
                self.modal = None
                pygame.key.stop_text_input()
        elif command == "rounds":
            self.rounds = self.rounds % 5 + 1
        elif command == "start":
            self.start()
        elif command == "ready":
            self.modal = None
            self.return_modal = None
            self.ai_after = pygame.time.get_ticks() + 650
        elif command.startswith("color:"):
            self.selected = int(command.split(":")[1])
        elif command == "submit":
            self.commit()
        elif command == "clear" and self.human_entry():
            self.draft = [None] * 4
            self.active_hole = 0
        elif (
            command == "next"
            and self.match
            and self.match.phase == Phase.ROUND_OVER
            and not self.animation
        ):
            self.match.next_round()
            if self.match.phase == Phase.SETTING:
                self.prepare_round()
        elif command == "new":
            self.overlay("new")
        elif command == "new_confirm":
            self.generation += 1
            if self.future:
                self.future.cancel()
            self.future = None
            self.match = None
            self.animation = None
            self.drag = None
            self.modal = None
        elif command == "help":
            self.overlay("help")
        elif command == "quit":
            self.overlay("quit")
        elif command == "quit_confirm":
            self.running = False
        elif command == "close":
            self.modal = self.return_modal
            self.return_modal = None
            pygame.key.stop_text_input()

    def event(self, event):
        if event.type == pygame.QUIT:
            self.overlay("quit")
        elif event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(
                (max(590, event.w), max(460, event.h)), pygame.RESIZABLE
            )
        elif event.type == pygame.TEXTINPUT and self.modal == "name":
            addition = "".join(c for c in event.text if c.isprintable())
            self.name_draft = (
                ("" if self.name_replace else self.name_draft) + addition
            )[:24]
            self.name_replace = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.logical(event.pos)
            for rect, command in reversed(self.buttons):
                if rect.collidepoint(pos):
                    self.dispatch(command)
                    if command.startswith("color:") and self.human_entry():
                        self.drag = {
                            "kind": "bank",
                            "colour": self.selected,
                            "start": pos,
                            "pos": pos,
                            "active": False,
                        }
                    return
            if not self.modal:
                for rect, index in self.holes:
                    if rect.collidepoint(pos):
                        if self.human_entry() and self.draft[index] is not None:
                            self.drag = {
                                "source": index,
                                "start": pos,
                                "pos": pos,
                                "active": False,
                            }
                        else:
                            self.place(index)
                        return
        elif event.type == pygame.MOUSEMOTION and self.drag:
            pos = self.logical(event.pos)
            self.drag["pos"] = pos
            if math.dist(pos, self.drag["start"]) >= 6:
                self.drag["active"] = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            self.finish_drag(self.logical(event.pos))
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.drag = None
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and not self.modal
            and self.human_entry()
        ):
            for rect, index in self.holes:
                if rect.collidepoint(self.logical(event.pos)):
                    self.draft[index] = None
                    self.active_hole = index
        elif event.type == pygame.KEYDOWN:
            if self.drag and event.key != pygame.K_ESCAPE:
                self.drag = None
            if self.modal == "name":
                if event.key == pygame.K_ESCAPE:
                    self.modal = None
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_RETURN:
                    self.dispatch("name_save")
                elif event.key == pygame.K_BACKSPACE:
                    self.name_draft = "" if self.name_replace else self.name_draft[:-1]
                    self.name_replace = False
                elif event.key == pygame.K_a and event.mod & (
                    pygame.KMOD_CTRL | pygame.KMOD_META
                ):
                    self.name_replace = True
                return
            if event.key == pygame.K_ESCAPE:
                if self.drag:
                    self.drag = None
                    return
                if self.modal in ("help", "new", "quit"):
                    self.dispatch("close")
                else:
                    self.overlay("quit")
            elif self.modal:
                if event.key == pygame.K_RETURN and self.modal in (
                    "maker_ready",
                    "breaker_ready",
                ):
                    self.dispatch("ready")
            elif event.key == pygame.K_F1:
                self.overlay("help")
            elif self.human_entry():
                if pygame.K_1 <= event.key <= pygame.K_6:
                    self.selected = event.key - pygame.K_1
                elif event.key == pygame.K_SPACE:
                    self.place(self.active_hole)
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.active_hole = (
                        self.active_hole + (1 if event.key == pygame.K_RIGHT else -1)
                    ) % 4
                elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    self.draft[self.active_hole] = None
                elif event.key == pygame.K_RETURN:
                    self.commit()

    def update(self):
        """One worker keeps AI search off the UI thread; stale results are ignored."""
        if not self.match:
            return
        if self.animation:
            self.animation.advance(pygame.time.get_ticks(), paused=bool(self.modal))
            if self.animation.done and not self.modal:
                self.finish_flight()
            return
        if self.modal:
            return
        match = self.match
        if self.future and self.future.done():
            future, self.future = self.future, None
            try:
                generation, guess = future.result()
                if generation == self.generation and match.phase == Phase.GUESSING:
                    self.begin_flight(guess)
            except Exception as error:
                self.notice = f"Computer search failed: {error}"
            return
        if self.future or pygame.time.get_ticks() < self.ai_after:
            return
        if match.phase == Phase.SETTING and match.players[match.maker].is_ai:
            self.begin_flight(
                tuple(match.rng.randrange(6) for _ in range(4)), secret=True
            )
            self.draft = [None] * 4
        elif match.phase == Phase.GUESSING and match.players[match.breaker].is_ai:
            candidates = tuple(self.candidates)
            guesses = tuple(match.guesses)
            generation = self.generation
            self.future = self.executor.submit(
                lambda: (generation, choose_guess(candidates, guesses))
            )
            self.notice = "Computer is considering only the public feedback…"

    def render_board(self):
        """A ten-row tray, numbered from the player's end toward the code shield."""
        # Raised brown injection-moulded body, bevel, screws and recessed wells.
        pygame.draw.rect(
            self.surface, (8, 13, 15), (78, 115, 494, 737), border_radius=30
        )
        pygame.draw.rect(
            self.surface, (88, 58, 39), (66, 99, 494, 737), border_radius=28
        )
        pygame.draw.rect(
            self.surface, (151, 109, 71), (70, 100, 486, 728), 3, border_radius=26
        )
        pygame.draw.rect(
            self.surface, (115, 78, 51), (88, 118, 449, 687), border_radius=18
        )
        for x, y in ((87, 121), (538, 121), (87, 810), (538, 810)):
            pygame.draw.circle(self.surface, (65, 50, 38), (x, y), 5)
            pygame.draw.line(self.surface, (169, 141, 104), (x - 3, y), (x + 3, y), 1)
        match = self.match
        revealed = (
            match
            and not self.animation
            and match.phase in (Phase.ROUND_OVER, Phase.MATCH_OVER)
        )
        setting = match and match.phase == Phase.SETTING and not self.modal
        secret_flight = self.animation and self.animation.kind == "secret"
        open_secret = secret_flight and not self.animation.concealed
        for i in range(4):
            center = (170 + i * 72, 170)
            self.socket(center)
            colour = match.secret[i] if revealed else self.draft[i] if setting else None
            if open_secret and self.animation.landed(i):
                colour = self.animation.code[i]
            if (
                self.drag
                and self.drag["active"]
                and self.drag.get("source") == i
                and setting
            ):
                colour = None
            if colour is not None:
                self.peg(center, COLOUR_RGB[colour], label=LETTERS[colour])
            if setting and self.human_entry():
                self.holes.append(
                    (pygame.Rect(center[0] - 26, center[1] - 26, 52, 52), i)
                )
        if not setting and not revealed and not open_secret:
            self.panel((119, 135, 309, 69), (83, 56, 40))
            self.fit("SECRET  /  SEALED", (147, 148, 260, 40), 19, GOLD, True)
            pygame.draw.line(self.surface, (185, 140, 91), (130, 139), (414, 139), 2)
        for row in range(ATTEMPTS):
            y = 752 - row * 54
            active = (
                match
                and not self.animation
                and match.phase == Phase.GUESSING
                and row == len(match.guesses)
            )
            rect = pygame.Rect(106, y - 25, 414, 51)
            pygame.draw.rect(
                self.surface,
                (127, 89, 58) if active else (101, 68, 46),
                rect,
                border_radius=8,
            )
            if active:
                pygame.draw.rect(self.surface, GOLD, rect, 2, border_radius=8)
            self.text(f"{row + 1:02}", 113, y - 9, 13, (224, 198, 160))
            for col in range(4):
                center = (170 + col * 72, y)
                self.socket(
                    center,
                    18,
                    active and col == self.active_hole and self.human_entry(),
                )
                colour = None
                if match and row < len(match.guesses):
                    colour = match.guesses[row][col]
                elif active and not self.modal:
                    colour = self.draft[col]
                if (
                    self.animation
                    and self.animation.kind == "guess"
                    and row == self.animation.row
                    and not self.animation.landed(col)
                ):
                    colour = None
                if (
                    active
                    and self.drag
                    and self.drag["active"]
                    and self.drag.get("source") == col
                ):
                    colour = None
                if colour is not None:
                    self.peg(center, COLOUR_RGB[colour], 16, LETTERS[colour])
                if active and self.human_entry():
                    self.holes.append(
                        (pygame.Rect(center[0] - 25, y - 24, 50, 48), col)
                    )
            # Grouped feedback is deliberately NOT aligned to guess positions.
            feedback = (
                match.feedback[row] if match and row < len(match.feedback) else None
            )
            if (
                self.animation
                and self.animation.kind == "guess"
                and row == self.animation.row
            ):
                feedback = None
            pins = ([5] * feedback[0] + [4] * feedback[1]) if feedback else []
            for i in range(4):
                center = (468 + (i % 2) * 21, y - 10 + (i // 2) * 20)
                self.socket(center, 5)
                if i < len(pins):
                    self.peg(center, COLOUR_RGB[pins[i]], 5)
        self.fit("CODE TABLE  ·  4 × 6", (125, 780, 340, 25), 13, (224, 198, 160))

    def render_side(self):
        match = self.match
        self.panel((610, 105, 510, 145))
        self.text("THE CODE TABLE", 635, 122, 14, GOLD)
        if not match:
            self.text("Make. Deduce. Discover.", 635, 155, 27, INK, True)
            self.wrap(
                "Two players. Four holes. Six colours. A small board with 1,296 possible secrets.",
                (635, 196, 460, 48),
            )
            return
        self.fit(
            f"Round {match.round_number} of {match.total_rounds}",
            (635, 150, 460, 38),
            28,
            INK,
            True,
        )
        self.fit(f"Maker: {match.players[match.maker].name}", (635, 197, 460, 23), 18)
        self.fit(
            f"Breaker: {match.players[match.breaker].name}", (635, 222, 460, 23), 18
        )
        for i, p in enumerate(match.players):
            self.panel((610, 267 + i * 69, 510, 59))
            self.fit(p.name, (630, 275 + i * 69, 320, 25), 20)
            self.text("Computer" if p.is_ai else "Human", 630, 302 + i * 69, 13, MUTED)
            self.fit(f"{p.score} pts", (984, 280 + i * 69, 115, 30), 23, GOLD, True)
        if self.animation:
            title = (
                "Placing secret…"
                if self.animation.kind == "secret"
                else f"Playing guess {self.animation.row + 1}"
            )
            detail = "Four pegs fly from the colour tray, one at a time. Feedback follows the final landing."
        elif match.phase == Phase.SETTING:
            title = "Choose the secret"
            detail = "Ask the breaker to look away. Fill four holes, then lock the code. Colours may repeat."
        elif match.phase == Phase.GUESSING:
            title = f"Guess {len(match.guesses) + 1} of 10"
            detail = "Drag from the colour bank to a hole, or select a colour and click a hole. Feedback pins give counts, not positions."
        elif match.phase == Phase.ROUND_OVER:
            title = "Code broken!" if match.solved else "Secret survived"
            award = match.history[-1]["points"]
            detail = f"{match.players[match.maker].name} earns {award} maker points. The secret is revealed above the rows."
        else:
            title = (
                "Match drawn"
                if len(match.winner) > 1
                else f"{match.players[match.winner[0]].name} wins"
            )
            detail = "Highest maker score wins after equal turns making codes. Start a new match to play again."
        self.fit(title, (630, 420, 470, 43), 27, GOLD, True)
        self.wrap(detail, (630, 472, 465, 82), 19)
        if self.animation or match.phase in (Phase.SETTING, Phase.GUESSING):
            active = self.human_entry()
            for i, name in enumerate(COLOURS):
                x = 647 + i * 79
                concealed = self.animation and self.animation.concealed
                self.peg(
                    (x, 592),
                    (101, 91, 78) if concealed else COLOUR_RGB[i],
                    23,
                    "?" if concealed else LETTERS[i],
                )
                if i == self.selected:
                    pygame.draw.circle(self.surface, GOLD, (x, 592), 29, 2)
                self.fit(f"{i + 1} {name}", (x - 32, 627, 73, 25), 12)
                if active:
                    self.buttons.append(
                        (pygame.Rect(x - 32, 561, 66, 94), f"color:{i}")
                    )
            complete = active and all(c is not None for c in self.draft)
            self.button(
                (630, 674, 294, 47),
                "Lock secret" if match.phase == Phase.SETTING else "Submit guess",
                "submit",
                complete,
                True,
            )
            self.button((938, 674, 162, 47), "Clear row", "clear", active)
            self.wrap(
                "Drag bank to hole · drag row pegs to swap · Enter submits",
                (630, 735, 470, 55),
                15,
            )
        elif match.phase == Phase.ROUND_OVER:
            final = match.round_number == match.total_rounds
            self.button(
                (630, 579, 470, 50),
                "Show match result" if final else "Next round · swap roles",
                "next",
                True,
                True,
            )
            self.wrap(
                "Maker points: one per guess; add one if all ten guesses failed. Most points wins.",
                (630, 650, 470, 78),
            )
        elif match.phase == Phase.MATCH_OVER:
            self.button((630, 580, 470, 50), "New match", "new", True, True)
        self.wrap(self.notice, (630, 800, 470, 70), 16)

    def render_motion(self):
        """Floating pegs draw over panels, but UNDER modal privacy curtains."""
        if self.drag and self.drag["active"] and self.human_entry():
            colour = (
                self.drag["colour"]
                if self.drag.get("kind") == "bank"
                else self.draft[self.drag["source"]]
            )
            self.peg(self.drag["pos"], COLOUR_RGB[colour], 22, LETTERS[colour])
            for rect, _ in self.holes:
                if rect.collidepoint(self.drag["pos"]):
                    pygame.draw.rect(self.surface, GOLD, rect, 2, border_radius=10)
        if self.animation:
            flying = self.animation.flying()
            if flying:
                index, x, y, radius = flying
                if self.animation.concealed:
                    # Neutral backs and fixed source slots reveal neither colour
                    # nor duplicate pattern in a computer maker's secret.
                    if y > 226:
                        self.peg((x, y), (101, 91, 78), radius, "?")
                else:
                    colour = self.animation.code[index]
                    self.peg((x, y), COLOUR_RGB[colour], radius, LETTERS[colour])

    def render_lobby(self):
        self.panel((610, 274, 510, 505))
        self.text("Choose your players", 635, 295, 27, INK, True)
        for i in range(2):
            y = 354 + i * 112
            self.text(f"SEAT {i + 1}", 635, y, 13, GOLD)
            self.button((635, y + 26, 265, 45), self.names[i], f"name:{i}")
            self.button(
                (914, y + 26, 180, 45),
                "Computer" if self.computers[i] else "Human",
                f"controller:{i}",
            )
        self.button(
            (635, 590, 460, 43),
            f"Maker rounds each: {self.rounds} · click to change",
            "rounds",
        )
        self.wrap(
            "Seat 1 makes the first code. Roles alternate. Every player gets the same number of maker rounds.",
            (635, 650, 460, 68),
        )
        self.button((635, 724, 460, 43), "Start match", "start", True, True)
        self.wrap(self.notice, (630, 803, 470, 65), 16)

    def render_modal(self):
        # Remove ALL underlying hit targets. Shading alone does not stop clicks.
        self.buttons, self.holes = [], []
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 210))
        self.surface.blit(shade, (0, 0))
        self.panel((230, 210, 720, 510))
        if self.modal in ("maker_ready", "breaker_ready"):
            maker = self.modal == "maker_ready"
            seat = self.match.maker if maker else self.match.breaker
            name = self.match.players[seat].name
            self.fit(f"Pass to {name}", (265, 252, 650, 52), 31, GOLD, True)
            self.wrap(
                "Codebreaker: look away while the maker enters the secret. The screen will be covered again before guessing begins."
                if maker
                else "The secret is now hidden. The codebreaker may look. Ready starts guessing; the secret stays shielded until the round ends.",
                (265, 342, 650, 160),
                23,
                INK,
            )
            self.button((265, 603, 650, 56), "Ready · Enter", "ready", True, True)
        elif self.modal == "name":
            self.text("Name this player", 265, 252, 30, GOLD, True)
            self.panel((265, 345, 650, 65), (21, 30, 31))
            self.fit(self.name_draft or "Type a name…", (283, 351, 610, 52), 26)
            self.wrap(
                "Up to 24 characters. Ctrl/Cmd+A replaces all; Backspace edits. Enter saves, Escape cancels.",
                (265, 443, 650, 70),
            )
            self.button((265, 603, 307, 50), "Cancel", "close")
            self.button(
                (593, 603, 322, 50),
                "Save name",
                "name_save",
                bool(self.name_draft.strip()),
                True,
            )
        elif self.modal == "help":
            self.text("How to play", 265, 240, 30, GOLD, True)
            paragraphs = [
                "Make a secret of FOUR pegs from SIX colours. Repeats are allowed; empty holes are not a colour.",
                "Black feedback = correct colour AND position. White feedback = correct colour, wrong position. A peg counts once. Feedback order does not identify positions.",
                "Break the code in TEN guesses. The maker earns one point per guess, plus one if unsolved. Swap roles; highest maker total wins after equal turns.",
                "Drag bank pegs into holes; drag row pegs to swap. Or choose colour 1–6 and click a hole (or Space). Enter locks/submits a full row. Right-click/Backspace removes a peg. The letter marks distinguish colours.",
            ]
            for i, p in enumerate(paragraphs):
                self.wrap(p, (265, 300 + i * 81, 650, 77), 17, INK)
            self.button((265, 650, 650, 44), "Back to table", "close", True, True)
        else:
            quitting = self.modal == "quit"
            self.text(
                "Close the table?" if quitting else "Start a new match?",
                265,
                260,
                30,
                GOLD,
                True,
            )
            self.wrap(
                "Current progress will be lost. This project does not save games automatically.",
                (265, 359, 650, 100),
                23,
            )
            self.button((265, 594, 310, 55), "Keep playing", "close", True, True)
            self.button(
                (595, 594, 320, 55),
                "Close" if quitting else "New match",
                "quit_confirm" if quitting else "new_confirm",
            )

    def render(self):
        self.surface.fill(BG)
        self.buttons, self.holes = [], []
        self.text("Mastermind", 65, 26, 39, INK, True)
        self.text("DAY 16  /  A CLASSIC CODE-BREAKING TABLE", 67, 76, 13, GOLD)
        self.button((850, 32, 122, 42), "Help · F1", "help")
        self.button((986, 32, 135, 42), "New match", "new", self.match is not None)
        self.render_board()
        self.render_side()
        if not self.match:
            self.render_lobby()
        self.text(
            "BLACK = EXACT     WHITE = COLOUR ONLY     /     REPEATS ALLOWED",
            70,
            870,
            13,
            MUTED,
        )
        self.render_motion()
        if self.modal:
            self.render_modal()
        w, h = self.window.get_size()
        self.scale = min(w / WIDTH, h / HEIGHT)
        size = (round(WIDTH * self.scale), round(HEIGHT * self.scale))
        self.offset = ((w - size[0]) // 2, (h - size[1]) // 2)
        self.window.fill((10, 15, 17))
        self.window.blit(pygame.transform.smoothscale(self.surface, size), self.offset)
        pygame.display.flip()

    def run(self, frames=0):
        """Always release the worker and display, including headless test exits."""
        count = 0
        try:
            while self.running and (not frames or count < frames):
                for event in pygame.event.get():
                    self.event(event)
                self.update()
                self.render()
                self.clock.tick(60)
                count += 1
        finally:
            self.executor.shutdown(wait=True, cancel_futures=True)
            pygame.quit()
