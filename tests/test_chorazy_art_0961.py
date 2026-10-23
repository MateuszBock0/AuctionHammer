"""0.9.61: S34 rarity-style artwork upgrades and real Windows icon.

Visual-only regression. These tests must not change any card definition,
ability-level computation, combat, choice queue, RNG, audit or persistence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.models import Unit
from game.ui.card_view import CardView, CHORAZY_ART_LEVELS
from test_engine import setup_game


ROOT=Path(__file__).resolve().parents[1]


class ChorazyArt0961(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((64,64))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_5_artifact_checksums_and_png_format(self):
        manifest=json.loads((ROOT/"assets/branding/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["card_id"],"SUM_START_GUARD")
        self.assertEqual(len(manifest["files"]),5)
        found=set()
        for item in manifest["files"]:
            path=ROOT/item["path"]
            self.assertTrue(path.is_file(),path)
            data=path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),item["sha256"])
            self.assertNotIn(item["path"],found)
            found.add(item["path"])
            if path.suffix.lower()==".png":
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(struct.unpack(">II",data[16:24]),
                                 (item["width"],item["height"]))
                self.assertEqual(data[25],6)  # RGBA truecolor
                surface=pygame.image.load(str(path)).convert_alpha()
                self.assertEqual(surface.get_size(),(item["width"],item["height"]))
            elif path.suffix.lower()==".ico":
                self.assertEqual(data[:4],b"\x00\x00\x01\x00")
                self.assertGreaterEqual(struct.unpack("<H",data[4:6])[0],4)

    def test_restored_s34_sprite_is_exact_original_git_blob(self):
        file=ROOT/"assets/cards/chorazy_krolewskiej_kompanii.png"
        raw=file.read_bytes()
        git_blob=hashlib.sha1(
            b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()
        self.assertEqual(git_blob,
                         "3807f79343f1f789a38a4db70f2b5325be89096e")
        img=pygame.image.load(str(file)).convert_alpha()
        self.assertEqual(img.get_size(),(96,96))

    def test_exact_three_starter_portraits_by_kills_and_s34_remains_constant(self):
        self.assertEqual(CHORAZY_ART_LEVELS,
            ("chorazy.png","chorazy_rzadka.png","chorazy_legendarna.png"))
        view=CardView()
        samples=[]
        for kills,name in ((0,"chorazy.png"),(1,"chorazy_rzadka.png"),
                           (2,"chorazy_legendarna.png"),(3,"chorazy_legendarna.png")):
            with self.subTest(kills=kills):
                with patch.object(view.images,"get_card_image",
                                  wraps=view.images.get_card_image) as loader:
                    portrait=view.art("SUM_START_GUARD","Ludzie",(96,96),
                                      card_name="Chorąży",guard_kills=kills)
                    self.assertEqual(loader.call_args.args[0],name)
                    self.assertEqual(portrait.get_size(),(96,96))
                    samples.append(pygame.image.tobytes(portrait,"RGBA"))
        self.assertEqual(len(set(samples[:3])),3)
        self.assertEqual(samples[2],samples[3])

        game=setup_game(96101)
        card=game.cards["S34"]
        for hand_turns in (0,3,6,12):
            card.hand_turns=hand_turns
            with patch.object(view.images,"get_card_image",
                              wraps=view.images.get_card_image) as loader:
                view.draw(pygame.Surface((215,265),pygame.SRCALPHA),
                          card,pygame.Rect(12,15,148,220))
                self.assertEqual(loader.call_args.args[0],
                                 "chorazy_krolewskiej_kompanii.png")

    def test_historical_guard_and_other_guard_still_use_the_original(self):
        game=setup_game(96102)
        view=CardView()
        portrait=view.art("SUM_START_GUARD","Ludzie",(96,96),
                          card_name="Chorąży",guard_kills=None)
        from game.ui.card_view import ART
        self.assertEqual(ART["S34"],"chorazy_krolewskiej_kompanii.png")
        self.assertIsNotNone(portrait)
        self.assertEqual(portrait.get_size(),(96,96))

    def test_real_window_icon_is_decodable_by_pygame(self):
        image=pygame.image.load(str(ROOT/"assets/branding/chorazy_zawsze_zdazy_icon.png"))
        self.assertEqual(image.get_size(),(128,128))
        pygame.display.set_icon(image)


if __name__=="__main__":
    unittest.main()
