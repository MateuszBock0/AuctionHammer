"""Produce a 70+51 card-copy coverage CSV from canonical data and live UI.

Run: python -m scripts.card_copy_matrix_0949 > card-copy-coverage.csv

This is a presentation coverage index, not proof that all engine branches
are behaviorally equivalent to the descriptions.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from types import SimpleNamespace
import sys

from game.core.auction_catalog import CATALOG_V22, TRIGGER, V22_CARDS, v23_variant
from game.ui.auction_copy import display_auction_copy, full_preview_auction_copy
from game.ui.card_infographics import card_cue
from game.ui.card_summary import ability_summary
from game.ui.v23_help import v23_base_card_note,v23_base_card_short_note

ROOT=Path(__file__).resolve().parents[1]
RARITIES=('podstawowa','rzadka','legendarna')
COLUMNS=('id','tier','ruleset','engine_module','trigger','family',
         'short_description','full_description','visual_cue','coverage_test')


def rows():
    raw=json.loads((ROOT/'data/cards_base_70.json').read_text(encoding='utf-8'))
    assert len(raw)==70,'Unexpected basic catalogue size'
    result=[]
    for spec in raw:
        growth=spec['hand_growth']
        definition=SimpleNamespace(
            **{**spec,'growth_atk':growth['atk_per_hand_turn'],
               'growth_hp':growth['hp_per_hand_turn']})
        card=SimpleNamespace(definition=definition,ability_level=0,hand_turns=0)
        summary=ability_summary(card)
        cue=card_cue(card)
        conditional=v23_base_card_note(spec['id'],'v23')
        result.append({
            'id':spec['id'],'tier':'base','ruleset':'v23',
            'engine_module':'game/core/engine.py','trigger':spec['trigger'],
            'family':spec['family'],
            'short_description':v23_base_card_short_note(spec['id'],'v23') or summary.short,
            'full_description':conditional or summary.full,
            'visual_cue':cue.base,
            'coverage_test':'tests/test_card_copy_matrix_0949.py',
        })
    assert len(V22_CARDS)==17,'Unexpected auction catalogue size'
    for aid in sorted(V22_CARDS):
        archetype=CATALOG_V22[aid]
        for tier in RARITIES:
            definition=SimpleNamespace(
                id=aid,name=archetype.name,trigger=TRIGGER[archetype.trigger],
                family=archetype.family,
                effect=v23_variant('v22',aid,tier,'v23'),
                scaling=f'POZIOM 0 · {tier.upper()} · BEZ SKALOWANIA')
            card=SimpleNamespace(definition=definition,ability_level=0,hand_turns=0)
            summary=ability_summary(card)
            cue=card_cue(card)
            result.append({
                'id':aid,'tier':tier,'ruleset':'v23',
                'engine_module':'game/core/auction_abilities.py',
                'trigger':definition.trigger,'family':definition.family,
                'short_description':summary.short,
                'full_description':full_preview_auction_copy(aid,tier,'v23',display_auction_copy(definition)),
                'visual_cue':cue.base,
                'coverage_test':'tests/test_card_copy_matrix_0949.py',
            })
    return result


def validate():
    data=rows()
    assert len(data)==121,(len(data),'Expected 70+51')
    assert len({(r['id'],r['tier']) for r in data})==121
    for row in data:
        assert all(str(row[k]).strip() for k in COLUMNS),(row,'Empty column')
        assert '{' not in row['full_description'],row
        if row['tier']!='base':
            assert 'AKTYWNA' in row['short_description'],row
            assert row['visual_cue']=='AKTYWNA',row
    return data


def main():
    writer=csv.DictWriter(sys.stdout,fieldnames=COLUMNS,lineterminator='\n')
    writer.writeheader()
    writer.writerows(validate())


if __name__=='__main__':
    main()
