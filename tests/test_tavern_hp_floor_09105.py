"""0.9.105: per-unit brawl HP floor, signed preservation, UI, AI and HTML audit."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import pygame

from game.core.engine import Match
from game.core.audit import state_snapshot,verify_replay
from game.core.persistence import save_match,load_match
from game.core.combat_html import render_combat_html
from game.core.beer_strategy import _projected_board_loss
from game.ui.decision_preview import brawl_at_risk,next_brawl_damage
from game.ui.tavern_help import brawl_help_lines
from game.ui.app import SoloApp
from test_balance_buff_v24_0990 import ready,starter


class BrawlHpFloor09105(unittest.TestCase):
    @staticmethod
    def scene(seed):
        game=ready(seed)
        game.tavern_scaled_damage_enabled=True
        game.tavern_min_hp_damage_enabled=True
        game.players[0].coins=200
        a=starter(game,'S01',0)
        b=starter(game,'S12',1)
        game.units[a].base_max_hp=21
        game.units[a].hp=21
        game.units[b].base_max_hp=101
        game.units[b].hp=101
        return game,a,b

    def test_floor_ceil_per_unit_and_decreasing_base(self):
        game,a,b=self.scene(910501)
        game.order_beer(0)
        for turns,health_a,health_b in ((2,18,90),(1,15,79),(0,12,68)):
            game.end_turn()
            self.assertEqual(game.beer_turns_remaining,turns)
            self.assertEqual((game.units[a].hp,game.units[b].hp),
                             (health_a,health_b))
        self.assertIn('10% MAX PŻ',' '.join(e['text'] for e in game.event_journal))
        self.assertTrue(any('BURDA — ' in e['text'] and '11 DMG' in e['text']
                            for e in game.event_journal))
        game.assert_integrity()

    def test_defenses_and_visible_risk_use_individual_hit(self):
        game,a,b=self.scene(910502)
        game.units[a].shield=1
        game.units[b].armor_temp=8
        game.order_beer(0)
        self.assertEqual(next_brawl_damage(game),3)
        self.assertEqual(next_brawl_damage(game,a),3)
        self.assertEqual(next_brawl_damage(game,b),11)
        game.end_turn()
        self.assertEqual(game.units[a].hp,21)
        self.assertEqual(game.units[a].shield,0)
        self.assertEqual(game.units[b].hp,98)
        self.assertEqual(game.units[b].armor_temp,0)
        game.units[b].hp=8
        self.assertTrue(brawl_at_risk(game,b))
        self.assertFalse(brawl_at_risk(game,a))
        self.assertGreater(_projected_board_loss(game,1,2),0)

    def test_help_and_combat_book_record_ticks(self):
        game,a,b=self.scene(910503)
        game.order_beer(0)
        game.end_turn()
        help_text=' '.join(brawl_help_lines(game))
        self.assertIn('10% MAX PŻ',help_text)
        self.assertIn('W GÓRĘ',help_text)
        self.assertIn('obu graczy',help_text)
        html=render_combat_html({'seed':game.seed,
                                'event_journal':game.event_journal,
                                'combat_analysis':{'attacks':[]}})
        self.assertIn('Karczemna Burda — zapisane',html)
        self.assertIn('BURDA #1',html)
        self.assertIn('11 DMG',html)
        self.assertIn('ticków Karczemnej Burdy',html)
        self.assertNotIn('<script src=',html)

    def test_new_save_and_old_without_flag(self):
        game,a,b=self.scene(910504)
        game.order_beer(0)
        game.end_turn()
        with TemporaryDirectory() as directory:
            path=Path(directory)/'save.json'
            save_match(game,path)
            loaded=load_match(path)
            self.assertTrue(loaded.tavern_min_hp_damage_enabled)
            self.assertEqual(state_snapshot(loaded),state_snapshot(game))
            old=ready(910505)
            old.tavern_scaled_damage_enabled=True
            del old.tavern_min_hp_damage_enabled
            save_match(old,path)
            legacy=load_match(path)
            self.assertFalse(legacy.tavern_min_hp_damage_enabled)

    def test_new_match_signed_and_historical_omitted(self):
        fresh=Match(910506,audit_enabled=True,auctions_enabled=True,
                    auction_catalog='v22',tavern_scaled_damage_enabled=True,
                    tavern_min_hp_damage_enabled=True)
        rules=fresh.audit_initial['ruleset_state']
        self.assertTrue(rules['tavern_min_hp_damage_enabled'])
        old=Match(910506,audit_enabled=True,auctions_enabled=True,
                  auction_catalog='v22',tavern_scaled_damage_enabled=True)
        self.assertNotIn('tavern_min_hp_damage_enabled',
                         old.audit_initial['ruleset_state'])
        disabled=Match(910506,auctions_enabled=True,
                       auction_catalog='v22',tavern_min_hp_damage_enabled=True)
        self.assertFalse(disabled.tavern_min_hp_damage_enabled)

    def test_signed_new_replay_with_real_paid_tick(self):
        game=Match(910507,audit_enabled=True,auctions_enabled=True,
                   auction_catalog='v22',tavern_scaled_damage_enabled=True,
                   tavern_min_hp_damage_enabled=True)
        game.finish_mulligan(0,[])
        game.finish_mulligan(1,[])
        purchased=False
        ticks=0
        for _ in range(110):
            if game.phase=='auction':
                auction=game.auction
                if auction.phase=='bidding':
                    game.auction_pass(auction.turn)
                else:
                    offers=[o for o in auction.offers
                            if o.uid not in auction.picks.values()]
                    game.auction_pick(auction.turn,offers[0].uid)
                continue
            if game.phase!='turn':
                break
            if not purchased and game.can_order_beer(game.active):
                game.order_beer(game.active)
                purchased=True
            before=game.beer_turns_remaining
            game.end_turn()
            if purchased and before>game.beer_turns_remaining:
                ticks+=1
            if purchased and ticks>=3:
                break
        self.assertTrue(purchased)
        self.assertEqual(ticks,3)
        payload={'complete_from_start':True,'seed':game.seed,'version':'0.9.105',
                 'initial_state':game.audit_initial,
                 'actions':game.audit_actions,
                 'internal_events':game.audit_internal,
                 'event_journal':game.event_journal,
                 'final_state':state_snapshot(game),
                 'summary':{'ruleset_version':game.ruleset_version,
                            'vacant_slot_income_enabled':game.vacant_income_enabled}}
        self.assertTrue(verify_replay(
            payload,lambda seed,**kwargs:Match(seed,audit_enabled=True,**kwargs)))


class SidebarCopy09105(unittest.TestCase):
    def test_paging_shows_all_content_without_cutoff(self):
        pygame.font.init()
        class Fake:
            card_description_rect=staticmethod(SoloApp.card_description_rect)
            _wrap=SoloApp._wrap
            _text=SoloApp._text
            _scroll_sidebar_description=SoloApp._scroll_sidebar_description
            _draw_sidebar_description=SoloApp._draw_sidebar_description
        fake=Fake()
        fake.screen=pygame.Surface((1480,980))
        fake.fonts={n:pygame.font.Font(None,n) for n in (11,13,14)}
        fake._sidebar_desc_uid=None
        fake._sidebar_desc_scroll=0
        fake._sidebar_desc_maxscroll=0
        description=' '.join(('Pełne warunki działania zdolności i wyjątki.' for _ in range(25)))
        fake._draw_sidebar_description('S01',description)
        self.assertGreater(fake._sidebar_desc_maxscroll,0)
        fake._scroll_sidebar_description(-2)
        self.assertGreater(fake._sidebar_desc_scroll,0)
        fake._draw_sidebar_description('S01',description)
        self.assertGreater(fake._sidebar_desc_scroll,0)
        fake._draw_sidebar_description('S02',description)
        self.assertEqual(fake._sidebar_desc_scroll,0)


if __name__=='__main__':
    unittest.main()
