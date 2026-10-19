"""Forensic regression for actual defects found in 100 v22 archived matches.

Tests reproduce missed quality poison on hero, pre-selection A015 blocking,
wrong S85 UI label, and the auction AI's old HP-only prioritization.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from game.core.ai import ComputerOpponent
from game.core.auction import AuctionOffer
from game.core.audit import state_snapshot, make_report, verify_replay
from game.core.persistence import load_match, save_match
from test_auction_v22_0931 import ready,award,choose
from test_auction_v4_engine import place_basic


def choose_target(game,mode,target):
    choices=[i for i,c in enumerate(game.pending.choices)
             if c.mode==mode and c.target==target]
    assert len(choices)==1,(mode,target,game.pending.choices)
    game.choose(choices[0])


class S11QualityPoisonOnHero(unittest.TestCase):
    def test_actual_attack_ticks_once_at_each_quality_level(self):
        for level in (0,1,2):
            with self.subTest(level=level):
                g=ready(934100+level)
                snake=place_basic(g,'S11',0)
                g.units[snake].ability_level=level
                g.active=0
                old=g.players[1].hp
                self.assertIn('hero:1',g.legal_attacks(snake))
                g.attack(snake,'hero:1')
                after_attack=g.players[1].hp
                self.assertLess(after_attack,old)
                statuses=[e for e in g.players[1].hero_effects if e.kind=='poison']
                self.assertEqual(len(statuses),1)
                self.assertEqual(statuses[0].bonus_once,level)
                self.assertEqual(statuses[0].initial_ticks,2)
                g._tick_poison(1)
                g._tick_poison(1)
                self.assertEqual(after_attack-g.players[1].hp,2+level)
                self.assertFalse(any(e.kind=='poison' for e in g.players[1].hero_effects))
                g.assert_integrity()

    def test_unit_poison_stays_consistent_with_hero_poison(self):
        for level in (0,1,2):
            g=ready(934110+level)
            snake=place_basic(g,'S11',0)
            victim=place_basic(g,'S33',1)
            g.units[victim].base_max_hp=25
            g.units[victim].hp=25
            g._add_poison(victim,1,2,snake,level)
            old=g.units[victim].hp
            g._tick_poison(1)
            g._tick_poison(1)
            self.assertEqual(old-g.units[victim].hp,2+level)
            g.assert_integrity()


class A015ChosenEffectRegression(unittest.TestCase):
    def setUp(self):
        self.g=ready(934150)
        self.warden=award(self.g,'A015',0,owner=1,zone='board')
        self.ally=place_basic(self.g,'S33',0)
        self.enemy=place_basic(self.g,'S01',1)
        self.g.units[self.enemy].base_max_hp=20
        self.g.units[self.enemy].hp=20
        self.g.active=0

    def test_S04_friendly_buff_allowed_without_consuming_ward(self):
        g=self.g
        place_basic(g,'S04',0,'hand')
        old=g.units[self.ally].atk
        g.play('S04')
        self.assertIsNotNone(g.pending)
        self.assertNotIn(self.warden,g.auction_blocked_play)
        choose_target(g,'Wzmocnij',self.ally)
        self.assertEqual(g.units[self.ally].atk,old+1)
        self.assertNotIn(self.warden,g.auction_blocked_play)
        g.assert_integrity()

    def test_S04_enemy_nerf_cancelled_after_actual_selection_once(self):
        g=self.g
        place_basic(g,'S04',0,'hand')
        old=g.units[self.enemy].atk
        g.play('S04')
        self.assertIsNotNone(g.pending)
        choose_target(g,'Osłab',self.enemy)
        self.assertEqual(g.units[self.enemy].atk,old)
        self.assertIn(self.warden,g.auction_blocked_play)
        g.players[0].played_this_turn=False
        place_basic(g,'S08',0,'hand')
        oldhp=g.units[self.enemy].max_hp
        g.play('S08')
        choose_target(g,'Osłab',self.enemy)
        self.assertEqual(g.units[self.enemy].max_hp,oldhp-4)
        g.assert_integrity()

    def test_S08_friendly_health_buff_allowed(self):
        g=self.g
        place_basic(g,'S08',0,'hand')
        old=g.units[self.ally].max_hp
        g.play('S08')
        self.assertIsNotNone(g.pending)
        choose_target(g,'Wzmocnij',self.ally)
        self.assertEqual(g.units[self.ally].max_hp,old+4)
        self.assertNotIn(self.warden,g.auction_blocked_play)
        g.assert_integrity()

    def test_pending_choice_survives_save_reload_and_consumes_ward_once(self):
        g=self.g
        place_basic(g,'S04',0,'hand')
        g.play('S04')
        self.assertIsNotNone(g.pending)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'save.json'
            save_match(g,file)
            g=load_match(file)
        self.assertIsNotNone(g.pending)
        old=g.units[self.enemy].atk
        choose_target(g,'Osłab',self.enemy)
        self.assertEqual(g.units[self.enemy].atk,old)
        self.assertEqual(len(g.auction_blocked_play),1)
        g.assert_integrity()

    def test_forced_hostile_S01_still_blocked_on_play(self):
        g=self.g
        place_basic(g,'S01',0,'hand')
        # Move earlier enemy S01 from board to reserve to avoid duplicated uid:
        # an existing basic ID is unique. Pick another enemy for this case.
        # The target list contains exactly one hostile target after setup.
        self.assertTrue(g.units)
        # S01's target options all hit enemy; A015 can cancel immediately.
        g.play('S01')
        self.assertIsNone(g.pending)
        self.assertIn(self.warden,g.auction_blocked_play)
        g.assert_integrity()


class S85DeathFallbackText(unittest.TestCase):
    def test_fallback_describes_real_heal_amount(self):
        from game.core.effects import options
        for level in (0,1,2):
            g=ready(934160+level)
            ghost=place_basic(g,'S85',0)
            g.units[ghost].ability_level=level
            choices=options(g,ghost,'death')
            self.assertEqual(len(choices),1)
            self.assertEqual(choices[0].target,'hero:0')
            self.assertIn(str(4+level),choices[0].label)
            self.assertIn('Ulecz',choices[0].label)
            g.assert_integrity()


class AuctionAiValuationRegression(unittest.TestCase):
    def test_v22_attack_and_mass_kill_count_more_than_raw_hp(self):
        g=ready(934170)
        bot=ComputerOpponent(0,'normalny')
        # Both are same ATK+HP, as mandated by catalogue.
        hp_dummy=AuctionOffer('HP',15,2,'podstawowa',1,'A005')
        mass_kill=AuctionOffer('KILL',9,8,'podstawowa',1,'A011')
        self.assertGreater(bot.auction_offer_value(g,mass_kill),
                           bot.auction_offer_value(g,hp_dummy))

    def test_extra_auction_card_synergy_responds_to_board(self):
        g=ready(934171)
        bot=ComputerOpponent(0,'trudny')
        offer=AuctionOffer('KILL',8,7,'rzadka',2,'A011')
        before=bot.auction_offer_value(g,offer)
        place_basic(g,'S01',1)
        self.assertGreater(bot.auction_offer_value(g,offer),before)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
