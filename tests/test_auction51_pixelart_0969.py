"""0.9.69: 51 authentic card characters + 102 generated scene backgrounds."""
import hashlib
import io
import json
import os
from pathlib import Path
import unittest
import zipfile
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

import pygame
from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.assets import ImageAssets

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'assets/auction/pixel_art/auction51_scenes.zip'

class Auction51Art0969(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_archive_includes_all_51_variant_pairs_and_hashes(self):
        self.assertTrue(ARCHIVE.is_file())
        with zipfile.ZipFile(ARCHIVE) as z:
            data=json.loads(z.read('manifest.json'))
            entries=data['cards']
            self.assertEqual(len(entries),51)
            self.assertEqual(data['archetypes'],17)
            self.assertEqual(data['files'],102)
            expected={(cid,rarity) for cid in V22_CARDS for rarity in RARITIES}
            actual={(e['id'],e['rarity']) for e in entries}
            self.assertEqual(expected,actual)
            self.assertNotIn('A017', {e['id'] for e in entries})
            unique=set()
            for e in entries:
                for kind,wh in (('portrait',(295,209)),('banner',(295,78))):
                    filename=e[kind]
                    self.assertEqual(filename,f"{e['id']}_{e['rarity']}_{kind}.png")
                    content=z.read(filename)
                    self.assertEqual(hashlib.sha256(content).hexdigest(),
                                     e[kind+'_sha256'])
                    decoded=pygame.image.load(io.BytesIO(content),filename)
                    self.assertEqual(decoded.get_size(),wh)
                    unique.add(e[kind+'_sha256'])
            self.assertEqual(len(unique),102)

    def test_all_live_card_compositions_and_unmodified_zoom(self):
        loader=ImageAssets()
        for cid in V22_CARDS:
            for rarity in RARITIES:
                original=loader.get_auction_image(cid,rarity,(96,96),mode='contain')
                self.assertIsNotNone(original,(cid,rarity))
                for dims in ((110,22),(136,38),(233,112),(295,209)):
                    art=loader.get_auction_image(cid,rarity,dims,mode='cover')
                    self.assertEqual(art.get_size(),dims)
                    self.assertIs(art,loader.get_auction_image(
                        cid,rarity,dims,mode='cover'))
                # Each exact original sprite remains available for large zoom.
                full=loader.get_auction_image(cid,rarity,(295,209),mode='contain')
                self.assertEqual(full.get_size(),(295,209))
                self.assertIn('auction_scene/'+cid+'_'+rarity+'_banner.png',
                              loader._original)
                self.assertIn('auction_scene/'+cid+'_'+rarity+'_portrait.png',
                              loader._original)

    def test_transparent_character_keeps_environment_visible(self):
        backdrop=pygame.Surface((295,78),pygame.SRCALPHA)
        backdrop.fill((24,51,89,255))
        sprite=pygame.Surface((96,96),pygame.SRCALPHA)
        sprite.fill((0,0,0,0))
        pygame.draw.circle(sprite,(236,87,173,255),(48,48),35)
        out=ImageAssets._compose_original_auction_character(backdrop,sprite,banner=True)
        self.assertEqual(out.get_size(),(295,78))
        self.assertEqual(out.get_at((4,39))[:3],(24,51,89))
        self.assertGreater(out.get_at((147,39)).r,160)

    def test_missing_background_uses_legacy_sprite_without_network(self):
        with patch('game.ui.assets.ROOT_DIR',Path('/nonexistent/auctionhammer')):
            loader=ImageAssets()
            self.assertIsNone(loader.get_auction_image('A001','podstawowa',(135,38)))

if __name__=='__main__':
    unittest.main()
