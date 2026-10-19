"""Independent cross-effect/UI clarity regressions for the v23 second-pass audit."""
import unittest
from game.core.auction_catalog import v23_variant,live_variant
from game.ui.v23_help import v23_base_card_note
from game.core.models import Effect,Choice
from game.core import auction_abilities
from test_auction_v22_0931 import ready,award
from test_auction_v4_engine import place_basic


class V23Descriptions(unittest.TestCase):
    def test_all_five_conditional_base_cards_have_visible_explanations(self):
        words={'S86':'+3 pancerza','S87':'4 PŻ','S88':'Tarcza',
               'S32':'2 zwykłe obrażenia','S95':'2 zwykłe obrażenia'}
        for cid,fragment in words.items():
            with self.subTest(card=cid):
                self.assertIn(fragment,v23_base_card_note(cid,'v23'))
                self.assertEqual(v23_base_card_note(cid,'v22'),'')

    def test_v23_exceptions_are_shown_first_not_truncated_after_four_lines(self):
        for aid,rarity,word in (('A014','rzadka','nominalne'),
                                ('A015','legendarna','przeciwnika'),
                                ('A018','legendarna','brak następnej aukcji')):
            with self.subTest(aid=aid):
                text=v23_variant('v22',aid,rarity,'v23')
                self.assertTrue(text.startswith('[v23:'))
                self.assertIn(word,text[:120])
                self.assertEqual(v23_variant('v22',aid,rarity,'v22'),
                                 live_variant('v22',aid,rarity))


class V23HealingAndWard(unittest.TestCase):
    def test_rare_A014_converts_nominal_heal_on_fully_healed_shielded_hero(self):
        g=ready(237210)
        award(g,'A014',1,owner=1,zone='board')
        g.players[0].hp=100
        g.players[0].hero_shield=1
        g._heal('hero:0',5)
        self.assertEqual(g.players[0].hp,100)
        self.assertEqual(g.players[0].hero_shield,0)
        self.assertEqual(g.players[1].hp,100)
        g.assert_integrity()

    def test_legendary_A014_full_hp_heal_5_deals_exactly_5_damage(self):
        g=ready(237211)
        award(g,'A014',2,owner=1,zone='board')
        g.players[0].hp=100
        g._heal('hero:0',5)
        self.assertEqual(g.players[0].hp,95)
        self.assertEqual(g.players[1].hp,100)
        g.assert_integrity()

    def test_death_S87_fallback_inherits_A014_conversion(self):
        g=ready(237212)
        award(g,'A014',2,owner=1,zone='board')
        victim=place_basic(g,'S87',0)
        g.players[0].hp=100
        g._damage(victim,100,ignore_defense=True)
        g._drain()
        self.assertEqual(g.players[0].hp,96)
        g.assert_integrity()

    def test_friendly_S86_death_survives_A015_but_enemy_S87_is_blocked(self):
        g=ready(237213)
        ward=award(g,'A015',2,owner=0,zone='board')
        s86=place_basic(g,'S86',0)
        s87=place_basic(g,'S87',1)
        g.players[1].hp=68
        g.units[s86].hp=0
        g.units[s87].hp=0
        g._kill_batch([s86,s87])
        self.assertEqual(len(g.death_waves),1)
        self.assertEqual(g.death_waves[0]['source_ids'],(s86,))
        g._drain()
        self.assertIsNotNone(g.pending)
        self.assertTrue(any(ch.target==ward for ch in g.pending.choices))
        g.choose(0)
        self.assertEqual(g.players[1].hp,68)
        g.assert_integrity()

    def test_silenced_A015_no_longer_blocks_enemy_death(self):
        g=ready(237214)
        ward=award(g,'A015',1,owner=0,zone='board')
        g.units[ward].effects.append(Effect('silence',positive=False))
        monster=place_basic(g,'S87',1)
        g.players[1].hp=70
        g._damage(monster,100,ignore_defense=True)
        g._drain()
        self.assertEqual(g.players[1].hp,74)
        g.assert_integrity()


    def test_both_legendary_A015_block_opposite_death_triggers_in_one_snapshot(self):
        from game.core.models import Card,Unit
        g=ready(237215)
        first=award(g,'A015',2,owner=0,zone='board')
        # A copied A015 is the legal way to have the same archetype
        # on both tables without illegally buying two original copies.
        g.serial+=1
        second=f'COPY{g.serial:07d}'
        ref=g.cards[first]
        g.cards[second]=Card(second,ref.definition,owner=1,zone='board')
        g.defs[second]=ref.definition
        g.ephemeral_ids.add(second)
        g.auction_awards[second]=dict(g.auction_awards[first],ephemeral=True)
        g.players[1].board.append(second)
        original=g.units[first]
        g.units[second]=Unit(second,1,original.atk,original.max_hp,
                             original.hp,original.ability_level,0)
        left=place_basic(g,'S86',0)
        right=place_basic(g,'S87',1)
        left_hp=g.players[0].hp
        right_hp=g.players[1].hp
        for cid in (first,second,left,right):
            g.units[cid].hp=0
        # The Wieszczki are dying in the SAME cohort, so their auras
        # must still block opposing sources for that cohort.
        g._kill_batch([first,second,left,right])
        self.assertFalse(g.death_waves)
        g._drain()
        self.assertEqual(g.players[0].hero_armor,0)
        self.assertEqual(g.players[0].hp,left_hp)
        self.assertEqual(g.players[1].hp,right_hp)
        self.assertEqual(g.death_counts,[2,2])
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
