"""Tiny frame-only beer-pour effect, isolated from cards and hitboxes.

All positions are derived from pygame ticks and one timestamp. No mutable
gameplay state, surfaces, textures, additional loops or sleeps.
"""


def beer_fx_state(now_ms,started_ms,enabled=True):
    """Return (fill_progress, torch_offset_px, pouring) for a buy animation."""
    if not enabled or started_ms is None or now_ms<started_ms:
        return 1.0,0,False
    age=now_ms-started_ms
    if age>=800:
        return 1.0,0,False
    fraction=min(1.0,age/600.0)
    # Discrete pixel-art sway is for TORCHES ONLY. Cards and their hitboxes
    # remain physically and visually fixed.
    sway=(0,1,2,1,0,-1,-2,-1)[min(7,age//100)]
    return fraction,sway,age<600


def beer_overflow_state(now_ms,started_ms,enabled=True):
    """Fades a shared decorative fire/splash after the mug is full."""
    if not enabled or started_ms is None or now_ms<started_ms:
        return 0.0
    age=now_ms-started_ms
    if age<600 or age>=1050:
        return 0.0
    return 1.0-(age-600)/450.0


# Stable, four-frame pixel animation: 130ms per frame, no RNG/surfaces.
# (horizontal sway, vertical offset, flame height change), in pixels.
_CANDLE_FRAMES=((0,0,0),(-1,0,1),(0,-1,0),(1,0,-1))


def candle_frame(now_ms,enabled=True,phase=0):
    """Pure loop: two staggered candle wicks move at most one pixel.

    Turning animations off yields one stable frame independently of time.
    This has no dependency on gameplay or which player bought beer.
    """
    if not enabled:
        return _CANDLE_FRAMES[0]
    return _CANDLE_FRAMES[(max(0,now_ms)//130+phase)%4]


def board_spill_timeline(now_ms,started_ms,enabled=True):
    """Pure staged cosmetic sequence after a verified paid beer order.

    0..600ms mug fills, 600..930ms tips, 700..1300ms beer crosses the frame,
    950..2100ms it catches fire and dies down into embers. Both sides reuse
    ONE timestamp: no new rule, combat RNG, additional damage or saved state.
    Returns (tilt, pour, burn), all in [0,1].
    """
    if not enabled or started_ms is None or now_ms<started_ms:
        return 0.0,0.0,0.0
    age=now_ms-started_ms
    if age>=2150:
        return 0.0,0.0,0.0
    tilt=min(1.0,max(0.0,(age-600)/240))
    if age>1260:
        tilt*=max(0.0,(1590-age)/330)
    pour=(min(1.0,max(0.0,(age-690)/150))
          * min(1.0,max(0.0,(1390-age)/290)))
    burn=(min(1.0,max(0.0,(age-950)/180))
          * min(1.0,max(0.0,(2150-age)/850)))
    return tilt,pour,burn


def slot_flame_strength(remaining_turns,now_ms,started_ms,enabled,
                        owner,slot):
    """Visible intensity of one card-position ember frame, never game state.

    Global 3-turn brawl counter is the *only* condition for ongoing fire.
    Immediately after a paid mug, flame spreads from the rightmost slot of
    both rows across the board. Loading a saved active match shows the steady
    state, because the purchase timestamp is intentionally not persisted.
    Every purchase restarts the short ignition wave without extending rules.
    """
    if not enabled or remaining_turns<=0 or owner not in (0,1):
        return 0.0
    if not 0<=slot<5:
        return 0.0
    if started_ms is None:
        return 1.0
    age=now_ms-started_ms
    if age<0:
        return 0.0
    # The first flames start after the purchased beer hits the board.
    # Spread over all 10 positions in ~0.7 seconds, right -> left.
    ignition=935+(4-slot)*155+owner*45
    return min(1.0,max(0.0,(age-ignition)/175.0))
