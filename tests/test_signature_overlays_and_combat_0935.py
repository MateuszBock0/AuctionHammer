"""0.9.35: restrained signature-trait overlays and truthful combat visuals.

All visual frames are sourced from real committed states; nothing changes HP
or causes dead units to remain in the game engine.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.status_view import VisibleStatus
from game.ui.card_view import CardView
from game.ui.combat_visuals import CombatVisuals
from game.ui.app import SoloApp
from test_engine import setup_game,force_unit


def status(name):
    return VisibleStatus(name,name,name,name)


class SignatureCardTintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.view=CardView()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_exactly_three_allowed_tints_and_priority(self):
        self.assertIsNone(CardView.board_tint([]))
        self.assertIsNone(CardView.board_tint([status('stun'),status('poison'),
                                              status('quick'),status('regen')]))
        red=CardView.board_tint([status('double')])
        silver=CardView.board_tint([status('taunt')])
        yellow=CardView.board_tint([status('shield')])
        self.assertEqual(red[:3],(227,69,78))
        self.assertEqual(silver[:3],(184,192,205))
        self.assertEqual(yellow[:3],(255,210,64))
        self.assertLessEqual(max(red[3],silver[3],yellow[3]),45)
        self.assertEqual(CardView.board_tint([status('double'),status('taunt')]),silver)
        self.assertEqual(CardView.board_tint([status('double'),status('shield')]),yellow)
        self.assertEqual(CardView.board_tint([status('taunt'),status('shield')]),yellow)

    def test_board_overlay_modifies_card_pixels_but_not_plain_or_temporary(self):
        game=setup_game(935200)
        unit=force_unit(game,'S01',0)
        rect=pygame.Rect(9,9,148,220)
        def pixel_for(statuses):
            surf=pygame.Surface((190,250),pygame.SRCALPHA)
            self.view.draw(surf,game.cards['S01'],rect,unit,statuses=statuses)
            return surf.get_at((rect.x+80,rect.y+90))
        base=pixel_for(())
        self.assertEqual(base,pixel_for((status('poison'),status('stun'))))
        self.assertNotEqual(base,pixel_for((status('double'),)))
        self.assertNotEqual(base,pixel_for((status('taunt'),)))
        self.assertNotEqual(base,pixel_for((status('shield'),)))

    def test_hp_override_is_visual_only(self):
        game=setup_game(935201)
        unit=force_unit(game,'S01',0)
        surf=pygame.Surface((190,250),pygame.SRCALPHA)
        self.view.draw(surf,game.cards['S01'],pygame.Rect(9,9,148,220),
                       unit,hp_override=0)
        self.assertGreater(unit.hp,0)
        self.assertEqual(unit.hp,game.cards['S01'].max_hp)


class CombatAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    @staticmethod
    def slot(owner,slot):
        return pygame.Rect(110+slot*176,431 if owner==0 else 152,148,220)

    @staticmethod
    def hero(owner):
        return pygame.Rect(110,662 if owner==0 else 98,935,44)

    def test_attacker_and_defender_highlight_and_hp_animates_after_confirmed_hit(self):
        g=setup_game(935220)
        a=force_unit(g,'S09',0)
        target=force_unit(g,'S01',1)
        a.played_turn=0
        target.base_max_hp=35
        target.hp=35
        v=CombatVisuals()
        v.sync(g,self.slot,self.hero,0)
        g.attack('S09','S01')
        v.sync(g,self.slot,self.hero,100)
        self.assertIn('S09',v.combat_cards)
        self.assertIn('S01',v.combat_cards)
        transition=v.combat_cards['S01']
        self.assertLess(transition.new_hp,transition.old_hp)
        self.assertEqual(v.interpolated_hp(transition,100),transition.old_hp)
        self.assertEqual(v.interpolated_hp(transition,340),transition.new_hp)
        self.assertEqual(g.units['S01'].hp,transition.new_hp)
        canvas=pygame.Surface((1480,980),pygame.SRCALPHA)
        v.draw_cards(canvas,g,CardView(),200)

    def test_fatal_damage_grays_card_before_disappearing_without_resurrecting(self):
        g=setup_game(935221)
        attacker=force_unit(g,'S09',0)
        victim=force_unit(g,'S01',1)
        attacker.played_turn=0
        victim.hp=2
        v=CombatVisuals()
        v.sync(g,self.slot,self.hero,0)
        g.attack('S09','S01')
        self.assertNotIn('S01',g.units)
        v.sync(g,self.slot,self.hero,100)
        ghosts=[x for x in v.fallen_cards if x.uid=='S01']
        self.assertEqual(len(ghosts),1)
        ghost=ghosts[0]
        self.assertEqual(v.interpolated_hp(ghost,100),2)
        self.assertEqual(v.interpolated_hp(ghost,340),0)
        self.assertEqual(ghost.old_hp,2)
        surf=pygame.Surface((1480,980),pygame.SRCALPHA)
        v.draw_cards(surf,g,CardView(),390)
        self.assertNotIn('S01',g.units)
        v.sync(g,self.slot,self.hero,600)
        self.assertFalse(v.fallen_cards)

    def test_nonfatal_board_disappearance_is_not_false_death_animation(self):
        g=setup_game(935222)
        force_unit(g,'S01',0)
        v=CombatVisuals()
        v.sync(g,self.slot,self.hero,0)
        g._remove_unit('S01',death=False)
        v.sync(g,self.slot,self.hero,100)
        self.assertFalse(v.fallen_cards)

    def test_archive_menu_mentions_versions(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        app.menu_page='archive'
        app._archive_records=[{
            'exported_at_utc':'2026-10-19T12:00:00+00:00','version':'0.9.32',
            'winner':0,'rounds':20}]
        captured=[]
        original=app._button
        def observe(rect,label,*args,**kwargs):
            captured.append(label)
            return original(rect,label,*args,**kwargs)
        app._button=observe
        app._draw_menu()
        self.assertTrue(any('v0.9.32' in line for line in captured))


class RemainingUiClarityTests(unittest.TestCase):
    def test_real_death_no_legal_target_is_reported_once(self):
        g=setup_game(935240)
        force_unit(g,'S86',0)
        g.units['S86'].hp=0
        g._kill_batch(['S86'])
        g._drain()
        mentions=[line for line in g.events if 'brak legalnego celu' in line]
        self.assertEqual(len(mentions),1)
        self.assertIn('przy śmierci',mentions[0])
        g.assert_integrity()

    def test_audit_preserves_raw_negative_hero_hp_with_nonnegative_view(self):
        from game.core.audit import make_report
        g=setup_game(935241)
        g.phase='finished'
        g.winner=0
        g.players[1].hp=-13
        summary=make_report(g)['payload']['summary']
        self.assertEqual(summary['hero_hp']['1'],-13)
        self.assertEqual(summary['hero_hp_display']['1'],0)
        self.assertEqual(summary['hero_hp_display']['0'],max(0,g.players[0].hp))


if __name__=='__main__':
    unittest.main()
