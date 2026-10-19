"""AuctionHammer v22 — reproducible AI-vs-AI tournament with full audited matches.

Examples:
    python tools/simulate_v22.py --games 100 --output-dir reports/v22_100
    python tools/simulate_v22.py --games 2 --verify-every 1 --output-dir reports/smoke

The tournament never touches %LOCALAPPDATA% or a player's own match archive.
Only finished matches are archived. A failed/incomplete match gets diagnostics.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game.core.ai import ComputerOpponent
from game.core.audit import (archive_path, list_archived_matches, read_report,
                             verify_replay, write_last_match, state_snapshot)
from game.core.engine import Match

LEVELS=("łatwy","normalny","trudny")
CATALOG="v22"
DEFAULT_SEED=220000


def choose_actor(game):
    """Return the ONLY actor allowed to issue the next public command."""
    if game.phase=="mulligan":
        return next((pid for pid in (0,1) if pid not in game.mulligan_done),None)
    if game.pending is not None:
        return game.pending.owner
    if game.phase=="auction" and game.auction is not None:
        return game.auction.turn
    if game.phase=="turn":
        return game.active
    return None


def simulate_one(seed,levels=("normalny","normalny"),max_steps=3000):
    """Play an entire seeded v22 match; check integrity after EVERY action."""
    game=Match(seed,audit_enabled=True,auctions_enabled=True,auction_catalog=CATALOG)
    agents=(ComputerOpponent(0,levels[0]),ComputerOpponent(1,levels[1]))
    game.assert_integrity()
    try:
        for step in range(1,max_steps+1):
            if game.phase=="finished":
                break
            actor=choose_actor(game)
            if actor not in (0,1):
                raise RuntimeError(f"Brak legalnego aktora: faza={game.phase}")
            before=len(game.audit_actions)
            agents[actor].step(game)
            game.assert_integrity()
            after=len(game.audit_actions)
            if after!=before+1:
                raise RuntimeError(
                    f"Brak postępu lub wiele komend na krok: seed={seed}, "
                    f"step={step}, phase={game.phase}, commands={after-before}")
        else:
            step=max_steps
        if game.phase!="finished":
            raise RuntimeError(f"Limit {max_steps} kroków bez zakończenia meczu")
        if game.winner not in (0,1):
            raise RuntimeError(f"Niepoprawny zwycięzca {game.winner!r}")
        game.assert_integrity()
        return game,step
    except Exception as exc:
        # Attach the exact partially played match for failure diagnostics.
        exc.match=game
        exc.sim_step=locals().get("step",0)
        raise


def collect_row(game,steps):
    purchases=Counter(meta.get("archetype") for meta in game.auction_awards.values()
                      if meta.get("archetype") and not meta.get("ephemeral"))
    offered=Counter(offer["archetype"] for auction in game.auction_history
                    for offer in auction["offers"] if offer.get("archetype"))
    rarity=Counter(meta.get("initial_rarity") for meta in game.auction_awards.values()
                   if meta.get("archetype"))
    return {
        "seed":game.seed,
        "status":"finished",
        "winner":game.winner,
        "first_player":game.first,
        "first_player_won":game.winner==game.first,
        "rounds":game.round,
        "steps":steps,
        "auctions_completed":len(game.auction_history),
        "auction_cards_bought":sum(purchases.values()),
        "purchased_archetypes":dict(sorted(purchases.items())),
        "offered_archetypes":dict(sorted(offered.items())),
        "initial_rarity_distribution":dict(sorted(rarity.items())),
        "hero_hp":[p.hp for p in game.players],
        "death_counts":list(game.death_counts),
        "action_commands":len(game.audit_actions),
        "failed_commands":sum(a["error"] is not None for a in game.audit_actions),
        "events":len(game.event_journal),
        "audit_file":None,
        "replay_verified":False,
    }


def _failure_data(seed,exc):
    game=getattr(exc,"match",None)
    diagnostics={
        "seed":seed,"status":"failed","type":type(exc).__name__,
        "message":str(exc),"step":getattr(exc,"sim_step",0),
        "traceback":traceback.format_exc(),
    }
    if game is not None:
        diagnostics.update({
            "phase":game.phase,"round":game.round,
            "active":game.active,"winner":game.winner,
            "audit_commands":len(game.audit_actions),
            "events_tail":game.event_journal[-30:],
        })
        try:
            diagnostics["state"]=state_snapshot(game)
        except Exception as snapshot_exc:
            diagnostics["snapshot_error"]=str(snapshot_exc)
    return diagnostics


def tournament(games=100,start_seed=DEFAULT_SEED,max_steps=3000,
               output_dir="reports/v22_100",levels=("normalny","normalny"),
               verify_every=10):
    """Run all seeds even if some fail; always write machine-readable results."""
    if games<1 or max_steps<10 or verify_every<0:
        raise ValueError("games>0, max_steps>=10, verify_every>=0 are required")
    if len(levels)!=2 or any(level not in LEVELS for level in levels):
        raise ValueError("Nieznany poziom AI")
    target=Path(output_dir)
    target.mkdir(parents=True,exist_ok=True)
    last_file=target/"AuctionHammer-OSTATNI-MECZ.json"
    rows=[]
    failures=[]
    for index in range(games):
        seed=start_seed+index
        game=None
        try:
            game,steps=simulate_one(seed,levels,max_steps)
            row=collect_row(game,steps)
            write_last_match(game,last_file)
            # read_report verifies each stored audit's SHA-256.
            checked=read_report(last_file)
            if checked["seed"]!=seed or not checked["complete_from_start"]:
                raise ValueError("Niepełny lub błędnie zapisany audyt")
            if checked["summary"]["failed_commands"]:
                raise ValueError("Silnik odrzucił komendę AI w zakończonym meczu")
            if verify_every and (index%verify_every==0 or index==games-1):
                verify_replay(checked,lambda replay_seed,auctions_enabled=False,
                              auction_catalog="v3":
                              Match(replay_seed,audit_enabled=True,
                                    auctions_enabled=auctions_enabled,
                                    auction_catalog=auction_catalog))
                row["replay_verified"]=True
            row["audit_file"]=str(archive_path(last_file).relative_to(target))+"/"
            rows.append(row)
        except Exception as exc:
            if not hasattr(exc,"match") and game is not None:
                exc.match=game
            detail=_failure_data(seed,exc)
            failures.append(detail)
            rows.append({"seed":seed,"status":"failed","message":str(exc)})
            error_path=target/"failures"/f"seed_{seed}.json"
            error_path.parent.mkdir(parents=True,exist_ok=True)
            error_path.write_text(json.dumps(detail,ensure_ascii=False,indent=2,
                                             allow_nan=False)+"\n",encoding="utf-8")
        if (index+1)%10==0 or index+1==games:
            print(f"[{index+1}/{games}] ukończone={sum(r['status']=='finished' for r in rows)} "
                  f"błędy={len(failures)}",flush=True)

    passed=[r for r in rows if r["status"]=="finished"]
    winners=Counter(r["winner"] for r in passed)
    offered=Counter()
    bought=Counter()
    rarity=Counter()
    for row in passed:
        offered.update(row["offered_archetypes"])
        bought.update(row["purchased_archetypes"])
        rarity.update(row["initial_rarity_distribution"])
    rounds=[r["rounds"] for r in passed]
    report={
        "format":"AuctionHammer.V22Tournament",
        "schema":1,
        "created_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "configuration":{"games":games,"start_seed":start_seed,
                         "last_seed":start_seed+games-1,
                         "max_steps":max_steps,"levels":list(levels),
                         "auction_catalog":CATALOG,"audits":True,
                         "integrity_check":"after_every_public_command",
                         "replay_every":verify_every},
        "summary":{"requested":games,"finished":len(passed),"failed":len(failures),
                   "wins":{"player0":winners[0],"player1":winners[1]},
                   "first_player_win_count":sum(r["first_player_won"] for r in passed),
                   "first_player_win_rate":(
                       sum(r["first_player_won"] for r in passed)/len(passed)
                       if passed else None),
                   "rounds_average":statistics.mean(rounds) if rounds else None,
                   "rounds_median":statistics.median(rounds) if rounds else None,
                   "rounds_min":min(rounds) if rounds else None,
                   "rounds_max":max(rounds) if rounds else None,
                   "total_auctions":sum(r["auctions_completed"] for r in passed),
                   "total_actions":sum(r["action_commands"] for r in passed),
                   "audit_replays_verified":sum(r["replay_verified"] for r in passed)},
        "auction_coverage":{
            "archetypes_offered":dict(sorted(offered.items())),
            "archetypes_purchased":dict(sorted(bought.items())),
            "rarities_initial":dict(sorted(rarity.items())),
            "distinct_offered":len(offered),
            "distinct_purchased":len(bought)},
        "matches":rows,
        "failed_seeds":[f["seed"] for f in failures],
    }
    # Verify the archive index also contains *all* successfully completed games.
    archived=list_archived_matches(archive_path(last_file))
    if len(archived)!=len(passed):
        failures.append({"type":"ArchiveMismatch","message":
                         f"Archiwum {len(archived)} vs zapisane mecze {len(passed)}"})
        report["summary"]["failed"]+=1
        report["summary"]["archive_error"]="Niekompletne archiwum"
    report_path=target/"raport_100_meczow.json"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2,
                                      allow_nan=False)+"\n",encoding="utf-8")
    with (target/"wyniki_meczow.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        columns=("seed","status","winner","first_player","first_player_won",
                 "rounds","steps","auctions_completed","auction_cards_bought",
                 "action_commands","failed_commands","events","replay_verified",
                 "message")
        writer=csv.DictWriter(fp,fieldnames=columns,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"report":str(report_path),
                      "summary":report["summary"],
                      "auction_coverage":report["auction_coverage"]},
                     ensure_ascii=False,indent=2),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(
        description="100 pełnych meczów AuctionHammer v22, audyty i kontrola integralności")
    parser.add_argument("--games",type=int,default=100)
    parser.add_argument("--start-seed",type=int,default=DEFAULT_SEED)
    parser.add_argument("--max-steps",type=int,default=3000)
    parser.add_argument("--output-dir",default="reports/v22_100")
    parser.add_argument("--level-0",choices=LEVELS,default="normalny")
    parser.add_argument("--level-1",choices=LEVELS,default="normalny")
    parser.add_argument("--verify-every",type=int,default=10,
                        help="Odtwórz komendy i hashe co N meczów; 0 wyłącza")
    args=parser.parse_args()
    try:
        report=tournament(args.games,args.start_seed,args.max_steps,args.output_dir,
                          (args.level_0,args.level_1),args.verify_every)
    except (OSError,ValueError,TypeError) as exc:
        parser.exit(2,f"BŁĄD KONFIGURACJI: {exc}\n")
    return 1 if report["summary"]["failed"] else 0


if __name__=="__main__":
    sys.exit(main())
