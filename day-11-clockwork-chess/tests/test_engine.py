"""Exact rules regressions: never weaken a perft count to hide an engine bug."""
import sys
from pathlib import Path
import threading
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Position, Move, START_FEN, notation_to_sq, sq_to_notation, perft, search


def play(pos,uci):
    move=next(m for m in pos.legal_moves() if m.uci()==uci)
    pos.push(move)
    return move


class Rules(unittest.TestCase):
    def test_square_roundtrip(self):
        for square in range(64):self.assertEqual(notation_to_sq(sq_to_notation(square)),square)
        for invalid in ('a0','i1','a11','',None):
            with self.assertRaises(ValueError):notation_to_sq(invalid)

    def test_start_perft(self):
        pos=Position()
        for depth,count in [(0,1),(1,20),(2,400),(3,8902)]:
            self.assertEqual(perft(pos,depth),count)
        self.assertEqual(pos.fen(),START_FEN)
        self.assertEqual(pos.history,[])

    def test_kiwipete_perft(self):
        pos=Position('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1')
        self.assertEqual(perft(pos,1),48)
        self.assertEqual(perft(pos,2),2039)

    def test_rook_pawn_endgame_perft(self):
        pos=Position('8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1')
        self.assertEqual(perft(pos,1),14)
        self.assertEqual(perft(pos,2),191)
        self.assertEqual(perft(pos,3),2812)

    def test_promotion_castling_suite(self):
        pos=Position('r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1')
        self.assertEqual(perft(pos,1),6)
        self.assertEqual(perft(pos,2),264)

    def test_each_move_undo_restores_all_state(self):
        pos=Position()
        for move in pos.legal_moves():
            before=(pos.fen(),pos.keys[:],len(pos.history))
            pos.push(move);pos.pop()
            self.assertEqual((pos.fen(),pos.keys,len(pos.history)),before)

    def test_castle_moves_rook_and_undo(self):
        for uci,rook_to in [('e1g1','f1'),('e1c1','d1')]:
            pos=Position('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
            before=pos.fen();play(pos,uci)
            self.assertEqual(pos.board[notation_to_sq(rook_to)],'R')
            self.assertNotIn('K',pos.castling);self.assertNotIn('Q',pos.castling)
            pos.pop();self.assertEqual(pos.fen(),before)

    def test_castle_through_attack_forbidden(self):
        pos=Position('4kr2/8/8/8/8/8/8/R3K2R w KQ - 0 1')
        moves={m.uci() for m in pos.legal_moves()}
        self.assertNotIn('e1g1',moves);self.assertIn('e1c1',moves)

    def test_capture_rook_loses_rights(self):
        pos=Position('r3k2r/8/8/8/8/8/7Q/4K3 w kq - 0 1')
        play(pos,'h2h8');self.assertNotIn('k',pos.castling);self.assertIn('q',pos.castling)

    def test_en_passant(self):
        pos=Position('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1')
        before=pos.fen();move=play(pos,'e5d6')
        self.assertTrue(move.en_passant)
        self.assertEqual(pos.board[notation_to_sq('d5')],'.')
        pos.pop();self.assertEqual(pos.fen(),before)

    def test_pinned_en_passant_not_legal_or_repetition_relevant(self):
        pos=Position('k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1')
        without=Position('k3r3/8/8/3pP3/8/8/8/4K3 w - - 0 1')
        self.assertNotIn('e5d6',{m.uci() for m in pos.legal_moves()})
        self.assertEqual(pos.key(),without.key())

    def test_legal_en_passant_changes_key(self):
        pos=Position('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1')
        without=Position('4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1')
        self.assertNotEqual(pos.key(),without.key())

    def test_all_four_promotions(self):
        pos=Position('4k3/P7/8/8/8/8/8/4K3 w - - 0 1')
        promotions=[m for m in pos.legal_moves() if m.from_sq==48]
        self.assertEqual({m.promotion for m in promotions},set('qrbn'))
        for move in promotions:
            before=pos.fen();pos.push(move)
            self.assertEqual(pos.board[56],move.promotion.upper());pos.pop()
            self.assertEqual(pos.fen(),before)

    def test_king_never_captured(self):
        pos=Position('4k3/8/8/8/8/8/4R3/K7 w - - 0 1')
        self.assertNotIn('e2e8',{m.uci() for m in pos.legal_moves()})

    def test_fools_mate(self):
        pos=Position()
        for uci in ['f2f3','e7e5','g2g4','d8h4']:play(pos,uci)
        self.assertEqual(pos.outcome(),'Black wins by checkmate')

    def test_stalemate(self):
        pos=Position('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        self.assertEqual(pos.outcome(),'Draw: stalemate')

    def test_insufficient_material_conservative(self):
        for fen in ['7k/8/8/8/8/8/8/K7 w - - 0 1','7k/8/8/8/8/8/8/KN6 w - - 0 1','7k/8/8/8/8/8/8/KB6 w - - 0 1']:
            self.assertIn('insufficient',Position(fen).outcome())
        self.assertFalse(Position('7k/8/8/8/8/8/8/KNN5 w - - 0 1').insufficient_material())

    def test_threefold(self):
        pos=Position()
        for uci in ['g1f3','g8f6','f3g1','f6g8']*2:play(pos,uci)
        self.assertIn('threefold',pos.outcome())
        pos.pop();self.assertIsNone(pos.outcome())

    def test_fifty_move_and_mate_precedence(self):
        self.assertIn('fifty',Position('7k/8/8/8/8/8/R7/K7 w - - 100 55').outcome())
        self.assertIn('checkmate',Position('7k/6Q1/5K2/8/8/8/8/8 b - - 100 55').outcome())

    def test_fen_validation(self):
        for fen in ['bad','8/8/8/8/8/8/8/8 w - - 0 1','4k3/8/8/8/8/8/8/4K3 w K - 0 1','4k3/8/8/8/8/8/8/4K3 w - e3 0 1','4k3/8/8/8/8/8/8/4K3 w - - -1 0','4k3/8/8/8/8/8/8/4K4 w - - 0 1']:
            with self.assertRaises(ValueError):Position(fen)

    def test_clone_independent(self):
        pos=Position();play(pos,'e2e4');clone=pos.clone();play(clone,'e7e5')
        self.assertNotEqual(pos.fen(),clone.fen());self.assertEqual(len(pos.history),1)


class Search(unittest.TestCase):
    def test_legal_move_no_mutation(self):
        pos=Position();before=pos.fen();keys=pos.keys[:]
        result=search(pos,max_depth=2,time_limit=1)
        self.assertIn(result.move,pos.legal_moves());self.assertGreaterEqual(result.depth,1)
        self.assertEqual(pos.fen(),before);self.assertEqual(pos.keys,keys);self.assertEqual(pos.history,[])

    def test_mate_in_one(self):
        pos=Position('7k/8/5KQ1/8/8/8/8/8 w - - 0 1')
        result=search(pos,max_depth=2,time_limit=1)
        pos.push(result.move);self.assertIn('checkmate',pos.outcome())

    def test_stop_and_short_timeout_have_legal_fallback(self):
        pos=Position();stop=threading.Event();stop.set()
        start=time.monotonic();result=search(pos,max_depth=8,time_limit=.001,stop_event=stop)
        self.assertLess(time.monotonic()-start,.5);self.assertIn(result.move,pos.legal_moves())
        self.assertEqual(result.depth,0);self.assertEqual(pos.fen(),START_FEN)

    def test_terminal_no_move(self):
        pos=Position('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        self.assertIsNone(search(pos).move)

    def test_search_arguments(self):
        for depth in [0,True,9]:
            with self.assertRaises(ValueError):search(Position(),max_depth=depth)
        for seconds in [0,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):search(Position(),time_limit=seconds)


if __name__=='__main__':unittest.main()
