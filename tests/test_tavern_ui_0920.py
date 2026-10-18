"""Tavern 0.9.20 acceptance: actual offline art, text-safe controls and fallback."""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from game.ui.visual_theme import ASSET_ROOT, VisualTheme
from game.ui.app import SoloApp


class TavernUIStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1480,980))
    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_required_wood_and_tavern_files_present(self):
        for name in ("tavern_scene.jpg","tavern_panel.png","tavern_plaque.png",
                     "gold_divider.png","wood_ambient.png"):
            with self.subTest(name=name):
                path=ASSET_ROOT/name
                self.assertTrue(path.is_file(),path)
                self.assertGreater(path.stat().st_size,2000)

    def test_loaded_tavern_background_contains_real_art(self):
        theme=VisualTheme()
        bg=theme.background((1480,980))
        self.assertEqual(bg.get_size(),(1480,980))
        # Strong visual variation: original photographed interior remains
        # visible outside the dark opaque wells, not a flat stone surface.
        self.assertNotEqual(bg.get_at((45,90)),bg.get_at((800,30)))
        self.assertNotEqual(bg.get_at((1100,250)),bg.get_at((1210,650)))

    def test_ornaments_and_panels_render_at_real_menu_sizes(self):
        theme=VisualTheme()
        surface=pygame.Surface((1480,980))
        surface.fill((0,0,0))
        theme.carved_panel(surface,pygame.Rect(432,186,625,632),opacity=98)
        theme.tavern_plaque(surface,pygame.Rect(530,120,380,58))
        theme.ornament(surface,565,228,350,22)
        self.assertNotEqual(surface.get_at((600,230)),(0,0,0,255))

    def test_all_menu_and_auction_labels_stay_inside_canvas(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            app=SoloApp()
        for draw in (app._draw_menu,app._draw_auction):
            seen=[]
            original=app._text
            def measured(label,size,x,y,color=None,center=False):
                rect=original(label,size,x,y,color,center)
                seen.append((label,rect))
                return rect
            if draw==app._draw_auction:
                for _ in range(6):
                    if app.game.phase=='auction':break
                    if app.game.phase=='mulligan':
                        app.game.finish_mulligan(0,[])
                        app.game.finish_mulligan(1,[])
                    else:app.game.end_turn()
            app.menu_open=draw==app._draw_menu
            with patch.object(app,"_text",side_effect=measured):
                draw()
            self.assertGreater(len(seen),5)
            for label,rect in seen:
                self.assertTrue(app.screen.get_rect().contains(rect),(label,rect))


if __name__=="__main__":
    unittest.main()
