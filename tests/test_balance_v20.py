"""Game Master v20 regression checks for anti-dead effects and boosted one-shot damage."""
import unittest
from game.core.models import Choice
from game.core.effects import options
from test_engine import setup_game, force_unit

class BalanceV20(unittest.TestCase):
    def test_catalogue_keeps_70_unique_cards_and_previous_stats(self):
        g=setup_game(2201)
        self.assertEqual(len(g.defs),70)
        for uid,power in dict(S01=5,S09=2,S21=6,S27=2,S59=3,S84=4,S103=2).items():
            self.assertIn(str(power),g.defs[uid].effect,uid)
        self.assertEqual((g.defs['S12'].atk,g.defs['S12'].hp),(4,5))

    def test_s12_no_armor_but_damage(self):
        g=setup_game(2202);force_unit(g,'S12',0);t=force_unit(g,'S33',1)
        old=t.hp
        g._execute('S12','attack',Choice('auto','S33',''),attacked='S33')
        self.assertEqual(t.hp,old-2)

    def test_s12_hero_armor_precedence(self):
        g=setup_game(2203);force_unit(g,'S12',0)
        g.players[1].hero_armor=3
        g._execute('S12','attack',Choice('auto','hero:1',''),attacked='hero:1')
        self.assertEqual(g.players[1].hero_armor,1)
        self.assertEqual(g.players[1].hp,100)

    def test_s74_fallback_damages_unbuffed_target(self):
        g=setup_game(2204);force_unit(g,'S74',0);t=force_unit(g,'S33',1)
        old=t.hp
        g._execute('S74','attack',Choice('auto','S33',''),attacked='S33')
        self.assertEqual(t.hp,old-2)

    def test_s27_targets_hero_without_enemy_units(self):
        g=setup_game(2205);force_unit(g,'S27',0)
        g._execute('S27','end',Choice('auto',None,''))
        self.assertEqual(g.players[1].hp,98)

    def test_s78_grants_hand_quick_when_no_fresh_ally(self):
        g=setup_game(2206);force_unit(g,'S78',0)
        opts=options(g,'S78','attack','hero:1')
        self.assertTrue(opts)
        self.assertTrue(all(o.target in g.players[0].hand for o in opts))
        g._execute('S78','attack',opts[0],'hero:1')
        self.assertTrue(g.cards[opts[0].target].quick_on_first_summon)

    def test_s85_hero_fallback(self):
        g=setup_game(2207);force_unit(g,'S85',0);g.players[0].hp=50
        self.assertEqual(options(g,'S85','death')[0].target,'hero:0')
        g._execute('S85','death',Choice('auto','hero:0',''))
        self.assertEqual(g.players[0].hp,54)

    def test_s97_heals_even_without_debuff(self):
        g=setup_game(2208);force_unit(g,'S97',0);t=force_unit(g,'S33',0)
        t.hp-=2
        g._execute('S97','end',Choice('Cel sojuszniczy','S33',''))
        self.assertEqual(t.hp,t.max_hp-1)

if __name__=='__main__':
    unittest.main()
