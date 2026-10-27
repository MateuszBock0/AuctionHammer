"""CI smoke test: real engine + signed replay + original pygame + ffmpeg."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from game.core.ai import ComputerOpponent
from game.core.audit import make_report, verify_replay
from game.core.engine import Match
from tools.native_trailer import NativeExporter, default_highlights


def main():
    # Established seed from the engine's full-match acceptance test.
    game = Match(1706, audit_enabled=True)
    agents = (ComputerOpponent(0), ComputerOpponent(1))
    for _ in range(1500):
        if game.phase == 'finished':
            break
        if game.phase == 'mulligan':
            for agent in agents:
                agent.step(game)
        elif game.pending is not None:
            agents[game.pending.owner].step(game)
        else:
            agents[game.active].step(game)
    assert game.phase == 'finished', 'AI demonstration failed to finish'

    payload = make_report(game)['payload']
    selected = default_highlights(payload, limit=4)
    assert selected, 'No real combat action to render'
    output = Path('preview/AuctionHammer-NATYWNE-AKCJE-demo.mp4')
    output.parent.mkdir(exist_ok=True)
    exporter = NativeExporter(payload, output, selected, fps=12, pre=.25, post=.8)
    try:
        assert verify_replay(
            payload, lambda seed, **kw: Match(seed, audit_enabled=True, **kw),
            frame_observer=exporter.observe
        )
    finally:
        exporter.close()
    assert output.stat().st_size > 100_000, 'Rendered MP4 is empty'
    print(f'PASS: {output} | {output.stat().st_size} bytes | real actions {selected}')


if __name__ == '__main__':
    main()
