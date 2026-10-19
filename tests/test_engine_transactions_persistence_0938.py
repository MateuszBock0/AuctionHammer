"""0.9.38: illegal public actions are atomic and mid-decision saves stable."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from game.core.engine import Match
from game.core import auction
from game.core.models import IllegalMove
from game.core.audit import state_snapshot,digest
from game.core.persistence import save_match,load_match
from test_auction_v22_0931 import ready,award
from test_auction_v4_engine import place_basic


def signature(game):
    # Audit snapshot includes ruleset schema, deck and board, pending,
    # auction supply and queued effects; rejection may append only a
    # diagnostic command, not mutate the authoritative state.
    return digest(state_snapshot(game))


class AtomicIllegalCommands(unittest.TestCase):
    def assert_rejected_without_mutation(self,game,method,*args):
        before=signature(game)
        rng_before=game.rng.getstate()
        with self.assertRaises(IllegalMove):
            method(*args)
        self.assertEqual(before,signature(game))
        self.assertEqual(rng_before,game.rng.getstate())
        game.assert_integrity()

    def test_no_play_attack_or_choose_outside_legality(self):
        g=ready(38400)
        self.assert_rejected_without_mutation(g,g.play,'not-a-card')
        self.assert_rejected_without_mutation(g,g.attack,'S01','hero:1')
        self.assert_rejected_without_mutation(g,g.choose,0)

    def test_pending_cannot_be_forged_or_skipped_by_another_action(self):
        g=ready(38401)
        place_basic(g,'S09',1)
        place_basic(g,'S01',0,'hand')
        g.play('S01')
        self.assertIsNotNone(g.pending)
        self.assert_rejected_without_mutation(g,g.choose,-1)
        self.assert_rejected_without_mutation(g,g.choose,99)
        self.assert_rejected_without_mutation(g,g.end_turn)
        self.assert_rejected_without_mutation(g,g.attack,'S01','S09')

    def test_illegal_bid_does_not_pay_or_change_winner(self):
        g=ready(38402)
        g.round=4
        state=auction.begin(g)
        bidder=state.turn
        self.assert_rejected_without_mutation(g,g.auction_bid,bidder,True)
        self.assert_rejected_without_mutation(g,g.auction_bid,bidder,-1)
        self.assert_rejected_without_mutation(g,g.auction_bid,bidder,g.players[bidder].coins+1)
        self.assert_rejected_without_mutation(g,g.auction_bid,1-bidder,1)
        self.assert_rejected_without_mutation(g,g.auction_pick,bidder,state.offers[0].uid)

    def test_illegal_auction_pick_preserves_offer_pool(self):
        g=ready(38403)
        g.round=4
        state=auction.begin(g)
        for _ in range(2):
            g.auction_pass(g.auction.turn)
        picker=g.auction.turn
        self.assert_rejected_without_mutation(g,g.auction_pick,picker,'AUC000bogus')
        self.assert_rejected_without_mutation(g,g.auction_pick,1-picker,state.offers[0].uid)


class MidDecisionPersistence(unittest.TestCase):
    def saved_clone(self,game):
        before=signature(game)
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'save.json'
            save_match(game,dest)
            clone=load_match(dest)
        self.assertEqual(before,signature(clone))
        self.assertEqual(game.rng.getstate(),clone.rng.getstate())
        clone.assert_integrity()
        return clone

    def test_mid_base_card_target_choice_loads_identically(self):
        g=ready(38410)
        place_basic(g,'S09',1)
        place_basic(g,'S01',0,'hand')
        g.play('S01')
        self.assertIsNotNone(g.pending)
        clone=self.saved_clone(g)
        g.choose(0)
        clone.choose(0)
        self.assertEqual(signature(g),signature(clone))

    def test_mid_cartographer_second_selection_loads_identically(self):
        g=ready(38411)
        place_basic(g,'S09',1)
        source=award(g,'A016',1)
        g.play(source)
        self.assertIsNotNone(g.pending)
        g.choose(0)
        self.assertIsNotNone(g.pending)
        clone=self.saved_clone(g)
        g.choose(0)
        clone.choose(0)
        self.assertEqual(signature(g),signature(clone))
        g.assert_integrity()
        clone.assert_integrity()

    def test_mid_auction_bidding_and_picking_loads_identically(self):
        g=ready(38412)
        g.round=4
        auction.begin(g)
        clone=self.saved_clone(g)
        for match in (g,clone):
            for _ in range(2):
                match.auction_pass(match.auction.turn)
            match.auction_pick(match.auction.turn,match.auction.offers[0].uid)
        self.assertEqual(signature(g),signature(clone))
        after=self.saved_clone(g)
        for match in (g,after):
            match.auction_pick(match.auction.turn,match.auction.offers[1].uid)
        self.assertEqual(signature(g),signature(after))
        self.assertEqual(len(g.auction_history),1)


class InvariantFaultDetection(unittest.TestCase):
    def test_misfiled_hand_card_is_detected(self):
        g=ready(38420)
        uid=g.players[0].hand[0]
        g.cards[uid].zone='deck'
        with self.assertRaisesRegex(AssertionError,'zone mismatch'):
            g.assert_integrity()

    def test_changed_board_owner_is_detected(self):
        g=ready(38421)
        card=place_basic(g,'S03',0,'board')
        g.units[card].owner=1
        with self.assertRaisesRegex(AssertionError,'owners disagree'):
            g.assert_integrity()

    def test_negative_currency_is_detected(self):
        g=ready(38422)
        g.players[0].coins=-1
        with self.assertRaisesRegex(AssertionError,'Invalid coin balance'):
            g.assert_integrity()


if __name__=='__main__':
    unittest.main()
