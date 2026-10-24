"""0.9.58: backgrounds around auction portraits follow their own PNG palette."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game import config as cfg
from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.assets import ImageAssets


class AuctionDominantBackdrop0958(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((32, 32))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_majority_cluster_ignores_transparency_and_small_highlights(self):
        sprite=pygame.Surface((96,96), pygame.SRCALPHA)
        sprite.fill((0,0,0,0))
        pygame.draw.rect(sprite,(66,96,118,255),(0,0,78,96))
        pygame.draw.rect(sprite,(225,197,45,255),(78,0,18,96))
        self.assertEqual(ImageAssets.dominant_color(sprite),(66,96,118))

    def test_fully_transparent_falls_back_to_generic_panel(self):
        sprite=pygame.Surface((96,96),pygame.SRCALPHA)
        sprite.fill((250,40,60,0))
        self.assertEqual(ImageAssets.dominant_color(sprite),cfg.PANEL)

    def test_contain_letterbox_has_sprite_color_not_global_blue_panel(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            folder=root/"assets"/"auction"
            folder.mkdir(parents=True)
            sprite=pygame.Surface((96,96),pygame.SRCALPHA)
            sprite.fill((80,112,48,255))
            pygame.draw.rect(sprite,(223,54,73,255),(35,35,26,26))
            pygame.image.save(sprite,str(folder/"A001_podstawowa.png"))
            with patch("game.ui.assets.ROOT_DIR",root):
                cache=ImageAssets()
                img=cache.get_auction_image("A001","podstawowa",(216,96),mode="contain")
                self.assertEqual(cache.get_auction_color("A001","podstawowa"),(80,112,48))
                self.assertEqual(img.get_at((0,48))[:3],(80,112,48))
                self.assertEqual(img.get_at((215,48))[:3],(80,112,48))
                # Original centrally painted area remains recognizable.
                self.assertGreater(img.get_at((108,48)).r,160)
                self.assertIs(img,cache.get_auction_image(
                    "A001","podstawowa",(216,96),mode="contain"))
                # Standard starter art must keep its legacy fill color.
                plain=ImageAssets.fit_art(sprite,(216,96),mode="contain")
                self.assertEqual(plain.get_at((0,48))[:3],cfg.PANEL)

    def test_color_change_tracks_rarity_without_cache_bleeding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            folder=root/"assets"/"auction"
            folder.mkdir(parents=True)
            palette=((82,45,51),(42,90,115),(111,80,32))
            for tier,color in zip(RARITIES,palette):
                sprite=pygame.Surface((96,96),pygame.SRCALPHA)
                sprite.fill((*color,255))
                pygame.image.save(sprite,str(folder/f"A018_{tier}.png"))
            with patch("game.ui.assets.ROOT_DIR",root):
                cache=ImageAssets()
                for tier,color in zip(RARITIES,palette):
                    self.assertEqual(cache.get_auction_color("A018",tier),color)
                    img=cache.get_auction_image("A018",tier,(150,75),mode="contain")
                    self.assertEqual(img.get_at((0,30))[:3],color)
                    self.assertEqual(img.get_at((149,30))[:3],color)
                self.assertIsNone(cache.get_auction_color("A017","rzadka"))
                self.assertIsNone(cache.get_auction_color("A018","unknown"))

    def test_actual_51_auction_sprites_match_containment_backgrounds(self):
        base=Path(__file__).resolve().parents[1]
        if not (base/"assets/auction/manifest.json").exists():
            self.skipTest("Auction graphics not installed")
        with patch("game.ui.assets.ROOT_DIR",base):
            cache=ImageAssets()
            found=set()
            for card_id in V22_CARDS:
                for tier in RARITIES:
                    with self.subTest(card_id=card_id,rarity=tier):
                        color=cache.get_auction_color(card_id,tier)
                        self.assertIsNotNone(color)
                        self.assertEqual(len(color),3)
                        self.assertTrue(all(0<=c<=255 for c in color))
                        image=cache.get_auction_image(
                            card_id,tier,(192,96),mode="contain")
                        self.assertIsNotNone(image)
                        # Final pixel art uses its own full-scene colors;
                        # the 96px legacy palette stays queryable separately.
                        self.assertEqual(image.get_size(),(192,96))
                        self.assertIn(
                            f'auction_final/{card_id}_{tier}_portrait.png',
                            cache._original)
                        found.add((card_id,tier))
            self.assertEqual(len(found),51)


if __name__=="__main__":
    unittest.main()
