"""0.9.30: 70-card authoritative v21 stat-growth and quality acceptance."""
import unittest
from collections import Counter
from game.core.engine import Match
from game.core.models import Card
from test_engine import setup_game,force_unit

CHANGED = set("S02 S08 S03 S05 S60 S61 S64 S66 S67 S10 S69 S12 S70 S71 S72 S76 S78 S79 S17 S81 S82 S20 S85 S86 S88 S90 S91 S25 S93 S26 S94 S31 S96 S99 S101 S102 S103 S104 S35 S105 S106 S109 S33 S39 S114 S115".split())
QUALITY={"Tarcza":(1,2),"Prowokacja":(1,2),"Szybki atak":(2,1),"Podwójny atak":(2,0)}

class BalanceV21(unittest.TestCase):
    def test_all_70_cards_at_0_3_6_9_12_hand_turns(self):
        game=setup_game(93001)
        self.assertEqual(len(game.defs),70)
        self.assertEqual(len(CHANGED),46)
        self.assertEqual(sum(1 for c in game.defs.values() if
                             (c.growth_atk,c.growth_hp)==(1,1)),58)
        self.assertEqual(sum(1 for c in game.defs.values() if
                             (c.growth_atk,c.growth_hp)==(2,0)),12)
        for uid,definition in game.defs.items():
            with self.subTest(uid=uid):
                expected=(1,1) if uid in CHANGED else (definition.growth_atk,definition.growth_hp)
                self.assertEqual((definition.growth_atk,definition.growth_hp),expected)
                self.assertEqual(sum(expected),2)
                c=Card(uid,definition)
                qa,qh=QUALITY.get(definition.family,(0,0))
                for n in (0,3,6,9,12):
                    c.hand_turns=n
                    self.assertEqual(c.attack,definition.atk+expected[0]*n+qa*(n//3))
                    self.assertEqual(c.max_hp,definition.hp+expected[1]*n+qh*(n//3))
                self.assertEqual((c.definition.atk,c.definition.hp),(definition.atk,definition.hp))

    def test_real_board_freezes_growth_after_play(self):
        g=setup_game(93002)
        c=g.cards['S94'];c.hand_turns=12
        atk,hp=c.attack,c.max_hp
        u=force_unit(g,'S94',0)
        self.assertEqual((u.atk,u.max_hp),(atk,hp))
        c.hand_turns=20
        self.assertEqual((u.atk,u.max_hp),(atk,hp))
        g.assert_integrity()

    def test_no_bonus_attack_uses_or_duplicate_physical_cards(self):
        g=setup_game(93003)
        self.assertEqual(len(g.cards),70)
        for d in g.defs.values():
            self.assertEqual(d.growth_atk+d.growth_hp,2)
        self.assertFalse(any(uid.startswith('A0') for uid in g.bank))
        g.assert_integrity()

    def test_sensitive_extreme_baselines_at_12_turns(self):
        g=setup_game(93004)
        wanted={"S94":(17,28),"S86":(19,29),"S05":(19,26),
                "S66":(22,20),"S115":(21,18)}
        for uid,expected in wanted.items():
            with self.subTest(uid=uid):
                c=g.cards[uid];c.hand_turns=12
                self.assertEqual((c.attack,c.max_hp),expected)

if __name__=='__main__':
    unittest.main()
