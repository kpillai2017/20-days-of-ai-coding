# Day 14 — Monopoly

A Python + Pygame implementation of **classic British Monopoly (London edition)**, with original
geometric graphics and **2–6 local players in any human/computer combination**.
Human turns share the same mouse and window (hot-seat play, not network play).

> **Rules status:** a substantial playable educational implementation, not an
> official licensed product or a claim of perfect rules certification. Read
> [RULES.md](RULES.md), especially its explicit differences and remaining gaps.
> Monopoly editions differ: this project uses the British London edition with fixed
> £200 Income Tax and £100 Super Tax. The two 16-card decks use functional
> summaries with London destinations; they are not a transcription of every
> historical British printing. No house rules or Speed Die are used.

## Install and run

Use Python **3.9–3.13** (pygame 2.6.1). From the repository root:

```sh
cd day-14-monopoly
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`. If `python3` is not
available, use `python`. If sound/display drivers are missing, install/run on a
normal desktop session; no sound device is needed for this game.

```sh
python main.py --seed 42           # reproducible random stream
python main.py --demo              # four computers, watch them play
python main.py --demo --frames 30  # exit after 30 frames (NOT 30 FPS)
```

There are no downloads, API keys, accounts, telemetry or network connections.
No save/load feature: closing the window abandons the game.

## Visual design

The interface uses an original ivory-and-navy London tabletop theme, graphical
dice, player cards, a dedicated current-decision panel and consistent dialogs.
See [DESIGN.md](DESIGN.md) for the design rationale, public usability references,
contrast checks and limitations. **Table journal +** opens recent event history.
System UI fonts are used when available, with a Pygame fallback; no font assets
are bundled. Use a reasonably large desktop window for the best readability.

The board prints **Pay £200** on Income Tax, **Pay £100** on Super Tax and
**Collect £200** on GO. GO is still a single salary, not an extra landing bonus.
The centre contains visible Chance and Community Chest card stacks. Click one
to inspect its **last drawn card** and the player who drew it. Before the first
draw it says no card has been drawn; the future deck order is never exposed.
Opening this view does not draw a card, move a player or apply an effect again.

## Controls and a first game

1. Click a seat to cycle **Human → Computer → Off**. Choose at least two active
   seats; all six can be human or computer. Click **Start game**.
2. Starting dice automatically determine who goes first. Everyone gets £1500.
3. Read the gold decision-maker heading: in an auction or debt interruption this
   may NOT be the player whose turn it is.
4. Click **Roll dice**. On a vacant property, buy it at printed price or decline and auction it.
5. Choose actions in the right panel. **Mouse wheel scrolls** the complete legal
   action list, including mortgages, buildings and other players' management.
6. **All available actions have the same green fill and outline.** READY means
   clickable; SUGGESTED marks the usual next step but is equally clickable—not
   more enabled than an optional mortgage or building action. **Grey LOCKED
   buttons** cannot execute. Hover or click one to see its reason at the bottom.
   Computer-management handoffs are hidden: computers manage their own turns. The gold-outlined player row identifies the decision-maker.
   Legal actions refresh after every decision; use the mouse wheel for more.
7. **Click any player's name** to inspect their owned cards. The overlay lists
   all title deeds, mortgages, houses/hotels, rents and held Get Out of Jail Free
   cards (including which deck they came from). Use **Next title deed page** if
   there are more than 14 deeds. Empty inventories say so. Computer play pauses
   while this overlay is open; **Close** or **Escape** returns to the board.
8. Click any board square to inspect price, owner, mortgage, rents and buildings.
   Street rents list bare, 1/2/3/4 houses and hotel. Station rents correspond to
   owning 1/2/3/4 stations; utility entries are dice multipliers, not flat rents.
9. **End turn** once automatic movement, cards and bills have resolved.

**F1:** instructions. **N / New game:** confirmation before returning to setup.
The selected-space details panel has its own **Close** button. **Escape**
dismisses an open dialog first, then selected-space details; with neither open,
it asks for quit
confirmation. **Keep playing / Return to setup** cancels; **Close application**
exits. The window close button also asks, because games are not saved. Resize the window freely; the
logical board is letterboxed, and mouse coordinates use the same scaling.

### Auctions

All surviving players with cash can bid, including the player who declined the
purchase. The **Property Auction** panel keeps the property name, highest bid,
leading bidder and player currently being asked to bid visible throughout. The heading identifies the current bidder. Buttons offer several
increases and the bidder's cash balance. Passing withdraws from that auction.
There is no reserve: a first bid can be £1. No bidder means the deed remains
unowned. Bids do not charge cash until the winner is determined.

### Property management and debt

Scroll for **Build**, **Sell building**, **Mortgage** and **Redeem** actions.
Illegal operations are not offered: no uneven building, no mortgaging a colour
set containing buildings, no construction through a mortgaged property.
There are only **32 houses and 12 hotels**. If no four houses are available to
break down a hotel, the interface offers whole-group liquidation at half price.

A bill that exceeds cash pauses the turn. Sell, mortgage or trade, then choose
**Pay outstanding**. Bankruptcy is available only when bank liquidation cannot
cover the bill. Money goes to the actual creditor, not a Free Parking pot.
For between-turn management, the current seat chooses another player's
**manage property / trade** action and that player finishes with **Finish
property management**. These explicit windows avoid silent out-of-turn changes.

### Trades

Choose **Propose a trade**. Change the recipient; toggle deeds on each side
(two pages cover all 28 deeds), adjust offered/requested money by £1/£10/£100,
and optionally include a held jail-free card. Submit the proposal.

Human recipients see a consent screen; **nothing transfers until acceptance**.
Computers use an intentionally simple valuation policy and may decline. The
engine validates again after acceptance, so impossible offers change nothing.
No deed in a developed colour group can be traded. Recipients pay immediate
mortgage interest; see the documented transfer limitation in RULES.md.
Computer-to-computer negotiations can buy missing deeds at a premium to help
complete colour sets. Computers do not automatically accept on a human's behalf.

## How the code works

| File | Read it to learn |
|---|---|
| `data.py` | Immutable board/deed rent tables and two card decks |
| `engine.py` | Players, legal commands, money, movement and interrupted payments |
| `ai.py` | Simple legal-action selection and consent-based trade valuation |
| `ui.py` | Original board drawing, scaled mouse hit testing, forms and buttons |
| `icons.py` | Small original vector symbols for familiar special board spaces |
| `main.py` | Setup, event dispatch and non-blocking computer turns |
| `tests/` | Rule examples, complete bot games and real headless button clicks |

Follow the [beginner learning guide](LEARNING_GUIDE.md) and
[rules/limitations](RULES.md). Code comments explain why a step exists, not just
what its Python syntax says. There is no dependency on another Monopoly engine.

## Tests

```sh
python -m unittest discover -s tests -v
```

For headless Linux/macOS smoke runs:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --demo --frames 10
```

CI runs tests and setup/demo smoke checks. Tests are not proof that every
possible rules dispute, strategy or platform has been covered.

## References and rights

See [REFERENCES.md](REFERENCES.md). **Monopoly is a Hasbro trademark**; names
identify the game being studied. No affiliation or endorsement is claimed.
No commercial board scan, logo, token mesh, card scan or recorded sound is
bundled. Artwork is drawn from primitive shapes using installed UI fonts, with
pygame's default font as fallback. No font files are copied into the repository.
This repository's original code and prose use the root [MIT licence](../LICENSE).
That licence does **not** grant rights to third-party marks, game presentation or
reference materials. Separately installed pygame is LGPL-licensed; see
[third-party notices](../THIRD_PARTY_NOTICES.md). Educational/noncommercial use
is not asserted to be a universal legal permission.
