"""Regression tests for Game Master v17 taunt target restrictions.

Taunt constrains the target of an elected attack. It never forces a player
to attack. Inherent taunt is disabled by stun/silence, whereas a bestowed
taunt is an independent status that stays active.
"""
import unittest

from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from test_engine import force_unit, setup_game


class TauntEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.g = setup_game(317)
        self.attacker = force_unit(self.g, "S01", 0)
        self.defender = force_unit(self.g, "S33", 1)
        self.other = force_unit(self.g, "S09", 1)

    def test_inherent_taunt_blocks_hero_and_non_taunt_target(self):
        g = self.g
        self.assertEqual(g.legal_attacks("S01"), ["S33"])
        hp = g.players[1].hp
        for target in ("hero:1", "S09"):
            with self.subTest(target=target):
                before = self.attacker.attacks
                with self.assertRaises(IllegalMove):
                    g.attack("S01", target)
                self.assertEqual(self.attacker.attacks, before)
                self.assertEqual(g.players[1].hp, hp)
        self.assertEqual(g.legal_attacks("S01"), ["S33"])

    def test_multiple_taunters_allow_either_but_no_other_target(self):
        g = self.g
        g._add_effect("S09", "taunt", source="S61")
        self.assertEqual(g.legal_attacks("S01"), ["S33", "S09"])
        with self.assertRaises(IllegalMove):
            g.attack("S01", "hero:1")
        g.attack("S01", "S09")
        self.assertEqual(self.attacker.attacks, 1)
        g.assert_integrity()

    def test_bestowed_taunt_is_enforced_and_survives_stun(self):
        g = self.g
        g._add_effect("S09", "taunt", source="S61")
        g._add_effect("S33", "stun", expires=g._expiry(1), source="S59", positive=False)
        self.assertEqual(g.legal_attacks("S01"), ["S09"])
        g._add_effect("S09", "stun", expires=g._expiry(1), source="S59", positive=False)
        # Stun disables the unit's skills, but not an externally granted taunt.
        self.assertEqual(g.legal_attacks("S01"), ["S09"])

    def test_inherent_taunt_is_disabled_by_stun_or_silence(self):
        for effect in ("stun", "silence"):
            with self.subTest(effect=effect):
                g = setup_game(318)
                force_unit(g, "S01", 0)
                force_unit(g, "S33", 1)
                force_unit(g, "S09", 1)
                g._add_effect("S33", effect, source="S59", positive=False)
                self.assertEqual(g.legal_attacks("S01"),
                                 ["S33", "S09", "hero:1"])

    def test_bestowed_taunt_is_enforced_after_intrinsic_is_silenced(self):
        g = self.g
        g._add_effect("S33", "silence", source="S59", positive=False)
        g._add_effect("S09", "taunt", source="S61")
        self.assertEqual(g.legal_attacks("S01"), ["S09"])

    def test_removing_last_taunter_releases_targeting(self):
        g = self.g
        g._remove_unit("S33", death=False)
        self.assertEqual(g.legal_attacks("S01"), ["S09", "hero:1"])
        g.assert_integrity()

    def test_temporary_taunt_expires_and_releases_targeting(self):
        g = self.g
        g._add_effect("S09", "taunt", expires=g.players[1].turn_count,
                      source="S96")
        self.assertEqual(g.legal_attacks("S01"), ["S33", "S09"])
        g.active = 1
        g._finalize_end_turn()
        g.active = 0
        self.assertEqual(g.legal_attacks("S01"), ["S33"])

    def test_ai_respects_taunt(self):
        g = setup_game(319)
        force_unit(g, "S09", 1)
        force_unit(g, "S33", 0)
        force_unit(g, "S01", 0)
        g.active = 1
        g.players[1].played_this_turn = True
        self.assertEqual(g.legal_attacks("S09"), ["S33"])
        hero_hp = g.players[0].hp
        ComputerOpponent(1).step(g)
        self.assertEqual(g.units["S09"].attacks, 1)
        self.assertEqual(g.players[0].hp, hero_hp)

    def test_taunt_does_not_force_attack(self):
        g = self.g
        self.assertEqual(g.legal_attacks("S01"), ["S33"])
        g.end_turn()  # Legal to skip all attacks.
        self.assertEqual(self.attacker.attacks, 0)


if __name__ == "__main__":
    unittest.main()
