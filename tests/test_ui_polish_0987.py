"""0.9.87: readable hover plaques and better framed square auction art.

Only UI/presentation is tested here. No changes to Match, auction mechanics or
the original set of 51 final auction illustrations.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.status_view import VisibleStatus
from game.core.auction_catalog import V22_CARDS, RARITIES
from game.ui.app import SoloApp
from game.ui.assets import ImageAssets
from game.ui.card_view import CardView, card_zones
from test_auction_placeholder_0919 import auction_game


class UIPolish0987(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_crisp_regions_partition_the_real_art_around_text(self):
        art=pygame.Rect(211,125,233,112)
        overlays=(pygame.Rect(217,225,62,14),
                  pygame.Rect(365,128,74,17),
                  pygame.Rect(236,222,42,17))
        chunks=CardView.artwork_only_regions(art,overlays)
        self.assertTrue(chunks)
        for part in chunks:
            self.assertTrue(art.contains(part))
            self.assertTrue(all(not part.colliderect(x) for x in overlays))
        for y in range(art.top,art.bottom):
            for x in range(art.left,art.right):
                visible=not any(r.collidepoint(x,y) for r in overlays)
                hits=sum(r.collidepoint(x,y) for r in chunks)
                self.assertEqual(hits,int(visible),(x,y))

    def test_card_preview_status_and_readiness_keep_smooth_font_pixels(self):
        game=Match(102)
        card=game.cards['S01']
        view=CardView()
        rect=pygame.Rect(140,100,255,380)
        statuses=(
            VisibleStatus('shield','TARCZ','Tarcza','Jedna tarcza','S20'),
            VisibleStatus('taunt','PROW','Prowokacja','Chroni bohatera','S61'),
            VisibleStatus('poison','TRUC','Trucizna','2 przez 3','S58'),
        )
        surface=pygame.Surface((550,550))
        view.draw(surface,card,rect,statuses=statuses,
                  attacks_total=1,attacks_remaining=1,ready=True)
        art=card_zones(rect)['art']
        def is_crisp(x,y):
            return any(r.collidepoint(x,y) for r in view.pixel_art_regions)
        self.assertTrue(is_crisp(art.centerx,art.centery))
        # Two badges + N counter at artwork bottom and ATAKI at top-right
        # are sampled from smoothscale (not nearest) by the presenter.
        self.assertFalse(is_crisp(art.left+14,art.bottom-11))
        self.assertFalse(is_crisp(art.right-17,art.y+11))
        self.assertTrue(all(art.contains(r) for r in view.pixel_art_regions))

    def test_square_offer_requests_cropped_sides_not_edge_bleed_bands(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        app.menu_open=False
        app.tutorial_welcome_open=False
        app.game=auction_game(1987)
        art=pygame.Surface((116,116),pygame.SRCALPHA)
        with patch.object(app.cards_view.images,'get_auction_image',
                          return_value=art) as load:
            app._draw_auction()
        squares=[call for call in load.call_args_list
                 if len(call.args)>2 and call.args[2]==(116,116)]
        self.assertEqual(len(squares),3)
        self.assertTrue(all(call.kwargs.get('mode')=='cover' for call in squares))
    def test_square_cover_preserves_real_top_and_bottom_rows(self):
        with TemporaryDirectory() as dirname:
            root=Path(dirname)
            folder=root/'assets'/'auction'/'final'
            folder.mkdir(parents=True)
            source=pygame.Surface((295,209),pygame.SRCALPHA)
            source.fill((52,66,73,255))
            pygame.draw.rect(source,(244,40,50),(0,0,295,9))
            pygame.draw.rect(source,(25,66,245),(0,200,295,9))
            pygame.image.save(source,str(folder/'A009_rzadka_portrait.png'))
            with patch('game.ui.assets.ROOT_DIR',root):
                assets=ImageAssets()
                tile=assets.get_auction_image('A009','rzadka',(116,116),
                                              mode='cover')
            self.assertEqual(tile.get_size(),(116,116))
            self.assertGreater(tile.get_at((58,1)).r,200)
            self.assertGreater(tile.get_at((58,114)).b,200)
            self.assertIs(tile,assets.get_auction_image('A009','rzadka',
                                                          (116,116),mode='cover'))

    def test_all_51_auction_variants_fit_square_without_missing_art(self):
        assets=ImageAssets()
        for archetype in V22_CARDS:
            for rarity in RARITIES:
                with self.subTest(archetype=archetype,rarity=rarity):
                    sprite=assets.get_auction_image(archetype,rarity,
                                                    (116,116),mode='cover')
                    self.assertIsNotNone(sprite)
                    self.assertEqual(sprite.get_size(),(116,116))


if __name__=='__main__':
    unittest.main()
