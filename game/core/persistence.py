"""Bezpieczny zapis v19: JSON z jawnym, ograniczonym katalogiem typów.

Nigdy nie używamy pickle ani dynamicznego importowania klas z pliku zapisu.
Zapis obejmuje również kolejki, aktywne fale śmierci, wybory i RNG, tak aby
wczytanie stanu nie powodowało rozbieżności w rozstrzyganiu kart.
"""
from __future__ import annotations

from collections import deque
from dataclasses import fields, is_dataclass
from pathlib import Path
import hashlib
import json
import os
import random
import sys

from game.core.engine import Match, ROOT
from game.core.models import (Card,CardDefinition,Unit,Player,Effect,Choice,Pending,
                              load_catalog)

from game.core.auction import AuctionState, AuctionOffer

SCHEMA=1
TYPES={cls.__name__:cls for cls in
       (Card,CardDefinition,Unit,Player,Effect,Choice,Pending,AuctionState,AuctionOffer)}


def save_path():
    appdata=os.getenv('LOCALAPPDATA')
    base=Path(appdata) if appdata else Path.home()/'.local'/'share'
    return base/'AuctionHammer'/'savegame_v19.json'


def _encode(obj):
    if obj is None or isinstance(obj,(str,int,float,bool)):
        return obj
    if isinstance(obj,random.Random):
        return {'_type':'rng','state':_encode(obj.getstate())}
    if is_dataclass(obj):
        name=type(obj).__name__
        if TYPES.get(name) is not type(obj):
            raise TypeError('Nieobsługiwany typ zapisu '+name)
        return {'_type':'dataclass','name':name,
                'fields':{f.name:_encode(getattr(obj,f.name))
                          for f in fields(obj)}}
    if isinstance(obj,deque):
        return {'_type':'deque','items':[_encode(v) for v in obj]}
    if isinstance(obj,(set,frozenset)):
        return {'_type':'set','frozen':isinstance(obj,frozenset),
                'items':[_encode(v) for v in sorted(obj,key=repr)]}
    if isinstance(obj,tuple):
        return {'_type':'tuple','items':[_encode(v) for v in obj]}
    if isinstance(obj,list):
        return [_encode(v) for v in obj]
    if isinstance(obj,dict):
        return {'_type':'dict','items':[
            [_encode(k),_encode(v)] for k,v in obj.items()]}
    raise TypeError(f'Nieobsługiwany typ zapisu: {type(obj).__name__}')


def _decode(obj):
    if obj is None or isinstance(obj,(str,int,float,bool)):
        return obj
    if isinstance(obj,list):
        return [_decode(v) for v in obj]
    if not isinstance(obj,dict):
        raise ValueError('Nieprawidłowa zawartość zapisu')
    kind=obj.get('_type')
    if kind=='rng':
        value=random.Random()
        value.setstate(_decode(obj['state']))
        return value
    if kind=='dataclass':
        cls=TYPES.get(obj.get('name'))
        if cls is None:raise ValueError('Nieznana klasa w zapisie')
        data=obj.get('fields')
        if not isinstance(data,dict) or set(data)!={x.name for x in fields(cls)}:
            raise ValueError('Niezgodne pola w zapisie')
        return cls(**{k:_decode(v) for k,v in data.items()})
    if kind=='deque':
        return deque(_decode(v) for v in obj['items'])
    if kind=='set':
        elements=(_decode(v) for v in obj['items'])
        return frozenset(elements) if obj.get('frozen') else set(elements)
    if kind=='tuple':
        return tuple(_decode(v) for v in obj['items'])
    if kind=='dict':
        pairs=obj.get('items')
        if not isinstance(pairs,list):raise ValueError('Nieprawidłowy słownik')
        return {_decode(k):_decode(v) for k,v in pairs}
    raise ValueError('Nieznany typ w zapisie')


def save_match(game: Match, path: Path | None = None):
    if game._draining or game._resolving_death_wave:
        raise ValueError('Nie można zapisać nierozstrzygniętej akcji')
    path=Path(path) if path is not None else save_path()
    encoded=_encode(game.__dict__)
    canonical=json.dumps(encoded,ensure_ascii=False,
                         separators=(',',':'),sort_keys=True)
    digest=hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    package={'schema':SCHEMA,'specification':'GAME_MASTER_v19',
             'checksum':digest,'state':encoded}
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    try:
        temporary.write_text(json.dumps(package,ensure_ascii=False),
                             encoding='utf-8')
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()
    return path


def load_match(path: Path | None = None) -> Match:
    path=Path(path) if path is not None else save_path()
    if path.stat().st_size>20_000_000:
        raise ValueError('Plik zapisu jest zbyt duży')
    package=json.loads(path.read_text(encoding='utf-8'))
    if package.get('schema')!=SCHEMA or package.get('specification')!='GAME_MASTER_v19':
        raise ValueError('Niezgodna wersja zapisu')
    canonical=json.dumps(package['state'],ensure_ascii=False,
                         separators=(',',':'),sort_keys=True)
    if hashlib.sha256(canonical.encode('utf-8')).hexdigest()!=package.get('checksum'):
        raise ValueError('Plik zapisu jest uszkodzony')
    data=_decode(package['state'])
    if not isinstance(data,dict):
        raise ValueError('Nieprawidłowy stan meczu')
    # Minimalne sprawdzenie zgodności z lokalnym katalogiem kart v19.
    ids=set(load_catalog(ROOT/'data'/'cards_base_70.json'))
    awards=data.get('auction_awards',{})
    if not isinstance(awards,dict):
        raise ValueError('Zapis zawiera nieprawidłowe karty aukcyjne')
    v4=data.get('auction_catalog') in ('v4','v22')
    ephemeral=set(data.get('ephemeral_ids',set())) if v4 else set()
    expected=ids|set(awards)|ephemeral
    if (not isinstance(data.get('cards'),dict)
            or set(data['cards'])!=expected
            or any(not (uid.startswith('AUC') or (v4 and uid in ephemeral))
                   for uid in awards)):
        raise ValueError('Zapis zawiera niezgodny katalog kart')
    if not isinstance(data.get('players'),list) or len(data['players'])!=2:
        raise ValueError('Nieprawidłowa liczba graczy')
    if not isinstance(data.get('rng'),random.Random):
        raise ValueError('Brak prawidłowego stanu losowania')
    if data.get('phase') not in ('mulligan','turn','auction','finished'):
        raise ValueError('Nieprawidłowa faza meczu')
    # Compatible with 0.9.18 saves created before the auction subsystem.
    # Saves from 0.9.19/0.9.20 predate the v3 catalog; keep their rule mode.
    data.setdefault('auction_catalog','placeholders'
                    if data.get('auctions_enabled',False) else 'v3')
    data.setdefault('auctions_enabled',False)
    data.setdefault('auction',None)
    data.setdefault('auction_history',[])
    data.setdefault('auction_awards',{})
    if data.get('auction_catalog') in ('v4','v22'):
        from game.core.auction_catalog import catalog_for
        CATALOG=catalog_for(data.get('auction_catalog'))
        seen={o.get('archetype') for h in data['auction_history']
              for o in h.get('offers',[]) if o.get('archetype')}
        if data.get('auction') is not None:
            seen.update(o.archetype for o in data['auction'].offers if o.archetype)
        data.setdefault('auction_bag',[a for a in CATALOG if a not in seen])
        data.setdefault('auction_discarded',
                        [h['unpicked'] for h in data['auction_history']
                         if h.get('unpicked')])
        data.setdefault('auction_used',
                        [uid for uid,card in data['cards'].items()
                         if card.zone=='auction_used'])
        # 0.9.23 mistakenly retired each third offer permanently. Restore
        # those unsold archetypes when migrating old v4 savegames.
        if data.get('auction_supply_version',1)<2:
            bought={meta.get('archetype') for meta in data['auction_awards'].values()
                    if meta.get('archetype') and not meta.get('ephemeral')}
            active={offer.archetype for offer in data['auction'].offers
                    if offer.archetype} if data['auction'] is not None else set()
            for aid in CATALOG:
                if (aid not in bought and aid not in active and
                        aid not in data['auction_bag']):
                    data['auction_bag'].append(aid)
        data['auction_supply_version']=3 if data.get('auction_catalog')=='v22' else 2
    else:
        data.setdefault('auction_bag',[])
        data.setdefault('auction_discarded',[])
        data.setdefault('auction_used',[])
        data.setdefault('auction_supply_version',0)
    # Loading a pre-0.9.34 save must never silently change the rules
    # halfway through a match. Fresh v22 games enable the bonus by default.
    data.setdefault('vacant_income_enabled',False)
    data.setdefault('slot_income',[0,0])
    data.setdefault('slot_income_turns',[0,0])
    data.setdefault('auction_vouchers',[[],[]])
    data.setdefault('auction_blocked_play',set())
    for name,default in (
            ('exiled',[]),('vanished',[]),('ephemeral_ids',set()),
            ('auction_death_grants',set()),('auction_rescue_spent',set()),
            ('auction_general_targets',{}),('auction_general_grants',{}),
            ('auction_pending_targets',{}),('auction_wave_ops',[])):
        data.setdefault(name,default)
    if 'death_counts' not in data:
        # Old builds showed current grave size as "losses". Reconstruct real
        # unit deaths only when a complete audit has enough information.
        counts=[0,0]
        actions=data.get('audit_actions',[])
        events=data.get('event_journal',[])
        if isinstance(actions,list) and isinstance(events,list):
            for action in actions:
                if not isinstance(action,dict):continue
                changes=action.get('changes',{})
                if not isinstance(changes,dict):continue
                transitions=changes.get('units',{})
                if not isinstance(transitions,dict):continue
                for delta in transitions.values():
                    if not isinstance(delta,dict):continue
                    previous,current=delta.get('before'),delta.get('after')
                    if isinstance(previous,dict) and current is None:
                        owner=previous.get('owner')
                        if owner in (0,1):counts[owner]+=1
            logged=sum(isinstance(e,dict) and
                       str(e.get('text','')).startswith('Zgon ')
                       for e in events)
            complete=(bool(data.get('audit_complete',False))
                      and sum(counts)==logged)
        else:
            complete=False
        data['death_counts']=counts if complete else [0,0]
        data['death_counts_complete']=complete
    else:
        data.setdefault('death_counts_complete',True)
    if (not isinstance(data['death_counts'],list)
            or len(data['death_counts'])!=2
            or any(type(n) is not int or n<0 for n in data['death_counts'])):
        raise ValueError('Nieprawidłowy licznik zgonów jednostek')
    match=Match.__new__(Match)
    match.__dict__.update(data)
    return match
