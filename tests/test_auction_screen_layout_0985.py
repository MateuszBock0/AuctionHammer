"""0.9.85: real auction screen — portrait/text zones and bid HUD geometry.

These tests check the Pygame layout, not a cosmetic reference image.
"""
from __future__ import annotations

import os
from unittest.mock import patch
import unittest

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.ui.app import SoloApp
from game.core.audit import digest,state_snapshot
from test_auction_placeholder_0919 import auction_game


class AuctionScreenLayout0985(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1536,864))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        self.app.game=auction_game(1985)

    def test_each_offer_has_real_extra_vertical_space_and_separate_zones(self):
        modal=pygame.Rect(203,25,1076,819)
        for i in range(3):
            r=self.app.auction_offer_rect(i)
            zones=self.app.auction_offer_zones(i)
            with self.subTest(i=i):
                self.assertTrue(modal.contains(r))
                self.assertEqual((r.top,r.bottom,r.height),(159,620,461))
                for name,rect in zones.items():
                    self.assertTrue(r.contains(rect),(name,rect,r))
                self.assertEqual(self.app.auction_inspection_rect(i),
                                 zones["inspect"])
                # Distinct art, rarity, trigger and description strips,
                # with no text permitted to overlay the character's face.
                order=("name","art","rarity","trigger","description",
                       "inspect","hint")
                for first,second in zip(order,order[1:]):
                    self.assertLessEqual(zones[first].bottom+5,
                                         zones[second].top,(first,second))
                self.assertLess(zones["art"].right,zones["atk"].left)
                self.assertLess(zones["art"].right,zones["hp"].left)

    def test_bid_header_number_footer_slider_and_buttons_have_distinct_rows(self):
        tiles=self.app.auction_bid_tiles()
        leader,own,summary=(tiles[k] for k in ("leader","own","summary"))
        slider=self.app.auction_slider_rect()
        controls=[self.app.auction_control_rect(key) for key in ("pass","bid")]
        self.assertFalse(leader.colliderect(own))
        self.assertEqual((leader.top,leader.bottom),(633,707))
        self.assertEqual((summary.top,summary.bottom),(713,734))
        self.assertGreaterEqual(summary.top,leader.bottom+5)
        self.assertGreaterEqual(slider.top,summary.bottom+10)
        for ctrl in controls:
            self.assertGreaterEqual(ctrl.top,slider.bottom+10)
            self.assertLess(ctrl.bottom,832)
        for i in range(3):
            card=self.app.auction_offer_rect(i)
            self.assertLess(card.bottom,leader.top)
            self.assertLess(card.bottom,own.top)

    def test_actual_auction_text_never_intersects_portraits_or_other_text(self):
        app=self.app
        for mode in ("bidding","picking"):
            if mode=="picking":
                a=app.game.auction
                app.game.auction_pass(a.turn)
                app.game.auction_pass(app.game.auction.turn)
            actual=app._text
            boxes=[]
            before=digest(state_snapshot(app.game))
            def record(label,size,x,y,color=None,center=False):
                rect=actual(label,size,x,y,color,center)
                boxes.append((str(label),rect))
                return rect
            with patch.object(app,"_text",side_effect=record):
                app._draw_auction()
            self.assertEqual(digest(state_snapshot(app.game)),before)
            for i,(label,a) in enumerate(boxes):
                for other,b in boxes[i+1:]:
                    self.assertFalse(a.colliderect(b),
                                     (mode,label,a,other,b))
                for k in range(3):
                    art=app.auction_offer_zones(k)["art"]
                    self.assertFalse(a.colliderect(art),
                                     (mode,label,a,"portrait",k,art))
            self.assertTrue(any("POZIOM" in t for t,_ in boxes))
            self.assertTrue(any("PEŁNA" not in t and "SKUTECZNA" in t
                                for t,_ in boxes) if mode=="bidding" else True)

    def test_leader_own_bid_text_is_padded_inside_wooden_panels(self):
        app=self.app
        tiles=app.auction_bid_tiles()
        lines=[]
        original=app._text
        def capture(label,size,x,y,color=None,center=False):
            rendered=original(label,size,x,y,color,center)
            lines.append((str(label),rendered))
            return rendered
        with patch.object(app,"_text",side_effect=capture):
            app._draw_auction()
        for prefix,tile in (("PROWADZI:",tiles["leader"]),
                            ("SKUTECZNA OFERTA",tiles["leader"]),
                            ("TWOJA OFERTA",tiles["own"]),
                            ("MINIMUM",tiles["own"]),
                            ("BONUS A018",tiles["summary"])):
            matches=[rect for text,rect in lines if text.startswith(prefix)]
            self.assertEqual(len(matches),1,(prefix,matches))
            inner=(tile if prefix=="BONUS A018" else tile.inflate(-12,-8))
            self.assertTrue(inner.contains(matches[0]),
                            (prefix,matches[0],tile))
        self.assertTrue(any(t.isdigit() for t,_ in lines))

    def test_live_v22_screenshot_archetypes_and_all_rarities_have_no_collisions(self):
        """A010 / A018 / A001 are the actual cards shown in user screenshot."""
        from game.core import auction
        from game.core.auction import AuctionOffer
        from game.core.auction_catalog import stats_v22,RARITIES
        from test_auction_v22_0931 import ready as v22_ready
        app=self.app
        game=v22_ready(985985)
        game.round=4
        auction.begin(game)
        app.game=game
        app.auction_inspect_index=None
        ids=('A010','A018','A001')
        for tier in range(3):
            # Source card IDs and all variant summaries are actual v22 data.
            game.auction.offers=[
                AuctionOffer(f'AUC001{cid}',stats_v22(cid,3)[1],
                             stats_v22(cid,3)[0],RARITIES[tier],1,cid)
                for cid in ids]
            before=digest(state_snapshot(game))
            labels=[]
            real=app._text
            def capture(text,size,x,y,color=None,center=False):
                rect=real(text,size,x,y,color,center)
                labels.append((str(text),rect))
                return rect
            with patch.object(app,'_text',side_effect=capture):
                app._draw_auction()
            self.assertEqual(digest(state_snapshot(game)),before)
            self.assertTrue(any('KONIEC TURY' in t for t,_ in labels))
            self.assertTrue(any('POZIOM' in t for t,_ in labels))
            for i,(text,rect) in enumerate(labels):
                for other,other_rect in labels[i+1:]:
                    self.assertFalse(rect.colliderect(other_rect),
                                     (tier,text,rect,other,other_rect))
                for n in range(3):
                    self.assertFalse(rect.colliderect(
                        app.auction_offer_zones(n)['art']),
                        (tier,text,rect,'art',n))

    def test_auction_rarity_labels_use_brown_silver_gold_without_layout_changes(self):
        from game.ui.app import AUCTION_RARITY_COLORS
        from game import config as cfg

        from dataclasses import replace

        app=self.app
        app.game.auction.offers=[
            replace(offer,rarity=tier)
            for offer,tier in zip(app.game.auction.offers,
                                  ('podstawowa','rzadka','legendarna'))
        ]

        labels=[]
        draw=app._text
        def capture(text,size,x,y,color=None,center=False):
            rect=draw(text,size,x,y,color,center)
            labels.append((str(text),color,rect))
            return rect

        with patch.object(app,'_text',side_effect=capture):
            app._draw_auction()

        for i,offer in enumerate(app.game.auction.offers):
            stripe=app.auction_offer_zones(i)['rarity']
            rarity=[(color,rect) for text,color,rect in labels
                    if text==offer.rarity.upper() and stripe.contains(rect)]
            level=[(color,rect) for text,color,rect in labels
                   if text==f'POZIOM {offer.level}' and stripe.contains(rect)]
            self.assertEqual(len(rarity),1,(offer.rarity,rarity))
            self.assertEqual(len(level),1,(offer.rarity,level))
            self.assertEqual(rarity[0][0],AUCTION_RARITY_COLORS[offer.rarity])
            self.assertEqual(level[0][0],cfg.MUTED)
            self.assertLess(rarity[0][1].right,level[0][1].left)

    def test_inspection_button_is_in_new_position_and_remains_clickable(self):
        app=self.app
        for i in range(3):
            app.auction_inspect_index=None
            app._auction_click(app.auction_inspection_rect(i).center)
            self.assertEqual(app.auction_inspect_index,i)


if __name__=="__main__":
    unittest.main()
