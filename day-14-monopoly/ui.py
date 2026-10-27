"""Pygame presentation: original vector board, ordinary buttons, no game rules.

All coordinates are logical pixels. The final surface is scaled into the window,
so hit testing must undo the same transformation. Keeping one rectangle per
square makes the drawing and mouse mapping agree at every window size.
"""
import io
from pathlib import Path
import pygame
from data import BOARD, TAX_AMOUNTS, GO_SALARY
from ai import accept_trade
from icons import icon_kind, draw_icon

BACKGROUND = (14, 23, 35)
PAPER = (242, 237, 223)
INK = (35, 48, 54)
GOLD = (226, 193, 128)
WHITE = (236, 242, 246)
MUTED = (164, 181, 199)
COLORS = [(239, 109, 106), (82, 186, 238), (238, 195, 72),
          (178, 135, 237), (90, 211, 148), (239, 145, 73)]
GROUPS = {'brown': (140, 82, 50), 'light_blue': (115, 202, 229),
          'pink': (209, 93, 157), 'orange': (240, 153, 54),
          'red': (212, 65, 61), 'yellow': (240, 219, 71),
          'green': (63, 153, 91), 'blue': (47, 90, 178)}


class GameUI:
    """Render the state and return commands; never implement rent or dice here."""
    WIDTH, HEIGHT = 1320, 940

    def __init__(self, width=1320, height=940):
        pygame.init()
        self.display = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption('Day 14 · Monopoly · Classic British Edition')
        self.surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.fonts = {}
        self.buttons = []
        # Disabled buttons are drawn but never registered as click targets.
        # Keep their rectangles separately so clicks cannot fall through.
        self.disabled_buttons = []
        self.disabled_targets = []
        self.button_states = {}
        self.button_reasons = {}
        self.holdings_player = None
        self.holdings_page = 0
        self.inspected_deck = 'chance'
        self.square_rects = self._board_rects()
        self.selected = None
        self.scroll = 0
        self.modes = ['Human', 'Computer', 'Off', 'Off', 'Off', 'Off']
        self.modal = None
        self.notice = ''
        self.help = False
        self.trade_state = None
        self.scale = 1
        self.offset = (0, 0)

    def _board_rects(self):
        """Large corner spaces and rectangular streets mimic a physical board.

        Two 95-pixel corners plus nine 62-pixel streets make a 748-pixel side.
        A shared rectangle map is the single source for drawing and hit tests.
        """
        x, y, side, corner, step = 24, 96, 748, 95, 62
        result = {
            0: pygame.Rect(x + side - corner, y + side - corner, corner, corner),
            10: pygame.Rect(x, y + side - corner, corner, corner),
            20: pygame.Rect(x, y, corner, corner),
            30: pygame.Rect(x + side - corner, y, corner, corner),
        }
        for n in range(1, 10):
            result[n] = pygame.Rect(x + side - corner - n * step, y + side - corner, step, corner)
            result[10 + n] = pygame.Rect(x, y + side - corner - n * step, corner, step)
            result[20 + n] = pygame.Rect(x + corner + (n - 1) * step, y, step, corner)
            result[30 + n] = pygame.Rect(x + side - corner, y + corner + (n - 1) * step, corner, step)
        return result

    def font(self, size):
        """Use installed UI fonts; bundle no font files and retain a fallback.

        Segoe/Arial/DejaVu are platform preferences, not hard dependencies.
        Cached font objects avoid repeated system-font lookups during drawing.
        """
        if size not in self.fonts:
            path = pygame.font.match_font('segoeui,arial,dejavusans,helveticaneue')
            fallback = Path(pygame.__file__).parent / pygame.font.get_default_font()
            try:
                font_data = Path(path).read_bytes() if path else fallback.read_bytes()
            except OSError:
                font_data = fallback.read_bytes()
            # SDL_ttf can retain its source stream for the font's lifetime.
            # BytesIO avoids holding an OS file descriptor per font/size/UI,
            # especially in repeated tests and after many fitted text sizes.
            self.fonts[size] = pygame.font.Font(io.BytesIO(font_data), size)
        return self.fonts[size]

    def panel(self, rect, fill=(23, 36, 51), border=(43, 59, 77), radius=14):
        """One reusable surface treatment keeps cards visually consistent."""
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.surface, (8, 15, 24), rect.move(0, 4), border_radius=radius)
        pygame.draw.rect(self.surface, fill, rect, border_radius=radius)
        pygame.draw.rect(self.surface, border, rect, 1, border_radius=radius)

    def fit_text(self, message, rect, size=20, color=WHITE, minimum=12):
        """Shrink one-line labels to fit; never silently crop property names."""
        rect = pygame.Rect(rect)
        while size > minimum and self.font(size).size(str(message))[0] > rect.width:
            size -= 1
        image = self.font(size).render(str(message), True, color)
        self.surface.blit(image, (rect.x, rect.centery - image.get_height() // 2))

    def dice(self, value, x, y, size=62):
        """Original vector dice use pips, so the latest roll reads at a glance."""
        rect = pygame.Rect(x, y, size, size)
        self.panel(rect, PAPER, (207, 198, 177), 12)
        patterns = {0: [], 1: [(1, 1)], 2: [(0, 0), (2, 2)],
                    3: [(0, 0), (1, 1), (2, 2)],
                    4: [(0, 0), (0, 2), (2, 0), (2, 2)],
                    5: [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
                    6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]}
        for px, py in patterns.get(value, []):
            pygame.draw.circle(self.surface, INK,
                               (x + size // 4 + px * size // 4,
                                y + size // 4 + py * size // 4), max(3, size // 13))

    def text(self, message, x, y, size=22, color=WHITE):
        """Draw one line; wrapping is a separate, reusable operation."""
        image = self.font(size).render(str(message), True, color)
        self.surface.blit(image, (x, y))

    def wrap(self, message, rect, size=20, color=WHITE):
        """Wrap words and split unusually long words rather than cutting them."""
        rect = pygame.Rect(rect)
        old_clip = self.surface.get_clip()
        self.surface.set_clip(rect.clip(old_clip))
        y = rect.y
        line_height = self.font(size).get_linesize()
        for paragraph in str(message).split('\n'):
            line = ''
            words = []
            for word in paragraph.split():
                while self.font(size).size(word)[0] > rect.width and len(word) > 1:
                    cut = len(word) - 1
                    while cut > 1 and self.font(size).size(word[:cut] + '-')[0] > rect.width:
                        cut -= 1
                    words.append(word[:cut] + '-')
                    word = word[cut:]
                words.append(word)
            for word in words:
                trial = (line + ' ' + word).strip()
                if self.font(size).size(trial)[0] > rect.width and line:
                    self.text(line, rect.x, y, size, color)
                    y += line_height
                    line = word
                else:
                    line = trial
            self.text(line, rect.x, y, size, color)
            y += line_height
        self.surface.set_clip(old_clip)
        return y

    def button(self, rect, label, command, color=(44, 66, 79),
               enabled=True, action=False, selected=False, suggested=False, reason=None):
        """Draw state explicitly, and register ONLY enabled controls for input.

        A bright outline and READY label mean an action can be clicked now.
        Disabled controls have a muted palette and LOCKED label. Text reinforces
        colour so availability is understandable without colour discrimination.
        """
        rect = pygame.Rect(rect)
        self.button_states[command] = enabled
        # Availability has exactly one visual treatment. A suggestion is a
        # separate text annotation, never a darker/lighter enabled button.
        fill = (31, 86, 72) if action and enabled else color
        self.button_reasons[command] = reason if not enabled else None
        if not enabled:
            fill = (31, 40, 48)
        pygame.draw.rect(self.surface, fill, rect, border_radius=7)
        if action or selected:
            border = GOLD if selected else ((101, 218, 165) if enabled else (71, 83, 92))
            pygame.draw.rect(self.surface, border, rect, 2, border_radius=7)
        size = 26 if rect.height >= 90 else 16
        content = rect.inflate(-14, -8)
        if action:
            # Reserve a fixed status column: long action labels never overlap it.
            content.width -= 104
            state = 'SUGGESTED' if enabled and suggested else 'READY' if enabled else 'LOCKED'
            self.text(state, rect.right - 100,
                      rect.centery - 8, 12, (158, 242, 195) if enabled else MUTED)
        if rect.height <= 46:
            self.fit_text(label, content, size, WHITE if enabled else MUTED)
        else:
            self.wrap(label, content, size, WHITE if enabled else MUTED)
        mouse = self.point(pygame.mouse.get_pos())
        if enabled and rect.collidepoint(mouse) and pygame.mouse.get_focused():
            pygame.draw.rect(self.surface, (147, 191, 205), rect, 2, border_radius=7)
            if pygame.mouse.get_pressed()[0]:
                pygame.draw.rect(self.surface, GOLD, rect.inflate(-4, -4), 2, border_radius=5)
        if enabled:
            self.buttons.append((rect, command))
        else:
            self.disabled_buttons.append(rect)
            self.disabled_targets.append((rect, command))

    def point(self, pos):
        """Convert physical mouse pixels into the logical drawing coordinates."""
        return ((pos[0] - self.offset[0]) / self.scale,
                (pos[1] - self.offset[1]) / self.scale)

    def command_at(self, pos):
        """Return the topmost drawn button command, or None."""
        logical = self.point(pos)
        for rect, command in reversed(self.buttons):
            if rect.collidepoint(logical):
                return command
        if any(rect.collidepoint(logical) for rect in self.disabled_buttons):
            # Clicking an unavailable action explains it instead of silently
            # ignoring the user. It still never reaches the game controller.
            for rect, command in self.disabled_targets:
                if rect.collidepoint(logical):
                    self.notice = self.button_reasons.get(command) or 'This control is unavailable now.'
                    break
            return None
        if self.modal is None:
            for index, rect in self.square_rects.items():
                if rect.collidepoint(logical):
                    self.selected = index
                    return None
        return None

    def start_trade(self, game):
        """Start a fresh proposal, never transferring a deed merely by opening."""
        choices = [i for i, p in enumerate(game.players) if i != game.actor and not p.bankrupt]
        if not choices:
            return
        self.trade_state = {'proposer': game.actor, 'other': choices[0],
                            'give': set(), 'take': set(), 'offer': 0,
                            'request': 0, 'give_card': False, 'take_card': False,
                            'page': 0}
        self.modal = 'trade'

    def trade_args(self):
        """One argument tuple is used for validation, AI consent and execution."""
        t = self.trade_state
        return (t['proposer'], t['other'], sorted(t['give']), sorted(t['take']),
                t['offer'], t['request'], t['give_card'], t['take_card'])

    def handle_local(self, command, game):
        """Handle presentation-only commands; return True when consumed."""
        if command == 'details_close':
            self.selected = None
            return True
        if command == 'close':
            self.modal = None
            return True
        if command.startswith('deck:'):
            self.inspected_deck = command.split(':')[1]
            self.modal = 'deck'
            return True
        if command == 'journal':
            self.modal = 'journal'
            return True
        if command.startswith('player:'):
            self.holdings_player = int(command.split(':')[1])
            self.holdings_page = 0
            self.modal = 'holdings'
            return True
        if command == 'holdings_page':
            self.holdings_page = 1 - self.holdings_page
            return True
        if command == 'trade':
            actor = game.players[game.actor]
            if game.phase in ('roll', 'end', 'debt') and not actor.is_ai:
                self.start_trade(game)
            return True
        if command == 'trade_submit':
            other = game.players[self.trade_state['other']]
            if other.is_ai:
                if accept_trade(game, *self.trade_args()):
                    self._finish_trade(game)
                else:
                    self.notice = f'{other.name} declines that proposal.'
            else:
                self.modal = 'consent'
            return True
        if command == 'trade_accept':
            self._finish_trade(game)
            return True
        if command == 'trade_reject':
            self.notice = 'Trade declined. No money, deeds or cards changed hands.'
            self.modal = None
            return True
        if command.startswith('trade_'):
            t = self.trade_state
            key, _, value = command[6:].partition(':')
            if key == 'other':
                choices = [i for i, p in enumerate(game.players) if i != t['proposer'] and not p.bankrupt]
                t['other'] = choices[(choices.index(t['other']) + 1) % len(choices)]
                t['take'].clear()
                t['request'] = 0
                t['take_card'] = False
            elif key in ('give', 'take'):
                index = int(value)
                if index in t[key]:
                    t[key].remove(index)
                else:
                    t[key].add(index)
            elif key in ('offer', 'request'):
                t[key] = max(0, t[key] + int(value))
            elif key in ('give_card', 'take_card'):
                t[key] = not t[key]
            elif key == 'page':
                t['page'] = (t['page'] + 1) % 2
            return True
        return False

    def _finish_trade(self, game):
        """Ask the engine to commit only after the recipient explicitly agrees."""
        success = game.trade(*self.trade_args())
        self.notice = 'Trade completed.' if success else 'Trade invalid: check cash, ownership, buildings and interest.'
        if success:
            self.modal = None
        else:
            self.modal = 'trade'

    def _setup(self):
        """A calm lobby gives seat choices a clear selected state and summary."""
        self.text('THE LONDON COLLECTION', 84, 72, 16, GOLD)
        self.text('Monopoly', 80, 110, 64)
        self.text('An evening of strategy. A table for everyone.', 84, 205, 25, MUTED)
        self.panel((84, 275, 1150, 430))
        self.text('01   BUILD YOUR TABLE', 110, 298, 17, GOLD)
        self.text('Click a seat to switch between Human, Computer and Off.', 110, 333, 19, MUTED)
        for i, mode in enumerate(self.modes):
            x, y = 110 + (i % 3) * 370, 395 + (i // 3) * 135
            active = mode != 'Off'
            self.button((x, y, 345, 110), f'SEAT {i + 1}\n{mode}', f'seat:{i}',
                        (34, 65, 69) if active else (30, 41, 55), selected=active)
            pygame.draw.circle(self.surface, COLORS[i] if active else (80, 91, 104), (x + 315, y + 25), 7)
        count = sum(mode != 'Off' for mode in self.modes)
        self.text(f'{count} seats selected  /  2–6 players  /  local hot-seat', 84, 755, 20, MUTED)
        self.button((854, 742, 380, 62), f'Begin game · {count} players', 'start',
                    (37, 105, 88), action=True)
        self.text('CLASSIC BRITISH EDITION', 84, 852, 16, GOLD)
        self.text('No Speed Die. No Free Parking jackpot. Just the classic game.', 84, 885, 18, MUTED)

    def _board(self, game):
        """An ivory board with functional colour bands, ownership and tokens."""
        self.panel((16, 88, 764, 764), (83, 73, 55), (147, 126, 88), 14)
        pygame.draw.rect(self.surface, PAPER, (24, 96, 748, 748), border_radius=8)
        pygame.draw.rect(self.surface, (229, 228, 213), (119, 191, 558, 558))
        pygame.draw.rect(self.surface, (201, 203, 183), (130, 202, 536, 536), 1, border_radius=10)
        for i, rect in self.square_rects.items():
            square = BOARD[i]
            tile = rect.inflate(-2, -2)
            fill = (248, 244, 233) if i not in (0, 10, 20, 30) else (228, 224, 207)
            pygame.draw.rect(self.surface, fill, tile)
            color = GROUPS.get(square.group)
            top_bottom = rect.height > rect.width
            if color:
                if top_bottom:
                    pygame.draw.rect(self.surface, color, (tile.x, tile.y, tile.width, 13))
                else:
                    pygame.draw.rect(self.surface, color, (tile.x, tile.y, 8, tile.height))
            left = 6 if top_bottom or not color else 13
            label = pygame.Rect(rect.x + left, rect.y + (19 if top_bottom else 5), rect.width - left - 5,
                                53 if top_bottom else 39)
            symbol = icon_kind(i, square.kind)
            if symbol:
                if i in (0, 10, 20, 30):
                    # Corners have room for a larger symbol between title and tokens.
                    label.height = 30
                    icon_rect = pygame.Rect(rect.centerx - 16, rect.y + 32, 32, 32)
                elif top_bottom:
                    label.y = rect.y + 5
                    label.height = 43
                    icon_rect = pygame.Rect(rect.centerx - 11, rect.y + 51, 22, 22)
                else:
                    # Side spaces reserve a right-hand icon gutter, not an overlay.
                    label.width -= 25
                    icon_rect = pygame.Rect(rect.right - 26, rect.y + 8, 22, 22)
                draw_icon(self.surface, symbol, icon_rect)
            size = 11 if top_bottom else (10 if symbol else 12)
            self.wrap(square.name, label, size, INK)
            if square.price:
                self.text(f'£{square.price}', rect.x + left, rect.bottom - 20, 12, INK)
                deed = game.properties[i]
                if deed.owner is not None:
                    pygame.draw.rect(self.surface, COLORS[deed.owner], (rect.x + 3, rect.bottom - 5, rect.width - 6, 3))
                if deed.mortgaged:
                    self.text('M', rect.right - 15, rect.bottom - 21, 12, (153, 56, 57))
                if deed.houses:
                    for n in range(1 if deed.houses == 5 else deed.houses):
                        pygame.draw.rect(self.surface, (164, 53, 52) if deed.houses == 5 else (32, 117, 78),
                                         (rect.x + left + n * 9, rect.y + 3, 7, 7), border_radius=1)
            if i in TAX_AMOUNTS:
                self.fit_text(f'Pay £{TAX_AMOUNTS[i]}',
                              (rect.x + 4, rect.bottom - 20, rect.width - 8, 17), 12, INK)
            elif i == 0:
                self.fit_text(f'Collect £{GO_SALARY}',
                              (rect.x + 4, rect.bottom - 20, rect.width - 8, 17), 11, INK)
            if self.selected == i:
                pygame.draw.rect(self.surface, (58, 130, 119), rect.inflate(-4, -4), 3, border_radius=3)
        # Tokens sit away from title text. Numbers distinguish players in
        # addition to colour, and a contrasting outline keeps tokens legible.
        for i, player in enumerate(game.players):
            if player.bankrupt:
                continue
            rect = self.square_rects[player.position]
            cx = rect.x + 12 + (i % 3) * 17
            cy = rect.bottom - 33 - (i // 3) * 18
            pygame.draw.circle(self.surface, (255, 253, 245), (cx, cy), 10)
            pygame.draw.circle(self.surface, COLORS[i], (cx, cy), 8)
            self.fit_text(str(i + 1), pygame.Rect(cx - 4, cy - 7, 10, 14), 11, INK)
        self.text('L O N D O N', 289, 232, 17, (93, 111, 106))
        self.text('Monopoly', 236, 276, 52, INK)
        self.text('CLASSIC BRITISH EDITION', 254, 343, 14, (78, 98, 91))
        self._card_deck(game, 'chance', pygame.Rect(158, 384, 145, 115))
        self._card_deck(game, 'chest', pygame.Rect(494, 384, 145, 115))
        self.dice(game.dice_values[0], 326, 435, 60)
        self.dice(game.dice_values[1], 404, 435, 60)
        self.fit_text(f'BANK   {game.houses_left} houses    /    {game.hotels_left} hotels',
                      (205, 516, 400, 28), 17, (76, 95, 89))
        if self.selected is not None:
            index = self.selected
            square = BOARD[index]
            self.panel((157, 564, 482, 149), (248, 246, 238), (205, 206, 188), 10)
            pygame.draw.rect(self.surface, GROUPS.get(square.group, (112, 143, 132)), (158, 565, 480, 5))
            # Reserve a separate close target instead of hiding dismissal in
            # a keyboard shortcut or overlapping a long property title.
            self.fit_text(square.name, (176, 582, 345, 28), 23, INK)
            self.button((539, 579, 84, 32), 'Close', 'details_close', (52, 79, 78))
            if square.price:
                deed = game.properties[index]
                owner = 'The bank' if deed.owner is None else game.players[deed.owner].name
                self.fit_text(f'{owner}   ·   price £{square.price}   ·   mortgage £{square.mortgage_value}',
                              (176, 617, 440, 26), 15, INK)
                if square.kind == 'utility':
                    rent = 'Rent: 4× dice / 10× dice when both owned'
                else:
                    rent = 'Rent schedule: ' + ' / '.join(f'£{r}' for r in square.rents)
                self.fit_text(rent, (176, 649, 440, 25), 14, INK)
                self.fit_text('MORTGAGED' if deed.mortgaged else f'Building level {deed.houses} · select actions on the right',
                              (176, 680, 440, 20), 13, INK)
            else:
                self.wrap('A classic board space. Movement and payments resolve automatically.',
                          pygame.Rect(176, 625, 440, 67), 18, INK)
        else:
            self.text('Explore the table', 277, 592, 23, INK)
            self.wrap('Select any board space for its deed.\nSelect a player to browse their collection.',
                      pygame.Rect(210, 636, 400, 70), 17, (75, 97, 90))

    def _card_deck(self, game, deck_name, rect):
        """Show card backs and the most recent public draw, never future order.

        The deck button is inspection only. Drawing must remain a landing effect
        in the engine; clicking a picture cannot give a player a free card.
        """
        is_chance = deck_name == 'chance'
        color = (155, 89, 46) if is_chance else (46, 102, 119)
        title = 'Chance' if is_chance else 'Community Chest'
        for offset in (6, 3):
            pygame.draw.rect(self.surface, (201, 197, 180), rect.move(offset, offset), border_radius=8)
            pygame.draw.rect(self.surface, (169, 166, 150), rect.move(offset, offset), 1, border_radius=8)
        self.button(rect, '', 'deck:' + deck_name, color)
        draw_icon(self.surface, 'chance' if is_chance else 'chest',
                  pygame.Rect(rect.centerx - 19, rect.y + 10, 38, 38))
        self.fit_text(title, (rect.x + 8, rect.y + 54, rect.width - 16, 24), 15)
        self.fit_text('View last card', (rect.x + 8, rect.y + 84, rect.width - 16, 18), 11, (244, 236, 216))

    def _hud(self, game):
        """Current decision, players and legal actions form three clear groups."""
        actor = game.players[game.actor]
        human_can_act = not actor.is_ai and game.phase != 'gameover'
        self.panel((800, 96, 492, 112), (30, 53, 64), (68, 104, 111))
        pygame.draw.circle(self.surface, COLORS[game.actor], (831, 127), 9)
        if game.phase == 'auction' and game.auction is not None:
            # Keep the lot visible for the ENTIRE auction, not just the first
            # journal message. Actor can change while the same lot stays open.
            auction = game.auction
            self.text('PROPERTY AUCTION', 852, 114, 13, MUTED)
            self.fit_text(BOARD[auction['index']].name, (822, 139, 440, 30), 25, GOLD)
            leader = auction['leader']
            highest = ('No bids yet' if leader is None else
                       f'£{auction["high"]} · {game.players[leader].name}')
            self.fit_text(f'Highest bid: {highest}', (822, 171, 440, 18), 14)
            self.fit_text(f'Bidding now: {actor.name}', (822, 190, 440, 16), 13, MUTED)
        else:
            self.text('CURRENT DECISION', 852, 114, 13, MUTED)
            self.fit_text(actor.name, (822, 143, 440, 32), 27)
            phase_names = {'roll': 'Roll the dice', 'buy': 'Purchase or auction',
                           'debt': 'Resolve an outstanding bill', 'end': 'Manage property or end turn',
                           'transfer': 'Choose mortgage treatment', 'gameover': 'Game complete'}
            self.fit_text(phase_names.get(game.phase, game.phase), (822, 180, 440, 21), 15, GOLD)
        self.text('THE PLAYERS', 800, 225, 13, MUTED)
        self.text('Click a card to view holdings', 1000, 225, 13, MUTED)
        for i, player in enumerate(game.players):
            x, y = 800 + (i % 2) * 252, 251 + (i // 2) * 62
            label = 'Bankrupt' if player.bankrupt else f'£{player.cash:,}'
            self.button((x, y, 240, 55), '', f'player:{i}',
                        (34, 54, 68) if i == game.actor else (24, 36, 51), selected=i == game.actor)
            pygame.draw.circle(self.surface, COLORS[i], (x + 16, y + 17), 5)
            self.fit_text(player.name, (x + 29, y + 5, 190, 23), 16)
            control = 'AI' if player.is_ai else 'Human'
            if player.jailed:
                control += ' · jail'
            self.fit_text(f'{label}   ·   {control}', (x + 29, y + 29, 190, 19), 13, MUTED)
        status = 'YOUR MOVE' if human_can_act else 'COMPUTER PLAYING'
        if game.phase == 'gameover':
            status = 'GAME COMPLETE'
        self.text(status, 800, 447, 15, GOLD if human_can_act else MUTED)
        self.text('Scroll for more actions', 1084, 447, 13, MUTED)
        # Do not offer the inert AI management handoff: computers manage their
        # own turns. Human between-turn management remains explicitly available.
        actions = [(label, command) for label, command in game.actions()
                   if not (command.startswith('manage:')
                           and game.players[int(command.split(':')[1])].is_ai)]
        candidates = ('manage_done', 'settle', 'roll', 'end')
        suggested = next((command for command in candidates
                          if any(cmd == command for _, cmd in actions)), None)
        maximum = max(0, len(actions) - 7)
        self.scroll = max(0, min(self.scroll, maximum))
        for row, (label, command) in enumerate(actions[self.scroll:self.scroll + 7]):
            self.button((800, 478 + row * 42, 492, 38), label, 'game:' + command,
                        enabled=human_can_act, action=True,
                        suggested=command == suggested,
                        reason='Computer-controlled decision — wait for its move.' if actor.is_ai
                        else 'The game has finished.')
        self.fit_text('Same green = available  ·  Suggested = usual next step',
                      (800, 765, 492, 23), 12, MUTED)
        if maximum:
            track = pygame.Rect(1300, 478, 3, 290)
            pygame.draw.rect(self.surface, (42, 55, 71), track, border_radius=1)
            thumb = max(20, round(290 * 7 / len(actions)))
            pygame.draw.rect(self.surface, GOLD,
                             (1300, 478 + round((290 - thumb) * self.scroll / maximum), 3, thumb), border_radius=1)
        trade_allowed = game.phase in ('roll', 'end', 'debt') and human_can_act
        trade_reason = ('The game has finished.' if game.phase == 'gameover' else
                        'Computer-controlled decision — wait for its move.' if actor.is_ai else
                        'Finish the current purchase, auction or mortgage decision before trading.')
        self.button((800, 794, 240, 46), 'Propose trade', 'trade',
                    enabled=trade_allowed, action=True, reason=trade_reason)
        self.button((1052, 794, 240, 46), 'New game', 'new')
        if game.phase == 'gameover':
            self.wrap(f'{game.players[game.winner].name} wins the table.',
                      pygame.Rect(820, 500, 440, 100), 30, GOLD)
        self.panel((24, 868, 1268, 56), (19, 30, 44), (36, 49, 66), 10)
        self.button((34, 880, 154, 30), 'Table journal  +', 'journal', (29, 43, 58))
        latest = game.log[-1] if game.log else 'Welcome to the table.'
        self.fit_text(latest, (196, 880, 1075, 27), 16, MUTED)

    def _trade(self, game):
        """Two pages cover even a player who owns every purchasable property."""
        t = self.trade_state
        self.text('Make a proposal', 150, 105, 30, GOLD)
        self.button((1010, 95, 150, 42), 'Cancel', 'close')
        self.text(f'From {game.players[t["proposer"]].name}', 150, 158, 21)
        self.button((690, 150, 470, 43), f'To {game.players[t["other"]].name} · change', 'trade_other')
        for column, key, owner in ((0, 'give', t['proposer']), (1, 'take', t['other'])):
            x = 150 + column * 540
            self.text('Give deeds' if key == 'give' else 'Request deeds', x, 210, 19)
            indices = [i for i, deed in game.properties.items() if deed.owner == owner]
            indices = indices[t['page'] * 14:(t['page'] + 1) * 14]
            if not indices:
                self.text('No title deeds on this page', x, 280, 17, MUTED)
            for row, index in enumerate(indices):
                marker = '[X]' if index in t[key] else '[ ]'
                self.button((x, 244 + row * 29, 470, 27), marker + ' ' + BOARD[index].name,
                            f'trade_{key}:{index}')
        self.button((150, 660, 470, 35), f'Deed page {t["page"] + 1} / 2 · change page', 'trade_page')
        for column, key in enumerate(('offer', 'request')):
            x = 150 + column * 540
            self.text(f'{key.title()} cash: £{t[key]}', x, 708, 20, GOLD)
            for j, amount in enumerate((-100, -10, -1, 1, 10, 100)):
                self.button((x + j * 78, 744, 72, 37), f'{amount:+}', f'trade_{key}:{amount}')
            card = 'give_card' if key == 'offer' else 'take_card'
            self.button((x, 792, 470, 36), f'[{"X" if t[card] else " "}] Include one jail-free card', f'trade_{card}')
        self.button((690, 660, 470, 35), 'Submit for recipient consent', 'trade_submit', (35, 125, 101))
        self.text('Mortgaged deeds: recipient pays 10% interest now. No developed groups.', 150, 850, 15, MUTED)

    def holdings(self, game, owner):
        """Read an inventory without changing it; useful for drawing and tests.

        Deeds and jail-free cards are the only cards players retain. Ordinary
        Chance/Chest cards return to the deck after their effect is resolved.
        """
        deeds = [(i, deed) for i, deed in game.properties.items() if deed.owner == owner]
        return deeds, list(game.players[owner].jail_cards)

    def _holdings(self, game):
        """Show fourteen deed cards per page, enough for every possible estate."""
        owner = self.holdings_player
        player = game.players[owner]
        deeds, cards = self.holdings(game, owner)
        pages = max(1, (len(deeds) + 13) // 14)
        self.holdings_page = min(self.holdings_page, pages - 1)
        self.fit_text(f'{player.name} · collection', (150, 102, 820, 48), 32, COLORS[owner])
        self.button((1010, 100, 150, 42), 'Close', 'close')
        state = 'Bankrupt' if player.bankrupt else ('In jail' if player.jailed else 'In play')
        self.text(f'£{player.cash:,} cash  ·  {state}  ·  {len(deeds)} title deeds', 150, 166, 20)
        held = ['Chance' if name == 'chance' else 'Community Chest' for name in cards]
        jail_text = ('Get Out of Jail Free: ' + ', '.join(held)) if held else 'Get Out of Jail Free: none held'
        self.wrap(jail_text, pygame.Rect(150, 208, 1000, 62), 19, GOLD)
        if not deeds:
            self.text('No properties, stations or utilities owned yet.', 150, 315, 30, MUTED)
        start = self.holdings_page * 14
        for slot, (index, deed) in enumerate(deeds[start:start + 14]):
            # Two columns, seven cards each. Every card has a named title band,
            # a mortgage/building status and the current rent on this deed.
            x = 150 + (slot // 7) * 520
            y = 294 + (slot % 7) * 66
            rect = pygame.Rect(x, y, 490, 58)
            pygame.draw.rect(self.surface, (39, 57, 69), rect, border_radius=6)
            color = GROUPS.get(BOARD[index].group, (130, 156, 174))
            pygame.draw.rect(self.surface, color, (x, y + 5, 6, 48), border_radius=2)
            self.fit_text(BOARD[index].name, (x + 16, y + 5, 460, 24), 18)
            development = 'Hotel' if deed.houses == 5 else f'{deed.houses} houses' if deed.houses else 'No buildings'
            state = 'MORTGAGED · no rent' if deed.mortgaged else f'{development} · rent £{game.rent(index)}'
            if BOARD[index].kind == 'utility' and not deed.mortgaged:
                count = sum(d.owner == owner and BOARD[i].kind == 'utility' for i, d in game.properties.items())
                state = f'Unmortgaged · rent {10 if count == 2 else 4} × dice total'
            self.fit_text(state, (x + 16, y + 32, 460, 20), 14, MUTED)
        self.text(f'Title deed page {self.holdings_page + 1} of {pages}', 150, 786, 18)
        self.button((690, 774, 470, 42), 'Next title deed page', 'holdings_page', enabled=pages > 1)
        self.text('Only jail-free cards are kept; other drawn cards return to their deck.', 150, 846, 15, MUTED)

    def _overlay(self, game):
        """Modal controls replace board controls so a click cannot leak through."""
        self.buttons.clear()
        self.disabled_buttons.clear()
        self.disabled_targets.clear()
        self.button_states.clear()
        self.button_reasons.clear()
        # The board is paused beneath a modal. Dim its old READY buttons too,
        # rather than implying those background controls remain available.
        veil = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.surface.blit(veil, (0, 0))
        self.panel((110, 70, 1090, 820), (22, 35, 50), (63, 82, 102), 16)
        if self.modal == 'holdings':
            self._holdings(game)
        elif self.modal == 'deck':
            name = self.inspected_deck
            title = 'Chance' if name == 'chance' else 'Community Chest'
            self.text(title, 160, 125, 34, GOLD)
            self.button((1010, 100, 150, 42), 'Close', 'close')
            draw_icon(self.surface, 'chance' if name == 'chance' else 'chest',
                      pygame.Rect(160, 210, 75, 75))
            self.text(f'{len(game.decks[name])} cards currently in this deck', 270, 228, 23)
            card = game.last_cards[name]
            if card is None:
                message = 'No card has been drawn from this deck yet.'
            else:
                message = f'LAST DRAWN CARD\n\n{card["text"]}\n\nDrawn by {game.players[card["player"]].name}.'
            self.wrap(message, pygame.Rect(160, 345, 960, 280), 26)
            self.wrap('Cards are drawn automatically when a player lands on the matching space. This view never reveals the next card or changes the deck.',
                      pygame.Rect(160, 713, 960, 100), 19, MUTED)
        elif self.modal == 'journal':
            self.text('Table journal', 150, 110, 32, GOLD)
            self.text('Most recent events · newest at the bottom', 150, 164, 18, MUTED)
            self.button((1010, 100, 150, 42), 'Close', 'close')
            self.wrap('\n'.join(game.log[-16:]), pygame.Rect(150, 220, 1000, 620), 18)
        elif self.modal == 'trade':
            self._trade(game)
        elif self.modal == 'consent':
            t = self.trade_state
            self.text(f'{game.players[t["other"]].name}: accept this trade?', 155, 160, 28, GOLD)
            detail = (f'You receive: £{t["offer"]}, ' + ', '.join(BOARD[i].name for i in sorted(t['give']))
                      + ('; one jail-free card' if t['give_card'] else '')
                      + f'\nYou give: £{t["request"]}, ' + ', '.join(BOARD[i].name for i in sorted(t['take']))
                      + ('; one jail-free card' if t['take_card'] else ''))
            self.wrap(detail, pygame.Rect(160, 260, 960, 300), 23)
            self.button((160, 650, 440, 65), 'Accept proposal', 'trade_accept', (35, 125, 101))
            self.button((670, 650, 440, 65), 'Reject proposal', 'trade_reject')
        elif self.modal == 'quit':
            self.text('Close Monopoly?', 160, 245, 32, GOLD)
            detail = ('This game is not saved. Closing will lose the current game.'
                      if game is not None else 'You can return to the table instead.')
            self.wrap(detail, pygame.Rect(160, 315, 950, 90), 22, MUTED)
            self.button((160, 450, 440, 65), 'Keep playing' if game else 'Return to setup', 'close', (35, 105, 88))
            self.button((670, 450, 440, 65), 'Close application', 'quit_confirm', (110, 56, 55))
        elif self.modal == 'new':
            self.text('Abandon this game and choose new seats?', 160, 250, 28, GOLD)
            self.button((160, 450, 440, 65), 'Yes · return to setup', 'new_confirm')
            self.button((670, 450, 440, 65), 'Keep playing', 'close')
        elif self.modal == 'help':
            self.wrap('HOW TO PLAY\n\nChoose an action on the right. Scroll the mouse wheel for more actions. Click a board space to inspect it. Auctions ask one bidder at a time; passing withdraws.\n\nDebt pauses play: sell buildings evenly, mortgage bare deeds, or negotiate a trade. Settle the bill after raising cash.\n\nBetween turns: choose another player’s management action to let that seat build, mortgage or trade; then finish management.\n\nF1: help · N: new game confirmation · Escape: close a dialog, or ask before quitting. There is no save feature: closing loses the game.', pygame.Rect(160, 130, 960, 570), 21)
            self.button((160, 760, 440, 65), 'Return to game', 'close')

    def render(self, game=None):
        """Compose a frame, then letterbox it without distorting the board."""
        self.surface.fill(BACKGROUND)
        self.buttons.clear()
        self.disabled_buttons.clear()
        self.disabled_targets.clear()
        self.button_states.clear()
        self.button_reasons.clear()
        if game is None:
            self._setup()
        else:
            self.text('Monopoly', 24, 22, 34)
            self.text('LONDON  /  CLASSIC EDITION', 310, 38, 13, GOLD)
            self.text('LOCAL HOT-SEAT     ·     F1 HELP     ·     N NEW GAME', 800, 38, 13, MUTED)
            self._board(game)
            self._hud(game)
        if self.modal:
            self._overlay(game)
        mouse = self.point(pygame.mouse.get_pos())
        hovered_reason = next((self.button_reasons.get(command)
                               for rect, command in self.disabled_targets
                               if rect.collidepoint(mouse)), None)
        message = hovered_reason or self.notice
        if message:
            self.panel((110, 895, 1090, 36), (73, 56, 34), (123, 98, 54), 7)
            self.fit_text(message, (126, 899, 1058, 26), 16, GOLD)
        width, height = self.display.get_size()
        self.scale = min(width / self.WIDTH, height / self.HEIGHT)
        size = (round(self.WIDTH * self.scale), round(self.HEIGHT * self.scale))
        self.offset = ((width - size[0]) // 2, (height - size[1]) // 2)
        self.display.fill((8, 16, 22))
        self.display.blit(pygame.transform.smoothscale(self.surface, size), self.offset)
        pygame.display.flip()
