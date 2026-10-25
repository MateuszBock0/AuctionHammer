"""0.9.83 UI contract: genuine nearest-neighbour pixel art and read-only feedback."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.ui.assets import ImageAssets
from game.ui.game_icons import GameIcons
from game.ui.auction_badges import draw_trigger_icon, PIXELS, TRIGGER_NAMES
from game.ui.app import SoloApp
from game.core.audit import digest, state_snapshot
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from test_auction_foundation_0921 import ready as auction_ready


class PixelArt083Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    @staticmethod
    def source_art():
        art=pygame.Surface((295,209),pygame.SRCALPHA)
        art.fill((42,53,61))
        for y in range(209):
            pygame.draw.rect(art,((47+y//2)%255,51,57),(0,y,8,1))
            pygame.draw.rect(art,(45,(65+y//2)%255,67),(287,y,8,1))
        # Deliberately prominent 8px top/bottom strips, like a hat and cape.
        pygame.draw.rect(art,(238,34,44),(24,0,247,8))
        pygame.draw.rect(art,(39,91,243),(24,201,247,8))
        # The central figure is never stretched, mirrored, or cloned.
        pygame.draw.rect(art,(254,215,113),(117,53,55,113))
        return art

    def test_extended_edges_are_not_flat_bars_and_center_is_intact(self):
        img=self.source_art()
        original=pygame.image.tobytes(img,'RGBA')
        picture=ImageAssets.fit_auction_pixel_bleed(img,(233,112))
        # The full portrait fits at width ~159, leaving two side bands.
        self.assertNotEqual(picture.get_at((4,19)),picture.get_at((4,81)))
        self.assertNotEqual(picture.get_at((228,19)),picture.get_at((228,81)))
        # Main subject occupies only the original image region.
        center=pygame.transform.scale(img,(159,112))
        self.assertEqual(picture.get_at((116,56)),center.get_at((79,56)))
        self.assertEqual(pygame.image.tobytes(img,'RGBA'),original)

    def test_square_offer_fills_top_and_bottom_with_real_scene_pixels(self):
        img=self.source_art()
        picture=ImageAssets.fit_auction_pixel_bleed(img,(90,90))
        self.assertEqual(picture.get_size(),(90,90))
        self.assertGreater(picture.get_at((45,0)).r,190)
        self.assertGreater(picture.get_at((45,89)).b,170)
        self.assertGreater(picture.get_at((45,45)).r,180)

    def test_auction_art_never_uses_smoothscale(self):
        img=self.source_art()
        with patch('game.ui.assets.pygame.transform.smoothscale',
                   side_effect=AssertionError('Pixel art cannot blur')):
            for shape in ((233,112),(90,90),(135,38),(276,520)):
                with self.subTest(shape=shape):
                    self.assertEqual(ImageAssets.fit_auction_pixel_bleed(
                        img,shape).get_size(),shape)

    def test_icons_are_crisp_scaled_8bit_images_not_smoothed(self):
        icons=GameIcons()
        sprite=pygame.Surface((2,2),pygame.SRCALPHA)
        sprite.fill((250,26,26),(0,0,1,1))
        sprite.fill((24,35,243),(1,0,1,1))
        sprite.fill((40,220,80),(0,1,1,1))
        sprite.fill((240,217,65),(1,1,1,1))
        icons._original['zdolnosci/obrazenia']=sprite
        with patch('game.ui.game_icons.pygame.transform.smoothscale',
                   side_effect=AssertionError('Do not blur glyphs')):
            scaled=icons.get('Obrażenia','families',20)
        self.assertEqual(scaled.get_at((2,2))[:3],(250,26,26))
        self.assertEqual(scaled.get_at((17,17))[:3],(240,217,65))
        self.assertIs(scaled,icons.get('Obrażenia','families',20))

    def test_trigger_tiles_have_five_by_five_pixel_patterns(self):
        for trigger,pattern in PIXELS.items():
            with self.subTest(trigger=trigger):
                self.assertEqual(len(pattern),5)
                self.assertTrue(all(len(row)==5 and set(row)<=set('01')
                                    for row in pattern))
                self.assertIn(trigger,TRIGGER_NAMES)
                surf=pygame.Surface((32,32))
                rect=pygame.Rect(4,4,23,23)
                draw_trigger_icon(surf,rect,trigger)
                self.assertEqual(surf.get_at(rect.center)[:3],
                                 (239,204,144))
        self.assertEqual(SoloApp.auction_badge_rects(2)[1].right,
                         SoloApp.auction_offer_rect(2).right-9)

    def test_real_auction_draws_offer_icons_and_bid_price_breakdown(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        app.menu_open=False
        app.game=auction_ready(2113)
        app.auction_inspect_index=None
        before=digest(state_snapshot(app.game))
        labels=[]
        actual=app._text
        def record(*args,**kwargs):
            labels.append(str(args[0]))
            return actual(*args,**kwargs)
        try:
            with patch.object(app,'_text',side_effect=record):
                app._draw_auction()
            self.assertTrue(any('MECHANIKA' in t or 'PASYWNA' in t
                                or 'PRZY' in t for t in labels))
            self.assertTrue(any('MONETY PO WYGRANEJ' in t for t in labels))
            self.assertEqual(digest(state_snapshot(app.game)),before)
        finally:
            app.menu_open=True


class AttackFeedback083Tests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        for seed in range(300,500):
            g=Match(seed,audit_enabled=True,auctions_enabled=True,
                    auction_catalog='v22',
                    starting_compensation='choice_2_5_or_coins')
            if g.first==0:
                break
        self.app.game=g
        opponent=ComputerOpponent()
        opponent.step(g)
        if 1 not in g.mulligan_done:
            opponent.step(g)
        g.finish_mulligan(0,[])
        self.app.tutorial_welcome_open=False
        self.app.selected=None

    def tearDown(self):
        pygame.quit()

    def test_attacker_brackets_without_gameplay_changes(self):
        game=self.app.game
        uid=game.players[0].hand[0]
        game.play(uid,slot=0)
        game.units[uid].played_turn=-1
        self.app.selected=uid
        self.assertTrue(game.legal_attacks(uid))
        before=digest(state_snapshot(game))
        real=pygame.draw.line
        with patch('game.ui.app.pygame.draw.line',wraps=real) as strokes:
            self.app._draw_attack_source_feedback()
        self.assertEqual(strokes.call_count,8)
        self.assertTrue(all(c.args[1]==(245,192,116)
                            for c in strokes.call_args_list))
        self.assertEqual(digest(state_snapshot(game)),before)

    def test_no_brackets_without_legal_attack(self):
        game=self.app.game
        uid=game.players[0].hand[0]
        game.play(uid,slot=0)
        self.app.selected=uid
        # Just played, not quick: cannot legally attack yet.
        if game.legal_attacks(uid):
            game.units[uid].attacks=99
        with patch('game.ui.app.pygame.draw.line') as strokes:
            self.app._draw_attack_source_feedback()
        strokes.assert_not_called()


if __name__=='__main__':
    unittest.main()
