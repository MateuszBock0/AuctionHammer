"""0.9.88: higher framing of square auction offers must visibly crop vertically."""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.app import SoloApp
from game.ui.assets import ImageAssets
from test_auction_placeholder_0919 import auction_game


FOCUS=(0.5,0.0)
ZOOM=1.08


class AuctionTopFraming0988(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    @staticmethod
    def vertical_gradient():
        source=pygame.Surface((295,209),pygame.SRCALPHA)
        for y in range(209):
            pygame.draw.line(source,(y,10,255-y,255),(0,y),(294,y))
        return source

    def test_top_crop_is_real_not_a_focus_only_noop(self):
        source=self.vertical_gradient()
        old=ImageAssets.fit_art(source,(116,116),mode='cover',pixelated=True)
        focus_only=ImageAssets.fit_art(source,(116,116),mode='cover',
                                       focus=FOCUS,pixelated=True)
        top=ImageAssets.fit_art(source,(116,116),mode='cover',
                                focus=FOCUS,zoom=ZOOM,pixelated=True)
        self.assertEqual(top.get_size(),(116,116))
        # Ordinary cover fits height exactly: focus_y cannot change anything.
        self.assertEqual(pygame.image.tostring(old,'RGB'),
                         pygame.image.tostring(focus_only,'RGB'))
        # Top edge is preserved; lower source row is genuinely cropped.
        self.assertEqual(top.get_at((58,0)),old.get_at((58,0)))
        self.assertLess(top.get_at((58,115)).r,old.get_at((58,115)).r)
        self.assertNotEqual(pygame.image.tostring(old,'RGB'),
                            pygame.image.tostring(top,'RGB'))

    def test_square_zoom_cache_is_distinct_and_repeatable(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            folder=root/'assets'/'auction'/'final'
            folder.mkdir(parents=True)
            pygame.image.save(self.vertical_gradient(),
                              str(folder/'A001_podstawowa_portrait.png'))
            with patch('game.ui.assets.ROOT_DIR',root):
                images=ImageAssets()
                old=images.get_auction_image('A001','podstawowa',
                                             (116,116),mode='cover')
                top=images.get_auction_image('A001','podstawowa',
                                             (116,116),mode='cover',
                                             focus=FOCUS,zoom=ZOOM)
                self.assertIsNot(old,top)
                self.assertIs(top,images.get_auction_image(
                    'A001','podstawowa',(116,116),mode='cover',
                    focus=FOCUS,zoom=ZOOM))
                self.assertLess(top.get_at((58,115)).r,
                                old.get_at((58,115)).r)

    def test_only_three_square_auction_offers_request_top_focus(self):
        with patch.object(SoloApp,'_desktop_resolution',
                          return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        app.menu_open=False
        app.tutorial_welcome_open=False
        app.game=auction_game(1988)
        sprite=pygame.Surface((116,116),pygame.SRCALPHA)
        with patch.object(app.cards_view.images,'get_auction_image',
                          return_value=sprite) as loader:
            app._draw_auction()
        tiles=[call for call in loader.call_args_list
               if len(call.args)>2 and call.args[2]==(116,116)]
        self.assertEqual(len(tiles),3)
        for call in tiles:
            self.assertEqual(call.kwargs.get('mode'),'cover')
            self.assertEqual(call.kwargs.get('focus'),FOCUS)
            self.assertEqual(call.kwargs.get('zoom'),ZOOM)

    def test_contain_and_normal_art_resizing_are_unchanged(self):
        source=self.vertical_gradient()
        a=ImageAssets.fit_art(source,(233,112),mode='contain',pixelated=True)
        b=ImageAssets.fit_art(source,(233,112),mode='contain',
                               pixelated=True,zoom=1.0)
        self.assertEqual(pygame.image.tostring(a,'RGB'),
                         pygame.image.tostring(b,'RGB'))
        with self.assertRaises(ValueError):
            ImageAssets.fit_art(source,(116,116),mode='contain',zoom=ZOOM)

    def test_all_51_real_auction_variants_have_top_focused_images(self):
        images=ImageAssets()
        for archetype in V22_CARDS:
            for rarity in RARITIES:
                with self.subTest(archetype=archetype,rarity=rarity):
                    sprite=images.get_auction_image(
                        archetype,rarity,(116,116),mode='cover',
                        focus=FOCUS,zoom=ZOOM)
                    self.assertIsNotNone(sprite)
                    self.assertEqual(sprite.get_size(),(116,116))


if __name__=='__main__':
    unittest.main()
