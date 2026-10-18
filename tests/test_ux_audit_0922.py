"""Regression tests derived from the completed 0.9.21 match audit (seed 205882526).

The original audit remains immutable; UI preflight must prevent repeats of
rejected actions without changing Match commands, rules or replay hashes.
"""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

from game.ui.app import SoloApp
from test_auction_foundation_0921 import ready
from test_engine import setup_game,force_unit


def shell(game,selected=None):
    app=SoloApp.__new__(SoloApp)
    app.game=game
    app.selected=selected
    app.last_error=''
    app.scroll=0
    app.auction_bid_text=''
    app.auction_status=''
    app.details_card=None
    app.sidebar_card=None
    app.tooltip_open=False
    return app


class AuctionBidPreflightTests(unittest.TestCase):
    def test_unaffordable_minimum_does_not_call_engine(self):
        game=ready(2201)
        game.auction.turn=0
        game.auction.current_bid=2
        game.players[0].coins=2
        app=shell(game)
        with patch.object(game,'auction_bid') as bid:
            app._auction_do('min')
            app._auction_do('bid')
            bid.assert_not_called()
        self.assertIn('PASUJ',app.auction_status)
        self.assertEqual(game.auction.current_bid,2)

    def test_unaffordable_custom_amount_does_not_call_engine(self):
        game=ready(2202)
        game.auction.turn=0
        game.auction.current_bid=1
        game.players[0].coins=4
        app=shell(game)
        app.auction_bid_text='20'
        with patch.object(game,'auction_bid') as bid:
            app._auction_do('bid')
            bid.assert_not_called()
        self.assertIn('4 monet',app.auction_status)

    def test_too_small_bid_does_not_call_engine(self):
        game=ready(2203)
        game.auction.turn=0
        game.auction.current_bid=4
        game.players[0].coins=10
        app=shell(game)
        app.auction_bid_text='3'
        with patch.object(game,'auction_bid') as bid:
            app._auction_do('bid')
            bid.assert_not_called()
        self.assertIn('5 monet',app.auction_status)

    def test_affordable_bid_still_uses_real_engine(self):
        game=ready(2204)
        game.auction.turn=0
        game.players[0].coins=12
        app=shell(game)
        app.auction_bid_text='5'
        app._auction_do('bid')
        self.assertEqual(game.auction.current_bid,5)
        self.assertEqual(game.auction.highest_bidder,0)
        self.assertEqual(app.auction_status,'')


class BoardAndAttackFeedbackTests(unittest.TestCase):
    def test_full_board_highlights_only_replaceable_units(self):
        g=setup_game(2211)
        for uid in list(g.bank)[:5]:
            force_unit(g,uid,0)
        app=shell(g,selected=g.players[0].hand[0])
        self.assertEqual(len(app._play_replacement_targets()),5)
        spent=g.players[0].board[0]
        g.units[spent].attacks=1
        self.assertNotIn(spent,app._play_replacement_targets())
        with patch.object(g,'play') as play:
            self.assertFalse(app._try_play(app.selected))
            play.assert_not_called()
        self.assertIn('Plansza 5/5',app.last_error)
        valid=g.players[0].board[1]
        self.assertTrue(app._try_play(app.selected,valid))
        self.assertNotIn(valid,g.players[0].board)

    def test_second_play_same_turn_does_not_create_failed_audit(self):
        g=setup_game(2212)
        app=shell(g,selected=g.players[0].hand[0])
        g.players[0].played_this_turn=True
        with patch.object(g,'play') as play:
            self.assertFalse(app._try_play(app.selected))
            play.assert_not_called()
        self.assertIn('jedną kartę',app.last_error)

    def test_taunt_explained_without_illegal_attack_command(self):
        g=setup_game(2213)
        force_unit(g,'S33',1)  # Innate Prowokacja on the enemy board
        force_unit(g,'S09',0)
        app=shell(g,selected='S09')
        self.assertIn('S33',g.legal_attacks('S09'))
        self.assertNotIn('hero:1',g.legal_attacks('S09'))
        with patch.object(g,'attack') as attack:
            app.click(app.hero_rect(1).center)
            attack.assert_not_called()
        self.assertIn('PROWOKACJA',app.last_error)

    def test_exhausted_unit_explained_without_engine_call(self):
        g=setup_game(2214)
        u=force_unit(g,'S09',0)
        u.attacks=1
        app=shell(g,selected='S09')
        with patch.object(g,'attack') as attack:
            app.click(app.hero_rect(1).center)
            attack.assert_not_called()
        self.assertIn('nie może teraz atakować',app.last_error)


class S91S09BalanceRegression(unittest.TestCase):
    def test_two_rounds_of_double_attack_deal_52_as_logged(self):
        """Audit observation, not a balance endorsement or a rules change."""
        g=setup_game(2221)
        g.cards['S09'].hand_turns=4   # 10 ATK, quality level 1
        u=force_unit(g,'S09',0)
        self.assertEqual((u.atk,u.ability_level),(10,1))
        g._add_effect('S09','double',source='S91')
        for ending_hp in (74,48):
            self.assertIn('hero:1',g.legal_attacks('S09'))
            g.attack('S09','hero:1')
            g.attack('S09','hero:1')
            self.assertEqual(g.players[1].hp,ending_hp)
            self.assertEqual(g.legal_attacks('S09'),[])
            if ending_hp!=48:
                g.end_turn()
                g.end_turn()


if __name__=='__main__':
    unittest.main()
