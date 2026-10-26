"""0.9.93: mirrored matches, new expert attack policy vs prior target selection.

No AI is given the opponent's hidden cards or RNG. Both players use EXACTLY
the same newly signed General rules. The reference bot restores only the old
first-attacker and target-score policy; other decisions stay identical.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from game.core.ai import ComputerOpponent
from game.core.engine import Match
from tools.simulate_v22 import choose_actor


class ReferenceHard(ComputerOpponent):
    """Old 0.9.92 combat target selection, no board-wide optimization."""

    def hard_attack_choice(self,game):
        p=game.players[self.player]
        for uid in p.board:
            targets=game.legal_attacks(uid)
            if not targets:
                continue
            attacker=game.units[uid]
            def target_score(t):
                if t.startswith('hero:'):
                    return (12 if not game.players[1-self.player].board else 4)+attacker.atk*.2
                defender=game.units[t]
                kill=15 if attacker.atk>=defender.hp+defender.armor and not defender.shield else 0
                survive=5 if attacker.hp>defender.atk else -1
                return kill+survive+defender.atk*.7-defender.armor*.2
            def expert_score(t):
                basic=target_score(t)
                if t.startswith('hero:'):
                    hero=game.players[1-self.player]
                    return (10000 if hero.hp<=attacker.atk else 0)+basic+(11 if hero.hp<35 else 0)
                target=game.units[t]
                effective=max(0,attacker.atk-target.armor)
                kill=target.hp<=effective and not target.shield
                survive=attacker.hp>target.atk
                return basic+(13 if kill else 0)+(4 if survive else -4)-(3 if target.shield or target.armor else 0)
            return uid,max(targets,key=expert_score)
        return None


def run_one(seed,swap,max_steps=3000):
    game=Match(seed,audit_enabled=True,auctions_enabled=True,
               auction_catalog='v22',
               fixed_board_slots=True,
               starting_compensation='choice_2_5_or_coins')
    if not game.general_friendly_only:
        raise AssertionError('General own-board rule missing')
    levels=(ReferenceHard(0,'trudny'),ComputerOpponent(1,'trudny'))
    if swap:
        levels=levels[::-1]
        for index,bot in enumerate(levels):
            bot.player=index
    for step in range(max_steps):
        if game.phase=='finished':
            break
        player=choose_actor(game)
        if player not in (0,1):
            raise AssertionError(f'No legal actor at {game.phase!r}')
        before=len(game.audit_actions)
        levels[player].step(game)
        game.assert_integrity()
        if len(game.audit_actions)!=before+1:
            raise AssertionError(f'Not exactly one command: seed={seed}, step={step}')
    if game.phase!='finished':
        raise AssertionError(f'Game not completed: {seed}')
    winner=game.winner
    is_new=isinstance(levels[winner],ComputerOpponent) and not isinstance(levels[winner],ReferenceHard)
    return is_new, len(game.auction_history),len(game.audit_actions)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pairs',type=int,default=24)
    p.add_argument('--seed',type=int,default=993000)
    p.add_argument('--output',type=Path)
    p.add_argument('--min-winrate',type=float,default=None)
    args=p.parse_args()
    if not 1<=args.pairs<=1000:
        raise ValueError('pairs must be 1..1000')
    stats=Counter()
    for offset in range(args.pairs):
        for swap in (False,True):
            new,auctions,steps=run_one(args.seed+offset,swap)
            stats['new_wins' if new else 'reference_wins']+=1
            stats['auctions']+=auctions
            stats['steps']+=steps
    total=stats['new_wins']+stats['reference_wins']
    result={'version':'0.9.93','comparison':'new hard tactics vs old first-attacker policy',
            'General_rule':'both bots use new owner-only General behavior',
            'seed_start':args.seed,'seed_pairs':args.pairs,'matches':total,
            'new_hard_wins':stats['new_wins'],
            'reference_wins':stats['reference_wins'],
            'new_hard_winrate':round(stats['new_wins']/total,4),
            'completed_auctions':stats['auctions'],
            'commands':stats['steps'],
            'seats':'each seed played in both assignments',
            'note':'Statistical winrate, NOT guaranteed outcome on arbitrary seeds.'}
    encoded=json.dumps(result,ensure_ascii=False,indent=2)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded+'\n',encoding='utf-8')
    if args.min_winrate is not None and result['new_hard_winrate']<=args.min_winrate:
        raise SystemExit(f"Hard tactical policy has not shown superiority: {result['new_hard_winrate']:.1%}")


if __name__=='__main__':
    main()
