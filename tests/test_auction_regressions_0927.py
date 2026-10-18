"""0.9.27 acceptance regressions: audit-based defects and the exact v4 card text.

Tests assert concrete outcomes, not only that a pending choice eventually closes.
"""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from game.core.engine import Match
from game.core import auction
from game.core import auction_abilities as abilities
from game.core.auction_catalog import CATALOG, V4_CARDS, v4_variant
from game.core.audit import make_report
from game.core.persistence import save_match, load_match
from game.ui.card_infographics import (
    card_cue, highlighted_numeric_ranges, AUCTION_MECHANIC_LABELS)
from game.ui.card_summary import ability_summary
from test_auction_v4_engine import ready, award, place_basic, settle
from test_auction_bags_and_zero_attack import finish_auction


class MatchAuditRegressions(unittest.TestCase):
    def test_shield_absorbs_the_entire_attack_and_explains_unchanged_hp(self):
        g=ready(92701)
        place_basic(g,'S21',0)
        place_basic(g,'S04',1)
        g.units['S04'].shield=1
        g.units['S04'].shield_source='S94'
        old_hp=g.units['S04'].hp
        g.attack('S21','S04')
        self.assertEqual(g.units['S04'].hp,old_hp)
        self.assertEqual(g.units['S04'].shield,0)
        self.assertTrue(any('Tarcza blokuje' in event['text']
                            and 'Tkacz Run' in event['text']
                            for event in g.event_journal))
        g.assert_integrity()

    def test_count_each_real_death_not_grave_size_and_ignore_replacement(self):
        g=ready(92702)
        place_basic(g,'S01',0)
        place_basic(g,'S02',1)
        g._kill_batch(['S01','S02'])
        self.assertEqual(g.death_counts,[1,1])
        # A basic card may be recycled and killed again.
        g.players[0].grave.remove('S01')
        place_basic(g,'S01',0)
        g._kill_batch(['S01'])
        self.assertEqual(g.death_counts,[2,1])
        self.assertEqual(len(g.players[0].grave),1)
        place_basic(g,'S03',0)
        g._remove_unit('S03',death=False)
        self.assertEqual(g.death_counts,[2,1])
        g.assert_integrity()

    def test_death_counts_persist_and_are_exposed_in_complete_audit(self):
        g=Match(92703,auctions_enabled=True,auction_catalog='v4',
                audit_enabled=True)
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        place_basic(g,'S01',0)
        g._kill_batch(['S01'])
        # Direct testing helper mutation bypasses the command journal, but
        # the persisted counter and finished-game summary still reflect it.
        g.players[1].hp=0
        g._check_winner()
        report=make_report(g)
        self.assertEqual(report['payload']['summary']['unit_deaths'],{'0':1,'1':0})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'save.json'
            save_match(g,path)
            loaded=load_match(path)
        self.assertEqual(loaded.death_counts,[1,0])
        self.assertTrue(loaded.death_counts_complete)

    def test_loading_legacy_save_does_not_fake_a_full_match_count(self):
        g=ready(92704)
        del g.death_counts
        del g.death_counts_complete
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old.json'
            save_match(g,path)
            restored=load_match(path)
        self.assertEqual(restored.death_counts,[0,0])
        self.assertFalse(restored.death_counts_complete)


class AuctionDescriptionContract(unittest.TestCase):
    def test_all_36_live_variants_display_exact_canonical_descriptions(self):
        for i,aid in enumerate(CATALOG):
            for tier,key in enumerate(('basic','rare','legendary')):
                with self.subTest(card=aid,tier=key):
                    g=ready(92750+i*3+tier)
                    uid=award(g,aid,tier)
                    card=g.cards[uid]
                    expected=v4_variant(aid,('podstawowa','rzadka','legendarna')[tier])
                    self.assertEqual(card.definition.effect,expected)
                    self.assertEqual(expected,V4_CARDS[aid]['variants'][key])
                    summary=ability_summary(card)
                    cue=card_cue(card)
                    self.assertIn('AKTYWNA',summary.short)
                    self.assertIn(expected,summary.full)
                    self.assertEqual(cue.base,'AKTYWNA')
                    self.assertEqual(cue.family,AUCTION_MECHANIC_LABELS[aid])
                    self.assertEqual(highlighted_numeric_ranges(card.definition),())
                    self.assertNotIn('W PRZYGOTOWANIU',cue.upgrade)
                    self.assertNotIn('NIEAKTYWNA',summary.full)

    def test_evolved_v4_card_shows_actual_rarity_and_purchase_level(self):
        g=ready(92801)
        uid=award(g,'A002',1)
        card=g.cards[uid]
        card.definition=replace(card.definition,
                                scaling='POZIOM 4 · RZADKA · NIE SKALUJE SIĘ')
        self.assertEqual(card_cue(card).ability_level,4)
        self.assertIn('RZADKA',ability_summary(card).short)
        self.assertIn('RZADKA',card_cue(card).upgrade)
        card.definition=replace(card.definition,
                                effect=v4_variant('A002','legendarna'),
                                scaling='POZIOM 4 · LEGENDARNA · NIE SKALUJE SIĘ')
        self.assertIn('LEGENDARNA',ability_summary(card).short)
        self.assertEqual(card_cue(card).next_threshold,'RZADKOŚĆ MAKSYMALNA')

    def test_historical_v3_inactive_card_stays_correctly_inactive(self):
        g=ready(92802)
        uid=award(g,'A002',0)
        card=g.cards[uid]
        card.definition=replace(card.definition,
                                effect='NIEAKTYWNA (planowana): stara aura')
        self.assertIn('NIEAKTYWNA',ability_summary(card).short)
        self.assertEqual(card_cue(card).base,'NIEAKTYWNA')


class AuctionGameplayContract(unittest.TestCase):
    def test_no_auction_is_scheduled_if_fewer_than_three_archetypes_remain(self):
        g=ready(92810)
        for completed in (3,6,9,12,15):
            g.round=completed+1
            self.assertIsNotNone(finish_auction(g))
        self.assertEqual(len(g.auction_bag),2)
        before=len(g.auction_history)
        self.assertIsNone(auction.begin(g))
        g.round=18
        g.active=1-g.first
        g.end_turn()
        self.assertIsNone(g.auction)
        self.assertEqual(g.phase,'turn')
        self.assertEqual(len(g.auction_history),before)
        g.assert_integrity()

    def test_a002_rare_and_legendary_grants_are_not_retrospective(self):
        g=ready(92811)
        place_basic(g,'S01',0)
        src=award(g,'A002',1)
        g.play(src)
        choice=next(i for i,c in enumerate(g.pending.choices)
                    if c.mode=='general_target' and c.target=='S01')
        g.choose(choice)
        self.assertTrue(abilities.boosted_attack(g,'S01'))
        self.assertTrue(g._double(g.units['S01']))
        g._kill_batch([src])
        self.assertFalse(abilities.boosted_attack(g,'S01'))
        g.assert_integrity()

        g=ready(92812)
        place_basic(g,'S01',0)
        src=award(g,'A002',2,zone='board')
        self.assertFalse(abilities.boosted_attack(g,'S01'))
        place_basic(g,'S02',0,'hand')
        g.play('S02')
        self.assertTrue(abilities.boosted_attack(g,'S02'))
        self.assertFalse(abilities.boosted_attack(g,'S01'))
        g._kill_batch([src])
        self.assertFalse(abilities.boosted_attack(g,'S02'))
        g.assert_integrity()

    def test_a008_marks_expire_after_enemy_next_turn_and_exile_is_not_death(self):
        g=ready(92813)
        place_basic(g,'S01',1)
        src=award(g,'A008',0)
        g.play(src)
        self.assertTrue(g.pending)
        idx=next(i for i,c in enumerate(g.pending.choices)
                 if c.mode=='mark' and c.target=='S01')
        g.choose(idx)
        self.assertIn('S01',g.units)
        g.players[1].turn_count+=1
        abilities.expire_exile_marks(g,1)
        self.assertIn('S01',g.exiled)
        self.assertNotIn('S01',g.players[1].grave)
        self.assertEqual(g.death_counts,[0,0])
        g.assert_integrity()

    def test_a008_legendary_exiles_up_to_three_plus_one_hand_card(self):
        g=ready(92814)
        for cid in ('S01','S02','S03'):place_basic(g,cid,1)
        old_hand=set(g.players[1].hand)
        src=award(g,'A008',2)
        g.play(src)
        for target in ('S01','S02','S03'):
            idx=next(i for i,c in enumerate(g.pending.choices)
                     if c.mode=='exile' and c.target==target)
            g.choose(idx)
        for cid in ('S01','S02','S03'):
            self.assertIn(cid,g.exiled)
        self.assertEqual(len(old_hand-set(g.players[1].hand)),1)
        self.assertEqual(g.death_counts,[0,0])
        g.assert_integrity()

    def test_a010_legendary_has_no_impossible_choice_without_any_ally(self):
        g=ready(92815)
        src=award(g,'A010',2,zone='board')
        g.end_turn()
        self.assertIsNone(g.pending)
        self.assertFalse(any(uid.startswith('SUM') for uid in g.units))
        g.assert_integrity()

    def test_a009_empty_enemy_hand_has_no_impossible_swap_choice(self):
        g=ready(92816)
        for cid in list(g.players[1].hand):
            g.players[1].hand.remove(cid)
            place_basic(g,cid,1,'grave')
        src=award(g,'A009',0)
        g.play(src)
        self.assertIsNone(g.pending)
        g.assert_integrity()

    def test_a001_legendary_chain_captures_only_after_genuine_death(self):
        g=ready(92817)
        place_basic(g,'S01',1)
        place_basic(g,'S02',1)
        src=award(g,'A001',2,zone='board')
        g._kill_batch([src]);g._drain()
        idx=next(i for i,c in enumerate(g.pending.choices)
                 if c.mode=='capture_chain' and c.target=='S01')
        g.choose(idx)
        settle(g)
        self.assertIn('S01',g.auction_death_grants)
        g._kill_batch(['S01']);g._drain()
        idx=next(i for i,c in enumerate(g.pending.choices)
                 if c.mode=='chain_capture' and c.target=='S02')
        g.choose(idx)
        settle(g)
        self.assertEqual(g.units['S02'].owner,0)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
