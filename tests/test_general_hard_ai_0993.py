"""AuctionHammer 0.9.93: General never buffs enemy in NEW signed games.

Also prove the hard bot actually reasons across all legal attackers.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from game.core import auction_abilities as aa
from game.core.ai import ComputerOpponent
from game.core.audit import state_snapshot
from game.core.persistence import save_match,load_match
from game.core.auction_catalog import RARITIES,v23_variant
from game.ui.aura_links import live_aura_links
from game.core.models import Choice
from test_balance_buff_v24_0990 import ready,award,starter


class GeneralOwnerOnly0993(unittest.TestCase):
    def test_basic_allies_only_both_sides_and_rendered_aura(self):
        for owner in (0,1):
            with self.subTest(owner=owner):
                g=ready(99310+owner)
                self.assertTrue(g.general_friendly_only)
                src=award(g,'A002',0,owner=owner,zone='board')
                ally=starter(g,'S01',owner)
                enemy=starter(g,'S12',1-owner)
                g._update_auras()
                self.assertEqual(g.units[src].aura_atk,1)
                self.assertEqual(g.units[ally].aura_atk,1)
                self.assertEqual(g.units[enemy].aura_atk,0)
                outgoing=live_aura_links(g,src)
                self.assertEqual({l.target for l in outgoing},{src,ally})
                self.assertFalse(any(l.source==src for l in live_aura_links(g,enemy)))
                g.assert_integrity()

    def test_rare_chooses_only_own_and_defends_only_self(self):
        g=ready(99321)
        src=award(g,'A002',1,zone='board')
        ally=starter(g,'S01')
        enemy=starter(g,'S12',1)
        available=aa.options(g,src,'play')
        self.assertTrue(available)
        self.assertTrue(all(x.target in g.players[0].board for x in available
                            if x.target is not None))
        self.assertFalse(any(x.target==enemy for x in available))
        ownbefore=g.units[ally].atk
        aa.execute(g,src,'play',Choice('general_target',ally,''))
        self.assertTrue(aa.boosted_attack(g,ally))
        self.assertFalse(aa.boosted_attack(g,enemy))
        self.assertEqual(g.units[src].armor_perm,2)
        self.assertEqual(g.units[src].shield,1)
        self.assertEqual(g.units[enemy].armor_perm,0)
        self.assertEqual(g.units[ally].atk,ownbefore)
        g.assert_integrity()

    def test_legendary_only_new_allies_and_not_old_or_enemy(self):
        g=ready(99332)
        src=award(g,'A002',2,zone='board')
        old=starter(g,'S01')
        enemy=starter(g,'S12',1)
        aa.execute(g,src,'play',Choice('auto',None,''))
        self.assertEqual(g.units[src].armor_perm,4)
        self.assertFalse(aa.boosted_attack(g,enemy))
        self.assertFalse(aa.boosted_attack(g,old))
        newcomer=starter(g,'S02')
        aa.mark_general_new_ally(g,newcomer)
        aa.mark_general_new_ally(g,enemy)
        self.assertIn(newcomer,g.auction_general_grants[src])
        self.assertNotIn(enemy,g.auction_general_grants[src])
        self.assertTrue(aa.boosted_attack(g,newcomer))
        self.assertFalse(aa.boosted_attack(g,enemy))
        # Even stale/corrupted grant maps may not enable an enemy bonus.
        g.auction_general_grants[src].add(enemy)
        self.assertFalse(aa.boosted_attack(g,enemy))
        g.assert_integrity()

    def test_historical_general_remains_global_with_explicit_legacy_rule(self):
        g=ready(99340)
        g.general_friendly_only=False
        src=award(g,'A002',0,zone='board')
        ally=starter(g,'S01')
        enemy=starter(g,'S12',1)
        g._update_auras()
        self.assertEqual(g.units[ally].aura_atk,1)
        self.assertEqual(g.units[enemy].aura_atk,1)
        self.assertNotIn('general_friendly_only',
                         state_snapshot(g)['ruleset_state'])
        with TemporaryDirectory() as d:
            p=Path(d)/'old.json'
            save_match(g,p)
            copy=load_match(p)
            self.assertFalse(copy.general_friendly_only)
            self.assertEqual(state_snapshot(copy),state_snapshot(g))

    def test_new_signed_rule_is_visible_and_legacy_description_preserved(self):
        g=ready(99350)
        self.assertIs(state_snapshot(g)['ruleset_state']['general_friendly_only'],True)
        new=v23_variant('v22','A002','podstawowa','v23',True)
        old=v23_variant('v22','A002','podstawowa','v23',False)
        self.assertIn('własnej planszy',new)
        self.assertIn('obu planszach',old)
        self.assertNotEqual(old,new)
        self.assertNotIn('wrogie',new)
        rare=v23_variant('v22','A002','rzadka','v23',True)
        legendary=v23_variant('v22','A002','legendarna','v23',True)
        self.assertIn('własna jednostka',rare)
        self.assertIn('zagrana przez Ciebie',legendary)

    def test_legacy_save_without_marker_restores_old_behavior(self):
        g=ready(99351)
        g.general_friendly_only=False
        src=award(g,'A002',0,zone='board')
        starter(g,'S12',1)
        g._update_auras()
        self.assertFalse(g.general_friendly_only)
        self.assertEqual(g.units['S12'].aura_atk,1)


class HardCombat0993(unittest.TestCase):
    def test_expert_chooses_lethal_attacker_not_first_weak_unit(self):
        g=ready(99360)
        weaker=starter(g,'S01')
        killer=starter(g,'S02')
        g.units[weaker].base_attack=1
        g.units[killer].base_attack=12
        g.players[1].hp=8
        bot=ComputerOpponent(0,'trudny')
        choice=bot.hard_attack_choice(g)
        self.assertEqual(choice,(killer,'hero:1'))
        before=len(g.audit_actions)
        bot.step(g)
        self.assertEqual(len(g.audit_actions),before+1)
        self.assertLessEqual(g.players[1].hp,0)

    def test_expert_shield_break_with_smallest_first_hit(self):
        g=ready(99361)
        weaker=starter(g,'S01')
        stronger=starter(g,'S02')
        g.units[weaker].base_attack=1
        g.units[stronger].base_attack=10
        g.players[1].hp=7
        g.players[1].hero_shield=1
        self.assertEqual(ComputerOpponent(0,'trudny').hard_attack_choice(g),
                         (weaker,'hero:1'))

    def test_expert_avoids_suicide_when_safe_attack_exists(self):
        g=ready(99362)
        actor=starter(g,'S01')
        g.units[actor].base_attack=8
        g.units[actor].hp=3
        scary=starter(g,'S12',1)
        easy=starter(g,'S09',1)
        g.units[scary].hp=7
        g.units[scary].base_attack=13
        g.units[easy].hp=5
        g.units[easy].base_attack=1
        choice=ComputerOpponent(0,'trudny').hard_attack_choice(g)
        self.assertEqual(choice,(actor,easy))

    def test_easy_and_normal_still_keep_their_original_decision_policy(self):
        g=ready(99363)
        starter(g,'S01')
        self.assertIsNone(ComputerOpponent(0,'łatwy').hard_attack_choice(g))
        self.assertIsNone(ComputerOpponent(0,'normalny').hard_attack_choice(g))


if __name__=='__main__':
    unittest.main()
