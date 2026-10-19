# Muzyka Fantasy Tavern w AuctionHammer

**Docelowy plik:** `assets/music/music_auctionhammer.mp3` (jeden album, około 48 minut).

Właściciel projektu potwierdził uzyskanie zgody na rozpowszechnianie
ścieżki dźwiękowej wraz z darmową grą. Nazwisko kompozytora, nazwa
wydawcy, pochodzenie albumu i zasady licencyjne są opisane w
[credits](../../docs/THIRD_PARTY_MUSIC.md), a credits można również
otworzyć z głównego menu gry.

## Publikacja dużego pliku na GitHubie

38,2 MB przekracza limit formularza GitHub w przeglądarce (25 MiB),
ale mieści się w limicie standardowego Git (100 MiB).

1. Zaktualizuj swój lokalny projekt: `git pull --ff-only`.
2. Skopiuj `music_auctionhammer.mp3` dokładnie do `assets/music/`.
3. Otwórz terminal w katalogu `AuctionHammer` i wykonaj:

```powershell
git add assets/music/music_auctionhammer.mp3
git commit -m "Add permitted PGN Music soundtrack"
git push origin main
```

Po udanym `git push` automatyczna kompilacja Windows skopiuje plik
do `AuctionHammer/assets/music/music_auctionhammer.mp3` w gotowej
paczce ZIP. Gracze nie muszą niczego pobierać osobno.

Nie zmieniaj nazwy pliku. Odtwarzacz zapętla **całą ścieżkę**, również
przy zmianie menu i pomiędzy meczami.

## Zgodność wsteczna

Odtwarzacz obsługuje również lokalny pełny album w nazwach
`fantasy_tavern_full.ogg`, `fantasy_tavern_full.mp3` i
`fantasy_tavern_full.wav`, albo wszystkie 13 ponumerowanych utworów.
Te dodatkowe pliki nie są automatycznie publikowane.

**Prawa do muzyki nie są przenoszone przez licencję MIT gry.**
Odpowiednie warunki zgody wydawcy należy zachować w dokumentacji projektu.
