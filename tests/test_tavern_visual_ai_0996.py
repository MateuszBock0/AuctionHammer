"""AuctionHammer 0.9.96 — lightweight tavern visual fx and expert buy policy."""
from __future__ import annotations

from time import perf_counter
import unittest

from game.core.ai import ComputerOpponent
from game.core.beer_strategy import should_ai_order_beer
from game.ui.beer_fx import beer_fx_state
from test_balance_buff_v24_0990 import ready,starter


class BeerVisual0996(unittest.TestCase):
    def test_pour_frames_end_automatically_and_sway_max_two_pixels(self):
        self.assertEqual(beer_fx_state(1000,None),(1.0,0,False))
        self.assertEqual(beer_fx_state(1000,1000),(0.0,0,True))
        self.assertEqual(beer_fx_state(1300,1000),(0.5,1,True))
        self.assertEqual(beer_fx_state(1600,1000)[0],1.0)
        self.assertFalse(beer_fx_state(1600,1000)[2])
        self.assertEqual(beer_fx_state(1800,1000),(1.0,0,False))
        for t in range(0,1100,9):
            p,sway,pouring=beer_fx_state(1000+t,1000)
            self.assertGreaterEqual(p,0.0)
            self.assertLessEqual(p,1.0)
            self.assertLessEqual(abs(sway),2)
        self.assertEqual(beer_fx_state(1010,1000,False),(1.0,0,False))

    def test_visuals_are_readonly_and_independent_from_engine(self):
        g=ready(99601)
        pre=(g.beer_turns_remaining,g.beer_orders,
             g.rng.getstate(),tuple(x.coins for x in g.players))
        for idx in range(1200):
            beer_fx_state(idx*7,30)
        post=(g.beer_turns_remaining,g.beer_orders,
              g.rng.getstate(),tuple(x.coins for x in g.players))
        self.assertEqual(pre,post)


class BeerBuyingExpert0996(unittest.TestCase):
    def _advantage(self,seed=99610,player=0):
        g=ready(seed)
        g.players[player].coins=100
        g.players[1-player].coins=0
        for uid in ('S12','S09','S70','S11','S15'):
            starter(g,uid,1-player)
            g.units[uid].hp=1
            g.units[uid].shield=0
            g.units[uid].armor_temp=0
            g.units[uid].armor_perm=0
        g.active=player
        return g

    def test_hard_buys_once_when_enemy_board_will_suffer(self):
        g=self._advantage()
        bot=ComputerOpponent(0,'trudny')
        self.assertTrue(should_ai_order_beer(g,0,'trudny'))
        cost=g.beer_price(0)
        bot.step(g)
        self.assertEqual(g.players[0].coins,100-cost)
        self.assertEqual(g.beer_orders,1)
        self.assertEqual(g.beer_turns_remaining,3)
        self.assertEqual(g.audit_actions[-1]['operation'],'order_beer')
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))
        g.assert_integrity()

    def test_normal_and_easy_do_not_purchase_automatically(self):
        for difficulty in ('łatwy','normalny'):
            g=self._advantage(seed=99611+len(difficulty))
            bot=ComputerOpponent(0,difficulty)
            bot.step(g)
            self.assertEqual(g.beer_orders,0)
            self.assertNotEqual(g.audit_actions[-1]['operation'],'order_beer')

    def test_expert_skips_bad_board_trade_and_no_target(self):
        g=self._advantage(seed=99623)
        for uid in tuple(g.players[1].board):
            g.units[uid].hp=g.units[uid].max_hp
            g.units[uid].shield=1
            g.units[uid].armor_temp=3
        # Protected healthy enemies cannot be harmed by three 1-dmg ticks.
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))
        g.players[1].board.clear()
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))

    def test_reserve_for_future_auction(self):
        g=self._advantage(seed=99624)
        cost=g.beer_price(0)
        self.assertLess(cost,100)
        g.players[0].coins=cost  # exact price is affordable, but no reserve
        self.assertTrue(g.can_order_beer(0))
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))

    def test_existing_effect_stops_duplicate_buy(self):
        g=self._advantage(seed=99625)
        self.assertTrue(should_ai_order_beer(g,0,'trudny'))
        g.beer_turns_remaining=3
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))
        g.beer_turns_remaining=1
        self.assertTrue(should_ai_order_beer(g,0,'trudny'))

    def test_constant_small_cpu_budget_no_rng_and_no_match_mutation(self):
        g=self._advantage(seed=99626)
        original=(g.rng.getstate(),g.beer_orders,g.players[0].coins,
                  len(g.audit_actions))
        timings=[]
        for _ in range(150):
            t0=perf_counter()
            should_ai_order_beer(g,0,'trudny')
            timings.append((perf_counter()-t0)*1000)
        timings.sort()
        self.assertLess(timings[round(.95*(len(timings)-1))],20.,
                        'Expert tavern decision should be a tiny board scan')
        self.assertEqual(original,
                         (g.rng.getstate(),g.beer_orders,g.players[0].coins,
                          len(g.audit_actions)))


if __name__=='__main__':
    unittest.main()
