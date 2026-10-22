"""Observational, read-only combat ledger built from a completed MatchAudit.

Never simulates combat or assumes damage. Original signed action diffs,
event journal and traced internal operations remain the only source of truth.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def _general_sources(state, uid, owner):
    """Resolve A002 grants from the *recorded* state, never by simulation."""
    if state.get("auction_catalog") not in ("v4", "v22"):
        return []
    data = state.get("auction_v4") or {}
    awards = state.get("auction_awards") or {}
    units = state.get("units") or {}
    found = []
    for src, target in (data.get("general_targets") or {}).items():
        leader = units.get(src)
        if (target == uid and leader is not None and
                leader.get("owner") == owner and
                awards.get(src, {}).get("archetype") == "A002" and
                awards[src].get("rarity") == "rzadka" and
                not any(e.get("kind") in ("stun", "silence")
                        for e in leader.get("effects", []))):
            found.append(src)
    for src, recipients in (data.get("general_grants") or {}).items():
        leader = units.get(src)
        if (uid in recipients and leader is not None and
                leader.get("owner") == owner and
                awards.get(src, {}).get("archetype") == "A002" and
                awards[src].get("rarity") == "legendarna" and
                not any(e.get("kind") in ("stun", "silence")
                        for e in leader.get("effects", []))):
            found.append(src)
    return list(dict.fromkeys(found))


def _participant(state, uid, names=None):
    """Compact signed-state view, including separately stored General grants."""
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
        "level": unit.get("ability_level"),
        "combat_bonuses": [
            (names or {}).get(src, "Generał Oddziału Natarcia") +
            " (" + src + "): do 2 ataków w turze, obrażenia standardowego ataku ×2"
            for src in _general_sources(state, uid, unit.get("owner"))
        ]
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
    for key in ("pending", "deferred_attack", "auction_v4",
                "auction_awards", "auction_catalog"):
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
             for key in ("players", "units", "cards", "auction_v4",
                         "auction_awards", "auction_catalog")}
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
                    "before": _participant(state, attacker, names), "after": None},
                "defender": {
                    "uid": target, "name": names.get(target, target),
                    "before": _participant(state, target, names), "after": None},
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
                entry["after"] = _participant(state, entry["uid"], names)
            if state["deferred_attack"] is None:
                open_battle["resolution"] = "completed"
                open_battle = None
            else:
                open_battle["resolution"] = "awaiting_ability_choice"
    if open_battle is not None:
        open_battle["resolution"] = "unresolved"
    return battles
