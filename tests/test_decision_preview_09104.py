"""0.9.104: decision aids are accurate, conservative, read-only, and clickable.

Test hero/unit defense, double hits, aura-replacement warning, both-sided
scaled/legacy brawl indicators, live hover previews, and no UI-driven actions.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
import pygame

from game.core.audit import state_snapshot
from game.ui.app import SoloApp
from game.ui.decision_preview import (
    hit_projection,preview_standard_attack,preview_replacement,
    next_brawl_damage,brawl_at_risk,
)
from test_balance_buff_v24_0990 import ready,starter


class DecisionPreview09104(TestCase):
    @staticmethod
    def scene(seed):
        g=ready(seed)
        g.tavern_beer_enabled=True
        g.tavern_scaled_damage_enabled=True
        a=starter(g,'S01',0)
        b=starter(g,'S12',1)
        return g,a,b

    def test_damage_calculations_mirror_shield_armor_and_hp(self):
        g,a,b=self.scene(914001)
        u=g.units[b]
        u.hp=8
        u.shield=1
        u.armor_perm=3
        p=hit_projection(u,9)
        self.assertEqual((p.hp_loss,p.after_hp,p.absorbed,p.blocked_by_shield),
                         (0,8,9,True))
        u.shield=0
        p=hit_projection(u,9)
        self.assertEqual((p.hp_loss,p.after_hp,p.absorbed,p.blocked_by_shield),
                         (6,2,3,False))
        u.armor_perm=0
        p=hit_projection(u,9)
        self.assertEqual((p.hp_loss,p.after_hp),(9,-1))

    def test_attack_only_when_legal_and_both_standard_hits(self):
        g,a,b=self.scene(914002)
        g.units[a].base_attack=5
        g.units[b].base_attack=3
        g.units[a].hp=9
        g.units[b].hp=9
        g.units[b].armor_temp=2
        p=preview_standard_attack(g,a,b)
        self.assertIsNotNone(p)
        self.assertEqual((p.strike.raw,p.strike.hp_loss,p.strike.after_hp),
                         (5,3,6))
        self.assertEqual((p.counter.raw,p.counter.hp_loss,p.counter.after_hp),
                         (3,3,6))
        self.assertIsNone(preview_standard_attack(g,b,a))
        g.units[a].attacks=1
        self.assertIsNone(preview_standard_attack(g,a,b))

    def test_hero_preview_shield_and_armor_no_counterattack(self):
        g,a,b=self.scene(914003)
        g.units[a].base_attack=12
        enemy=g.players[1]
        enemy.hero_shield=1
        enemy.hero_armor=3
        p=preview_standard_attack(g,a,'hero:1')
        self.assertIsNone(p.counter)
        self.assertEqual(p.strike.hp_loss,0)
        self.assertTrue(p.strike.blocked_by_shield)
        enemy.hero_shield=0
        p=preview_standard_attack(g,a,'hero:1')
        self.assertEqual(p.strike.hp_loss,9)
        self.assertEqual(p.strike.after_hp,enemy.hp-9)

    def test_replacement_only_on_full_board_and_legal_choice(self):
        g,a,b=self.scene(914004)
        incoming=starter(g,'S20',0,zone='hand')
        self.assertIsNone(preview_replacement(g,incoming,a))
        for cid in ('S02','S03','S04','S05'):
            starter(g,cid,0)
        self.assertEqual(len(g.players[0].board),5)
        p=preview_replacement(g,incoming,a)
        self.assertIsNotNone(p)
        self.assertEqual(p.old_atk,g.units[a].atk)
        self.assertEqual(p.new_atk,g.cards[incoming].attack)
        self.assertEqual(p.new_hp,g.cards[incoming].max_hp)
        g.units[a].attacks=1
        self.assertIsNone(preview_replacement(g,incoming,a))
        g.units[a].attacks=0
        g.players[0].played_this_turn=True
        self.assertIsNone(preview_replacement(g,incoming,a))

    def test_brawl_lethal_markers_on_both_boards_and_legacy(self):
        g,a,b=self.scene(914005)
        g.beer_turns_remaining=3
        g.units[a].hp=2
        g.units[b].hp=3
        self.assertTrue(brawl_at_risk(g,a))
        self.assertTrue(brawl_at_risk(g,b))
        g.units[b].shield=1
        self.assertFalse(brawl_at_risk(g,b))
        g.units[b].shield=0
        g.units[b].armor_perm=2
        self.assertFalse(brawl_at_risk(g,b))
        g.tavern_scaled_damage_enabled=False
        self.assertEqual(next_brawl_damage(g),1)
        self.assertFalse(brawl_at_risk(g,a))
        g.units[a].hp=1
        self.assertTrue(brawl_at_risk(g,a))
        g.beer_turns_remaining=0
        self.assertFalse(brawl_at_risk(g,a))

    def test_pure_engine_state_and_rng_not_modified_by_previews(self):
        g,a,b=self.scene(914006)
        g.beer_turns_remaining=3
        g.units[a].hp=2
        snapshot=state_snapshot(g)
        rng=g.rng.getstate()
        for _ in range(10):
            self.assertIsNotNone(preview_standard_attack(g,a,b))
            brawl_at_risk(g,a)
            next_brawl_damage(g)
        self.assertEqual(snapshot,state_snapshot(g))
        self.assertEqual(rng,g.rng.getstate())


class DecisionPreviewCanvas09104(TestCase):
    def setUp(self):
        pygame.font.init()

    def fixture(self,seed=914010):
        g=ready(seed)
        g.tavern_scaled_damage_enabled=True
        g.tavern_beer_enabled=True
        a=starter(g,'S01',0)
        b=starter(g,'S12',1)
        class Fake:
            FIRST_X,SLOT_W,SLOT_H,SLOT_GAP,OWN_Y,OPP_Y=107,148,220,26,431,152
            DRAG_THRESHOLD_SQ=100
            _draw_brawl_risk_badges=SoloApp._draw_brawl_risk_badges
            _draw_decision_preview=SoloApp._draw_decision_preview
            slot_rect=SoloApp.slot_rect
            hero_rect=SoloApp.hero_rect
            target_under=SoloApp.target_under
            mouse_pos=lambda self:self.pointer
            _bonus_selection_due=lambda self:False
            _panel=lambda self,rect,*a,**kw:pygame.draw.rect(
                self.screen,(72,55,38),rect,border_radius=8)
            _text=lambda self,*a,**kw:None

        f=Fake()
        f.game=g
        f.screen=pygame.Surface((1480,980))
        f.screen.fill((11,13,17))
        f.fonts={n:pygame.font.Font(None,n) for n in (13,15)}
        f.cards_view=SimpleNamespace(clip=lambda text,font,width:text)
        f.pointer=SoloApp.slot_rect(f,1,g.slot_of(b)).center
        f.selected=a
        f.drag_start=None
        f.drag_pointer=None
        f.menu_open=False
        f.history_open=False
        f.help_open=False
        f.replay_index=None
        f.details_card=None
        f.confirm_action=None
        f.tutorial_welcome_open=False
        return f,a,b

    def test_selected_attack_shows_sidebar_panel_not_card(self):
        f,a,b=self.fixture()
        SoloApp._draw_decision_preview(f)
        self.assertNotEqual(f.screen.get_at((1110,300)),(11,13,17,255))
        for p in ((200,210),(200,510),(800,400)):
            self.assertEqual(f.screen.get_at(p),(11,13,17,255))
        f.pointer=(15,15)
        f.screen.fill((11,13,17))
        SoloApp._draw_decision_preview(f)
        self.assertEqual(f.screen.get_at((1110,300)),(11,13,17,255))

    def test_dragging_attacker_and_legal_replacement_render(self):
        f,a,b=self.fixture(914011)
        f.drag_start=(100,100),a
        f.drag_pointer=f.pointer
        SoloApp._draw_decision_preview(f)
        self.assertNotEqual(f.screen.get_at((1110,300)),(11,13,17,255))
        g=f.game
        f.drag_start=None
        hand=starter(g,'S20',0,zone='hand')
        for cid in ('S02','S03','S04','S05'):
            starter(g,cid,0)
        f.selected=hand
        f.pointer=SoloApp.slot_rect(f,0,g.slot_of(a)).center
        f.screen.fill((11,13,17))
        SoloApp._draw_decision_preview(f)
        self.assertNotEqual(f.screen.get_at((1110,300)),(11,13,17,255))
        g.units[a].attacks=1
        f.screen.fill((11,13,17))
        SoloApp._draw_decision_preview(f)
        self.assertEqual(f.screen.get_at((1110,300)),(11,13,17,255))

    def test_brawl_risk_badges_are_outside_cards_even_without_animation(self):
        f,a,b=self.fixture(914012)
        f.game.beer_turns_remaining=3
        f.game.units[a].hp=1
        f.game.units[b].hp=2
        f.animations_enabled=False
        SoloApp._draw_brawl_risk_badges(f)
        own=SoloApp.slot_rect(f,0,f.game.slot_of(a))
        foe=SoloApp.slot_rect(f,1,f.game.slot_of(b))
        for rect in (own,foe):
            self.assertNotEqual(f.screen.get_at((rect.right+10,rect.y+6)),
                                (11,13,17,255))
            self.assertEqual(f.screen.get_at(rect.center),(11,13,17,255))
        f.game.beer_turns_remaining=0
        f.screen.fill((11,13,17))
        SoloApp._draw_brawl_risk_badges(f)
        self.assertEqual(f.screen.get_at((own.right+10,own.y+6)),
                         (11,13,17,255))

    def test_modal_prevents_prediction_drawing(self):
        for prop in ('menu_open','history_open','help_open','details_card',
                     'confirm_action','tutorial_welcome_open','replay_index'):
            f,a,b=self.fixture(914013)
            setattr(f,prop,0 if prop=='replay_index' else True)
            SoloApp._draw_decision_preview(f)
            self.assertEqual(f.screen.get_at((1110,300)),(11,13,17,255))


if __name__=='__main__':
    import unittest
    unittest.main()
