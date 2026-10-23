"""Tests for 70 pixel-art base cards without changing the engine."""
import hashlib
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "cards" / "pixel_art"

class PixelBase70Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "data" / "cards_base_70.json").read_text(encoding="utf-8"))

    def test_identity_and_special_chorazy(self):
        from game.ui.card_view import PIXEL_ART_IDS, ART
        rows = self.manifest["cards"]
        self.assertEqual(len(rows), 70)
        expected = {c["id"]: (c["name"], c["faction"]) for c in self.catalog}
        actual = {c["id"]: (c["name"], c["faction"]) for c in rows}
        self.assertEqual(actual, expected)
        self.assertEqual(set(actual), PIXEL_ART_IDS)
        self.assertNotIn("SUM_START_GUARD", PIXEL_ART_IDS)
        self.assertEqual(ART["S34"], "chorazy_krolewskiej_kompanii.png")

    def test_png_checksums_and_size(self):
        import pygame
        pygame.init()
        pygame.display.set_mode((1, 1))
        try:
            for card in self.manifest["cards"]:
                for kind, size in (("portrait", (295, 209)), ("banner", (295, 78))):
                    filename = card[kind]
                    self.assertEqual(filename, f"{card['id']}_{kind}.png")
                    p = ASSETS / filename
                    self.assertTrue(p.is_file(), filename)
                    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                                     card[kind + "_sha256"], filename)
                    self.assertEqual(pygame.image.load(str(p)).get_size(),
                                     size, filename)
        finally:
            pygame.quit()

    def test_rendering_all_base_cards_in_three_sizes(self):
        import pygame
        from game.ui.card_view import CardView
        pygame.init()
        pygame.display.set_mode((1, 1))
        try:
            view = CardView()
            for card in self.manifest["cards"]:
                for size in ((110, 22), (136, 38), (233, 112)):
                    image = view.art(card["id"], card["faction"], size,
                                     card["family"], card["name"])
                    self.assertEqual(image.get_size(), size,
                                     (card["id"], size))
                cache = view.images._scaled
                self.assertIn((f"pixel_art/{card['id']}_banner.png",
                               (110, 22), "cover", (0.5, 0.35), True), cache)
                self.assertIn((f"pixel_art/{card['id']}_portrait.png",
                               (233, 112), "cover", (0.5, 0.35), True), cache)
        finally:
            pygame.quit()

if __name__ == "__main__":
    unittest.main()
