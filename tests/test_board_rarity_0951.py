"""0.9.51: physical slot tactics, signed replay compatibility and rarity.

No mocked combat engine. Existing Match() defaults to legacy for old archives.
"""
import os
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

from game.core.engine import Match
from game.core.audit import state_snapshot,digest,verify_replay
from game.core.persistence import save_match,load_match
from game.core.auction import advance_rarity
from game.core.models import IllegalMove
from game.ui.rarity_view import card_rarity,rarity_color
from test_engine import force_unit
from test_auction_v22_0931 import award


def fixed_match(seed=95100):
    g=Match(seed,audit_enabled=True,auctions_enabled=True,
            auction_catalog='v22',fixed_board_slots=True)
    g.finish_mulligan(0,[])
    g.finish_mulligan(1,[])
    g.phase='turn';g.active=0;g.pending=None
    if g.players[0].turn_count==0:g.players[0].turn_count=1
    return g


class StablePhysicalBoard(unittest.TestCase):
    def test_death_leaves_middle_hole_with_units_to_the_right_unmoved(self):
        g=fixed_match(95101)
        left=force_unit(g,'S01',0,slot=0)
        middle=force_unit(g,'S27',0,slot=2)
        right=force_unit(g,'S34',0,slot=4)
        self.assertEqual([g.unit_at(0,i) for i in range(5)],
                         ['S01',None,'S27',None,'S34'])
        g._remove_unit('S27',death=True)
        self.assertEqual(g.slot_of('S01'),0)
        self.assertEqual(g.slot_of('S34'),4)
        self.assertEqual([g.unit_at(0,i) for i in range(5)],
                         ['S01',None,None,None,'S34'])
        self.assertIn(2,g.available_slots(0))
        g.assert_integrity()

    def test_explicit_slot_play_and_occupied_slot_rejection(self):
        g=fixed_match(95102)
        uid=g.players[0].hand[0]
        self.assertTrue(g.can_play(0,uid,slot=4))
        self.assertFalse(g.can_play(0,uid,slot=7))
        g.play(uid,slot=4)
        self.assertEqual(g.slot_of(uid),4)
        self.assertFalse(g.can_play(0,uid,slot=4))
        self.assertEqual(g.unit_at(0,4),uid)
        g.assert_integrity()

    def test_full_board_replacement_keeps_target_slot(self):
        g=fixed_match(95103)
        for i,uid in enumerate(('S01','S27','S34','S35','S108')):
            force_unit(g,uid,0,slot=i)
        candidate=g.players[0].hand[0]
        old='S34'
        self.assertTrue(g.can_play(0,candidate,old,slot=2))
        self.assertFalse(g.can_play(0,candidate,old,slot=1))
        g.play(candidate,old,slot=2)
        self.assertEqual(g.slot_of(candidate),2)
        self.assertEqual([g.slot_of(uid) for uid in g.players[0].board],
                         [0,1,2,3,4])
        self.assertNotIn(old,g.units)
        g.assert_integrity()

    def test_s34_has_only_true_neighbours(self):
        g=fixed_match(95104)
        s=force_unit(g,'S34',0,slot=0)
        target=force_unit(g,'S01',0,slot=2)
        g._update_auras(defer_reactive=True)
        self.assertEqual(target.aura_atk,0)
        adjacent=force_unit(g,'S27',0,slot=1)
        g._update_auras(defer_reactive=True)
        self.assertEqual(adjacent.aura_atk,1)
        self.assertEqual(target.aura_atk,0)
        g.assert_integrity()

    def test_s108_only_opposing_slot_and_once(self):
        g=fixed_match(95105)
        force_unit(g,'S108',0,slot=3)
        elsewhere=force_unit(g,'S01',1,slot=1)
        before=elsewhere.hp
        g._apply_position_reactions()
        self.assertEqual(elsewhere.hp,before)
        opposite=force_unit(g,'S27',1,slot=3)
        before=opposite.hp
        g._apply_position_reactions()
        self.assertLess(opposite.hp,before)
        after=opposite.hp
        g._apply_position_reactions()
        self.assertEqual(opposite.hp,after)
        self.assertEqual(g.slot_of('S108'),3)
        g.assert_integrity()

    def test_save_load_keeps_all_holes_and_legacy_mode_stays_compact(self):
        g=fixed_match(95106)
        force_unit(g,'S01',0,slot=0)
        force_unit(g,'S27',0,slot=4)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fixed.json'
            before=digest(state_snapshot(g))
            save_match(g,path)
            restored=load_match(path)
        self.assertTrue(restored.fixed_board_slots)
        self.assertEqual(digest(state_snapshot(restored)),before)
        self.assertEqual(restored.unit_at(0,4),'S27')
        self.assertEqual(restored.available_slots(0),[1,2,3])
        restored.assert_integrity()
        legacy=Match(95106,auctions_enabled=True,auction_catalog='v22')
        self.assertNotIn('board_layout',state_snapshot(legacy))
        self.assertFalse(legacy.fixed_board_slots)

    def test_complete_signed_replay_reconstructs_new_layout(self):
        g=Match(95107,auctions_enabled=True,auction_catalog='v22',
                audit_enabled=True,fixed_board_slots=True)
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        if g.phase=='turn' and g.pending is None:
            active=g.active
            if g.players[active].hand:
                g.play(g.players[active].hand[0],slot=4)
        payload={
            'seed':g.seed,'complete_from_start':True,
            'initial_state':g.audit_initial,'actions':g.audit_actions,
            'event_journal':g.event_journal,'internal_events':g.audit_internal,
            'final_state':state_snapshot(g),
            'summary':{'vacant_slot_income_enabled':g.vacant_income_enabled,
                       'ruleset_version':g.ruleset_version},
        }
        self.assertTrue(verify_replay(payload,lambda seed,**kwargs:
                                     Match(seed,audit_enabled=True,**kwargs)))


class FixedBoardCanvas(unittest.TestCase):
    def test_click_selected_empty_slot_plays_card_at_that_slot(self):
        import pygame
        from unittest.mock import patch
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        try:
            app.menu_open=False
            g=app.game
            g.phase='turn';g.active=0;g.pending=None
            g.players[0].turn_count=max(1,g.players[0].turn_count)
            g.players[0].played_this_turn=False
            uid=g.players[0].hand[0]
            app.selected=uid
            app.click(app.slot_rect(0,4).center)
            self.assertEqual(g.slot_of(uid),4)
            self.assertEqual(g.unit_at(0,4),uid)
            self.assertIsNone(g.unit_at(0,0))
            g.assert_integrity()
        finally:
            pygame.quit()


class RarityIdentity(unittest.TestCase):
    def test_three_distinct_tiers_and_only_auction_cards(self):
        self.assertEqual(len({rarity_color(r) for r in
                              ('podstawowa','rzadka','legendarna')}),3)
        g=fixed_match(95108)
        self.assertIsNone(card_rarity(g.cards['S01']))
        uid=award(g,'A014',0,owner=0)
        card=g.cards[uid]
        self.assertEqual(card_rarity(card,'podstawowa'),'podstawowa')
        self.assertEqual(card_rarity(card,'rzadka'),'rzadka')
        self.assertEqual(card_rarity(card,'legendarna'),'legendarna')

    def test_evolution_updates_both_authoritative_tier_and_rendered_identity(self):
        g=fixed_match(95109)
        uid=award(g,'A014',0,owner=0)
        m=g.auction_awards[uid]
        m['purchase_round']=3
        m['last_evolve_round']=3
        self.assertEqual(card_rarity(g.cards[uid],m['rarity']),'podstawowa')
        advance_rarity(g,6)
        self.assertEqual(m['rarity'],'rzadka')
        self.assertEqual(card_rarity(g.cards[uid],m['rarity']),'rzadka')
        advance_rarity(g,9)
        self.assertEqual(m['rarity'],'legendarna')
        self.assertEqual(card_rarity(g.cards[uid],m['rarity']),'legendarna')
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
