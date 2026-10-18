"""Regression: 0-ATK combat targets and completely separate auction card bags.

Unchosen auction offers never join the 70-card bank and never reappear.
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

    def test_four_auctions_consume_all_12_unique_archetypes(self):
        game=ready(2611)
        offered_archetypes=set()
        rejected_uids=set()
        selected_uids=set()
        for index,round_number in enumerate((4,7,10,13),start=1):
            game.round=round_number
            offers=finish_auction(game)
            self.assertEqual(len(offers),3)
            these={o.archetype for o in offers}
            self.assertFalse(these & offered_archetypes)
            offered_archetypes.update(these)
            self.assertEqual(len(game.auction_bag),12-3*index)
            unchosen=offers[2].uid
            self.assertIn(unchosen,game.auction_discarded)
            self.assertNotIn(unchosen,game.cards)
            self.assertNotIn(unchosen,game.bank)
            self.assertNotIn(unchosen,game.players[0].deck)
            self.assertNotIn(unchosen,game.players[1].deck)
            rejected_uids.add(unchosen)
            selected_uids.update([offers[0].uid,offers[1].uid])
        self.assertEqual(offered_archetypes,set(CATALOG))
        self.assertEqual(set(game.auction_discarded),rejected_uids)
        self.assertEqual(len(game.auction_discarded),4)
        self.assertEqual(len(game.auction_awards),8)
        self.assertTrue(selected_uids<=set(game.cards))
        self.assertIsNone(auction.begin(game))
        self.assertEqual(len(game.auction_history),4)
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
        self.assertEqual(len(before['auction_v4']['bag']),9)
        self.assertEqual(before['auction_v4']['unchosen_discarded'],[offers[2].uid])
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'auction_bags.json'
            save_match(game,path)
            restored=load_match(path)
        self.assertEqual(before,state_snapshot(restored))
        self.assertNotIn(offers[2].uid,restored.cards)
        self.assertEqual(restored.auction_bag,game.auction_bag)
        restored.assert_integrity()

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
