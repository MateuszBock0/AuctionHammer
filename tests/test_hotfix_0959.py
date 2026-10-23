"""0.9.59: historical replay compatibility and readable General status."""
from __future__ import annotations

import copy
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.core.audit import (digest, initialize_audit, state_snapshot,
                             verify_replay)
from game.core.auction_abilities import execute, mark_general_new_ally
from game.core.combat_analysis import build_combat_analysis
from game.core.combat_html import render_combat_html
from game.core.models import Choice
from game.ui.card_view import status_display_priority
from game.core.status_view import VisibleStatus
from test_auction_v4_engine import ready, place_basic, award


ARCHIVED_VERBOSE_BUILD = "164cdfcfff7368589dabfcda9d0256b0d3dbb0d7"
ARCHIVED_CLASSIC_BUILD = "cbce8308608599cb8aa32f8304b650d78317432e"


def _prepared_game(seed):
    game = ready(seed)
    place_basic(game, "S35", owner=0)
    uid = award(game, "A002", tier=1, owner=0, zone="hand")
    game.audit_enabled = True
    initialize_audit(game, complete=True)
    return game, uid


class HistoricalGeneralReplayTests(unittest.TestCase):
    def test_both_published_general_journal_versions_replay_without_altering_rules(self):
        for verbose, build_sha in ((False, ARCHIVED_CLASSIC_BUILD),
                                   (True, ARCHIVED_VERBOSE_BUILD)):
            with self.subTest(verbose=verbose):
                seed = 95910
                game, uid = _prepared_game(seed)
                game._replay_verbose_general_0958 = verbose
                game.play(uid)
                self.assertIsNotNone(game.pending)
                game.choose(0)
                self.assertEqual(game.auction_general_targets[uid], "S35")
                old = "Generał wybiera Komendant Straży do podwójnych ataków."
                new = ("Generał wybiera Komendant Straży: do 2 ataków "
                       "i obrażenia standardowych ataków ×2.")
                lines = [e["text"] for e in game.event_journal]
                self.assertIn(new if verbose else old, lines)
                self.assertNotIn(old if verbose else new, lines)
                payload = {
                    "seed": seed,
                    "initial_state": game.audit_initial,
                    "complete_from_start": True,
                    "actions": game.audit_actions,
                    "internal_events": game.audit_internal,
                    "event_journal": game.event_journal,
                    "final_state": state_snapshot(game),
                    "environment": {"build": {"commit": build_sha}},
                }
                frozen = digest(payload)
                self.assertTrue(verify_replay(payload, lambda seed, **kw: _prepared_game(seed)[0]))
                self.assertEqual(digest(payload), frozen)

    def test_new_games_keep_classic_events_and_legendary_grants_silent(self):
        rare = ready(95911)
        place_basic(rare, "S35", owner=0)
        leader = award(rare, "A002", tier=1, zone="board")
        execute(rare, leader, "play", Choice("general_target", "S35", ""))
        self.assertEqual(
            rare.event_journal[-1]["text"],
            "Generał wybiera Komendant Straży do podwójnych ataków.")

        legendary = ready(95912)
        src = award(legendary, "A002", tier=2, zone="board")
        unit = place_basic(legendary, "S01", owner=0)
        before = len(legendary.event_journal)
        mark_general_new_ally(legendary, unit)
        self.assertIn(unit, legendary.auction_general_grants[src])
        self.assertEqual(len(legendary.event_journal), before)
        mark_general_new_ally(legendary, unit)
        self.assertEqual(len(legendary.event_journal), before)

    def test_archived_verbose_legendary_grants_generate_exactly_one_event(self):
        legendary = ready(95913)
        src = award(legendary, "A002", tier=2, zone="board")
        unit = place_basic(legendary, "S01", owner=0)
        legendary._replay_verbose_general_0958 = True
        before = len(legendary.event_journal)
        mark_general_new_ally(legendary, unit)
        self.assertEqual(len(legendary.event_journal), before + 1)
        self.assertIn("obrażenia standardowych ataków ×2",
                      legendary.event_journal[-1]["text"])
        mark_general_new_ally(legendary, unit)
        self.assertEqual(len(legendary.event_journal), before + 1)


class ArchiveBookRegenerationTests(unittest.TestCase):
    def test_stale_signed_battle_summary_is_rebuilt_read_only_with_name_and_bonus(self):
        initial = {
            "players": {"0": {"hp": 100}, "1": {"hp": 100}},
            "units": {
                "G": {"owner": 0, "hp": 8, "current_attack": 2,
                      "current_max_hp": 8, "effects": [], "attacks": 0},
                "S35": {"owner": 0, "hp": 9, "current_attack": 5,
                        "current_max_hp": 9, "effects": [], "attacks": 0},
                "V": {"owner": 1, "hp": 6, "current_attack": 2,
                      "current_max_hp": 6, "effects": [], "attacks": 0},
            },
            "cards": {}, "pending": None, "deferred_attack": None,
            "auction_catalog": "v22",
            "auction_awards": {"G": {"archetype": "A002", "rarity": "rzadka"}},
            "auction_v4": {
                "general_targets": {"G": "S35"},
                "general_grants": {}
            }
        }
        payload = {
            "seed": 95914,
            "initial_state": initial,
            "actions": [{
                "seq": 1, "operation": "attack", "args": ["S35", "V"],
                "result": "ok", "actor_before": 0, "round_before": 4,
                "changes": {}
            }],
            "internal_events": [], "event_journal": []
        }
        fresh = build_combat_analysis(payload, {"S35": "Komendant Straży"})
        old = copy.deepcopy(fresh)
        for battle in old:
            for role in ("attacker", "defender"):
                for period in ("before", "after"):
                    if battle[role][period] is not None:
                        battle[role][period].pop("combat_bonuses", None)
        payload["combat_analysis"] = {"attacks": old}
        signed_before = digest(payload)
        document = render_combat_html(payload)
        self.assertEqual(digest(payload), signed_before)
        self.assertIn("Komendant Straży", document)
        self.assertIn("Generał Oddziału Natarcia (G)", document)
        self.assertIn("obrażenia standardowego ataku ×2", document)
        self.assertNotIn("combat_bonuses", str(old))

    def test_general_damage_badge_is_in_first_two_without_hiding_stun_or_taunt(self):
        def status(category, name):
            return VisibleStatus(category, category, name, name)
        statuses = [
            status("armor", "Pancerz"),
            status("poison", "Trucizna"),
            status("double", "Premia Generała Oddziału Natarcia"),
            status("taunt", "Prowokacja"),
        ]
        ordered = sorted(statuses, key=status_display_priority)
        self.assertEqual([s.name for s in ordered[:2]],
                         ["Prowokacja", "Premia Generała Oddziału Natarcia"])
        stunned = sorted(statuses + [status("stun", "Ogłuszenie")],
                         key=status_display_priority)
        self.assertEqual(stunned[0].name, "Ogłuszenie")


if __name__ == "__main__":
    unittest.main()
