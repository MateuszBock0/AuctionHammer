"""Pixel-safe text layout shared by cards, sidebars and auction windows.

The engine and card copy are untouched: layout may wrap or visibly elide text,
while full copy remains accessible via the relevant detailed view.
"""
from __future__ import annotations


def clip_pixels(text, font, width):
    """Return one line that never renders outside the supplied pixel width."""
    text=str(text)
    if width<=0:
        return ''
    if font.size(text)[0]<=width:
        return text
    marker='…'
    if font.size(marker)[0]>width:
        return ''
    lo,hi=0,len(text)
    while lo<hi:
        mid=(lo+hi+1)//2
        if font.size(text[:mid]+marker)[0]<=width:
            lo=mid
        else:
            hi=mid-1
    return text[:lo]+marker


def wrap_pixels(text, font, width, max_lines=None):
    """Wrap by measured glyph widths, including very long unbroken tokens.

    With max_lines, overflow is visibly indicated by an ellipsis. The returned
    lines fit the requested width regardless of DPI or local font metrics.
    Empty paragraphs keep their line break, and the function is read-only.
    """
    if width<=0 or (max_lines is not None and max_lines<=0):
        return ()
    result=[]
    for paragraph in str(text).split('\n'):
        if not paragraph.strip():
            result.append('')
            continue
        line=''
        for token in paragraph.split():
            candidate=(line+' '+token) if line else token
            if font.size(candidate)[0]<=width:
                line=candidate
                continue
            if line:
                result.append(line)
                line=''
            # Split even a token without whitespace (URLs, codes, rare words).
            rest=token
            while rest and font.size(rest)[0]>width:
                lo,hi=1,len(rest)
                while lo<hi:
                    mid=(lo+hi+1)//2
                    if font.size(rest[:mid])[0]<=width:
                        lo=mid
                    else:
                        hi=mid-1
                if font.size(rest[:lo])[0]>width:
                    # A viewport narrower than one glyph cannot fit it.
                    rest=rest[1:]
                    continue
                result.append(rest[:lo])
                rest=rest[lo:]
            line=rest
        if line:
            result.append(line)
    if max_lines is not None and len(result)>max_lines:
        result=result[:max_lines]
        last=result[-1]
        # Replace the last line with an explicitly shortened version.
        result[-1]=clip_pixels(last+'…',font,width)
        if result[-1] and not result[-1].endswith('…'):
            result[-1]=clip_pixels(result[-1]+'…',font,width)
    return tuple(clip_pixels(line,font,width) for line in result)
