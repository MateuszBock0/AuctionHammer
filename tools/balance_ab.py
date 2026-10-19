"""Paired seeded compensation experiment. No production balance changes."""
from __future__ import annotations
import argparse
import csv
import json
import math
from datetime import datetime,timezone
from pathlib import Path
from tools.simulate_v22 import simulate_one

MODES=("coins","unit_5_5","unit_3_5")

def wilson(k,n,z=1.96):
    if n==0:return None
    p=k/n
    d=1+z*z/n
    mid=(p+z*z/(2*n))/d
    r=(z/d)*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return [round(mid-r,5),round(mid+r,5)]

def mcnemar_exact(b,c):
    n=b+c
    if n==0:return 1.
    k=min(b,c)
    logs=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)-n*math.log(2)
          for i in range(k+1)]
    high=max(logs)
    return min(1.,2*math.exp(high)*math.fsum(math.exp(x-high) for x in logs))

def run(games,start_seed,levels,output,max_steps=3000):
    if games<1:raise ValueError("games must be positive")
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    rows=[];errors=[]
    for idx in range(games):
        seed=start_seed+idx
        for mode in MODES:
            try:
                g,steps=simulate_one(seed,levels=levels,max_steps=max_steps,
                                     starting_compensation=mode)
                rows.append(dict(seed=seed,mode=mode,first_player=g.first,
                                 winner=g.winner,first_won=int(g.winner==g.first),
                                 rounds=g.round,steps=steps,
                                 total_starting_token=int("SUM_START_GUARD" in g.cards)))
            except Exception as exc:
                errors.append(dict(seed=seed,mode=mode,error_type=type(exc).__name__,
                                   message=str(exc)))
        if (idx+1)%25==0 or idx+1==games:
            print(f"BALANCE: {idx+1}/{games} paired seeds, errors={len(errors)}",flush=True)
    summary={}
    for mode in MODES:
        vals=[r for r in rows if r["mode"]==mode]
        wins=sum(r["first_won"] for r in vals)
        n=len(vals)
        summary[mode]={"games":n,"first_wins":wins,
                       "first_win_rate":round(wins/n,5) if n else None,
                       "wilson_95":wilson(wins,n),
                       "mean_rounds":round(sum(r["rounds"] for r in vals)/n,2) if n else None}
    paired={}
    for i,left in enumerate(MODES):
        for right in MODES[i+1:]:
            a={r["seed"]:r["first_won"] for r in rows if r["mode"]==left}
            b={r["seed"]:r["first_won"] for r in rows if r["mode"]==right}
            seeds=sorted(set(a)&set(b))
            lost=sum(a[s]==1 and b[s]==0 for s in seeds)
            gained=sum(a[s]==0 and b[s]==1 for s in seeds)
            paired[left+" vs "+right]={
                "pairs":len(seeds),"first_to_second":lost,
                "second_to_first":gained,
                "mcnemar_p":round(mcnemar_exact(lost,gained),6)}
    result={"created_utc":datetime.now(timezone.utc).isoformat(),
            "seed_start":start_seed,"levels":list(levels),
            "requested_games_per_mode":games,
            "summary":summary,"paired":paired,"errors":errors,
            "note":"AI vs AI only; paired seed comparison, not human PvP balance proof."}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    with output.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as fp:
        writer=csv.DictWriter(fp,fieldnames=("seed","mode","first_player","winner",
                          "first_won","rounds","steps","total_starting_token"))
        writer.writeheader();writer.writerows(rows)
    print(json.dumps({"summary":summary,"paired":paired,"errors":len(errors)},
                     ensure_ascii=False,indent=2),flush=True)
    if errors:raise RuntimeError(f"{len(errors)} simulation failures")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--games",type=int,default=400)
    p.add_argument("--start-seed",type=int,default=39000)
    p.add_argument("--level-0",choices=("łatwy","normalny","trudny"),default="normalny")
    p.add_argument("--level-1",choices=("łatwy","normalny","trudny"),default="normalny")
    p.add_argument("--max-steps",type=int,default=3000)
    p.add_argument("--output",default="reports/chorazy/balance_ab.json")
    a=p.parse_args()
    run(a.games,a.start_seed,(a.level_0,a.level_1),a.output,a.max_steps)
