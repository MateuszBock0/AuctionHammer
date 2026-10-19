"""Acceptance: versioned Chorazy 3/5 for the player acting second."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from game.core.engine import Match
from game.core.audit import digest, state_snapshot, make_report, verify_replay
from game.core.persistence import load_match, save_match
from game.ui.app import SoloApp
from game.ui.card_summary import ability_summary
from game.ui.card_infographics import card_cue

TOKEN="SUM_START_GUARD"

def fresh(seed=41000,mode="unit_3_5"):
    return Match(seed,audit_enabled=True,auctions_enabled=True,
                 auction_catalog="v22",starting_compensation=mode)

def factory(seed,auctions_enabled=False,auction_catalog="v3",
            starting_compensation="coins"):
    return Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                 auction_catalog=auction_catalog,
                 starting_compensation=starting_compensation)

class ChorazyEngineAcceptance(unittest.TestCase):
    def test_both_seats_pool_stats_flavor_and_no_powers(self):
        seats=set()
        for seed in range(41000,41040):
            with self.subTest(seed=seed):
                g=fresh(seed)
                second=1-g.first
                seats.add(second)
                c=g.cards[TOKEN];u=g.units[TOKEN]
                self.assertEqual(len(g.defs),70)
                self.assertEqual(len(g.cards),71)
                self.assertEqual(g.players[second].board,[TOKEN])
                self.assertEqual((g.players[0].coins,g.players[1].coins),(0,0))
                self.assertEqual((u.atk,u.hp,u.max_hp),(3,5,5))
                self.assertEqual((u.shield,u.armor), (0,0))
                self.assertEqual(u.effects,[])
                self.assertEqual(c.definition.name,"Chorąży")
                self.assertEqual(c.definition.effect,"Chorąży zawsze zdąży.")
                self.assertEqual(c.definition.family,"Bez zdolności")
                self.assertEqual(c.owner,second)
                self.assertEqual(c.zone,"board")
                self.assertIn("Chorąży zawsze zdąży.",ability_summary(c).full)
                self.assertEqual(ability_summary(c).short,"BEZ ZDOLNOŚCI")
                self.assertEqual(card_cue(c).base,"BEZ ZDOLNOŚCI")
                self.assertEqual(card_cue(c).upgrade,"JEDNOSTKA STARTOWA")
                self.assertIn(TOKEN,g.ephemeral_ids)
                self.assertNotIn(TOKEN,g.bank)
                self.assertTrue(all(TOKEN not in p.hand+p.deck+p.grave for p in g.players))
                g.assert_integrity()
        self.assertEqual(seats,{0,1})

    def test_no_quick_attack_first_turn(self):
        g=fresh()
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        g.end_turn()
        self.assertEqual(g.active,1-g.first)
        self.assertEqual(g.legal_attacks(TOKEN),[])
        g.end_turn()
        g.end_turn()
        self.assertIn("hero:"+str(g.first),g.legal_attacks(TOKEN))
        g.assert_integrity()

    def test_removal_vanishes_forever(self):
        for death in (True,False):
            with self.subTest(death=death):
                g=fresh()
                g._remove_unit(TOKEN,death=death)
                self.assertNotIn(TOKEN,g.units)
                self.assertIn(TOKEN,g.vanished)
                self.assertEqual(g.cards[TOKEN].zone,"vanished")
                self.assertTrue(all(TOKEN not in p.grave+p.deck+p.hand for p in g.players))
                g.assert_integrity()

    def test_history_5x5_and_coins_unchanged(self):
        old=fresh(mode="unit_5_5")
        self.assertEqual((old.units[TOKEN].atk,old.units[TOKEN].hp),(5,5))
        self.assertEqual(old.cards[TOKEN].definition.name,"Strażnik Drugiego Gracza")
        self.assertEqual(old.cards[TOKEN].definition.effect,
                         "Stała jednostka 5/5 bez zdolności specjalnych.")
        self.assertEqual(old.audit_state_schema,3)
        coins=fresh(mode="coins")
        self.assertNotIn(TOKEN,coins.cards)
        self.assertEqual(coins.players[1-coins.first].coins,3)
        self.assertEqual(coins.audit_state_schema,2)
        self.assertEqual(fresh().audit_state_schema,3)
        with self.assertRaises(ValueError):
            fresh(mode="unknown")

    def test_save_load_mulligan_turn(self):
        g=fresh()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"save.json"
            for stage in (0,1):
                if stage:
                    g.finish_mulligan(0,[])
                    g.finish_mulligan(1,[])
                save_match(g,path)
                loaded=load_match(path)
                self.assertEqual(loaded.starting_compensation,"unit_3_5")
                self.assertEqual(digest(state_snapshot(loaded)),digest(state_snapshot(g)))
                loaded.assert_integrity()

    def test_all_three_signed_full_match_replays(self):
        from tools.simulate_v22 import simulate_one
        for mode in ("coins","unit_5_5","unit_3_5"):
            with self.subTest(mode=mode):
                complete,_=simulate_one(41888,starting_compensation=mode)
                self.assertTrue(verify_replay(make_report(complete)["payload"],factory))

    def test_unknown_audit_mode_must_fail(self):
        from tools.simulate_v22 import simulate_one
        complete,_=simulate_one(41889,starting_compensation="unit_3_5")
        report=make_report(complete)["payload"]
        report["initial_state"]["ruleset_state"]["starting_compensation"]="unit_2_2"
        with self.assertRaises(ValueError):
            verify_replay(report,factory)

class ChorazyUITest(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
    def tearDown(self):
        pygame.quit()
    def test_new_game_and_details(self):
        self.assertEqual(self.app.game.starting_compensation,"unit_3_5")
        self.app.restart()
        self.assertEqual(self.app.game.cards[TOKEN].definition.name,"Chorąży")
        self.app.details_card=TOKEN
        self.app._draw_details()
        self.app.details_card=None
        self.app.sidebar_card=TOKEN
        self.app._draw_sidebar()
        self.assertIn("Chorąży zawsze zdąży.",
                      ability_summary(self.app.game.cards[TOKEN]).full)
    def test_mulligan_caption_matches_loaded_mode(self):
        for mode,expected in (("coins","+3 MONETY"),
                              ("unit_5_5","STRAŻNIK 5/5"),
                              ("unit_3_5","CHORĄŻY 3/5")):
            with self.subTest(mode=mode):
                self.app.game=fresh(mode=mode)
                seen=[]
                old=self.app._text
                def observe(label,*args,**kwargs):
                    seen.append(str(label))
                    return old(label,*args,**kwargs)
                with patch.object(self.app,"_text",side_effect=observe):
                    self.app._draw_sidebar()
                self.assertTrue(any(expected in line for line in seen),seen[-10:])

if __name__=="__main__":
    unittest.main()
