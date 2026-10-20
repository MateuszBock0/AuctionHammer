"""Warm walnut UI palette: visible contrast, read-only painting and continuity."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame

from game.ui.visual_theme import (
    VisualTheme, TAVERN_PANEL_BG, TAVERN_PANEL_INNER,
    TAVERN_TOOLTIP_BG, TAVERN_GOLD, TAVERN_BRASS,
    TAVERN_HOVER_GOLD, TAVERN_TEXT, TAVERN_MUTED,
    TAVERN_SCRIM,
)
from game.ui.app import SoloApp
from game.core.engine import Match
from game.core.audit import digest, state_snapshot


def luminance(rgb):
    vals=[]
    for channel in rgb[:3]:
        x=channel/255
        vals.append(x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4)
    return 0.2126*vals[0]+0.7152*vals[1]+0.0722*vals[2]


def contrast(foreground,background):
    a,b=sorted((luminance(foreground),luminance(background)),reverse=True)
    return (a+0.05)/(b+0.05)


class TavernColorPass(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((400,300))
    def tearDown(self):
        pygame.quit()

    def test_wood_palette_is_warm_and_gold_only_an_accent(self):
        for swatch in (TAVERN_PANEL_BG,TAVERN_PANEL_INNER,
                       TAVERN_TOOLTIP_BG,TAVERN_SCRIM):
            with self.subTest(swatch=swatch):
                self.assertGreater(swatch[0],swatch[1])
                self.assertGreater(swatch[1],swatch[2])
                self.assertLess(max(swatch),90)
        self.assertGreater(TAVERN_GOLD[0],TAVERN_GOLD[2])
        self.assertGreater(TAVERN_HOVER_GOLD[0],TAVERN_GOLD[0])
        self.assertGreater(TAVERN_BRASS[0],TAVERN_BRASS[2])

    def test_parchment_text_meets_ordinary_4_5_to_1_contrast(self):
        for background in (TAVERN_PANEL_BG,TAVERN_PANEL_INNER,
                           TAVERN_TOOLTIP_BG):
            for foreground in (TAVERN_TEXT,TAVERN_MUTED):
                with self.subTest(bg=background,fg=foreground):
                    self.assertGreaterEqual(contrast(foreground,background),4.5)

    def test_actual_drawn_panel_is_brown_with_gold_edge(self):
        surface=pygame.Surface((400,300))
        surface.fill((5,8,12))
        area=pygame.Rect(38,45,242,174)
        VisualTheme().panel(surface,area,TAVERN_TOOLTIP_BG,TAVERN_GOLD,12)
        center=surface.get_at(area.center)[:3]
        self.assertGreater(center[0],center[1])
        self.assertGreater(center[1],center[2])
        self.assertEqual(surface.get_at((area.centerx,area.top))[:3],TAVERN_GOLD)

    def test_tinted_board_keeps_warm_hand_well(self):
        background=VisualTheme.background((1480,980))
        pixel=background.get_at((95,735))[:3]
        self.assertGreater(pixel[0],pixel[2])


class ColorPassCannotChangeGame(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
    def tearDown(self):
        pygame.quit()

    def test_bonus_modal_and_general_hud_are_read_only(self):
        game=next(
            Match(seed,audit_enabled=True,auctions_enabled=True,
                  auction_catalog='v22',
                  starting_compensation='choice_2_5_or_coins')
            for seed in range(42000,42200)
            if Match(seed,auctions_enabled=True,auction_catalog='v22',
                     starting_compensation='choice_2_5_or_coins').first==1
        )
        self.app.game=game
        snapshot=digest(state_snapshot(game))
        with patch.object(self.app,'mouse_pos',return_value=(-1000,-1000)):
            self.app.draw()
        self.assertEqual(digest(state_snapshot(game)),snapshot)
        # Sample an empty left margin of the decorated modal (no text/card).
        panel_pixel=self.app.screen.get_at((347,430))[:3]
        self.assertGreater(panel_pixel[0],panel_pixel[2])

    def test_hover_tooltip_uses_the_named_wooden_color(self):
        app=self.app
        if app._bonus_selection_due():
            app._choose_bonus('coins')
        card_id,area=next(iter(app.hand_layout().items()))
        app.game.cards[card_id].quick_on_first_summon=True
        from game.ui.card_view import card_zones
        pos=(area.x+1,card_zones(area)['art'].y)
        before=digest(state_snapshot(app.game))
        fills=[]
        orig=app._panel
        def spy(rect,fill=None,line=None,radius=14):
            fills.append(fill)
            return orig(rect,fill,line,radius)
        with patch.object(app,'mouse_pos',return_value=pos):
            with patch.object(app,'_panel',side_effect=spy):
                app._draw_hover_guidance()
        self.assertIn(TAVERN_TOOLTIP_BG,fills)
        self.assertEqual(digest(state_snapshot(app.game)),before)


if __name__=='__main__':
    unittest.main()
