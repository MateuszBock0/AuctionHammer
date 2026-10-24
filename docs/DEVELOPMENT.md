# AuctionHammer — uruchamianie z kodu

Dla osób zainteresowanych kodem gry i testami. **Gracze Windows nie muszą wykonywać tych kroków:** wystarczy [gotowa paczka ZIP](https://github.com/MateuszBock0/AuctionHammer/releases/latest).

## Wymagania

- Python **3.12**.
- `pygame-ce` zgodne z `requirements.txt`.
- Windows lub środowisko zdolne uruchomić pygame-ce (CI testuje także Linux).

```bash
git clone https://github.com/MateuszBock0/AuctionHammer.git
cd AuctionHammer
python -m pip install -r requirements.txt
python -m game.main
```

## Testy

```bash
python -m tools.release_meta check
python -m unittest discover -s tests -v
python -m tools.check_fixed_board_0951 --games 20
```

Testy graficzne w CI uruchamiają Pygame z `SDL_VIDEODRIVER=dummy` i `SDL_AUDIODRIVER=dummy`. Osobne joby sprawdzają Windows, launcher PowerShell oraz odtwarzanie podpisanych audytów. Ręczne testy rzeczywistych DPI i wydania EXE pozostają osobną kontrolą.

## Gdzie szukać kodu?

| Obszar | Lokalizacja |
|---|---|
| Zasady gry, AI, aukcje, audyty | `game/core/` |
| Interfejs, karty, animacje, podpowiedzi | `game/ui/` |
| Definicje 70 kart, dane aukcji, metadane | `data/`, `VERSION.json` |
| Grafiki, muzyka | `assets/` |
| Testy regresyjne, symulacje | `tests/`, `tools/` |
| Historia zmian i zasady wydawania | `CHANGELOG.md`, `docs/RELEASE_PROCESS.md` |

Zmiana na ekranie UI nie powinna zmieniać mechaniki gry. Unikaj opierania się na nazwie karty, gdy silnik udostępnia jej stabilny identyfikator. Sprawdzaj zarówno działanie na aktualnej planszy pięciu pól, jak i kompatybilność istniejących zapisów, jeśli dotykasz logiki stanu.

[Zasady kontrybucji](../CONTRIBUTING.md) · [Wersjonowanie i publikacja](RELEASE_PROCESS.md)
