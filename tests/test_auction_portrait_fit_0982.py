"""0.9.82: pixel-art-safe centering for every auction presentation size."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.ui.assets import ImageAssets
from game.ui.card_view import CardView


class AuctionPortraitFit0982(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        folder=self.root/"assets"/"auction"/"final"
        folder.mkdir(parents=True)
        for kind,dims in (("banner",(295,78)),("portrait",(295,209))):
            surf=pygame.Surface(dims,pygame.SRCALPHA)
            surf.fill((43,58,62,255))
            pygame.draw.line(surf,(230,31,37,255),(0,0),(dims[0]-1,0),8)
            pygame.draw.line(surf,(30,98,231,255),(0,dims[1]-1),
                             (dims[0]-1,dims[1]-1),8)
            pygame.image.save(surf,str(folder/f"A002_rzadka_{kind}.png"))

    def test_strip_uses_uncropped_banner_and_keeps_top_bottom(self):
        with patch("game.ui.assets.ROOT_DIR",self.root):
            loader=ImageAssets()
            strip=loader.get_auction_image("A002","rzadka",(133,38),
                                          mode="contain")
            self.assertEqual(strip.get_size(),(133,38))
            self.assertIn("auction_final/A002_rzadka_banner.png",loader._original)
            self.assertNotIn("auction_final/A002_rzadka_portrait.png",loader._original)
            self.assertGreater(strip.get_at((65,2)).r,190)
            self.assertGreater(strip.get_at((65,35)).b,170)
            self.assertIs(strip,loader.get_auction_image("A002","rzadka",
                                                         (133,38),mode="contain"))

    def test_large_hover_card_keeps_head_and_bottom_in_center(self):
        with patch("game.ui.assets.ROOT_DIR",self.root):
            loader=ImageAssets()
            card=loader.get_auction_image("A002","rzadka",(233,112),
                                         mode="contain")
            self.assertEqual(card.get_size(),(233,112))
            self.assertIn("auction_final/A002_rzadka_portrait.png",loader._original)
            self.assertGreater(card.get_at((116,1)).r,190)
            self.assertGreater(card.get_at((116,110)).b,170)
            # The side margins are the source's dominant hue, not a black void.
            self.assertEqual(card.get_at((0,55))[:3],(43,58,62))
            self.assertEqual(card.get_at((232,55))[:3],(43,58,62))

    def test_square_auction_offer_keeps_full_portrait_centered(self):
        with patch("game.ui.assets.ROOT_DIR",self.root):
            loader=ImageAssets()
            offer=loader.get_auction_image("A002","rzadka",(90,90),
                                          mode="contain")
            self.assertEqual(offer.get_size(),(90,90))
            self.assertGreater(offer.get_at((45,13)).r,190)
            self.assertGreater(offer.get_at((45,76)).b,170)
            # 0.9.83 extends scene edge pixels behind the intact art,
            # rather than painting the former uniform letterbox bars.
            self.assertGreater(offer.get_at((45,0)).r,190)
            self.assertGreater(offer.get_at((45,89)).b,170)

    def test_card_view_uses_contain_for_small_and_large_auction_cards(self):
        view=CardView()
        with patch.object(view.images,"get_auction_image",
                          return_value=pygame.Surface((133,38))) as fn:
            view.art("A002","Ludzie",(133,38),"ATK ±","Generał",rarity="rzadka")
            fn.assert_called_once_with("A002","rzadka",(133,38),mode="contain")
        with patch.object(view.images,"get_auction_image",
                          return_value=pygame.Surface((233,112))) as fn:
            view.art("A002","Ludzie",(233,112),"ATK ±","Generał",rarity="rzadka")
            fn.assert_called_once_with("A002","rzadka",(233,112),mode="contain")


if __name__=="__main__":
    unittest.main()
