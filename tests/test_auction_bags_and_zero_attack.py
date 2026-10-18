"""Regression: 0-ATK combat targets and completely separate auction card bags.

Unsold archetypes return to the auction-only bag; their old offer IDs are inert.
Only purchased offers become cards, and after leaving the board they may
not be drawn through the basic deck/grave recycling mechanism.
"""
import tempfile
import unittest
from pathlib import Path

from game.core import auction
from game.core.auction_catalog import CATALOG
from game.core.models import Unit
from game.core.audit import state_snapshot
from game.core.persistence import save_match,load_match
from game.ui.app import SoloApp
from test_auction_v4_engine import ready,place_basic


def finish_auction(game):
    current=auction.begin(game)
    if current is None:
        return None
    offered=current.offers[:]
    game.auction_pass(game.auction.turn)
    game.auction_pass(game.auction.turn)
    game.auction_pick(game.auction.turn,offered[0].uid)
    game.auction_pick(game.auction.turn,offered[1].uid)
    game.assert_integrity()
    return offered


class ZeroAttackTargetTests(unittest.TestCase):
    def test_zero_attack_taunt_remains_the_only_attack_target(self):
        game=ready(2601)
        place_basic(game,'S02',0)
        place_basic(game,'S33',1)  # passive PROWOKACJA
        place_basic(game,'S01',1)
        old=game.units['S33'].atk
        game._add_effect('S33','atk',-old,positive=False,source='debuff')
        self.assertEqual(game.units['S33'].atk,0)
        self.assertEqual(game.legal_attacks('S02'),['S33'])
        game.attack('S02','S33')
        self.assertEqual(game.units['S02'].attacks,1)
        game.assert_integrity()

    def test_defender_zero_atk_and_attacker_zero_atk_are_still_targetable(self):
        game=ready(2602)
        place_basic(game,'S02',0)
        place_basic(game,'S33',1)
        game.units['S02'].base_attack=0
        game.units['S33'].base_attack=0
        self.assertEqual(game.legal_attacks('S02'),['S33'])
        app=SoloApp.__new__(SoloApp)
        app.game=game
        app.selected='S02'
        self.assertEqual(app._attack_target_rects(),[app.slot_rect(1,0)])

    def test_original_0922_v3_engine_also_allows_zero_attack_target(self):
        from test_engine import setup_game,force_unit
        game=setup_game(2604)
        force_unit(game,'S02',0)
        force_unit(game,'S33',1)
        game.units['S33'].base_attack=0
        self.assertEqual(game.auction_catalog,'v3')
        self.assertEqual(game.units['S33'].atk,0)
        self.assertEqual(game.legal_attacks('S02'),['S33'])

    def test_no_taunt_zero_attack_enemy_is_selectable_normally(self):
        game=ready(2603)
        place_basic(game,'S02',0)
        place_basic(game,'S01',1)
        game.units['S01'].base_attack=0
        self.assertIn('S01',game.legal_attacks('S02'))
        self.assertIn('hero:1',game.legal_attacks('S02'))


class SeparateAuctionSupplyTests(unittest.TestCase):
    def test_banks_are_separate_from_match_creation(self):
        game=ready(2610)
        self.assertEqual(set(game.auction_bag),set(CATALOG))
        self.assertEqual(len(game.auction_bag),12)
        self.assertEqual(len(game.bank),50)
        self.assertTrue(all(uid.startswith('S') for uid in game.bank))
        self.assertEqual(game.auction_discarded,[])
        self.assertEqual(game.auction_used,[])
        game.assert_integrity()

    def test_unsold_archetypes_return_exclusively_to_auction_supply(self):
        game=ready(2611)
        purchased=set()
        rejected_uids=[]
        for index,round_number in enumerate((4,7,10,13,16),start=1):
            game.round=round_number
            offers=finish_auction(game)
            self.assertEqual(len(offers),3)
            these={o.archetype for o in offers}
            self.assertEqual(len(these),3)
            # No previously purchased archetype can be re-offered.
            self.assertFalse(these & purchased)
            sold={offers[0].archetype,offers[1].archetype}
            purchased.update(sold)
            returned=offers[2]
            self.assertIn(returned.archetype,game.auction_bag)
            self.assertNotIn(returned.uid,game.cards)
            self.assertIn(returned.uid,game.auction_discarded)
            self.assertEqual(len(game.auction_bag),12-2*index)
            self.assertEqual(len(game.auction_awards),2*index)
            self.assertFalse(set(game.auction_bag) & purchased)
            self.assertTrue(all(x.startswith('S') for x in game.bank))
            rejected_uids.append(returned.uid)
            game.assert_integrity()
        # Three offers are mandatory. After five auctions, 10 cards were
        # purchased and two unpurchased archetypes remain safely isolated.
        self.assertEqual(len(purchased),10)
        self.assertEqual(set(game.auction_bag),set(CATALOG)-purchased)
        self.assertEqual(len(game.auction_discarded),5)
        self.assertEqual(game.auction_discarded,rejected_uids)
        self.assertIsNone(auction.begin(game))
        self.assertEqual(len(game.auction_history),5)
        game.assert_integrity()

    def test_reoffered_archetype_can_be_bought_with_new_round_stats(self):
        game=ready(2616)
        game.round=4
        first=finish_auction(game)
        unbought=first[2].archetype
        self.assertIn(unbought,game.auction_bag)
        game.round=7
        # Ensure re-offer deterministically without assuming a specific RNG
        # shuffle: temporarily restrict choices by purchasing other two in
        # the normal first auction and selecting the returned third.
        original_sample=game.rng.sample
        game.rng.sample=lambda pop,n: [unbought]+[
            a for a in pop if a!=unbought][:n-1]
        try:
            second=auction.begin(game)
        finally:
            game.rng.sample=original_sample
        offer=next(o for o in second.offers if o.archetype==unbought)
        self.assertNotEqual(offer.uid,first[2].uid)
        self.assertEqual(offer.atk+offer.hp,14)  # R=6 -> total 14
        game.auction_pass(game.auction.turn)
        game.auction_pass(game.auction.turn)
        game.auction_pick(game.auction.turn,offer.uid)
        other=next(o.uid for o in second.offers if o.uid!=offer.uid)
        game.auction_pick(game.auction.turn,other)
        self.assertIn(offer.uid,game.auction_awards)
        self.assertNotIn(unbought,game.auction_bag)
        self.assertTrue(all(uid.startswith('S') for uid in game.bank))
        game.assert_integrity()

    def test_purchased_card_leaving_board_never_enters_basic_draw_cycle(self):
        game=ready(2612)
        game.round=4
        offers=finish_auction(game)
        uid=offers[0].uid
        owner=game.cards[uid].owner
        player=game.players[owner]
        self.assertIn(uid,player.hand)
        player.hand.remove(uid)
        player.board.append(uid)
        card=game.cards[uid]
        card.zone='board'
        game.units[uid]=Unit(uid,owner,card.attack,card.max_hp,
                             card.max_hp,card.ability_level,0)
        game._remove_unit(uid,death=False)
        self.assertIn(uid,game.auction_used)
        self.assertEqual(card.zone,'auction_used')
        self.assertNotIn(uid,player.grave)
        self.assertNotIn(uid,player.deck)
        self.assertNotIn(uid,player.hand)
        basic=next(x for x in player.hand if x.startswith('S'))
        player.hand.remove(basic)
        player.grave.append(basic)
        game.cards[basic].zone='grave'
        game.active=owner
        game._start_turn()
        self.assertNotIn(uid,player.hand)
        self.assertNotIn(uid,player.deck)
        self.assertNotIn(uid,player.grave)
        game.assert_integrity()

    def test_save_load_and_audit_track_both_separate_bags(self):
        game=ready(2613)
        game.round=4
        offers=finish_auction(game)
        self.assertIn(offers[2].uid,game.auction_discarded)
        before=state_snapshot(game)
        self.assertEqual(len(before['auction_v4']['bag']),10)
        self.assertEqual(before['auction_v4']['unsold_offers_history'],[offers[2].uid])
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'auction_bags.json'
            save_match(game,path)
            restored=load_match(path)
        self.assertEqual(before,state_snapshot(restored))
        self.assertNotIn(offers[2].uid,restored.cards)
        self.assertEqual(restored.auction_bag,game.auction_bag)
        restored.assert_integrity()

    def test_old_0923_save_restores_wrongly_discarded_archetype(self):
        game=ready(2617)
        game.round=4
        offers=finish_auction(game)
        unsold=offers[2].archetype
        # Recreate the released 0.9.23 save format before the correction.
        game.auction_bag.remove(unsold)
        game.auction_supply_version=1
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'v4_0923.json'
            save_match(game,path)
            loaded=load_match(path)
        self.assertIn(unsold,loaded.auction_bag)
        self.assertEqual(loaded.auction_supply_version,2)
        self.assertNotIn(offers[2].uid,loaded.cards)
        loaded.assert_integrity()

    def test_a009_discarding_stolen_auction_card_goes_to_spent_not_grave(self):
        from test_auction_v4_engine import award
        game=ready(2615)
        thief=award(game,'A009',2,owner=0,zone='hand',number=1)
        victim=award(game,'A005',0,owner=0,zone='hand',number=2)
        game.play(thief)
        # Swap the hands; the opposite player must choose up to two discards.
        index=next(i for i,c in enumerate(game.pending.choices)
                   if c.mode=='swap_all')
        game.choose(index)
        self.assertIn(victim,game.players[1].hand)
        index=next(i for i,c in enumerate(game.pending.choices)
                   if c.target==victim and c.mode=='discard')
        game.choose(index)
        self.assertIn(victim,game.auction_used)
        self.assertEqual(game.cards[victim].zone,'auction_used')
        self.assertNotIn(victim,game.players[1].grave)
        while game.pending:
            game.choose(0)
        game.assert_integrity()

    def test_v3_old_saves_keep_legacy_rule_mode(self):
        from game.core.engine import Match
        game=Match(2614,auctions_enabled=True,auction_catalog='v3')
        self.assertEqual(game.auction_bag,[])
        self.assertEqual(game.auction_discarded,[])
        self.assertEqual(game.auction_used,[])
        self.assertTrue(all(uid.startswith('S') for uid in game.bank))


if __name__=='__main__':
    unittest.main()
