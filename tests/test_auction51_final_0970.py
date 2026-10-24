"""v0.9.70 — finished pixel art for all 51 auction variants."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.assets import ImageAssets
from game.ui.card_view import CardView

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"assets"/"auction"/"final"

class Auction51FinalArt0970(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.manifest=json.loads((ART/"manifest.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_manifest_exact_51_and_102_real_unique_png(self):
        rows=self.manifest["cards"]
        self.assertEqual(len(rows),51)
        self.assertEqual(self.manifest["files"],102)
        self.assertEqual(self.manifest["archetypes"],17)
        expected={(cid,rarity) for cid in V22_CARDS for rarity in RARITIES}
        self.assertEqual({(r["id"],r["rarity"]) for r in rows},expected)
        self.assertNotIn("A017",{r["id"] for r in rows})
        sha=set()
        for row in rows:
            for kind,dims in (("banner",(295,78)),("portrait",(295,209))):
                name=f"{row['id']}_{row['rarity']}_{kind}.png"
                self.assertEqual(row[kind],name)
                file=ART/name
                self.assertTrue(file.is_file(),name)
                digest=hashlib.sha256(file.read_bytes()).hexdigest()
                self.assertEqual(digest,row[kind+"_sha256"],name)
                self.assertNotIn(digest,sha)
                sha.add(digest)
                self.assertEqual(pygame.image.load(str(file)).get_size(),dims)
        self.assertEqual(len(sha),102)

    def test_all_rarity_modes_render_and_cache_without_compositing(self):
        loader=ImageAssets()
        for cid in V22_CARDS:
            for rarity in RARITIES:
                for size,kind in (((110,22),"banner"),((136,38),"banner"),
                                  ((233,112),"portrait"),((295,209),"portrait")):
                    with self.subTest(cid=cid,rarity=rarity,size=size):
                        img=loader.get_auction_image(cid,rarity,size,mode="cover")
                        self.assertEqual(img.get_size(),size)
                        self.assertIs(img,loader.get_auction_image(cid,rarity,size,"cover"))
                        self.assertIn(f"auction_final/{cid}_{rarity}_{kind}.png",
                                      loader._original)
                zoom=loader.get_auction_image(cid,rarity,(276,520),mode="contain")
                self.assertEqual(zoom.get_size(),(276,520))
        self.assertFalse(hasattr(ImageAssets,"_compose_original_auction_character"))
        self.assertFalse(hasattr(ImageAssets,"_auction_pixel_scene"))

    def test_game_card_view_matches_both_image_formats(self):
        cards=CardView()
        for cid,definition in V22_CARDS.items():
            for rarity in RARITIES:
                for size in ((110,22),(233,112)):
                    art=cards.art(cid,"Ludzie",size,"Obrażenia",
                                  definition["name"],rarity=rarity)
                    self.assertEqual(art.get_size(),size)

    def test_missing_final_png_falls_back_to_old_exact_rarity(self):
        original=ROOT/"assets"/"auction"/"A001_podstawowa.png"
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            folder=root/"assets"/"auction"
            folder.mkdir(parents=True)
            (folder/original.name).write_bytes(original.read_bytes())
            with patch("game.ui.assets.ROOT_DIR",root):
                old=ImageAssets().get_auction_image("A001","podstawowa",(110,22))
                self.assertIsNotNone(old)
                self.assertEqual(old.get_size(),(110,22))
        self.assertIsNone(ImageAssets().get_auction_image("A017","podstawowa",(110,22)))
        self.assertIsNone(ImageAssets().get_auction_image("A001","unknown",(110,22)))

if __name__=="__main__":
    unittest.main()
