# Natywny trailer AuctionHammer (Pygame)

Ten eksporter **nie tworzy własnej planszy ani grafik**. Odtwarza oryginalny,
podpisany audyt meczu przez `game.core.engine.Match` (z weryfikacją SHA-256),
a obraz każdej wybranej akcji generuje przez **`SoloApp.draw()`** oraz
**`CombatVisuals.sync()`** — te same funkcje, które działają w prawdziwej grze.
Również muzyka pochodzi z `assets/music/music_auctionhammer.mp3`, jeśli plik
jest obecny.

## Uruchomienie na komputerze z pełnym repozytorium gry

W katalogu głównym AuctionHammer:

```powershell
py -m pip install -r requirements.txt
# FFmpeg musi być zainstalowany i dostępny jako ffmpeg w PATH.
py -m tools.native_trailer "AuctionHammer-OSTATNI-MECZ.json" "AuctionHammer-NATYWNY-TRAILER.mp4"
```

Dla przesłanego audytu v0.9.103, kiedy chcesz uzyskać 8 konkretnych
uderzeń w kolejności z tego samego meczu:

```powershell
py -m tools.native_trailer "AuctionHammer-OSTATNI-MECZ(2).json" "AuctionHammer-NATYWNY-TRAILER.mp4" --seq 51 99 110 137 158 201 206 208
```

Opcje: `--fps 30`, `--highlights 7` (ranking automatyczny),
`--seq ...` (jawny wybór akcji `attack` po numerach z audytu).

## Założenia jakości

- Obraz pochodzi z oryginalnego canvasu gry (1480 × 980), bez skalowania
  sprite'ów do innego stylu.
- Podczas cięć krótkie wygaszenie przechodzi między autentycznymi stanami.
- Klip zawiera klatki PRZED atakiem i PO rozstrzygnięciu; nie jest to
  fikcyjna animacja ruchu kart ani filmowanie pliku HTML.
- Silnik podczas eksportu odtwarza i weryfikuje **wszystkie** komendy, choć
  eksportuje tylko wybrane momenty. Zmiany zasad względem nagranej wersji,
  które uniemożliwią odtworzenie, kończą eksport błędem, bez fałszowania historii.
- Format MP4: H.264, yuv420p; jeśli ścieżka muzyczna gry istnieje: AAC.

**Wymagania:** pełne repozytorium (nie tylko audyt JSON), Python 3.12+,
pygame-ce z `requirements.txt` oraz `ffmpeg`.

To narzędzie nie jest jeszcze opublikowanym gotowym filmem; aby uzyskać MP4,
należy uruchomić je w środowisku dysponującym aktualnymi assetami gry.
