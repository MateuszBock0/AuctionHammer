"""Targeted Game Master v19 regressions, plus truthful hero HP rendering.

Only tests are added for cleansing, poison, stun and double attack.
The ability catalog, state transitions and combat engine remain unchanged.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")

import pygame
from game.core.models import Choice, IllegalMove
from test_engine import setup_game, force_unit


class HeroPresentationTests(unittest.TestCase):
    def setUp(self):
        from game.ui.app import SoloApp
        self.app_class=SoloApp
        pygame.init()
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        pygame.quit()

    def test_negative_hero_hp_is_clamped_only_in_the_visual_counter(self):
        g=self.app.game
        g.players[0].hp=-5
        display=[]
        old=self.app._text
        def watch(text,*args,**kwargs):
            display.append(str(text))
            return old(text,*args,**kwargs)
        with patch.object(self.app,"_text",side_effect=watch):
            self.app._draw_hero(0)
        self.assertIn("0/100",display)
        self.assertNotIn("-5/100",display)
        self.assertEqual(g.players[0].hp,-5)

    def test_result_screen_clamps_negative_hp_but_audit_keeps_real_value(self):
        from game.core.audit import make_report
        g=self.app.game
        g.phase="finished"
        g.winner=1
        g.players[0].hp=-5
        display=[]
        old=self.app._text
        def watch(text,*args,**kwargs):
            display.append(str(text))
            return old(text,*args,**kwargs)
        with patch.object(self.app,"_text",side_effect=watch):
            self.app._draw_gameover()
        self.assertTrue(any("GRACZ: 0 PŻ" in line for line in display))
        self.assertFalse(any("GRACZ: -5 PŻ" in line for line in display))
        self.assertEqual(make_report(g)["payload"]["summary"]["hero_hp"]["0"],-5)
        self.assertEqual(g.players[0].hp,-5)

    def test_no_change_to_nonlethal_hero_hp(self):
        self.app.game.players[0].hp=63
        lines=[]
        old=self.app._text
        with patch.object(self.app,"_text",side_effect=lambda t,*a,**k:
                          (lines.append(str(t)),old(t,*a,**k))[1]):
            self.app._draw_hero(0)
        self.assertIn("63/100",lines)


class CleansingV19Tests(unittest.TestCase):
    def test_cleansing_only_temporary_negative_status_and_not_positive(self):
        g=setup_game(18101)
        unit=force_unit(g,"S01",0)
        g._add_poison("S01",2,2,"S83")
        g._add_effect("S01","atk",2,expires=4,source="S04",positive=True)
        g._add_effect("S01","atk",-1,source="S23",positive=False) # permanent
        self.assertTrue(g._clean("S01",negative=True))
        self.assertEqual([e.kind for e in unit.effects],["atk","atk"])
        self.assertEqual([e.value for e in unit.effects],[2,-1])
        self.assertFalse(g._clean("S01",negative=True))

    def test_s07_friendly_cleanse_only_rewards_useful_cleanse(self):
        g=setup_game(18102)
        source=force_unit(g,"S07",0)
        target=force_unit(g,"S01",0)
        source.ability_level=1
        target.hp=1
        g._execute("S07","play",Choice("Oczyść własną","S01","cel"),None)
        self.assertEqual(target.hp,2) # base 1; no useful cleanse bonus
        g._add_poison("S01",2,2,"S83")
        g._execute("S07","play",Choice("Oczyść własną","S01","cel"),None)
        self.assertEqual(target.hp,4) # base 1 + level 1
        self.assertFalse(any(e.kind=="poison" for e in target.effects))

    def test_s07_enemy_cleanse_only_removes_temporary_positive_effects(self):
        g=setup_game(18103)
        source=force_unit(g,"S07",0)
        enemy=force_unit(g,"S01",1)
        source.ability_level=1
        enemy.hp=4
        g._execute("S07","play",Choice("Oczyść wrogą","S01","cel"),None)
        self.assertEqual(enemy.hp,4)
        g._add_effect("S01","atk",2,expires=4,source="S04",positive=True)
        g._add_effect("S01","atk",-1,expires=4,source="S23",positive=False)
        g._execute("S07","play",Choice("Oczyść wrogą","S01","cel"),None)
        self.assertEqual(enemy.hp,3) # upgrade only for useful enemy cleanse
        self.assertEqual([e.value for e in enemy.effects],[-1])

    def test_cleanse_respects_missing_unit(self):
        g=setup_game(18104)
        self.assertFalse(g._clean("S01",True))


class PoisonV19Tests(unittest.TestCase):
    def test_poison_ticks_bypass_shield_and_armor_and_expire(self):
        g=setup_game(18201)
        victim=force_unit(g,"S01",1)
        victim.shield=1
        victim.armor_perm=3
        g._add_poison("S01",2,2,"S83")
        self.assertEqual(victim.hp,4)
        g._tick_poison(1)
        self.assertEqual(victim.hp,2)
        self.assertEqual((victim.shield,victim.armor_perm),(1,3))
        self.assertEqual([e.remaining for e in victim.effects if e.kind=="poison"],[1])
        g._tick_poison(1)
        self.assertNotIn("S01",g.units) # 0 HP removes the card
        self.assertIn("S01",g.players[1].grave)

    def test_poison_immune_unit_rejects_it_and_no_later_tick(self):
        g=setup_game(18202)
        victim=force_unit(g,"S39",1)
        g._add_poison("S39",3,2,"S83")
        self.assertFalse(any(e.kind=="poison" for e in victim.effects))
        old=victim.hp
        g._tick_poison(1)
        self.assertEqual(victim.hp,old)

    def test_aura_immunity_prevents_poison_until_expiry(self):
        g=setup_game(18203)
        victim=force_unit(g,"S01",1)
        g._grant_immunity("S01",("poison",),source="S64")
        g._add_poison("S01",2,2,"S83")
        self.assertFalse(any(e.kind=="poison" for e in victim.effects))


class StunV19Tests(unittest.TestCase):
    def test_stun_blocks_attack_and_expires_at_end_of_own_turn(self):
        g=setup_game(18301)
        victim=force_unit(g,"S09",0)
        victim.played_turn=0
        self.assertEqual(g.legal_attacks("S09"),["hero:1"])
        g._add_effect("S09","stun",expires=1,source="S59",positive=False)
        self.assertEqual(g.legal_attacks("S09"),[])
        g.end_turn()
        self.assertFalse(any(e.kind=="stun" for e in victim.effects))
        g.active=0
        g.players[0].turn_count=2
        self.assertEqual(g.legal_attacks("S09"),["hero:1"])

    def test_stun_immunity_prevents_application(self):
        g=setup_game(18302)
        victim=force_unit(g,"S09",0)
        g._grant_immunity("S09",("stun",),source="S88")
        ok=g._add_effect("S09","stun",expires=2,source="S59",positive=False)
        self.assertFalse(ok)
        self.assertFalse(any(e.kind=="stun" for e in victim.effects))


class DoubleAttackV19Tests(unittest.TestCase):
    def test_s115_two_legal_attacks_third_rejected(self):
        g=setup_game(18401)
        u=force_unit(g,"S115",0)
        u.played_turn=0
        for _ in range(2):
            self.assertIn("hero:1",g.legal_attacks("S115"))
            g.attack("S115","hero:1")
        self.assertEqual(u.attacks,2)
        self.assertEqual(g.legal_attacks("S115"),[])
        with self.assertRaises(IllegalMove):
            g.attack("S115","hero:1")

    def test_s79_conditionally_unlocks_only_second_attack(self):
        g=setup_game(18402)
        u=force_unit(g,"S79",0)
        u.played_turn=0
        self.assertFalse(g._double(u))
        g.attack("S79","hero:1")
        self.assertTrue(g._double(u))
        self.assertIn("hero:1",g.legal_attacks("S79"))
        g.attack("S79","hero:1")
        self.assertEqual(g.legal_attacks("S79"),[])

    def test_s67_grants_double_to_selected_ally_not_every_ally(self):
        g=setup_game(18403)
        source=force_unit(g,"S67",0)
        recipient=force_unit(g,"S09",0)
        other=force_unit(g,"S10",0)
        recipient.played_turn=0
        other.played_turn=0
        g._execute("S67","play",Choice("board_double","S09","cel"),None)
        self.assertTrue(g._double(recipient))
        self.assertFalse(g._double(other))
        for _ in range(2):
            self.assertIn("hero:1",g.legal_attacks("S09"))
            g.attack("S09","hero:1")
        self.assertEqual(g.legal_attacks("S09"),[])

    def test_double_attack_does_not_bypass_stun_or_summoning_sickness(self):
        g=setup_game(18404)
        u=force_unit(g,"S115",0)
        u.played_turn=g.players[0].turn_count
        self.assertEqual(g.legal_attacks("S115"),[])
        u.played_turn=0
        g._add_effect("S115","stun",expires=1,source="S59",positive=False)
        self.assertEqual(g.legal_attacks("S115"),[])


if __name__=="__main__":
    unittest.main()
