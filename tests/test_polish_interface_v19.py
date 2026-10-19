"""Sprawdzenie polskiego interfejsu i zgodności bieżącego katalogu v19."""
import json
import re
import unittest
from pathlib import Path

from game import config
from game.ui.card_infographics import card_cue, FAMILY_SYMBOLS, UPGRADES
from test_engine import setup_game
from test_v19_integration import to_hand

ROOT=Path(__file__).resolve().parents[1]
ANGIELSKIE_ETKI=re.compile(
    r'\b(?:QUICK|DOUBLE|DMG|HEAL|ARMOR|SHIELD|POISON|STUN|TAUNT|CLEANSE|'
    r'IMMUNE|LEVEL|LOCKED|GROWTH|TICK|TOTAL|PER TURN|NEXT|FIRST|CURRENT)\b',
    re.IGNORECASE,
)


class PolskiInterfejsTests(unittest.TestCase):
    def test_all_70_cards_display_polish_cues_at_scaling_thresholds(self):
        g=setup_game(990)
        self.assertEqual(len(g.cards),70)
        for card in g.cards.values():
            for hand_turns in (0,2,3,6,9):
                with self.subTest(card=card.uid,hand_turns=hand_turns):
                    card.hand_turns=hand_turns
                    cue=card_cue(card)
                    for field in (cue.trigger,cue.family,cue.base,cue.upgrade,
                                  cue.growth,cue.next_threshold):
                        self.assertIsNone(ANGIELSKIE_ETKI.search(field),(card.uid,field))
                    self.assertIn('3T',cue.upgrade)
                    self.assertEqual(cue.ability_level,hand_turns//3)

    def test_every_family_has_a_polish_name_and_upgrade(self):
        self.assertEqual(len(FAMILY_SYMBOLS),14)
        self.assertEqual(len(UPGRADES),14)
        self.assertEqual(set(FAMILY_SYMBOLS),set(UPGRADES))
        for family in FAMILY_SYMBOLS:
            self.assertIsNone(ANGIELSKIE_ETKI.search(FAMILY_SYMBOLS[family]),family)
            self.assertIsNone(ANGIELSKIE_ETKI.search(UPGRADES[family]),family)
        self.assertEqual(FAMILY_SYMBOLS['Szybki atak'],'SZYBKI')
        self.assertEqual(FAMILY_SYMBOLS['Podwójny atak'],'2 ATAKI')
        self.assertIn('ŁĄCZ',UPGRADES['Trucizna'])

    def test_s66_and_s67_visible_choices_hide_engine_identifiers(self):
        for uid,term in (('S66','Szybki atak'),('S67','Podwójny atak')):
            with self.subTest(card=uid):
                g=setup_game(991)
                to_hand(g,uid)
                if uid=='S66':to_hand(g,'S01')
                g.play(uid)
                self.assertIsNotNone(g.pending)
                labels=[c.label for c in g.pending.choices]
                self.assertTrue(any(term in x for x in labels))
                for label in labels:
                    self.assertNotIn('hand_quick',label)
                    self.assertNotIn('board_double',label)
                    self.assertIsNone(ANGIELSKIE_ETKI.search(label),label)

    def test_structured_rules_and_real_cards_agree(self):
        master=json.loads((ROOT/'data/GAME_MASTER.json').read_text(encoding='utf-8'))
        raw=json.loads((ROOT/'data/cards_base_70.json').read_text(encoding='utf-8'))
        cards=raw if isinstance(raw,list) else raw['cards']
        self.assertEqual(master['rules']['version'],'19.0')
        historical={card['id']:card for card in master['starter_cards']}
        current={card['id']:card for card in cards}
        exceptions={'S05','S61','S70','S72','S20','S86',
                    'S94','S96','S106','S33'}
        self.assertEqual(set(historical),set(current))
        for cid in historical:
            old=dict(historical[cid]);new=dict(current[cid])
            if cid in exceptions:
                self.assertIn('+1 ATK i +2 MAX HP',new['scaling'])
                new['scaling']=old['scaling']
            self.assertEqual(new,old,cid)
        self.assertEqual(len(cards),70)
        self.assertEqual({c['id'] for c in cards},{c['id'] for c in master['starter_cards']})
        self.assertEqual((next(c for c in cards if c['id']=='S79')['atk'],
                          next(c for c in cards if c['id']=='S79')['hp']),(2,6))

    def test_window_title_is_polish(self):
        self.assertIn('Gra z komputerem',config.WINDOW_TITLE)
        self.assertNotIn('Solo vs Computer',config.WINDOW_TITLE)


if __name__=='__main__':
    unittest.main()
