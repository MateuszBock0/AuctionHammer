"""0.9.32 regressions for v22 card isolation, real rarity evolution and save transitions.

These cases reproduce two omissions found during the 0.9.31 source audit.
The older 12-card v4 mode must retain its existing behaviour.
"""
import tempfile
import unittest
from pathlib import Path

from game.core import auction,auction_abilities
from game.core.auction_catalog import CATALOG_V22,CATALOG,V22_CARDS,live_variant
from game.core.persistence import save_match,load_match
from game.core.audit import state_snapshot
from test_auction_v22_0931 import ready,award,choose
from test_auction_v4_engine import place_basic


def round_trip(game):
    with tempfile.TemporaryDirectory() as folder:
        filename=Path(folder)/'state.json'
        save_match(game,filename)
        recovered=load_match(filename)
    recovered.assert_integrity()
    return recovered


def close_auction(game):
    state=game.auction
    if state.phase=='bidding':
        game.auction_pass(state.turn)
        game.auction_pass(game.auction.turn)
    game.auction_pick(game.auction.turn,state.offers[0].uid)
    game.auction_pick(game.auction.turn,state.offers[1].uid)
    game.assert_integrity()


class AuctionV22RarityRegression(unittest.TestCase):
    def test_purchased_v22_cards_evolve_on_real_full_rounds_not_hand_turns(self):
        game=ready(932000)
        hand=award(game,'A013',0,zone='hand')
        on_board=award(game,'A014',0,zone='board',n=2)
        frozen={uid:(game.cards[uid].attack,game.cards[uid].max_hp)
                for uid in (hand,on_board)}
        for round_value,expected in ((6,'rzadka'),(9,'legendarna'),(12,'legendarna')):
            with self.subTest(completed_round=round_value):
                game.round=round_value
                game.active=1-game.first  # end of complete round
                game.phase='turn'
                game.end_turn()
                for uid in (hand,on_board):
                    meta=game.auction_awards[uid]
                    self.assertEqual(meta['rarity'],expected)
                    self.assertEqual(meta['last_evolve_round'],round_value)
                    self.assertEqual(game.cards[uid].definition.effect,
                                     live_variant('v22',meta['archetype'],expected))
                    self.assertEqual((game.cards[uid].attack,game.cards[uid].max_hp),
                                     frozen[uid])
                self.assertEqual(game.phase,'auction')
                close_auction(game)
        game.assert_integrity()

    def test_evolution_from_basic_to_rare_survives_save_and_no_duplicate_upgrade(self):
        game=ready(932001)
        uid=award(game,'A018',0)
        game.round=6
        game.active=1-game.first
        game.end_turn()
        self.assertEqual(game.auction_awards[uid]['rarity'],'rzadka')
        loaded=round_trip(game)
        self.assertEqual(loaded.auction_awards[uid]['rarity'],'rzadka')
        self.assertEqual(loaded.cards[uid].definition.effect,
                         live_variant('v22','A018','rzadka'))
        before=state_snapshot(loaded)
        auction.advance_rarity(loaded,6)
        self.assertEqual(state_snapshot(loaded),before)
        close_auction(loaded)
        loaded.assert_integrity()

    def test_A002_rarity_evolution_opens_choice_and_can_resume_saved_game(self):
        game=ready(932011)
        ally=place_basic(game,'S01',0)
        general=award(game,'A002',0,zone='board')
        game.round=6
        game.active=1-game.first
        game.end_turn()
        self.assertEqual(game.auction_awards[general]['rarity'],'rzadka')
        self.assertIsNotNone(game.pending)
        self.assertEqual(game.pending.uid,general)
        self.assertEqual(game.pending.context,'auction_evolve')
        self.assertTrue(any(c.mode=='general_target' and c.target==ally
                            for c in game.pending.choices))
        resumed=round_trip(game)
        choose(resumed,'general_target',ally)
        self.assertEqual(resumed.auction_general_targets[general],ally)
        self.assertTrue(auction_abilities.boosted_attack(resumed,ally))
        self.assertEqual(resumed.phase,'auction')
        close_auction(resumed)
        resumed.assert_integrity()

    def test_v4_legacy_still_evolves_without_17_card_catalog(self):
        from test_auction_v4_engine import ready as v4_ready,award as v4_award
        game=v4_ready(932002)
        uid=v4_award(game,'A005',0)
        game.round=6
        game.active=1-game.first
        game.end_turn()
        self.assertEqual(game.auction_awards[uid]['rarity'],'rzadka')
        self.assertEqual(len(CATALOG),12)
        self.assertEqual(len(CATALOG_V22),17)
        self.assertEqual(len(game.auction_bag),11 if game.auction is None else 8)
        recovered=round_trip(game)
        self.assertEqual(recovered.auction_catalog,'v4')
        self.assertEqual(recovered.auction_awards[uid]['rarity'],'rzadka')
        game.assert_integrity()

class AuctionV22DiscardIsolation(unittest.TestCase):
    def _swap_with_auction_card(self,save_on_pending=False):
        game=ready(932030+int(save_on_pending))
        thief=award(game,'A009',2,owner=0)
        other=award(game,'A014',0,owner=0,n=2)
        game.play(thief)
        self.assertIsNotNone(game.pending)
        if save_on_pending:
            game=round_trip(game)
        choose(game,'swap_all')
        self.assertIn(other,game.players[1].hand)
        self.assertEqual(game.cards[other].owner,1)
        self.assertIsNotNone(game.pending)
        self.assertEqual(game.pending.context,'auction_discard')
        if save_on_pending:
            game=round_trip(game)
        choose(game,'discard',other)
        # A009 can ask for a second discard. It must not move the already
        # discarded auction card again; any remaining choice is resolved.
        while game.pending:
            game.choose(0)
        return game,other

    def test_legendary_A009_discard_preserves_auction_only_bag(self):
        game,other=self._swap_with_auction_card()
        self.assertIn(other,game.auction_used)
        self.assertEqual(game.cards[other].zone,'auction_used')
        self.assertNotIn(other,game.players[1].grave)
        self.assertNotIn(other,game.players[0].grave)
        self.assertNotIn(other,game.bank)
        self.assertFalse(any(uid.startswith('AUC') for p in game.players
                             for uid in p.deck+p.grave))
        game.assert_integrity()

    def test_pending_A009_swaps_and_discards_survive_save_reload(self):
        game,other=self._swap_with_auction_card(save_on_pending=True)
        restored=round_trip(game)
        self.assertIn(other,restored.auction_used)
        self.assertNotIn(other,restored.players[1].grave)
        self.assertEqual(restored.auction_catalog,'v22')
        restored.assert_integrity()

    def test_canonical_v22_metadata_is_live_with_draft_source_preserved(self):
        from pathlib import Path
        import json
        path=Path(__file__).resolve().parents[1]/'data'/'auction'/'KATALOG_AUKCYJNY_17_v22.json'
        spec=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(spec['status'],'LIVE_V22')
        self.assertEqual(spec['count_archetypes'],17)
        self.assertEqual(spec['count_effect_variants'],51)
        self.assertEqual(spec['total_archetypes'],17)
        self.assertEqual(spec['variants'],51)
        self.assertEqual(set(CATALOG_V22),{card['id'] for card in spec['cards']})
        self.assertEqual(sum(len(card['variants']) for card in spec['cards']),51)
        self.assertNotIn('A017',CATALOG_V22)
        self.assertEqual(spec['auction_rules']['status'],'IMPLEMENTED_V22_LOCAL_DEMO')
        self.assertEqual(spec['approval']['status'],
                         'IMPLEMENTED_IN_LOCAL_DEMO_NOT_STATISTICALLY_BALANCED')
        self.assertEqual(spec['source_proposal_metadata']['approval']['status'],
                         'PROPOSAL_REVIEWED_NOT_FINAL_BALANCED')
        self.assertEqual(len(spec['source_proposal_metadata']['notes_needing_confirmation']),4)

    def test_v22_no_auction_after_eight_purchases_returns_one_unbought(self):
        game=ready(932035)
        for index in range(8):
            game.round=4+3*index
            state=auction.begin(game)
            self.assertIsNotNone(state)
            self.assertEqual(len({o.archetype for o in state.offers}),3)
            close_auction(game)
        self.assertEqual(len(game.auction_bag),1)
        game.round=28
        self.assertIsNone(auction.begin(game))
        self.assertFalse(any(x.startswith('AUC') for x in game.bank))
        game.assert_integrity()


class AuctionV22TriggerAndSaveBoundaries(unittest.TestCase):
    def test_A015_cancel_once_then_after_removal_no_ward(self):
        game=ready(932050)
        warden=award(game,'A015',0,zone='board')
        target=place_basic(game,'S33',0)
        attacker=place_basic(game,'S01',1,'hand')
        # Basic A015 should consume protection once for a hostile play
        # aimed at the owner's board. After warden removal the guard dies.
        self.assertTrue(auction_abilities.block_trigger(game,attacker,'play'))
        self.assertIn(warden,game.auction_blocked_play)
        self.assertFalse(auction_abilities.block_trigger(game,attacker,'play'))
        restored=round_trip(game)
        self.assertIn(warden,restored.auction_blocked_play)
        self.assertFalse(auction_abilities.block_trigger(restored,attacker,'play'))
        restored._remove_unit(warden,death=False)
        self.assertNotIn(warden,restored.auction_blocked_play)
        self.assertFalse(auction_abilities.block_trigger(restored,attacker,'play'))
        restored.assert_integrity()

    def test_A015_rare_global_death_block_and_silence_switch(self):
        game=ready(932051)
        warden=award(game,'A015',1,zone='board')
        self.assertTrue(auction_abilities.global_trigger_block(game,'death'))
        self.assertFalse(auction_abilities.global_trigger_block(game,'end'))
        game._add_effect(warden,'silence',expires=game._expiry(0),source='test')
        self.assertFalse(auction_abilities.global_trigger_block(game,'death'))
        game.assert_integrity()

    def test_A015_legendary_block_three_triggers_but_not_passive_or_attack(self):
        game=ready(932052)
        warden=award(game,'A015',2,zone='board')
        for ctx in ('play','death','end'):
            self.assertTrue(auction_abilities.global_trigger_block(game,ctx))
        for ctx in ('passive','attack','auction_evolve'):
            self.assertFalse(auction_abilities.global_trigger_block(game,ctx))
        loaded=round_trip(game)
        for ctx in ('play','death','end'):
            self.assertTrue(auction_abilities.global_trigger_block(loaded,ctx))
        loaded.assert_integrity()

    def test_A016_saved_pending_choice_and_A018_vouchers_remain_unmodified(self):
        game=ready(932053)
        card=award(game,'A016',1)
        game.play(card)
        self.assertIsNotNone(game.pending)
        old=state_snapshot(game)
        loaded=round_trip(game)
        self.assertEqual(state_snapshot(loaded),old)
        target=loaded.pending.choices[0].target
        loaded.choose(0)
        self.assertIn(target,loaded.players[0].hand)
        while loaded.pending:
            loaded.choose(0)
        loaded.assert_integrity()

        other=ready(932054)
        owner_card=award(other,'A018',1)
        other.play(owner_card)
        self.assertEqual(other.auction_vouchers[0],[{'bonus':5}])
        resumed=round_trip(other)
        resumed.round=4
        offer=auction.begin(resumed)
        self.assertEqual(offer.bid_bonus[0],5)
        self.assertEqual(resumed.auction_vouchers[0],[])
        while offer.phase=='bidding':
            resumed.auction_pass(offer.turn)
        resumed=round_trip(resumed)
        self.assertEqual(resumed.auction.bid_bonus[0],5)
        close_auction(resumed)
        resumed.assert_integrity()

if __name__=='__main__':
    unittest.main()
