"""v0.9.68: live hover preview of both boards and full-width auction art."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

import pygame
from game.core.engine import Match
from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp
from game.ui.card_view import CardView


def board_match(owner):
    for seed in range(4450,4490):
        match = Match(seed, auctions_enabled=True, auction_catalog='v22',
                      starting_compensation='unit_3_5', audit_enabled=True)
        if match.units['SUM_START_GUARD'].owner == owner:
            match.phase = 'turn'
            return match
    raise AssertionError('Need both first-player permutations')


class BoardHoverAuctionArt0968(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, '_desktop_resolution', return_value=(1536,864)):
            self.app = SoloApp(start_in_menu=True)
        self.app.menu_open = False

    def tearDown(self):
        pygame.quit()

    def test_board_hover_both_owners_dwell_and_no_state_change(self):
        app = self.app
        for owner in (0, 1):
            with self.subTest(owner=owner):
                app.game = board_match(owner)
                uid = 'SUM_START_GUARD'
                rect = app.slot_rect(owner, app.game.slot_of(uid))
                before = digest(state_snapshot(app.game))
                app._update_hover_target(rect.center, now=1000)
                self.assertEqual(app._hover_uid, uid)
                self.assertFalse(app._hover_preview_ready(now=1419))
                self.assertTrue(app._hover_preview_ready(now=1420))
                popup = app._hover_preview_rect(uid)
                self.assertFalse(popup.colliderect(rect))
                self.assertTrue(pygame.Rect(0,0,1480,980).contains(popup))
                with patch.object(app,'mouse_pos',return_value=rect.center):
                    with patch('game.ui.app.pygame.time.get_ticks',return_value=1500):
                        with patch.object(app.cards_view,'draw',
                                          wraps=app.cards_view.draw) as render:
                            app._draw_hover_guidance()
                rendered = [call for call in render.call_args_list
                            if len(call.args) > 1 and
                            call.args[1] is app.game.cards[uid]]
                self.assertEqual(len(rendered),1)
                self.assertIs(rendered[0].kwargs['unit'],app.game.units[uid])
                self.assertIn('statuses',rendered[0].kwargs)
                self.assertIn('attacks_total',rendered[0].kwargs)
                self.assertIn('guard_kills',rendered[0].kwargs)
                self.assertEqual(digest(state_snapshot(app.game)),before)
                app._update_hover_target((1400,940),now=1501)
                self.assertFalse(app._hover_preview_ready(now=2000))

    def test_hover_blocked_by_modals_and_removed_unit(self):
        app=self.app
        app.game=board_match(0)
        uid='SUM_START_GUARD'
        rect=app.slot_rect(0,app.game.slot_of(uid))
        app._update_hover_target(rect.center,now=1000)
        self.assertTrue(app._hover_preview_ready(now=1500))
        app.help_open=True
        self.assertFalse(app._hover_preview_ready(now=1500))
        app.help_open=False
        app.game.units.pop(uid)
        self.assertFalse(app._hover_preview_ready(now=1500))

    def test_auction_art_centers_strip_and_full_zoom_without_crop(self):
        view=CardView()
        placeholder=pygame.Surface((133,38))
        with patch.object(view.images,'get_auction_image',
                          return_value=placeholder) as lookup:
            self.assertIs(view.art('A002','Ludzie',(133,38),
                                   'ATK ±','Generał',rarity='legendarna'),
                          placeholder)
            lookup.assert_called_once_with('A002','legendarna',(133,38),
                                           mode='contain')
        # Cover and contain remain two distinct available presentation modes.
        source=pygame.Surface((96,96),pygame.SRCALPHA)
        source.fill((50,60,70,255))
        pygame.draw.rect(source,(230,40,50,255),(0,0,18,96))
        pygame.draw.rect(source,(20,40,230,255),(78,0,18,96))
        full=view.images.fit_art(source,(133,38),mode='cover')
        self.assertGreater(full.get_at((0,19)).r,190)
        self.assertGreater(full.get_at((132,19)).b,190)
        contained=view.images.fit_art(source,(133,38),mode='contain')
        self.assertEqual(contained.get_size(),(133,38))
        self.assertNotEqual(full.get_at((0,19)),contained.get_at((0,19)))


if __name__=='__main__':
    unittest.main()
