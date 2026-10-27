"""Non-graphical tests for choosing signed native trailer moments."""
import unittest
from tools.native_trailer import default_highlights


class NativeTrailerSelectionTests(unittest.TestCase):
    def test_finisher_and_damage_beats_are_selected_in_chronological_order(self):
        events = [
            {'seq': 1, 'text': 'Bestia atakuje: jednostka.'},
            {'seq': 2, 'text': 'Jednostka otrzymuje 20 obrażeń w PŻ (20 → 0/20).'},
            {'seq': 3, 'text': 'Zgon Jednostka.'},
            {'seq': 4, 'text': 'Bohater otrzymuje 3 obrażeń w PŻ (5 → 2/100).'},
            {'seq': 5, 'text': 'Bohater otrzymuje 2 obrażeń w PŻ (2 → 0/100).'},
            {'seq': 6, 'text': 'KONIEC MECZU! Zwycięzca: GRACZ.'},
        ]
        def attack(seq, start, end):
            return {'seq': seq, 'operation': 'attack', 'result': 'ok',
                    'event_seq_start': start, 'event_seq_end': end}
        data = {'event_journal': events,
                'actions': [attack(10, 1, 3), attack(11, 4, 6)]}
        self.assertEqual(default_highlights(data, 1), [11])
        self.assertEqual(default_highlights(data, 2), [10, 11])

    def test_invalid_or_uncommitted_attacks_do_not_make_highlights(self):
        data = {'event_journal': [{'seq': 1, 'text': 'Wystawiono kartę'}],
                'actions': [{'seq': 7, 'operation': 'attack', 'result': 'error',
                             'event_seq_start': 1, 'event_seq_end': 1}]}
        self.assertEqual(default_highlights(data), [])


if __name__ == '__main__':
    unittest.main()
