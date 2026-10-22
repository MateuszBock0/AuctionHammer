"""Regression tests: General damage multiplier visibility is read-only and source-linked."""
import copy
import unittest

from game.core.audit import digest
from game.core.auction_abilities import boosted_attack
from game.core.combat_analysis import build_combat_analysis
from game.core.combat_html import render_combat_html
from game.core.status_view import active_statuses
from test_auction_v4_engine import ready, place_basic, award
from test_engine import setup_game, force_unit


def general_statuses(game, uid):
    return [status for status in active_statuses(game, uid)
            if status.name == 'Premia Generała Oddziału Natarcia']


class GeneralEffectVisibilityTests(unittest.TestCase):
    def test_rare_general_shows_double_attacks_and_double_damage_on_recipient(self):
        game = ready(95901)
        recipient = place_basic(game, 'S35', owner=0)
        general = award(game, 'A002', tier=1, zone='board')
        game.auction_general_targets[general] = recipient

        self.assertTrue(boosted_attack(game, recipient))
        statuses = general_statuses(game, recipient)
        self.assertEqual(len(statuses), 1)
        self.assertIn('2 ataki', statuses[0].detail)
        self.assertIn('×2', statuses[0].detail)
        self.assertIn('Generał Oddziału Natarcia', statuses[0].source)
        self.assertEqual(game.units[recipient].atk, game.cards[recipient].attack)

        game._add_effect(general, 'stun', source='S59', positive=False,
                         expires=game.players[0].turn_count + 1)
        self.assertFalse(boosted_attack(game, recipient))
        self.assertEqual(general_statuses(game, recipient), [])
        game._clean(general, negative=True)
        self.assertTrue(boosted_attack(game, recipient))
        game._remove_unit(general, death=False)
        self.assertEqual(general_statuses(game, recipient), [])

    def test_legendary_general_new_ally_grant_is_visible_then_removed(self):
        game = ready(95902)
        general = award(game, 'A002', tier=2, zone='board')
        recipient = place_basic(game, 'S01', owner=0)
        game.auction_general_grants.setdefault(general, set()).add(recipient)

        self.assertTrue(boosted_attack(game, recipient))
        self.assertEqual(len(general_statuses(game, recipient)), 1)
        self.assertTrue(game._double(game.units[recipient]))
        game._remove_unit(general, death=False)
        self.assertFalse(boosted_attack(game, recipient))
        self.assertEqual(general_statuses(game, recipient), [])

    def test_non_adjacent_unit_not_attributed_as_neighbor_aura(self):
        game = setup_game(95903)
        game.fixed_board_slots = True
        force_unit(game, 'S01', 0, slot=0)
        force_unit(game, 'S34', 0, slot=1)
        force_unit(game, 'S02', 0, slot=4)
        game._update_auras()

        self.assertEqual(game.units['S01'].aura_atk, 1)
        self.assertEqual(game.units['S02'].aura_atk, 0)
        statuses = [s for s in active_statuses(game, 'S01') if s.name == 'Aura ATK']
        self.assertEqual(len(statuses), 1)
        self.assertIn('Chorąży Królewskiej Kompanii', statuses[0].source)

    def test_forensic_book_reports_recorded_general_bonus_without_changing_audit(self):
        initial = {
            'players': {'0': {'hp': 100}, '1': {'hp': 100}},
            'units': {
                'G': {'owner': 0, 'hp': 8, 'current_attack': 2,
                      'current_max_hp': 8, 'effects': [], 'attacks': 0},
                'U': {'owner': 0, 'hp': 9, 'current_attack': 5,
                      'current_max_hp': 9, 'effects': [], 'attacks': 0},
                'V': {'owner': 1, 'hp': 9, 'current_attack': 2,
                      'current_max_hp': 9, 'effects': [], 'attacks': 0},
            },
            'cards': {}, 'pending': None, 'deferred_attack': None,
            'auction_catalog': 'v22',
            'auction_awards': {
                'G': {'archetype': 'A002', 'rarity': 'rzadka'}
            },
            'auction_v4': {
                'general_targets': {'G': 'U'}, 'general_grants': {}
            }
        }
        disconnected = copy.deepcopy(initial['auction_v4'])
        disconnected['general_targets'] = {}
        payload = {
            'seed': 95904, 'initial_state': initial,
            'actions': [{
                'seq': 1, 'operation': 'attack', 'args': ['U', 'V'],
                'result': 'ok', 'actor_before': 0, 'round_before': 4,
                'changes': {'auction_v4': {
                    'before': initial['auction_v4'], 'after': disconnected}}
            }, {
                'seq': 2, 'operation': 'attack', 'args': ['U', 'V'],
                'result': 'ok', 'actor_before': 0, 'round_before': 5,
                'changes': {}
            }],
            'internal_events': [], 'event_journal': []
        }
        before_digest = digest(payload)
        battles = build_combat_analysis(payload, {'G': 'Generał Oddziału Natarcia'})
        self.assertEqual(digest(payload), before_digest)
        self.assertIn('×2', battles[0]['attacker']['before']['combat_bonuses'][0])
        self.assertEqual(battles[0]['attacker']['after']['combat_bonuses'], [])
        self.assertEqual(battles[1]['attacker']['before']['combat_bonuses'], [])
        html = render_combat_html(payload)
        self.assertIn('Statusy i premie:', html)
        self.assertIn('Generał Oddziału Natarcia (G)', html)
        self.assertIn('obrażenia standardowego ataku ×2', html)

    def test_forensic_book_does_not_claim_stunned_general_grants_bonus(self):
        game = ready(95905)
        recipient = place_basic(game, 'S35', owner=0)
        general = award(game, 'A002', tier=1, zone='board')
        game.auction_general_targets[general] = recipient
        game._add_effect(general, 'stun', source='S59', positive=False,
                         expires=game.players[0].turn_count + 1)
        from game.core.audit import state_snapshot
        state = state_snapshot(game)
        state['players'] = {str(p): row for p, row in enumerate(state['players'])} if isinstance(state['players'], list) else state['players']
        payload = {'initial_state': state,
                   'actions': [{'seq': 1, 'operation': 'attack', 'args': [recipient, 'hero:1'],
                                'result': 'ok', 'actor_before': 0, 'round_before': 5,
                                'changes': {}}],
                   'internal_events': [], 'event_journal': []}
        battles = build_combat_analysis(payload)
        self.assertEqual(battles[0]['attacker']['before']['combat_bonuses'], [])


if __name__ == '__main__':
    unittest.main()
