"""Regresje kolejki zdarzeń — wspólne migawki, atomowe zgony i kaskady v19.

Testy używają prawdziwego silnika Match, 70 fizycznych kart oraz tych
samych komend, z których korzystają interfejs i przeciwnik komputerowy.
"""
import unittest
from unittest.mock import patch

from game.core.models import Choice, IllegalMove
from test_engine import setup_game, force_unit


class WspolneFaleZgonow(unittest.TestCase):
    def test_dokument_kolejki_v19_jest_aktualnym_zrodlem(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        order=json.loads((root/'data/event_order_v19.json').read_text(encoding='utf-8'))
        master=json.loads((root/'data/GAME_MASTER.json').read_text(encoding='utf-8'))
        self.assertEqual(order['version'],'19.0')
        self.assertTrue(order['simultaneous_death_batch'])
        self.assertTrue(order['hero_death_end_of_closed_wave'])
        self.assertIn('simultaneous_death_triggers_from_single_snapshot',
                      order['authoritative_priority'])
        self.assertEqual(master['canonical_event_order_file'],'data/event_order_v19.json')
        self.assertEqual(master['rules']['version'],'19.0')

    def test_kolejnosc_migawki_aktywny_gracz_od_lewej(self):
        g=setup_game(700)
        force_unit(g,'S82',1)
        force_unit(g,'S84',0)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g._kill_batch(['S82','S17','S21','S84'])
        # W każdej fali obowiązuje porządek przed usunięciem jednostek:
        # bieżący gracz od lewej, potem rywal od lewej.
        self.assertEqual(g.death_waves[0]['fallen'],('S84','S21','S82','S17'))
        self.assertEqual(g.death_waves[0]['source_ids'],
                         ('S84','S21','S82','S17'))
        self.assertIsNone(g.death_waves[0]['sources'])
        self.assertEqual(g.players[0].grave.count('S84'),1)
        self.assertEqual(g.players[1].grave.count('S82'),1)
        g.assert_integrity()

    def test_migawka_wyborow_podczas_wspolnej_fali(self):
        g=setup_game(701)
        force_unit(g,'S84',0)  # Ogłusza i zadaje 2 obrażenia
        force_unit(g,'S82',1)  # Przyznaje 6 pancerza własnej jednostce
        target=force_unit(g,'S01',1)
        target.hp=2
        g._kill_batch(['S84','S82'])
        # Jeszcze przed wykonaniem S84 obie listy legalnych celów są ustalone.
        wave=g.death_waves[0]
        self.assertIsNone(wave['sources'])
        self.assertEqual(target.armor,0)
        g._drain()
        self.assertEqual(len(wave['sources']),2)
        self.assertIn('S01',[c.target for c in wave['sources'][0][1]])
        self.assertIn('S01',[c.target for c in wave['sources'][1][1]])
        self.assertEqual(g.pending.uid,'S84')
        idx=next(i for i,c in enumerate(g.pending.choices) if c.target=='S01')
        g.choose(idx)
        self.assertIsNotNone(g.pending)
        self.assertEqual(g.pending.uid,'S82')
        # Pierwszy wybór tylko rejestruje decyzję, nie zmienia HP/statusów.
        self.assertEqual(target.hp,2)
        self.assertEqual(target.armor,0)
        idx=next(i for i,c in enumerate(g.pending.choices) if c.target=='S01')
        g.choose(idx)
        self.assertIsNone(g.pending)
        self.assertIn('S01',g.units)
        self.assertEqual(g.units['S01'].hp,2)
        self.assertEqual(g.units['S01'].armor,4)
        self.assertTrue(any(e.kind=='stun' for e in g.units['S01'].effects))
        g.assert_integrity()

    def test_skutki_zgonow_obu_stron_jedna_fala_nie_konczy_przedwczesnie(self):
        g=setup_game(702)
        force_unit(g,'S21',0) # 4 obrażeń wrogiemu bohaterowi
        force_unit(g,'S17',1) # 6 leczenia własnego bohatera
        g.players[1].hp=3
        g._kill_batch(['S21','S17'])
        g._drain()
        # Obrażenia i leczenie z jednej fali rozpatrywane łącznie.
        self.assertEqual(g.players[1].hp,5)
        self.assertEqual(g.phase,'turn')
        self.assertIsNone(g.winner)
        self.assertEqual(sum('Zamknięto falę śmierci' in x for x in g.events),1)
        g.assert_integrity()

    def test_monety_za_prog_75_liczone_od_koncowego_hp_fali(self):
        g=setup_game(714)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g.players[1].hp=76
        g._kill_batch(['S21','S17'])
        g._drain()
        self.assertEqual(g.players[1].hp,78)
        # 76 -> 72 -> 78 to jedna fala, a nie dwa osobne zdarzenia.
        self.assertNotIn(75,g.players[1].thresholds)
        self.assertFalse(any('75 PŻ' in x for x in g.events))
        g.assert_integrity()

    def test_monety_za_prog_po_fali_z_rzeczywistym_spadkiem(self):
        g=setup_game(715)
        force_unit(g,'S21',0)
        g.players[1].hp=77
        old_coins=g.players[1].coins
        g._kill_batch(['S21'])
        g._drain()
        self.assertEqual(g.players[1].hp,73)
        self.assertEqual(g.players[1].coins,old_coins+3)  # +1 za zgon S21, +2 za próg 75
        self.assertIn(75,g.players[1].thresholds)
        g.assert_integrity()

    def test_kaskadowy_zgon_tworzony_w_nastepnej_fali(self):
        g=setup_game(703)
        force_unit(g,'S81',0)  # Po śmierci zmniejsza MAX PŻ wroga o 5
        force_unit(g,'S17',1)
        source=force_unit(g,'S21',1)
        source.base_max_hp=4  # Spadek maksymalnego PŻ do zera zabija S21.
        source.hp=4
        initial_coins=g.players[0].coins
        g._kill_batch(['S81','S17'])
        g._drain()
        self.assertEqual(g.pending.uid,'S81')
        index=next(i for i,c in enumerate(g.pending.choices)
                   if c.target=='S21' and c.mode=='Osłab')
        g.choose(index)
        self.assertNotIn('S21',g.units)
        self.assertEqual(g.players[1].grave.count('S21'),1)
        self.assertEqual(g.players[0].coins,initial_coins+2)
        closings=[x for x in g.events if x.startswith('Zamknięto falę śmierci')]
        self.assertEqual(len(closings),2)
        self.assertIn('falę śmierci 1',closings[0])
        self.assertIn('falę śmierci 2',closings[1])
        g.assert_integrity()

    def test_ogluszona_zmarla_jednostka_nie_dodaje_zdolnosci(self):
        g=setup_game(704)
        a=force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g._add_effect('S21','stun',expires=g._expiry(0),source='S59',positive=False)
        old=g.players[1].hp
        g._kill_batch(['S21','S17'])
        self.assertEqual(g.death_waves[0]['source_ids'],('S17',))
        g._drain()
        self.assertEqual(g.players[1].hp,old)
        self.assertEqual(g.players[1].grave.count('S17'),1)
        g.assert_integrity()

    def test_grupa_dwustronnej_walki_przed_efektami_smierci(self):
        g=setup_game(705)
        a=force_unit(g,'S21',0)
        b=force_unit(g,'S17',1)
        a.base_attack=4;b.base_attack=4
        a.hp=3;b.hp=3
        g.attack('S21','S17')
        self.assertNotIn('S21',g.units)
        self.assertNotIn('S17',g.units)
        self.assertEqual(g.players[1].hp,100)  # -4 obrażenia i +6 leczenia, do maksimum 100
        self.assertEqual(g.players[0].hp,100)
        self.assertEqual(len([x for x in g.events if x.startswith('Zamknięto falę śmierci')]),1)
        g.assert_integrity()

    def test_powtarzalnosc_przy_jednym_ziarnie_losowym(self):
        def trace(seed):
            g=setup_game(seed)
            force_unit(g,'S90',0)
            force_unit(g,'S91',0)
            g._kill_batch(['S91','S90'])
            g._drain()
            return [x for x in g.players[0].hand
                    if g.cards[x].quick_on_first_summon or g.cards[x].double_on_first_eligible]
        self.assertEqual(trace(706),trace(706))

    def test_trucizna_i_oczyszczanie_jednej_fali_nie_usuwaja_nowych_efektow(self):
        g=setup_game(709)
        force_unit(g,'S83',0)  # Trucizna 2 na 3 aktywacje
        force_unit(g,'S87',1)  # Oczyszczenie sojusznika przy śmierci
        victim=force_unit(g,'S01',1)
        g._kill_batch(['S83','S87'])
        g._drain()
        self.assertEqual(g.pending.uid,'S83')
        g.choose(next(i for i,c in enumerate(g.pending.choices) if c.target=='S01'))
        self.assertEqual(g.pending.uid,'S87')
        # Oba wybory są zamrożone; nie ma jeszcze zatrucia.
        self.assertFalse(any(e.kind=='poison' for e in victim.effects))
        g.choose(next(i for i,c in enumerate(g.pending.choices) if c.target=='S01'))
        # Oczyszczanie widziało początek fali, nie usuwa więc trucizny
        # powstałej jednocześnie (efekty te nie działają sekwencyjnie).
        self.assertTrue(any(e.kind=='poison' for e in victim.effects))
        g.assert_integrity()

    def test_oczyszczanie_usunie_stary_status_a_nowy_z_jednej_fali_zostanie(self):
        g=setup_game(710)
        force_unit(g,'S83',0)
        force_unit(g,'S87',1)
        victim=force_unit(g,'S01',1)
        g._add_effect('S01','poison',1,2,source='S58',positive=False)
        g._kill_batch(['S83','S87'])
        g._drain()
        g.choose(next(i for i,c in enumerate(g.pending.choices) if c.target=='S01'))
        g.choose(next(i for i,c in enumerate(g.pending.choices) if c.target=='S01'))
        poisons=[e for e in victim.effects if e.kind=='poison']
        self.assertEqual([e.source for e in poisons],['S83'])
        g.assert_integrity()

    def test_ochrona_bohatera_i_obrazenia_tej_samej_fali(self):
        g=setup_game(711)
        force_unit(g,'S20',0)
        force_unit(g,'S21',1)
        before=g.players[0].hp
        g._kill_batch(['S20','S21'])
        g._drain()
        self.assertEqual(g.players[0].hp,before)
        self.assertEqual(g.players[0].hero_shield,0)
        self.assertEqual(g.players[0].hero_armor,2)
        self.assertEqual(g.players[1].grave.count('S21'),1)
        g.assert_integrity()

    def test_zwyciezca_po_zamknieciu_wspolnej_fali(self):
        g=setup_game(707)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g.players[0].hp=3;g.players[1].hp=3
        old_execute=g._execute
        def execution(uid,ctx,choice,attacked=None):
            if ctx=='death':
                g._damage(f'hero:{1-g.cards[uid].owner}',5)
            else:
                old_execute(uid,ctx,choice,attacked)
        with patch.object(g,'_execute',side_effect=execution):
            g._kill_batch(['S21','S17'])
            g._drain()
        self.assertEqual(g.players[0].hp,-2)
        self.assertEqual(g.players[1].hp,-2)
        self.assertEqual(g.phase,'finished')
        self.assertIsNotNone(g.winner)
        self.assertEqual(sum('KONIEC MECZU!' in x for x in g.events),1)

    def test_losowanie_s90_niezalezne_od_kolejnosci_kart_na_rece(self):
        def wyniki(odwroc):
            g=setup_game(712)
            force_unit(g,'S90',0)
            if odwroc:
                g.players[0].hand.reverse()
            g._kill_batch(['S90'])
            g._drain()
            chosen=sorted(x for x in g.players[0].hand
                          if g.cards[x].quick_on_first_summon)
            self.assertTrue(any(x.startswith('Losowanie S90 #1:') for x in g.events))
            self.assertEqual(g.rng_draw_index,1)
            return chosen
        self.assertEqual(wyniki(False),wyniki(True))

    def test_leczenie_wspolnej_fali_moze_uratowac_bohatera(self):
        g=setup_game(713)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g.players[1].hp=1
        g._kill_batch(['S21','S17'])
        g._drain()
        # Leczenie S17 ratuje bohatera w tej samej fali.
        self.assertEqual(g.phase,'turn')
        self.assertEqual(g.players[1].hp,3)
        self.assertIsNone(g.winner)

    def test_wiele_pelnych_meczy_bez_blokady_kolejki_i_duplikatow(self):
        # Stress test silnika na realnych decyzjach obu przeciwników AI.
        from game.core.ai import ComputerOpponent
        from game.core.engine import Match
        for seed in range(740,752):
            with self.subTest(ziarno=seed):
                g=Match(seed)
                g.finish_mulligan(1,[])
                g.finish_mulligan(0,[])
                opponents=[ComputerOpponent(0),ComputerOpponent(1)]
                for step in range(450):
                    if g.phase=='finished':
                        break
                    if g.pending is not None:
                        opponents[g.pending.owner].choose(g)
                    else:
                        opponents[g.active].step(g)
                    if step%25==0:
                        g.assert_integrity()
                    self.assertLessEqual(len(g.death_waves),70)
                g.assert_integrity()
                self.assertIn(g.phase,('turn','finished'))

    def test_zamkniecie_fali_wstrzymuje_nowe_deklaracje(self):
        g=setup_game(708)
        force_unit(g,'S84',0)
        force_unit(g,'S82',1)
        force_unit(g,'S01',1)
        g._kill_batch(['S84','S82'])
        g._drain()
        self.assertIsNotNone(g.pending)
        with self.assertRaises(IllegalMove):
            g.end_turn()
        with self.assertRaises(IllegalMove):
            g.attack('S01','hero:0')
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
