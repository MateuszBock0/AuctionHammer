# AuctionHammer — katalog aukcyjny v4: stan integracji

**18.10.2026 · wersja robocza (DRAFT) · materiały referencyjne, nie aktywacja w silniku.**

## Co rzeczywiście działa

W `main` od MVP **0.9.21** istnieje fundament aukcji **v3**: co trzy pełne rundy generowane są trzy różne oferty spośród 12 archetypów, działa licytacja i przydział dwóch kart do rąk (po jednej dla gracza), ewolucja rzadkości, nagrody za zabicie oraz zapis i audyt. **Specjalne zdolności A001–A012 są nieaktywne** (`NIEAKTYWNA / PLANOWANA`). Zasada „brak silnika aukcji w repozytorium” w oryginalnym pakiecie v4 jest zatem nieaktualna; dotyczy niezintegrowanej logiki v4, nie podstawowego modułu aukcji.

## Zakres tej aktualizacji

W tej zmianie dodajemy **wyłącznie wersjonowane dane, dokumentację, arkusze i testy spójności danych**. Nie modyfikujemy `game/core/auction.py`, `game/core/auction_catalog.py`, `game/core/engine.py`, `VERSION.json`, podstawowego `data/GAME_MASTER.json` ani `data/cards_base_70.json`. Działająca rozgrywka nadal korzysta z katalogu v3 i nie wykonuje zdolności v4.

- Kanoniczna kopia źródłowa v4 (z nieaktualnym historycznym polem) pozostaje w przesłanym pakiecie ZIP; w `data/auction/KATALOG_AUKCYJNY_12_v4.json` skorygowano **wyłącznie opis stanu repozytorium** i dodano pole `auction_integration_scope`.
- Dla pięciu archetypów v4 proponuje inne startowe ATK/PŻ: **A002 3/8, A005 2/9, A007 2/9, A010 4/7 i A012 3/8**.
- W **rundzie zakupu R = 3, 6, 9, ...** v4 proponuje: `ATK(R) = ATK(3) + (R-3)/3`, `MAX_HP(R) = R+8-ATK(R)`. Każde kolejne trzy rundy aukcji dodają **+1 ATK / +2 PŻ**, lecz **egzemplarz nie rośnie po zakupie**.
- Na każdej aukcji są 3 oferty, a do graczy trafiają tylko 2 karty **na rękę**, po jednej na gracza; trzecia nie jest przydzielana. Normalne wystawienie z ręki nadal podlega limitowi **jednej karty na turę**. Przywołania zdolnościami to odrębne zdarzenia i nie mogą przekraczać pięciu pól.
- Ewolucja rzadkości po 3 i 6 kolejnych pełnych rundach od zakupu nie uruchamia ponownie zdolności „Przy wystawieniu”, nie zwiększa bazowych statystyk i nie przywraca zużytych zdolności.

## Co musi przejść osobną integrację przed aktywacją

1. Uzgodnienie reguł A002 (wybór celu aury), A004 (wywołanie „Przy wystawieniu” kopii i zabezpieczenia przed pętlą), A010 (kumulacja buffów) i A012 (kierunek kopiowania PŻ).
2. Adaptacja formuły statystyk do `game/core/auction_catalog.py` i testy 12 kart dla rund 3/6/9/12/120; brak wpływu na statystyki wcześniej zakupionych egzemplarzy.
3. Typowane zdolności A001–A012 w istniejącym systemie zdarzeń Game Master v19, w tym jednoczesne fale zgonów A011, prawa własności A001/A009, łańcuchy kopii i save/load.
4. Pełne testy automatyczne i manualne Pygame dla wszystkich **36 wariantów**, walidacja AI, audytu i zgodności zapisów v3 oraz uruchomienie CI Linux/Windows.
5. Osobne wydanie Windows po zatwierdzeniu działania silnika; żadnego automatycznego balansu bez rozegranych danych.

## Materiały

- `data/auction/KATALOG_AUKCYJNY_12_v4.json` — 12 archetypów × trzy wersje zdolności, propozycja statystyk.
- `docs/auction/KATALOG_AUKCYJNY_12_v4.md` — szczegółowe założenia pakietu (oryginalny tekst).
- `docs/auction/RAPORT_WERYFIKACJI_AUKCJI_v4.md` — wyniki 35 izolowanych testów i ograniczenia raportu.
- `reference/KARTY_AUKCYJNE_12_v4.xlsx` — arkusz źródłowy.
- `docs/GAME_MASTER_v20.md` oraz `data/reference/GAME_MASTER_v20.json` — pełne archiwalne snapshoty dokumentacji, **nie są bieżącymi plikami ładowanymi przez silnik**.
- `data/BALANCE_CHANGESET_v20.json`, `data/ZMIANY_KART_v20.csv` i `reference/KARTY_PODSTAWOWE_BALANS_v20.xlsx` — dane źródłowe balansu 16 kart wdrażanego osobno przez PR #21.

**Stan QA:** 35/35 testów *izolowanego narzędzia katalogu v4* (według załączonego raportu). Nie oznacza to przetestowania 36 zdolności w działającej grze. Niniejszy PR dodatkowo weryfikuje format i niezmienniki katalogu. Nie jest testem balansu PvP ani integracji efektów.
