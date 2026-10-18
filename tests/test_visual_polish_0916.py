"""0.9.16: rzeczywiste fonty, tekstura Pygame i testy kolizji etykiet.

These checks target *logical* canvas coordinates and do not claim to certify
legibility on a physical 125/150% DPI laptop screen.
"""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game import config as cfg
from game.ui.app import SoloApp
from game.ui.card_view import CardView,card_zones
from game.ui.visual_theme import VisualTheme
from game.ui.layout import canvas_to_window,window_to_canvas,preferred_window_size
from game.core.status_view import VisibleStatus
from game.ui.combat_visuals import CombatVisuals


class VisualPolishTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        pygame.quit()

    def _traced_labels(self,draw):
        recorded=[]
        original=self.app._text
        def observer(s,size,x,y,color=None,center=False):
            rect=original(s,size,x,y,color,center)
            recorded.append((str(s),rect.copy()))
            return rect
        self.app._text=observer
        try:draw()
        finally:self.app._text=original
        return recorded

    def _assert_separated_labels(self,items,excluded=None):
        excluded=excluded or ()
        bounds=pygame.Rect(0,0,cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)
        for text,rect in items:
            self.assertTrue(bounds.contains(rect),(text,rect))
        for i,(a,ra) in enumerate(items):
            for b,rb in items[i+1:]:
                if a in excluded or b in excluded:
                    continue
                self.assertFalse(ra.colliderect(rb),(a,ra,b,rb))

    def test_new_background_is_deterministic_and_visible(self):
        theme=VisualTheme()
        a=theme.background((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        b=theme.background((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        self.assertEqual(a.get_size(),b.get_size())
        for point in ((0,0),(400,220),(570,395),(1300,800)):
            self.assertEqual(a.get_at(point),b.get_at(point))
        self.assertNotEqual(a.get_at((40,50)),a.get_at((500,520)))

    def test_panels_slots_and_buttons_preserve_real_click_geometry(self):
        app=self.app
        surface=pygame.Surface((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        theme=app.theme
        for owner in (0,1):
            for i in range(5):
                r=app.slot_rect(owner,i)
                theme.slot(surface,r,owner)
                self.assertTrue(surface.get_rect().contains(r))
        btn=pygame.Rect(535,322,420,61)
        theme.button(surface,btn,hover=True,accent=True)
        self.assertTrue(surface.get_rect().contains(btn))

    def test_header_shortcuts_have_separate_measured_regions(self):
        app=self.app
        logo,mode,help_area=app.header_regions()
        for a,b in ((logo,mode),(mode,help_area),(logo,help_area)):
            self.assertFalse(a.colliderect(b))
        labels=self._traced_labels(app._draw_header)
        self._assert_separated_labels(labels)
        self.assertEqual(len(labels),4)
        self.assertTrue(logo.contains(labels[0][1]))
        self.assertTrue(logo.contains(labels[1][1]))
        self.assertTrue(mode.contains(labels[2][1]))
        self.assertTrue(help_area.contains(labels[3][1]))

    def test_instruction_board_and_full_side_labels_do_not_overlap(self):
        app=self.app
        labels=self._traced_labels(app._draw_board)
        self._assert_separated_labels(labels)
        app.selected=app.game.players[0].hand[0]
        side=self._traced_labels(app._draw_sidebar)
        self._assert_separated_labels(side)

    def test_sidebar_more_than_two_statuses_does_not_hit_details_button(self):
        from test_engine import force_unit
        app=self.app
        if app.game.phase=='mulligan':
            app.game.finish_mulligan(0,[])
        if app.game.phase=='mulligan':
            app.game.finish_mulligan(1,[])
        unit=force_unit(app.game,'S115',0)
        unit.shield=1
        unit.armor_perm=4
        app.game._add_poison('S115',2,3,'S83',0)
        app.selected='S115'
        labels=self._traced_labels(app._draw_sidebar)
        self._assert_separated_labels(labels)
        details_rect=pygame.Rect(1103,686,316,40)
        for name,rect in labels:
            if 'pozostałych efektów' in name:
                self.assertFalse(rect.colliderect(details_rect))
                self.assertLessEqual(rect.bottom,details_rect.top)

    def test_menu_history_replay_and_game_over_legends_do_not_collide(self):
        app=self.app
        app.menu_open=True
        self._assert_separated_labels(self._traced_labels(app._draw_menu))
        app.menu_page='settings'
        self._assert_separated_labels(self._traced_labels(app._draw_menu))
        app.menu_open=False
        for i in range(60):
            app.game._log(f'Wydarzenie {i}: przykładowa długa historia statusu.')
        self._assert_separated_labels(self._traced_labels(app._draw_history_overlay))
        app.replay_index=0
        self._assert_separated_labels(self._traced_labels(app._draw_replay_controls))
        app.replay_index=None
        app.game.phase='finished'
        app.game.winner=0
        self._assert_separated_labels(self._traced_labels(app._draw_gameover))

    def test_all_70_cards_keep_data_inside_nonoverlapping_regions(self):
        app=self.app
        view=CardView()
        surface=pygame.Surface((380,490))
        sizes=((125,195),(148,220),(255,380))
        for card in app.game.cards.values():
            for w,h in sizes:
                with self.subTest(card=card.uid,size=(w,h)):
                    rect=pygame.Rect(18,18,w,h)
                    view.draw(surface,card,rect)
                    zone=card_zones(rect)
                    plan=view.summary_layout(card,rect)
                    self.assertTrue(rect.contains(zone['stats']))
                    self.assertTrue(rect.contains(zone['info']))
                    for box in plan['boxes']:
                        self.assertLessEqual(box.bottom,plan['footer'].top)
                        self.assertFalse(box.colliderect(zone['stats']))
                    self.assertFalse(zone['art'].colliderect(zone['stats']))

    def test_100_125_150_windows_dpi_input_mapping(self):
        app=self.app
        logical=(1480,980)
        for dpi in (1.,1.25,1.5):
            desktop=(round(1920/dpi),round(1080/dpi))
            size=preferred_window_size(desktop,logical)
            from game.ui.layout import fitted_viewport
            viewport=fitted_viewport(size,logical)
            for card,rect in app.hand_layout().items():
                with self.subTest(scale=dpi,card=card):
                    point=canvas_to_window(rect.center,viewport,logical)
                    result=window_to_canvas(point,viewport,logical)
                    self.assertTrue(rect.collidepoint(result))

    def test_cosmetic_animation_summon_and_turn_do_not_mutate_game(self):
        app=self.app
        game=app.game
        before=(game.active,game.round,game.players[0].hp,len(game.units))
        fx=CombatVisuals()
        fx.sync(game,app.slot_rect,app.hero_rect,1000)
        game.active=1-game.active
        fx.sync(game,app.slot_rect,app.hero_rect,1010)
        self.assertIn('turn',{p.kind for p in fx.pulses})
        surface=pygame.Surface((1480,980))
        fx.draw(surface,1200,app.fonts_bold[16])
        self.assertEqual((game.round,game.players[0].hp,len(game.units)),
                         (before[1],before[2],before[3]))


if __name__=='__main__':
    unittest.main()
