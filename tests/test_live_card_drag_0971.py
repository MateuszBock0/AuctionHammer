"""v0.9.71 — visible hand-card drag, legal placement and read-only return."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.core.audit import digest, state_snapshot
from game.core.engine import Match
from game.ui.app import SoloApp


class LiveCardDrag0971(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, "_desktop_resolution", return_value=(1536, 864)):
            self.app = SoloApp(start_in_menu=True)
        app = self.app
        app.menu_open = False
        for seed in range(300, 450):
            game = Match(seed, audit_enabled=True, auctions_enabled=True,
                         auction_catalog="v22",
                         starting_compensation="choice_2_5_or_coins")
            if game.first == 0:
                break
        else:
            self.fail("Could not find player-one seed")
        app.game = game
        app.ai.step(game)
        if 1 not in game.mulligan_done:
            app.ai.step(game)
        game.finish_mulligan(0, [])
        self.assertEqual((game.phase, game.active), ("turn", 0))
        app.drag_start = None
        app.drag_pointer = None
        app.drag_return = None
        app._hover_uid = None
        app.tutorial_welcome_open = False

    def tearDown(self):
        pygame.quit()

    def send(self, kind, point, **extra):
        event = pygame.event.Event(kind, {"pos": point, **extra})
        with patch.object(self.app, "_physical_to_virtual", side_effect=lambda p: p):
            return self.app.handle(event)

    def start_and_move(self, uid, end, grab=None):
        rect = self.app.hand_layout()[uid]
        grab = grab or (rect.left + 17, rect.top + 41)
        self.send(pygame.MOUSEBUTTONDOWN, grab, button=1)
        self.send(pygame.MOUSEMOTION, end,
                  buttons=(1, 0, 0),
                  rel=(end[0]-grab[0], end[1]-grab[1]))
        return rect, grab

    def test_drag_follows_pointer_without_jump_or_game_mutation(self):
        app = self.app
        uid = app.game.players[0].hand[0]
        before = digest(state_snapshot(app.game))
        rect, grab = self.start_and_move(uid, (602, 426))
        visual = app._floating_hand_card()
        self.assertIsNotNone(visual)
        self.assertEqual(visual[0], uid)
        self.assertFalse(visual[2])
        self.assertEqual(visual[1].topleft,
                         (rect.left + 602-grab[0], rect.top + 426-grab[1]))
        with patch.object(app.cards_view, "draw", wraps=app.cards_view.draw) as draw:
            app.draw()
        calls = [c for c in draw.call_args_list
                 if len(c.args) > 1 and c.args[1] is app.game.cards[uid]]
        # A floating card is drawn once above the board, not duplicated in hand.
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[2], visual[1])
        self.assertEqual(digest(state_snapshot(app.game)), before)

        self.send(pygame.MOUSEMOTION, (790, 300),
                  buttons=(1, 0, 0), rel=(188, -126))
        self.assertEqual(app._floating_hand_card()[1].topleft,
                         (visual[1].x+188, visual[1].y-126))
        self.assertEqual(digest(state_snapshot(app.game)), before)

    def test_release_outside_table_uses_eased_return_without_move(self):
        app = self.app
        uid = app.game.players[0].hand[0]
        initial = app.hand_layout()[uid]
        before = digest(state_snapshot(app.game))
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1000):
            self.start_and_move(uid, (1040, 720))
            from_pos = app._floating_hand_card()[1].topleft
            self.assertTrue(self.send(pygame.MOUSEBUTTONUP, (1040, 720), button=1))
            self.assertIsNone(app.drag_start)
            self.assertIsNotNone(app.drag_return)
            self.assertEqual(app._floating_hand_card()[1].topleft, from_pos)
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1090):
            midway = app._floating_hand_card()
            self.assertTrue(midway[2])
            self.assertNotEqual(midway[1].topleft, from_pos)
            self.assertNotEqual(midway[1].topleft, initial.topleft)
            app.draw()
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1180):
            self.assertIsNone(app._floating_hand_card())
            self.assertIsNone(app.drag_return)
        self.assertIn(uid, app.game.players[0].hand)
        self.assertEqual(digest(state_snapshot(app.game)), before)

    def test_drop_on_real_slot_places_card_once(self):
        app = self.app
        uid = app.game.players[0].hand[0]
        target = app.slot_rect(0, 0).center
        self.start_and_move(uid, target)
        self.assertTrue(any(rect.collidepoint(target)
                            for rect in app._play_target_rects()))
        self.assertTrue(self.send(pygame.MOUSEBUTTONUP, target, button=1))
        self.assertIn(uid, app.game.players[0].board)
        self.assertNotIn(uid, app.game.players[0].hand)
        self.assertIsNone(app.drag_return)
        self.assertIsNone(app.drag_start)

    def test_drop_in_gap_never_falls_back_to_arbitrary_slot(self):
        app = self.app
        uid = app.game.players[0].hand[0]
        target = (app.slot_rect(0, 0).right + 10, app.OWN_Y + 50)
        self.assertIsNone(app.slot_under(0, target))
        before = digest(state_snapshot(app.game))
        self.start_and_move(uid, target)
        self.assertTrue(self.send(pygame.MOUSEBUTTONUP, target, button=1))
        self.assertIn(uid, app.game.players[0].hand)
        self.assertIsNotNone(app.drag_return)
        self.assertEqual(digest(state_snapshot(app.game)), before)

    def test_click_without_motion_still_selects_card(self):
        app = self.app
        uid = app.game.players[0].hand[0]
        spot = app.hand_layout()[uid].center
        self.send(pygame.MOUSEBUTTONDOWN, spot, button=1)
        self.assertIsNone(app._floating_hand_card())
        self.assertTrue(self.send(pygame.MOUSEBUTTONUP, spot, button=1))
        self.assertEqual(app.selected, uid)
        self.assertIsNone(app.drag_return)

    def test_animation_switch_disables_return_but_not_dragging(self):
        app = self.app
        app.animations_enabled = False
        uid = app.game.players[0].hand[0]
        self.start_and_move(uid, (1040, 720))
        self.assertIsNotNone(app._floating_hand_card())
        self.send(pygame.MOUSEBUTTONUP, (1040, 720), button=1)
        self.assertIsNone(app.drag_return)
        self.assertIn(uid, app.game.players[0].hand)


if __name__ == "__main__":
    unittest.main()
