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
