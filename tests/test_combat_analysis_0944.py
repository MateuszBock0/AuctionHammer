"""0.9.44: authoritative per-attack forensic ledger, not speculative combat."""
import copy
import json
import unittest

from game.core.combat_analysis import build_combat_analysis
from game.core.audit import digest, make_report, read_report
from game.core.engine import Match


class CombatAnalysisTests(unittest.TestCase):
    def _snapshot(self):
        return {
            "players":{
                "0":{"hp":100,"hero_armor":0,"hero_shield":0,"hero_effects":[]},
                "1":{"hp":100,"hero_armor":0,"hero_shield":0,"hero_effects":[]}
            },
            "units":{
                "A":{"owner":0,"hp":5,"current_attack":4,"current_max_hp":5,
                     "current_armor":0,"shield":0,"effects":[],"attacks":0},
                "B":{"owner":1,"hp":8,"current_attack":2,"current_max_hp":8,
                     "current_armor":4,"shield":0,"effects":[],"attacks":0}
            },
            "cards":{},"pending":None,"deferred_attack":None
        }

    def test_armor_and_death_keep_exact_before_and_after_no_fake_hp(self):
        original=self._snapshot()
        attacker_before=copy.deepcopy(original["units"]["A"])
        attacker_after=copy.deepcopy(attacker_before,attacks=1)
        defender_before=copy.deepcopy(original["units"]["B"])
        defender_after=copy.deepcopy(defender_before,current_armor=0)
        first={
            "seq":1,"operation":"attack","args":["B","A"],"result":"ok",
            "actor_before":1,"round_before":3,
            "changes":{"units":{
                "A":{"before":attacker_before,"after":attacker_after},
                "B":{"before":defender_before,"after":defender_after}
            }}
        }
        second={
            "seq":2,"operation":"attack","args":["A","B"],"result":"ok",
            "actor_before":0,"round_before":3,
            "changes":{"units":{"B":{"before":defender_after,"after":None}}}
        }
        payload={
            "initial_state":original,"actions":[first,second],
            "internal_events":[
                {"seq":1,"action_seq":1,"operation":"_damage",
                 "args":["B",4],"before":{"B":{"hp":8,"armor":4}},
                 "after":{"B":{"hp":8,"armor":0}},"result":0},
                {"seq":2,"action_seq":2,"operation":"_damage",
                 "args":["B",8],"before":{"B":{"hp":8,"armor":0}},
                 "after":{"B":None},"result":8}
            ],"event_journal":[
                {"action_seq":1,"text":"Zablokowano pancerzem"},
                {"action_seq":2,"text":"B został pokonany"}
            ]
        }
        frozen=digest(payload)
        attacks=build_combat_analysis(payload,{"A":"Łucznik","B":"Rycerz"})
        self.assertEqual(digest(payload),frozen,"Read-only report mutated original audit")
        self.assertEqual(len(attacks),2)
        self.assertEqual(attacks[0]["attacker"]["name"],"Rycerz")
        self.assertEqual(attacks[0]["attacker"]["before"]["armor"],4)
        self.assertEqual(attacks[0]["attacker"]["after"]["armor"],0)
        self.assertEqual(attacks[0]["steps"][0]["damage_requested"],4)
        self.assertEqual(attacks[0]["steps"][0]["hp_damage_reported"],0)
        self.assertIsNone(attacks[1]["defender"]["after"])
        self.assertEqual(attacks[1]["resolution"],"completed")

    def test_deferred_choice_included_in_same_attack_and_statuses_retained(self):
        initial=self._snapshot()
        weakened=copy.deepcopy(initial["units"]["B"])
        weakened["hp"]=5
        weakened["effects"]=[{"kind":"atk","value":-1,"remaining":0,
                              "source":"A","positive":False}]
        pending={"context":"attack","uid":"A"}
        attack={
            "seq":1,"operation":"attack","args":["A","B"],"result":"ok",
            "actor_before":0,"round_before":3,
            "changes":{
                "deferred_attack":{"before":None,"after":["A","B"]},
                "pending":{"before":None,"after":pending}}
        }
        choose={
            "seq":2,"operation":"choose","args":[1],"result":"ok",
            "actor_before":0,"round_before":3,
            "changes":{
                "units":{"B":{"before":initial["units"]["B"],"after":weakened}},
                "deferred_attack":{"before":["A","B"],"after":None},
                "pending":{"before":pending,"after":None}
            }
        }
        payload={"initial_state":initial,"actions":[attack,choose],
                 "internal_events":[{"seq":1,"action_seq":2,
                                    "operation":"_add_effect","args":["B","atk",-1],
                                    "before":{"B":{"effects":[]}},
                                    "after":{"B":{"effects":weakened["effects"]}}}],
                 "event_journal":[{"action_seq":2,"text":"Osłabiono cel"}]}
        item=build_combat_analysis(payload)[0]
        self.assertEqual(item["actions"],[1,2])
        self.assertEqual(item["resolution"],"completed")
        self.assertEqual(item["defender"]["before"]["effects"],[])
        self.assertEqual(item["defender"]["after"]["effects"][0]["kind"],"atk")
        self.assertEqual(item["defender"]["after"]["hp"],5)
        self.assertEqual(item["events"],["Osłabiono cel"])

    def test_attacking_hero_uses_hero_hp_shield_and_armor(self):
        initial=self._snapshot()
        initial["players"]["1"]["hero_shield"]=1
        action={
            "seq":1,"operation":"attack","args":["A","hero:1"],"result":"ok",
            "actor_before":0,"round_before":2,
            "changes":{"players":{"1":{
                "before":copy.deepcopy(initial["players"]["1"]),
                "after":dict(initial["players"]["1"],hero_shield=0)
            }}}
        }
        item=build_combat_analysis({"initial_state":initial,"actions":[action],
                                    "internal_events":[],"event_journal":[]})[0]
        self.assertEqual(item["defender"]["before"]["hp"],100)
        self.assertEqual(item["defender"]["before"]["shield"],1)
        self.assertEqual(item["defender"]["after"]["shield"],0)
        self.assertIsNone(item["defender"]["after"]["attack"])

    def test_new_export_contains_signed_combat_ledger_without_changing_game(self):
        match=Match(944,audit_enabled=True)
        match.phase="finished";match.winner=0
        before=digest({"players":[p.hp for p in match.players],"rng":repr(match.rng.getstate())})
        output=make_report(match)
        payload=output["payload"]
        self.assertEqual(digest(payload),output["sha256"])
        self.assertIn("combat_analysis",payload)
        self.assertEqual(payload["summary"]["combat_attacks"],0)
        self.assertEqual(digest({"players":[p.hp for p in match.players],"rng":repr(match.rng.getstate())}),before)


if __name__=="__main__":
    unittest.main()
