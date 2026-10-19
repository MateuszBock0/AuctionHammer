"""Acceptance of v23 slider and four-record archive pagination."""
from __future__ import annotations

import os, unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from game.ui.app import SoloApp
from test_auction_v22_0931 import ready as v22_ready


class AuctionSliderV23Tests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def test_effective_bid_bounds_are_computed_by_same_rule_as_engine(self):
        g=v22_ready(230300)
        a=g.auction
        if a is None:
            from game.core import auction
            g.round=4
            a=auction.begin(g)
        a.phase='bidding';a.turn=0
        g.players[0].coins=14
        a.highest_effective=7
        a.bid_bonus[0]=0
        app=SoloApp.__new__(SoloApp);app.game=g
        app.auction_slider_key=None;app.auction_slider_value=None
        app.auction_slider_dragging=False
        self.assertEqual(app.auction_slider_bounds(),(8,14))
        app._sync_auction_slider()
        self.assertEqual(app.auction_slider_value,8)
        a.bid_bonus[0]=2
        self.assertEqual(app.auction_slider_bounds(),(6,14))
        app._sync_auction_slider()
        self.assertEqual(app.auction_slider_value,6)
        app._shift_auction_slider(edge='balance')
        self.assertEqual(app.auction_slider_value,14)
        a.highest_effective=10
        app._sync_auction_slider()
        self.assertEqual(app.auction_slider_value,9)
        self.assertEqual(g.players[0].coins,14)  # dragging doesn't pay

    def test_slider_unaffordable_and_exact_balance_edge(self):
        g=v22_ready(230301)
        from game.core import auction
        g.round=4
        a=auction.begin(g)
        a.phase='bidding';a.turn=0
        app=SoloApp.__new__(SoloApp);app.game=g
        app.auction_slider_key=None;app.auction_slider_value=None
        app.auction_slider_dragging=False;app.auction_status=''
        a.highest_effective=5;g.players[0].coins=5
        app._sync_auction_slider()
        self.assertIsNone(app.auction_slider_value)
        with patch.object(g,'auction_bid') as bid:
            app._auction_do('bid')
            bid.assert_not_called()
        g.players[0].coins=6
        app._sync_auction_slider()
        self.assertEqual(app.auction_slider_value,6)


class ArchivePaginationV23Tests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def _app(self,n):
        app=SoloApp.__new__(SoloApp)
        app.menu_page='archive'
        app.menu_message=''
        app.archive_page=0
        app._archive_records=[{'file':f'mecz_{i}.json.gz','version':'0.9.35'} for i in range(n)]
        app._archive_selected_record=None
        app._open_audit_folder=lambda archive=False: True
        return app

    def test_all_lengths_0_1_4_5_8_9_have_right_page_count(self):
        for n,expected in ((0,1),(1,1),(4,1),(5,2),(8,2),(9,3)):
            with self.subTest(n=n):
                app=self._app(n)
                app.archive_page=100
                app._menu_click((10,10))
                self.assertEqual(app.archive_page,expected-1)

    def test_second_page_second_row_selects_global_record_five(self):
        app=self._app(9)
        app._menu_click((800,732))  # next
        self.assertEqual(app.archive_page,1)
        app._menu_click((700,322+1*81+25))  # local row 2 => global index 5
        self.assertEqual(app._archive_selected_record['file'],'mecz_5.json.gz')

    def test_navigation_round_trip_does_not_change_archive_contents(self):
        app=self._app(5)
        old=list(app._archive_records)
        app._menu_click((800,732))
        self.assertEqual(app.archive_page,1)
        app._menu_click((600,732))
        self.assertEqual(app.archive_page,0)
        self.assertEqual(app._archive_records,old)


if __name__=='__main__':
    unittest.main()
