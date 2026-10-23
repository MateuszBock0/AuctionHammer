"""0.9.63 — starter Chorazy 2/1+4 armor and archived 0.9.62 preservation."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from game.core.engine import Match
from game.core.audit import digest, initialize_audit, state_snapshot, verify_replay
from game.core.persistence import save_match,load_match
from game.ui.card_summary import ability_summary
from game.ui.card_infographics import card_cue
from test_chorazy_kills_0962 import GUARD, fresh, strike_victim, signed_trace, replay_factory


class ArmoredStarter0963(unittest.TestCase):
    def test_starter_has_one_hp_four_permanent_armor_and_correct_copy(self):
        g=Match(96301,auctions_enabled=True,auction_catalog="v22",
                starting_compensation="choice_2_5_or_coins")
        self.assertTrue(g.starter_guard_armor_rule)
        owner=1-g.first
        g.choose_starting_compensation(owner,"unit_2_5")
        u=g.units[GUARD]
        card=g.cards[GUARD]
        self.assertEqual((u.atk,u.hp,u.max_hp,u.armor_perm,u.armor),(2,1,1,4,4))
        self.assertEqual(u.armor_perm_grants,{GUARD:4})
        self.assertIn("4 trwałego pancerza",card.definition.effect)
        self.assertIn("zabójstwo",card.definition.effect)
        summary=ability_summary(card,u)
        cue=card_cue(card,u)
        self.assertNotIn("BEZ ZDOLNOŚCI",summary.short)
        self.assertIn("ZABÓJSTWA",summary.short)
        self.assertIn("MAX",summary.full)
        self.assertEqual(cue.family,"ZABÓJSTWA")
        self.assertIn("ZABÓJSTWA",cue.upgrade)
        self.assertIn("2/1 z 4 pancerza",g.event_journal[-1]["text"])
        g.assert_integrity()

    def test_armor_absorbs_damage_but_kills_never_restore_spent_armor(self):
        g=fresh(96302)
        self.assertEqual(g.units[GUARD].armor,4)
        self.assertEqual(g._damage(GUARD,3),0)
        self.assertEqual((g.units[GUARD].hp,g.units[GUARD].armor),(1,1))
        self.assertEqual(g._damage(GUARD,1),0)
        self.assertEqual((g.units[GUARD].hp,g.units[GUARD].armor),(1,0))
        strike_victim(g,"S01",hp=1,atk=0)
        u=g.units[GUARD]
        self.assertEqual((u.atk,u.hp,u.max_hp,u.armor),(3,3,3,0))
        strike_victim(g,"S02",hp=1,atk=0)
        strike_victim(g,"S03",hp=1,atk=0)
        strike_victim(g,"S04",hp=1,atk=0)
        u=g.units[GUARD]
        self.assertEqual((u.atk,u.hp,u.max_hp,u.armor),(5,7,7,0))
        self.assertEqual(g.starter_guard_kills,3)
        g.assert_integrity()

    def test_summon_old_0962_2_5_is_unchanged_and_can_replay(self):
        g=Match(96303,audit_enabled=True,auctions_enabled=True,
                auction_catalog="v22",starting_compensation="choice_2_5_or_coins")
        g.starter_guard_armor_rule=False
        old="Drugi gracz wybierze Chorążego 2/5 lub +3 monety."
        new="Drugi gracz wybierze Chorążego 2/1 z 4 pancerza lub +3 monety."
        for e in g.event_journal:e["text"]=e["text"].replace(new,old)
        g.events=[e.replace(new,old) for e in g.events]
        initialize_audit(g)
        g.choose_starting_compensation(1-g.first,"unit_2_5")
        u=g.units[GUARD]
        self.assertEqual((u.atk,u.hp,u.max_hp,u.armor),(2,5,5,0))
        self.assertTrue(g.starter_guard_kill_rule)
        self.assertNotIn("starter_guard_armor_rule",
                         state_snapshot(g)["ruleset_state"])
        payload=signed_trace(g)
        original_hash=digest(payload)
        self.assertTrue(verify_replay(payload,replay_factory))
        self.assertEqual(original_hash,digest(payload))

    def test_new_signed_rule_replays_and_save_preserves_armor(self):
        g=Match(96304,audit_enabled=True,auctions_enabled=True,
                auction_catalog="v22",starting_compensation="choice_2_5_or_coins")
        rules=g.audit_initial["ruleset_state"]
        self.assertTrue(rules["starter_guard_armor_rule"])
        g.choose_starting_compensation(1-g.first,"unit_2_5")
        payload=signed_trace(g)
        self.assertTrue(verify_replay(payload,replay_factory))
        before=digest(state_snapshot(g))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"save.json"
            save_match(g,path)
            loaded=load_match(path)
        self.assertTrue(loaded.starter_guard_armor_rule)
        self.assertEqual((loaded.units[GUARD].hp,loaded.units[GUARD].armor),(1,4))
        self.assertEqual(before,digest(state_snapshot(loaded)))

    def test_legacy_save_missing_new_rule_still_loads_at_old_values(self):
        g=Match(96305,auctions_enabled=True,auction_catalog="v22",
                starting_compensation="choice_2_5_or_coins")
        g.starter_guard_armor_rule=False
        g.choose_starting_compensation(1-g.first,"unit_2_5")
        delattr(g,"starter_guard_armor_rule")
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"oldsave.json"
            save_match(g,path)
            loaded=load_match(path)
        self.assertFalse(loaded.starter_guard_armor_rule)
        self.assertEqual((loaded.units[GUARD].hp,loaded.units[GUARD].armor),(5,0))

    def test_historical_3_5_guard_still_has_no_armor_or_kill_bonus(self):
        g=fresh(96306,mode="unit_3_5")
        u=g.units[GUARD]
        self.assertEqual((u.atk,u.hp,u.armor),(3,5,0))
        self.assertFalse(g.starter_guard_armor_rule)
        self.assertFalse(g.starter_guard_kill_rule)
        self.assertEqual(card_cue(g.cards[GUARD],u).base,"BEZ ZDOLNOŚCI")


if __name__=="__main__":
    unittest.main()
