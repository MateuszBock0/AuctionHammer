"""v0.9.100 brawl: signed opt-in N..1 AoE, old replay safety, live flames."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pygame

from game.core.engine import Match
from game.core.audit import state_snapshot, verify_replay
from game.core.persistence import save_match,load_match
from game.ui.beer_fx import tavern_flame_intensity
from game.ui.tavern_art import draw_slot_flamelets
from test_balance_buff_v24_0990 import ready,starter


class ScaledTavernBrawl09100(unittest.TestCase):
    @staticmethod
    def scene(seed):
        game=ready(seed)
        game.tavern_scaled_damage_enabled=True
        game.players[0].coins=200
        a=starter(game,'S01',0)
        b=starter(game,'S12',1)
        for uid in (a,b):
            game.units[uid].max_hp=60
            game.units[uid].hp=60
        return game,a,b

    def test_three_two_one_to_both_boards_and_zero_afterwards(self):
        g,a,b=self.scene(910001)
        g.order_beer(0)
        self.assertEqual(g.beer_turns_remaining,3)
        for remaining,expected_hp,damage in ((2,57,3),(1,55,2),(0,54,1)):
            g.end_turn()
            self.assertEqual(g.beer_turns_remaining,remaining)
            self.assertEqual(g.units[a].hp,expected_hp)
            self.assertEqual(g.units[b].hp,expected_hp)
            self.assertTrue(any(f'{damage} DMG' in e['text']
                                for e in g.event_journal[-15:]))
        g.end_turn()
        self.assertEqual(g.units[a].hp,54)
        self.assertEqual(g.units[b].hp,54)
        g.assert_integrity()

    def test_two_mugs_stack_turns_and_next_damage_six(self):
        g,a,b=self.scene(910002)
        g.order_beer(0)
        g.order_beer(0)
        self.assertEqual(g.beer_turns_remaining,6)
        g.end_turn()
        self.assertEqual(g.beer_turns_remaining,5)
        self.assertEqual(g.units[a].hp,54)
        self.assertEqual(g.units[b].hp,54)

    def test_normal_shields_and_armor_apply_to_scaled_hit(self):
        g,a,b=self.scene(910003)
        g.units[a].shield=1
        g.units[b].armor_temp=2
        g.order_beer(0)
        g.end_turn()  # next hit is 3: shield absorbs 3; armor absorbs 2
        self.assertEqual(g.units[a].hp,60)
        self.assertEqual(g.units[a].shield,0)
        self.assertEqual(g.units[b].hp,59)
        self.assertEqual(g.units[b].armor_temp,0)
        g.end_turn()  # next hit 2
        self.assertEqual(g.units[a].hp,58)
        self.assertEqual(g.units[b].hp,57)

    def test_new_signed_replay_and_old_unflagged_rule(self):
        g=Match(99570,audit_enabled=True,auctions_enabled=True,
                auction_catalog='v22',starting_compensation='coins',
                tavern_scaled_damage_enabled=True)
        self.assertTrue(g.tavern_scaled_damage_enabled)
        self.assertTrue(g.audit_initial['ruleset_state'][
            'tavern_scaled_damage_enabled'])
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        bought=False
        ticks=0
        for _ in range(110):
            if g.phase=='auction':
                auction=g.auction
                if auction.phase=='bidding':
                    g.auction_pass(auction.turn)
                else:
                    choices=[c for c in auction.offers if c.uid not in auction.picks.values()]
                    g.auction_pick(auction.turn,choices[0].uid)
                continue
            if g.phase!='turn':
                break
            if not bought and g.can_order_beer(g.active):
                g.order_beer(g.active)
                bought=True
            before=g.beer_turns_remaining
            g.end_turn()
            if bought and before>g.beer_turns_remaining:
                ticks+=1
            if bought and ticks>=3:
                break
        self.assertTrue(bought)
        self.assertEqual(ticks,3)
        payload={'complete_from_start':True,'seed':g.seed,
                 'version':'0.9.100','initial_state':g.audit_initial,
                 'actions':g.audit_actions,'internal_events':g.audit_internal,
                 'event_journal':g.event_journal,
                 'final_state':state_snapshot(g),
                 'summary':{'ruleset_version':g.ruleset_version,
                            'vacant_slot_income_enabled':g.vacant_income_enabled}}
        self.assertTrue(verify_replay(
            payload,lambda seed,**kwargs:Match(seed,audit_enabled=True,**kwargs)))
        old=Match(99570,audit_enabled=True,auctions_enabled=True,
                  auction_catalog='v22')
        self.assertNotIn('tavern_scaled_damage_enabled',
                         old.audit_initial['ruleset_state'])
        self.assertFalse(old.tavern_scaled_damage_enabled)

    def test_new_save_and_legacy_missing_flag(self):
        g,a,b=self.scene(910004)
        g.order_beer(0)
        g.end_turn()
        with TemporaryDirectory() as d:
            path=Path(d)/'brawl.json'
            save_match(g,path)
            restored=load_match(path)
            self.assertTrue(restored.tavern_scaled_damage_enabled)
            self.assertEqual(restored.beer_turns_remaining,2)
            self.assertEqual(state_snapshot(restored),state_snapshot(g))
            old=ready(910005)
            del old.tavern_scaled_damage_enabled
            save_match(old,path)
            historical=load_match(path)
            self.assertFalse(historical.tavern_scaled_damage_enabled)

    def test_turn_based_light_level_and_distinct_animated_pixels(self):
        self.assertEqual([tavern_flame_intensity(n) for n in (0,1,2,3,6)],
                         [0.0,0.32,0.62,1.0,1.0])
        def pixels(ms,turns,slot=2):
            surface=pygame.Surface((430,400))
            surface.fill((12,18,23))
            if turns:
                draw_slot_flamelets(surface,pygame.Rect(140,75,148,220),
                                    now_ms=ms,index=slot,owner=1,
                                    strength=tavern_flame_intensity(turns))
            self.assertEqual(surface.get_at((215,180)),(12,18,23,255))
            return pygame.image.tobytes(surface,'RGB')
        self.assertNotEqual(pixels(0,0),pixels(0,1))
        self.assertNotEqual(pixels(0,1),pixels(0,2))
        self.assertNotEqual(pixels(0,2),pixels(0,3))
        self.assertNotEqual(pixels(0,3),pixels(135,3))
        self.assertNotEqual(pixels(0,3,0),pixels(0,3,4))


if __name__=='__main__':
    unittest.main()
