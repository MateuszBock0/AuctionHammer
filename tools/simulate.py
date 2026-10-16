"""Heurystyczne testy integracyjne na identycznym silniku, bez pygame.
Użycie: python tools/simulate.py [liczba_meczy]
"""
from pathlib import Path
import sys
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game.core.engine import Match
from game.core.ai import ComputerOpponent


def main():
    total=int(sys.argv[1]) if len(sys.argv)>1 else 100
    wins=Counter()
    turns=[]
    bots=(ComputerOpponent(0),ComputerOpponent(1))
    for seed in range(total):
        m=Match(seed)
        m.finish_mulligan(0,[]);m.finish_mulligan(1,[])
        for tick in range(3000):
            if m.phase=='finished':break
            if m.pending:bots[m.pending.owner].choose(m)
            else:bots[m.active].step(m)
            m.assert_integrity()
        if m.phase!='finished':raise RuntimeError(f'Partia seed={seed} nie ukończyła się')
        wins[m.winner]+=1
        turns.append(m.round)
    print(f'AuctionHammer 0.9.2 (Game Master v17): {total} partii bez aukcji')
    print(f'Wygrane P1: {wins[0]} ({100*wins[0]/total:.1f}%)')
    print(f'Wygrane P2: {wins[1]} ({100*wins[1]/total:.1f}%)')
    print(f'Średnia długość: {sum(turns)/len(turns):.1f} rund')
    print('Uwaga: oba agenty używają tej samej prostej heurystyki; to NIE dowód balansu.')

if __name__=='__main__':main()
