"""Reproduce physical and virtual mouse gestures in the Windows portable client."""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.ui.app import SoloApp

class DragAndDropRelease0943(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False

    def tearDown(self):
        pygame.quit()

    def start_match(self,seed):
        game=Match(seed,audit_enabled=True,auctions_enabled=True,
                   auction_catalog='v22',
                   starting_compensation='choice_2_5_or_coins')
        if game.first!=0:
            return None
        self.app.game=game
        self.app.ai.step(game)
        if 1 not in game.mulligan_done:
            self.app.ai.step(game)
        game.finish_mulligan(0,[])
        self.assertEqual(game.phase,'turn')
        self.assertEqual(game.active,0)
        self.app.selected=None
        self.app.drag_start=None
        self.app._hover_uid=None
        self.app.replay_index=None
        self.app.history_open=False
        self.app.details_card=None
        self.app.menu_open=False
        return game

    def gesture(self,uid,target,render_mid_drag=True):
        app=self.app
        rect=app.hand_layout()[uid]
        start=rect.center
        self.assertNotEqual(app.card_under(start),None)
        down=pygame.event.Event(pygame.MOUSEBUTTONDOWN,{'pos':start,'button':1})
        motion=pygame.event.Event(pygame.MOUSEMOTION,{
            'pos':target,'rel':(target[0]-start[0],target[1]-start[1]),'buttons':(1,0,0)})
        up=pygame.event.Event(pygame.MOUSEBUTTONUP,{'pos':target,'button':1})
        with patch.object(app,'_physical_to_virtual',side_effect=lambda pos:pos):
            self.assertTrue(app.handle(down))
            self.assertIsNotNone(app.drag_start)
            self.assertTrue(app.handle(motion))
            if render_mid_drag:
                app.update()
                app.draw()
            self.assertTrue(app.handle(up))
            app.update()
            app.draw()
        self.assertIsNone(app.drag_start)

    def test_drag_each_card_to_own_board_does_not_crash(self):
        checked=0
        for seed in range(300,360):
            game=self.start_match(seed)
            if game is None:continue
            for uid in list(game.players[0].hand):
                # Each card is tested independently against a fresh game.
                game=self.start_match(seed)
                self.assertIn(uid,game.players[0].hand)
                self.gesture(uid,self.app.slot_rect(0,0).center)
                self.assertIn(uid,game.players[0].board)
                checked+=1
            if checked>=25:break
        self.assertGreaterEqual(checked,25)

    def test_drag_outside_board_is_cancelled_without_playing(self):
        game=self.start_match(next(i for i in range(300,450)
                                     if Match(i,starting_compensation='choice_2_5_or_coins').first==0))
        uid=game.players[0].hand[0]
        self.gesture(uid,(1058,740))
        self.assertIn(uid,game.players[0].hand)
        self.assertNotIn(uid,game.players[0].board)

    def test_drag_on_mulligan_does_not_exit_and_keeps_choices(self):
        app=self.app
        if app._bonus_selection_due():
            app._choose_bonus('coins')
        uid=app.game.players[0].hand[0]
        # The gesture must not play any card during a pre-match mulligan.
        self.gesture(uid,app.slot_rect(0,0).center)
        self.assertEqual(app.game.phase,'mulligan')
        self.assertIn(uid,app.game.players[0].hand)

if __name__=='__main__':
    unittest.main()
