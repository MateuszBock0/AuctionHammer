"""AuctionHammer 0.9.102: normal bidding pays for first-pick value, not auction age.

Normal: skip near-equal offers; pursue meaningful premium choices; respect
real coin spend and future reserve. Easy and hard bidding remain unchanged.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from game.core.ai import ComputerOpponent
from test_smart_auction_ai_0990 import fixture


class NormalValueBasedBidding09102(unittest.TestCase):
    def test_negligible_edge_does_not_trigger_baseline_at_any_auction_number(self):
        normal=ComputerOpponent(1,'normalny')
        for round_no in (1,2,6,18,60):
            game=fixture(coins=35,number=round_no)
            normal.auction_first_pick_advantage=lambda _: (.25,.15)
            self.assertEqual(normal.auction_bid_ceiling(game),0)
            normal.step(game)
            game.auction_bid.assert_not_called()
            game.auction_pass.assert_called_once_with(1)

    def test_auction_number_no_longer_increases_willingness_to_pay(self):
        normal=ComputerOpponent(1,'normalny')
        normal.auction_first_pick_advantage=lambda _: (4.0,1.0)
        budgets=[]
        for round_no in (1,4,10,100):
            game=fixture(coins=30,number=round_no)
            budgets.append(normal.auction_bid_ceiling(game))
        self.assertEqual(budgets,[budgets[0]]*len(budgets))
        self.assertGreater(budgets[0],0)

    def test_premium_card_draws_higher_limit_than_minor_edge(self):
        normal=ComputerOpponent(1,'normalny')
        weak=fixture(coins=24,number=3)
        normal.auction_first_pick_advantage=lambda _: (1.5,.2)
        weak_budget=normal.auction_bid_ceiling(weak)
        strong=fixture(coins=24,number=3)
        normal.auction_first_pick_advantage=lambda _: (9.,4.)
        strong_budget=normal.auction_bid_ceiling(strong)
        self.assertGreater(strong_budget,weak_budget+7)
        self.assertGreater(strong_budget,10)
        self.assertLessEqual(strong_budget,24)

    def test_first_choice_considers_denial_to_opponent_not_only_own_pick(self):
        normal=ComputerOpponent(1,'normalny')
        game=fixture(coins=40)
        normal.auction_first_pick_advantage=lambda _: (2.5,0)
        private_gain=normal.auction_bid_ceiling(game)
        normal.auction_first_pick_advantage=lambda _: (2.5,8.)
        with_denial=normal.auction_bid_ceiling(game)
        self.assertGreater(with_denial,private_gain)

    def test_future_auction_reserve_and_last_auction_competition(self):
        normal=ComputerOpponent(1,'normalny')
        normal.auction_first_pick_advantage=lambda _: (32.,20.)
        future=fixture(coins=40,bag=['A001','A002','A003','A004'])
        final=fixture(coins=40,bag=[])
        future_budget=normal.auction_bid_ceiling(future)
        last_budget=normal.auction_bid_ceiling(final)
        self.assertLess(future_budget,last_budget)
        self.assertLessEqual(future_budget,40-max(4,40//6))
        self.assertEqual(last_budget,40)

    def test_short_coins_and_vouchers_use_actual_paid_coins(self):
        normal=ComputerOpponent(1,'normalny')
        normal.auction_first_pick_advantage=lambda _: (14.,8.)
        game=fixture(coins=9,number=4,bag=['A001','A002','A003'])
        budget=normal.auction_bid_ceiling(game)
        self.assertLessEqual(budget,9)
        game.auction.highest_effective=12
        game.auction.bid_bonus[1]=6  # next REAL bid needs 7, not 13
        normal.step(game)
        if budget>=7:
            game.auction_bid.assert_called_once_with(1,7)
        else:
            game.auction_pass.assert_called_once_with(1)
        self.assertLess(budget,9)

    def test_really_strong_offers_are_more_attractive_than_similar_offers(self):
        from types import SimpleNamespace
        normal=ComputerOpponent(1,'normalny')
        weak=[
            SimpleNamespace(uid=str(i),archetype='A001',atk=6,hp=8,
                            rarity='podstawowa') for i in range(3)]
        premium=[
            SimpleNamespace(uid='0',archetype='A011',atk=10,hp=9,
                            rarity='legendarna'),
            SimpleNamespace(uid='1',archetype='A005',atk=5,hp=7,
                            rarity='podstawowa'),
            SimpleNamespace(uid='2',archetype='A003',atk=5,hp=7,
                            rarity='podstawowa')]
        g=fixture(coins=30,number=5,offers=weak)
        self.assertEqual(normal.auction_bid_ceiling(g),0)
        g.auction.offers=premium
        self.assertGreater(normal.auction_bid_ceiling(g),8)

    def test_no_hidden_info_or_rng_and_no_change_to_easy_hard(self):
        game=fixture(coins=25,number=8)
        normal=ComputerOpponent(1,'normalny')
        with patch.object(ComputerOpponent,'auction_first_pick_advantage',
                          return_value=(3.,1.)):
            prior=(game.players[1].coins,game.auction.current_bid,
                   game.auction.highest_effective,list(game.auction_bag))
            for _ in range(10):
                normal.auction_bid_ceiling(game)
            self.assertEqual(prior,
                (game.players[1].coins,game.auction.current_bid,
                 game.auction.highest_effective,list(game.auction_bag)))
        self.assertEqual(ComputerOpponent(1,'łatwy').auction_bid_ceiling(
            fixture(coins=10,number=15)),5)
        old=fixture(coins=60,number=3)
        old.auction_catalog='v4'
        self.assertEqual(normal.auction_bid_ceiling(old),8)
        self.assertEqual(ComputerOpponent(1,'trudny').auction_bid_ceiling(old),8)


if __name__=='__main__':
    unittest.main()
