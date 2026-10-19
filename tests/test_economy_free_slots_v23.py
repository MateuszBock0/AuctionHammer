"""Regression: payout for vacant own board slots after full turn resolution.

Both human (0) and computer (1) earn 5-board_size coins at THEIR own
turn end. Full-round +1 income, auctions, saves and historical card effects
must remain independent.
"""
import tempfile
import unittest
from pathlib import Path
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.persistence import save_match, load_match
from test_engine import setup_game,force_unit


class FreeSlotsIncomeTests(unittest.TestCase):
    def test_all_six_board_occupancies(self):
        identities=("S01","S02","S03","S04","S05")
        for n in range(6):
            with self.subTest(occupied=n):
                game=setup_game(2300+n)
                game.first=0
                game.active=0
                game.round=1
                for uid in identities[:n]:
                    force_unit(game,uid,0)
                before=game.players[0].coins
                opponent=game.players[1].coins
                game.end_turn()
                self.assertEqual(game.players[0].coins-before,5-n)
                self.assertEqual(game.players[1].coins,opponent)
                self.assertTrue(any(f'+{5-n} monet za {5-n} wolnych miejsc' in msg
                                    for msg in game.events))

    def test_both_players_get_own_income_plus_full_round_coin(self):
        game=setup_game(2310)
        game.first=0
        game.active=0
        game.round=1
        force_unit(game,'S01',0)
        original=(game.players[0].coins,game.players[1].coins)
        game.end_turn()
        self.assertEqual(game.players[0].coins,original[0]+4)
        self.assertEqual(game.players[1].coins,original[1])
        for uid in ('S02','S03','S04','S05'):
            force_unit(game,uid,1)
        game.end_turn()
        self.assertEqual(game.players[0].coins,original[0]+4+1)
        self.assertEqual(game.players[1].coins,original[1]+1+1)
        self.assertEqual(game.round,2)
        game.assert_integrity()

    def test_auction_resume_never_pays_twice(self):
        game=Match(seed=2311,auctions_enabled=True,auction_catalog='v22')
        game.finish_mulligan(0,[])
        game.finish_mulligan(1,[])
        game.first=0
        game.active=1
        game.players[1].turn_count=max(1,game.players[1].turn_count)
        game.round=3
        before=(game.players[0].coins,game.players[1].coins)
        game.end_turn()
        self.assertEqual(game.phase,'auction')
        self.assertEqual(game.players[0].coins,before[0]+1)
        self.assertEqual(game.players[1].coins,before[1]+5+1)
        self.assertFalse(game._space_income_due)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'state.json'
            save_match(game,path)
            game=load_match(path)
        while game.auction is not None and game.auction.phase=='bidding':
            game.auction_pass(game.auction.turn)
        while game.auction is not None and game.auction.phase=='picking':
            picked=set(game.auction.picks.values())
            uid=next(x.uid for x in game.auction.offers if x.uid not in picked)
            game.auction_pick(game.auction.turn,uid)
        self.assertEqual(game.players[0].coins,before[0]+1)
        self.assertEqual(game.players[1].coins,before[1]+5+1)
        self.assertFalse(game._space_income_due)
        game.assert_integrity()

    def test_legacy_save_without_new_flag_loads(self):
        game=setup_game(2312)
        game.__dict__.pop('_space_income_due')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'legacy.json'
            save_match(game,path)
            loaded=load_match(path)
        self.assertFalse(loaded._space_income_due)

    def test_ai_uses_vacant_slot_money_in_bidding_ceiling(self):
        game=Match(seed=2313,auctions_enabled=True,auction_catalog='v22')
        game.finish_mulligan(0,[])
        game.finish_mulligan(1,[])
        game.round=4
        # Open auction by the same official flow used by Match.
        from game.core import auction as auction_rules
        game.players[1].coins=12
        game.auction= None
        game.auction_history=[]
        game.auction_bag=list(game.auction_bag)
        auction_rules.begin(game)
        game.auction.turn=1
        game.auction.phase='bidding'
        game.auction.current_bid=0
        game.auction.highest_bidder=None
        game.auction.highest_effective=0
        opponent=ComputerOpponent(player=1,difficulty='normalny')
        opponent.step(game)
        self.assertEqual(game.auction.highest_bidder,1)
        self.assertEqual(game.auction.current_bid,1)


if __name__=='__main__':
    unittest.main()
