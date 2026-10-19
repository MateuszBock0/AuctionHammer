"""v23 focused mechanical/UI regression: verified defects only."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game.core.engine import Match
from game.core.models import Choice
from game.core.effects import options
from game.core.auction_abilities import global_trigger_block
from game.core.persistence import save_match,load_match
from test_auction_v22_0931 import ready,award,choose
from test_auction_v4_engine import place_basic


class V23EconomyAfterAtomicDeathWave(unittest.TestCase):
    def test_A003_death_revive_after_end_turn_counts_final_board_and_save_resume(self):
        g=ready(230100)
        self.assertEqual(g.ruleset_version,'v23')
        monster=award(g,'A003',1,zone='board')
        rescued=place_basic(g,'S01',0,'grave')
        g.units[monster].hp=0
        g._finalize_end_turn()
        self.assertEqual(g.slot_income[0],0)
        self.assertEqual(g.pending_vacant_income,0)
        g._drain()
        self.assertIsNotNone(g.pending)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'pending.json'
            save_match(g,path)
            g=load_match(path)
        choose(g,'revive_one',rescued)
        self.assertIn(rescued,g.players[0].board)
        self.assertEqual(g.slot_income[0],4)
        self.assertEqual(g.slot_income_turns[0],1)
        self.assertIsNone(g.pending_vacant_income)
        g.assert_integrity()

    def test_A001_capture_after_death_is_paid_only_on_final_board(self):
        g=ready(230101)
        assassin=award(g,'A001',1,zone='board')
        captured=place_basic(g,'S09',1)
        g.units[assassin].hp=0
        g._finalize_end_turn()
        g._drain()
        self.assertIsNotNone(g.pending)
        choose(g,'capture',captured)
        self.assertIn(captured,g.players[0].board)
        self.assertEqual(g.slot_income[0],4)
        g.assert_integrity()

    def test_archived_ruleset_keeps_historical_income_policy(self):
        g=ready(230102)
        g.ruleset_version='v22'
        g._finalize_end_turn()
        self.assertEqual(g.slot_income[0],5)
        self.assertIsNone(g.pending_vacant_income)


class V23OpposingA015(unittest.TestCase):
    def test_legendary_cancels_enemy_only_even_if_both_have_ward(self):
        g=ready(230110)
        ward0=award(g,'A015',2,owner=0,zone='board',n=1)
        # In real matches the bought archetype is unique. An opposing
        # Wieszczka requires a copied/captured instance. This synthetic
        # second instance is deliberately NOT another auction purchase.
        from game.core.models import Card,Unit
        uid='COPY0000001'
        original=g.cards[ward0]
        g.cards[uid]=Card(uid,original.definition,owner=1,zone='board')
        g.defs[uid]=original.definition
        g.ephemeral_ids.add(uid)
        g.auction_awards[uid]=dict(g.auction_awards[ward0],ephemeral=True)
        g.players[1].board.append(uid)
        old=g.units[ward0]
        g.units[uid]=Unit(uid,1,old.atk,old.max_hp,old.hp,old.ability_level,0)
        ward1=uid
        self.assertTrue(global_trigger_block(g,'play',0))
        self.assertTrue(global_trigger_block(g,'play',1))
        g.units[ward1].effects.append(
            __import__('game.core.models',fromlist=['Effect']).Effect('silence',0))
        self.assertFalse(global_trigger_block(g,'play',0))
        self.assertTrue(global_trigger_block(g,'play',1))

    def test_friendly_end_trigger_survives_friendly_legendary_ward(self):
        g=ready(230111)
        award(g,'A015',2,owner=0,zone='board')
        place_basic(g,'S27',0)
        old=g.players[1].hp
        g.end_turn()
        self.assertLess(g.players[1].hp,old)
        g.assert_integrity()


class V23FallbackCards(unittest.TestCase):
    def test_S86_S87_S88_no_ally_are_real_death_wave_fallbacks(self):
        for card in ('S86','S87','S88'):
            with self.subTest(card=card):
                g=ready(230120)
                place_basic(g,card,0)
                g.players[0].hp=70
                g._damage(card,1000,ignore_defense=True)
                g._drain()
                if card=='S86':self.assertEqual(g.players[0].hero_armor,3)
                elif card=='S87':self.assertEqual(g.players[0].hp,74)
                else:self.assertEqual(g.players[0].hero_shield,1)
                g.assert_integrity()

    def test_enemy_rare_warden_stops_S86_death_fallback(self):
        g=ready(230121)
        award(g,'A015',1,owner=1,zone='board')
        place_basic(g,'S86',0)
        g._damage('S86',1000,ignore_defense=True)
        g._drain()
        self.assertEqual(g.players[0].hero_armor,0)

    def test_S32_fallback_only_when_all_enemies_already_poisoned_by_source(self):
        g=ready(230122)
        place_basic(g,'S32',0)
        target=place_basic(g,'S01',1)
        g._add_poison(target,1,2,'S32',0)
        target_hp=g.units[target].hp
        choices=options(g,'S32','end')
        self.assertEqual(len(choices),1)
        self.assertEqual(choices[0].mode,'auto')
        g._execute('S32','end',choices[0])
        self.assertEqual(g.units[target].hp,target_hp-2)
        self.assertEqual(sum(e.kind=='poison' for e in g.units[target].effects),1)

    def test_S95_fallback_does_not_change_previous_stun_target(self):
        g=ready(230123)
        place_basic(g,'S95',0)
        victim=place_basic(g,'S01',1)
        g.units['S95'].last_stun_target=victim
        g.units['S95'].last_stun_turn=g.players[0].turn_count-1
        hp=g.units[victim].hp
        g._execute('S95','end',Choice('auto',None,''))
        self.assertEqual(g.units[victim].hp,hp-2)
        self.assertEqual(g.units['S95'].last_stun_target,victim)


class V23A018(unittest.TestCase):
    def test_last_auction_legendary_permanently_grows_without_voucher(self):
        g=ready(230130)
        card=award(g,'A018',2,owner=0,zone='hand')
        initial=g.cards[card].attack,g.cards[card].max_hp
        # Keep the actual 17-card supply integral; isolate structural
        # "no future auction" eligibility as an independent condition.
        with patch('game.core.auction_abilities.any_future_auction',return_value=False):
            g.play(card)
        self.assertEqual((g.units[card].atk,g.units[card].max_hp),
                         (initial[0]+5,initial[1]+5))
        self.assertFalse(g.auction_vouchers[0])
        g.assert_integrity()

    def test_future_auction_keeps_legendary_guarantee(self):
        g=ready(230131)
        card=award(g,'A018',2,owner=0,zone='hand')
        g.play(card)
        self.assertTrue(g.auction_vouchers[0][0]['guaranteed'])
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
