"""0.9.44: mouse-friendly quit + precise inactive/hover card rendering."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.models import Effect
from game.core.audit import state_snapshot,digest
from game.ui.app import SoloApp
from game.ui.attack_view import inactive_card_reason
from game.ui.card_view import CardView,card_zones


def guard_game():
    match=Match(4451,auctions_enabled=True,auction_catalog='v22',
                starting_compensation='unit_3_5',audit_enabled=True)
    assert 'SUM_START_GUARD' in match.units
    return match


class CombatAvailabilityVisualTests(unittest.TestCase):
    def test_stun_has_priority_and_removal_restores_original_appearance(self):
        game=guard_game()
        uid='SUM_START_GUARD'
        u=game.units[uid]
        owner=game.players[u.owner]
        owner.turn_count=2
        u.played_turn=1
        self.assertEqual(inactive_card_reason(game,uid),'')
        u.effects.append(Effect('stun',remaining=1,source=uid))
        self.assertEqual(inactive_card_reason(game,uid),'OGŁUSZONA')
        u.effects.clear()
        self.assertEqual(inactive_card_reason(game,uid),'')

    def test_attack_limit_double_attack_and_own_turn_are_engine_based(self):
        game=guard_game()
        uid='SUM_START_GUARD'
        u=game.units[uid]
        p=game.players[u.owner]
        p.turn_count=2
        u.played_turn=1
        u.attacks=1
        self.assertEqual(inactive_card_reason(game,uid),'ATAKI WYKORZYSTANE')
        u.effects.append(Effect('double',source=uid))
        self.assertEqual(inactive_card_reason(game,uid),'')
        u.attacks=2
        self.assertEqual(inactive_card_reason(game,uid),'ATAKI WYKORZYSTANE')
        u.effects.clear()
        u.attacks=0
        game.active=1-u.owner
        self.assertEqual(inactive_card_reason(game,uid),'',
                         'Waiting for the next turn must not gray every unit')

    def test_fresh_unit_without_fast_attack_is_muted_but_quick_is_not(self):
        game=guard_game()
        uid='SUM_START_GUARD'
        u=game.units[uid]
        game.players[u.owner].turn_count=u.played_turn
        self.assertEqual(inactive_card_reason(game,uid),'NOWA JEDNOSTKA')
        u.effects.append(Effect('quick',source=uid))
        self.assertEqual(inactive_card_reason(game,uid),'')

    def test_no_muting_in_mulligan_or_for_missing_unit(self):
        game=guard_game()
        uid='SUM_START_GUARD'
        game.units[uid].effects.append(Effect('stun'))
        self.assertEqual(inactive_card_reason(game,uid),'')
        self.assertEqual(inactive_card_reason(game,'missing'),'')
        game.phase='finished'
        self.assertEqual(inactive_card_reason(game,uid),'')

    def test_grayscale_only_art_keeps_stats_readable_and_hover_is_subtle(self):
        pygame.init()
        try:
            game=guard_game()
            card=game.cards['SUM_START_GUARD']
            unit=game.units['SUM_START_GUARD']
            view=CardView()
            rect=pygame.Rect(120,140,148,220)
            a=pygame.Surface((520,480))
            b=pygame.Surface((520,480))
            c=pygame.Surface((520,480))
            view.draw(a,card,rect,unit,dim=False)
            view.draw(b,card,rect,unit,dim=True)
            view.draw(c,card,rect,unit,hover=True)
            zone=card_zones(rect)
            rgb=b.get_at(zone['art'].center)[:3]
            self.assertLessEqual(max(rgb)-min(rgb),3)
            self.assertEqual(a.get_at(zone['stats'].center),
                             b.get_at(zone['stats'].center),
                             'Readability of ATK/HP must not change')
            point=(rect.x-1,rect.centery)
            self.assertNotEqual(a.get_at(point),c.get_at(point))
        finally:
            pygame.quit()


class ExitAndBoardDrawingTests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)

    def tearDown(self):
        pygame.quit()

    def mouseup(self,pos):
        return pygame.event.Event(pygame.MOUSEBUTTONUP,{'pos':pos,'button':1})

    def test_visible_main_menu_exit_really_exits_on_click(self):
        app=self.app
        app.game.phase='mulligan'
        app.menu_open=True
        with patch.object(app,'_physical_to_virtual',side_effect=lambda x:x):
            self.assertFalse(app.handle(self.mouseup(app.menu_exit_rect().center)))

    def test_header_exit_asks_about_unsaved_game_and_can_cancel(self):
        app=self.app
        app.menu_open=False
        app.game.phase='turn'
        before=digest(state_snapshot(app.game))
        with patch.object(app,'_physical_to_virtual',side_effect=lambda x:x):
            self.assertTrue(app.handle(self.mouseup(app.exit_button_rect().center)))
        self.assertEqual(app.confirm_action,'quit')
        self.assertEqual(before,digest(state_snapshot(app.game)))
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_ESCAPE}))
        self.assertIsNone(app.confirm_action)
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_menu_exit_does_not_bypass_save_confirmation_mid_match(self):
        app=self.app
        app.menu_open=True
        app.menu_page='main'
        app.game.phase='turn'
        with patch.object(app,'_physical_to_virtual',side_effect=lambda x:x):
            self.assertTrue(app.handle(self.mouseup(app.menu_exit_rect().center)))
        self.assertEqual(app.confirm_action,'quit')

    def test_board_uses_only_engine_reason_and_does_not_mutate_match(self):
        app=self.app
        app.menu_open=False
        game=guard_game()
        app.game=game
        uid='SUM_START_GUARD'
        u=game.units[uid]
        game.players[u.owner].turn_count=2
        u.played_turn=1
        u.attacks=1
        state=digest(state_snapshot(game))
        with patch.object(app.cards_view,'draw',wraps=app.cards_view.draw) as painted:
            with patch.object(app,'mouse_pos',return_value=(0,0)):
                app._draw_board()
        args=[call for call in painted.call_args_list if
              len(call.args)>2 and call.args[2] is game.cards[uid]]
        # CardView.draw(screen,card,rect,unit,...) — identify by card object.
        args=[call for call in painted.call_args_list if
              len(call.args)>1 and call.args[1] is game.cards[uid]]
        self.assertEqual(len(args),1)
        self.assertTrue(args[0].kwargs['dim'])
        self.assertEqual(state,digest(state_snapshot(game)))

    def test_hover_receives_boolean_for_hand_and_board(self):
        app=self.app
        app.menu_open=False
        game=guard_game()
        app.game=game
        uid=game.players[0].hand[0]
        position=app.hand_layout()[uid].center
        with patch.object(app,'mouse_pos',return_value=position):
            with patch.object(app.cards_view,'draw',wraps=app.cards_view.draw) as painted:
                app._draw_board()
        hand=[call for call in painted.call_args_list if
              len(call.args)>1 and call.args[1] is game.cards[uid]]
        self.assertEqual(len(hand),1)
        self.assertTrue(hand[0].kwargs['hover'])

if __name__=='__main__':
    unittest.main()
