"""0.9.103: BURDA hover is readable, live, legacy-aware and read-only."""
from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from game.ui.app import SoloApp
from game.ui.tavern_help import brawl_help_lines


class BrawlHelpText09103(unittest.TestCase):
    def game(self,turns=3,scaled=True,enabled=True):
        return SimpleNamespace(tavern_beer_enabled=enabled,
                               tavern_scaled_damage_enabled=scaled,
                               beer_turns_remaining=turns,
                               pending=None,phase='turn')

    def test_scaled_damage_and_turns_are_live_from_match(self):
        game=self.game()
        self.assertIn('3 DMG', ' '.join(brawl_help_lines(game)))
        game.beer_turns_remaining=2
        self.assertIn('2 DMG', ' '.join(brawl_help_lines(game)))
        game.beer_turns_remaining=1
        self.assertIn('1 DMG', ' '.join(brawl_help_lines(game)))
        game.beer_turns_remaining=0
        text=' '.join(brawl_help_lines(game))
        self.assertIn('NIEAKTYWNA',text)
        self.assertIn('Kup kufel',text)
        self.assertNotIn('NASTĘPNY KONIEC TURY:',text)

    def test_legacy_save_retains_fixed_one_damage_description(self):
        game=self.game(6,scaled=False)
        text=' '.join(brawl_help_lines(game))
        self.assertIn('1 DMG',text)
        self.assertIn('starsza partia',text)
        self.assertIn('nadal 1 DMG',text)
        self.assertNotIn('6 DMG',text)

    def test_tooltip_explains_target_defenses_safety_and_extensions(self):
        text=' '.join(brawl_help_lines(self.game()))
        for term in ('obu graczy','Tarcza','pancerz','Bohaterowie',
                     'na ręce','+3 tury'):
            self.assertIn(term,text)
        self.assertEqual(brawl_help_lines(self.game(enabled=False)),())


class BrawlHover09103(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def fake_app(self,turns=3,scaled=True,enabled=True,pos=(52,509)):
        class Fake:
            brawl_status_rect=staticmethod(SoloApp.brawl_status_rect)
            _draw_brawl_hover_help=SoloApp._draw_brawl_hover_help
            _wrap=SoloApp._wrap
            _text=SoloApp._text
            _panel=lambda self,rect,fill=None,line=None,radius=0: pygame.draw.rect(
                self.screen,fill or (120,89,39),rect,border_radius=radius)
            _bonus_selection_due=lambda self:False

            def mouse_pos(self):
                return self.pointer

        fake=Fake()
        fake.screen=pygame.Surface((1480,980))
        fake.screen.fill((7,8,9))
        fake.pointer=pos
        fake.game=SimpleNamespace(tavern_beer_enabled=enabled,
                                  tavern_scaled_damage_enabled=scaled,
                                  beer_turns_remaining=turns,
                                  pending=None,phase='turn')
        fake.fonts={size:pygame.font.Font(None,size) for size in (11,13,16)}
        fake.cards_view=SimpleNamespace(clip=lambda text,font,width:text)
        fake.menu_open=False
        fake.history_open=False
        fake.replay_index=None
        fake.details_card=None
        fake.confirm_action=None
        fake.help_open=False
        fake.drag_start=None
        return fake

    def test_hover_highlights_label_and_draws_only_in_sidebar(self):
        fake=self.fake_app()
        self.assertTrue(SoloApp._draw_brawl_hover_help(fake,fake.pointer))
        self.assertNotEqual(fake.screen.get_at((11,500)),(7,8,9,255))
        self.assertNotEqual(fake.screen.get_at((1120,310)),(7,8,9,255))
        # No card art, health bar or purchase button is touched.
        for pt in ((150,530),(350,350),(800,470),(105,570),(600,820)):
            self.assertEqual(fake.screen.get_at(pt),(7,8,9,255))

    def test_outside_label_and_purchase_button_never_trigger_info(self):
        for pointer in ((5,507),(55,544),(56,565),(105,507),(400,600)):
            fake=self.fake_app(pos=pointer)
            self.assertFalse(SoloApp._draw_brawl_hover_help(fake,pointer))
            self.assertEqual(fake.screen.get_at((11,500)),(7,8,9,255))
            self.assertEqual(fake.screen.get_at((1120,310)),(7,8,9,255))

    def test_works_even_without_brawl_and_when_animations_disabled(self):
        fake=self.fake_app(turns=0)
        fake.animations_enabled=False
        self.assertTrue(SoloApp._draw_brawl_hover_help(fake,fake.pointer))
        disabled=self.fake_app(enabled=False)
        self.assertFalse(SoloApp._draw_brawl_hover_help(
            disabled,disabled.pointer))

    def test_modal_and_replay_suppress_hover_without_mutating_game(self):
        for key,value in (('menu_open',True),('history_open',True),
                          ('replay_index',0),('details_card','S01'),
                          ('confirm_action','exit'),('help_open',True),
                          ('drag_start',object())):
            fake=self.fake_app()
            setattr(fake,key,value)
            game_before=dict(vars(fake.game))
            SoloApp._draw_hover_guidance(fake)
            self.assertEqual(dict(vars(fake.game)),game_before)
            self.assertEqual(fake.screen.get_at((11,500)),(7,8,9,255))
            self.assertEqual(fake.screen.get_at((1120,310)),(7,8,9,255))


if __name__=='__main__':
    unittest.main()
