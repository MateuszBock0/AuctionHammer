"""Complete, deterministic v19 match audit (not the 480-frame UI replay).

All recording is observational. For every attempted public engine command the
report keeps the command, its outcome, event range, authoritative state delta
and SHA-256 state hashes. Exactly one *completed* match is exported as JSON.
No hidden state is exposed in the live UI before the match has finished.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from dataclasses import fields, is_dataclass
from functools import wraps
from hashlib import sha256
from pathlib import Path
import json
import os

FORMAT="AuctionHammer.MatchAudit"
SCHEMA=1
FILENAME="AuctionHammer-OSTATNI-MECZ.json"
ACTIONS=("mulligan_toggle","finish_mulligan","play","attack","end_turn","choose",
         "auction_bid","auction_pass","auction_pick")


def audit_path() -> Path:
    """Outside the auto-update folder; stable across portable EXE upgrades."""
    root=os.getenv("LOCALAPPDATA")
    home=Path(root) if root else Path.home()/".local"/"share"
    return home/"AuctionHammer"/FILENAME


def configure_audit_context(game, difficulty, build=None, fresh=False):
    """Keep AI settings and build identity alongside, not inside, game state.

    An older imported save has unknown ORIGINAL code revision: stamping it with
    today's checkout would incorrectly claim reproducibility.
    """
    from .build_info import build_identity
    metadata=getattr(game,"audit_metadata",None)
    if not isinstance(metadata,dict):
        metadata={
            "ai_difficulty_initial":difficulty if fresh else None,
            "ai_difficulty_current":difficulty,
            "ai_difficulty_history":[],
            "build":(build or build_identity()) if fresh
                    else {"commit":None,"source":"legacy-save","version":"unknown"}
        }
        game.audit_metadata=metadata
    return metadata


def record_ai_difficulty(game, difficulty):
    metadata=configure_audit_context(game,difficulty,fresh=False)
    previous=metadata["ai_difficulty_current"]
    if previous==difficulty:
        return
    metadata["ai_difficulty_history"].append({
        "after_action_seq":len(getattr(game,"audit_actions",[])),
        "round":game.round,
        "from":previous,
        "to":difficulty
    })
    metadata["ai_difficulty_current"]=difficulty


def _plain(value):
    """Deterministic, JSON-only representation; never imports executable code."""
    if value is None or isinstance(value,(str,int,float,bool)):
        return value
    if is_dataclass(value):
        return {f.name:_plain(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,(tuple,list,deque)):
        return [_plain(item) for item in value]
    if isinstance(value,(set,frozenset)):
        return sorted((_plain(item) for item in value),
                      key=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True))
    if isinstance(value,dict):
        return {str(key):_plain(item) for key,item in sorted(
            value.items(),key=lambda pair:str(pair[0]))}
    raise TypeError(f"Unsupported audit value: {type(value).__name__}")


def _canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False)


def digest(value):
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def state_snapshot(game):
    """Detailed snapshot, including hidden hands/decks for post-game audit."""
    return {
        "round":game.round,
        "action_turn":game.action_turn,
        "active":game.active,
        "first":game.first,
        "phase":game.phase,
        "winner":game.winner,
        "serial":game.serial,
        "rng_draw_index":game.rng_draw_index,
        "rng_state_hash":sha256(repr(game.rng.getstate()).encode()).hexdigest(),
        "players":{str(p.idx):_plain(p) for p in game.players},
        "cards":{
            uid:{
                "owner":card.owner,
                "zone":card.zone,
                "hand_turns":card.hand_turns,
                "ability_level":card.ability_level,
                "attack":card.attack,
                "max_hp":card.max_hp,
                "quick_next_turn":card.quick_next_turn,
                "quick_on_first_summon":card.quick_on_first_summon,
                "double_on_first_eligible":card.double_on_first_eligible
            } for uid,card in sorted(game.cards.items())
        },
        "units":{
            uid:dict(_plain(unit),**{
                "current_attack":unit.atk,"current_max_hp":unit.max_hp,
                "current_armor":unit.armor})
            for uid,unit in sorted(game.units.items())
        },
        "bank":list(game.bank),
        "excluded":list(game.excluded),
        "mulligan_done":_plain(game.mulligan_done),
        "mulligan_requests":_plain(game.mulligan_requests),
        "pending":_plain(game.pending),
        "trigger_queue":_plain(game.trigger_queue),
        "death_waves":_plain(game.death_waves),
        "active_death_wave":_plain(game.active_death_wave),
        "deferred_attack":_plain(game.deferred_attack),
        "end_queue":_plain(game.end_queue),
        "flags":{
            "_draining":game._draining,
            "_resolving_death_wave":game._resolving_death_wave,
            "_next_death_wave_id":game._next_death_wave_id,
            "_next_turn_due":game._next_turn_due,
            "position_reactions_due":game.position_reactions_due,
            "_suspend_hero_thresholds":game._suspend_hero_thresholds
        },
        "wave_accumulators":{
            "damage":_plain(game._wave_damage),
            "healing":_plain(game._wave_healing),
            "statuses":_plain(game._wave_status_ops),
            "defenses":_plain(game._wave_defense_ops)
        },
        "death_disabled":_plain(game._death_disabled),
        "death_levels":_plain(game._death_levels),
        "auctions_enabled":getattr(game,"auctions_enabled",False),
        "auction":_plain(getattr(game,"auction",None)),
        "auction_history":_plain(getattr(game,"auction_history",[])),
        "auction_awards":_plain(getattr(game,"auction_awards",{})),
        "auction_catalog_mode":getattr(game,"auction_catalog_mode","placeholders"),
        "ephemerals":_plain(getattr(game,"ephemerals",set())),
        "auction_copy_serial":getattr(game,"auction_copy_serial",0),
        "auction_death_links":_plain(getattr(game,"auction_death_links",set())),
        "auction_chain":_plain(getattr(game,"auction_chain",None))
    }


def _changes(before,after):
    """Sparse diffs per card/unit/hero; no 70-card copy on every move."""
    changes={}
    for key in before:
        old,new=before[key],after[key]
        if old==new:
            continue
        if key in ("players","cards","units","flags","wave_accumulators") and isinstance(old,dict) and isinstance(new,dict):
            item_diff={}
            for uid in sorted(old.keys() | new.keys()):
                prev=old.get(uid)
                curr=new.get(uid)
                if prev!=curr:
                    item_diff[uid]={"before":prev,"after":curr}
            changes[key]=item_diff
        else:
            changes[key]={"before":old,"after":new}
    return changes


def initialize_audit(game, complete=True):
    game.audit_initial=state_snapshot(game)
    game.audit_actions=[]
    game.audit_internal=[]
    game._audit_open_action=None
    game._audit_open_internal=None
    game.audit_complete=bool(complete)
    game.audit_first_event=len(game.event_journal)


def _targets(game,args):
    """Inspect only directly referenced heroes/units during one micro-effect."""
    ids=set()
    def collect(item):
        if isinstance(item,str) and (item in game.cards or
                                      item.startswith("hero:")):
            ids.add(item)
        elif isinstance(item,(tuple,list,set,frozenset)):
            for value in item:
                collect(value)
    for value in args:
        collect(value)
    result={}
    for uid in sorted(ids):
        if uid.startswith("hero:"):
            try:
                p=game.players[int(uid.split(":")[1])]
            except (IndexError,ValueError):
                continue
            result[uid]={"hp":p.hp,"armor":p.hero_armor,
                         "shield":p.hero_shield,"effects":_plain(p.hero_effects)}
        elif uid in game.units:
            u=game.units[uid]
            result[uid]={"hp":u.hp,"atk":u.atk,"max_hp":u.max_hp,
                         "shield":u.shield,"armor":u.armor,
                         "effects":_plain(u.effects)}
        else:
            result[uid]=None
    return result


def trace_effect(kind):
    """Exact nested engine operation order, without altering resolution rules."""
    def decorate(method):
        @wraps(method)
        def traced(game,*args,**kwargs):
            if not getattr(game,"audit_enabled",False):
                return method(game,*args,**kwargs)
            if not hasattr(game,"audit_internal"):
                initialize_audit(game,complete=False)
            record={
                "seq":len(game.audit_internal)+1,
                "action_seq":getattr(game,"_audit_open_action",None),
                "operation":kind,
                "args":_plain(args),
                "kwargs":_plain(kwargs),
                "before":_targets(game,args),
                "round":game.round,
                "action_turn":game.action_turn,
                "result":None,
                "error":None,
                "after":None
            }
            game.audit_internal.append(record)
            previous=getattr(game,"_audit_open_internal",None)
            game._audit_open_internal=record["seq"]
            try:
                outcome=method(game,*args,**kwargs)
                record["result"]=_plain(outcome)
                return outcome
            except Exception as exc:
                record["error"]={"type":type(exc).__name__,"message":str(exc)}
                raise
            finally:
                record["after"]=_targets(game,args)
                game._audit_open_internal=previous
        return traced
    return decorate


def audit_action(operation):
    """Decorator for external Match commands; catches failed attempts as well."""
    if operation not in ACTIONS:
        raise ValueError(operation)

    def decorated(method):
        @wraps(method)
        def audited(game,*args,**kwargs):
            if not hasattr(game,"audit_actions"):
                # A legacy save may pre-date audit support; never claim the
                # reconstructed history is complete.
                initialize_audit(game,complete=False)
            before=state_snapshot(game)
            choice_owner=(game.pending.owner if game.pending else None)
            if operation=="finish_mulligan":
                command_owner=(args[0] if args else kwargs.get("player_idx",0))
            elif operation=="mulligan_toggle":
                command_owner=0
            elif operation=="choose":
                command_owner=choice_owner
            else:
                command_owner=game.active
            start_event=len(game.event_journal)
            start_internal=len(game.audit_internal)
            old_open=getattr(game,"_audit_open_action",None)
            game._audit_open_action=len(game.audit_actions)+1
            error=None
            selected=None
            if operation=="choose" and game.pending and args:
                index=args[0]
                if isinstance(index,int) and 0<=index<len(game.pending.choices):
                    selected=_plain(game.pending.choices[index])
            try:
                result=method(game,*args,**kwargs)
            except Exception as exc:
                error={"type":type(exc).__name__,"message":str(exc)}
                raise
            finally:
                after=state_snapshot(game)
                game._audit_open_action=old_open
                seq=len(game.audit_actions)+1
                record={
                    "seq":seq,
                    "operation":operation,
                    "args":_plain(args),
                    "kwargs":_plain(kwargs),
                    "actor_before":before["active"],
                    "command_owner":command_owner,
                    "ai_difficulty":getattr(game,"audit_metadata",{}).get("ai_difficulty_current"),
                    "round_before":before["round"],
                    "round_after":after["round"],
                    "phase_before":before["phase"],
                    "phase_after":after["phase"],
                    "selected_choice":selected,
                    "result":"ok" if error is None else "error",
                    "error":error,
                    "event_seq_start":start_event+1,
                    "event_seq_end":len(game.event_journal),
                    "internal_seq_start":start_internal+1,
                    "internal_seq_end":len(game.audit_internal),
                    "before_sha256":digest(before),
                    "after_sha256":digest(after),
                    "changes":_changes(before,after)
                }
                game.audit_actions.append(record)
            return result
        return audited
    return decorated


def make_report(game):
    if game.phase!="finished":
        raise ValueError("Audyt można udostępnić dopiero po zakończeniu meczu")
    if not hasattr(game,"audit_actions"):
        initialize_audit(game,complete=False)
    initial=game.audit_initial
    final=state_snapshot(game)
    payload={
        "format":FORMAT,
        "schema":SCHEMA,
        "specification":"GAME_MASTER_v19",
        "version":"0.9.18",
        "exported_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed":game.seed,
        "first_player":game.first,
        "environment":getattr(game,"audit_metadata",{
            "ai_difficulty_initial":None,
            "ai_difficulty_current":None,
            "ai_difficulty_history":[],
            "build":{"commit":None,"source":"unknown","version":"unknown"}
        }),
        "complete_from_start":bool(game.audit_complete),
        "note":"Historia niepełna: mecz wczytano z zapisu starszej wersji" if not game.audit_complete else "",
        "initial_state":initial,
        "actions":game.audit_actions,
        "internal_events":game.audit_internal,
        "event_journal":list(game.event_journal),
        "final_state":final,
        "summary":{
            "winner":game.winner,
            "rounds":game.round,
            "action_commands":len(game.audit_actions),
            "internal_operations":len(game.audit_internal),
            "events":len(game.event_journal),
            "failed_commands":sum(a["result"]=="error" for a in game.audit_actions),
            "hero_hp":{str(p.idx):p.hp for p in game.players}
        }
    }
    return {"payload":payload,"sha256":digest(payload)}


def write_last_match(game,path=None):
    """Atomically replace the single exported *completed* match."""
    report=make_report(game)
    dest=Path(path) if path is not None else audit_path()
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_name(dest.name+".tmp")
    try:
        temp.write_text(json.dumps(report,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n",encoding="utf-8")
        os.replace(temp,dest)
    finally:
        if temp.exists():
            temp.unlink()
    return dest


def read_report(path):
    path=Path(path)
    if path.stat().st_size>30_000_000:
        raise ValueError("Plik audytu przekracza limit 30 MB")
    document=json.loads(path.read_text(encoding="utf-8"))
    payload=document.get("payload")
    if not isinstance(payload,dict) or payload.get("format")!=FORMAT or payload.get("schema")!=SCHEMA:
        raise ValueError("Niezgodny format audytu")
    if document.get("sha256")!=digest(payload):
        raise ValueError("Audyt jest uszkodzony lub zmodyfikowany")
    return payload


def verify_replay(payload,match_factory):
    """Re-run recorded commands on v19 engine, comparing state/event hashes.

    This is independent of pygame and suitable for reviewing an uploaded JSON.
    """
    if not payload.get("complete_from_start"):
        raise ValueError("Niepełny audyt: brak początku rozgrywki")
    auction_enabled=bool(payload.get("initial_state",{}).get("auctions_enabled",False))
    catalog_mode=payload.get("initial_state",{}).get("auction_catalog_mode","placeholders")
    if auction_enabled:
        try:
            game=match_factory(payload["seed"],auctions_enabled=True,
                               auction_catalog_mode=catalog_mode)
        except TypeError as exc:
            raise ValueError("Odtwarzanie aukcji wymaga fabryki z auctions_enabled") from exc
    else:
        game=match_factory(payload["seed"])
    if digest(state_snapshot(game)) != digest(payload["initial_state"]):
        raise ValueError("Początkowy stan nie odpowiada wskazanemu seed")
    for record in payload["actions"]:
        name=record["operation"]
        if name not in ACTIONS:
            raise ValueError(f"Nieznana komenda: {name}")
        if digest(state_snapshot(game))!=record["before_sha256"]:
            raise ValueError(f"Niezgodny stan przed akcją {record['seq']}")
        caught=None
        try:
            getattr(game,name)(*record["args"],**record["kwargs"])
        except Exception as exc:
            caught={"type":type(exc).__name__,"message":str(exc)}
        if caught != record["error"]:
            raise ValueError(f"Niezgodny wynik akcji {record['seq']}")
        if digest(state_snapshot(game))!=record["after_sha256"]:
            raise ValueError(f"Niezgodny stan po akcji {record['seq']}")
    if game.event_journal!=payload["event_journal"]:
        raise ValueError("Niezgodny dziennik zdarzeń silnika")
    if game.audit_internal!=payload["internal_events"]:
        raise ValueError("Niezgodna wewnętrzna kolejność efektów")
    if digest(state_snapshot(game))!=digest(payload["final_state"]):
        raise ValueError("Niezgodny stan końcowy")
    return True
