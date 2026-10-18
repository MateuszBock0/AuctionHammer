"""Regresja opisów v19 i rozdzielenia możliwości ataku od jego licznika."""
import json
import unittest
from pathlib import Path
from game.core.engine import Match
from game.ui.card_summary import SPECS, ability_summary
from game.ui.attack_view import attack_display


class AbilitySummaryV19Tests(unittest.TestCase):
    def setUp(self):
        self.game = Match(912)

    def test_exact_70_matching_ids_and_usable_polish_summaries(self):
        data = json.loads((Path(__file__).resolve().parents[1] /
                            'data/cards_base_70.json').read_text(encoding='utf-8'))
        self.assertEqual(set(SPECS), {row['id'] for row in data})
        self.assertEqual(len(SPECS), 70)
        for card in self.game.cards.values():
            with self.subTest(card=card.definition.id):
                summary = ability_summary(card)
                self.assertTrue(summary.short and summary.full)
                self.assertNotIn('[I]', summary.short)
                self.assertNotIn('SZCZEGÓŁY', summary.short)
                self.assertTrue(len(summary.full) > len(summary.short) // 2)
                self.assertNotIn('{', summary.full)

    def test_alternative_targets_and_v19_exceptions(self):
        checks = {
            'S02': ('bohatera', 'sojusznika'),
            'S20': ('bohatera', 'sojusznika'),
            'S66': ('ręce', 'siebie'),
            'S67': ('siebie', 'sojusznika'),
            'S79': ('pierwszym', 'drug'),
            'S82': ('bohatera', 'sojusznika'),
            'S90': ('losowym', 'w ręce'),
            'S91': ('sojusznik', 'w ręce'),
            'S105': ('jednorazowo', 'odnawia'),
            'S109': ('KAŻDEJ', 'własnej'),
            'S114': ('siebie', 'Szybki'),
            'S115': ('siebie', 'Podwójny'),
        }
        for cid, phrases in checks.items():
            with self.subTest(card=cid):
                text = ability_summary(self.game.cards[cid]).full.lower()
                for phrase in phrases:
                    self.assertIn(phrase.lower(), text)

    def test_scaling_values_do_not_rewrite_durations_or_attack_limit(self):
        examples = [
            ('S01', 3, ['6 obrażeń']),
            ('S02', 3, ['5 PŻ']),
            ('S58', 3, ['przez 2 tury', 'łącznie 5']),
            ('S109', 3, ['3 PŻ', 'KAŻDEJ']),
            ('S115', 6, ['maks. dwa']),
        ]
        for cid, turns, expected in examples:
            card = self.game.cards[cid]
            card.hand_turns = turns
            with self.subTest(card=cid, turns=turns):
                text = ability_summary(card).full
                for fragment in expected:
                    self.assertIn(fragment.lower(), text.lower())


class AttacksDisplayedTests(unittest.TestCase):
    def test_non_active_turn_never_erases_remaining_attacks(self):
        from test_engine import setup_game, force_unit
        game=setup_game(913)
        if game.phase=='mulligan':
            game.finish_mulligan(0,[])
            game.finish_mulligan(1,[])
        game.active=0
        game.players[0].turn_count=max(1, game.players[0].turn_count)
        unit=force_unit(game,'S115',0)
        unit.played_turn=0
        unit.attacks=1
        one=attack_display(game,'S115')
        self.assertEqual((one.remaining,one.limit),(1,2))
        game.active=1
        two=attack_display(game,'S115')
        self.assertEqual((two.remaining,two.limit),(1,2))
        self.assertFalse(two.ready)
        self.assertIn('CZEKA',two.reason)

    def test_conditional_second_attack_only_after_first(self):
        from test_engine import setup_game, force_unit
        game=setup_game(914)
        if game.phase=='mulligan':
            game.finish_mulligan(0,[])
            game.finish_mulligan(1,[])
        game.active=0
        game.players[0].turn_count=max(1,game.players[0].turn_count)
        unit=force_unit(game,'S79',0)
        unit.played_turn=0
        unit.attacks=0
        before=attack_display(game,'S79')
        self.assertEqual(before.limit,1)
        self.assertTrue(before.next_attack_bonus)
        unit.attacks=1
        after=attack_display(game,'S79')
        self.assertEqual(after.limit,2)
        self.assertEqual(after.remaining,1)
        self.assertFalse(after.next_attack_bonus)


if __name__ == '__main__':
    unittest.main()
