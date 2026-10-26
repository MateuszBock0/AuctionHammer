"""Read-only, deterministic source -> recipient -> outcome ability feedback.

Only confirmed audit actions and completed internal trace changes are displayed.
Never affects Match, its event journal, hashes, RNG, replay or hitboxes.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import OrderedDict

import pygame


PALETTE={
    'heal':(115,224,165),
    'damage':(240,124,123),
    'defense':(145,198,246),
    'buff':(230,196,113),
    'debuff':(196,157,234),
}


@dataclass(frozen=True)
class AbilityCue:
    source: str
    targets: tuple[str,...]
    label: str
    kind: str
    born: int
    source_name: str
    target_names: tuple[str,...]
    lifetime: int = 1180


def _integer(value, default=0):
    return value if type(value) is int else default


def _effect_label(kind, value, remaining):
    if kind=='regen':
        return f'REGEN {value}/{remaining}' if value>0 and remaining>0 else 'REGENERACJA', 'heal'
    if kind=='atk':
        return f'ATK {value:+d}', 'buff' if value>=0 else 'debuff'
    if kind=='max_hp':
        return f'MAX PŻ {value:+d}', 'buff' if value>=0 else 'debuff'
    names={
        'stun':('OGŁUSZENIE','debuff'),
        'poison':('TRUCIZNA','debuff'),
        'silence':('WYCISZENIE','debuff'),
        'shield':('TARCZA','defense'),
        'armor':('PANCERZ','defense'),
        'taunt':('PROWOKACJA','buff'),
        'quick':('SZYBKI ATAK','buff'),
        'double':('PODWÓJNY ATAK','buff'),
        'immune_poison':('ODPORNOŚĆ','buff'),
    }
    return names.get(kind,('', 'buff'))


def _status_deltas(before,after):
    """Use committed before/after, never the intended choice description."""
    if not isinstance(before,dict) or not isinstance(after,dict):
        return ()
    changes=[]
    for prop,label in (('shield','TARCZA'),('armor','PANCERZ')):
        old,new=before.get(prop),after.get(prop)
        if type(old) is int and type(new) is int and new>old:
            changes.append((f'{label} +{new-old}','defense'))
    old,new=before.get('hp'),after.get('hp')
    if type(old) is int and type(new) is int and new!=old:
        changes.append((f'PŻ {new-old:+d}','heal' if new>old else 'damage'))
    return tuple(changes)


class AbilityFeedback:
    """Render succinct readable, bounded feedback for newly committed effects."""

    MAX_CUES=12
    MAX_EVENTS_PER_ACTION=6

    def __init__(self):
        self.reset()

    def reset(self,game=None):
        self.game=game
        self.read_actions=len(getattr(game,'audit_actions',()) or ())
        self.cues: list[AbilityCue]=[]
        self.rects={}
        self._last_render_ms=0

    @staticmethod
    def _visible_rects(game,unit_rect,hero_rect):
        result={}
        for owner,player in enumerate(game.players):
            result[f'hero:{owner}']=hero_rect(owner).copy()
            for uid in player.board:
                if uid in game.units:
                    result[uid]=unit_rect(owner,game.slot_of(uid)).copy()
        return result

    @staticmethod
    def _name(game,uid):
        if uid.startswith('hero:'):
            try:
                return 'Bohater '+game.players[int(uid.split(':')[1])].name
            except (IndexError,ValueError):
                return 'Bohater'
        card=game.cards.get(uid)
        return card.definition.name if card is not None else uid

    @staticmethod
    def _pairs_for_action(action,internals):
        """Return confirmed (source,recipient,label,type), with no guessed hits.

        _add_effect has an explicit source ID, so it is always attributable.
        Healing/damage is attributed only within a non-attack _execute chain;
        ordinary weapon damage is never confused with a skill.
        """
        if action.get('result')!='ok':
            return []
        source=None
        context=None
        pairs=[]
        for trace in internals:
            if trace.get('error') is not None:
                source=None
                context=None
                continue
            op=trace.get('operation')
            args=trace.get('args') or []
            kwargs=trace.get('kwargs') or {}
            before=trace.get('before') or {}
            after=trace.get('after') or {}
            if op=='_execute':
                source=args[0] if args and isinstance(args[0],str) else None
                context=args[1] if len(args)>1 else None
                if source and source in before and source in after:
                    for label,kind in _status_deltas(before[source],after[source]):
                        # Self-defense is the most reliable trace for A002/A004.
                        # HP deltas of the source can also be due to a nested
                        # effect; render those from the nested operation only.
                        if kind=='defense':
                            pairs.append((source,source,label,kind))
                continue
            if op in ('_start_turn','_tick_poison','_finalize_end_turn',
                      '_kill_batch','_resolve_death_wave','_remove_unit'):
                source=None
                context=None
                continue
            if not args or not isinstance(args[0],str):
                continue
            target=args[0]
            if target not in before or target not in after or before[target]==after[target]:
                continue
            if op=='_add_effect':
                actual_source=kwargs.get('source')
                if not isinstance(actual_source,str) or not actual_source:
                    # Some base effects are invoked by _execute without a
                    # source kwarg; only use a current, non-combat caster.
                    if action.get('operation')=='attack':
                        continue
                    actual_source=source
                if not actual_source:
                    continue
                kind=args[1] if len(args)>1 else kwargs.get('kind')
                value=_integer(args[2] if len(args)>2 else kwargs.get('value'))
                remaining=_integer(args[3] if len(args)>3 else kwargs.get('remaining'))
                label,family=_effect_label(kind,value,remaining)
                if label:
                    pairs.append((actual_source,target,label,family))
            elif op in ('_heal','_damage'):
                # In a regular attack chain, an untagged _damage is often
                # *weapon* impact after an ability. Do not attribute it.
                if (not source or context not in ('play','end','death',
                        'auction_cart_play','auction_exchange_enemy',
                        'auction_v24_fallback')
                        or action.get('operation')=='attack'):
                    continue
                for label,family in _status_deltas(before[target],after[target]):
                    if family in ('heal','damage','defense'):
                        pairs.append((source,target,label,family))
        # De-duplicate traces of one actual modifier, preserve order.
        return list(OrderedDict.fromkeys(pairs))[:AbilityFeedback.MAX_EVENTS_PER_ACTION]

    def observe(self,game,unit_rect,hero_rect,now,allowed=True):
        latest=self._visible_rects(game,unit_rect,hero_rect)
        if game is not self.game:
            self.reset(game)
            self.rects=latest
            return
        # Keep last valid coordinates for a card that has just died.
        self.rects.update(latest)
        actions=getattr(game,'audit_actions',()) or ()
        if len(actions)<self.read_actions:
            self.reset(game)
            self.rects=latest
            return
        fresh=actions[self.read_actions:]
        self.read_actions=len(actions)
        self.cues=[c for c in self.cues if 0<=now-c.born<c.lifetime]
        if not allowed:
            self.cues.clear()
            return
        traces=getattr(game,'audit_internal',()) or ()
        if not traces:
            return
        for action in fresh[-8:]:
            start=_integer(action.get('internal_seq_start'),1)
            end=_integer(action.get('internal_seq_end'))
            if end<start or start<1:
                continue
            batch=traces[start-1:end]
            pairs=self._pairs_for_action(action,batch)
            # Consolidate a mass buff (e.g. legendary A014 healing 5 allies)
            # into ONE cue rather than five callout layers.
            groups=OrderedDict()
            for source,target,label,kind in pairs:
                if source not in self.rects or target not in self.rects:
                    continue
                key=(source,label,kind)
                groups.setdefault(key,[])
                if target not in groups[key]:
                    groups[key].append(target)
            for (source,label,kind),targets in list(groups.items())[:4]:
                self.cues.append(AbilityCue(
                    source,tuple(targets),label,kind,int(now),
                    self._name(game,source),
                    tuple(self._name(game,x) for x in targets)))
        self.cues=self.cues[-self.MAX_CUES:]

    @staticmethod
    def _edge_corners(screen,rect,tint,alpha):
        outside=rect.inflate(8,8)
        layer=pygame.Surface((outside.width,outside.height),pygame.SRCALPHA)
        w,h=outside.size
        col=(*tint,alpha)
        for x,sx in ((2,1),(w-3,-1)):
            for y,sy in ((2,1),(h-3,-1)):
                pygame.draw.line(layer,col,(x,y),(x+sx*12,y),2)
                pygame.draw.line(layer,col,(x,y),(x,y+sy*12),2)
        screen.blit(layer,outside.topleft)

    @staticmethod
    def _friendly_path(source_rect,target_rect,owner):
        if owner==0:
            y=max(source_rect.bottom,target_rect.bottom)+5
            return (source_rect.midbottom,(source_rect.centerx,y),
                    (target_rect.centerx,y),target_rect.midbottom)
        y=min(source_rect.top,target_rect.top)-5
        return (source_rect.midtop,(source_rect.centerx,y),
                (target_rect.centerx,y),target_rect.midtop)

    def draw(self,screen,now,font):
        """Board-safe corners/path plus one compact cue in the empty hand gap."""
        self.cues=[cue for cue in self.cues if 0<=now-cue.born<cue.lifetime]
        if not self.cues:
            return
        # Show the latest verified trigger; never put labels over stat plates.
        cue=self.cues[-1]
        age=now-cue.born
        alpha=max(0,int(205*(1-age/cue.lifetime)))
        tint=PALETTE.get(cue.kind,PALETTE['buff'])
        src=self.rects.get(cue.source)
        if src is None:
            return
        self._edge_corners(screen,src,tint,alpha)
        for target in cue.targets[:5]:
            dest=self.rects.get(target)
            if dest is None:
                continue
            self._edge_corners(screen,dest,tint,alpha)
            if target==cue.source or target.startswith('hero:'):
                continue
            # Friendly links can run in the tiny EMPTY gap by the hero bar;
            # a cross-row link would slice through the central HUD, so it
            # gets synchronized endpoint corners + the arrow in the ticker.
            own_src=src.centery>400
            own_dst=dest.centery>400
            if own_src!=own_dst:
                continue
            path=self._friendly_path(src,dest,0 if own_src else 1)
            stroke=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
            pygame.draw.lines(stroke,(*tint,min(alpha,116)),False,path,2)
            screen.blit(stroke,(0,0))
        if len(cue.targets)>1:
            dest=f'{len(cue.targets)} CELE'
        else:
            dest=cue.target_names[0]
        # Hero bar ends at y=706, hand starts at y=746: a 34px ticker
        # here cannot cover combatants, status plates, cards or input areas.
        width=min(915,screen.get_width()-190)
        box=pygame.Rect(112,710,width,31)
        surface=pygame.Surface(box.size,pygame.SRCALPHA)
        pygame.draw.rect(surface,(16,29,38,min(216,alpha+65)),surface.get_rect(),border_radius=5)
        pygame.draw.rect(surface,(*tint,alpha),surface.get_rect(),1,border_radius=5)
        line=f'{cue.source_name}  →  {dest}  ·  {cue.label}'
        while line and font.size(line)[0]>width-22:
            # Fit long names by shortening the source; never hide result.
            if len(cue.source_name)>12:
                abbreviated=cue.source_name[:max(10,len(cue.source_name)-6)].rstrip()+'…'
                cue=AbilityCue(cue.source,cue.targets,cue.label,cue.kind,cue.born,
                               abbreviated,cue.target_names,cue.lifetime)
                line=f'{cue.source_name}  →  {dest}  ·  {cue.label}'
            elif len(dest)>13:
                dest=dest[:max(10,len(dest)-5)].rstrip()+'…'
                line=f'{cue.source_name}  →  {dest}  ·  {cue.label}'
            else:
                break
        text=font.render(line,True,tint)
        text.set_alpha(alpha)
        surface.blit(text,(11,(box.height-text.get_height())//2))
        screen.blit(surface,box.topleft)
