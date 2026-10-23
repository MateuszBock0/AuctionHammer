"""0.9.62: starter Chorazy kill-based growth, old archives and persistence."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.engine import Match
from game.core.audit import (
    digest, initialize_audit, make_report, state_snapshot, verify_replay)
from game.core.persistence import load_match, save_match
from game.ui.card_view import CardView, ART, CHORAZY_ART_LEVELS
from test_engine import force_unit


GUARD="SUM_START_GUARD"


def fresh(seed=96201,mode="choice_2_5_or_coins"):
    game=Match(seed,audit_enabled=False,auctions_enabled=True,
               auction_catalog="v22",starting_compensation=mode,
               fixed_board_slots=True)
    if mode=="choice_2_5_or_coins":
        game.choose_starting_compensation(1-game.first,"unit_2_5")
    game.finish_mulligan(0,[])
    game.finish_mulligan(1,[])
    owner=game.units[GUARD].owner
    game.active=owner
    game.phase="turn"
    game.players[owner].turn_count=max(1,game.players[owner].turn_count)
    game.units[GUARD].played_turn=0
    return game


def strike_victim(game,cid,hp=1,atk=0):
    guard=game.units[GUARD]
    guard.attacks=0
    game.active=guard.owner
    target=force_unit(game,cid,1-guard.owner)
    target.base_attack=atk
    target.base_max_hp=hp
    target.hp=hp
    assert cid in game.legal_attacks(GUARD), game.legal_attacks(GUARD)
    game.attack(GUARD,cid)


def replay_factory(seed,auctions_enabled=False,auction_catalog="v3",
                   starting_compensation="coins"):
    return Match(seed,audit_enabled=True,
                 auctions_enabled=auctions_enabled,
                 auction_catalog=auction_catalog,
                 starting_compensation=starting_compensation)


class StarterGuardKillTests(unittest.TestCase):
    def test_three_direct_kills_grow_attack_hp_and_cap(self):
        game=fresh()
        self.assertTrue(game.starter_guard_kill_rule)
        self.assertEqual((game.units[GUARD].atk,game.units[GUARD].hp),(2,5))
        for n,cid in enumerate(("S01","S02","S03","S04"),1):
            strike_victim(game,cid)
            capped=min(n,3)
            unit=game.units[GUARD]
            self.assertEqual(game.starter_guard_kills,capped)
            self.assertEqual((unit.base_attack,unit.base_max_hp,unit.hp),
                             (2+capped,5+2*capped,5+2*capped))
            self.assertEqual(CHORAZY_ART_LEVELS[min(capped,2)],
                             ("chorazy_rzadka.png" if n==1 else
                              "chorazy_legendarna.png"))
        self.assertEqual(game.starter_guard_kills,3)
        game.assert_integrity()

    def test_counterattack_does_not_award_a_kill(self):
        game=fresh(96202)
        guard=game.units[GUARD]
        owner=guard.owner
        attacker=force_unit(game,"S01",1-owner)
        attacker.hp=1
        attacker.base_max_hp=1
        attacker.base_attack=1
        attacker.played_turn=0
        game.players[1-owner].turn_count=max(1,game.players[1-owner].turn_count)
        game.active=1-owner
        game.attack("S01",GUARD)
        self.assertEqual(game.starter_guard_kills,0)
        self.assertEqual(guard.base_attack,2)
        self.assertNotIn("S01",game.units)

    def test_simultaneous_double_ko_does_not_rescue_guard(self):
        game=fresh(96203)
        strike_victim(game,"S02",hp=1,atk=12)
        self.assertNotIn(GUARD,game.units)
        self.assertEqual(game.starter_guard_kills,0)

    def test_noncombat_death_and_hero_damage_do_not_count(self):
        game=fresh(96204)
        force_unit(game,"S01",1-game.units[GUARD].owner)
        game._damage("S01",100)
        self.assertEqual(game.starter_guard_kills,0)
        game.units[GUARD].attacks=0
        target="hero:"+str(1-game.units[GUARD].owner)
        self.assertIn(target,game.legal_attacks(GUARD))
        game.attack(GUARD,target)
        self.assertEqual(game.starter_guard_kills,0)

    def test_historical_3_5_guard_has_no_upgrade(self):
        game=fresh(96205,"unit_3_5")
        self.assertFalse(game.starter_guard_kill_rule)
        strike_victim(game,"S01")
        self.assertEqual(game.starter_guard_kills,0)
        self.assertEqual((game.units[GUARD].atk,game.units[GUARD].max_hp),(3,5))

    def test_save_load_keeps_progress_and_signed_state(self):
        game=fresh(96206)
        strike_victim(game,"S01")
        before=digest(state_snapshot(game))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"game.json"
            save_match(game,path)
            saved=load_match(path)
        self.assertTrue(saved.starter_guard_kill_rule)
        self.assertEqual(saved.starter_guard_kills,1)
        self.assertEqual(digest(state_snapshot(saved)),before)
        saved.assert_integrity()

    def test_previous_audit_has_no_new_field_and_replays_bit_identically(self):
        game=Match(96207,audit_enabled=True,auctions_enabled=True,
                   auction_catalog="v22",
                   starting_compensation="choice_2_5_or_coins")
        # Simulate a pre-0.9.62 archive: its signed state has no kill marker.
        game.starter_guard_kill_rule=False
        game.starter_guard_kills=0
        initialize_audit(game)
        game.choose_starting_compensation(1-game.first,"unit_2_5")
        payload=make_report(game)["payload"]
        self.assertNotIn("starter_guard_kills",
                         payload["initial_state"]["ruleset_state"])
        frozen=digest(payload)
        self.assertTrue(verify_replay(payload,replay_factory))
        self.assertEqual(digest(payload),frozen)

    def test_new_audit_declares_signed_kill_rule_and_replays(self):
        game=Match(96208,audit_enabled=True,auctions_enabled=True,
                   auction_catalog="v22",
                   starting_compensation="choice_2_5_or_coins")
        before=state_snapshot(game)["ruleset_state"]
        self.assertIs(before["starter_guard_kill_rule"],True)
        self.assertEqual(before["starter_guard_kills"],0)
        game.choose_starting_compensation(1-game.first,"unit_2_5")
        payload=make_report(game)["payload"]
        self.assertTrue(verify_replay(payload,replay_factory))

    def test_old_s34_art_does_not_upgrade(self):
        pygame.init()
        pygame.display.set_mode((32,32))
        view=CardView()
        self.assertEqual(ART["S34"],"chorazy_krolewskiej_kompanii.png")
        for level in (0,1,2,3,10):
            view.art("S34","Ludzie",(96,96),level=level)
        self.assertTrue(all(x[0].startswith("chorazy_krolewskiej")
                            for x in view.images._scaled if isinstance(x[0],str)))


if __name__=="__main__":
    unittest.main()
