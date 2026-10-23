"""v0.9.67 UI: combat ATK colors, max HP semantics and armor indicator."""
import unittest
from types import SimpleNamespace
import pygame
from game.ui.card_view import (
    GENERAL_DAMAGE_STATUS, STAT_UP_COLOR, STAT_DOWN_COLOR,
    ARMOR_SILVER, standard_hit_damage, stat_tint, armor_medallion_rect,
)

class CombatStatVisuals0967(unittest.TestCase):
    def test_live_general_is_shown_as_buffed_combat_atk(self):
        general=SimpleNamespace(name=GENERAL_DAMAGE_STATUS)
        atk,active=standard_hit_damage(9,[general])
        self.assertEqual((atk,active),(18,True))
        self.assertEqual(stat_tint(atk,9,(255,215,132)),STAT_UP_COLOR)
        self.assertEqual(stat_tint(9,9,(255,215,132)),(255,215,132))
        self.assertEqual(standard_hit_damage(9,[]),(9,False))

    def test_buff_and_debuff_tints_are_signed(self):
        neutral=(255,215,132)
        self.assertEqual(stat_tint(12,9,neutral),STAT_UP_COLOR)
        self.assertEqual(stat_tint(6,9,neutral),STAT_DOWN_COLOR)
        self.assertEqual(stat_tint(9,9,neutral),neutral)

    def test_maxhp_colours_only_when_max_changes(self):
        neutral=(223,196,198)
        self.assertEqual(stat_tint(15,12,neutral),STAT_UP_COLOR)
        self.assertEqual(stat_tint(10,12,neutral),STAT_DOWN_COLOR)
        self.assertEqual(stat_tint(12,12,neutral),neutral)
        # Wounds reduce current HP but do not indicate MAX HP weakening.
        current_hp,max_hp,base_maxhp=4,12,12
        self.assertLess(current_hp,max_hp)
        self.assertEqual(stat_tint(max_hp,base_maxhp,neutral),neutral)

    def test_armor_badge_position_for_three_card_sizes(self):
        for width,height,large in ((57,37,False),(65,41,False),(113,52,True)):
            hp=pygame.Rect(25,120,width,height)
            badge=armor_medallion_rect(hp,large)
            self.assertTrue(badge.colliderect(hp))
            self.assertEqual(badge.width,badge.height)
            self.assertLessEqual(badge.right,hp.right+10)
            self.assertGreaterEqual(badge.top,hp.top-2)
            self.assertEqual(ARMOR_SILVER,(215,230,239))

if __name__=="__main__":
    unittest.main()
