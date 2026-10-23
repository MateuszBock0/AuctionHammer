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
        self.assertEqual(manifest["card_id"],"S34")
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

    def test_exact_three_distinct_s34_portraits_by_existing_ability_level(self):
        self.assertEqual(CHORAZY_ART_LEVELS,
            ("chorazy.png","chorazy_rzadka.png","chorazy_legendarna.png"))
        game=setup_game(96100)
        card=game.cards["S34"]
        view=CardView()
        filenames=("chorazy.png","chorazy_rzadka.png",
                   "chorazy_legendarna.png","chorazy_legendarna.png")
        samples=[]
        for hand_turns,name in zip((0,3,6,12),filenames):
            with self.subTest(hand_turns=hand_turns):
                card.hand_turns=hand_turns
                with patch.object(view.images,"get_card_image",
                                  wraps=view.images.get_card_image) as loader:
                    view.draw(pygame.Surface((215,265),pygame.SRCALPHA),
                              card,pygame.Rect(12,15,148,220))
                    self.assertEqual(loader.call_args.args[0],name)
                    self.assertEqual(loader.call_args.kwargs["mode"],"cover")
                art=view.art("S34","Ludzie",(96,96),rarity="podstawowa",
                             level=card.ability_level)
                self.assertEqual(art.get_size(),(96,96))
                samples.append(pygame.image.tobytes(art,"RGBA"))
        self.assertEqual(len(set(samples[:3])),3)
        self.assertEqual(samples[2],samples[3])

    def test_on_board_and_in_hand_use_identical_level_and_no_mutation(self):
        game=setup_game(96101)
        card=game.cards["S34"]
        card.hand_turns=6
        card.owner=0
        unit=Unit("S34",0,card.attack,card.max_hp,card.max_hp,
                  card.ability_level,played_turn=1)
        original=(card.hand_turns,card.attack,card.max_hp,unit.atk,unit.hp)
        view=CardView()
        surface=pygame.Surface((260,300),pygame.SRCALPHA)
        with patch.object(view.images,"get_card_image",
                          wraps=view.images.get_card_image) as loader:
            view.draw(surface,card,pygame.Rect(20,20,148,220),
                      unit,ready=False,attacks_remaining=0,attacks_total=1)
            self.assertEqual(loader.call_args.args[0],"chorazy_legendarna.png")
        self.assertEqual((card.hand_turns,card.attack,card.max_hp,unit.atk,unit.hp),original)

    def test_real_window_icon_is_decodable_by_pygame(self):
        image=pygame.image.load(str(ROOT/"assets/branding/chorazy_zawsze_zdazy_icon.png"))
        self.assertEqual(image.get_size(),(128,128))
        pygame.display.set_icon(image)


if __name__=="__main__":
    unittest.main()
