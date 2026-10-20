"""121-card presentation coverage matrix regression; no game mutation."""
import unittest
from scripts.card_copy_matrix_0949 import COLUMNS,validate


class CardCopyMatrix0949(unittest.TestCase):
    def test_every_basic_and_auction_variant_has_evaluated_display_copy(self):
        rows=validate()
        self.assertEqual(len(rows),121)
        self.assertEqual(sum(x['tier']=='base' for x in rows),70)
        self.assertEqual(sum(x['tier']!='base' for x in rows),51)
        self.assertEqual({x['tier'] for x in rows},
                         {'base','podstawowa','rzadka','legendarna'})
        for row in rows:
            with self.subTest(card=row['id'],tier=row['tier']):
                self.assertEqual(set(row),set(COLUMNS))
                self.assertNotIn('{',row['short_description'])
                self.assertNotIn('{',row['full_description'])
        for card_id in ('S15','S59','S84','S108','S95'):
            line=next(x for x in rows if x['id']==card_id)
            self.assertIn('→',line['visual_cue'])

    def test_v23_conditional_notes_are_not_empty(self):
        rows=validate()
        for cid in ('S32','S95','S86','S87','S88'):
            desc=next(x['full_description'] for x in rows if x['id']==cid)
            self.assertGreater(len(desc),100)


if __name__=='__main__':
    unittest.main()
