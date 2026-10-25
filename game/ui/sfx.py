"""Quiet, procedural UI sound effects. Purely cosmetic; game state untouched.

No third-party samples: deterministic short PCM waveforms generated into RIFF
in memory. Disabled automatically when SDL audio is unavailable.
"""
from __future__ import annotations

from collections import deque
from io import BytesIO
from math import exp, pi, sin
from pathlib import Path
from random import Random
from struct import pack
import json
import wave

import pygame

from game.core.persistence import save_path

DEFAULT_MUSIC = 0.40
DEFAULT_SFX = 0.10
STEPS = tuple(x / 10 for x in range(11))
AUDIO_SETTINGS = save_path().parent / 'audio_settings.json'

# Duration, base frequency, spectral/noise balance, downward sweep, seed.
_PRESETS = {
    'card_pick': (0.21, 640, .21, .13, 1),
    'card_place': (0.24, 220, .61, .19, 2),
    'attack_swoosh': (0.28, 390, .27, .77, 3),
    'hit': (0.30, 140, .44, .55, 4),
    'shield_armor': (0.41, 590, .78, .30, 5),
    'ability': (0.53, 760, .88, .03, 6),
    'death': (0.40, 115, .69, .82, 7),
    'auction_gavel': (0.35, 275, .60, .28, 8),
}
_RATE = 22050


def _level(value,default):
    if type(value) not in (int,float) or not 0 <= value <= 1:
        return default
    return round(value,2)


def load_levels(path: Path | None = None) -> dict[str,float]:
    """Settings are separate from savegames/replays and have safe defaults."""
    path = Path(path) if path is not None else AUDIO_SETTINGS
    try:
        values = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(values,dict):
            raise ValueError('invalid audio settings')
    except (OSError,ValueError,UnicodeError,TypeError):
        values={}
    return {'music': _level(values.get('music'),DEFAULT_MUSIC),
            'sfx': _level(values.get('sfx'),DEFAULT_SFX)}


def save_levels(levels:dict[str,float],path: Path | None = None) -> bool:
    path = Path(path) if path is not None else AUDIO_SETTINGS
    data={'music':_level(levels.get('music'),DEFAULT_MUSIC),
          'sfx':_level(levels.get('sfx'),DEFAULT_SFX)}
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_name(path.name+'.tmp')
        temporary.write_text(json.dumps(data,sort_keys=True),encoding='utf-8')
        temporary.replace(path)
        return True
    except (OSError,ValueError,TypeError):
        return False


def synthesize_wav(kind: str) -> bytes:
    """Create a small, <= -19 dBFS mono 16-bit WAV, no external asset needed."""
    duration,hz,tonal,sweep,seed = _PRESETS[kind]
    rng=Random(seed)
    samples=int(_RATE*duration)
    filtered=0.
    raw=bytearray()
    for i in range(samples):
        u=i/max(1,samples-1)
        # No click at either end. Short attack + restrained decay.
        envelope=min(1.,u*90)*(1-u)**2.35
        white=rng.uniform(-1,1)
        filtered=filtered*.83+white*.17
        phase=2*pi*hz*duration*(u-.5*sweep*u*u)
        ring=sin(phase)+.19*sin(phase*2.01)
        wave_value=tonal*ring/1.19+(1-tonal)*filtered*1.4
        raw+=pack('<h',int(max(-3600,min(3600,3600*envelope*wave_value))))
    memory=BytesIO()
    with wave.open(memory,'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(_RATE)
        wav.writeframes(raw)
    return memory.getvalue()


class QuietSFX:
    """Low-volume, capped SFX from committed Match/audit events only."""

    MIN_GAP_MS=145

    def __init__(self,volume:float=DEFAULT_SFX):
        self.volume=_level(volume,DEFAULT_SFX)
        self.error=None
        self.sounds={}
        self.last_played={}
        self.last_global=-100000
        self.queue=deque(maxlen=5)
        self._game=None
        self._actions_seen=0
        self._pulse_ids=set()
        if self.volume<=0:
            return
        self._ensure_loaded()

    def _ensure_loaded(self):
        if self.sounds or self.error is not None:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name in _PRESETS:
                sound=pygame.mixer.Sound(file=BytesIO(synthesize_wav(name)))
                sound.set_volume(self.volume)
                self.sounds[name]=sound
        except (OSError,pygame.error) as exc:
            self.sounds.clear()
            self.error=str(exc)

    def set_volume(self,level:float):
        self.volume=_level(level,DEFAULT_SFX)
        if self.volume>0:
            self._ensure_loaded()
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def reset(self,game=None):
        self._game=game
        self._actions_seen=len(getattr(game,'audit_actions',()) or ())
        self._pulse_ids=set()
        self.queue.clear()

    def enqueue(self,kind:str,now:int):
        if self.volume<=0 or kind not in _PRESETS:
            return
        if self.last_played.get(kind,-100000)+160>now:
            return
        if self.queue and self.queue[-1][0]==kind:
            return
        self.queue.append((kind,now))

    def observe(self,game,visuals,now:int,allowed=True):
        """Consume authoritative actions and confirmed visual pulses.

        Even if a modal is open or sound muted, advance indices so old events
        cannot suddenly play when a menu is dismissed or volume is restored.
        """
        if game is not self._game:
            self.reset(game)
            self._pulse_ids={id(p) for p in getattr(visuals,'pulses',())}
            return
        actions=getattr(game,'audit_actions',()) or ()
        if self._actions_seen>len(actions):
            self._actions_seen=0
        fresh=actions[self._actions_seen:]
        self._actions_seen=len(actions)
        current={id(p) for p in getattr(visuals,'pulses',())}
        new=[p for p in getattr(visuals,'pulses',()) if id(p) not in self._pulse_ids]
        self._pulse_ids=current
        if not allowed or self.volume<=0:
            self.queue.clear()
            return
        for action in fresh:
            if action.get('result')!='ok':
                continue
            kind={'play':'card_place','attack':'attack_swoosh',
                  'choose':'ability','auction_pick':'auction_gavel'}.get(
                      action.get('operation'))
            if kind:
                self.enqueue(kind,now)
        # One actual impact cue per committed batch, not eight simultaneous
        # effects for damage + shield + poison on the same resolution frame.
        priority=('death','shield','armor','damage','stun','poison','regen','special')
        present={p.kind for p in new}
        first=next((kind for kind in priority if kind in present),None)
        if first:
            sound=('death' if first=='death' else
                   'shield_armor' if first in ('shield','armor') else
                   'hit' if first=='damage' else 'ability')
            self.enqueue(sound,now)
        self.tick(now)

    def tick(self,now:int):
        if self.volume<=0 or not self.queue:
            return
        if now-self.last_global<self.MIN_GAP_MS:
            return
        # Expired feedback should not lag behind the action.
        while self.queue and now-self.queue[0][1]>850:
            self.queue.popleft()
        if not self.queue:
            return
        self._ensure_loaded()
        if not self.sounds:
            self.queue.clear()
            return
        kind,_=self.queue.popleft()
        try:
            self.sounds[kind].play()
        except pygame.error:
            return
        self.last_global=now
        self.last_played[kind]=now
