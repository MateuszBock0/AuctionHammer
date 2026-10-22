"""Regression tests: hand-card selection is reversible in both UI phases."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.core.audit import digest, state_snapshot
from game.core.engine import Match
from game.ui.app import SoloApp
from test_engine import setup_game, force_unit


def minimal_app(game):
    """Use the production click handler without creating an SDL window."""
    app=SoloApp.__new__(SoloApp)
    app.game=game
    app.selected=None
    app.details_card=None
    app.sidebar_card=None
    app.last_error=''
    app.scroll=0
    app.choice_page=0
    app.tooltip_open=False
    return app


class HandCardDeselectionTests(unittest.TestCase):
    def test_clicking_same_hand_card_twice_clears_selection(self):
        game=setup_game(95801)
        app=minimal_app(game)
        uid=game.players[0].hand[0]
        point=app.hand_layout()[uid].center
        before=digest(state_snapshot(game))

        app.click(point)
        self.assertEqual(app.selected,uid)
        self.assertTrue(app.tooltip_open)
        app.click(point)
        self.assertIsNone(app.selected)
        self.assertFalse(app.tooltip_open)
        self.assertEqual(digest(state_snapshot(game)),before)

    def test_clicking_empty_board_clears_hand_selection_without_playing(self):
        game=setup_game(95802)
        app=minimal_app(game)
        uid=game.players[0].hand[0]
        app.click(app.hand_layout()[uid].center)
        before=digest(state_snapshot(game))

        app.click((80,400))  # empty gap, not a play slot or card
        self.assertIsNone(app.selected)
        self.assertFalse(app.tooltip_open)
        self.assertEqual(digest(state_snapshot(game)),before)
        self.assertIn(uid,game.players[0].hand)

    def test_mulligan_click_again_removes_both_selection_and_marker(self):
        game=Match(95803)
        self.assertEqual(game.phase,'mulligan')
        app=minimal_app(game)
        uid=game.players[0].hand[0]
        point=app.hand_layout()[uid].center

        app.click(point)
        self.assertEqual(app.selected,uid)
        self.assertIn(uid,game.players[0].mulligan_selected)
        app.click(point)
        self.assertIsNone(app.selected)
        self.assertNotIn(uid,game.players[0].mulligan_selected)
        self.assertIn(uid,game.players[0].hand)

    def test_selected_hand_card_does_not_block_selecting_a_ready_attacker(self):
        game=setup_game(95805)
        game.fixed_board_slots=True
        unit=force_unit(game,'S09',0,slot=0)
        game.players[0].played_this_turn=True
        app=minimal_app(game)
        hand_card=game.players[0].hand[0]
        app.click(app.hand_layout()[hand_card].center)
        self.assertEqual(app.selected,hand_card)

        app.click(app.slot_rect(0,0).center)
        self.assertEqual(app.selected,'S09')
        self.assertEqual(app.last_error,'')
        self.assertIn(hand_card,game.players[0].hand)
        app.click(app.hero_rect(1).center)
        self.assertEqual(unit.attacks,1)

    def test_occupied_slot_selects_ally_when_board_has_room(self):
        game=setup_game(95806)
        game.fixed_board_slots=True
        force_unit(game,'S09',0,slot=0)
        app=minimal_app(game)
        hand_card=game.players[0].hand[0]
        app.click(app.hand_layout()[hand_card].center)
        app.click(app.slot_rect(0,0).center)

        self.assertEqual(app.selected,'S09')
        self.assertIn(hand_card,game.players[0].hand)
        self.assertFalse(game.players[0].played_this_turn)

    def test_full_board_legal_replacement_still_works(self):
        from test_engine import force_unit
        game=setup_game(95807)
        game.fixed_board_slots=True
        for slot,uid in enumerate(('S01','S02','S03','S04','S05')):
            force_unit(game,uid,0,slot=slot)
        app=minimal_app(game)
        hand_card=game.players[0].hand[0]
        self.assertTrue(game.can_play(0,hand_card,'S01',0))
        app.click(app.hand_layout()[hand_card].center)
        app.click(app.slot_rect(0,0).center)

        self.assertIn(hand_card,game.players[0].board)
        self.assertEqual(game.slot_of(hand_card),0)
        self.assertNotIn(hand_card,game.players[0].hand)
        self.assertTrue(game.players[0].played_this_turn)
        self.assertEqual(app.last_error,'')

    def test_valid_board_placement_is_unchanged(self):
        game=setup_game(95804)
        app=minimal_app(game)
        uid=game.players[0].hand[0]
        app.click(app.hand_layout()[uid].center)
        app.click(app.slot_rect(0,0).center)

        self.assertIn(uid,game.players[0].board)
        self.assertNotIn(uid,game.players[0].hand)
        self.assertTrue(game.players[0].played_this_turn)
        self.assertEqual(app.last_error,'')


if __name__ == '__main__':
    unittest.main()
