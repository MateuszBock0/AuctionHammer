"""Windows release-candidate smoke: window, real clicks, saves and tooltip paths.

Runs headless on Windows CI. The actual ZIP's updater + SHA256 + rollback
are independently checked by tests/windows/test_portable_launcher_0943.ps1
and the windows-portable release workflow. Physical DPI review remains manual.
"""
from __future__ import annotations

import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import pygame

from game.core.audit import state_snapshot
from game.core.persistence import save_match,load_match
from game.ui.app import SoloApp
from test_balance_buff_v24_0990 import ready,starter


class WindowsReleaseReadiness09104(TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        self.app.help_open=False
        self.app.history_open=False
        self.app.replay_index=None
        self.app.details_card=None
        self.app.confirm_action=None
        self.app.drag_start=None
        self.app.drag_pointer=None

    def tearDown(self):
        pygame.quit()

    def fresh_game(self,seed):
        g=ready(seed)
        g.tavern_beer_enabled=True
        g.tavern_scaled_damage_enabled=True
        self.app.game=g
        self.app.selected=None
        return g

    def test_open_window_click_play_save_load_and_render(self):
        app=self.app
        self.assertEqual(app.screen.get_size(),(1480,980))
        g=self.fresh_game(914201)
        # This mirrors two real logical-space left-clicks in a scaled client.
        hand=next(uid for uid in g.players[0].hand)
        app.click(app.hand_layout()[hand].center)
        self.assertEqual(app.selected,hand)
        app.click(app.slot_rect(0,0).center)
        self.assertIn(hand,g.players[0].board)
        app.update()
        app.draw()
        with TemporaryDirectory() as folder:
            path=Path(folder)/'portable_acceptance.json'
            save_match(g,path)
            restored=load_match(path)
            self.assertEqual(state_snapshot(restored),state_snapshot(g))
            self.assertIn(hand,restored.players[0].board)
            app.game=restored
            app.update()
            app.draw()

    def test_hover_attack_and_brawl_after_paying_mug(self):
        app=self.app
        g=self.fresh_game(914202)
        a=starter(g,'S01',0)
        b=starter(g,'S12',1)
        app.selected=a
        target=app.slot_rect(1,g.slot_of(b)).center
        with patch.object(app,'mouse_pos',return_value=target):
            app.draw()  # render attack information without a game command
        g.players[0].coins=99
        app.click(app.beer_buy_rect().center)
        self.assertEqual(g.beer_turns_remaining,3)
        g.units[a].hp=1
        g.units[b].hp=2
        with patch.object(app,'mouse_pos',return_value=app.brawl_status_rect().center):
            app.draw()  # live brawl help, lethal risk markers, no game mutation
        self.assertEqual(g.beer_turns_remaining,3)

    def test_invalid_click_does_not_move_units(self):
        app=self.app
        g=self.fresh_game(914203)
        before=state_snapshot(g)
        app.click((1080,720))
        self.assertEqual(before,state_snapshot(g))


if __name__=='__main__':
    import unittest
    unittest.main()
