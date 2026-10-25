"""Paired head-to-head whole-match auction AI experiment (v23 / v22 cards).

Run from repo root:
    python -m tools.simulate_smart_auction_0990 --pairs 24 --output reports/auction_ai_0990.json

Each deterministic seed is played twice with opposite difficulty assignments,
so seat order is balanced. No result is forced: better agents can lose games.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import json
import math

from tools.simulate_v22 import simulate_one

MATCHUPS=(("łatwy","normalny"),("normalny","trudny"))


def wilson(wins:int,total:int,z:float=1.96):
    if total==0:
        return [0.,1.]
    p=wins/total
    a=1+z*z/total
    center=(p+z*z/(2*total))/a
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/a
    return [round(max(0.,center-radius),4),
            round(min(1.,center+radius),4)]


def tournament(pairs:int=24,seed:int=990000):
    if pairs<1 or pairs>3000:
        raise ValueError('pairs must be 1..3000')
    results=[]
    for weaker,stronger in MATCHUPS:
        stats=defaultdict(int)
        for offset in range(pairs):
            match_seed=seed+offset
            for levels in ((weaker,stronger),(stronger,weaker)):
                game,steps=simulate_one(
                    match_seed,levels,max_steps=3000,
                    starting_compensation='choice_2_5_or_coins',
                    fixed_board_slots=True)
                winner=levels[game.winner]
                stats[winner+'_wins']+=1
                stats['games']+=1
                stats['auctions']+=len(game.auction_history)
                stats['steps']+=steps
                for auction in game.auction_history:
                    price=auction.get('price',0)
                    if price>0:
                        stats['paid_auctions']+=1
                        stats['total_spent']+=price
        games=stats['games']
        results.append({
            'weaker':weaker,'stronger':stronger,
            'pairs':pairs,'matches':games,
            'weaker_wins':stats[weaker+'_wins'],
            'stronger_wins':stats[stronger+'_wins'],
            'stronger_win_rate':round(stats[stronger+'_wins']/games,4),
            'stronger_wilson_95':wilson(stats[stronger+'_wins'],games),
            'total_auctions':stats['auctions'],
            'paid_auctions':stats['paid_auctions'],
            'mean_auction_price':round(stats['total_spent']/max(1,stats['paid_auctions']),3),
            'mean_commands':round(stats['steps']/games,1)
        })
    return {
        'version':'0.9.90',
        'method':'paired deterministic full matches; each seed played with swapped levels, 50/50 seat allocation',
        'seed_start':seed,
        'warning':'No difficulty can guarantee 100% wins; win rates and Wilson intervals are empirical only.',
        'comparisons':results,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pairs',type=int,default=24)
    parser.add_argument('--seed',type=int,default=990000)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--min-stronger-winrate',type=float,default=None,
                        help='CI acceptance: require each stronger agent to beat the weaker in > threshold fraction')
    args=parser.parse_args()
    report=tournament(args.pairs,args.seed)
    encoded=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded+'\n',encoding='utf-8')
    if args.min_stronger_winrate is not None:
        failed=[f"{r['weaker']} vs {r['stronger']}: {r['stronger_win_rate']:.1%}"
                for r in report['comparisons']
                if r['stronger_win_rate'] <= args.min_stronger_winrate]
        if failed:
            raise SystemExit("SMART AUCTION AI QUALITY GATE FAILED: "+", ".join(failed))


if __name__=='__main__':
    main()
