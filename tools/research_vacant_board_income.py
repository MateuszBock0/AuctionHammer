"""Non-production experiment: +1 coin per empty own board slot at own turn end.

Does NOT change the game's rules or starting coins. Play full real v22 matches,
compare the same deterministic seeds under two rule sets, check integrity after
each AI command, and export diagnostic CSV/JSON.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import statistics
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game.core.ai import ComputerOpponent
from game.core.engine import Match
from tools.simulate_v22 import choose_actor
from tools.analyze_first_player_advantage import wilson_interval


def vacant_slot_bonus(unit_count):
    """After ALL own-turn abilities resolved, max 5 board slots exist."""
    if not 0<=unit_count<=5:
        raise ValueError("Board must contain between 0 and 5 units")
    return 5-unit_count


class VacantBoardIncomeMatch(Match):
    """Experimental subclass: standard engine + extra end-of-turn coin grant."""

    def __init__(self,*args,**kwargs):
        self.slot_income=[0,0]
        self.slot_income_turns=[0,0]
        super().__init__(*args,**kwargs)

    def _finalize_end_turn(self):
        actor=self.active
        super()._finalize_end_turn()
        # After end-turn effects, before the next player's turn/next auction.
        if self.phase=="turn" and self.players[actor].hp>0:
            coins=vacant_slot_bonus(len(self.players[actor].board))
            self.players[actor].coins+=coins
            self.slot_income[actor]+=coins
            self.slot_income_turns[actor]+=1
            self._log(f"{self.players[actor].name}: +{coins} monet za "
                      f"{5-len(self.players[actor].board)} wolnych pól planszy "
                      "na koniec własnej tury.")


def duel(seed,level="normalny",extra_income=False,max_steps=3000):
    engine=VacantBoardIncomeMatch if extra_income else Match
    g=engine(seed,audit_enabled=False,auctions_enabled=True,auction_catalog="v22")
    bots=(ComputerOpponent(0,level),ComputerOpponent(1,level))
    g.assert_integrity()
    for step in range(1,max_steps+1):
        if g.phase=="finished":break
        actor=choose_actor(g)
        if actor not in (0,1):
            raise RuntimeError(f"No legal actor: seed={seed} phase={g.phase}")
        bots[actor].step(g)
        g.assert_integrity()
    if g.phase!="finished" or g.winner not in (0,1):
        raise RuntimeError(f"Unfinished match: seed={seed}, phase={g.phase}, "
                           f"round={g.round}, steps={step}")
    first=g.first;second=1-first
    return {
        "seed":seed,"level":level,"rule":"vacant_slots" if extra_income else "baseline",
        "first":first,"winner":g.winner,
        "first_won":int(g.winner==first),
        "rounds":g.round,"steps":step,
        "auctions":len(g.auction_history),
        "first_auction_wins":sum(a["winner"]==first for a in g.auction_history),
        "second_auction_wins":sum(a["winner"]==second for a in g.auction_history),
        "first_auction_spent":sum(a["price"] for a in g.auction_history if a["winner"]==first),
        "second_auction_spent":sum(a["price"] for a in g.auction_history if a["winner"]==second),
        "coins_first_end":g.players[first].coins,
        "coins_second_end":g.players[second].coins,
        "slot_income_first":g.slot_income[first] if extra_income else 0,
        "slot_income_second":g.slot_income[second] if extra_income else 0,
    }


def study(seeds=200,start_seed=220000,levels=("normalny","trudny"),
          output_dir="reports/empty_slots",max_steps=3000):
    if seeds<1 or max_steps<10 or not levels:
        raise ValueError("Invalid requested games/steps/levels")
    target=Path(output_dir)
    target.mkdir(parents=True,exist_ok=True)
    rows=[];failures=[]
    for level in levels:
        if level not in ("łatwy","normalny","trudny"):
            raise ValueError(f"Unknown AI level: {level}")
        for rule in (False,True):
            label=f"{level}/{'vacant_slots' if rule else 'baseline'}"
            for i in range(seeds):
                seed=start_seed+i
                try:
                    rows.append(duel(seed,level,rule,max_steps))
                except Exception as exc:
                    failures.append({"seed":seed,"level":level,"rule":rule,
                                     "error":str(exc),"traceback":traceback.format_exc()})
            own=[r for r in rows if r["level"]==level and
                 r["rule"]==("vacant_slots" if rule else "baseline")]
            print(f"{label}: finished {len(own)}/{seeds}, "
                  f"first won {sum(r['first_won'] for r in own)}",flush=True)
    groups=[]
    for level in levels:
        before={r["seed"]:r for r in rows if r["level"]==level and r["rule"]=="baseline"}
        after={r["seed"]:r for r in rows if r["level"]==level and r["rule"]=="vacant_slots"}
        matched=sorted(before.keys()&after.keys())
        flipped_to_second=sum(before[k]["first_won"]==1 and after[k]["first_won"]==0
                              for k in matched)
        flipped_to_first=sum(before[k]["first_won"]==0 and after[k]["first_won"]==1
                             for k in matched)
        for rule,subset in [("baseline",[before[k] for k in matched]),
                            ("vacant_slots",[after[k] for k in matched])]:
            n=len(subset);w=sum(r["first_won"] for r in subset)
            groups.append({
                "level":level,"rule":rule,"played":n,
                "first_wins":w,"second_wins":n-w,
                "first_win_rate":w/n if n else None,
                "first_win_rate_wilson_95":wilson_interval(w,n),
                "mean_rounds":statistics.mean(r["rounds"] for r in subset) if n else None,
                "mean_first_end_coins":statistics.mean(r["coins_first_end"] for r in subset) if n else None,
                "mean_second_end_coins":statistics.mean(r["coins_second_end"] for r in subset) if n else None,
                "mean_first_slot_income":statistics.mean(r["slot_income_first"] for r in subset) if n else None,
                "mean_second_slot_income":statistics.mean(r["slot_income_second"] for r in subset) if n else None,
                "first_auction_share":sum(r["first_auction_wins"] for r in subset)/
                    sum(r["auctions"] for r in subset) if sum(r["auctions"] for r in subset) else None,
                "matched_seeds":n,
                "first_to_second_flips":flipped_to_second,
                "second_to_first_flips":flipped_to_first,
                "net_more_second_wins":flipped_to_second-flipped_to_first,
            })
    report={
        "format":"AuctionHammer.V22VacantSlotsStudy",
        "schema":1,
        "created_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "production_modified":False,
        "experiment_rule":"Each player receives 5 - len(own_board) extra coins at end of their own turn after end triggers; 0 when full. Other income unchanged.",
        "configuration":{"seeds":seeds,"start_seed":start_seed,
                         "levels":list(levels),"coins_for_second_at_start":3,
                         "max_steps":max_steps,
                         "auctions_enabled":True,"auction_catalog":"v22"},
        "finished":len(rows),"expected":2*seeds*len(levels),
        "failed":len(failures),"comparisons":groups,"failures":failures,
    }
    (target/"summary.json").write_text(json.dumps(
        report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    with (target/"matches.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        names=list(rows[0]) if rows else ["seed"]
        writer=csv.DictWriter(fp,fieldnames=names);writer.writeheader();writer.writerows(rows)
    with (target/"scenarios.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        names=list(groups[0]) if groups else ["level"]
        writer=csv.DictWriter(fp,fieldnames=names);writer.writeheader();writer.writerows(groups)
    print(json.dumps({"finished":report["finished"],"expected":report["expected"],
                      "failed":report["failed"],"comparisons":groups},
                     ensure_ascii=False,indent=2),flush=True)
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=int,default=200)
    ap.add_argument("--start-seed",type=int,default=220000)
    ap.add_argument("--max-steps",type=int,default=3000)
    ap.add_argument("--levels",nargs="+",default=["normalny","trudny"])
    ap.add_argument("--output-dir",default="reports/empty_slots")
    args=ap.parse_args()
    result=study(args.seeds,args.start_seed,args.levels,args.output_dir,args.max_steps)
    return int(result["failed"]>0)


if __name__=="__main__":
    sys.exit(main())
