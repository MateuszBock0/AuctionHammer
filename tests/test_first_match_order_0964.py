"""0.9.64: stable first-play human-second start, alternating only on NEW games.

The selection lives in SoloApp's live session and uses ordinary seeded Match
instances. Headless simulations and historical signed replay stay unchanged.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp


class AlternatingSeatSessionTests(unittest.TestCase):
    def create_app(self,menu=False):
        with patch.object(SoloApp,'_desktop_resolution',
                          return_value=(1536,864)):
            return SoloApp(start_in_menu=menu)

    def tearDown(self):
        pygame.quit()

    def test_actual_first_game_is_always_human_second_then_alternates(self):
        app=self.create_app(menu=False)
        self.assertEqual(app.game.first,1)
        self.assertEqual(app._next_first_player,0)
        self.assertEqual(app.game.players[0].name,'GRACZ')
        self.assertEqual(app.game.players[1].name,'KOMPUTER')
        for expected in (0,1,0,1,0):
            app.restart()
            self.assertEqual(app.game.first,expected)
            self.assertEqual(app.game.active,expected)
            self.assertEqual(app._next_first_player,1-expected)

    def test_menu_new_match_does_not_skip_hidden_unplayed_game(self):
        app=self.create_app(menu=True)
        self.assertTrue(app.menu_open)
        self.assertTrue(app._first_menu_game_unused)
        self.assertEqual(app.game.first,1)
        first_seed=app.game.seed
        first_signed=digest(state_snapshot(app.game))
        app._menu_click((742,347))   # NOWY MECZ in opening menu
        self.assertFalse(app.menu_open)
        self.assertFalse(app._first_menu_game_unused)
        self.assertEqual(app.game.seed,first_seed)
        self.assertEqual(digest(state_snapshot(app.game)),first_signed)
        self.assertEqual(app.game.first,1)
        app.restart()
        self.assertEqual(app.game.first,0)

    def test_menu_continue_and_guided_use_first_game(self):
        app=self.create_app(menu=True)
        seed=app.game.seed
        app._menu_click((742,427))   # KONTYNUUJ
        self.assertEqual(app.game.seed,seed)
        self.assertFalse(app._first_menu_game_unused)
        app.restart()
        self.assertEqual(app.game.first,0)
        pygame.quit()

        guided=self.create_app(menu=True)
        seed=guided.game.seed
        self.assertTrue(guided._start_guided_match())
        self.assertEqual(guided.game.seed,seed)
        self.assertTrue(guided.tutorial.active)
        self.assertEqual(guided.game.first,1)
        guided.restart()
        self.assertEqual(guided.game.first,0)

    def test_confirmed_restart_advances_once_unconfirmed_does_not(self):
        app=self.create_app()
        first_seed=app.game.seed
        app.game.phase='turn'
        app._request_restart()
        self.assertEqual(app.confirm_action,'restart')
        self.assertEqual(app.game.seed,first_seed)
        app._resolve_confirmation(save=False)
        self.assertEqual(app.game.first,0)
        self.assertIsNone(app.confirm_action)
        app.restart()
        self.assertEqual(app.game.first,1)

    def test_active_game_requires_confirmation_even_if_opening_menu_was_never_used(self):
        app=self.create_app(menu=True)
        original=app.game.seed
        app.game.phase='turn'
        self.assertTrue(app._first_menu_game_unused)
        app._request_restart()
        self.assertEqual(app.confirm_action,'restart')
        self.assertEqual(app.game.seed,original)
        app.confirm_action=None
        app._start_guided_match()
        self.assertEqual(app.confirm_action,'restart')
        self.assertEqual(app.game.seed,original)
        app._resolve_confirmation(save=False)
        self.assertEqual(app.game.first,0)
        self.assertTrue(app.tutorial.active)

    def test_loaded_save_does_not_create_game_and_next_is_opposite(self):
        app=self.create_app(menu=True)
        existing=Match(96411,audit_enabled=True,auctions_enabled=True,
                       auction_catalog='v22',
                       starting_compensation='choice_2_5_or_coins')
        app.menu_page='main'
        with patch('game.ui.app.load_match',return_value=existing):
            app._menu_click((742,505))  # WCZYTAJ ZAPIS
        self.assertIs(app.game,existing)
        self.assertFalse(app._first_menu_game_unused)
        app.restart()
        self.assertEqual(app.game.first,1-existing.first)

    def test_selected_seeds_replay_natively_and_engine_stays_random(self):
        app=self.create_app()
        for _ in range(6):
            game=app.game
            cloned=Match(game.seed,audit_enabled=True,auctions_enabled=True,
                         auction_catalog='v22',
                         starting_compensation='choice_2_5_or_coins',
                         fixed_board_slots=True,
                         tavern_price_v2_enabled=True,
                         tavern_scaled_damage_enabled=True,
                         tavern_min_hp_damage_enabled=True)
            self.assertEqual(cloned.first,game.first)
            self.assertEqual(digest(cloned.audit_initial),
                             digest(game.audit_initial))
            app.restart()
        self.assertEqual({Match(seed).first for seed in range(50)},{0,1})

    def test_invalid_seat_rejected_before_match_creation(self):
        with self.assertRaises(ValueError):
            SoloApp._match_with_first_player(2)


if __name__=='__main__':
    unittest.main()
