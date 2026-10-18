"""Integration checks for the actual AuctionHammer Match engine and Game Master v19."""
import os
import unittest
from test_engine import setup_game,force_unit
from game.core.models import Choice,IllegalMove
from game.ui.card_infographics import (
    card_cue,highlighted_numeric_ranges,FAMILY_SYMBOLS,UPGRADES,
)

def to_hand(g,uid,owner=0):
    for p in g.players:
        for zone in ('hand','deck','grave','board'):
            arr=getattr(p,zone)
            if uid in arr:arr.remove(uid)
    if uid in g.bank:g.bank.remove(uid)
    g.cards[uid].owner=owner;g.cards[uid].zone='hand'
    g.players[owner].hand.append(uid)

class V19EngineIntegration(unittest.TestCase):
    def test_new_stats_and_exact_catalogue(self):
        g=setup_game(910)
        self.assertEqual(len(g.defs),70)
        for uid,expected in dict(S66=(2,4),S67=(1,5),S79=(2,6),
                                 S114=(1,5),S115=(1,6)).items():
            self.assertEqual((g.defs[uid].atk,g.defs[uid].hp),expected)

    def test_s66_self_choice_mandatory_and_immediate(self):
        g=setup_game(911)
        to_hand(g,'S66')
        g.play('S66')
        self.assertIsNotNone(g.pending)
        self.assertTrue(any(c.mode=='self_quick' for c in g.pending.choices))
        with self.assertRaises(IllegalMove):
            g.end_turn()
        index=next(i for i,c in enumerate(g.pending.choices) if c.mode=='self_quick')
        g.choose(index)
        self.assertIsNone(g.pending)
        self.assertIn('hero:1',g.legal_attacks('S66'))
        g.assert_integrity()

    def test_s66_hand_grant_is_instance_specific_and_not_self(self):
        g=setup_game(912)
        to_hand(g,'S66')
        to_hand(g,'S01')
        to_hand(g,'S03')
        g.play('S66')
        idx=next(i for i,c in enumerate(g.pending.choices)
                 if c.mode=='hand_quick' and c.target=='S01')
        g.choose(idx)
        self.assertNotIn('hero:1',g.legal_attacks('S66'))
        self.assertTrue(g.cards['S01'].quick_on_first_summon)
        self.assertFalse(g.cards['S03'].quick_on_first_summon)
        g.end_turn();g.end_turn()
        g.play('S01')
        self.assertIn('hero:1',g.legal_attacks('S01'))
        self.assertFalse(g.cards['S01'].quick_on_first_summon)
        g.assert_integrity()

    def test_s67_selects_self_or_ally_without_summoning_sickness_bypass(self):
        for recipient in ('S67','S01'):
            with self.subTest(recipient=recipient):
                g=setup_game(913)
                to_hand(g,'S67')
                force_unit(g,'S01',0)
                g.play('S67')
                self.assertIsNotNone(g.pending)
                self.assertEqual({c.target for c in g.pending.choices},
                                 {'S67','S01'})
                idx=next(i for i,c in enumerate(g.pending.choices)
                         if c.target==recipient)
                g.choose(idx)
                self.assertTrue(g._double(g.units[recipient]))
                self.assertFalse(g._double(g.units['S01' if recipient=='S67' else 'S67']))
                self.assertEqual(g.legal_attacks('S67'),[])

    def test_hyena_waits_and_never_gets_three_attacks(self):
        g=setup_game(914)
        u=force_unit(g,'S79',0)
        self.assertEqual((u.atk,u.hp),(2,6))
        u.played_turn=g.players[0].turn_count
        self.assertEqual(g.legal_attacks('S79'),[])
        u.played_turn=0
        self.assertFalse(g._double(u))
        g.attack('S79','hero:1')
        self.assertTrue(g._double(u))
        g.attack('S79','hero:1')
        self.assertEqual(u.attacks,2)
        self.assertEqual(g.legal_attacks('S79'),[])

    def test_human_traits_are_self_only(self):
        g=setup_game(915)
        to_hand(g,'S114')
        g.play('S114')
        self.assertIn('hero:1',g.legal_attacks('S114'))
        self.assertEqual(g.units['S114'].hp,5)
        g2=setup_game(916)
        to_hand(g2,'S115')
        g2.play('S115')
        self.assertEqual(g2.units['S115'].hp,6)
        self.assertTrue(g2._double(g2.units['S115']))
        self.assertEqual(g2.legal_attacks('S115'),[])

    def test_s90_death_grants_two_distinct_hand_cards(self):
        g=setup_game(917)
        force_unit(g,'S90',0)
        before=set(g.players[0].hand)
        g._kill_batch(['S90']);g._drain()
        boosted={x for x in g.players[0].hand if g.cards[x].quick_on_first_summon}
        self.assertEqual(len(boosted),min(2,len(before)))
        self.assertTrue(boosted<=before)
        self.assertFalse(g.players[0].next_fast)

    def test_s91_fallback_last_ally_to_hand_first_eligible_turn(self):
        g=setup_game(918)
        force_unit(g,'S91',0)
        g._kill_batch(['S91']);g._drain()
        boosted=[x for x in g.players[0].hand if g.cards[x].double_on_first_eligible]
        self.assertEqual(len(boosted),1)
        uid=boosted[0]
        g.play(uid)
        # The randomly chosen hand card may itself have a mandatory on-play
        # effect; finish that choice before proceeding to turn boundaries.
        while g.pending is not None:
            g.choose(0)
        self.assertFalse(g.cards[uid].double_on_first_eligible)
        self.assertEqual(g.legal_attacks(uid),[])
        for _ in range(2):
            g.end_turn()
            while g.pending is not None:
                g.choose(0)
        self.assertTrue(g._double(g.units[uid]))
        self.assertIn('hero:1',g.legal_attacks(uid))
        g.end_turn()
        while g.pending is not None:
            g.choose(0)
        self.assertFalse(g.units[uid].fallback_double_pending)

    def test_s20_and_s82_death_protection_has_hero_fallback(self):
        for uid,armor,shield in (('S20',2,1),('S82',6,0)):
            with self.subTest(card=uid):
                g=setup_game(920)
                force_unit(g,uid,0)
                g._kill_batch([uid]);g._drain()
                self.assertEqual(g.players[0].hero_armor,armor)
                self.assertEqual(g.players[0].hero_shield,shield)

    def test_s105_armor_does_not_refill_after_damage(self):
        g=setup_game(921)
        src=force_unit(g,'S105',0)
        victim=force_unit(g,'S01',0)
        g._update_auras()
        self.assertEqual(victim.aura_armor.get('S105'),2)
        g._damage('S01',2)
        self.assertEqual(victim.aura_armor.get('S105'),0)
        g._update_auras()
        self.assertEqual(victim.aura_armor.get('S105'),0)

    def test_s109_regenerates_every_own_end_turn_with_quality(self):
        g=setup_game(922)
        g.cards['S109'].hand_turns=6
        u=force_unit(g,'S109',0)
        u.hp-=20
        initial=u.hp
        g.end_turn()
        self.assertEqual(u.hp-initial,4)

class V19InfographicTests(unittest.TestCase):
    def test_all_70_cards_have_trigger_family_and_upgrade(self):
        g=setup_game(931)
        for c in g.cards.values():
            with self.subTest(card=c.uid):
                cue=card_cue(c)
                self.assertTrue(cue.trigger)
                self.assertTrue(cue.family)
                self.assertTrue(cue.base)
                self.assertIn('/3T',cue.upgrade)
        self.assertEqual(len(FAMILY_SYMBOLS),14)

    def test_damage_quantity_bold_not_duration(self):
        g=setup_game(932)
        s=g.defs['S59']
        spans=highlighted_numeric_ranges(s)
        self.assertEqual([s.effect[a:b] for a,b in spans],['1'])
        self.assertGreater(spans[0][0],s.effect.index('1 jej własną'))
        s2=g.defs['S01']
        self.assertEqual([s2.effect[a:b] for a,b in highlighted_numeric_ranges(s2)],['3'])

    def test_stat_only_upgrades_do_not_fake_additional_attacks(self):
        g=setup_game(933)
        for uid in ('S66','S67','S79','S114','S115'):
            self.assertEqual(highlighted_numeric_ranges(g.defs[uid]),())
        self.assertIn('+2 ATK',card_cue(g.cards['S115']).upgrade)
        self.assertIn('+1 HP',card_cue(g.cards['S114']).upgrade)

    def test_v19_s109_bonus_is_per_turn(self):
        g=setup_game(934)
        g.cards['S109'].hand_turns=9
        cue=card_cue(g.cards['S109'])
        self.assertIn('PER TURN',cue.upgrade)
        self.assertEqual(cue.effect_value,5)


os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
try:
    import pygame
except ImportError:
    pygame=None

@unittest.skipIf(pygame is None,'pygame-ce unavailable')
class V19CardRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init();pygame.font.init()
        pygame.display.set_mode((1480,920))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_render_all_70_cards_small_and_large(self):
        from game.ui.card_view import CardView
        g=setup_game(935)
        view=CardView()
        screen=pygame.Surface((800,600))
        for card in g.cards.values():
            with self.subTest(card=card.uid):
                view.draw(screen,card,pygame.Rect(10,10,125,169))
                view.draw(screen,card,pygame.Rect(170,10,255,338))


if __name__=='__main__':unittest.main()
