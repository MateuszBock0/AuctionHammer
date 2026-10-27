"""Export real AuctionHammer gameplay highlights via the original pygame renderer.

Usage from repository root:
  python -m tools.native_trailer "AuctionHammer-OSTATNI-MECZ.json" trailer.mp4

Every frame is drawn by SoloApp.draw() from signed Match audit actions,
not invented graphics or a restaging of event-log text.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch


def default_highlights(payload, limit=7):
    """Choose completed, high-impact attack commands from the signed journal."""
    import re

    journal = {e['seq']: e['text'] for e in payload['event_journal']}
    ranked = []
    for action in payload['actions']:
        if action['operation'] != 'attack' or action['result'] != 'ok':
            continue
        messages = [journal[i] for i in range(action['event_seq_start'],
                                              action['event_seq_end'] + 1)
                    if i in journal]
        damages = [int(m.group(1)) for text in messages
                   for m in re.finditer(r'otrzymuje (\\d+) obrażeń w PŻ', text)]
        deaths = sum(text.startswith('Zgon ') for text in messages)
        finisher = any('KONIEC MECZU' in text for text in messages)
        if damages:
            score = max(damages) * 1.5 + deaths * 6 + (50 if finisher else 0)
            ranked.append((score, action['seq']))
    top = {seq for _, seq in sorted(ranked, reverse=True)[:limit]}
    return sorted(top)


class NativeExporter:
    def __init__(self, payload, output, seqs, fps=30, pre=0.4, post=1.35):
        import pygame
        from game.ui.app import SoloApp
        from game.ui.combat_visuals import CombatVisuals

        self.pg = pygame
        self.CombatVisuals = CombatVisuals
        self.app = SoloApp(start_in_menu=False)
        self.app.menu_open = False
        self.app.animations_enabled = True
        self.seqs = set(seqs)
        self.fps = fps
        self.pre_frames = max(1, round(fps * pre))
        self.post_frames = max(1, round(fps * post))
        self.ms = 4000
        self.captured = []
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        width, height = self.app.screen.get_size()
        self.size = width, height
        music = Path(__file__).resolve().parents[1] / 'assets' / 'music' / 'music_auctionhammer.mp3'
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{height}',
               '-r', str(fps), '-i', '-']
        if music.is_file():
            cmd += ['-stream_loop', '-1', '-i', str(music),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac',
                    '-b:a', '160k', '-shortest']
        else:
            cmd += ['-an']
        cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(self.output)]
        self.encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.total = 0

    def frames(self, n, fade_in=False, fade_out=False):
        pg = self.pg
        for i in range(n):
            with patch.object(pg.time, 'get_ticks', return_value=self.ms):
                self.app.draw()  # Original native UI and native combat animation.
            frame = self.app.screen.copy()
            if fade_in and i < min(7, n):
                overlay = pg.Surface(self.size)
                overlay.fill((0, 0, 0))
                overlay.set_alpha(round(255 * (1 - i / min(7, n))))
                frame.blit(overlay, (0, 0))
            if fade_out and i >= max(0, n - 7):
                overlay = pg.Surface(self.size)
                overlay.fill((0, 0, 0))
                overlay.set_alpha(round(255 * (i - (n - 7)) / 7))
                frame.blit(overlay, (0, 0))
            self.encoder.stdin.write(pg.image.tobytes(frame, 'RGB'))
            self.total += 1
            self.ms += round(1000 / self.fps)

    def observe(self, game, action, when):
        if action['seq'] not in self.seqs:
            return
        if action['operation'] != 'attack' or action['result'] != 'ok':
            return
        app = self.app
        app.game = game
        app.replay_index = None
        app.history_open = False
        app.menu_open = False
        app.confirm_action = None
        app.details_card = None
        attacker = action['args'][0] if action['args'] else None
        app.selected = attacker if attacker in game.players[0].board else None
        if when == 'before':
            app.combat_visuals = self.CombatVisuals()
            app.combat_visuals.sync(game, app.slot_rect, app.hero_rect, self.ms)
            app.ability_feedback.reset(game)
            self.frames(self.pre_frames, fade_in=True)
        else:
            app.combat_visuals.sync(game, app.slot_rect, app.hero_rect, self.ms)
            self.frames(self.post_frames, fade_out=True)
            self.captured.append(action['seq'])

    def close(self):
        if self.encoder.stdin:
            self.encoder.stdin.close()
        result = self.encoder.wait()
        self.pg.quit()
        if result:
            raise RuntimeError(f'FFmpeg exited with code {result}')
        if not self.captured:
            self.output.unlink(missing_ok=True)
            raise RuntimeError('No selected actions were recorded')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Native AuctionHammer video from signed match audit')
    parser.add_argument('audit', type=Path, help='Original JSON match audit')
    parser.add_argument('output', type=Path, help='Output MP4')
    parser.add_argument('--seq', type=int, nargs='*', default=None,
                        help='Attack command IDs; automatic selection if omitted')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--highlights', type=int, default=7)
    args = parser.parse_args(argv)
    if args.fps < 1 or args.fps > 60:
        parser.error('FPS must be in 1..60')
    if shutil.which('ffmpeg') is None:
        parser.error('FFmpeg must be in PATH')
    from game.core.audit import read_report, verify_replay
    from game.core.engine import Match
    payload = read_report(args.audit)
    selected = args.seq if args.seq is not None else default_highlights(payload, args.highlights)
    valid = {a['seq'] for a in payload['actions']
             if a['operation'] == 'attack' and a['result'] == 'ok'}
    if not selected or any(seq not in valid for seq in selected):
        parser.error('No valid attack actions to export')
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    exporter = NativeExporter(payload, args.output, selected, fps=args.fps)
    try:
        verify_replay(payload, Match, frame_observer=exporter.observe)
    finally:
        exporter.close()
    print(f'Created {args.output}: {exporter.total} frames, actions {exporter.captured}')


if __name__ == '__main__':
    main()
