"""Pygame-ce klient 0.9.1: pełna plansza 2D, ręka, wybory celów, AI, ekran wyniku."""
from __future__ import annotations
import pygame
from game import config as cfg
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from game.ui.card_view import CardView, FACTION_COLORS
from game.core.status_view import active_statuses, hand_grants, STATUS_COLORS
from game.ui.layout import fitted_viewport, window_to_canvas

class SoloApp:
    SIDEBAR_X=1082
    SLOT_W=148
    SLOT_H=180
    SLOT_GAP=26
    FIRST_X=107
    OPP_Y=169
    OWN_Y=451
    HAND_Y=722
    HAND_W=125
    HAND_H=169

    def __init__(self):
        pygame.init()
        # A fixed logical canvas keeps every hitbox in one coordinate system.
        # Only presentation is resized: the viewport preserves aspect ratio.
        self.window=pygame.display.set_mode((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT),pygame.RESIZABLE)
        self.screen=pygame.Surface((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)).convert()
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        self.clock=pygame.time.Clock()
        self.fonts={n:pygame.font.SysFont('segoeui',n,bold=(n>=22)) for n in (12,13,14,15,16,18,22,28,34,46)}
        self.cards_view=CardView()
        self.ai=ComputerOpponent()
        self.bg=self._create_background()
        self.restart()

    def restart(self):
        self.game=Match()
        self.ai.step(self.game)  # AI mulligan is committed, player's hand still hidden from it.
        self.selected=None
        self.hover=None
        self.scroll=0
        self.choice_page=0
        self.last_error=''
        self.last_ai_ms=0
        self.drag_start=None
        self.tooltip_open=False
        self.details_card=None
        self.details_scroll=0
        self.sidebar_card=None
        self._old_pending=None

    def _viewport(self):
        return pygame.Rect(*fitted_viewport(self.window.get_size(),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)))

    def _physical_to_virtual(self,pos):
        result=window_to_canvas(pos,tuple(self._viewport()),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        return result if result is not None else (-10000,-10000)

    def mouse_pos(self):
        return self._physical_to_virtual(pygame.mouse.get_pos())

    def _present(self):
        viewport=self._viewport()
        self.window.fill((5,9,14))
        if viewport.size==self.screen.get_size():
            self.window.blit(self.screen,viewport.topleft)
        else:
            scaled=pygame.transform.smoothscale(self.screen,viewport.size)
            self.window.blit(scaled,viewport.topleft)
        pygame.display.flip()

    def _open_details(self,uid=None):
        uid=uid or self.selected or self.card_under(self.mouse_pos())
        if uid not in self.game.cards:return
        self.details_card=uid
        self.details_scroll=0

    def _create_background(self):
        bg=pygame.Surface((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        for y in range(cfg.WINDOW_HEIGHT):
            k=y/cfg.WINDOW_HEIGHT
            col=(int(16+8*k),int(23+9*k),int(34+11*k))
            pygame.draw.line(bg,col,(0,y),(cfg.WINDOW_WIDTH,y))
        for cx,cy,r in ((380,365,320),(840,330,240)):
            pygame.draw.circle(bg,(26,40,50),(cx,cy),r,2)
            pygame.draw.circle(bg,(26,40,50),(cx,cy),int(r*.66),2)
        return bg

    def _text(self,s,size,x,y,color=None,center=False):
        font=self.fonts[size]
        sf=font.render(str(s),True,color or cfg.TEXT)
        pos=sf.get_rect(center=(x,y)) if center else (x,y)
        self.screen.blit(sf,pos)
        return sf.get_rect(topleft=pos) if not center else sf.get_rect(center=(x,y))

    def _wrap(self,text,size,maxwidth):
        font=self.fonts[size]
        result=[]
        for para in text.split('\n'):
            line=''
            for word in para.split():
                candidate=(line+' '+word).strip()
                if font.size(candidate)[0]>maxwidth and line:
                    result.append(line);line=word
                else:line=candidate
            result.append(line)
        return result

    def _panel(self,rect,fill=None,line=None,radius=14):
        pygame.draw.rect(self.screen,fill or cfg.PANEL,rect,border_radius=radius)
        pygame.draw.rect(self.screen,line or cfg.PANEL_BORDER,rect,1,border_radius=radius)

    def _button(self,rect,label,active=True,accent=False,small=False):
        mp=self.mouse_pos();hover=rect.collidepoint(mp)
        fill=(72,109,108) if accent else (45,65,77)
        if hover and active:fill=(88,130,132) if accent else (67,92,103)
        if not active:fill=(38,47,56)
        self._panel(rect,fill,cfg.GOLD if accent and active else cfg.PANEL_BORDER,9)
        self._text(label,14 if small else 16,rect.centerx,rect.centery,cfg.TEXT if active else cfg.MUTED,center=True)

    def slot_rect(self,owner,index):
        return pygame.Rect(self.FIRST_X+index*(self.SLOT_W+self.SLOT_GAP),self.OWN_Y if owner==0 else self.OPP_Y,self.SLOT_W,self.SLOT_H)

    def hand_layout(self):
        hand=self.game.players[0].hand
        visible=6
        self.scroll=max(0,min(self.scroll,max(0,len(hand)-visible)))
        result={}
        for i,uid in enumerate(hand[self.scroll:self.scroll+visible]):
            result[uid]=pygame.Rect(90+i*156,self.HAND_Y,self.HAND_W,self.HAND_H)
        return result

    def hero_rect(self,idx):
        return pygame.Rect(110,113,935,44) if idx==1 else pygame.Rect(110,648,935,44)

    def card_under(self,pos):
        for uid,rect in self.hand_layout().items():
            if rect.collidepoint(pos):return uid
        for idx,p in enumerate(self.game.players):
            for j,uid in enumerate(p.board):
                if self.slot_rect(idx,j).collidepoint(pos):return uid
        return None

    def target_under(self,pos):
        for idx in (0,1):
            if self.hero_rect(idx).collidepoint(pos):return f'hero:{idx}'
            for j,uid in enumerate(self.game.players[idx].board):
                if self.slot_rect(idx,j).collidepoint(pos):return uid
        return None

    CHOICES_PER_PAGE = 8
    CHOICE_FIRST_Y = 354
    CHOICE_ROW_HEIGHT = 54

    def choice_bounds(self):
        """Choice buttons belong to the sidebar, never above the game board."""
        pending = self.game.pending
        if pending is None:
            return []
        start = self.choice_page * self.CHOICES_PER_PAGE
        count = min(len(pending.choices), start + self.CHOICES_PER_PAGE)
        return [(i, pygame.Rect(1101, self.CHOICE_FIRST_Y +
                                (i - start) * self.CHOICE_ROW_HEIGHT, 324, 47))
                for i in range(start, count)]

    def _choice_last_page(self):
        pending = self.game.pending
        return (len(pending.choices) - 1) // self.CHOICES_PER_PAGE if pending else 0

    def _choose(self, index):
        try:
            self.game.choose(index)
            self.last_error = ''
        except IllegalMove as exc:
            self.last_error = str(exc)
        self.choice_page = 0

    def _choose_target(self, target):
        """Clicking a highlighted board target picks an unambiguous option."""
        pending = self.game.pending
        if pending is None or target is None:
            return
        matches = [i for i, item in enumerate(pending.choices)
                   if item.target == target]
        if len(matches) == 1:
            self._choose(matches[0])
        elif len(matches) > 1:
            self.choice_page = matches[0] // self.CHOICES_PER_PAGE
            self.last_error = 'Wybierz wariant zdolności w panelu po prawej.'

    def click(self,pos,button=1):
        g=self.game
        if self.details_card is not None:
            self.details_card=None;return
        if g.phase=='finished':
            if pygame.Rect(1192,823,236,55).collidepoint(pos):self.restart()
            return
        if g.pending:
            if g.pending.owner != 0:
                return
            for index, rect in self.choice_bounds():
                if rect.collidepoint(pos):
                    self._choose(index)
                    return
            if pygame.Rect(1102,802,150,37).collidepoint(pos):
                self.choice_page = max(0, self.choice_page - 1)
                return
            if pygame.Rect(1274,802,150,37).collidepoint(pos):
                self.choice_page = min(self._choice_last_page(), self.choice_page + 1)
                return
            self._choose_target(self.target_under(pos))
            return
        if pygame.Rect(1103,686,316,40).collidepoint(pos):
            uid=self.sidebar_card
            if uid in g.cards:self._open_details(uid)
            return
        if g.phase=='mulligan':
            for uid,rect in self.hand_layout().items():
                if rect.collidepoint(pos):
                    try:g.mulligan_toggle(uid)
                    except IllegalMove as e:self.last_error=str(e)
                    return
            if pygame.Rect(1182,808,243,59).collidepoint(pos):
                try:g.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
                self.selected=None
            return
        if pygame.Rect(1201,816,221,52).collidepoint(pos):
            if g.active==0:
                try:g.end_turn()
                except IllegalMove as e:self.last_error=str(e)
                self.selected=None
            return
        if pygame.Rect(1093,869,145,33).collidepoint(pos):
            self.restart();return
        if pygame.Rect(924,851,40,37).collidepoint(pos):
            self.scroll=min(self.scroll+1,max(0,len(g.players[0].hand)-6));return
        if pygame.Rect(42,851,40,37).collidepoint(pos):
            self.scroll=max(0,self.scroll-1);return
        hand_card=next((uid for uid,r in self.hand_layout().items() if r.collidepoint(pos)),None)
        if hand_card and g.active==0:
            self.selected=hand_card if self.selected!=hand_card else None
            self.tooltip_open=True;return
        target=self.target_under(pos)
        if g.active==0:
            if self.selected in g.players[0].hand:
                if (target in g.players[0].board) or (self.OWN_Y-12<=pos[1]<=self.OWN_Y+self.SLOT_H+12):
                    replace=target if target in g.players[0].board and len(g.players[0].board)==5 else None
                    self._try_play(self.selected,replace)
                    return
                if target is None:return
            if self.selected in g.players[0].board and target is not None and (target in g.players[1].board or target=='hero:1'):
                try:g.attack(self.selected,target);self.last_error=''
                except IllegalMove as e:self.last_error=str(e)
                if self.selected not in g.units:self.selected=None
                return
            if target in g.players[0].board:
                self.selected=target if self.selected!=target else None
                self.tooltip_open=True;return
        if target in g.units:self.selected=target;self.tooltip_open=True

    def _try_play(self,uid,replace=None):
        try:self.game.play(uid,replace);self.selected=None;self.last_error=''
        except IllegalMove as e:self.last_error=str(e)

    def handle(self,event):
        if event.type==pygame.QUIT:return False
        if event.type==pygame.VIDEORESIZE:
            self.window=pygame.display.set_mode((max(700,event.w),max(500,event.h)),pygame.RESIZABLE)
            return True
        if self.details_card is not None:
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_ESCAPE,pygame.K_i):
                self.details_card=None
            elif event.type==pygame.MOUSEWHEEL:
                self.details_scroll=max(0,min(getattr(self,'details_maxscroll',0),self.details_scroll-event.y*35))
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                self.details_card=None
            return True
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                self.selected=None;self.tooltip_open=False
                if self.game.phase=='finished':self.restart()
            elif event.key==pygame.K_r and not self.game.pending:self.restart()
            elif (self.game.pending and self.game.pending.owner == 0
                  and pygame.K_1 <= event.key <= pygame.K_8):
                index = self.choice_page * self.CHOICES_PER_PAGE + event.key - pygame.K_1
                if index < len(self.game.pending.choices):
                    self._choose(index)
            elif event.key==pygame.K_RETURN and self.game.phase=='mulligan':
                try:self.game.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
            elif event.key==pygame.K_SPACE and self.game.phase=='turn' and self.game.active==0 and not self.game.pending:
                try:self.game.end_turn();self.selected=None
                except IllegalMove as e:self.last_error=str(e)
            elif event.key==pygame.K_LEFT:
                if self.game.pending and self.game.pending.owner==0:self.choice_page=max(0,self.choice_page-1)
                else:self.scroll=max(0,self.scroll-1)
            elif event.key==pygame.K_RIGHT:
                if self.game.pending and self.game.pending.owner==0:self.choice_page=min(self._choice_last_page(),self.choice_page+1)
                else:self.scroll+=1
            elif event.key==pygame.K_i:
                self._open_details(self.game.pending.uid if self.game.pending
                                   else self.selected or self.sidebar_card)
            elif event.key==pygame.K_F11:
                flags=pygame.RESIZABLE if self.window.get_flags() & pygame.FULLSCREEN else pygame.FULLSCREEN
                self.window=pygame.display.set_mode(self.window.get_size(),flags)
            elif event.key==pygame.K_q:return False
        elif event.type==pygame.MOUSEWHEEL:
            if self.game.pending and self.game.pending.owner==0:
                self.choice_page=max(0,min(self._choice_last_page(),self.choice_page-event.y))
            else:self.scroll=max(0,self.scroll-event.y)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            self.drag_start=(pos,self.card_under(pos))
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            if self.drag_start:
                down,card=self.drag_start;self.drag_start=None
                if not self.game.pending and card in self.game.players[0].hand and (pos[0]-down[0])**2+(pos[1]-down[1])**2>100:
                    if self.OWN_Y-12<=pos[1]<=self.OWN_Y+self.SLOT_H+12 and self.game.phase=='turn' and self.game.active==0:
                        target=self.target_under(pos)
                        replace=target if target in self.game.players[0].board and len(self.game.players[0].board)==5 else None
                        self._try_play(card,replace)
                    return
            self.click(pos)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==3:
            self.selected=None;self.tooltip_open=False
        return True

    def update(self):
        g=self.game
        if g.phase=='finished' or self.details_card is not None:return
        if self._old_pending is not g.pending:
            self.choice_page=0
            self._old_pending=g.pending
        t=pygame.time.get_ticks()
        if t-self.last_ai_ms>265:
            if (g.phase=='turn' and (g.active==1 or g.pending and g.pending.owner==1)) or (g.pending and g.pending.owner==1):
                try:self.ai.step(g)
                except IllegalMove as e:self.last_error=str(e)
                self.last_ai_ms=t
        if self.selected in g.cards and self.selected not in g.players[0].hand and self.selected not in g.units:
            self.selected=None

    def _draw_hero(self,idx):
        p=self.game.players[idx]
        rect=self.hero_rect(idx)
        border=cfg.GREEN if idx==0 else cfg.RED
        self._panel(rect,(29,45,59),border,9)
        x=rect.x+176
        hp=max(0,min(100,p.hp))
        pygame.draw.rect(self.screen,(64,71,79),(x,rect.y+14,425,17),border_radius=6)
        pygame.draw.rect(self.screen,(66,171,125) if idx==0 else (181,78,87),(x,rect.y+14,int(hp/100*425),17),border_radius=6)
        self._text(p.name,18,rect.x+15,rect.y+9)
        self._text(f'{p.hp}/100',14,x+173,rect.y+14,(255,255,255))
        self._text(f'MONETY  {p.coins}',16,rect.right-172,rect.y+11,cfg.GOLD)

    def _draw_board(self):
        self._text('STREFA KOMPUTERA',15,107,92,cfg.MUTED)
        self._text('TWOJA STREFA',15,107,425,cfg.MUTED)
        self._draw_hero(1)
        self._draw_hero(0)
        for owner,p in enumerate(self.game.players):
            for i in range(5):
                rect=self.slot_rect(owner,i)
                self._panel(rect,(28,42,52),cfg.SLOT_BORDER,12)
                if i>=len(p.board):
                    self._text('+',34,rect.centerx,rect.centery-8,(64,85,100),center=True)
                    self._text(f'POLE {i+1}',12,rect.centerx,rect.bottom-21,cfg.MUTED,center=True)
                    continue
                uid=p.board[i]
                if uid not in self.game.units:continue
                selected=self.selected==uid
                self.cards_view.draw(self.screen,self.game.cards[uid],rect,self.game.units[uid],selected=selected,hover=rect.collidepoint(self.mouse_pos()),statuses=active_statuses(self.game,uid))
                if owner==0 and self.game.active==0 and self.game.legal_attacks(uid):
                    pygame.draw.circle(self.screen,cfg.GREEN,(rect.right-12,rect.y+9),5)
        self._text('ARENA   ·   WYSTAWIANIE OD PRAWEJ   ·   ATAKI W DOWOLNEJ KOLEJNOŚCI',14,508,406,cfg.GOLD,center=True)
        self._text('RĘKA GRACZA  ·  kliknij kartę, potem planszę (lub przeciągnij)',14,89,705,cfg.MUTED)
        hand=self.hand_layout()
        for uid,rect in hand.items():
            pygame.draw.rect(self.screen,(18,32,41),rect.inflate(11,10),border_radius=13)
            self.cards_view.draw(self.screen,self.game.cards[uid],rect,selected=uid==self.selected,
                                 dim=(self.game.phase=='turn' and self.game.active!=0),statuses=hand_grants(self.game,uid))
        if len(self.game.players[0].hand)>6:
            self._button(pygame.Rect(42,851,40,37),'‹',active=self.scroll>0,small=True)
            self._button(pygame.Rect(924,851,40,37),'›',active=self.scroll+6<len(self.game.players[0].hand),small=True)
            self._text(f'{self.scroll+1}–{min(self.scroll+6,len(self.game.players[0].hand))} / {len(self.game.players[0].hand)}',13,850,701,cfg.MUTED)

    def _draw_sidebar(self):
        rect=pygame.Rect(self.SIDEBAR_X,87,364,819)
        self._panel(rect,(23,35,47),cfg.PANEL_BORDER,16)
        self._text('KARTA / AKCJE',22,1103,106,cfg.GOLD)
        card_id=self.selected or self.card_under(self.mouse_pos())
        self.sidebar_card=card_id if card_id in self.game.cards else None
        if self.game.pending and self.game.pending.owner == 0:
            self._draw_choice_sidebar()
            return
        if card_id and card_id in self.game.cards:
            c=self.game.cards[card_id];d=c.definition
            self._text(d.name,18,1105,151,FACTION_COLORS[d.faction])
            self._text(f'{d.id}  ·  {d.faction}  ·  {d.trigger}',13,1105,178,cfg.MUTED)
            u=self.game.units.get(card_id)
            self._text(f'ATK {u.atk if u else c.attack}    HP {u.hp if u else c.max_hp}/{u.max_hp if u else c.max_hp}',18,1105,204)
            if not u:
                self._text(f'Tury na ręce: {c.hand_turns}    Zdolność: +{c.ability_level}',14,1105,234,cfg.GOLD)
            else:
                self._text(f'Pancerz: {u.armor}    Tarcza: {u.shield}    Ataki: {u.attacks}',14,1105,234,cfg.GOLD)
            self._text('ZDOLNOŚĆ',15,1105,271,cfg.HOVER)
            yy=294
            max_description_y=415 if u else 479
            for line in self._wrap(d.effect,14,326):
                if yy>max_description_y:break
                self._text(line,14,1105,yy);yy+=20
            if u:
                pygame.draw.line(self.screen,cfg.PANEL_BORDER,(1105,440),(1419,440),1)
                statuses=active_statuses(self.game,card_id)
                self._text(f'AKTYWNE EFEKTY ({len(statuses)})',15,1105,448,cfg.GOLD)
                if not statuses:self._text('Brak aktywnych statusów',14,1105,476,cfg.MUTED)
                else:
                    for j,st in enumerate(statuses[:6]):
                        yy=477+j*32
                        pygame.draw.circle(self.screen,st.color,(1112,yy+8),5)
                        description=st.name
                        if st.source:description+=f'  ← {st.source}'
                        description=self.cards_view.clip(description,self.fonts[13],297)
                        self._text(description,13,1126,yy,st.color)
                        # Show magnitude and duration in the large [I] card modal.
                    if len(statuses)>6:
                        self._text(f'+{len(statuses)-6} dalszych efektów — otwórz [I]',13,1105,672,cfg.MUTED)
            else:
                self._text('SKALOWANIE',15,1105,507,cfg.HOVER)
                yy=533
                for line in self._wrap(d.scaling,13,326):
                    self._text(line,13,1105,yy,cfg.MUTED);yy+=18
                    if yy>672:break
        else:
            lines=['Kliknij kartę, aby zobaczyć jej opis.','Najpierw zagrywasz JEDNĄ jednostkę','na turę, potem możesz atakować','dowolną liczbą gotowych jednostek.','','FRAKCJE:',
                   'ELFY: efekt przy wystawieniu','BESTIE: efekt przy ataku','POTWORY: efekt przy śmierci',
                   'KRASNOLUDY: efekt na koniec tury','LUDZIE: efekty pasywne']
            y=171
            for line in lines:
                self._text(line,14,1105,y,cfg.MUTED);y+=29
            self._text('KOLORY AKTYWNYCH EFEKTÓW',14,1105,531,cfg.GOLD)
            samples=[('PROW','taunt'),('TRUC','poison'),('OGŁ','stun'),
                     ('TARCZ','shield'),('REGEN','regen'),('ODP','immune'),
                     ('SZYB','quick'),('2×','double')]
            for i,(label,key) in enumerate(samples):
                x=1105+(i%2)*153;y=559+(i//2)*28
                pygame.draw.circle(self.screen,STATUS_COLORS[key],(x+6,y+6),5)
                self._text(label,14,x+18,y,STATUS_COLORS[key])
        if card_id and card_id in self.game.cards:
            self._button(pygame.Rect(1103,686,316,40),'PEŁNY OPIS KARTY  [I]',accent=True,small=True)
        if self.game.phase=='mulligan':
            n=len(self.game.players[0].mulligan_selected)
            self._text(f'WYBRANO DO WYMIANY: {n}/3',16,1104,743,cfg.GOLD)
            self._button(pygame.Rect(1182,808,243,59),'ZATWIERDŹ MULLIGAN',accent=True)
        elif self.game.phase=='finished':
            self._button(pygame.Rect(1192,823,236,55),'NOWY MECZ',accent=True)
        else:
            self._text(f'RUNDA {self.game.round}',18,1104,743,cfg.GOLD)
            if self.game.active==0:
                self._text('TWOJA TURA',15,1104,773,cfg.GREEN)
            else:self._text('RUCH KOMPUTERA',15,1104,773,cfg.RED)
            if self.game.players[0].next_fast:
                self._text('NASTĘPNA KARTA: SZYBKI ATAK',13,1104,796,STATUS_COLORS['quick'])
            can=self.game.active==0 and not self.game.pending
            self._button(pygame.Rect(1201,816,221,52),'ZAKOŃCZ TURĘ',active=can,accent=can)
        self._button(pygame.Rect(1093,869,145,33),'NOWY MECZ  [R]',small=True)

    def _draw_header(self):
        self._text('AUCTION',34,106,22,(232,189,107))
        self._text('HAMMER',34,300,22,cfg.TEXT)
        self._text('SOLO  /  70 KART  /  BEZ AUKCJI',15,758,34,cfg.MUTED)
        self._text('MVP 0.9.3 · v17',14,1310,35,cfg.GOLD)

    def _draw_log(self):
        # Zdarzenia pokazujemy pomiędzy rzędami, nie na pasku HP przeciwnika.
        entries=self.game.events[-2:]
        y=367
        for s in entries:
            trimmed=s if len(s)<117 else s[:114]+'…'
            self._text(trimmed,12,118,y,cfg.MUTED)
            y+=16
        if self.last_error:
            self._text(self.last_error[:105],13,280,899,cfg.RED)

    def _draw_choices(self):
        """Highlight legal targets without hiding the battlefield or its labels."""
        pending = self.game.pending
        if pending is None or pending.owner != 0:
            return
        counts = {}
        for ch in pending.choices:
            if ch.target is not None:
                counts[ch.target] = counts.get(ch.target, 0) + 1
        for target, count in counts.items():
            rect = None
            if target.startswith('hero:'):
                rect = self.hero_rect(int(target.split(':')[1]))
            else:
                for player in self.game.players:
                    if target in player.board:
                        rect = self.slot_rect(player.idx, player.board.index(target))
                        break
            if rect is not None:
                pygame.draw.rect(self.screen, cfg.GOLD, rect.inflate(8, 8), 4, border_radius=13)

    def _draw_choice_sidebar(self):
        """A full-height, readable selector in the existing right sidebar."""
        pending = self.game.pending
        card = self.game.cards[pending.uid].definition
        self._text('WYBIERZ CEL / EFEKT',22,1104,106,cfg.GOLD)
        name = self.cards_view.clip(card.name,self.fonts[18],320)
        self._text(name,18,1104,149,FACTION_COLORS[card.faction])
        self._text(f'Aktywacja: {card.trigger}',14,1104,179,cfg.TEXT)
        self._text('ZDOLNOŚĆ',14,1104,211,cfg.GOLD)
        lines = self._wrap(card.effect,14,320)
        for i,line in enumerate(lines[:4]):
            self._text(line,14,1104,234+i*21,cfg.TEXT)
        if len(lines)>4:
            self._text('Pełny opis karty: naciśnij [I].',12,1104,320,cfg.MUTED)
        pygame.draw.line(self.screen,cfg.PANEL_BORDER,(1104,335),(1425,335),1)
        total = len(pending.choices)
        self._text(f'LEGALNE WYBORY: {total}',14,1104,338,cfg.GOLD)
        for index, rect in self.choice_bounds():
            choice = pending.choices[index]
            pygame.draw.rect(self.screen,(40,64,73),rect,border_radius=9)
            pygame.draw.rect(self.screen,cfg.HOVER if rect.collidepoint(self.mouse_pos())
                             else cfg.PANEL_BORDER,rect,2,border_radius=9)
            desc = choice.label.replace('  →  ', ' → ')
            fragments = self._wrap(desc,13,286)
            first = self.cards_view.clip(fragments[0],self.fonts[13],281)
            self._text(f'{index%self.CHOICES_PER_PAGE+1}. {first}',13,
                       rect.x+9,rect.y+(8 if len(fragments)>1 else 15))
            if len(fragments)>1:
                second = self.cards_view.clip(' '.join(fragments[1:]),self.fonts[13],290)
                self._text(second,13,rect.x+23,rect.y+26,cfg.MUTED)
        if self._choice_last_page():
            self._button(pygame.Rect(1102,802,150,37),'← WSTECZ',
                         active=self.choice_page>0,small=True)
            self._button(pygame.Rect(1274,802,150,37),'DALEJ →',
                         active=self.choice_page<self._choice_last_page(),small=True)
            self._text(f'Strona {self.choice_page+1}/{self._choice_last_page()+1}',
                       13,1260,847,cfg.MUTED,center=True)
        else:
            self._text('Wybierz z listy lub kliknij podświetlony cel.',
                       12,1104,816,cfg.MUTED)
        self._text('Wybór wymagany, gdy istnieje legalny cel.',
                   12,1104,879,cfg.MUTED)

    def _draw_details(self):
        uid=self.details_card
        if uid not in self.game.cards:return
        card=self.game.cards[uid];d=card.definition
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((1,5,10,226));self.screen.blit(shade,(0,0))
        box=pygame.Rect(146,94,1190,745)
        self._panel(box,(24,38,52),FACTION_COLORS[d.faction],18)
        pygame.draw.line(self.screen,(66,91,106),(489,180),(489,766),2)
        # Large card illustration and attributes.
        self._text('PODGLĄD KARTY',16,186,124,cfg.GOLD)
        self.cards_view.draw(self.screen,card,pygame.Rect(194,198,255,338),
                             unit=self.game.units.get(uid),selected=True,
                             statuses=active_statuses(self.game,uid) if uid in self.game.units else hand_grants(self.game,uid))
        self._text(f'{d.id}  ·  {d.faction}',18,194,557,FACTION_COLORS[d.faction])
        self._text(f'Aktywacja: {d.trigger}',18,194,588)
        self._text(f'Rodzina: {d.family}',18,194,619)
        u=self.game.units.get(uid)
        self._text(f'Poziom zdolności: +{u.ability_level if u else card.ability_level}',18,194,650,cfg.GOLD)
        if not u:
            self._text(f'Tury na ręce: {card.hand_turns}',18,194,681,cfg.MUTED)
        else:
            self._text(f'Pancerz: {u.armor}  ·  Tarcza: {u.shield}',16,194,681,cfg.MUTED)
        # Right-hand reading column; no ellipses or clipped card text.
        self._text(d.name,28,520,118,FACTION_COLORS[d.faction])
        self._text('ZDOLNOŚĆ',20,520,191,cfg.GOLD)
        lines=self._wrap(d.effect,22,760)
        y=232-self.details_scroll
        content_top=226;content_bottom=745
        for line in lines:
            if content_top<=y<=content_bottom-28:self._text(line,22,520,y)
            y+=31
        y+=28
        if content_top<=y<=content_bottom-26:self._text('ROZWÓJ ZDOLNOŚCI',20,520,y,cfg.GOLD)
        y+=42
        for line in self._wrap(d.scaling,20,760):
            if content_top<=y<=content_bottom-25:self._text(line,20,520,y,cfg.TEXT)
            y+=29
        y+=30
        if content_top<=y<=content_bottom-23:self._text('WZROST STATYSTYK NA RĘCE',18,520,y,cfg.GOLD)
        y+=31
        growth=f'+{d.growth_atk} ATK  /  +{d.growth_hp} MAX HP  po każdej własnej turze'
        if content_top<=y<=content_bottom-25:self._text(growth,18,520,y,cfg.TEXT)
        y+=47
        statuses=active_statuses(self.game,uid) if uid in self.game.units else hand_grants(self.game,uid)
        if statuses:
            if content_top<=y<=content_bottom-24:
                self._text(f'AKTYWNE EFEKTY / NADANE STATUSY ({len(statuses)})',18,520,y,cfg.GOLD)
            y+=37
            for st in statuses:
                if content_top<=y<=content_bottom-23:
                    self._text('●',18,523,y,st.color)
                    self._text(st.name,18,549,y,st.color)
                y+=26
                provenance=f'Źródło: {st.source}' if st.source else 'Źródło: własne / aktualny stan'
                text=st.detail+'  |  '+provenance
                for line in self._wrap(text,15,736):
                    if content_top<=y<=content_bottom-22:self._text(line,15,550,y,cfg.TEXT)
                    y+=22
                y+=13
        else:
            if content_top<=y<=content_bottom-25:self._text('AKTYWNE EFEKTY: brak',18,520,y,cfg.MUTED)
            y+=34
        self.details_maxscroll=max(0,y-705)
        self._text('Kółko myszy — przewiń opis i statusy',14,524,774,cfg.MUTED)
        self._button(pygame.Rect(1095,777,201,39),'ZAMKNIJ [I / ESC]',small=True)

    def _draw_gameover(self):
        if self.game.phase!='finished':return
        overlay=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        overlay.fill((0,0,0,160));self.screen.blit(overlay,(0,0))
        self._panel(pygame.Rect(332,279,810,290),(28,44,58),cfg.GOLD,16)
        self._text('ZWYCIĘSTWO!' if self.game.winner==0 else 'PORAŻKA',46,738,340,cfg.GREEN if self.game.winner==0 else cfg.RED,center=True)
        self._text(f'Wygrywa: {self.game.players[self.game.winner].name}',22,738,409,center=True)
        self._text('Naciśnij R, aby rozpocząć nowy mecz.',16,738,464,cfg.MUTED,center=True)
        self._button(pygame.Rect(1192,823,236,55),'NOWY MECZ',accent=True)

    def draw(self):
        self.screen.blit(self.bg,(0,0))
        self._draw_header()
        self._draw_board()
        self._draw_sidebar()
        self._draw_log()
        self._draw_choices()
        self._draw_gameover()
        self._draw_details()
        self._present()

    def run(self):
        running=True
        while running:
            for event in pygame.event.get():
                if not self.handle(event):running=False
            self.update()
            self.draw()
            self.clock.tick(cfg.FPS)
        pygame.quit()


def run():
    SoloApp().run()
