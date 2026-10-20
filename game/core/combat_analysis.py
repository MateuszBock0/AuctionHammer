"""Observational, read-only combat ledger built from a completed MatchAudit.

Never simulates combat or assumes damage. Original signed action diffs,
event journal and traced internal operations remain the only source of truth.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def _participant(state, uid):
    """A compact signed-state view including pre/post HP, ATK, shield and effects."""
    if not isinstance(uid, str):
        return None
    if uid.startswith("hero:"):
        index = uid.partition(":")[2]
        hero = state["players"].get(index)
        if hero is None:
            return None
        return {
            "type": "hero", "owner": int(index), "hp": hero.get("hp"),
            "attack": None, "max_hp": 100,
            "armor": hero.get("hero_armor", 0),
            "shield": hero.get("hero_shield", 0),
            "effects": deepcopy(hero.get("hero_effects", [])),
            "attacks_used": None
        }
    unit = state["units"].get(uid)
    if unit is None:
        return None  # includes dead or removed units; never fake 0 HP
    return {
        "type": "unit", "owner": unit.get("owner"),
        "hp": unit.get("hp"),
        "attack": unit.get("current_attack", unit.get("base_attack")),
        "max_hp": unit.get("current_max_hp", unit.get("base_max_hp")),
        "armor": unit.get("current_armor",
                          unit.get("armor_perm", 0) + unit.get("armor_temp", 0)),
        "shield": unit.get("shield", 0),
        "effects": deepcopy(unit.get("effects", [])),
        "attacks_used": unit.get("attacks"),
        "level": unit.get("ability_level")
    }


def _apply_changes(state, changes):
    """Apply only the recorded sparse delta, not engine rules or inferred moves."""
    for key in ("units", "players", "cards"):
        for uid, entry in changes.get(key, {}).items():
            value = entry["after"]
            if value is None:
                state[key].pop(uid, None)
            else:
                state[key][uid] = value
    for key in ("pending", "deferred_attack"):
        if key in changes:
            state[key] = changes[key]["after"]


def build_combat_analysis(payload, names=None):
    """Return ordered one-record-per-attack ledger.

    For attacks which create a pending ON_ATTACK choice, concatenate the
    subsequent choose command(s) until deferred_attack has resolved.
    Both participants are snapshotted immediately before the first attack and
    after its FULL resolution; nested operations preserve intermediate facts.
    Old 0.9.43 audits work without any additional telemetry.
    """
    names = names or {}
    initial = payload["initial_state"]
    state = {key: deepcopy(initial.get(key, {}))
             for key in ("players", "units", "cards")}
    state["pending"] = deepcopy(initial.get("pending"))
    state["deferred_attack"] = deepcopy(initial.get("deferred_attack"))
    operations = defaultdict(list)
    for entry in payload.get("internal_events", []):
        operations[entry.get("action_seq")].append(entry)
    journal = defaultdict(list)
    for entry in payload.get("event_journal", []):
        if "action_seq" in entry:
            journal[entry["action_seq"]].append(entry)
    battles = []
    open_battle = None
    for action in payload["actions"]:
        operation, seq = action["operation"], action["seq"]
        args = action.get("args") or []
        if (operation == "attack" and action.get("result") == "ok"
                and len(args) >= 2):
            if open_battle is not None:
                open_battle["resolution"] = "interrupted"
            attacker, target = args[:2]
            open_battle = {
                "number": len(battles) + 1, "action_seq": seq,
                "round": action["round_before"],
                "active_player": action["actor_before"],
                "attacker": {
                    "uid": attacker, "name": names.get(attacker, attacker),
                    "before": _participant(state, attacker), "after": None},
                "defender": {
                    "uid": target, "name": names.get(target, target),
                    "before": _participant(state, target), "after": None},
                "actions": [], "steps": [], "events": [],
                "resolution": "completed"
            }
            battles.append(open_battle)
        elif (open_battle is None or operation != "choose"
              or state["deferred_attack"] is None):
            open_battle = None

        if open_battle is not None:
            open_battle["actions"].append(seq)
            for item in operations.get(seq, ()):
                op = item.get("operation")
                step = {
                    "seq": item["seq"], "operation": op,
                    "args": item.get("args", []),
                    "result": item.get("result"),
                    "before": item.get("before", {}),
                    "after": item.get("after", {})
                }
                if op == "_damage":
                    arguments = item.get("args", [])
                    step["target"] = arguments[0] if arguments else None
                    # Requested damage and actual HP impact are DISTINCT.
                    step["damage_requested"] = (
                        arguments[1] if len(arguments) >= 2 else None)
                    step["hp_damage_reported"] = item.get("result")
                open_battle["steps"].append(step)
            open_battle["events"].extend(
                event["text"] for event in journal.get(seq, ()))

        _apply_changes(state, action.get("changes", {}))
        if open_battle is not None:
            for role in ("attacker", "defender"):
                entry = open_battle[role]
                entry["after"] = _participant(state, entry["uid"])
            if state["deferred_attack"] is None:
                open_battle["resolution"] = "completed"
                open_battle = None
            else:
                open_battle["resolution"] = "awaiting_ability_choice"
    if open_battle is not None:
        open_battle["resolution"] = "unresolved"
    return battles
