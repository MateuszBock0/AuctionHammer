"""Regresje wymagające odrębnej migawki każdej grupy zgodnie z GM v19 §7."""
import unittest

from test_engine import setup_game,force_unit


def wybor(g,target):
    assert g.pending is not None
    index=next(i for i,c in enumerate(g.pending.choices) if c.target==target)
    g.choose(index)


class MigawkiKolejnychFal(unittest.TestCase):
    def test_nastepna_grupa_widzi_cele_dopiero_po_zamknieciu_poprzedniej(self):
        g=setup_game(981)
        g.active=1
        force_unit(g,'S84',1)
        force_unit(g,'S83',1)
        pierwsza=force_unit(g,'S01',0)
        force_unit(g,'S02',0)
        pierwsza.hp=1
        g._kill_batch(['S84'])
        g._kill_batch(['S83'])  # kolejna grupa już wykryta, jeszcze bez migawki
        self.assertIsNone(g.death_waves[1]['sources'])
        g._drain()
        self.assertEqual(g.pending.uid,'S84')
        wybor(g,'S01')
        self.assertNotIn('S01',g.units)
        self.assertEqual(g.pending.uid,'S83')
        self.assertEqual([c.target for c in g.pending.choices],['S02'])
        wybor(g,'S02')
        self.assertFalse(g.death_waves)
        g.assert_integrity()

    def test_odpornosc_w_tejsamej_fali_nie_anuluje_legalnego_ogluszenia(self):
        g=setup_game(982)
        g.active=1
        force_unit(g,'S88',1)
        force_unit(g,'S84',0)
        cel=force_unit(g,'S01',1)
        g._kill_batch(['S88','S84'])
        g._drain()
        self.assertEqual(g.pending.uid,'S88')
        wybor(g,'S01')
        self.assertEqual(g.pending.uid,'S84')
        wybor(g,'S01')
        rodzaje=[e.kind for e in cel.effects]
        self.assertIn('immune_stun',rodzaje)
        self.assertIn('stun',rodzaje)
        g.assert_integrity()

    def test_oczyszczenie_dotyczy_starego_statusu_nie_nowego(self):
        g=setup_game(983)
        g.active=1
        force_unit(g,'S87',1)
        force_unit(g,'S84',0)
        cel=force_unit(g,'S01',1)
        g._add_effect('S01','stun',expires=3,source='S59',positive=False)
        g._kill_batch(['S87','S84'])
        g._drain()
        wybor(g,'S01')
        wybor(g,'S01')
        self.assertEqual(sum(e.kind=='stun' for e in cel.effects),1)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
