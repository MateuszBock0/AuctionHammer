"""Production-mode QA: 20 full AI matches with permanent physical board slots.

Every game uses the *new* 0.9.51 rule, not legacy compact v22.
Check action count, zero rejected commands, state integrity at EVERY command
(simulate_one) and complete signed replay from an independently read file.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import tempfile

from game.core.engine import Match
from game.core.audit import read_report,verify_replay,write_last_match
from tools.simulate_v22 import simulate_one


def check(games=20,seed=951510):
    total=0
    with tempfile.TemporaryDirectory(prefix="auctionhammer-0951-") as temp:
        for i in range(games):
            match,steps=simulate_one(
                seed+i,starting_compensation="choice_2_5_or_coins",
                fixed_board_slots=True)
            assert match.fixed_board_slots
            assert match.winner in (0,1)
            assert not any(a.get('result')!="ok" for a in match.audit_actions)
            # The signed report must explicitly include the new board layout.
            path=Path(temp)/f"game-{i}.json"
            write_last_match(match,path)
            record=read_report(path)
            assert record['initial_state']['board_layout']['fixed'] is True
            assert record['final_state']['board_layout']['fixed'] is True
            assert verify_replay(record,lambda s,**kwargs:
                                 Match(s,audit_enabled=True,**kwargs))
            total+=len(match.audit_actions)
            print(f"Fixed-board replay {i+1}/{games}: seed={seed+i}, "
                  f"actions={len(match.audit_actions)}, steps={steps}",flush=True)
    print(f"PASS: {games} fixed-slot full matches, {games} signed replays, "
          f"{total} verified commands, no rejected commands.",flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--games",type=int,default=20)
    p.add_argument("--seed",type=int,default=951510)
    a=p.parse_args()
    if a.games<1:raise SystemExit("games must be positive")
    check(a.games,a.seed)


if __name__=="__main__":
    main()
