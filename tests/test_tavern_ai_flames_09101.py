"""0.9.101: all AI difficulties decide beer from visible marginal brawl damage."""
from __future__ import annotations

from time import perf_counter
import unittest

import pygame

from game.core.ai import ComputerOpponent
from game.core.audit import state_snapshot
from game.core.beer_strategy import should_ai_order_beer,_projected_board_loss
from game.ui.tavern_art import draw_slot_flamelets
from test_balance_buff_v24_0990 import ready,starter


class SmartBeer09101(unittest.TestCase):
    @staticmethod
    def scene(seed):
        g=ready(seed)
        g.tavern_scaled_damage_enabled=True
        g.players[0].coins=100
        g.players[1].coins=0
        g.active=0
        g.players[0].board[:]=[]  # ready helper has no friendly units normally
        for uid in ('S12','S09','S70','S11','S15'):
            starter(g,uid,1)
            g.units[uid].hp=4
            g.units[uid].shield=0
            g.units[uid].armor_perm=0
            g.units[uid].armor_temp=0
        return g

    def test_all_three_difficulties_purchase_when_scaled_damage_is_clearly_profitable(self):
        for i,difficulty in enumerate(('łatwy','normalny','trudny')):
            g=self.scene(911101+i)
            self.assertTrue(should_ai_order_beer(g,0,difficulty),difficulty)
            cost=g.beer_price(0)
            bot=ComputerOpponent(0,difficulty)
            bot.step(g)
            self.assertEqual(g.beer_orders,1,difficulty)
            self.assertEqual(g.beer_turns_remaining,3)
            self.assertEqual(g.players[0].coins,100-cost)
            self.assertEqual(g.audit_actions[-1]['operation'],'order_beer')
            self.assertFalse(should_ai_order_beer(g,0,difficulty),
                             'No repeated purchases within one AI turn')

    def test_armor_and_shield_block_buying_to_no_real_advantage(self):
        g=self.scene(911104)
        for uid in tuple(g.players[1].board):
            u=g.units[uid]
            u.shield=1
            u.armor_temp=4
        for difficulty in ('łatwy','normalny','trudny'):
            self.assertFalse(should_ai_order_beer(g,0,difficulty))
        self.assertEqual(_projected_board_loss(g,1,3),0.0)

    def test_own_board_can_make_buying_a_bad_trade(self):
        g=self.scene(911105)
        for uid in ('S01','S02','S03','S04','S05'):
            starter(g,uid,0)
            g.units[uid].base_attack=12
            g.units[uid].hp=2
        # Highly valuable friendly cards perish while enemies are small.
        for uid in tuple(g.players[1].board):
            g.units[uid].hp=1
            g.units[uid].base_attack=0
        for difficulty in ('łatwy','normalny','trudny'):
            self.assertFalse(should_ai_order_beer(g,0,difficulty))

    def test_does_not_buy_without_funds_target_or_at_3_turns(self):
        g=self.scene(911106)
        for d in ('łatwy','normalny','trudny'):
            g.beer_turns_remaining=3
            self.assertFalse(should_ai_order_beer(g,0,d))
        g.beer_turns_remaining=0
        g.players[0].coins=0
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))
        g.players[0].coins=100
        for uid in tuple(g.players[1].board):
            g.players[1].board.remove(uid)
        self.assertFalse(should_ai_order_beer(g,0,'trudny'))

    def test_preserve_legacy_easy_and_normal_purchasing_behavior(self):
        g=self.scene(911107)
        g.tavern_scaled_damage_enabled=False
        self.assertFalse(should_ai_order_beer(g,0,'łatwy'))
        # Normal legacy AI was not called by ComputerOpponent.step.
        for diff in ('łatwy','normalny'):
            bot=ComputerOpponent(0,diff)
            bot.step(g)
            self.assertEqual(g.beer_orders,0)

    def test_public_board_only_no_mutation_and_small_cpu_cost(self):
        g=self.scene(911108)
        prior=state_snapshot(g)
        rng=g.rng.getstate()
        measurements=[]
        for i in range(120):
            t0=perf_counter()
            should_ai_order_beer(g,0,('łatwy','normalny','trudny')[i%3])
            measurements.append((perf_counter()-t0)*1000)
        measurements.sort()
        self.assertLess(measurements[int(.95*(len(measurements)-1))],20.)
        self.assertEqual(state_snapshot(g),prior)
        self.assertEqual(g.rng.getstate(),rng)


class BrighterFlames09101(unittest.TestCase):
    @staticmethod
    def render(now,turns,owner=0,index=0):
        screen=pygame.Surface((390,350))
        screen.fill((8,11,15))
        if turns:
            from game.ui.beer_fx import tavern_flame_intensity
            draw_slot_flamelets(screen,pygame.Rect(110,65,148,220),
                                now_ms=now,owner=owner,index=index,
                                strength=tavern_flame_intensity(turns))
        return screen

    @staticmethod
    def painted(surface):
        return sum(1 for y in range(surface.get_height())
                   for x in range(surface.get_width())
                   if surface.get_at((x,y))[:3]!=(8,11,15))

    def test_brighter_flames_scale_and_remain_outside_card(self):
        dark=self.render(0,0)
        embers=self.render(0,1)
        medium=self.render(0,2)
        high=self.render(0,3)
        self.assertEqual(self.painted(dark),0)
        self.assertLess(self.painted(embers),self.painted(medium))
        self.assertLess(self.painted(medium),self.painted(high))
        for surf in (embers,medium,high):
            self.assertEqual(surf.get_at((180,100)),(8,11,15,255))
            self.assertEqual(surf.get_at((180,210)),(8,11,15,255))
            self.assertEqual(surf.get_at((180,279)),(8,11,15,255))

    def test_flames_are_animated_and_differ_between_slots(self):
        a=self.render(0,3)
        b=self.render(135,3)
        c=self.render(0,3,index=3)
        self.assertNotEqual(pygame.image.tobytes(a,'RGB'),
                            pygame.image.tobytes(b,'RGB'))
        self.assertNotEqual(pygame.image.tobytes(a,'RGB'),
                            pygame.image.tobytes(c,'RGB'))


if __name__=='__main__':
    unittest.main()
