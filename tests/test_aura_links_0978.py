"""0.9.78: live aura links exactly follow authoritative board and effects."""
from __future__ import annotations

import os
from dataclasses import replace
from copy import deepcopy
from unittest.mock import patch
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.models import Card, Effect
from game.core.audit import digest,state_snapshot
from game.ui.aura_links import AuraLink,live_aura_links
from game.ui.app import SoloApp
from test_engine import setup_game,force_unit


def fixed(seed=978001):
    game=setup_game(seed)
    game.fixed_board_slots=True
    return game


def source_general(game,rarity):
    definition=replace(game.cards['S01'].definition,
                       id='A002',name='Generał Oddziału Natarcia')
    game.cards['TEST_GENERAL']=Card('TEST_GENERAL',definition)
    force_unit(game,'TEST_GENERAL',0,slot=3)
    game.auction_awards['TEST_GENERAL']={
        'archetype':'A002','rarity':rarity}
    return game.units['TEST_GENERAL']


class AuraLinkRules0978(unittest.TestCase):
    def test_s34_right_neighbor_is_strict_priority_with_real_bonus(self):
        g=fixed()
        u=force_unit(g,'S34',0,slot=2)
        u.ability_level=2
        force_unit(g,'S01',0,slot=1)
        force_unit(g,'S02',0,slot=3)
        g._update_auras()
        before=digest(state_snapshot(g))
        self.assertEqual(live_aura_links(g,'S34'),
                         (AuraLink('S34','S02','atk',3,'ATK +3'),))
        self.assertEqual(digest(state_snapshot(g)),before)

    def test_s34_uses_left_when_right_is_empty(self):
        g=fixed(978002)
        force_unit(g,'S34',0,slot=2)
        force_unit(g,'S01',0,slot=1)
        g._update_auras()
        self.assertEqual([(x.target,x.amount) for x in live_aura_links(g,'S34')],
                         [('S01',1)])

    def test_s34_enemy_mode_is_negative_exact_matching_slot(self):
        g=fixed(978003)
        u=force_unit(g,'S34',0,slot=2)
        u.ability_level=1
        u.aura_mode='enemy'
        force_unit(g,'S09',1,slot=2)
        force_unit(g,'S01',1,slot=1)
        g._update_auras()
        self.assertEqual(live_aura_links(g,'S34'),
                         (AuraLink('S34','S09','atk',-2,'ATK -2'),))
        self.assertEqual(live_aura_links(g,'S09'),
                         (AuraLink('S34','S09','atk',-2,'ATK -2'),))

    def test_s35_allied_max_hp_contributions_multiple_targets(self):
        g=fixed(978004)
        source=force_unit(g,'S35',0,slot=2)
        source.ability_level=2
        force_unit(g,'S01',0,slot=0)
        force_unit(g,'S02',0,slot=4)
        force_unit(g,'S09',1,slot=2)
        g._update_auras()
        links=live_aura_links(g,'S35')
        self.assertEqual({(l.target,l.amount,l.label) for l in links},
                         {('S01',3,'MAX PŻ +3'),
                          ('S02',3,'MAX PŻ +3')})
        self.assertNotIn('S35',{l.target for l in links})
        self.assertEqual(g.units['S01'].aura_hp,3)

    def test_s35_enemy_debuff_respects_actual_owner(self):
        g=fixed(978005)
        source=force_unit(g,'S35',0,slot=2)
        source.aura_mode='enemy'
        force_unit(g,'S01',0,slot=1)
        force_unit(g,'S09',1,slot=4)
        g._update_auras()
        self.assertEqual([(l.target,l.kind,l.amount) for l in live_aura_links(g,'S35')],
                         [('S09','max_hp',-1)])

    def test_s105_read_actual_unspent_aura_armor_value(self):
        g=fixed(978006)
        source=force_unit(g,'S105',0,slot=2)
        source.ability_level=2
        force_unit(g,'S01',0,slot=0)
        force_unit(g,'S02',0,slot=3)
        g._update_auras()
        self.assertEqual({(l.target,l.amount) for l in live_aura_links(g,'S105')},
                         {('S01',4),('S02',4)})
        g.units['S01'].aura_armor['S105']=1
        g.units['S02'].aura_armor['S105']=0
        self.assertEqual(live_aura_links(g,'S105'),
                         (AuraLink('S105','S01','armor',1,'PANC. +1'),))

    def test_incoming_multiple_sources_only_when_unit_is_beneficiary(self):
        g=fixed(978007)
        force_unit(g,'S34',0,slot=1)
        force_unit(g,'S35',0,slot=0)
        force_unit(g,'S02',0,slot=2)
        g._update_auras()
        links=live_aura_links(g,'S02')
        self.assertEqual({(l.source,l.kind) for l in links},
                         {('S34','atk'),('S35','max_hp')})

    def test_stun_and_silence_never_show_inactive_source(self):
        for blocked in ('stun','silence'):
            with self.subTest(blocked=blocked):
                g=fixed(978008)
                src=force_unit(g,'S35',0,slot=0)
                force_unit(g,'S01',0,slot=1)
                src.effects.append(Effect(blocked))
                g._update_auras()
                self.assertEqual(live_aura_links(g,'S35'),())
                self.assertEqual(live_aura_links(g,'S01'),())

    def test_bronze_general_global_bonus_including_self_no_upgrade_guess(self):
        g=Match(978009,auctions_enabled=True,auction_catalog='v22',
                fixed_board_slots=True,starting_compensation='coins')
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        g.active=0
        g.phase='turn'
        source_general(g,'podstawowa')
        force_unit(g,'S01',0,slot=0)
        force_unit(g,'S09',1,slot=1)
        g._update_auras()
        items=live_aura_links(g,'TEST_GENERAL')
        self.assertEqual({(l.target,l.amount) for l in items},
                         {('S01',1),('S09',1),('TEST_GENERAL',1)})
        self.assertEqual(g.units['S09'].aura_atk,1)
        g.auction_awards['TEST_GENERAL']['rarity']='rzadka'
        self.assertEqual(live_aura_links(g,'TEST_GENERAL'),())
        g.auction_awards['TEST_GENERAL']['rarity']='legendarna'
        self.assertEqual(live_aura_links(g,'TEST_GENERAL'),())

    def test_legacy_compact_board_keeps_engine_neighbor_order(self):
        g=setup_game(978010)
        source=force_unit(g,'S34',0)
        force_unit(g,'S01',0)
        force_unit(g,'S02',0)
        source.aura_mode='ally'
        g._update_auras()
        self.assertEqual([(l.target,l.amount) for l in live_aura_links(g,'S34')],
                         [('S01',1)])

    def test_s108_never_painted_as_committed_buff(self):
        g=fixed(978011)
        force_unit(g,'S108',0,slot=4)
        force_unit(g,'S09',1,slot=4)
        g._update_auras()
        self.assertEqual(live_aura_links(g,'S108'),())

    def test_no_ghost_link_after_source_is_removed(self):
        g=fixed(978012)
        force_unit(g,'S34',0,slot=0)
        force_unit(g,'S01',0,slot=1)
        g._update_auras()
        self.assertTrue(live_aura_links(g,'S34'))
        g._remove_unit('S34',death=False)
        g._update_auras()
        self.assertEqual(live_aura_links(g,'S34'),())
        self.assertEqual(live_aura_links(g,'S01'),())


class AuraVisualAcceptance0978(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        self.app.game=fixed(978101)
        force_unit(self.app.game,'S34',0,slot=2)
        force_unit(self.app.game,'S01',0,slot=3)
        self.app.game._update_auras()
        self.app.selected='S34'

    def tearDown(self):
        pygame.quit()

    def test_visual_links_are_read_only_and_hitboxes_stay_put(self):
        app=self.app
        before=digest(state_snapshot(app.game))
        rect=app.slot_rect(0,2)
        with patch.object(app,'card_under',return_value=None):
            with patch('game.ui.app.pygame.draw.line',
                       wraps=pygame.draw.line) as lines:
                app._draw_aura_links()
        self.assertTrue(lines.called)
        self.assertEqual(digest(state_snapshot(app.game)),before)
        self.assertEqual(app.slot_rect(0,2),rect)
        self.assertEqual(app.game.slot_of('S34'),2)

    def test_hover_source_works_without_click_and_incoming_focus(self):
        app=self.app
        app.selected=None
        with patch.object(app,'card_under',return_value='S34'):
            self.assertEqual(app._aura_focus(),'S34')
        with patch.object(app,'card_under',return_value='S01'):
            self.assertEqual(app._aura_focus(),'S01')
        with patch.object(app,'card_under',return_value=None):
            self.assertIsNone(app._aura_focus())

    def test_replay_menu_and_modal_suppress_lines(self):
        app=self.app
        with patch.object(app,'card_under',return_value='S34'):
            app.menu_open=True
            self.assertIsNone(app._aura_focus())
            app.menu_open=False
            app.history_open=True
            self.assertIsNone(app._aura_focus())
            app.history_open=False
            app.game.pending=object()
            self.assertIsNone(app._aura_focus())
            app.game.pending=None
            app.replay_index=0
            self.assertIsNone(app._aura_focus())

    def test_full_board_and_no_aura_no_unrelated_lines(self):
        app=self.app
        app.selected='S01'
        with patch.object(app,'card_under',return_value=None):
            # S01 receives S34 aura: incoming arrow to selected beneficiary.
            self.assertEqual(len(live_aura_links(app.game,'S01')),1)
            with patch('game.ui.app.pygame.draw.line',
                       wraps=pygame.draw.line) as lines:
                app._draw_aura_links()
            self.assertTrue(lines.called)
        app.game.units['S34'].effects.append(Effect('silence'))
        app.game._update_auras()
        with patch.object(app,'card_under',return_value=None):
            with patch('game.ui.app.pygame.draw.line',
                       wraps=pygame.draw.line) as lines:
                app._draw_aura_links()
            self.assertFalse(lines.called)


if __name__=='__main__':
    unittest.main()
