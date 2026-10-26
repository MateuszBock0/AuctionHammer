"""Bounded hard combat: legal, deterministic, capped and fast (0.9.94)."""
from __future__ import annotations

from time import perf_counter
import unittest

from game.core.ai import ComputerOpponent
from game.core.hard_tactics import DEPTH,WIDTH,forced_hero_finish,shield_break_setup
from game.core.models import Effect
from test_balance_buff_v24_0990 import ready,starter


class BoundedHard0994(unittest.TestCase):
    def test_hard_limit_constants(self):
        self.assertEqual(DEPTH,3)
        self.assertEqual(WIDTH,5)

    def test_hero_shield_cleared_by_low_attack_and_then_lethal(self):
        g=ready(99401)
        weak=starter(g,'S01')
        strong=starter(g,'S02')
        g.units[weak].base_attack=1
        g.units[strong].base_attack=10
        g.players[1].hp=7
        g.players[1].hero_shield=1
        action=forced_hero_finish(g,0)
        self.assertEqual(action,(weak,'hero:1'))
        ai=ComputerOpponent(0,'trudny')
        self.assertEqual(ai.hard_attack_choice(g),action)
        n=len(g.audit_actions)
        ai.step(g)
        self.assertEqual(len(g.audit_actions),n+1)
        self.assertFalse(g.players[1].hero_shield)
        self.assertEqual(g.players[1].hp,7)

    def test_double_attack_same_unit_counts_as_two_separate_hits(self):
        g=ready(99402)
        uid=starter(g,'S01')
        unit=g.units[uid]
        unit.base_attack=9
        unit.effects.append(Effect('double',expires=None,source=uid))
        g.players[1].hp=6
        g.players[1].hero_shield=1
        self.assertEqual(forced_hero_finish(g,0),(uid,'hero:1'))
        # A single ordinary hit would only remove the shield.
        unit.effects.clear()
        self.assertIsNone(forced_hero_finish(g,0))

    def test_armor_applies_to_each_hit_until_consumed(self):
        g=ready(99403)
        small=starter(g,'S01')
        big=starter(g,'S02')
        g.units[small].base_attack=1
        g.units[big].base_attack=6
        g.players[1].hp=5
        g.players[1].hero_armor=4
        self.assertIsNone(forced_hero_finish(g,0))
        g.units[big].base_attack=8
        # Two cumulative hits (and consumption of armor) are required.
        self.assertIsNotNone(forced_hero_finish(g,0))

    def test_taunt_prevents_illegal_face_combo(self):
        g=ready(99404)
        starter(g,'S01')
        guard=starter(g,'S12',1)
        from game.core.models import Effect
        g.units[guard].effects.append(Effect('taunt',source=guard))
        self.assertIsNone(forced_hero_finish(g,0))

    def test_staged_shield_breaks_only_with_two_legal_safe_attacks(self):
        g=ready(99405)
        weak=starter(g,'S01')
        big=starter(g,'S02')
        victim=starter(g,'S12',1)
        g.units[weak].base_attack=1
        g.units[big].base_attack=12
        g.units[weak].hp=10
        g.units[big].hp=10
        g.units[victim].hp=7
        g.units[victim].base_attack=2
        g.units[victim].shield=1
        self.assertEqual(shield_break_setup(g,0),(weak,victim))

    def test_no_rng_draw_and_no_audit_mutation_from_scoring(self):
        g=ready(99406)
        for cid in ('S01','S02','S03','S04'):
            starter(g,cid)
        for cid in ('S12','S09'):
            starter(g,cid,1)
        bot=ComputerOpponent(0,'trudny')
        before_rng=g.rng.getstate()
        before_actions=len(g.audit_actions)
        before_events=len(g.event_journal)
        first=bot.hard_attack_choice(g)
        for _ in range(25):
            self.assertEqual(first,bot.hard_attack_choice(g))
        self.assertEqual(g.rng.getstate(),before_rng)
        self.assertEqual(len(g.audit_actions),before_actions)
        self.assertEqual(len(g.event_journal),before_events)
        g.assert_integrity()

    def test_normal_and_easy_unchanged(self):
        g=ready(99407)
        starter(g,'S01')
        self.assertIsNone(ComputerOpponent(0,'normalny').hard_attack_choice(g))
        self.assertIsNone(ComputerOpponent(0,'łatwy').hard_attack_choice(g))

    def test_p95_bounded_planning_stays_sub_100ms_on_ci_cpu(self):
        g=ready(99408)
        for cid in ('S01','S02','S03','S04','S05'):
            starter(g,cid)
        for cid in ('S09','S12','S22','S23','S24'):
            starter(g,cid,1)
        bot=ComputerOpponent(0,'trudny')
        elapsed=[]
        for _ in range(250):
            start=perf_counter()
            bot.hard_attack_choice(g)
            elapsed.append((perf_counter()-start)*1000)
        elapsed.sort()
        self.assertLess(elapsed[round(0.95*(len(elapsed)-1))],100.,
                        'The bounded planner must not stall the turn')


if __name__=='__main__':
    unittest.main()
