"""Paired first-seat test for the new second-mover 2/5-or-coins choice.

Every mode uses the same match seed, AI configuration and current ruleset.
'coins' is the legacy fixed +3 baseline.
'forced_guard' forces the second mover to select Chorazy 2/5.
'adaptive' lets that AI choose from its actual first hand; no opponent peeking.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.simulate_v22 import simulate_one
from tools.balance_ab import wilson, mcnemar_exact

MODES=('coins','forced_guard','adaptive')
def experiment(games=400,start_seed=39000,output='reports/0941/balance_choice.json'):
    if games<1:raise ValueError('games must be positive')
    table=[];errors=[]
    for n in range(games):
        seed=start_seed+n
        for mode in MODES:
            try:
                kwargs={'starting_compensation':('coins' if mode=='coins'
                          else 'choice_2_5_or_coins')}
                if mode=='forced_guard':kwargs['forced_starting_choice']='unit_2_5'
                game,steps=simulate_one(seed,levels=('normalny','normalny'),
                                        max_steps=3000,**kwargs)
                selected=(getattr(game,'starting_compensation_choice',None)
                          if mode!='coins' else 'coins')
                table.append(dict(seed=seed,mode=mode,choice=selected,
                                  first=game.first,winner=game.winner,
                                  first_wins=int(game.winner==game.first),
                                  rounds=game.round,steps=steps))
            except Exception as exc:
                errors.append(dict(seed=seed,mode=mode,error=str(exc)))
        if (n+1)%50==0 or n+1==games:
            print(f'QA: {n+1}/{games} paired seeds; errors={len(errors)}',flush=True)
    summary={}
    for mode in MODES:
        rows=[x for x in table if x['mode']==mode]
        n=len(rows);won=sum(x['first_wins'] for x in rows)
        summary[mode]={'n':n,'first_wins':won,
                       'first_win_rate':won/n if n else None,
                       'wilson95':wilson(won,n),
                       'second_choices':{c:sum(x['choice']==c for x in rows)
                                         for c in ('coins','unit_2_5')}}
    pairs={}
    for a,b in (('coins','forced_guard'),('coins','adaptive'),('forced_guard','adaptive')):
        lhs={x['seed']:x['first_wins'] for x in table if x['mode']==a}
        rhs={x['seed']:x['first_wins'] for x in table if x['mode']==b}
        shared=set(lhs)&set(rhs)
        b1=sum(lhs[s]==1 and rhs[s]==0 for s in shared)
        c1=sum(lhs[s]==0 and rhs[s]==1 for s in shared)
        pairs[a+'__'+b]={'paired_seeds':len(shared),
                        'first_to_second':b1,'second_to_first':c1,
                        'mcnemar_exact_p':mcnemar_exact(b1,c1)}
    report={'baseline_sha_label':'workflow_head_sha','seed_start':start_seed,
            'requested_games_per_mode':games,'summary':summary,'paired':pairs,
            'errors':errors,'caution':'AI simulation, not a human PvP balance proof'}
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with dest.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as fd:
        writer=csv.DictWriter(fd,fieldnames=('seed','mode','choice','first','winner',
                                             'first_wins','rounds','steps'))
        writer.writeheader();writer.writerows(table)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if errors:raise RuntimeError(f'{len(errors)} simulations failed')
    if any(x['n']!=games for x in summary.values()):
        raise RuntimeError('Incomplete paired experiment')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--games',type=int,default=400)
    p.add_argument('--start-seed',type=int,default=39000)
    p.add_argument('--output',default='reports/0941/balance_choice.json')
    args=p.parse_args()
    experiment(args.games,args.start_seed,args.output)
