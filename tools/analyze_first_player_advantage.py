"""Causal probe of AuctionHammer v22 first-mover advantage.

Production rules are NOT changed. Each seeded what-if match is created by the
normal v22 Match constructor; only the second player's starting coins may be
overridden BEFORE either agent acts. In particular, bonus=3 is byte-for-byte
the production rule. Both agents use identical levels and bidding policy.

Compare equal-seed cohorts; do not mistake these AI simulations for human PvP.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import json
from math import sqrt
from pathlib import Path
import statistics
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game.core.ai import ComputerOpponent
from game.core.engine import Match
from tools.simulate_v22 import choose_actor

DEFAULT_START_SEED=220000
BONUSES=(0,3,5,7,10)
PROFILES=(("normalny","standard"),("trudny","standard"),
          ("normalny","auction_plus4"))


class AuctionPlusFourAI(ComputerOpponent):
    """Controlled behavioral variant: only increase the bid ceiling by 4.

    Everything else, including card choices and combat, uses ComputerOpponent.
    """
    def step(self,game):
        if (game.phase=="auction" and game.auction is not None and
                game.auction.turn==self.player and
                game.auction.phase=="bidding"):
            state=game.auction
            minimum=max(1,state.highest_effective+1-state.bid_bonus[self.player])
            ceiling=min(game.players[self.player].coins,6+state.number*2)
            if minimum<=ceiling:
                game.auction_bid(self.player,minimum)
            else:
                game.auction_pass(self.player)
            return
        super().step(game)


def wilson_interval(successes, attempts, z=1.95996398454):
    """95% Wilson CI for a binomial proportion; no external dependencies."""
    if not attempts:
        return [None,None]
    p=successes/attempts
    div=1+z*z/attempts
    middle=(p+z*z/(2*attempts))/div
    half=z*sqrt(p*(1-p)/attempts+z*z/(4*attempts*attempts))/div
    return [max(0,middle-half),min(1,middle+half)]


def early_observation(game):
    first=game.first
    left=game.players[first]
    right=game.players[1-first]
    return {
        "round_completed":game.auction.completed_round,
        "hero_hp_first":left.hp,
        "hero_hp_second":right.hp,
        "hp_gap_first_minus_second":left.hp-right.hp,
        "coins_gap_first_minus_second":left.coins-right.coins,
        "board_gap_first_minus_second":len(left.board)-len(right.board),
        "board_attack_gap_first_minus_second":
            sum(game.units[uid].atk for uid in left.board)-
            sum(game.units[uid].atk for uid in right.board),
    }


def play(seed, second_bonus=3, level="normalny",policy="standard",
         max_steps=3000):
    """One complete paired-seed trial using exactly the live rules/agents."""
    if not isinstance(second_bonus,int) or second_bonus<0:
        raise ValueError("Coin bonus must be a nonnegative integer")
    if level not in ("łatwy","normalny","trudny"):
        raise ValueError("Unknown difficulty")
    if policy not in ("standard","auction_plus4"):
        raise ValueError("Unknown bidding policy")
    game=Match(seed,audit_enabled=False,auctions_enabled=True,auction_catalog="v22")
    first=game.first
    second=1-first
    if second_bonus!=3:
        # Experimental intervention only. Do NOT change the real game's
        # configured 3-coin rule or pretend these are unmodified game audits.
        game.players[second].coins=second_bonus
    agents=(ComputerOpponent(0,level),ComputerOpponent(1,level)) if policy=="standard" else (
        AuctionPlusFourAI(0,level),AuctionPlusFourAI(1,level))
    early={}
    game.assert_integrity()
    for step in range(1,max_steps+1):
        if game.phase=="finished":
            break
        if game.phase=="auction" and game.auction is not None:
            round_completed=game.auction.completed_round
            if round_completed in (3,6,9) and round_completed not in early:
                early[round_completed]=early_observation(game)
        actor=choose_actor(game)
        if actor not in (0,1):
            raise RuntimeError(f"No valid actor at seed {seed}: {game.phase}")
        agents[actor].step(game)
        game.assert_integrity()
    if game.phase!="finished":
        raise RuntimeError(f"Unfinished after {max_steps} steps; seed={seed}, phase={game.phase}")
    if game.winner not in (0,1):
        raise RuntimeError(f"Illegal winner seed={seed}: {game.winner}")
    auctions=game.auction_history
    first_auction_wins=sum(a["winner"]==first for a in auctions)
    second_auction_wins=sum(a["winner"]==second for a in auctions)
    first_auction_spent=sum(a["price"] for a in auctions if a["winner"]==first)
    second_auction_spent=sum(a["price"] for a in auctions if a["winner"]==second)
    return {
        "seed":seed,"ai_level":level,"bidding_policy":policy,
        "second_player_start_coins":second_bonus,
        "first_player_index":first,"winner_index":game.winner,
        "first_player_won":int(game.winner==first),
        "rounds":game.round,"steps":step,
        "auctions_completed":len(auctions),
        "auctions_won_first":first_auction_wins,
        "auctions_won_second":second_auction_wins,
        "auction_spend_first":first_auction_spent,
        "auction_spend_second":second_auction_spent,
        "hero_hp_first_final":game.players[first].hp,
        "hero_hp_second_final":game.players[second].hp,
        "round3_hp_gap":early.get(3,{}).get("hp_gap_first_minus_second"),
        "round3_coin_gap":early.get(3,{}).get("coins_gap_first_minus_second"),
        "round3_board_gap":early.get(3,{}).get("board_gap_first_minus_second"),
        "round3_attack_gap":early.get(3,{}).get("board_attack_gap_first_minus_second"),
        "round6_hp_gap":early.get(6,{}).get("hp_gap_first_minus_second"),
        "round9_hp_gap":early.get(9,{}).get("hp_gap_first_minus_second"),
        "actions_observed":"integrity_after_every_step",
    }


def _mean(rows,key):
    values=[r[key] for r in rows if r.get(key) is not None]
    return statistics.mean(values) if values else None


def summarize(rows,first_reference=None):
    finished=len(rows)
    wins=sum(row["first_player_won"] for row in rows)
    result={
        "played":finished,"first_wins":wins,
        "second_wins":finished-wins,
        "first_win_rate":wins/finished if finished else None,
        "first_win_rate_wilson_95":wilson_interval(wins,finished),
        "first_seat_index_counts":dict(sorted(Counter(
            str(r["first_player_index"]) for r in rows).items())),
        "mean_rounds":_mean(rows,"rounds"),
        "median_rounds":statistics.median(r["rounds"] for r in rows) if rows else None,
        "mean_auctions":_mean(rows,"auctions_completed"),
        "mean_first_auction_win_share": (
            sum(r["auctions_won_first"] for r in rows)/
            sum(r["auctions_completed"] for r in rows)
            if sum(r["auctions_completed"] for r in rows) else None),
        "mean_first_auction_spend":_mean(rows,"auction_spend_first"),
        "mean_second_auction_spend":_mean(rows,"auction_spend_second"),
        "first_auction_reached":sum(r["round3_hp_gap"] is not None for r in rows),
        "round3_mean_hp_gap_first_minus_second":_mean(rows,"round3_hp_gap"),
        "round3_mean_coins_gap_first_minus_second":_mean(rows,"round3_coin_gap"),
        "round3_mean_board_gap_first_minus_second":_mean(rows,"round3_board_gap"),
        "round3_mean_board_attack_gap_first_minus_second":_mean(rows,"round3_attack_gap"),
        "round6_mean_hp_gap_first_minus_second":_mean(rows,"round6_hp_gap"),
        "round9_mean_hp_gap_first_minus_second":_mean(rows,"round9_hp_gap"),
    }
    if first_reference is not None:
        ref={r["seed"]:r for r in first_reference}
        common=[r for r in rows if r["seed"] in ref]
        helped=sum(ref[r["seed"]]["first_player_won"]==1 and r["first_player_won"]==0
                   for r in common)
        harmed=sum(ref[r["seed"]]["first_player_won"]==0 and r["first_player_won"]==1
                   for r in common)
        result["paired_vs_3coins_same_ai_policy"]={
            "matched_seeds":len(common),
            "flips_first_to_second":helped,
            "flips_second_to_first":harmed,
            "net_more_second_wins":helped-harmed,
        }
    return result


def experiment(games_per_scenario=200,start_seed=DEFAULT_START_SEED,
               bonuses=BONUSES,profiles=PROFILES,max_steps=3000,
               output_dir="reports/first_player_v22"):
    if games_per_scenario<1 or max_steps<10:
        raise ValueError("games_per_scenario>=1 and max_steps>=10 required")
    if not bonuses or any(not isinstance(c,int) or c<0 for c in bonuses):
        raise ValueError("Nonnegative coin bonuses required")
    if 3 not in bonuses:
        raise ValueError("Must include the live 3-coin baseline for paired analysis")
    if not profiles or any(policy not in ("standard","auction_plus4")
                           or level not in ("łatwy","normalny","trudny")
                           for level,policy in profiles):
        raise ValueError("Invalid AI profiles")
    destination=Path(output_dir)
    destination.mkdir(parents=True,exist_ok=True)
    by_scenario={}
    failures=[]
    all_rows=[]
    for level,policy in profiles:
        for bonus in bonuses:
            label=f"{level}__{policy}__bonus{bonus}"
            rows=[]
            for index in range(games_per_scenario):
                seed=start_seed+index
                try:
                    row=play(seed,bonus,level,policy,max_steps)
                    rows.append(row)
                    all_rows.append(row)
                except Exception as exc:
                    failure={
                        "scenario":label,"seed":seed,
                        "type":type(exc).__name__,"message":str(exc),
                        "traceback":traceback.format_exc(),
                    }
                    failures.append(failure)
                    print(f"FAIL {label} seed={seed}: {exc}",flush=True)
            by_scenario[(level,policy,bonus)]=rows
            print(f"[{label}] ukończone={len(rows)}/{games_per_scenario}; "
                  f"pierwszy wygrywa={sum(r['first_player_won'] for r in rows)}; "
                  f"błędy={sum(f['scenario']==label for f in failures)}",
                  flush=True)
    scenarios=[]
    for level,policy in profiles:
        ref=by_scenario[(level,policy,3)]
        for bonus in bonuses:
            row=by_scenario[(level,policy,bonus)]
            stats=summarize(row,ref if bonus!=3 else None)
            scenarios.append({"ai_level":level,"bidding_policy":policy,
                              "second_start_coins":bonus,**stats})
    scenario_baseline=next((s for s in scenarios
                            if s["ai_level"]=="normalny" and
                               s["bidding_policy"]=="standard" and
                               s["second_start_coins"]==3),None)
    baseline_100=by_scenario.get(("normalny","standard",3),[])[:100]
    report={
        "format":"AuctionHammer.FirstPlayerAdvantageExperiment",
        "schema":1,
        "created_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope":"offline v22; identical AI both seats; experimental coin overrides only",
        "production_second_player_bonus":3,
        "gameplay_code_modified":False,
        "audited_replay_per_game":False,
        "integrity_checked":"after every AI action; no engine instrumentation",
        "configuration":{"start_seed":start_seed,
                         "games_per_scenario":games_per_scenario,
                         "seed_pool":"the same ordered seeds in every scenario",
                         "bonuses":list(bonuses),
                         "profiles":[{"level":l,"bidding_policy":p} for l,p in profiles],
                         "max_steps":max_steps},
        "summary":{"total_expected":games_per_scenario*len(bonuses)*len(profiles),
                   "total_finished":len(all_rows),
                   "total_failed":len(failures),
                   "reference_normal_standard_3coin":scenario_baseline,
                   "first100_reference_wins":sum(r["first_player_won"] for r in baseline_100),
                   "first100_reference_count":len(baseline_100),
                   "all_first_wins":sum(r["first_player_won"] for r in all_rows)},
        "scenarios":scenarios,
        "failures":failures,
    }
    (destination/"wyniki_scenariuszy.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    with (destination/"wyniki_scenariuszy.csv").open(
            "w",newline="",encoding="utf-8-sig") as fp:
        cols=["ai_level","bidding_policy","second_start_coins","played",
              "first_wins","second_wins","first_win_rate",
              "round3_mean_hp_gap_first_minus_second",
              "round3_mean_coins_gap_first_minus_second",
              "round3_mean_board_gap_first_minus_second",
              "mean_first_auction_win_share","mean_first_auction_spend",
              "mean_second_auction_spend","mean_rounds","median_rounds"]
        wr=csv.DictWriter(fp,fieldnames=cols,extrasaction="ignore")
        wr.writeheader()
        wr.writerows(scenarios)
    with (destination/"wyniki_meczow.csv").open(
            "w",newline="",encoding="utf-8-sig") as fp:
        cols=list(all_rows[0]) if all_rows else ["seed"]
        wr=csv.DictWriter(fp,fieldnames=cols,extrasaction="ignore")
        wr.writeheader()
        wr.writerows(all_rows)
    print(json.dumps({
        "report":str(destination/"wyniki_scenariuszy.json"),
        "summary":report["summary"],
        "scenarios":[{"ai_level":s["ai_level"],"policy":s["bidding_policy"],
                      "bonus":s["second_start_coins"],"first_wins":s["first_wins"],
                      "played":s["played"],"first_win_rate":s["first_win_rate"],
                      "round3_hp_gap":s["round3_mean_hp_gap_first_minus_second"],
                      "first_auction_share":s["mean_first_auction_win_share"]}
                     for s in scenarios]},
        ensure_ascii=False,indent=2),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(
        description="Eksperyment przewagi pierwszego gracza: bonusy i strategie AI")
    parser.add_argument("--games-per-scenario",type=int,default=200)
    parser.add_argument("--start-seed",type=int,default=DEFAULT_START_SEED)
    parser.add_argument("--max-steps",type=int,default=3000)
    parser.add_argument("--bonuses",type=int,nargs="+",default=list(BONUSES))
    parser.add_argument("--output-dir",default="reports/first_player_v22")
    args=parser.parse_args()
    report=experiment(args.games_per_scenario,args.start_seed,args.bonuses,
                      max_steps=args.max_steps,output_dir=args.output_dir)
    return 1 if report["summary"]["total_failed"] else 0


if __name__=="__main__":
    sys.exit(main())
