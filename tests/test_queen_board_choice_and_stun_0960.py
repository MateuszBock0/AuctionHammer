"""Regression tests: queen board-click variants and explicit stunned-attack UX.

Only UI click routing and presentation change; signed game actions still use
Match.choose(index), not new engine operations or free-slot spawn placement.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.ui.app import SoloApp
from game.core.status_view import active_statuses
from game.ui.attack_view import attack_display
from test_auction_v22_0931 import ready, award
from test_auction_v4_engine import place_basic
from test_hand_card_deselection import minimal_app


class QueenBoardChoiceRegressionTests(unittest.TestCase):
    def queen_pending(self, tier=0, seed=96001):
        game=ready(seed)
        uid=award(game,'A010',tier=tier,zone='board')
        game.end_turn()
        self.assertIsNotNone(game.pending)
        self.assertEqual(game.pending.uid,uid)
        self.assertEqual(game.pending.context,'end')
        return game,uid,minimal_app(game)

    def test_clicking_queen_selects_growth_not_summon(self):
        game,uid,app=self.queen_pending(seed=96001)
        base_atk=game.units[uid].atk
        before=set(game.units)
        self.assertIn('grow',{c.mode for c in game.pending.choices})
        self.assertIn('summon',{c.mode for c in game.pending.choices})

        app.click(app.slot_rect(0,game.slot_of(uid)).center)
        self.assertIsNone(game.pending)
        self.assertEqual(set(game.units),before)
        self.assertEqual(game.units[uid].atk,base_atk+1)
        self.assertEqual(app.last_error,'')

    def test_clicking_empty_friendly_slot_selects_summoning(self):
        for tier in (0,1,2):
            with self.subTest(tier=tier):
                game,uid,app=self.queen_pending(tier=tier,seed=96010+tier)
                old_atk=game.units[uid].atk
                empty_slot=next(i for i in range(5) if game.unit_at(0,i) is None)
                app.click(app.slot_rect(0,empty_slot).center)
                self.assertIsNone(game.pending)
                self.assertEqual(game.units[uid].atk,old_atk)
                self.assertEqual(len([x for x in game.players[0].board
                                      if x.startswith('SUM')]),(1,2,2)[tier])
                self.assertEqual(app.last_error,'')

    def test_full_board_queen_cannot_pick_unavailable_summon(self):
        game=ready(96020)
        uid=award(game,'A010',zone='board')
        for cid in ('S01','S02','S03','S04'):
            place_basic(game,cid)
        game.end_turn()
        self.assertEqual({c.mode for c in game.pending.choices},{'grow'})
        app=minimal_app(game)
        # No vacant own slots and clicking enemy-side empty slot is inert.
        app.click(app.slot_rect(1,2).center)
        self.assertIsNotNone(game.pending)
        app.click(app.slot_rect(0,game.slot_of(uid)).center)
        self.assertIsNone(game.pending)
        self.assertEqual(len(game.players[0].board),5)

    def test_other_queen_choices_and_existing_side_panel_still_work(self):
        game,uid,app=self.queen_pending(seed=96021)
        # Existing choice buttons are still supported; no mouse target required.
        selected=next(i for i,c in enumerate(game.pending.choices)
                      if c.mode=='grow')
        app.click(dict(app.choice_bounds())[selected].center)
        self.assertIsNone(game.pending)

    def test_no_global_click_hijacking_for_other_pending_cards(self):
        game=ready(96022)
        uid=award(game,'A010',zone='board')
        game.end_turn()
        game.auction_awards[uid]['archetype']='A009'
        app=minimal_app(game)
        app.click(app.slot_rect(0,game.slot_of(uid)).center)
        self.assertIsNotNone(game.pending)


class StunBadgeRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,960)):
            cls.app=SoloApp()
        cls.screen=pygame.Surface((700,550))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_stunned_fast_attacker_explains_no_attack_instead_of_1_of_1(self):
        game=ready(96030)
        cid=place_basic(game,'S105',owner=0)
        unit=game.units[cid]
        game._add_effect(cid,'quick',source='temporary',expires=game.players[0].turn_count)
        game._add_effect(cid,'stun',source='S74',positive=False,
                         expires=game.players[0].turn_count+1)
        statuses=active_statuses(game,cid)
        self.assertTrue(any(st.category=='quick' for st in statuses))
        self.assertTrue(any(st.category=='stun' for st in statuses))
        self.assertEqual(game.legal_attacks(cid),[])
        attack=attack_display(game,cid)
        self.assertFalse(attack.ready)

        rect=pygame.Rect(50,70,148,220)
        with patch.object(self.app.cards_view,'_pill',
                          wraps=self.app.cards_view._pill) as render_pill:
            self.app.cards_view.draw(self.screen,game.cards[cid],rect,unit,
                                     statuses=statuses,ready=attack.ready,
                                     attacks_remaining=attack.remaining,
                                     attacks_total=attack.limit)
        labels=[c.args[2] for c in render_pill.call_args_list
                if len(c.args)>=3]
        self.assertIn('OGŁUSZONY',labels)
        self.assertNotIn('ATAKI 1/1',labels)


if __name__=="__main__":
    unittest.main()
