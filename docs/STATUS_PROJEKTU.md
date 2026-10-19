# AuctionHammer — status projektu

**Ostatnia aktualizacja dokumentacji:** 19 października 2026  
**Wersja aplikacji:** 0.9.39  
**Stan:** działające demo offline na Windows, tryb solo przeciw AI. Rozwój trwa.

## Zaimplementowane

- 70 kart podstawowych, wspólna pula początkowa, talie graczy, rozwój kart na ręce, 5 pól na stronę i walka z bohaterem o 100 PŻ.
- Aukcje co trzy pełne rundy: 17 unikalnych archetypów, 3 poziomy rzadkości (51 wariantów zdolności), zakup prawa pierwszego wyboru.
- Silnik reguł v23: dochód za puste pola po rozstrzygnięciu fal śmierci, efekty awaryjne wybranych kart, reguły A014/A015/A018.
- Przeciwnik komputerowy, zapis/wczytanie rozgrywki, pełna historia i archiwum zakończonych meczów, replaye i kontrola integralności.
- Polska wersja interfejsu, suwak aukcji, wizualizacja walczących kart, animacja utraty PŻ oraz zgonu; filtry trzech cech (Podwójny atak, Prowokacja, Tarcza).
- Opcjonalne odtwarzanie albumu muzycznego podczas gry.

**Ważne rozróżnienie:** `S34` (Chorąży Królewskiej Kompanii) jest kartą **podstawową** z efektem +1 ATK sąsiadowi albo −1 ATK wrogowi naprzeciwko. `A002` (Generał Oddziału Natarcia) jest kartą **aukcyjną**; jej podstawowa rzadkość daje +1 ATK jednostkom na obu planszach. Zakupione karty aukcyjne nie są tasowane do podstawowej puli.

## Stabilizacja 0.9.38

Dodana macierz 121 przypadków aktywacji (70 bazowych + 51 aukcyjnych), silniejsze niezmienniki dla lokalizacji kart i własności, testy atomowego odrzucania niedozwolonych akcji oraz wczytywania zapisu podczas wyborów. To kontrola integracyjna, nie pełny dowód wszystkich kombinacji zdolności. [Raport](ENGINE_STABILIZATION_0938.md).

## Testy i ograniczenia

W wydaniu 0.9.37 przeprowadzono 492 testy oraz dwie serie po 100 meczów (w tym kontrolę 100/100 pełnych replayów). Nie gwarantuje to bezbłędności każdej kombinacji efektów. Brak fizycznej walidacji odtwarzania audio i UI na wszystkich konfiguracjach Windows.

**Jeszcze niezaimplementowane:** tryb multiplayer online. Dodatkowe strategie licytacji AI wymagają odrębnej decyzji i testu A/B; nie są częścią obecnego stanu produkcyjnego.

## Dokumentacja i prawa

- [README](../README.md) — funkcje gry, instalacja, najważniejsze reguły i credits.
- [Game Master](../AUCTIONHAMMER_MASTER.md) i [aneks v23](GAME_MASTER_v23_ADDENDUM.md) — reguły mechaniczne.
- [Audyt v23](QA_V23_SECOND_PASS_20261019.md) — testy i znane ograniczenia.
- [Licencja MIT](../LICENSE) — autorskie oprogramowanie i własna dokumentacja.
- [Pełne przypisanie muzyki](THIRD_PARTY_MUSIC.md) — Alek Kaczan, PGN Music, album, 13 utworów i osobne informacje prawne.

Muzyka i materiały podmiotów trzecich nie stają się objęte MIT przez sam fakt użycia w AuctionHammer. Publiczna dokumentacja podaje credits i źródła, a nie treść odrębnych indywidualnych ustaleń.

## Etap 0.9.39 — nowe mecze

Rekompensata dla gracza wykonującego drugi ruch: na jego planszy pojawia się neutralny **Strażnik 5/5** zamiast 3 monet. Zajmuje pole, nie ma zdolności, nie atakuje w swojej pierwszej turze, po usunięciu znika bez powrotu do talii. Historyczne mecze zachowują +3 monety i oryginalne podpisy audytu. Interfejs zyskuje ochronę przed przypadkowym restartem/wyjściem, globalny resize, dwuwierszowe podpowiedzi i zachowanie stanu animacji podczas restartu. Szczegóły: [UIUX_0939_ACCEPTANCE.md](UIUX_0939_ACCEPTANCE.md).
