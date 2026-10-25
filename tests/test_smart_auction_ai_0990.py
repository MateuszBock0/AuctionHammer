"""AuctionHammer 0.9.90: strategic bid ceilings and public-state limits."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from game.core.ai import ComputerOpponent


def fixture(coins=20,number=2,offers=None,bag=()):
    if offers is None:
        offers=[
            SimpleNamespace(uid='A',archetype='A011',atk=8,hp=8,rarity='legendarna'),
            SimpleNamespace(uid='B',archetype='A005',atk=8,hp=8,rarity='podstawowa'),
            SimpleNamespace(uid='C',archetype='A003',atk=8,hp=8,rarity='podstawowa'),
        ]
    players=[
        SimpleNamespace(coins=coins,hp=80,board=[],grave=[]),
        SimpleNamespace(coins=coins,hp=80,board=[],grave=[]),
    ]
    state=SimpleNamespace(number=number,phase='bidding',turn=1,
                          offers=offers,highest_effective=0,
                          current_bid=0,bid_bonus=[0,0],picks={})
    game=SimpleNamespace(players=players,auction=state,auction_bag=list(bag),
                         auction_catalog='v22',phase='auction')
    game.auction_bid=Mock()
    game.auction_pass=Mock()
    return game


class SmartAuctionAI0990(unittest.TestCase):
    def test_easy_never_spends_more_than_half_including_odd_amounts(self):
        ai=ComputerOpponent(1,'łatwy')
        for cash in range(0,101):
            with self.subTest(coins=cash):
                game=fixture(coins=cash,number=40)
                self.assertLessEqual(ai.auction_bid_ceiling(game),cash//2)
                self.assertGreaterEqual(ai.auction_bid_ceiling(game),0)
        self.assertEqual(ai.auction_bid_ceiling(fixture(1,20)),0)
        self.assertEqual(ai.auction_bid_ceiling(fixture(2,20)),1)
        self.assertEqual(ai.auction_bid_ceiling(fixture(10,20)),5)

    def test_bid_action_obeys_real_spend_ceiling_despite_bonus(self):
        game=fixture(coins=9,number=30)
        game.auction.bid_bonus[1]=12
        easy=ComputerOpponent(1,'łatwy')
        # Voucher reduces the required coins to 1, not the 50% cash cap.
        easy.step(game)
        game.auction_bid.assert_called_once_with(1,1)
        game.auction_bid.reset_mock()
        game.auction.highest_effective=17
        # Effective bid 18 needs six REAL coins; easy ceiling = floor(9/2)=4.
        easy.step(game)
        game.auction_bid.assert_not_called()
        game.auction_pass.assert_called_once_with(1)

    def test_first_pick_advantage_is_zero_if_all_three_equivalent(self):
        offers=[
            SimpleNamespace(uid=str(i),archetype='A001',atk=6,hp=8,
                            rarity='podstawowa') for i in range(3)
        ]
        game=fixture(offers=offers)
        normal=ComputerOpponent(1,'normalny')
        hard=ComputerOpponent(1,'trudny')
        self.assertEqual(normal.auction_first_pick_advantage(game),(0.,0.))
        self.assertEqual(normal.auction_bid_ceiling(game),0)
        self.assertEqual(hard.auction_bid_ceiling(game),0)

    def test_normal_spends_more_for_genuinely_better_first_choice(self):
        offers=[
            SimpleNamespace(uid='0',archetype='A001',atk=5,hp=8,
                            rarity='podstawowa'),
            SimpleNamespace(uid='1',archetype='A003',atk=5,hp=8,
                            rarity='podstawowa'),
            SimpleNamespace(uid='2',archetype='A005',atk=5,hp=8,
                            rarity='podstawowa'),
        ]
        a=fixture(offers=offers)
        b=fixture(offers=[
            SimpleNamespace(uid='0',archetype='A011',atk=9,hp=8,
                            rarity='legendarna'),*offers[1:]])
        bot=ComputerOpponent(1,'normalny')
        weak=bot.auction_bid_ceiling(a)
        strong=bot.auction_bid_ceiling(b)
        self.assertGreater(strong,weak)
        self.assertLessEqual(strong,20)

    def test_hard_reserves_coins_when_strong_archetypes_remain(self):
        game=fixture(coins=18,number=4,bag=['A011','A002','A006','A012',
                                           'A014','A015','A009','A010','A004'])
        hard=ComputerOpponent(1,'trudny')
        ceiling_with_future=hard.auction_bid_ceiling(game)
        game.auction_bag=[]
        ceiling_final_auction=hard.auction_bid_ceiling(game)
        self.assertLessEqual(ceiling_with_future,ceiling_final_auction)
        self.assertLess(ceiling_with_future,18)

    def test_hard_responds_to_foe_public_board_in_first_pick_calculation(self):
        game=fixture(coins=24)
        bot=ComputerOpponent(1,'trudny')
        before=bot.auction_first_pick_advantage(game)
        game.players[0].board.extend(['x','y','z'])
        after=bot.auction_first_pick_advantage(game)
        self.assertTrue(all(x>=0 for x in before+after))
        self.assertNotEqual(before,after)
        # The fixture intentionally has NO opponent .hand attribute:
        # looking at hidden cards would have raised AttributeError.

    def test_no_audited_failure_when_minimum_above_willingness_to_pay(self):
        game=fixture(coins=12,number=1)
        game.auction.highest_effective=45
        for difficulty in ('łatwy','normalny','trudny'):
            with self.subTest(difficulty=difficulty):
                game.auction_bid.reset_mock()
                game.auction_pass.reset_mock()
                ComputerOpponent(1,difficulty).step(game)
                game.auction_bid.assert_not_called()
                game.auction_pass.assert_called_once_with(1)

    def test_paired_real_matches_complete_without_ai_illegal_moves(self):
        from tools.simulate_smart_auction_0990 import tournament
        result=tournament(pairs=2,seed=990300)
        self.assertEqual(len(result['comparisons']),2)
        for group in result['comparisons']:
            self.assertEqual(group['matches'],4)
            self.assertEqual(group['stronger_wins']+group['weaker_wins'],4)
            self.assertGreaterEqual(group['total_auctions'],1)
            self.assertTrue(0<=group['stronger_win_rate']<=1)

    def test_legacy_bidding_limit_kept_for_normal_and_hard(self):
        game=fixture(coins=60,number=3)
        game.auction_catalog='v4'
        for difficulty in ('normalny','trudny'):
            self.assertEqual(ComputerOpponent(1,difficulty).auction_bid_ceiling(game),8)


if __name__=='__main__':
    unittest.main()
