"""Release 0.9.33 acceptance tests beyond the first-pass unit regressions.

Covers corner cases, legacy v4 behavior, UI and multi-match history.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.engine import Match
from game.core.audit import (archive_path, list_archived_matches,
                             read_report, write_last_match)
from game.ui.app import SoloApp
from test_auction_v22_0931 import ready as ready_v22, award as award_v22, choose
from test_auction_v4_engine import ready as ready_v4, award as award_v4, place_basic


class CartographerEdgeAcceptance(unittest.TestCase):
    def test_basic_no_deck_and_no_grave_has_no_spurious_choice(self):
        game=ready_v22(933501)
        for uid in list(game.players[0].deck):
            place_basic(game,uid,0,zone="hand")
        self.assertFalse(game.players[0].deck)
        self.assertFalse(game.players[0].grave)
        cart=award_v22(game,"A016",0)
        game.play(cart)
        self.assertIsNone(game.pending)
        self.assertEqual(game.players[0].grave,[])
        self.assertEqual(game.players[0].deck,[])
        game.assert_integrity()

    def test_rare_can_play_enemy_deck_even_when_own_draw_is_impossible(self):
        game=ready_v22(933502)
        for uid in list(game.players[0].deck):
            place_basic(game,uid,0,zone="hand")
        self.assertFalse(game.players[0].deck)
        self.assertFalse(game.players[0].grave)
        enemy_deck=set(game.players[1].deck)
        cart=award_v22(game,"A016",1)
        game.play(cart)
        self.assertIsNotNone(game.pending)
        self.assertEqual(game.pending.context,"auction_cart_play")
        selection=next(c.target for c in game.pending.choices
                       if c.mode=="cart_play" and c.target in enemy_deck)
        choose(game,"cart_play",selection)
        self.assertIn(selection,game.players[0].board)
        self.assertEqual(game.cards[selection].owner,0)
        self.assertEqual(game.cards[selection].zone,"board")
        self.assertNotIn(selection,game.players[1].deck)
        game.assert_integrity()

    def test_legendary_can_take_enemy_deck_when_own_cards_exhausted(self):
        game=ready_v22(933503)
        for uid in list(game.players[0].deck):
            place_basic(game,uid,0,zone="hand")
        enemy_deck=set(game.players[1].deck)
        cart=award_v22(game,"A016",2)
        game.play(cart)
        self.assertIsNotNone(game.pending)
        selection=next(c.target for c in game.pending.choices
                       if c.mode=="cart_play" and c.target in enemy_deck)
        choose(game,"cart_play",selection)
        self.assertIn(selection,game.players[0].board)
        self.assertEqual(game.cards[selection].owner,0)
        game.assert_integrity()

    def test_legendary_full_board_does_not_shuffle_unusable_grave(self):
        game=ready_v22(933504)
        initial_deck=list(game.players[0].deck)
        for uid in initial_deck[:4]:
            place_basic(game,uid,0,zone="board")
        place_basic(game,initial_deck[4],0,zone="grave")
        cart=award_v22(game,"A016",2)
        grave=list(game.players[0].grave)
        self.assertEqual(len(game.players[0].board),4)
        game.play(cart)
        self.assertEqual(len(game.players[0].board),5)
        self.assertEqual(game.players[0].grave,grave)
        self.assertEqual(game.players[0].deck,[])
        self.assertIsNone(game.pending)
        game.assert_integrity()


class QueenCapacityAndLegacyAcceptance(unittest.TestCase):
    def test_rare_and_legendary_summon_only_into_empty_slots(self):
        for tier in (1,2):
            with self.subTest(tier=tier):
                game=ready_v22(933520+tier)
                for uid in list(game.players[0].deck)[:3]:
                    place_basic(game,uid,0,zone="board")
                queen=award_v22(game,"A010",tier,zone="board")
                self.assertEqual(len(game.players[0].board),4)
                game.end_turn()
                choose(game,"summon")
                soldiers=[uid for uid in game.players[0].board
                          if uid.startswith("SUM")]
                self.assertEqual(len(soldiers),1)
                self.assertEqual(len(game.players[0].board),5)
                self.assertEqual((game.units[soldiers[0]].atk,
                                  game.units[soldiers[0]].max_hp),
                                 ((2,2) if tier==1 else (3,3)))
                game.assert_integrity()

    def test_v4_rare_queen_still_has_original_four_four_growth(self):
        game=ready_v4(933541)
        queen=award_v4(game,"A010",1,zone="board")
        old=(game.units[queen].atk,game.units[queen].max_hp)
        game.end_turn()
        game.choose(next(i for i,ch in enumerate(game.pending.choices)
                         if ch.mode=="grow"))
        self.assertEqual((game.units[queen].atk,game.units[queen].max_hp),
                         (old[0]+4,old[1]+4))
        game.assert_integrity()

    def test_v4_legendary_queen_still_copies_ally_not_fixed_token(self):
        game=ready_v4(933542)
        friend=place_basic(game,"S01",0,zone="board")
        game.units[friend].base_attack=14
        game.units[friend].base_max_hp=19
        game.units[friend].hp=19
        queen=award_v4(game,"A010",2,zone="board")
        game.end_turn()
        game.choose(next(i for i,ch in enumerate(game.pending.choices)
                         if ch.mode=="summon"))
        soldiers=[game.units[uid] for uid in game.players[0].board
                  if uid.startswith("SUM")]
        self.assertEqual([(x.atk,x.max_hp) for x in soldiers],
                         [(14,19),(14,19)])
        game.assert_integrity()

    def test_v22_queen_can_use_legendary_choices_alone(self):
        game=ready_v22(933543)
        queen=award_v22(game,"A010",2,zone="board")
        game.end_turn()
        self.assertEqual({c.mode for c in game.pending.choices},
                         {"grow","summon"})
        choose(game,"grow")
        self.assertEqual((game.units[queen].atk,game.units[queen].max_hp),
                         (7,10))
        game.assert_integrity()


class ArchiveLongTermAcceptance(unittest.TestCase):
    @staticmethod
    def completed(seed, winner=0):
        game=Match(seed,audit_enabled=True,auctions_enabled=True,
                   auction_catalog="v22")
        game.phase="finished"
        game.winner=winner
        return game

    def test_five_consecutive_matches_survive_overwrites_and_rereads(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"AuctionHammer-OSTATNI-MECZ.json"
            for i in range(5):
                write_last_match(self.completed(933560+i,i%2),file)
            folder=archive_path(file)
            index=list_archived_matches(folder)
            self.assertEqual(len(index),5)
            self.assertEqual(len({entry["id"] for entry in index}),5)
            self.assertEqual(len(list(folder.glob("mecz_*.json.gz"))),5)
            self.assertEqual({read_report(folder/item["file"])["seed"]
                              for item in index},
                             set(range(933560,933565)))
            self.assertEqual(read_report(file)["seed"],933564)
            self.assertEqual({item["winner"] for item in index},{0,1})
            write_last_match(self.completed(933564,0),file)
            self.assertEqual(len(list_archived_matches(folder)),5)

    def test_corrupt_last_match_does_not_silently_get_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"AuctionHammer-OSTATNI-MECZ.json"
            write_last_match(self.completed(933571),file)
            file.write_text('{"payload":',encoding="utf-8")
            with self.assertRaises(ValueError):
                write_last_match(self.completed(933572),file)
            self.assertEqual(file.read_text(encoding="utf-8"),'{"payload":')
            self.assertEqual(len(list_archived_matches(archive_path(file))),1)

    def test_all_archived_matches_visible_in_index_regardless_of_menu_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"AuctionHammer-OSTATNI-MECZ.json"
            for i in range(6):
                write_last_match(self.completed(933581+i),file)
            with patch("game.core.audit.audit_path",return_value=file):
                self.assertEqual(len(list_archived_matches()),6)


class ArchiveMenuAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            cls.app=SoloApp(start_in_menu=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_tavern_opens_history_and_archived_folder(self):
        app=self.app
        app.menu_page="main"
        records=[{"exported_at_utc":"2026-10-19T11:20:00+00:00",
                  "winner":0,"rounds":12,"file":"game.json.gz","id":"abc"}]
        with patch("game.ui.app.list_archived_matches",return_value=records),patch.object(
            app,"_open_audit_folder",return_value=True
        ) as folder:
            app._menu_click(pygame.Rect(625,282,240,34).center)
            self.assertEqual(app.menu_page,"archive")
            self.assertEqual(app._archive_records,records)
            app._draw_menu()
            app._menu_click(pygame.Rect(535,322,420,61).center)
            folder.assert_called_once_with(archive=True)
            app._menu_click(pygame.Rect(535,322+4*81,420,61).center)
            self.assertEqual(app.menu_page,"main")

    def test_empty_archive_is_accessible_without_crashing(self):
        app=self.app
        app.menu_page="main"
        with patch("game.ui.app.list_archived_matches",return_value=[]):
            app._menu_click(pygame.Rect(625,282,240,34).center)
            self.assertEqual(app.menu_page,"archive")
            self.assertEqual(app._archive_records,[])
            app._draw_menu()
            app._menu_click(pygame.Rect(535,322+4*81,420,61).center)
            self.assertEqual(app.menu_page,"main")


if __name__=="__main__":
    unittest.main()
