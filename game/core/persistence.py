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

SCHEMA=1
TYPES={cls.__name__:cls for cls in
       (Card,CardDefinition,Unit,Player,Effect,Choice,Pending)}


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
    if not isinstance(data.get('cards'),dict) or set(data['cards'])!=ids:
        raise ValueError('Zapis zawiera niezgodny katalog kart')
    if not isinstance(data.get('players'),list) or len(data['players'])!=2:
        raise ValueError('Nieprawidłowa liczba graczy')
    if not isinstance(data.get('rng'),random.Random):
        raise ValueError('Brak prawidłowego stanu losowania')
    if data.get('phase') not in ('mulligan','turn','finished'):
        raise ValueError('Nieprawidłowa faza meczu')
    match=Match.__new__(Match)
    match.__dict__.update(data)
    return match
