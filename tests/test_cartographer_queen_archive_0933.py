"""0.9.33: live v22 Kartograf, symmetric Queen, persistent all-match archive.

All tests use real Match commands; v4 historical rules stay unchanged.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from game.core.engine import Match
from game.core.audit import (archive_path, list_archived_matches,
                             read_report, write_last_match)
from test_auction_v22_0931 import ready, award, choose
from test_auction_v4_engine import place_basic


class CartographerDeckRefillTests(unittest.TestCase):
    def test_basic_refills_empty_deck_from_own_grave_and_draws(self):
        g=ready(93301)
        own=g.players[0]
        used=list(own.deck)
        for cid in used:
            place_basic(g,cid,0,zone='grave')
        self.assertFalse(own.deck)
        self.assertEqual(set(own.grave),set(used))
        cart=award(g,'A016',0)
        g.play(cart)
        self.assertEqual(g.pending.uid,cart)
        self.assertTrue(all(c.mode=='cart_draw' for c in g.pending.choices))
        self.assertEqual(len(g.pending.choices),3)
        self.assertFalse(own.grave)
        self.assertEqual(set(own.deck),set(used))
        target=g.pending.choices[0].target
        choose(g,'cart_draw',target)
        self.assertIn(target,own.hand)
        self.assertEqual(g.cards[target].zone,'hand')
        self.assertTrue(own.played_this_turn)
        g.assert_integrity()

    def test_rare_recycles_again_after_draw_and_plays_extra_card(self):
        g=ready(93302)
        own=g.players[0]
        first=own.deck[-1]
        for cid in list(own.deck):
            if cid!=first:
                place_basic(g,cid,0,zone='grave')
        self.assertEqual(own.deck,[first])
        cart=award(g,'A016',1)
        g.play(cart)
        choose(g,'cart_draw',first)
        self.assertEqual(g.pending.context,'auction_cart_play')
        self.assertTrue(own.deck)
        self.assertFalse(own.grave)
        choice=next(c for c in g.pending.choices
                    if c.mode=='cart_play' and c.target in own.deck)
        choose(g,'cart_play',choice.target)
        self.assertIn(choice.target,own.board)
        self.assertEqual(g.cards[choice.target].zone,'board')
        self.assertTrue(own.played_this_turn)
        g.assert_integrity()

    def test_legendary_refills_without_another_ally(self):
        g=ready(93303)
        own=g.players[0]
        for cid in list(own.deck):
            place_basic(g,cid,0,zone='grave')
        cart=award(g,'A016',2)
        g.play(cart)
        self.assertIsNotNone(g.pending)
        self.assertEqual(g.pending.context,'play')
        choices=[c for c in g.pending.choices
                 if c.mode=='cart_play' and c.target in own.deck]
        self.assertTrue(choices)
        chosen=choices[0].target
        choose(g,'cart_play',chosen)
        self.assertIn(chosen,own.board)
        g.assert_integrity()


class QueenSymmetryTests(unittest.TestCase):
    def test_v22_summons_have_exact_rarity_stats(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93310+tier)
                queen=award(g,'A010',tier,zone='board')
                g.end_turn()
                self.assertEqual({ch.mode for ch in g.pending.choices},
                                 {'summon','grow'})
                choose(g,'summon')
                soldiers=[u for u in g.players[0].board if u.startswith('SUM')]
                self.assertEqual(len(soldiers),(1,2,2)[tier])
                for uid in soldiers:
                    unit=g.units[uid]
                    self.assertEqual((unit.atk,unit.max_hp,unit.hp),
                                     ((1,1,1),(2,2,2),(3,3,3))[tier])
                    self.assertEqual(any(e.kind=='taunt' for e in unit.effects),
                                     tier==1)
                g.assert_integrity()

    def test_v22_growth_matches_soldier_strength(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93320+tier)
                queen=award(g,'A010',tier,zone='board')
                initial=g.units[queen]
                initial_stats=(initial.atk,initial.max_hp,initial.hp)
                g.end_turn()
                choose(g,'grow')
                unit=g.units[queen]
                bonus=(1,2,3)[tier]
                self.assertEqual((unit.atk,unit.max_hp,unit.hp),
                                 tuple(v+bonus for v in initial_stats))
                self.assertEqual(any(e.kind=='taunt' for e in unit.effects),
                                 tier==1)
                g.assert_integrity()

    def test_v22_legendary_does_not_copy_stronger_ally(self):
        g=ready(93325)
        friend=place_basic(g,'S01',0)
        g.units[friend].base_attack=14
        g.units[friend].base_max_hp=19
        g.units[friend].hp=19
        queen=award(g,'A010',2,zone='board')
        g.end_turn()
        choose(g,'summon')
        soldiers=[g.units[cid] for cid in g.players[0].board if cid.startswith('SUM')]
        self.assertEqual([(u.atk,u.max_hp) for u in soldiers],[(3,3),(3,3)])
        g.assert_integrity()


class PersistentArchiveTests(unittest.TestCase):
    @staticmethod
    def finished(seed,winner):
        game=Match(seed,audit_enabled=True,auctions_enabled=True,
                   auction_catalog='v22')
        game.phase='finished'
        game.winner=winner
        return game

    def test_every_finished_match_is_archived_once_and_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'AuctionHammer-OSTATNI-MECZ.json'
            a=self.finished(93331,0)
            b=self.finished(93332,1)
            write_last_match(a,path)
            records=list_archived_matches(archive_path(path))
            self.assertEqual(len(records),1)
            first=archive_path(path)/records[0]['file']
            self.assertEqual(read_report(first)['seed'],a.seed)
            compressed=first.read_bytes()
            write_last_match(a,path)
            self.assertEqual(len(list_archived_matches(archive_path(path))),1)
            self.assertEqual(first.read_bytes(),compressed)
            write_last_match(b,path)
            records=list_archived_matches(archive_path(path))
            self.assertEqual(len(records),2)
            self.assertEqual({read_report(archive_path(path)/item['file'])['seed']
                              for item in records},{a.seed,b.seed})
            self.assertEqual(read_report(path)['seed'],b.seed)
            self.assertTrue((archive_path(path)/'indeks.json').is_file())

    def test_old_last_match_is_migrated_before_first_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'AuctionHammer-OSTATNI-MECZ.json'
            old=self.finished(93341,0)
            new=self.finished(93342,1)
            from game.core.audit import make_report
            path.write_text(json.dumps(make_report(old),ensure_ascii=False),
                            encoding='utf-8')
            self.assertFalse(archive_path(path).exists())
            write_last_match(new,path)
            old_and_new={read_report(archive_path(path)/item['file'])['seed']
                         for item in list_archived_matches(archive_path(path))}
            self.assertEqual(old_and_new,{old.seed,new.seed})
            self.assertEqual(read_report(path)['seed'],new.seed)


if __name__=='__main__':
    unittest.main()
