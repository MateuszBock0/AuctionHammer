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
import gzip

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
    state={
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
        "auction_catalog":getattr(game,"auction_catalog","placeholders"),
        "auction":_plain(getattr(game,"auction",None)),
        "auction_history":_plain(getattr(game,"auction_history",[])),
        "auction_awards":_plain(getattr(game,"auction_awards",{}))
    }
    # Legacy v3 snapshots retain byte-identical fields for old replay files.
    if getattr(game,'auction_catalog',None) in ('v4','v22'):
        state['auction_v4']={
            'bag':_plain(game.auction_bag),
            'unsold_offers_history':_plain(game.auction_discarded),
            'unsold_archetypes_return_to_bag':True,
            'supply_policy_version':getattr(game,'auction_supply_version',1),
            'purchased_spent':_plain(game.auction_used),
            'exiled':_plain(game.exiled),
            'vanished':_plain(game.vanished),
            'ephemeral_ids':_plain(game.ephemeral_ids),
            'death_grants':_plain(game.auction_death_grants),
            'rescue_spent':_plain(game.auction_rescue_spent),
            'general_targets':_plain(game.auction_general_targets),
            'general_grants':_plain(game.auction_general_grants),
            'pending_targets':_plain(game.auction_pending_targets),
            'wave_ops':_plain(game.auction_wave_ops)
        }
    if getattr(game,'auction_catalog',None)=='v22':
        state['auction_v22']={
            'catalog_size':17,
            'vouchers':_plain(game.auction_vouchers),
            'blocked_play_wardens':_plain(game.auction_blocked_play),
        }
    # Starting with audit-schema 2, the rules that affect future actions
    # and the deferred end-turn payment are part of the signed state, not
    # merely report metadata. Older v22/v23 archives retain their ORIGINAL
    # hashes because their replay explicitly selects schema 1.
    if (getattr(game,'audit_state_schema',1)>=2
            and getattr(game,'ruleset_version',None)=='v23'):
        schema=getattr(game,'audit_state_schema',2)
        state['ruleset_state']={
            'audit_schema':schema,
            'version':'v23',
            'pending_vacant_income':getattr(game,'pending_vacant_income',None),
            'vacant_income_enabled':getattr(game,'vacant_income_enabled',False),
        }
        if schema>=3:
            state['ruleset_state']['starting_compensation']=getattr(
                game,'starting_compensation','coins')
    return state


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
        "version":"0.9.38" if game.auction_catalog=="v22" else "0.9.30" if game.auction_catalog=="v4" else "0.9.21",
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
            "vacant_slot_income_enabled":bool(getattr(game,'vacant_income_enabled',False)),
            "ruleset_version":getattr(game,'ruleset_version','v22'),
            "vacant_slot_income_total":list(getattr(game,'slot_income',[0,0])),
            # Keep exact (possibly negative) engine HP for scientific replay,
            # and a separate nonnegative number for presentation in viewers.
            "hero_hp":{str(p.idx):p.hp for p in game.players},
            "hero_hp_display":{str(p.idx):max(0,p.hp) for p in game.players},
            "unit_deaths":{str(p.idx):game.death_counts[p.idx]
                           for p in game.players}
            if (getattr(game,'death_counts',None) is not None and
                getattr(game,'death_counts_complete',False)) else None
        }
    }
    return {"payload":payload,"sha256":digest(payload)}


ARCHIVE_FORMAT="AuctionHammer.MatchArchiveIndex"
ARCHIVE_DIRECTORY="historia_meczow"


def archive_path(last_match_path=None):
    """Persistent data folder shared by the portable game and future builds."""
    last=Path(last_match_path) if last_match_path is not None else audit_path()
    return last.parent/ARCHIVE_DIRECTORY


def _atomic_write(destination,contents):
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+".tmp")
    try:
        temporary.write_bytes(contents)
        os.replace(temporary,destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _archive_document(document,last_match_path):
    """Store an entire verified audit once, including a compact searchable index."""
    payload=document.get("payload")
    if (not isinstance(payload,dict) or payload.get("format")!=FORMAT
            or payload.get("schema")!=SCHEMA or
            document.get("sha256")!=digest(payload)):
        raise ValueError("Niezgodny lub uszkodzony audyt do archiwizacji")
    match_id=digest({
        "seed":payload.get("seed"),
        "initial_state":payload.get("initial_state"),
        "actions":payload.get("actions"),
        "final_state":payload.get("final_state"),
    })
    folder=archive_path(last_match_path)
    filename=f"mecz_{match_id[:24]}.json.gz"
    target=folder/filename
    # Stable content-based filename avoids duplicates after app restart or
    # repeated exports on a different calendar day.
    if not target.exists():
        packed=json.dumps(document,ensure_ascii=False,
                          separators=(",",":"),allow_nan=False).encode("utf-8")
        _atomic_write(target,gzip.compress(packed,compresslevel=9,mtime=0))
    index_path=folder/"indeks.json"
    if index_path.exists():
        index=json.loads(index_path.read_text(encoding="utf-8"))
        if (index.get("format")!=ARCHIVE_FORMAT
                or index.get("schema")!=1 or not isinstance(index.get("matches"),list)):
            raise ValueError("Nieprawidłowy indeks historii; archiwum zachowane")
    else:
        index={"format":ARCHIVE_FORMAT,"schema":1,"matches":[]}
    if not any(item.get("id")==match_id for item in index["matches"]):
        summary=payload.get("summary",{})
        index["matches"].append({
            "id":match_id,
            "file":filename,
            "exported_at_utc":payload.get("exported_at_utc"),
            "version":payload.get("version"),
            "winner":summary.get("winner"),
            "rounds":summary.get("rounds"),
            "events":summary.get("events"),
            "action_commands":summary.get("action_commands"),
            "complete_from_start":payload.get("complete_from_start",False),
        })
        index["matches"].sort(key=lambda item:item.get("exported_at_utc") or "",
                              reverse=True)
        _atomic_write(index_path,(json.dumps(index,ensure_ascii=False,
                                             indent=2)+"\n").encode("utf-8"))
    return target


def list_archived_matches(folder=None):
    """Read the lightweight history index; do not load complete battle ledgers."""
    directory=Path(folder) if folder is not None else archive_path()
    path=directory/"indeks.json"
    if not path.exists():
        return []
    data=json.loads(path.read_text(encoding="utf-8"))
    if (data.get("format")!=ARCHIVE_FORMAT or data.get("schema")!=1
            or not isinstance(data.get("matches"),list)):
        raise ValueError("Nieprawidłowy indeks historii")
    return sorted(data["matches"],key=lambda item:item.get("exported_at_utc") or "",
                  reverse=True)


def write_last_match(game,path=None):
    """Persist the latest readable JSON and preserve ALL completed matches."""
    report=make_report(game)
    dest=Path(path) if path is not None else audit_path()
    # Upgrade path: preserve the pre-0.9.33 last match before overwriting it.
    if dest.is_file():
        old_document=json.loads(dest.read_text(encoding="utf-8"))
        _archive_document(old_document,dest)
    _archive_document(report,dest)
    _atomic_write(dest,(json.dumps(report,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n").encode("utf-8"))
    return dest


def read_report(path):
    path=Path(path)
    if path.stat().st_size>30_000_000:
        raise ValueError("Plik audytu przekracza limit 30 MB")
    if path.suffix==".gz":
        with gzip.open(path,"rb") as stream:
            data=stream.read(30_000_001)
        if len(data)>30_000_000:
            raise ValueError("Rozpakowany audyt przekracza limit 30 MB")
        document=json.loads(data.decode("utf-8"))
    else:
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
    initial=payload.get("initial_state",{})
    auction_enabled=bool(initial.get("auctions_enabled",False))
    catalog=initial.get("auction_catalog","placeholders")
    signed_rule=initial.get('ruleset_state')
    compensation=('unit_5_5' if isinstance(signed_rule,dict)
                  and signed_rule.get('audit_schema')==3
                  and signed_rule.get('starting_compensation')=='unit_5_5'
                  else 'coins')
    if auction_enabled:
        try:
            kwargs={'auctions_enabled':True,'auction_catalog':catalog}
            if compensation=='unit_5_5':
                kwargs['starting_compensation']=compensation
            game=match_factory(payload["seed"],**kwargs)
        except TypeError as exc:
            raise ValueError("Odtwarzanie aukcji wymaga fabryki z trybem katalogu") from exc
    else:
        game=match_factory(payload["seed"])
    # v0.9.34 introduced optional vacant-slot income for NEW v22 matches.
    # A pre-0.9.34 archived match (or a resumed old save) used the old
    # economy. Infer it from signed audit metadata, not today's defaults.
    # This does not emulate old ability logic; it prevents a spurious
    # mismatch caused ONLY by the newer starting economy.
    if auction_enabled and catalog=='v22':
        summary=payload.get('summary',{})
        if 'vacant_slot_income_enabled' in summary:
            enabled=summary['vacant_slot_income_enabled']
        elif payload.get('version') in ('0.9.31','0.9.32','0.9.33'):
            enabled=False  # Archive predates the new 0.9.34 economy.
        else:
            # A deliberately minimal in-memory replay payload need not
            # include report metadata. Preserve the factory's actual rules.
            enabled=getattr(game,'vacant_income_enabled',False)
        if type(enabled) is not bool:
            raise ValueError("Niezgodna flaga dochodu za wolne pola w audycie")
        if not hasattr(game,'vacant_income_enabled'):
            if enabled:
                raise ValueError("Silnik odtwarzania nie obsługuje dochodu za wolne pola")
        else:
            game.vacant_income_enabled=enabled
    if auction_enabled and catalog=='v22':
        report_rules=payload.get('summary',{}).get('ruleset_version')
        if report_rules is None:
            # Old signed archives predate the explicit ruleset field.
            report_rules='v22' if payload.get('version') in (
                '0.9.31','0.9.32','0.9.33','0.9.34','0.9.35') else getattr(game,'ruleset_version','v23')
        if report_rules not in ('v22','v23'):
            raise ValueError('Niezgodny wariant zasad w audycie')
        game.ruleset_version=report_rules
        game.pending_vacant_income=None
        # Replay snapshots from 0.9.36 are schema 1, despite already
        # using ruleset v23. New files advertise schema 2 explicitly.
        signed_schema=initial.get('ruleset_state')
        if signed_schema is None:
            game.audit_state_schema=1
        elif (isinstance(signed_schema,dict)
              and signed_schema.get('audit_schema') in (2,3)
              and signed_schema.get('version')=='v23'
              and signed_schema.get('pending_vacant_income') is None
              and signed_schema.get('vacant_income_enabled') is
                  getattr(game,'vacant_income_enabled',False)
              and (signed_schema.get('audit_schema')==2 or
                   signed_schema.get('starting_compensation')=='unit_5_5')):
            game.audit_state_schema=signed_schema['audit_schema']
        else:
            raise ValueError("Niezgodne metadane wersji zasad w migawce audytu")
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
    if ('vacant_slot_income_total' in payload.get('summary',{})
            and list(getattr(game,'slot_income',[0,0])) !=
                payload['summary']['vacant_slot_income_total']):
        raise ValueError("Niezgodny licznik dochodu za wolne pola w audycie")
    return True
