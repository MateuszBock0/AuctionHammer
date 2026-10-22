"""0.9.52: physical click/drag acceptance and rarity graphics in Pygame."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from game import config as cfg
from game.ui.app import SoloApp
from game.ui.layout import canvas_to_window
from game.ui.visual_theme import VisualTheme
from test_engine import force_unit


class BoardDragAcceptance(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, '_desktop_resolution', return_value=(1920,1080)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self._start_turn()

    def tearDown(self):
        pygame.quit()

    def _start_turn(self):
        g=self.app.game
        g.phase='turn';g.active=0;g.pending=None
        g.players[0].turn_count=max(1,g.players[0].turn_count)
        g.players[0].played_this_turn=False
        self.assertTrue(g.fixed_board_slots)

    def _window(self,canvas_pos):
        return canvas_to_window(canvas_pos,tuple(self.app._viewport()),
                                (cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))

    def _drag(self,uid,destination):
        source=self.app.hand_layout()[uid].center
        down=pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                {'button':1,'pos':self._window(source)})
        up=pygame.event.Event(pygame.MOUSEBUTTONUP,
                              {'button':1,'pos':self._window(destination)})
        self.assertTrue(self.app.handle(down))
        self.assertTrue(self.app.handle(up))
        self.assertIsNone(self.app.drag_start)

    def test_drag_fifth_slot_in_three_window_sizes(self):
        for size in ((1480,980),(1184,784),(986,653)):
            with self.subTest(window=size):
                self.app.window=pygame.display.set_mode(size,pygame.RESIZABLE)
                self.app.restart()
                self._start_turn()
                g=self.app.game
                uid=g.players[0].hand[0]
                self._drag(uid,self.app.slot_rect(0,4).center)
                self.assertEqual(g.slot_of(uid),4)
                self.assertIsNone(g.unit_at(0,0))
                g.assert_integrity()

    def test_gap_between_fields_never_autoplays(self):
        g=self.app.game;uid=g.players[0].hand[0]
        a=self.app.slot_rect(0,0);b=self.app.slot_rect(0,1)
        gap=((a.right+b.left)//2,a.centery)
        before=len(g.audit_actions)
        self.assertIsNone(self.app.slot_under(0,gap))
        self._drag(uid,gap)
        self.assertIn(uid,g.players[0].hand)
        self.assertEqual(len(g.audit_actions),before)
        self.assertIn('pięciu pól',self.app.last_error)
        g.assert_integrity()

    def test_drop_on_opponent_board_is_not_a_play(self):
        g=self.app.game;uid=g.players[0].hand[0]
        before=len(g.audit_actions)
        self._drag(uid,self.app.slot_rect(1,3).center)
        self.assertIn(uid,g.players[0].hand)
        self.assertEqual(len(g.audit_actions),before)
        g.assert_integrity()

    def test_occupied_field_on_nonfull_board_cannot_replace(self):
        g=self.app.game
        occupied=force_unit(g,'S01',0,slot=2)
        uid=next(x for x in g.players[0].hand if x!=occupied.uid)
        before=len(g.audit_actions)
        self._drag(uid,self.app.slot_rect(0,2).center)
        self.assertEqual(g.unit_at(0,2),occupied.uid)
        self.assertIn(uid,g.players[0].hand)
        self.assertEqual(len(g.audit_actions),before)
        g.assert_integrity()

    def test_full_board_replacement_preserves_other_positions(self):
        g=self.app.game
        for i,card in enumerate(('S01','S27','S34','S35','S108')):
            force_unit(g,card,0,slot=i)
        candidate=g.players[0].hand[0]
        old=g.unit_at(0,2)
        self._drag(candidate,self.app.slot_rect(0,2).center)
        self.assertEqual(g.unit_at(0,2),candidate)
        self.assertNotIn(old,g.units)
        self.assertEqual([g.slot_of(x) for x in g.players[0].board],
                         [0,1,2,3,4])
        g.assert_integrity()

    def test_death_gap_can_be_reused_without_shifting_neighbours(self):
        g=self.app.game
        for slot,card in ((0,'S01'),(2,'S27'),(4,'S34')):
            force_unit(g,card,0,slot=slot)
        g._remove_unit('S27',death=True)
        candidate=g.players[0].hand[0]
        self._drag(candidate,self.app.slot_rect(0,2).center)
        self.assertEqual(g.slot_of(candidate),2)
        self.assertEqual(g.slot_of('S01'),0)
        self.assertEqual(g.slot_of('S34'),4)
        g.assert_integrity()

    def test_drag_without_prior_selection_shows_legal_targets(self):
        g=self.app.game;uid=g.players[0].hand[0]
        self.app.selected=None
        self.assertEqual(self.app._play_target_rects(),[])
        self.app.drag_start=(self.app.hand_layout()[uid].center,uid)
        self.assertEqual(self.app._play_target_rects(),
                         [self.app.slot_rect(0,i) for i in range(5)])
        self.app.drag_start=None


class RarityFrameAcceptance(unittest.TestCase):
    def test_distinct_frames_leave_card_center_untouched(self):
        pygame.init()
        try:
            original=(33,55,77,255)
            images=[]
            rect=pygame.Rect(60,55,180,280)
            for rarity in ('podstawowa','rzadka','legendarna'):
                surface=pygame.Surface((320,420),pygame.SRCALPHA)
                surface.fill(original)
                VisualTheme().rarity_frame(surface,rect,rarity,animate=False)
                self.assertEqual(tuple(surface.get_at(rect.center)),original)
                images.append(pygame.image.tostring(surface,'RGBA'))
            self.assertEqual(len(set(images)),3)
        finally:
            pygame.quit()


if __name__=='__main__':
    unittest.main()
