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
    # Use the public deterministic engine to produce an actual finished match.
    # Some seeded AI games end without combat, so require a confirmed attack.
    selected = []
    payload = None
    for seed in range(1706, 1722):
        game = Match(seed, audit_enabled=True)
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
        if game.phase != 'finished':
            continue
        payload = make_report(game)['payload']
        selected = default_highlights(payload, limit=4)
        if selected:
            break
    assert selected, 'No committed attack found across the seeded test matches'
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
