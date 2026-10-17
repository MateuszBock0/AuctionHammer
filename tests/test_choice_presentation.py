"""Tests for required on-play choices and the non-obscuring selection interface."""
import os
import unittest
from game.core.models import IllegalMove
from test_engine import force_unit, setup_game


def playable(m, uid):
    for player in m.players:
        for zone in ('hand','deck','grave','board'):
            if uid in getattr(player,zone):
                getattr(player,zone).remove(uid)
    if uid in m.bank:
        m.bank.remove(uid)
    m.cards[uid].owner=0
    m.cards[uid].zone='hand'
    m.players[0].hand.append(uid)
    m.players[0].played_this_turn=False


class RequiredChoiceTests(unittest.TestCase):
    def test_on_play_must_select_legal_target(self):
        m=setup_game(33)
        target=force_unit(m,'S72',0)
        playable(m,'S05')
        m.play('S05')
        self.assertEqual(m.pending.context,'play')
        self.assertEqual(m.pending.owner,0)
        self.assertIn('S72',[c.target for c in m.pending.choices])
        with self.assertRaises(IllegalMove):
            m.end_turn()
        with self.assertRaises(IllegalMove):
            m.play(m.players[0].hand[0])
        index=next(i for i,c in enumerate(m.pending.choices) if c.target==target.uid)
        m.choose(index)
        self.assertIsNone(m.pending)
        self.assertEqual(m.units[target.uid].shield,1)
        self.assertEqual(m.units[target.uid].armor_perm,1)
        m.assert_integrity()

    def test_on_play_with_no_target_still_plays(self):
        m=setup_game(72)
        playable(m,'S01')
        self.assertEqual(m.players[1].board,[])
        m.play('S01')
        self.assertIsNone(m.pending)
        self.assertIn('S01',m.players[0].board)
        m.assert_integrity()


os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
try:
    import pygame
except ImportError:
    pygame=None


@unittest.skipIf(pygame is None,'pygame-ce unavailable')
class SelectionLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        from game.ui.app import SoloApp
        self.app=SoloApp()
        self.app.game=setup_game(91)
        force_unit(self.app.game,'S72',0)
        playable(self.app.game,'S05')
        self.app.game.play('S05')

    def test_selection_is_confined_to_sidebar(self):
        buttons=self.app.choice_bounds()
        self.assertTrue(buttons)
        for _,rect in buttons:
            self.assertGreaterEqual(rect.left,1082)
            self.assertGreaterEqual(rect.top,467)
            self.assertLessEqual(rect.right,1446)
            self.assertLessEqual(rect.bottom,786)
        self.app.draw()

    def test_click_target_on_board(self):
        m=self.app.game
        pos=self.app.slot_rect(0,m.players[0].board.index('S72')).center
        self.app.click(pos)
        self.assertIsNone(m.pending)
        self.assertEqual(m.units['S72'].shield,1)

    def test_choice_sidebar_button(self):
        m=self.app.game
        index=next(i for i,ch in enumerate(m.pending.choices) if ch.target=='S72')
        rect=dict(self.app.choice_bounds())[index]
        self.app.click(rect.center)
        self.assertIsNone(m.pending)
        self.assertEqual(m.units['S72'].armor_perm,1)

    def test_restart_does_not_cancel_required_choice(self):
        m=self.app.game
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_r))
        self.assertIs(self.app.game,m)
        self.assertIsNotNone(m.pending)

    def test_trigger_badges_cover_all_factions(self):
        from game.ui.card_view import TRIGGER_BADGES
        self.assertEqual(len(TRIGGER_BADGES),5)
        for definition in self.app.game.defs.values():
            self.assertIn(definition.trigger,TRIGGER_BADGES)
            label,colour=TRIGGER_BADGES[definition.trigger]
            self.assertTrue(label)
            self.assertEqual(len(colour),3)

    def test_choice_area_is_distinct_from_description(self):
        self.assertEqual(self.app.CHOICES_PER_PAGE,6)
        self.assertGreater(self.app.CHOICE_FIRST_Y,459)
        self.assertTrue(all(467<=r.top and r.bottom<=786 for _,r in self.app.choice_bounds()))
        self.assertGreaterEqual(self.app.AI_ACTION_DELAY_MS,700)

    def test_mulligan_selection_is_highlighted(self):
        self.app.restart()
        m=self.app.game
        uid=m.players[0].hand[0]
        rect=self.app.hand_layout()[uid]
        self.app.click(rect.center)
        self.assertIn(uid,m.players[0].mulligan_selected)
        self.app._draw_board()
        from game import config as cfg
        pixel=self.app.screen.get_at((rect.x-3,rect.y+10))[:3]
        self.assertEqual(pixel,tuple(cfg.GOLD))
        self.app.click(rect.center)
        self.assertNotIn(uid,m.players[0].mulligan_selected)

    def test_haste_play_selects_unit_immediately(self):
        self.app.restart()
        self.app.game=setup_game(307)
        playable(self.app.game,'S66')
        self.app._try_play('S66')
        self.assertEqual(self.app.selected,'S66')
        self.assertIn('hero:1',self.app.game.legal_attacks('S66'))


if __name__=='__main__':
    unittest.main()
