"""Pure geometry for aspect-ratio-preserving pygame presentation.

Coordinates in the engine and canvas stay in the same logical space even when
Windows scales the resizable application window. No pygame dependency here.
"""
from __future__ import annotations


def fitted_viewport(window_size: tuple[int,int], logical_size: tuple[int,int]) -> tuple[int,int,int,int]:
    ww,wh=window_size
    lw,lh=logical_size
    if ww<=0 or wh<=0 or lw<=0 or lh<=0:
        raise ValueError('Window and logical sizes must be positive')
    factor=min(ww/lw,wh/lh)
    width=max(1,round(lw*factor))
    height=max(1,round(lh*factor))
    return ((ww-width)//2,(wh-height)//2,width,height)


def window_to_canvas(point: tuple[int,int],viewport: tuple[int,int,int,int],logical_size: tuple[int,int]) -> tuple[int,int] | None:
    x,y,w,h=viewport
    px,py=point
    if not(x<=px<x+w and y<=py<y+h):return None
    lw,lh=logical_size
    return (min(lw-1,int((px-x)*lw/w)), min(lh-1,int((py-y)*lh/h)))

def preferred_window_size(
    desktop_size: tuple[int, int],
    logical_size: tuple[int, int],
) -> tuple[int, int]:
    """Fit the opening window within the usable desktop, including a taskbar margin.

    Windows can expose a 1920x1080 display as about 1536x864 logical pixels
    at 125% scaling. Requesting the full 1480x920 canvas as a window would
    hide its bottom controls. Keep the canvas unchanged and scale its viewport.
    The window itself has the same aspect ratio, avoiding wasted black bars.
    """
    dw, dh = desktop_size
    lw, lh = logical_size
    if min(dw, dh, lw, lh) <= 0:
        raise ValueError("Desktop and logical canvas sizes must be positive")

    margin_w = min(96, max(32, dw // 18))
    margin_h = min(120, max(72, dh // 9))
    usable_w = max(1, dw - margin_w)
    usable_h = max(1, dh - margin_h)
    factor = min(1.0, usable_w / lw, usable_h / lh)
    return max(1, int(lw * factor)), max(1, int(lh * factor))


def canvas_to_window(
    point: tuple[int, int],
    viewport: tuple[int, int, int, int],
    logical_size: tuple[int, int],
) -> tuple[int, int]:
    """Inverse of window_to_canvas, useful for verifying resized hitboxes."""
    x, y, width, height = viewport
    lw, lh = logical_size
    px, py = point
    if width <= 0 or height <= 0 or lw <= 0 or lh <= 0:
        raise ValueError("Canvas and viewport sizes must be positive")
    if not (0 <= px < lw and 0 <= py < lh):
        raise ValueError("Point lies outside the canvas")
    return (x + int((px + 0.5) * width / lw),
            y + int((py + 0.5) * height / lh))
