# Interface design: a contemporary tabletop, not a developer control panel

## Design direction

The visual theme is an original London-club tabletop: deep navy surfaces, warm
ivory board stock, restrained brass accents and emerald primary actions. It is
not a reproduction of Hasbro artwork, nor a copied commercial app skin.

The redesign follows public usability guidance rather than claiming that one
visual style is a universal best practice. Sources were reachable on
27 October 2026:

- Nielsen Norman Group, [Ten usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/):
  visible system status, recognition rather than recall, consistency and control.
- Material Design, [Interaction states](https://m3.material.io/foundations/interaction/states/overview):
  distinguish enabled, disabled, hovered, pressed and selected controls.
- W3C, [Understanding minimum contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
  use relative luminance to check core text/background pairs. WCAG is web
  guidance; using its contrast formula here is **not** a claim that a Pygame
  desktop game meets every accessibility requirement.

## What changed, and why

| Decision | Purpose |
|---|---|
| Dedicated current-decision card | Answers “Who must do what next?” before showing options |
| Two-column player cards | Readable money/controller/state without six cramped text rows |
| Ivory board, larger corners | More physical-table character; title and token areas are distinct |
| Graphical dice | Last roll is recognisable without parsing a debug-style numeric line |
| Centre deed preview | Details are readable without printing every rent onto tiny spaces |
| Identical enabled fill; separate SUGGESTED text | Optional actions are just as available as the usual next step |
| Disabled reasons on hover/click | Explains why a visible control cannot execute |
| Hidden computer-management handoffs | Avoids offering a click that immediately returns without visible work |
| READY / LOCKED plus colour | State does not depend on colour alone; locked targets do not accept clicks |
| Selected player outline plus token number | Colour is supplementary, not the only identity signal |
| Hover / pressed outline | Mouse interaction receives immediate feedback |
| Visible scrollbar | Makes additional legal actions discoverable |
| Journal button and read-only overlay | Keeps the main table calm without removing event history |
| Consistent dimmed dialogs | Trade and inspection pause background actions; no click-through |
| Empty states | An empty collection or trade column explains itself rather than appearing broken |

## Familiar board symbols and safe exit

Special spaces use small original vector symbols: locomotive, question mark,
chest, light bulb, tap, tax diamond, GO arrow, car and jail bars. These convey
familiar board concepts but are not scans or tracings of commercial artwork.
`icons.py` draws them on a transparent reference surface, then scales each into
a reserved box. Streets retain their colour bands without extra decoration;
labels and prices are not replaced by icons.

Escape dismisses an existing dialog first. From the table or lobby it opens a
quit confirmation, as does the window close control. Cancellation is the first
button and no game state changes until the explicit close confirmation. AI play
pauses while the confirmation is visible. Test frame limits still exit directly
because they are deliberately requested automated-run limits.

## Printed amounts and centre decks

Income Tax and Super Tax show their payment amounts directly on the perimeter.
`TAX_AMOUNTS` is shared with the engine, preventing display/rules drift. GO shows
its collection amount without adding a second landing bonus. The title is the
plain word **Monopoly**, not a reproduced commercial logo.

Two original card-back stacks sit beside the central dice. Clicking one opens a
read-only view of its most recent public draw. `Game.last_cards` stores only the
last drawn card per deck, separate from hidden future deck order. A card image
is an inspection control, never permission to draw outside a landing effect.

## Typography and layout

The UI prefers an installed regular-weight Segoe UI, Arial or DejaVu Sans font,
with Pygame's default font as fallback. No system font files are copied into the
repository. Typeface rendering varies by platform; fonts are cached by size.

Spacing and corner radii are shared through helper functions. `panel()` draws
surfaces consistently; `button()` controls interaction states; `fit_text()` fits
single-line labels; `wrap()` splits long words in narrow board cells.
The board's full names remain available in the centre inspector and collection.
Street labels on the perimeter are intentionally smaller than action text.

The logical canvas remains **1320 × 940**. The original rectangle hit map now
uses 95-pixel corners and 62-pixel rectangular street spans. Both drawing and
mouse selection use exactly that map. Window resizing uniformly scales and
letterboxes the scene; it does **not** reflow into a mobile layout. A very small
window still makes text small. Use a larger window for comfortable play.

## Testing and limitations

`tests/test_design.py` checks all 40 targets at several window sizes, six-player
panel separation, modal target bounds, journal behaviour and core contrast pairs.
Existing tests still check enabled states, trades, ownership and rules.

Screenshots should also be inspected: geometry tests cannot measure elegance,
reading comfort or whether a card feels overcrowded. This is a mouse-oriented
Pygame interface, not an accessibility-certified screen-reader application.
Future improvements could include keyboard focus traversal, adjustable text size,
and a responsive/reflowing layout rather than uniform desktop scaling.
