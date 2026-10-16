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
