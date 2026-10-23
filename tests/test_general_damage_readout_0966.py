"""v0.9.66: General doubles normal-hit damage, not displayed base ATK."""
import unittest
from types import SimpleNamespace
from game.ui.card_view import GENERAL_DAMAGE_STATUS, standard_hit_damage

class GeneralDamageReadout0966(unittest.TestCase):
    def test_general_bonus_shows_actual_predefense_damage(self):
        general=SimpleNamespace(name=GENERAL_DAMAGE_STATUS,category='double')
        self.assertEqual(standard_hit_damage(9,[general]),(18,True))
        self.assertEqual(standard_hit_damage(12,[general]),(24,True))

    def test_unrelated_double_attack_does_not_double_damage(self):
        double=SimpleNamespace(name='Podwójny atak (wrodzony)',category='double')
        self.assertEqual(standard_hit_damage(9,[double]),(9,False))
        self.assertEqual(standard_hit_damage(9,[]),(9,False))

    def test_general_bonus_is_not_multiplicative_per_source(self):
        general=SimpleNamespace(name=GENERAL_DAMAGE_STATUS,category='double')
        self.assertEqual(standard_hit_damage(9,[general,general]),(18,True))

    def test_preview_does_not_mutate_statuses_or_stats(self):
        general=SimpleNamespace(name=GENERAL_DAMAGE_STATUS,category='double')
        statuses=[general]
        atk=9
        for _ in range(3):
            self.assertEqual(standard_hit_damage(atk,statuses),(18,True))
        self.assertEqual(atk,9)
        self.assertEqual(statuses,[general])

if __name__=='__main__':
    unittest.main()
