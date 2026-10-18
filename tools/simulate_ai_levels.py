"""Benchmark poziomów AI na PRAWDZIWYM silniku v19, bez modyfikowania zasad.

Przykład:
  python tools/simulate_ai_levels.py --games 1000 --max-steps 1200
Wyniki w JSON (stdout); liczby to wyniki pomiarów, nie zapewniony balans.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game.core.engine import Match
from game.core.ai import ComputerOpponent

LEVELS=('łatwy','normalny','trudny')


def duel(seed:int,first_level='trudny',second_level='normalny',
         max_steps=1600):
    game=Match(seed)
    agents=(ComputerOpponent(0,first_level),ComputerOpponent(1,second_level))
    steps=0
    for steps in range(1,max_steps+1):
        if game.phase=='finished':
            break
        if game.phase=='mulligan':
            for ai in agents:
                ai.step(game)
        else:
            player=game.pending.owner if game.pending else game.active
            agents[player].step(game)
    return {'winner':game.winner,'round':game.round,'steps':steps,
            'finished':game.phase=='finished','seed':seed}


def tournament(games=20,max_steps=1600):
    scores={'trudny':0,'normalny':0,'nierozstrzygnięte':0}
    rounds=[]
    for index in range(games):
        swap=index%2==1
        levels=('normalny','trudny') if swap else ('trudny','normalny')
        result=duel(index+17000,*levels,max_steps=max_steps)
        if result['finished'] and result['winner'] is not None:
            scores[levels[result['winner']]]+=1
        else:
            scores['nierozstrzygnięte']+=1
        rounds.append(result['round'])
    return {'games':games,'max_steps':max_steps,'scores':scores,
            'average_round':sum(rounds)/games if games else 0,
            'specification':'GAME_MASTER_v19','auctions':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--games',type=int,default=20)
    parser.add_argument('--max-steps',type=int,default=1600)
    args=parser.parse_args()
    if not 1<=args.games<=100000 or args.max_steps<10:
        parser.error('Zły zakres parametrów')
    print(json.dumps(tournament(args.games,args.max_steps),
                     indent=2,ensure_ascii=False))
