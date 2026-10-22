"""0.9.54: legendary cards are recognizable without obscuring game data."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.auction_catalog import CATALOG_V22,TRIGGER,stats_v22,live_variant
from game.core.models import Card,CardDefinition,Unit
from game.ui.card_view import CardView,card_zones
from game.ui.visual_theme import VisualTheme


class LegendaryVisualIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.view=CardView()
        archetype=CATALOG_V22['A014']
        atk,hp=stats_v22('A014',3)
        definition=CardDefinition(
            'A014',archetype.name,'Ludzie',archetype.family,
            TRIGGER[archetype.trigger],atk,hp,
            live_variant('v22','A014','legendarna'),
            'v22',0,0)
        cls.card=Card('AUC-LEGENDARY-TEST',definition,owner=0,zone='hand')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _render(self,tier,rect,animated=False):
        surface=pygame.Surface((430,500),pygame.SRCALPHA)
        surface.fill((19,31,37,255))
        self.view.draw(surface,self.card,rect,rarity=tier,
                       animate_rarity=animated)
        return surface

    def test_all_three_card_sizes_keep_name_rules_and_stats_unchanged(self):
        for size in ((125,195),(148,220),(255,380)):
            with self.subTest(size=size):
                rect=pygame.Rect(65,70,*size)
                rare=self._render('rzadka',rect)
                legendary=self._render('legendarna',rect)
                zones=card_zones(rect)
                # Actual opaque information cells, not a synthetic blank card.
                for key in ('name','trigger','info'):
                    point=zones[key].center
                    self.assertEqual(rare.get_at(point),legendary.get_at(point),
                                     (size,key,point))
                # The zone center is the gap between ATK and HP boxes.
                # Compare centers of the two opaque value cells instead.
                stats=zones['stats']
                for label,point in (
                    ('ATK',(stats.left+stats.width//4,stats.centery)),
                    ('PZ',(stats.left+3*stats.width//4,stats.centery)),
                ):
                    self.assertEqual(rare.get_at(point),legendary.get_at(point),
                                     (size,label,point))
                # The illustration and outside edge visibly differ.
                # On hand-sized cards the level/progress badge occupies
                # the artwork's center. Sample the uncovered left third.
                art=zones['art']
                art_sample=(art.x+art.width//3,art.centery)
                self.assertNotEqual(
                    rare.get_at(art_sample),
                    legendary.get_at(art_sample),size)
                self.assertNotEqual(
                    pygame.image.tostring(rare,'RGBA'),
                    pygame.image.tostring(legendary,'RGBA'))

    def test_static_legendary_render_is_deterministic_and_no_clock_needed(self):
        rect=pygame.Rect(65,70,148,220)
        with patch.object(pygame.time,'get_ticks',
                          side_effect=AssertionError('clock used with animations disabled')):
            a=self._render('legendarna',rect)
            b=self._render('legendarna',rect)
            self.assertEqual(
                pygame.image.tostring(a,'RGBA'),
                pygame.image.tostring(b,'RGBA'))

    def test_auction_artwork_badges_do_not_overlap_or_claim_hand_scaling(self):
        hand_rect=pygame.Rect(65,70,125,195)
        with patch.object(self.view,'_pill',wraps=self.view._pill) as pill:
            self._render('legendarna',hand_rect)
        captions=[str(c.args[2]) for c in pill.call_args_list]
        self.assertIn('LEG.',captions)
        self.assertFalse(any('0/3' in value for value in captions),captions)

        unit=Unit(self.card.uid,0,self.card.attack,self.card.max_hp,
                  self.card.max_hp,0,0)
        board_rect=pygame.Rect(65,70,148,220)
        surface=pygame.Surface((430,500),pygame.SRCALPHA)
        with patch.object(self.view,'_pill',wraps=self.view._pill) as pill:
            self.view.draw(surface,self.card,board_rect,unit=unit,
                           rarity='legendarna',attacks_remaining=1,
                           attacks_total=1,ready=True,animate_rarity=False)
        captions=[str(c.args[2]) for c in pill.call_args_list]
        self.assertIn('ATAKI 1/1',captions)
        self.assertNotIn('LEG.',captions)

    def test_legendary_offer_ornament_decorates_corners_not_description(self):
        theme=VisualTheme()
        surface=pygame.Surface((430,500),pygame.SRCALPHA)
        surface.fill((47,35,29,255))
        rect=pygame.Rect(55,60,278,364)
        middle=tuple(surface.get_at(rect.center))
        before_corner=tuple(surface.get_at((rect.left+15,rect.top+15)))
        theme.legendary_offer_ornament(surface,rect,animate=False)
        self.assertEqual(tuple(surface.get_at(rect.center)),middle)
        self.assertNotEqual(
            tuple(surface.get_at((rect.left+15,rect.top+15))),before_corner)

    def test_basic_and_rare_appearances_unchanged_by_legendary_pass(self):
        rect=pygame.Rect(65,70,148,220)
        basic=self._render('podstawowa',rect)
        rare=self._render('rzadka',rect)
        legendary=self._render('legendarna',rect)
        self.assertEqual(
            tuple(basic.get_at(card_zones(rect)['art'].center)),
            tuple(rare.get_at(card_zones(rect)['art'].center)))
        self.assertNotEqual(
            tuple(basic.get_at(card_zones(rect)['art'].center)),
            tuple(legendary.get_at(card_zones(rect)['art'].center)))


if __name__=='__main__':
    unittest.main()
