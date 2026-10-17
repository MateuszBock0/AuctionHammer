"""Adaptive Windows display tests for Full HD laptops and DPI scaling.

The game keeps a fixed 1480x920 logical canvas. Presentation must fit
the available desktop without cutting the bottom of the screen.
"""
import os
import unittest
from unittest.mock import patch

from game.ui.layout import (
    preferred_window_size, fitted_viewport,
    canvas_to_window, window_to_canvas,
)

LOGICAL=(1480,920)


class AdaptiveGeometryTests(unittest.TestCase):
    def test_full_hd_at_125_percent_scaling(self):
        # 1920x1080 physical pixels -> approximately 1536x864 in many
        # Windows UI coordinate configurations.
        width,height=preferred_window_size((1536,864),LOGICAL)
        self.assertLess(width,1536)
        self.assertLess(height,864)
        self.assertLessEqual(height,864-72)
        self.assertAlmostEqual(width/height,1480/920,delta=0.005)

    def test_full_hd_with_100_percent_scaling(self):
        self.assertEqual(preferred_window_size((1920,1080),LOGICAL),LOGICAL)

    def test_common_laptop_display_sizes(self):
        for desktop in ((1536,864),(1920,1080),(1366,768),
                        (1600,900),(1280,720),(1024,768),(800,600)):
            with self.subTest(desktop=desktop):
                ww,wh=preferred_window_size(desktop,LOGICAL)
                self.assertGreater(ww,0)
                self.assertGreater(wh,0)
                self.assertLess(ww,desktop[0])
                self.assertLess(wh,desktop[1])
                self.assertAlmostEqual(ww/wh,1480/920,delta=0.009)
                rect=fitted_viewport((ww,wh),LOGICAL)
                self.assertLessEqual(rect[0]+rect[2],ww)
                self.assertLessEqual(rect[1]+rect[3],wh)

    def test_window_hitboxes_match_visual_positions(self):
        # Covers top cards, board, sidebar, choice buttons and bottom controls.
        targets=((110,115),(342,285),(500,540),(1118,150),
                 (1250,735),(1201,842),(1420,885))
        for desktop in ((1536,864),(1920,1080),(1366,768),(1024,768)):
            with self.subTest(desktop=desktop):
                size=preferred_window_size(desktop,LOGICAL)
                viewport=fitted_viewport(size,LOGICAL)
                for logical_point in targets:
                    window_point=canvas_to_window(logical_point,viewport,LOGICAL)
                    mapped=window_to_canvas(window_point,viewport,LOGICAL)
                    self.assertIsNotNone(mapped)
                    self.assertAlmostEqual(mapped[0],logical_point[0],delta=2)
                    self.assertAlmostEqual(mapped[1],logical_point[1],delta=2)

    def test_letterbox_clicks_not_mistaken_for_cards(self):
        viewport=fitted_viewport((1600,900),LOGICAL)
        self.assertIsNone(window_to_canvas((viewport[0]-1,450),viewport,LOGICAL))
        self.assertIsNone(window_to_canvas((viewport[0]+viewport[2],450),viewport,LOGICAL))

    def test_bad_dimensions_rejected(self):
        for desktop in ((0,1080),(1920,0),(-1,100)):
            with self.assertRaises(ValueError):
                preferred_window_size(desktop,LOGICAL)


os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
try:
    import pygame
except ImportError:
    pygame=None


@unittest.skipIf(pygame is None,"pygame-ce not available")
class AdaptiveWindowIntegrationTests(unittest.TestCase):
    def setUp(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        pygame.quit()

    def test_opening_window_is_inside_available_desktop(self):
        size=self.app.window.get_size()
        self.assertEqual(size,preferred_window_size((1536,864),LOGICAL))
        self.assertEqual(self.app.screen.get_size(),LOGICAL)
        self.app.draw()

    def test_clicks_match_rendered_controls_after_resize(self):
        event=pygame.event.Event(pygame.VIDEORESIZE,{"w":1000,"h":670})
        with patch.object(self.app,"_desktop_resolution",return_value=(1536,864)):
            self.assertTrue(self.app.handle(event))
        viewport=tuple(self.app._viewport())
        for point in ((200,190),(1182,808),(1200,878)):
            pixel=canvas_to_window(point,viewport,LOGICAL)
            mapped=self.app._physical_to_virtual(pixel)
            self.assertAlmostEqual(mapped[0],point[0],delta=2)
            self.assertAlmostEqual(mapped[1],point[1],delta=2)
        self.app.draw()

    def test_f11_is_available_even_with_details_open(self):
        uid=self.app.game.players[0].hand[0]
        self.app.details_card=uid
        with patch.object(self.app,"_toggle_fullscreen") as toggle:
            self.app.handle(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_F11}))
            toggle.assert_called_once_with()


if __name__=="__main__":
    unittest.main()
