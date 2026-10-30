"""Original Pygame tabletop: input drafts moves; only engine commits them.

The pending-placement dictionary is a view model, not the real board. Humans
can recall or revise it without undoing engine history. Background AI searches
work on a snapshot, so a new game cannot race an old computer result.
"""

import copy
import io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pygame
from engine import Game, PREMIUMS
from ai import find_move
from definitions import lookup
from animation import TileFlight
from persistence import DEFAULT_SAVE, load_game, save_game

BG = (15, 29, 34)
PANEL = (26, 45, 51)
IVORY = (241, 232, 207)
INK = (37, 52, 53)
WHITE = (236, 243, 239)
MUTED = (165, 187, 187)
GOLD = (231, 193, 113)
GREEN = (49, 115, 93)
PREMIUM_COLORS = {
    1: (150, 199, 207),
    2: (66, 133, 158),
    3: (223, 156, 146),
    4: (186, 83, 86),
}
PREMIUM_LABELS = {1: "DL", 2: "TL", 3: "DW", 4: "TW"}


class ScrabbleApp:
    """One responsive local window, with explicit privacy and confirmation states."""

    WIDTH, HEIGHT = 1180, 920

    def __init__(self, lexicon, seed=None, demo=False):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("Scrabble · Day 15")
        self.surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = {}
        self.lexicon = lexicon
        self.save_path = DEFAULT_SAVE
        self.seed = seed
        self.modes = ["Human", "Computer", "Off", "Off"]
        self.human_names = [f"Human {i + 1}" for i in range(4)]
        self.editing_name = None
        self.name_draft = ""
        self.name_select_all = False
        self.game = None
        self.running = True
        self.modal = None
        self.log_filter = None
        self.log_page = 0
        self.pending = {}
        self.selected = None
        self.exchange_mode = False
        self.exchange_selected = set()
        self.blank_target = None
        self.drag = None
        self.animation = None
        self.notice = ""
        self.buttons = []
        self.disabled = []
        self.disabled_reasons = []
        self.scale = 1
        self.offset = (0, 0)
        self.cells = {
            (r, c): pygame.Rect(38 + c * 42, 110 + r * 42, 42, 42)
            for r in range(15)
            for c in range(15)
        }
        self.rack_rects = [pygame.Rect(153 + i * 65, 792, 55, 55) for i in range(7)]
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="scrabble-search"
        )
        self.future = None
        self.search_kind = None
        self.definition_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="word-definition"
        )
        self.definition_jobs = {}
        self.definition_cache = {}
        self.inspected_words = []
        self.word_index = 0
        self.definition_page = 0
        self.score_page = 0
        self.generation = 0
        self.ai_ready = 0
        # Privacy is a persistent turn permission, not inferred from which
        # overlay happens to be visible (e.g. window-close during handoff).
        self.rack_revealed = False
        if demo:
            self.start([(f"Computer {i + 1}", True) for i in range(4)])

    def font(self, size, role="body"):
        """Cache fonts by size AND purpose: a heading is not a tile letter.

        Font families are tried in order, so each OS can use an installed
        equivalent. We read bytes rather than keeping font files open; no
        commercial system font is copied into this project's distribution.
        """
        families = {
            "heading": "georgia,palatino,dejavuserif",
            "body": "avenirnext,trebuchetms,dejavusans,arial",
            "tile": "trebuchetms,dejavusans,arial",
        }
        key = (size, role)
        if key not in self.fonts:
            path = pygame.font.match_font(
                families[role], bold=role in ("heading", "tile")
            )
            fallback = Path(pygame.__file__).parent / pygame.font.get_default_font()
            try:
                data = Path(path).read_bytes() if path else fallback.read_bytes()
            except OSError:
                data = fallback.read_bytes()
            self.fonts[key] = pygame.font.Font(io.BytesIO(data), size)
        return self.fonts[key]

    def text(self, message, x, y, size=20, color=WHITE, role=None):
        """Large titles get a bookish serif; small instructions stay sans-serif."""
        role = role or ("heading" if size >= 24 else "body")
        self.surface.blit(
            self.font(size, role).render(str(message), True, color), (x, y)
        )

    def fit(self, message, rect, size=19, color=WHITE, role=None):
        """Fit labels without switching font families midway through shrinking."""
        role = role or ("heading" if size >= 24 else "body")
        rect = pygame.Rect(rect)
        while size > 10 and self.font(size, role).size(str(message))[0] > rect.width:
            size -= 1
        image = self.font(size, role).render(str(message), True, color)
        self.surface.blit(image, (rect.x, rect.centery - image.get_height() // 2))

    def wrap(self, message, rect, size=19, color=WHITE):
        """Draw wrapped prose clipped to a panel; rules errors remain readable."""
        rect = pygame.Rect(rect)
        old = self.surface.get_clip()
        self.surface.set_clip(rect)
        y = rect.y
        for paragraph in str(message).split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if line and self.font(size).size(candidate)[0] > rect.width:
                    self.text(line, rect.x, y, size, color, role="body")
                    y += self.font(size).get_linesize()
                    line = word
                else:
                    line = candidate
            self.text(line, rect.x, y, size, color, role="body")
            y += self.font(size).get_linesize()
        self.surface.set_clip(old)

    def panel(self, rect, color=PANEL):
        """Reuse a consistent card treatment across setup, HUD and dialogs."""
        pygame.draw.rect(self.surface, color, rect, border_radius=12)
        pygame.draw.rect(self.surface, (58, 80, 83), rect, 1, border_radius=12)

    def button(self, rect, label, command, enabled=True, reason=None):
        """Enabled/disabled is one consistent signal, not an artistic hint."""
        rect = pygame.Rect(rect)
        pygame.draw.rect(
            self.surface, GREEN if enabled else (40, 52, 56), rect, border_radius=7
        )
        pygame.draw.rect(
            self.surface,
            (96, 173, 145) if enabled else (77, 90, 94),
            rect,
            1,
            border_radius=7,
        )
        content = rect.inflate(-18, -8)
        if rect.height <= 65 and command not in (
            "close",
            "ready",
            "quit_confirm",
            "new_confirm",
            "pass_confirm",
        ):
            content.width -= 19
            # State is an explicit symbol as well as colour: hollow dot means
            # unavailable, filled dot means clickable. Hover reveals reasons.
            pygame.draw.circle(
                self.surface,
                (171, 236, 204) if enabled else MUTED,
                (rect.right - 15, rect.centery),
                3,
                0 if enabled else 1,
            )
        self.fit(label, content, 18, WHITE if enabled else MUTED)
        mouse = (
            (pygame.mouse.get_pos()[0] - self.offset[0]) / self.scale,
            (pygame.mouse.get_pos()[1] - self.offset[1]) / self.scale,
        )
        if enabled and pygame.mouse.get_focused() and rect.collidepoint(mouse):
            pygame.draw.rect(
                self.surface,
                GOLD if pygame.mouse.get_pressed()[0] else (151, 205, 180),
                rect,
                2,
                border_radius=7,
            )
        if enabled:
            self.buttons.append((rect, command))
        else:
            self.disabled.append(rect)
            self.disabled_reasons.append(
                (rect, reason or "Not available during this decision.")
            )

    def start(self, names):
        """Create a new generation and invalidate any previous background work."""
        self.generation += 1
        if self.future:
            self.future.cancel()
        self.future = None
        self.animation = None
        self.game = Game(names, self.lexicon, self.seed)
        self.log_filter = None
        self.log_page = 0
        self.clear_draft()
        self.notice = ""
        self.handoff()

    def clear_draft(self):
        """Discard view-only placements before changing rack order or turns."""
        self.drag = None
        self.pending.clear()
        self.selected = None
        self.exchange_mode = False
        self.exchange_selected.clear()
        self.blank_target = None

    def handoff(self):
        """Hide every new human rack until that player explicitly says ready."""
        self.rack_revealed = False
        if self.game.phase == "gameover":
            self.modal = None
        else:
            self.modal = (
                None if self.game.players[self.game.current].is_ai else "handoff"
            )
        self.ai_ready = pygame.time.get_ticks() + 400

    def human_active(self):
        """Read-only controls remain available even when turn actions are not."""
        return bool(
            self.game
            and self.game.phase == "play"
            and not self.modal
            and self.rack_revealed
            and not self.game.players[self.game.current].is_ai
            and self.future is None
            and self.animation is None
        )

    def preview(self):
        """Translate validation exceptions into a score/error display, not a crash."""
        if not self.pending:
            return None, ""
        try:
            return self.game.preview(self.pending), ""
        except ValueError as error:
            return None, str(error)

    def board_click(self, pos):
        """Click a provisional tile to recall it; committed tiles cannot move."""
        if not self.human_active() or self.exchange_mode:
            return
        if pos in self.pending:
            del self.pending[pos]
            return
        if pos in self.game.board or self.selected is None:
            return
        index = self.selected
        if index in {i for i, letter in self.pending.values()}:
            return
        tile = self.game.players[self.game.current].rack[index]
        if tile.blank:
            self.blank_target = pos, index
            self.modal = "blank"
        else:
            self.pending[pos] = (index, tile.letter)
            self.selected = None
        self.notice = ""

    def begin_search(self, kind):
        """Search an isolated snapshot; dictionary/trie can be shared read-only."""
        if self.future is not None:
            return
        snapshot = copy.copy(self.game)
        snapshot.board = dict(self.game.board)
        snapshot.players = copy.deepcopy(self.game.players)
        self.search_kind = kind, self.generation, self.game.current
        self.future = self.executor.submit(find_move, snapshot, self.lexicon, 1.4)

    def dispatch(self, command):
        """A single command dispatcher supports both mouse clicks and tests."""
        if command.startswith("name:"):
            index = int(command.split(":")[1])
            if self.game is None and self.modes[index] == "Human":
                self.editing_name = index
                self.name_draft = self.human_names[index]
                self.name_select_all = True
                self.modal = "name"
                pygame.key.start_text_input()
        elif command == "name_save":
            value = self.name_draft.strip()
            if not value:
                self.notice = "Please enter a name, or cancel to keep the existing one."
            elif any(
                i != self.editing_name
                and self.modes[i] != "Off"
                and value.casefold()
                == (
                    self.human_names[i]
                    if self.modes[i] == "Human"
                    else f"Computer {i + 1}"
                ).casefold()
                for i in range(4)
            ):
                self.notice = "Choose a distinct name for each active player."
            else:
                self.human_names[self.editing_name] = value
                self.notice = ""
                self.modal = None
                pygame.key.stop_text_input()
        elif command == "inspect_next":
            self.word_index = (self.word_index + 1) % len(self.inspected_words)
            self.definition_page = 0
            self.request_definition()
        elif command == "definition_next":
            self.definition_page += 1
        elif command == "lookup_definition":
            self.request_definition()
        elif command == "save" and self.game:
            self.modal = "save"
        elif command == "load":
            self.modal = "load"
        elif command == "save_confirm" and self.game:
            try:
                save_game(self.game, self.save_path)
            except (OSError, ValueError) as error:
                self.notice = f"Save failed: {error}"
            else:
                self.notice = f"Game saved to {self.save_path}"
                self.dispatch("close")
        elif command == "load_confirm":
            try:
                restored = load_game(self.lexicon, self.save_path)
            except (OSError, ValueError) as error:
                self.notice = f"Load failed: {error}"
            else:
                # Discard stale worker results BEFORE swapping in restored state.
                self.generation += 1
                if self.future:
                    self.future.cancel()
                self.future = None
                self.animation = None
                self.game = restored
                self.clear_draft()
                self.log_filter = None
                self.log_page = 0
                self.handoff()
                self.notice = "Saved game loaded. Unfinished drafts were not saved."
        elif command == "turn_log" and self.game:
            self.log_filter = None
            self.log_page = 0
            self.modal = "log"
        elif command.startswith("log_filter:") and self.game:
            value = command.split(":")[1]
            self.log_filter = None if value == "all" else int(value)
            self.log_page = 0
        elif command in ("log_previous", "log_next") and self.game:
            change = -1 if command == "log_previous" else 1
            last = max(0, (len(self.log_entries()) - 1) // 4)
            self.log_page = max(0, min(last, self.log_page + change))
        elif command == "score_details":
            self.score_page = 0
            self.modal = "score"
        elif command == "score_next":
            result, _ = self.preview()
            if result:
                self.score_page = (self.score_page + 1) % len(result.breakdown)
        elif command == "quit_confirm":
            self.running = False
        elif command == "close":
            if self.modal == "name":
                pygame.key.stop_text_input()
                self.notice = ""
            self.modal = (
                "handoff"
                if self.game
                and self.animation is None
                and self.game.phase == "play"
                and not self.game.players[self.game.current].is_ai
                and not self.rack_revealed
                else None
            )
        elif command == "return_handoff":
            self.modal = "handoff"
        elif command == "help_button":
            self.modal = "help"
        elif command == "ready":
            self.rack_revealed = True
            self.modal = None
        elif command.startswith("seat:"):
            i = int(command.split(":")[1])
            modes = ["Human", "Computer", "Off"]
            self.modes[i] = modes[(modes.index(self.modes[i]) + 1) % 3]
        elif command == "start":
            names = [
                (
                    self.human_names[i] if mode == "Human" else f"Computer {i + 1}",
                    mode == "Computer",
                )
                for i, mode in enumerate(self.modes)
                if mode != "Off"
            ]
            if len(names) < 2:
                self.notice = "Choose at least two active seats."
            elif len({name.casefold() for name, ai in names}) != len(names):
                self.notice = "Choose distinct names for all active players."
            else:
                self.start(names)
        elif command == "new":
            self.modal = "new"
        elif command == "new_confirm":
            self.generation += 1
            if self.future:
                self.future.cancel()
            self.future = None
            self.animation = None
            self.game = None
            self.modal = None
            self.clear_draft()
        elif command.startswith("blank:") and self.modal == "blank":
            letter = command.split(":")[1]
            pos, index = self.blank_target
            self.pending[pos] = (index, letter)
            self.selected = None
            self.blank_target = None
            self.modal = None
        elif command == "pass_confirm" and self.modal == "pass":
            self.game.pass_turn()
            self.clear_draft()
            self.handoff()
        elif not self.human_active():
            return
        elif command.startswith("rack:"):
            index = int(command.split(":")[1])
            if self.exchange_mode:
                if index in self.exchange_selected:
                    self.exchange_selected.remove(index)
                else:
                    self.exchange_selected.add(index)
            elif index not in {i for i, letter in self.pending.values()}:
                self.selected = index
        elif command == "recall":
            self.clear_draft()
            self.notice = "Draft recalled. No turn used."
        elif command == "play":
            try:
                score = self.commit_animated(self.pending)
            except ValueError as error:
                self.notice = str(error)
            else:
                self.notice = f"Move accepted: {score} points."
                self.clear_draft()
        elif command == "pass":
            self.modal = "pass"
        elif command == "exchange":
            if self.exchange_mode:
                try:
                    self.game.exchange(sorted(self.exchange_selected))
                except ValueError as error:
                    self.notice = str(error)
                else:
                    self.clear_draft()
                    self.handoff()
            elif len(self.game.bag) < 7:
                self.notice = "At least seven tiles must be in the bag to exchange."
            else:
                self.clear_draft()
                self.exchange_mode = True
                self.notice = (
                    "Select rack tiles, then confirm exchange. Recall cancels."
                )
        elif command == "shuffle":
            self.clear_draft()
            self.game.shuffle_rack()
        elif command == "hint":
            self.clear_draft()
            self.begin_search("hint")

    def commit_animated(self, placements):
        """Snapshot only played tile identities, commit once, then reveal slowly.

        Never snapshot/display an AI's unused rack. Source slot positions convey
        where each played tile came from without revealing other private tiles.
        """
        player = self.game.current
        result = self.game.preview(placements)
        items = []
        for position in sorted(placements):
            index, letter = placements[position]
            items.append(
                {
                    "position": position,
                    "placed": result.placements[position],
                    "start": self.rack_rects[index].center,
                    "end": self.cells[position].center,
                    "rack_index": index,
                }
            )
        score = self.game.play(placements)
        self.animation = TileFlight(items, player, pygame.time.get_ticks())
        self.rack_revealed = False
        self.modal = None
        return score

    def render_flight(self):
        """Show only played tiles at source slots; unused rack faces stay hidden."""
        if self.animation is None:
            return
        flight = self.animation
        for index, item in enumerate(flight.items):
            if flight.elapsed < index * flight.step_ms:
                tile = item["placed"]
                x, y = item["start"]
                self.tile(
                    pygame.Rect(x - 27, y - 27, 55, 55),
                    tile.letter,
                    tile.value,
                    blank=tile.blank,
                )
        flying = flight.flying()
        if flying:
            index, x, y, size = flying
            tile = flight.items[index]["placed"]
            shadow = pygame.Rect(
                round(x - size / 2) + 4,
                round(y - size / 2) + 8,
                round(size),
                round(size),
            )
            pygame.draw.rect(self.surface, (17, 29, 29), shadow, border_radius=5)
            self.tile(
                pygame.Rect(
                    round(x - size / 2), round(y - size / 2), round(size), round(size)
                ),
                tile.letter,
                tile.value,
                selected=True,
                blank=tile.blank,
            )

    def logical_point(self, pos):
        """Use the same coordinate conversion for press, motion and release."""
        return (
            (pos[0] - self.offset[0]) / self.scale,
            (pos[1] - self.offset[1]) / self.scale,
        )

    def begin_drag(self, source, index, pos, board_pos=None):
        """Remember identity without removing anything until a valid drop.

        Holding references in this view model means an outside-window release
        or a cancelled drag cannot lose a physical tile or mutate the board.
        """
        self.drag = {
            "source": source,
            "index": index,
            "board": board_pos,
            "start": pos,
            "pos": pos,
            "active": False,
        }

    def reorder_rack(self, source, target):
        """Move one physical tile and remap every pending rack reference.

        Draft placements store rack indices, not copies. Reordering without
        updating these references would silently change a drafted word's tiles.
        """
        rack = self.game.players[self.game.current].rack
        order = list(range(len(rack)))
        old = order.pop(source)
        order.insert(target, old)
        remap = {old: new for new, old in enumerate(order)}
        rack[:] = [rack[index] for index in order]
        self.pending = {
            pos: (remap[index], letter) for pos, (index, letter) in self.pending.items()
        }
        if self.selected is not None:
            self.selected = remap[self.selected]

    def finish_drag(self, pos):
        """Commit a drop to the draft/rack only; rules still validate on Play."""
        drag = self.drag
        self.drag = None
        if drag is None or not self.human_active():
            return
        if not drag["active"]:
            if drag["source"] == "board":
                self.board_click(drag["board"])
            return
        source = drag["board"]
        index = drag["index"]
        # Drop on a rack slot: recall a draft tile, then reorder the rack.
        rack = self.game.players[self.game.current].rack
        target = next(
            (
                i
                for i, rect in enumerate(self.rack_rects[: len(rack)])
                if rect.collidepoint(pos)
            ),
            None,
        )
        if target is not None:
            if source is not None:
                self.pending.pop(source, None)
            self.reorder_rack(index, target)
            self.selected = None
            return
        target = next(
            (cell for cell, rect in self.cells.items() if rect.collidepoint(pos)), None
        )
        if target is None or target in self.game.board:
            self.notice = "Drop cancelled — use an empty board square or the rack."
            return
        if source == target:
            return
        if source is None:
            if target in self.pending:
                self.notice = "That square already has a draft tile."
                return
            self.selected = index
            self.board_click(target)  # Includes the normal blank-letter dialog.
        else:
            tile = self.pending[source]
            other = self.pending.get(target)
            if other is None:
                del self.pending[source]
            else:
                self.pending[source] = other
            self.pending[target] = tile
            self.selected = None

    def render_drag(self):
        """Draw the dragged tile over the table and show a legal drop outline."""
        if not self.drag or not self.drag["active"] or not self.human_active():
            return
        drag = self.drag
        x, y = drag["pos"]
        target = next(
            (
                rect
                for cell, rect in self.cells.items()
                if rect.collidepoint((x, y)) and cell not in self.game.board
            ),
            None,
        )
        if target is None:
            target = next(
                (rect for rect in self.rack_rects if rect.collidepoint((x, y))), None
            )
        if target:
            pygame.draw.rect(self.surface, GOLD, target, 3, border_radius=4)
        tile = self.game.players[self.game.current].rack[drag["index"]]
        letter = (
            self.pending[drag["board"]][1] if drag["board"] is not None else tile.letter
        )
        self.tile(
            pygame.Rect(round(x) - 27, round(y) - 28, 55, 55),
            letter,
            tile.value,
            selected=True,
            blank=tile.blank,
            pending=True,
        )

    def event(self, event):
        """Transform scaled clicks once, then route modal buttons before board."""
        if event.type == pygame.QUIT:
            self.drag = None
            self.modal = "quit"
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.drag = None
        elif event.type == pygame.MOUSEMOTION and self.drag:
            point = self.logical_point(event.pos)
            self.drag["pos"] = point
            dx = point[0] - self.drag["start"][0]
            dy = point[1] - self.drag["start"][1]
            if dx * dx + dy * dy >= 36:
                self.drag["active"] = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.finish_drag(self.logical_point(event.pos))
        elif event.type == pygame.MOUSEWHEEL and self.modal == "log":
            if event.y:
                self.dispatch("log_previous" if event.y > 0 else "log_next")
        elif event.type == pygame.TEXTINPUT and self.modal == "name":
            # TEXTINPUT supports Unicode names and OS keyboard layouts. Control
            # characters are rejected, and length is bounded to fit scorecards.
            text = "".join(ch for ch in event.text if ch.isprintable())
            self.name_draft = (
                ("" if self.name_select_all else self.name_draft) + text
            )[:20]
            self.name_select_all = False
        elif event.type == pygame.KEYDOWN:
            if self.modal == "name":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.dispatch("name_save")
                elif event.key == pygame.K_ESCAPE:
                    self.dispatch("close")
                elif event.key == pygame.K_BACKSPACE:
                    self.name_draft = (
                        "" if self.name_select_all else self.name_draft[:-1]
                    )
                    self.name_select_all = False
                elif event.key == pygame.K_a and getattr(event, "mod", 0) & (
                    pygame.KMOD_CTRL | pygame.KMOD_META
                ):
                    self.name_select_all = True
                return
            if self.modal == "log" and event.key in (
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_PAGEUP,
                pygame.K_PAGEDOWN,
            ):
                self.dispatch(
                    "log_previous"
                    if event.key in (pygame.K_LEFT, pygame.K_PAGEUP)
                    else "log_next"
                )
                return
            if event.key == pygame.K_ESCAPE:
                if self.drag:
                    self.drag = None
                    return
                if self.modal in ("handoff", "quit_handoff"):
                    self.modal = (
                        "quit_handoff" if self.modal == "handoff" else "handoff"
                    )
                elif self.modal:
                    self.dispatch("close")
                else:
                    self.modal = "quit"
            elif event.key == pygame.K_F1:
                if self.modal not in ("handoff", "quit_handoff"):
                    self.modal = None if self.modal == "help" else "help"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = (
                (event.pos[0] - self.offset[0]) / self.scale,
                (event.pos[1] - self.offset[1]) / self.scale,
            )
            for rect, command in reversed(self.buttons):
                if rect.collidepoint(pos):
                    if (
                        command.startswith("rack:")
                        and self.human_active()
                        and not self.exchange_mode
                    ):
                        self.begin_drag("rack", int(command.split(":")[1]), pos)
                    self.dispatch(command)
                    return
            if self.modal is None:
                for cell, rect in self.cells.items():
                    if rect.collidepoint(pos):
                        if (
                            cell in self.pending
                            and self.human_active()
                            and not self.exchange_mode
                        ):
                            self.begin_drag("board", self.pending[cell][0], pos, cell)
                        else:
                            if cell in self.game.board and self.animation is None:
                                self.inspect_word(cell)
                            else:
                                self.board_click(cell)
                        return

    def update(self):
        """Poll completed workers; never wait on an unfinished future in the UI."""
        for word, future in list(self.definition_jobs.items()):
            if future.done():
                try:
                    self.definition_cache[word] = future.result()
                except Exception:
                    self.definition_cache[word] = {
                        "status": "Definition lookup failed.",
                        "entries": [],
                    }
                del self.definition_jobs[word]
        if self.animation is not None:
            self.animation.advance(
                pygame.time.get_ticks(), paused=self.modal is not None
            )
            if not self.animation.done:
                return
            self.animation = None
            self.handoff()
            return
        if self.future and self.future.done():
            # A completed AI move waits behind a quit/help dialog. Do not reveal
            # the next human rack or change the game underneath a confirmation.
            if self.modal:
                return
            future = self.future
            kind, generation, player = self.search_kind
            self.future = None
            try:
                move = future.result()
            except Exception as error:
                self.notice = f"Search failed: {error}"
                move = None
            if (
                generation != self.generation
                or not self.game
                or self.game.current != player
            ):
                return
            if kind == "hint":
                if move:
                    self.pending = move
                    self.notice = (
                        "Suggested draft — review its score, then Play or Recall."
                    )
                else:
                    self.notice = "No move found within the search budget."
            else:
                if move:
                    self.commit_animated(move)
                elif len(self.game.bag) >= 7:
                    self.game.exchange(list(range(len(self.game.players[player].rack))))
                else:
                    self.game.pass_turn()
                self.clear_draft()
                if self.animation is None:
                    self.handoff()
        if (
            self.game
            and self.game.phase == "play"
            and not self.modal
            and not self.future
            and self.animation is None
            and self.game.players[self.game.current].is_ai
            and pygame.time.get_ticks() >= self.ai_ready
        ):
            self.begin_search("ai")

    def star(self, center, radius=12, color=INK):
        """Draw a ten-vertex star, avoiding font-dependent missing glyphs."""
        import math

        points = []
        for n in range(10):
            angle = -math.pi / 2 + n * math.pi / 5
            length = radius if n % 2 == 0 else radius * 0.43
            points.append(
                (
                    center[0] + math.cos(angle) * length,
                    center[1] + math.sin(angle) * length,
                )
            )
        pygame.draw.polygon(self.surface, color, points)

    def tile(self, rect, letter, value, selected=False, blank=False, pending=False):
        """Square wood-style tiles: centred letter, low-right value, blank dot.

        Physical blanks are empty before assignment, not a diamond character.
        Their zero value and small marker persist after assignment to a letter.
        """
        rect = pygame.Rect(rect).inflate(-5, -5)
        pygame.draw.rect(self.surface, (116, 81, 42), rect.move(0, 3), border_radius=4)
        pygame.draw.rect(
            self.surface,
            (215, 233, 200) if pending else (238, 214, 166),
            rect,
            border_radius=4,
        )
        pygame.draw.line(
            self.surface, (255, 241, 208), rect.topleft, (rect.right - 3, rect.y), 2
        )
        pygame.draw.rect(
            self.surface,
            GOLD if selected else (171, 135, 80),
            rect,
            3 if selected else 1,
            border_radius=4,
        )
        if letter != "?":
            image = self.font(29 if rect.width >= 45 else 25, "tile").render(
                letter, True, INK
            )
            self.surface.blit(
                image,
                (
                    rect.centerx - image.get_width() // 2 - 1,
                    rect.centery - image.get_height() // 2 - 1,
                ),
            )
        self.text(str(value), rect.right - 11, rect.bottom - 14, 10, INK)
        if blank:
            pygame.draw.circle(
                self.surface, (41, 99, 78), (rect.x + 6, rect.bottom - 7), 2
            )

    def render_board(self):
        """Classic symmetric premium grid with an original-drawn green frame."""
        self.panel((23, 95, 660, 660), (43, 79, 61))
        pygame.draw.rect(self.surface, (167, 151, 103), (31, 103, 644, 644), 1)
        premium_words = {
            1: ("DOUBLE", "LETTER", "SCORE"),
            2: ("TRIPLE", "LETTER", "SCORE"),
            3: ("DOUBLE", "WORD", "SCORE"),
            4: ("TRIPLE", "WORD", "SCORE"),
        }
        for pos, rect in self.cells.items():
            premium = PREMIUMS.get(pos)
            color = PREMIUM_COLORS.get(premium, (211, 219, 189))
            pygame.draw.rect(self.surface, color, rect.inflate(-1, -1))
            placed = self.game.board.get(pos)
            if self.animation is not None:
                index = next(
                    (
                        n
                        for n, item in enumerate(self.animation.items)
                        if item["position"] == pos
                    ),
                    None,
                )
                if index is not None and not self.animation.landed(index):
                    placed = None
            draft = pos in self.pending
            if not placed and not draft:
                if pos == (7, 7):
                    self.star(rect.center, 13)
                elif premium:
                    ink = INK if premium in (1, 3) else WHITE
                    for line, word in enumerate(premium_words[premium]):
                        image = self.font(8).render(word, True, ink)
                        self.surface.blit(
                            image,
                            (
                                rect.centerx - image.get_width() // 2,
                                rect.y + 5 + line * 10,
                            ),
                        )
            if placed:
                self.tile(rect, placed.letter, placed.value, blank=placed.blank)
            elif draft and not (
                self.drag and self.drag["active"] and self.drag["board"] == pos
            ):
                index, letter = self.pending[pos]
                tile = self.game.players[self.game.current].rack[index]
                self.tile(
                    rect,
                    letter,
                    tile.value,
                    selected=True,
                    blank=tile.blank,
                    pending=True,
                )
            if pos in self.game.last_move and placed:
                pygame.draw.rect(
                    self.surface,
                    (30, 105, 77),
                    rect.inflate(-4, -4),
                    2,
                    border_radius=3,
                )
        for n in range(15):
            self.fit(str(n + 1), (38 + n * 42, 76, 42, 20), 11, MUTED)
            self.fit(chr(65 + n), (6, 110 + n * 42, 25, 42), 11, MUTED)
        self.fit(
            "DL · Double letter    TL · Triple letter    DW · Double word    TW · Triple word",
            (34, 757, 635, 23),
            12,
            MUTED,
        )

    def render_game(self):
        """Public score panel; private rack is drawn only after human handoff."""
        game = self.game
        self.render_board()
        display_player = self.animation.player if self.animation else game.current
        player = game.players[display_player]
        self.panel((700, 110, 450, 105))
        status = "GAME COMPLETE" if game.phase == "gameover" else "CURRENT TURN"
        self.text("PLAYING TILES" if self.animation else status, 720, 126, 13, MUTED)
        self.fit(player.name, (720, 153, 410, 34), 27, GOLD)
        self.text(
            "Tiles arrive one at a time…"
            if self.animation
            else "Searching for a legal move…"
            if self.future
            else "Select tiles to return, then confirm"
            if self.exchange_mode
            else "Choose a tile, then a square",
            720,
            194,
            15,
            MUTED,
        )
        for i, p in enumerate(game.players):
            y = 235 + i * 54
            self.panel(
                (700, y, 450, 46), (34, 65, 65) if i == display_player else PANEL
            )
            if i == display_player:
                pygame.draw.rect(
                    self.surface, GOLD, (701, y + 7, 3, 32), border_radius=1
                )
            self.fit(p.name, (716, y + 3, 260, 23), 18)
            self.fit(
                "Computer" if p.is_ai else "Human", (716, y + 27, 260, 16), 11, MUTED
            )
            self.fit(f"{p.score} pts", (995, y + 8, 135, 30), 22, GOLD)
        self.panel((700, 454, 450, 43), (30, 50, 51))
        self.text(
            f"Bag: {len(game.bag)} tiles    Scoreless turns: {game.scoreless_turns}/6",
            705,
            466,
            16,
            MUTED,
        )
        result, error = self.preview()
        active = self.human_active()
        self.button(
            (700, 510, 218, 44),
            f"Play · {result.score} pts" if result else "Play word",
            "play",
            active and result is not None and not self.exchange_mode,
            reason=error
            or (
                "Select and place tiles for a valid word first."
                if active
                else "Wait for the active human turn."
            ),
        )
        self.button((932, 510, 218, 44), "Recall draft", "recall", active)
        self.button((700, 566, 218, 44), "Pass turn", "pass", active)
        exchange_label = (
            f"Confirm exchange ({len(self.exchange_selected)})"
            if self.exchange_mode
            else "Exchange tiles"
        )
        self.button(
            (932, 566, 218, 44),
            exchange_label,
            "exchange",
            active and len(game.bag) >= 7,
            reason="Exchange requires at least seven tiles in the bag."
            if len(game.bag) < 7
            else "Wait for the active human turn.",
        )
        self.button((700, 622, 218, 44), "Shuffle rack", "shuffle", active)
        self.button((932, 622, 218, 44), "Find a hint", "hint", active)
        self.button((700, 682, 142, 40), "New game", "new")
        self.button((854, 682, 142, 40), "Game log", "turn_log")
        self.button((1008, 682, 142, 40), "Help · F1", "help_button")
        self.panel((700, 735, 450, 91))
        if game.phase == "gameover":
            self.text("FINAL RESULT", 716, 745, 11, GOLD)
            self.fit(
                "Winner: " + ", ".join(game.players[i].name for i in game.winner),
                (716, 768, 416, 36),
                23,
                GOLD,
            )
        elif error:
            self.text("CHECK YOUR DRAFT", 716, 745, 11, (240, 174, 139))
            self.wrap(error, (716, 766, 416, 52), 16, (240, 174, 139))
        elif result:
            self.text(f"VALID DRAFT  ·  {result.score} points", 716, 742, 12, GOLD)
            summary = " + ".join(str(score) for word, score in result.words)
            if result.bingo:
                summary += f" + {result.bingo} bonus"
            self.fit(f"{summary} = {result.score}", (716, 759, 416, 20), 13, MUTED)
            self.button(
                (716, 784, 416, 33),
                "Show step-by-step calculation",
                "score_details",
                active,
            )
        else:
            self.text("MOVE PREVIEW", 716, 745, 11, MUTED)
            self.wrap(
                "Place tiles to see word-by-word scoring before you commit.",
                (716, 766, 416, 52),
                16,
                MUTED,
            )
        reveal = not player.is_ai and self.rack_revealed and game.phase == "play"
        self.text("YOUR RACK" if reveal else "RACK HIDDEN", 30, 803, 12, GOLD)
        # A physical-looking rack supports the seven square tiles. Grain lines
        # are decorative primitives, not a copied wood texture.
        pygame.draw.rect(
            self.surface, (112, 76, 43), (143, 789, 475, 64), border_radius=7
        )
        for y in (795, 839):
            pygame.draw.line(self.surface, (151, 108, 61), (148, y), (612, y), 1)
        pygame.draw.rect(
            self.surface, (171, 124, 68), (139, 843, 483, 11), border_radius=3
        )
        if reveal:
            used = {index for index, letter in self.pending.values()}
            for i, tile in enumerate(player.rack):
                rect = self.rack_rects[i]
                if i in used:
                    pygame.draw.rect(self.surface, (36, 55, 56), rect, border_radius=6)
                    continue
                if (
                    self.drag
                    and self.drag["active"]
                    and self.drag["source"] == "rack"
                    and self.drag["index"] == i
                ):
                    continue
                chosen = i == self.selected or i in self.exchange_selected
                self.tile(rect, tile.letter, tile.value, chosen, tile.blank)
                self.buttons.append((rect, f"rack:{i}"))
        else:
            self.fit(
                "Tiles are private until the next human is ready.",
                (155, 801, 450, 35),
                16,
                MUTED,
            )
        self.panel((30, 880, 1120, 35))
        self.fit(self.last_play_text(), (44, 885, 1092, 25), 16, GOLD)

    def inspect_word(self, cell):
        """Collect both complete words at an intersection; never reveal racks."""
        words = []
        for direction in ((0, 1), (1, 0)):
            cells = self.game._word(self.game.board, cell, direction)
            if len(cells) > 1:
                word = "".join(self.game.board[pos].letter for pos in cells)
                if word not in words:
                    words.append(word)
        if words:
            self.drag = None
            self.inspected_words = words
            self.word_index = 0
            self.definition_page = 0
            self.modal = "word"
            self.request_definition()

    def request_definition(self):
        """Fetch local data automatically; no consent/network step is needed."""
        word = self.inspected_words[self.word_index]
        if word not in self.definition_jobs and word not in self.definition_cache:
            self.definition_jobs[word] = self.definition_executor.submit(lookup, word)

    def last_play_text(self):
        """Use structured public history, not a journal line that may change."""
        game = self.game
        if game.last_play is None:
            latest = game.last_turn
            return (
                f"Last turn: {game.players[latest['player']].name} {latest['action']}. No word played yet."
                if latest
                else "Last play: no word played yet."
            )
        play = game.last_play
        words = ", ".join(f"{word} ({score})" for word, score in play["words"])
        message = f"Last play: {game.players[play['player']].name} — {words} = {play['score']} points"
        if play["bingo"]:
            message += f" (includes {play['bingo']}-point bonus)"
        if game.last_turn and game.last_turn["action"] != "played":
            turn = game.last_turn
            message += (
                f" · Latest turn: {game.players[turn['player']].name} {turn['action']}"
            )
        return message

    def render_word_details(self):
        """Show sourced meanings automatically from the local definition index."""
        word = self.inspected_words[self.word_index]
        self.text(word, 185, 205, 36, GOLD)
        self.text(
            "Board word · CC0 gameplay list, not an official Scrabble dictionary",
            185,
            257,
            16,
            MUTED,
        )
        self.button(
            (185, 293, 350, 40),
            "Other crossing word",
            "inspect_next",
            len(self.inspected_words) > 1,
        )
        self.button((808, 202, 185, 42), "Close", "close")
        result = self.definition_cache.get(word)
        if result is None:
            self.wrap(
                "Loading the local offline dictionary… No network request is made.",
                (185, 363, 790, 150),
                22,
            )
        else:
            self.text(result["status"], 185, 354, 18, MUTED)
            entries = result["entries"]
            if entries:
                self.definition_page %= len(entries)
                entry = entries[self.definition_page]
                self.wrap(
                    entry["part"] + " — " + entry["text"], (185, 395, 790, 170), 23
                )
                licence = entry["license"]
                attribution = (
                    "Source: "
                    + ", ".join(entry["sources"])
                    + "\nLicence: "
                    + str(licence.get("name", "not supplied"))
                    + " "
                    + str(licence.get("url", ""))
                )
                self.wrap(attribution, (185, 572, 790, 64), 12, MUTED)
                self.button(
                    (185, 657, 790, 42),
                    f"Definition {self.definition_page + 1}/{len(entries)} · next",
                    "definition_next",
                    len(entries) > 1,
                )
            else:
                self.wrap(
                    "The word remains valid in the selected gameplay list, but this offline extract has no sourced meaning for it. No definition is invented.",
                    (185, 402, 790, 160),
                    23,
                )

    def render_score_details(self):
        """Use the scorer's own arithmetic trace, never a second UI calculator."""
        result, error = self.preview()
        self.text("How your move scores", 185, 205, 31, GOLD)
        self.button((808, 202, 185, 42), "Close", "close")
        if result is None:
            self.wrap(error or "Place a valid draft first.", (185, 320, 790, 180), 23)
            return
        part = result.breakdown[self.score_page % len(result.breakdown)]
        self.text(f"{part['word']} · {part['score']} points", 185, 287, 27)
        terms = " + ".join(part["terms"])
        bonuses = ", ".join(part["word_bonuses"]) or "No new word premium"
        calculation = (
            terms
            + f"\n\nLetter subtotal = {part['subtotal']}\n"
            + bonuses
            + f"\n{part['subtotal']} × {part['multiplier']} = {part['score']}"
        )
        self.wrap(calculation, (185, 337, 790, 218), 22)
        total = " + ".join(str(score) for word, score in result.words)
        self.wrap(
            f"All words: {total}\nSeven-tile bonus: {result.bingo}\nMOVE TOTAL: {result.score}",
            (185, 565, 790, 92),
            21,
            GOLD,
        )
        self.button(
            (185, 665, 790, 42),
            f"Word {self.score_page + 1}/{len(result.breakdown)} · next calculation",
            "score_next",
            len(result.breakdown) > 1,
        )

    def log_entries(self):
        """Filter public completed turns without modifying the engine's history."""
        return [
            entry
            for entry in self.game.turn_history
            if self.log_filter is None or entry["player"] == self.log_filter
        ]

    def render_turn_log(self):
        """Four roomy rows per page keep crosswords legible on a long game."""
        self.text("Game log", 185, 195, 31, GOLD)
        self.button((850, 195, 145, 40), "Close", "close")
        filters = [("All players", "all")] + [
            (p.name, str(i)) for i, p in enumerate(self.game.players)
        ]
        width = 800 // len(filters)
        for i, (label, value) in enumerate(filters):
            chosen = (value == "all" and self.log_filter is None) or str(
                self.log_filter
            ) == value
            self.button(
                (185 + i * width, 251, width - 6, 37),
                ("• " if chosen else "") + label,
                "log_filter:" + value,
            )
        entries = self.log_entries()
        last = max(0, (len(entries) - 1) // 4)
        self.log_page = min(self.log_page, last)
        if not entries:
            self.text("No completed turns yet.", 195, 350, 22, MUTED)
        for row, entry in enumerate(entries[self.log_page * 4 : self.log_page * 4 + 4]):
            y = 304 + row * 77
            self.panel((185, y, 810, 70))
            name = self.game.players[entry["player"]].name
            self.fit(f"Turn {entry['turn']} · {name}", (197, y + 4, 530, 23), 18, GOLD)
            self.fit(
                f"+{entry['score']} pts · total {entry['total']}",
                (735, y + 4, 245, 23),
                17,
            )
            words = ", ".join(f"{word} ({score})" for word, score in entry["words"])
            if entry["bingo"]:
                words += f" + {entry['bingo']} seven-tile bonus"
            self.wrap(words or entry["action"].capitalize(), (197, y + 29, 780, 37), 14)
        self.fit(
            f"Page {self.log_page + 1} / {last + 1} · {len(entries)} turns",
            (380, 623, 420, 25),
            16,
            MUTED,
        )
        self.button((185, 621, 175, 36), "Previous", "log_previous", self.log_page > 0)
        self.button((820, 621, 175, 36), "Next", "log_next", self.log_page < last)
        self.wrap(
            "Turn totals exclude final rack deductions. Final scores: "
            + ", ".join(f"{p.name} {p.score}" for p in self.game.players)
            if self.game.phase == "gameover"
            else "Public completed turns only · mouse wheel or arrow keys changes page.",
            (185, 670, 810, 45),
            14,
            MUTED,
        )

    def render_modal(self):
        """Modal controls replace all background click targets, not just cover them."""
        self.buttons.clear()
        self.disabled.clear()
        self.disabled_reasons.clear()
        shade = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        self.surface.blit(shade, (0, 0))
        self.panel((140, 170, 900, 570))
        if self.modal in ("save", "load"):
            self.render_save_dialog()
        elif self.modal == "log":
            self.render_turn_log()
        elif self.modal == "name":
            self.text(
                f"Name human player · seat {self.editing_name + 1}", 185, 220, 31, GOLD
            )
            self.text(
                "Type a name (1–20 characters). Enter saves; Escape cancels.",
                185,
                290,
                20,
                MUTED,
            )
            self.panel((185, 355, 790, 75), (38, 63, 65))
            self.fit(
                self.name_draft or "Enter a name…",
                (205, 371, 750, 42),
                30,
                GOLD if self.name_select_all else WHITE,
            )
            self.text(
                "Current text selected — typing replaces it."
                if self.name_select_all
                else f"{len(self.name_draft)}/20 characters · Ctrl/Cmd+A selects all",
                185,
                457,
                17,
                MUTED,
            )
            self.button((185, 570, 380, 60), "Cancel", "close")
            self.button((595, 570, 380, 60), "Save name", "name_save")
        elif self.modal == "word":
            self.render_word_details()
        elif self.modal == "score":
            self.render_score_details()
        elif self.modal == "handoff":
            name = self.game.players[self.game.current].name
            self.text("Pass the screen", 190, 230, 36, GOLD)
            self.wrap(
                f"{name}, your private rack is ready. Other players should look away.",
                (190, 310, 790, 140),
                25,
            )
            self.button((190, 540, 790, 65), f"I am {name} · show my rack", "ready")
        elif self.modal in ("quit", "quit_handoff", "new", "pass"):
            title = {
                "quit": "Close Scrabble?",
                "quit_handoff": "Close Scrabble?",
                "new": "Start a new game?",
                "pass": "Pass this turn?",
            }[self.modal]
            self.text(title, 190, 235, 34, GOLD)
            detail = (
                "Unsaved play will be lost."
                if self.modal in ("quit", "quit_handoff", "new")
                else "Your draft will be recalled. Passing counts as a scoreless turn."
            )
            self.wrap(detail, (190, 320, 790, 120), 24)
            cancel = "return_handoff" if self.modal == "quit_handoff" else "close"
            confirm = (
                "new_confirm"
                if self.modal == "new"
                else "pass_confirm"
                if self.modal == "pass"
                else "quit_confirm"
            )
            self.button((190, 550, 370, 60), "Keep playing", cancel)
            self.button((590, 550, 390, 60), "Confirm", confirm)
        elif self.modal == "blank":
            self.text("Choose the blank’s letter", 185, 215, 32, GOLD)
            self.text(
                "It keeps that letter permanently and always scores zero.",
                185,
                275,
                19,
                MUTED,
            )
            for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
                self.button(
                    (190 + (i % 9) * 86, 335 + (i // 9) * 73, 70, 57),
                    letter,
                    "blank:" + letter,
                )
        elif self.modal == "help":
            self.text("How to play", 185, 210, 32, GOLD)
            self.wrap(
                "Click a rack tile then a square, or drag it onto the board. Drag rack tiles to reorder; drag draft tiles to move, swap or return them to the rack. Committed tiles stay fixed. Blank tiles ask for a letter.\n\nThe first word must cover the star. New tiles lie in one row or column, without gaps. All formed words must be in the chosen dictionary.\n\nPlay commits the scored preview; Recall changes nothing. Exchange requires at least seven tiles in the bag. Pass needs confirmation.\n\nThe app automatically rejects invalid words; there is no challenge penalty. Six scoreless turns end play. F1 or Escape closes this help. No saves: quit asks first.",
                (185, 270, 790, 340),
                20,
            )
            self.button((185, 652, 790, 45), "Return to game", "close")

    def render_save_dialog(self):
        """Explicit confirmations prevent overwriting a save or a live game."""
        saving = self.modal == "save"
        self.text(
            "Save this game?" if saving else "Load saved game?", 185, 220, 32, GOLD
        )
        detail = (
            "Save the committed board, scores, racks, bag and turn log. Any existing save will be replaced. Unplayed draft tiles are not saved."
            if saving
            else "Replace the current game with the saved game. Unsaved changes and drafts will be lost. The saved dictionary must match the current one."
        )
        self.wrap(detail, (185, 300, 800, 145), 22)
        self.wrap("Local file: " + str(self.save_path), (185, 455, 800, 70), 15, MUTED)
        self.wrap(
            "Privacy: this plain-text file includes every private rack and the bag. Do not share it during a game.",
            (185, 535, 800, 70),
            18,
            GOLD,
        )
        self.button((185, 640, 380, 50), "Cancel", "close")
        self.button(
            (595, 640, 390, 50),
            "Save game" if saving else "Load game",
            "save_confirm" if saving else "load_confirm",
        )

    def render(self):
        """Letterbox a fixed logical surface and use that same scale for input."""
        self.surface.fill(BG)
        self.buttons.clear()
        self.disabled.clear()
        self.disabled_reasons.clear()
        self.text("Scrabble", 30, 25, 40, GOLD)
        self.fit("CLASSIC ENGLISH  /  LOCAL TABLE", (700, 17, 450, 22), 13, MUTED)
        self.button(
            (854, 48, 142, 35),
            "Save game",
            "save",
            self.game is not None,
            reason="Start a game before saving.",
        )
        self.button((1008, 48, 142, 35), "Load game", "load")
        if self.game:
            self.render_game()
        else:
            self.text("Make room for a good word.", 95, 160, 38)
            self.text(
                "Choose 2–4 seats. Click a seat to change its controller.",
                95,
                230,
                22,
                MUTED,
            )
            for i, mode in enumerate(self.modes):
                self.button(
                    (95 + (i % 2) * 510, 320 + (i // 2) * 160, 470, 65),
                    f"Seat {i + 1} · {mode}",
                    f"seat:{i}",
                )
                if mode == "Human":
                    self.button(
                        (95 + (i % 2) * 510, 393 + (i // 2) * 160, 470, 38),
                        f"{self.human_names[i]} · edit name",
                        f"name:{i}",
                    )
            count = sum(mode != "Off" for mode in self.modes)
            self.button(
                (95, 670, 980, 65), f"Start game · {count} players", "start", count >= 2
            )
            self.fit(
                f"Dictionary: {self.lexicon.label} · {len(self.lexicon.words):,} words",
                (95, 780, 980, 30),
                18,
                MUTED,
            )
        self.render_drag()
        self.render_flight()
        if self.modal:
            self.render_modal()
        mouse = (
            (pygame.mouse.get_pos()[0] - self.offset[0]) / self.scale,
            (pygame.mouse.get_pos()[1] - self.offset[1]) / self.scale,
        )
        reason = next(
            (
                message
                for rect, message in self.disabled_reasons
                if rect.collidepoint(mouse)
            ),
            None,
        )
        if reason or self.notice:
            self.fit(reason or self.notice, (30, 855, 1120, 21), 14, GOLD)
        width, height = self.screen.get_size()
        self.scale = min(width / self.WIDTH, height / self.HEIGHT)
        size = round(self.WIDTH * self.scale), round(self.HEIGHT * self.scale)
        self.offset = ((width - size[0]) // 2, (height - size[1]) // 2)
        self.screen.fill((8, 15, 19))
        self.screen.blit(pygame.transform.smoothscale(self.surface, size), self.offset)
        pygame.display.flip()

    def run(self, frames=0):
        """Never block on AI results; limited test runs also clean up the worker."""
        count = 0
        try:
            while self.running:
                for event in pygame.event.get():
                    self.event(event)
                self.update()
                self.render()
                count += 1
                if frames and count >= frames:
                    break
                self.clock.tick(60)
        finally:
            self.executor.shutdown(wait=True, cancel_futures=True)
            self.definition_executor.shutdown(wait=True, cancel_futures=True)
            pygame.quit()
