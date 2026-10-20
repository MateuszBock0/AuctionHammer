"""Verified 25-card presentation contract for 0.9.48: old rules untouched."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from game.core.auction_catalog import live_variant,v23_variant
from game.ui.card_summary import ability_summary
from game.ui.card_infographics import card_cue
from game.ui.auction_copy import (identify_auction_variant,display_auction_copy,
                                  preview_auction_copy,full_preview_auction_copy)
from game.ui.v23_help import v23_base_card_note,v23_base_card_short_note

ROOT=Path(__file__).resolve().parents[1]
BASIC={x['id']:x for x in json.loads((ROOT/'data/cards_base_70.json').read_text(encoding='utf8'))}

def base_card(card_id,level=0):
    return SimpleNamespace(definition=SimpleNamespace(**BASIC[card_id]),ability_level=level)

def auc(archetype,rarity,ruleset='v23',mode='v22'):
    names={'podstawowa':'PODSTAWOWA','rzadka':'RZADKA','legendarna':'LEGENDARNA'}
    effect=(v23_variant(mode,archetype,rarity,'v23') if ruleset=='v23'
            else live_variant(mode,archetype,rarity))
    return SimpleNamespace(
        definition=SimpleNamespace(id=archetype,name=archetype,
            family={'A014':'Leczenie','A015':'Oczyszczanie','A018':'Pancerz'}.get(archetype,'Pancerz'),
            trigger='Pasywna' if archetype!='A018' else 'Przy wystawieniu',
            effect=effect,scaling=f'POZIOM 1 · {names[rarity]} · NIE SKALUJE SIĘ'),
        ability_level=0)

class CardCopyContract0948(unittest.TestCase):
    VARIANTS=(('A014','podstawowa'),('A014','rzadka'),
              ('A014','legendarna'),('A015','podstawowa'),
              ('A015','rzadka'),('A015','legendarna'),
              ('A018','legendarna'))

    def test_70_baseline_descriptions_have_no_raw_placeholders(self):
        self.assertEqual(len(BASIC),70)
        for card_id in BASIC:
            for level in (0,1,3):
                with self.subTest(card=card_id,level=level):
                    item=ability_summary(base_card(card_id,level))
                    self.assertTrue(item.short and item.full)
                    self.assertNotIn('{',item.full)
                    self.assertNotIn('}',item.full)

    def test_13_corrected_cards_contain_key_ability_branches(self):
        required={
            'S05':['+1 ATK','+2 MAX'],
            'S07':['jeśli usunięto efekt','obrażeń'],
            'S12':['pancerza','zamiast'],
            'S15':['1 bazowe','Tylko'],
            'S27':['bohaterowi'],
            'S59':['3 obrażenia','ogłuszenie'],
            'S74':['dodatkowych obrażeń','nic nie usunięto'],
            'S78':['kartę w ręce'],
            'S84':['4 obrażenia','ogłuszenie'],
            'S85':['bohatera','regenerację'],
            'S97':['w przeciwnym razie'],
            'S99':['1 tymczasowego pancerza','trwałego pancerza'],
            'S108':['po raz pierwszy','1 bazowe'],
        }
        for cid,fragments in required.items():
            for level in (0,1,3):
                full=ability_summary(base_card(cid,level)).full
                for value in fragments:
                    with self.subTest(id=cid,level=level,phrase=value):
                        self.assertIn(value,full)

    def test_conditional_v23_notes_never_leak_to_v22(self):
        for cid in ('S86','S87','S88','S32','S95'):
            self.assertTrue(v23_base_card_note(cid,'v23'))
            self.assertTrue(v23_base_card_short_note(cid,'v23'))
            self.assertFalse(v23_base_card_note(cid,'v22'))
            self.assertFalse(v23_base_card_short_note(cid,'v4'))

    def test_7_current_variants_recognize_actual_v23_and_human_copy(self):
        for aid,rarity in self.VARIANTS:
            with self.subTest(id=aid,tier=rarity):
                card=auc(aid,rarity)
                canonical=card.definition.effect
                hit=identify_auction_variant(card.definition)
                self.assertIsNotNone(hit)
                self.assertEqual(hit[0],rarity)
                self.assertIn('AKTYWNA',ability_summary(card).short)
                self.assertEqual(card_cue(card).base,'AKTYWNA')
                human=display_auction_copy(card.definition)
                self.assertNotIn('[v23:',human)
                self.assertNotEqual(human,canonical)
                preview=preview_auction_copy(aid,rarity,'v23',canonical)
                self.assertNotIn('[v23:',preview)
                self.assertTrue(full_preview_auction_copy(aid,rarity,'v23',canonical))
                self.assertEqual(card.definition.effect,canonical)

    def test_legacy_and_inert_are_not_misidentified(self):
        for aid,rarity in self.VARIANTS:
            old=auc(aid,rarity,ruleset='v22')
            self.assertEqual(display_auction_copy(old.definition),old.definition.effect)
            self.assertEqual(preview_auction_copy(aid,rarity,'v22',old.definition.effect),
                             old.definition.effect)
        bad=auc('A014','rzadka')
        bad.definition.effect='Arbitrary invalid effect'
        self.assertIsNone(identify_auction_variant(bad.definition))
        self.assertNotIn('AKTYWNA',ability_summary(bad).short)
        bad.definition.effect='NIEAKTYWNA — stara wersja'
        self.assertIsNone(identify_auction_variant(bad.definition))
        self.assertIn('NIEAKTYWNA',ability_summary(bad).short)

    def test_v4_legacy_A010_recognized_without_v23_replacement(self):
        for rarity in ('podstawowa','rzadka','legendarna'):
            card=auc('A010',rarity,'v22','v4')
            hit=identify_auction_variant(card.definition)
            self.assertIsNotNone(hit)
            self.assertEqual(hit[1],'v4')
            self.assertEqual(display_auction_copy(card.definition),card.definition.effect)

if __name__=='__main__':
    unittest.main()
