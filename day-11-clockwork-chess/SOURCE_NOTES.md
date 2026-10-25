# VICE source mapping and attribution

Requested reference: [bluefeversoft/vice, `Vice11/src` on main](https://github.com/bluefeversoft/vice/tree/main/Vice11/src). VICE means **Video Instructional Chess Engine**, written in C by **Richard Allbert / Bluefever Software** as a teaching series. Its README warns that the deliberately simplified instructional structure should not be treated as universal best practice.

## Licence review

The upstream root [LICENSE](https://github.com/bluefeversoft/vice/blob/main/LICENSE) is MIT, copyright **2022 bluefeversoft**. It permits modification and redistribution subject to preserving its copyright/permission notice. We retain the full fetched notice as [VICE_LICENSE.txt](VICE_LICENSE.txt) and reference it in `engine.py` and root third-party notices. The review was performed on 25 October 2026. The main branch URL is mutable, not an immutable revision pin.

We read the upstream README, licence and selected C files directly before implementing this Python rewrite. No C files, binaries, ROMs, books or asset bundles are shipped. The design borrows VICE's instructional logic and standard chess-engine algorithms; this is **not a line-by-line translation**, and no claim is made that behaviour or strength matches VICE11.

## Conceptual mapping

| Upstream reference | Python implementation | Difference for clarity |
| --- | --- | --- |
| `defs.h`, board infrastructure | `Position`, `Move`, 64-square list | No 120-square mailbox, packed move bitfields, incremental piece lists or Zobrist hash |
| `movegen.c`, `GenerateAllMoves` | `Position.pseudo_moves` | Explicit file/rank bounds prevent wraparound; Python immutable Move records |
| `makemove.c`, `MakeMove`, `TakeMove` | `push`, `pop`, `legal_moves` | Snapshot board/state, filter moves that leave mover in check; snapshots cost speed but simplify restoration |
| Attack detection | `is_attacked`, `in_check` | Attacks remain distinct from legal moves; pinned pieces still attack king-path squares |
| `evaluate.c`, `EvalPosition` | `evaluate` | Independent simple material, minor-piece centrality and pawn-advance terms, not copied tables |
| `search.c`, `AlphaBeta`, `Quiescence`, `SearchPosition` | `search` and nested negamax/quiesce | Iterative completed depths, deadline/cancellation inside recursion, try/finally restoration |
| `movegen.c`, MVV/LVA scores | capture sorting | Prefer high-value victims and cheaper attackers; promotions get a bonus |

The linked tree contains features beyond this small project, including transposition-table machinery and other search optimisations. We intentionally omit those, along with null-move pruning, opening books, SMP search and UCI/console engine protocols.

## Deliberate rules/UI decisions

- Threefold and fifty-move draws are automatically claimed in this friendly app. Fivefold/75-move tournament distinctions are omitted.
- Repetition keys include en-passant targets only if an actual legal capture is available, including pinned-pawn king safety.
- Material draw detection is conservative, not a complete all-position dead-position proof.
- FEN parsing validates structure, counters, kings, castling placement and en-passant plausibility. It is not a full retrograde legality validator for positions reachable from the starting game.
- Search's bounded quiescence cap can evaluate a nonterminal checked position at its extension limit. This limits runaway checks and is a strength tradeoff, not a rule-generation error.
- Presentation is independent original Pygame code, with switchable top-down/isometric views, six attacker-specific procedural combat styles and synthesised audio. Neither VICE nor Battle Chess supplies our piece geometry, animation or audio.

## Verification sources

Exact expectations are taken from standard public perft reference positions, not adjusted to match a faulty result:

- Start: depth 1 **20**, depth 2 **400**, depth 3 **8,902**.
- Kiwipete: depth 1 **48**, depth 2 **2,039**.
- Rook/pawn endgame reference: **14**, **191**, **2,812**.
- Castling/promotion reference: **6**, **264**.

See [Chess Programming Wiki perft results](https://www.chessprogramming.org/Perft_Results). These small depths are strong regression checks but not exhaustive certification. The tests also directly exercise special moves, draws, search restoration and animation/UI state.
