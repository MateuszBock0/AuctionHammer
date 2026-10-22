"""Auction illustration mapping, cache and supply-chain tests (0.9.57).

Asset-package acceptance runs automatically once the binary PNG pack is
checked into assets/auction. Temporary fixtures test the loader before that.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.assets import ImageAssets
from game.ui.card_view import CardView
from tools.install_auction_sprites_0957 import (
    EXPECTED, validate_manifest, validate_installed
)


class AuctionSpriteTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((64, 64))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dir = self.root / "assets" / "auction"
        self.dir.mkdir(parents=True)

    def tearDown(self):
        pygame.quit()

    def make_png(self, cid, tier, color):
        image=pygame.Surface((96, 96),pygame.SRCALPHA)
        image.fill((*color, 255))
        path=self.dir / f"{cid}_{tier}.png"
        pygame.image.save(image, str(path))
        return path

    def test_exact_17_by_three_catalog_and_no_a017(self):
        self.assertEqual(len(V22_CARDS), 17)
        self.assertEqual(len(EXPECTED), 51)
        self.assertNotIn("assets/auction/A017_legendarna.png",EXPECTED)

    def test_loader_uses_exact_tier_and_keeps_scaled_surface_cached(self):
        colors=((90,10,10), (10,90,10), (10,10,90))
        for tier,color in zip(RARITIES,colors):
            self.make_png("A001",tier,color)
        with patch("game.ui.assets.ROOT_DIR",self.root):
            loader=ImageAssets()
            for tier,color in zip(RARITIES,colors):
                item=loader.get_auction_image("A001",tier,(64,64))
                self.assertIsNotNone(item)
                # SDL smoothscale may round channel values while downsampling.
                actual=item.get_at((32,32))[:3]
                self.assertTrue(all(abs(a-b)<=5 for a,b in zip(actual,color)),
                                (tier,actual,color))
                self.assertIs(item,loader.get_auction_image("A001",tier,(64,64)))
            self.assertIsNone(loader.get_auction_image("A017","legendarna",(64,64)))
            self.assertIsNone(loader.get_auction_image("A001","mythic",(64,64)))
            self.assertIsNone(loader.get_auction_image("A018","rzadka",(64,64)))
            self.make_png("A018","rzadka",(7,8,9))
            self.assertIsNotNone(loader.get_auction_image("A018","rzadka",(64,64)))

    def test_card_view_passes_rarity_not_random_category(self):
        card_view=CardView()
        expected=pygame.Surface((60,50),pygame.SRCALPHA)
        for tier in RARITIES:
            with patch.object(card_view.images,"get_auction_image",
                              return_value=expected) as lookup:
                self.assertIs(
                    card_view.art("A018","Ludzie",(60,50),"Pancerz","Test",rarity=tier),
                    expected)
                lookup.assert_called_once_with("A018",tier,(60,50))
        with patch.object(card_view.images,"get_auction_image") as lookup:
            card_view.art("S01","Elfy",(60,50),"Obrażenia","Mag",rarity="rzadka")
            lookup.assert_not_called()

    def test_manifest_checks_every_sha_and_rejects_tampering(self):
        records=[]
        for i,cid in enumerate(sorted(V22_CARDS)):
            for j,tier in enumerate(RARITIES):
                path=self.make_png(cid,tier,((i*17)%255,(j*73+i)%255, (i*11+j*57)%255))
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                records.append({"id":cid,"rarity":tier,
                                "target_path":f"assets/auction/{path.name}",
                                "filename":path.name,"target_size":[96,96],
                                "output_sha256":digest})
        manifest={"assets":records,"total_images":51,"total_cards":17,
                  "rarities":list(RARITIES),"card_ids":sorted(V22_CARDS)}
        read=lambda name:(self.root/name).read_bytes()
        self.assertEqual(len(validate_manifest(manifest,read)),51)
        records[0]["output_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            validate_manifest(manifest,read)

    def test_real_supplied_asset_pack_when_installed(self):
        root=Path(__file__).resolve().parents[1]
        manifest=root/"assets"/"auction"/"manifest.json"
        if not manifest.exists():
            self.skipTest("Binary PNG/manifest not yet committed; release gate pending")
        self.assertEqual(len(validate_installed(root)),51)


if __name__=="__main__":
    unittest.main()
