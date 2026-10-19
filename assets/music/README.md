# Muzyka Fantasy Tavern w AuctionHammer

**Docelowy plik:** `assets/music/music_auctionhammer.mp3` (jeden album, około 48 minut).

Właściciel projektu potwierdził uzyskanie zgody na rozpowszechnianie
ścieżki dźwiękowej wraz z darmową grą. Nazwisko kompozytora, nazwa
wydawcy, pochodzenie albumu i zasady licencyjne są opisane w
[credits](../../docs/THIRD_PARTY_MUSIC.md), a credits można również
otworzyć z głównego menu gry.

## Stan aktualny i weryfikacja

Plik `assets/music/music_auctionhammer.mp3` jest już śledzony przez Git
i automatycznie umieszczany w paczce Windows w `AuctionHammer/assets/music/`.
Nie należy wykonywać instrukcji ponownego dodawania tego samego pliku.

Odtwarzacz `game/ui/music.py` używa pojedynczego pełnego albumu w pętli,
z głośnością początkową 30%. Utwór **nie powinien zaczynać się od nowa**
przy wejściu do menu lub rozpoczęciu następnego meczu. Brak urządzenia audio
nie może przerywać działania gry; szczegóły w `docs/THIRD_PARTY_MUSIC.md`.

Można uruchomić test bez realnych głośników:
`SDL_AUDIODRIVER=dummy python -m unittest tests.test_music_live_asset_v23`.
Test sprawdza, czy włączony do repozytorium MP3 otwiera się przez mixer SDL,
odtwarza i może zostać zatrzymany.

## Zgodność wsteczna

Odtwarzacz obsługuje również lokalny pełny album w nazwach
`fantasy_tavern_full.ogg`, `fantasy_tavern_full.mp3` i
`fantasy_tavern_full.wav`, albo wszystkie 13 ponumerowanych utworów.
Te dodatkowe pliki nie są automatycznie publikowane.

**Prawa do muzyki nie są przenoszone przez licencję MIT gry.**
Odpowiednie warunki zgody wydawcy należy zachować w dokumentacji projektu.
