"""Regression for crash KeyError 'SUM0000007' in AuctionHammer 0.9.28.

A010 Queen creates synthetic ephemeral SUM cards outside the 70-card catalogue.
They must render in all sizes, on the live board (during/after a pending
summon), in details, and after save/reload. All rarities are exercised.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.ui.app import SoloApp
from game.ui.card_infographics import card_cue
from game.ui.card_summary import ability_summary, SPECS
from game.core.persistence import save_match, load_match
from test_auction_v4_engine import ready, award, place_basic, settle


class QueenSummonRenderingRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            cls.app=SoloApp()
        cls.surface=pygame.Surface((600,600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _summon(self,tier,seed):
        g=ready(seed)
        if tier==2:
            ally=place_basic(g,'S01',0)
            g.units[ally].base_attack=6
            g.units[ally].base_max_hp=8
            g.units[ally].hp=8
        queen=award(g,'A010',tier,zone='board')
        g.end_turn()
        self.assertIsNotNone(g.pending)
        self.assertIn('summon',{c.mode for c in g.pending.choices})
        self.app.game=g
        # Reproduce original screenshot: pending A010 choice, board rendering.
        self.app._draw_board()
        choice=next(i for i,c in enumerate(g.pending.choices)
                    if c.mode=='summon')
        g.choose(choice)
        settle(g)
        summoned=[uid for uid in g.players[0].board if uid.startswith('SUM')]
        self.assertEqual(len(summoned),(1,2,2)[tier])
        g.assert_integrity()
        return g,summoned

    def test_queen_spawn_all_tiers_render_board_and_card_details(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g,ids=self._summon(tier,92911+tier)
                self.app.game=g
                # This exact call used to crash after _spawn.
                self.app._draw_board()
                self.app.draw()
                for uid in ids:
                    card=g.cards[uid]; unit=g.units[uid]
                    self.assertNotIn(card.definition.id,SPECS)
                    self.assertTrue(uid.startswith('SUM'))
                    summary=ability_summary(card,unit)
                    cue=card_cue(card,unit)
                    self.assertTrue(summary.full)
                    self.assertEqual(cue.upgrade,'JEDNOSTKA EFEMERYCZNA')
                    self.assertIn('NIE WRACA DO TALII',cue.next_threshold)
                    self.assertNotIn('TARCZA',summary.short)
                    if tier==1:
                        self.assertEqual(card.definition.family,'Prowokacja')
                        self.assertIn('PROWOKACJA',summary.short)
                    else:
                        self.assertEqual(card.definition.family,'Bez zdolności')
                        self.assertEqual(summary.short,'BEZ ZDOLNOŚCI')
                    for size in ((125,195),(148,220),(255,380)):
                        rect=pygame.Rect(8,8,*size)
                        self.app.cards_view.draw(self.surface,card,rect,unit)
                        layout=self.app.cards_view.summary_layout(card,rect,unit)
                        self.assertGreater(len(layout['lines']),0)
                    self.app.details_card=uid
                    self.app.draw()
                    self.app.details_card=None

    def test_summoned_unit_survives_save_load_and_can_render(self):
        g,ids=self._summon(0,92920)
        uid=ids[0]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'queen_summon.json'
            save_match(g,path)
            loaded=load_match(path)
        loaded.assert_integrity()
        self.assertIn(uid,loaded.units)
        self.app.game=loaded
        self.app._draw_board()
        self.app.draw()
        self.app.cards_view.draw(self.surface,loaded.cards[uid],
                                 pygame.Rect(8,8,148,220),loaded.units[uid])

    def test_summoned_unit_exile_never_triggers_basic_draw(self):
        g,ids=self._summon(0,92921)
        uid=ids[0]
        g._kill_batch([uid])
        g._drain()
        self.assertNotIn(uid,g.units)
        self.assertIn(uid,g.vanished)
        self.assertNotIn(uid,g.players[0].grave)
        self.assertNotIn(uid,g.players[0].deck)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
