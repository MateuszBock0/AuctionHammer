"""0.9.94 bounded-hard vs exact 0.9.93 logic, full mirrored audited matches.

    python -m tools.simulate_bounded_hard_0994 --pairs 32 --output reports/bounded-hard-0994.json

Matches use identical new General semantics, public observations and seed.
Latency reports isolated PURE-PLANNER call timings, not the engine/pygame.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import quantiles
from time import perf_counter_ns

from game.core.ai import ComputerOpponent
from game.core.engine import Match
from tools.simulate_v22 import choose_actor


class PreviousExpert(ComputerOpponent):
    """Exact 0.9.93 expert combat choice without bounded lookahead."""

    def hard_combo_finish(self,game):
        return None

    def hard_attack_choice(self,game):
        return self._hard_attack_choice_093(game)


def run_one(seed,swapped,max_steps=3000):
    game=Match(seed,audit_enabled=True,auctions_enabled=True,
               auction_catalog='v22',fixed_board_slots=True,
               starting_compensation='choice_2_5_or_coins')
    assert game.general_friendly_only
    agents=(ComputerOpponent(0,'trudny'),PreviousExpert(1,'trudny')) if not swapped else (
        PreviousExpert(0,'trudny'),ComputerOpponent(1,'trudny'))
    timings=[]
    for step in range(max_steps):
        if game.phase=='finished':
            break
        actor=choose_actor(game)
        if actor not in (0,1):
            raise RuntimeError('No active player')
        ai=agents[actor]
        if (isinstance(ai,ComputerOpponent) and
                not isinstance(ai,PreviousExpert) and
                game.phase=='turn' and game.pending is None):
            t=perf_counter_ns()
            ai.hard_attack_choice(game)
            elapsed=perf_counter_ns()-t
            timings.append(elapsed/1_000_000)
        n=len(game.audit_actions)
        ai.step(game)
        game.assert_integrity()
        if len(game.audit_actions)!=n+1:
            raise AssertionError(f'Not exactly one audited action: {seed=} {step=}')
    if game.phase!='finished':
        raise AssertionError(f'Incomplete match for seed={seed}')
    return (not isinstance(agents[game.winner],PreviousExpert),
            len(game.audit_actions),timings)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pairs',type=int,default=32)
    parser.add_argument('--seed',type=int,default=994000)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--min-winrate',type=float,default=None)
    parser.add_argument('--max-p95-ms',type=float,default=100.0)
    args=parser.parse_args()
    if args.pairs<1 or args.pairs>1000:
        raise ValueError('pairs must be 1..1000')
    counts=Counter()
    durations=[]
    for offset in range(args.pairs):
        for swapped in (False,True):
            won,steps,times=run_one(args.seed+offset,swapped)
            counts['new_wins' if won else 'old_wins']+=1
            counts['commands']+=steps
            durations.extend(times)
    games=counts['new_wins']+counts['old_wins']
    times=sorted(durations)
    p95=times[min(len(times)-1,int(.95*(len(times)-1)))] if times else 0.
    report={
        'version':'0.9.94',
        'comparison':'bounded hard 0.9.94 vs previous expert 0.9.93',
        'seed_pairs':args.pairs,
        'games':games,
        'new_wins':counts['new_wins'],
        'reference_wins':counts['old_wins'],
        'new_winrate':round(counts['new_wins']/games,4),
        'audited_commands':counts['commands'],
        'planner_calls':len(times),
        'planner_median_ms':round(times[len(times)//2],4) if times else 0.,
        'planner_p95_ms':round(p95,4),
        'planner_max_ms':round(max(times),4) if times else 0.,
        'planner_latency_note':'CPU-specific CI samples, excludes Match action and UI rendering',
        'fairness':'same seeds, swapped seats, same public rules, no hidden hand reading',
        'result_not_guaranteed':'win rate is empirical and can vary by seed',
    }
    rendered=json.dumps(report,ensure_ascii=False,indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered+'\n',encoding='utf-8')
    if args.min_winrate is not None and report['new_winrate']<=args.min_winrate:
        raise SystemExit('No measured advantage over v0.9.93: '+str(report['new_winrate']))
    if p95>args.max_p95_ms:
        raise SystemExit('Planner too slow: '+str(p95)+'ms p95')


if __name__=='__main__':
    main()
