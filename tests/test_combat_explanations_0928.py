"""Player-readable battle explanations: numerical effects must match state deltas.

Covers shields, temporary/permanent armor, hero defenses, healing,
non-damaging attacks, timed status application and continuously changing auras.
"""
import unittest

from test_auction_v4_engine import ready, award, place_basic, settle
from game.ui.app import SoloApp


def log(game):
    return [event['text'] for event in game.event_journal]


class CombatOutcomeExplanationTests(unittest.TestCase):

    def test_unit_shield_reports_full_absorption_and_source(self):
        g=ready(928201)
        place_basic(g,'S01',0)
        place_basic(g,'S02',1)
        g.units['S02'].shield=1
        g.units['S02'].shield_source='S01'
        hp=g.units['S02'].hp
        self.assertEqual(g._damage('S02',5),0)
        self.assertEqual(g.units['S02'].hp,hp)
        self.assertEqual(g.units['S02'].shield,0)
        self.assertTrue(any('Tarcza blokuje 5 obrażeń' in s and
                            'S02' not in s for s in log(g)))

    def test_armor_consumption_and_actual_hp_loss_are_separated(self):
        g=ready(928202)
        place_basic(g,'S01',1)
        u=g.units['S01']
        u.armor_temp=2
        u.armor_perm=3
        before=u.hp
        self.assertEqual(g._damage('S01',8),3)
        self.assertEqual(u.hp,before-3)
        self.assertEqual(u.armor,0)
        self.assertTrue(any('pancerz pochłania 5 z 8 obrażeń' in s for s in log(g)))
        self.assertTrue(any('otrzymuje 3 obrażeń w PŻ' in s for s in log(g)))

    def test_full_armor_blocks_damage_and_hero_shield_blocks_a_hit(self):
        g=ready(928203)
        place_basic(g,'S01',1)
        u=g.units['S01']
        u.armor_temp=20
        before=u.hp
        self.assertEqual(g._damage('S01',7),0)
        self.assertEqual(u.hp,before)
        self.assertTrue(any('otrzymuje 0 obrażeń w PŻ' in s for s in log(g)))
        p=g.players[1]
        p.hero_shield=1
        self.assertEqual(g._damage('hero:1',100),0)
        self.assertEqual(p.hp,100)
        self.assertEqual(p.hero_shield,0)
        self.assertTrue(any('Tarcza bohatera blokuje 100 obrażeń' in s for s in log(g)))

    def test_hero_armor_and_hp_damage_both_visible(self):
        g=ready(928204)
        p=g.players[1]
        p.hero_armor=6
        self.assertEqual(g._damage('hero:1',10),4)
        self.assertEqual((p.hp,p.hero_armor),(96,0))
        self.assertTrue(any('pancerz bohatera pochłania 6 z 10' in s for s in log(g)))
        self.assertTrue(any('otrzymuje 4 obrażeń w PŻ' in s for s in log(g)))

    def test_healing_shows_actual_capped_amount(self):
        g=ready(928205)
        place_basic(g,'S01',0)
        u=g.units['S01']
        u.hp=u.max_hp-2
        g._heal('S01',100)
        self.assertEqual(u.hp,u.max_hp)
        self.assertTrue(any('odzyskuje 2 PŻ' in s for s in log(g)))
        p=g.players[0];p.hp=98
        g._heal('hero:0',100)
        self.assertEqual(p.hp,100)
        self.assertTrue(any('odzyskuje 2 PŻ' in s for s in log(g)))

    def test_zero_attack_has_clear_zero_damage_reason(self):
        g=ready(928206)
        place_basic(g,'S01',1)
        hp=g.units['S01'].hp
        self.assertEqual(g._damage('S01',0),0)
        self.assertEqual(g.units['S01'].hp,hp)
        self.assertTrue(any('0 obrażeń; PŻ bez zmian' in s for s in log(g)))

    def test_silence_and_aura_change_have_named_status_and_number(self):
        g=ready(928207)
        place_basic(g,'S01',1)
        u=g.units['S01']
        g._add_effect('S01','silence',expires=g._expiry(1),source='S02',positive=False)
        self.assertTrue(any('Wyciszenie' in s for s in log(g)))
        src=award(g,'A002',0,zone='board')
        g._update_auras()
        self.assertTrue(any('zmiana aury ATK +1' in s for s in log(g)))
        g._kill_batch([src])
        self.assertTrue(any('zmiana aury ATK -1' in s for s in log(g)))
        g.assert_integrity()

    def test_feedback_colors_distinguish_defenses_from_damage(self):
        shield=SoloApp._feedback_color('Tkacz Run: Tarcza blokuje 10 obrażeń')
        damage=SoloApp._feedback_color('Tkacz Run otrzymuje 10 obrażeń w PŻ')
        armor=SoloApp._feedback_color('Pancerz pochłania 4 obrażeń')
        self.assertNotEqual(shield,damage)
        self.assertEqual(shield,armor)

    def test_legacy_v3_retains_previous_event_journal_contract(self):
        from game.core.engine import Match
        g=Match(928208,auctions_enabled=True,auction_catalog='v3')
        # Match's v3 audit/replay payload was generated before v4 combat
        # explanations. This remains essential for older saved matches.
        g._damage('hero:1',5)
        self.assertFalse(any('otrzymuje 5 obrażeń w PŻ' in s for s in log(g)))


if __name__=='__main__':
    unittest.main()
