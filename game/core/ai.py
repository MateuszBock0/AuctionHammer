"""AI dla offline MVP: deterministyczne decyzje i ocena bieżącego stanu.
Nie modyfikuje stanu poza publicznymi komendami Match.
"""
from __future__ import annotations
from .models import IllegalMove

class ComputerOpponent:
    def __init__(self,player=1):
        self.player=player

    def choose(self,game):
        p=game.pending
        if p is None:return
        choices=p.choices
        def score(opt):
            target=opt.target
            if target is None:
                return 4 if opt.mode in ('ally','Wzmocnij') else 3
            if target.startswith('hero:'):
                hero=game.players[int(target.split(':')[1])]
                return 15 if hero.idx==self.player and hero.hp<80 else 5
            if target in game.units:
                u=game.units[target]
                is_enemy=u.owner!=self.player
                if is_enemy:
                    if opt.mode in ('Wzmocnij','Cel sojuszniczy','Wzmocnij siebie'):return -50
                    return 10 + max(0,7-u.hp)+u.atk*.7
                if opt.mode in ('Osłab','Cel wrogi'):return -50
                return 7+(u.atk*.7)+(2 if u.hp<u.max_hp else 0)
            if target in game.cards:return 7 + game.cards[target].attack
            return 0
        best=max(range(len(choices)),key=lambda i:(score(choices[i]),-i))
        game.choose(best)

    def step(self,game):
        if game.phase=='finished':return
        if game.phase=='mulligan':
            if self.player not in game.mulligan_done:
                game.finish_mulligan(self.player,[])
            return
        if game.pending:
            if game.pending.owner==self.player:self.choose(game)
            return
        if game.active!=self.player or game.phase!='turn':return
        p=game.players[self.player]
        # Prefer a good unit; basic creature scaling is included in attack and hp.
        candidates=[cid for cid in p.hand if game.can_play(self.player,cid)]
        if candidates:
            def unit_score(cid):
                card=game.cards[cid]
                f=card.definition.faction
                return card.attack*.65+card.max_hp*.34+(2.5 if f in ('Elfy','Ludzie') else 1.0)
            best=max(candidates,key=unit_score)
            game.play(best)
            return
        # Full board: optional replacement of an own unit that has not attacked.
        if not p.played_this_turn and len(p.board)==5 and p.hand:
            eligible=[uid for uid in p.board if game.units[uid].attacks==0]
            if eligible:
                def quality(cid):
                    c=game.cards[cid]
                    if cid in game.units:
                        u=game.units[cid]
                        return u.atk*.65 + (u.hp+u.armor)*.34
                    return c.attack*.65+c.max_hp*.34 + (1.5 if c.definition.faction=='Elfy' else 0)
                worst=min(eligible,key=quality)
                best=max(p.hand,key=quality)
                if quality(best)>quality(worst)+1.75 and game.can_play(self.player,best,worst):
                    game.play(best,worst)
                    return
        # Attack legal opponents: prioritize kills and otherwise enemy hero if favorable.
        for uid in list(p.board):
            targets=game.legal_attacks(uid)
            if not targets:continue
            attacker=game.units[uid]
            def target_score(t):
                if t.startswith('hero:'):
                    return (12 if not game.players[1-self.player].board else 4)+attacker.atk*.2
                defender=game.units[t]
                kill=15 if attacker.atk>=defender.hp+defender.armor and not defender.shield else 0
                survive=5 if attacker.hp>defender.atk else -1
                return kill+survive+defender.atk*.7-defender.armor*.2
            tgt=max(targets,key=target_score)
            game.attack(uid,tgt)
            return
        game.end_turn()
