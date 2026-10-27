"""Generate real AuctionHammer highlights from a minimal gameplay command log.

This script contains neither the user's full signed audit nor the hidden state
snapshots. The seed and 208 commands reproduce the game's actual engine state.
"""
import base64
import json
import os
from pathlib import Path
import zlib


# Sanitized gameplay commands only: operation name + public arguments.
_COMMANDS = (
    "eNrVWcFuozAQ/RefOdiGBJNb1A/oStEeVlWEaMKmqAlEQLRaRfn3BdLddQljPMaQtLeo82w882be2HMmRRxvyYIJwecBCwLmkE12OETptiCLlzPJjmRBfiZpUryFh9N+n+yilDgkynf1/5nzsl475P3X9ff5cnE+IJu3LCvisCijvEzSXVgteozTIiqTTMJTh5zSpAx5OCPd6/zdMyyz3W4f/4eSFaN4jO+Z7DPHgyi/90Zg0Gi3/XEf/f60sCCq0Eok6DaL021YnnJpY719+Yw4afXRsjUp9llJFhS/evtjdQ/PyKD1orKMNu8tdzrN4ex6q+aMRXfdBANiJHRAmMMdCKZGjB1jF/QcsxDwJjIKD+qeLjpt6qIZviZbufAyhDV1fNTaArV2oLY+RkXRWyz+GSeyEyt5WH5/opQtaRUsDJJJSKjkt/jQa99mAkdlxlucZwuKyw0khjeEAz1lmk58kBnkZTj5uNIvrjKpxkvDm8ooxq6MuOhL9NXJmjb86fnbD9r8cR28KZe8QS1FOwYB06ngsKsaLmlLvXsXlWI0GLdoqPsSNc/qCBgRDAY+RJVacddmV2VFwjlqbRe1todae4YRfGoi23xJGSMmrcKXQ4Lp3aakUFerLuULmtR2bfczXAxTJxz0c+FQYk1rBxtkluXbOA9f4zjHFneJAxrVxrIe3Yipj2QWUmga/vayfmK23YcxtxrPH+DNg9EZtrYw8PUJiD+SMxUnpw3gNH0A6krckmo2+m3brRJHGN22KySba8qZG4wmZN6YlKyz5MvxWIorRGdv8KXNneQaBZwM5J3m9hDr+jNCIXQqnOVibt6ErHz4Fu3aeKBGd6w+Qwn9NfooXDNkGCchqVVN9sXD6Y83ugB5VUC5kQDVSMxzr8q+i57NwMIXOJrBgCE17+okk+evhlT95zcdfMhfd02xoU89XbWNTTPHG3ksp3Ye/PWmn6U90+WW99V67dfsbfqcJpCzASsctfLEN0FtnVVuMmvua6SLqK0q+4FT9OEjY2iwBJIHOqF4jOm75PExRoC67xjcfB7z4Uw72ThgWHcdojJu5nkQh9AwyxOQjrLXq8zqEGHcCe+1vvwB+EwmVw=="
)
SOURCE_VERSION = "0.9.103"
SELECTED = {51, 110, 162, 194, 201, 202, 206, 208}
EXPECTED_FAILED = {6, 80, 81, 82}
INITIAL_HASH = "ec39e79684fffb08c6ab1e5f2676aefa97ecf38b1a27be25676531e91f9878a1"
FINAL_HASH = "0548bc3e0c2dc19d0d991b1212636f68cc4c079bb3e715b42a577fd9a48d3200"


def main():
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    from game.core.audit import state_snapshot, digest
    from game.core.engine import Match
    from tools.native_trailer import NativeExporter

    data = json.loads(zlib.decompress(base64.b64decode(_COMMANDS)))
    game = Match(
        seed=data['seed'],
        audit_enabled=True,
        auctions_enabled=True,
        auction_catalog='v22',
        starting_compensation='choice_2_5_or_coins',
        fixed_board_slots=True,
        tavern_price_v2_enabled=True,
        tavern_scaled_damage_enabled=True,
    )
    actual_initial = digest(state_snapshot(game))
    if actual_initial != INITIAL_HASH:
        raise ValueError(f'Initial ruleset mismatch: {actual_initial}')
    output = Path('preview/AuctionHammer_EPICKIE_AKCJE_NATYWNY.mp4')
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter = NativeExporter({}, output, SELECTED, fps=24, pre=.42, post=1.75)
    try:
        for seq, cmd in enumerate(data['commands'], 1):
            name = cmd['op']
            args = cmd['args']
            kwargs = cmd['kwargs']
            event = {'seq':seq, 'operation':name, 'args':args, 'result':'ok'}
            if name=='attack' and seq in SELECTED:
                exporter.observe(game, event, 'before')
            failed = False
            try:
                getattr(game, name)(*args, **kwargs)
            except Exception:
                failed = True
                if seq not in EXPECTED_FAILED:
                    raise
            if failed != (seq in EXPECTED_FAILED):
                raise ValueError(f'Action {seq} diverged: failed={failed}')
            if name=='attack' and seq in SELECTED:
                exporter.observe(game, event, 'after')
        actual_final = digest(state_snapshot(game))
        if actual_final != FINAL_HASH:
            raise ValueError(f'Final ruleset mismatch: {actual_final}')
    except BaseException:
        exporter.abort()
        raise
    else:
        exporter.close()
    assert set(exporter.captured)==SELECTED
    print(f'RENDERED {output} ({output.stat().st_size} bytes) '
          f'from exact {SOURCE_VERSION} signed match: '
          f'{len(data["commands"])} commands; frames={exporter.total}')


if __name__ == '__main__':
    main()
