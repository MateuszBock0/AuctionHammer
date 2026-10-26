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
