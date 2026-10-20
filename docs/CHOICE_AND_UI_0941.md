# AuctionHammer 0.9.41 — wybór drugiego gracza + selektywny pakiet UI/UX

## Źródła, aktualność i konflikt specyfikacji
- Podstawa: repozytorium `main` v0.9.39, niezmergowany PR #54 v0.9.40 i przesłany pakiet `AuctionHammer_UIUX_AUDYT_WDROZENIA_0_9_40(2).zip`.
- Pakiet analizował `main` SHA `a8428394`, więc jego zakaz zmiany silnika dotyczy **prac wyłącznie UI**. Bieżąca prośba użytkownika **osobno** autoryzuje wybór Chorąży 2/5 lub +3 monety; nie aktualizujemy aukcji.
- Nie nadpisujemy starego Game Master v14 ani danych kart; 70 kart podstawowych/51 zdolności aukcyjnych zostają niezmienione.

## Nowa reguła
- Drugi gracz, niezależnie od indeksu P0/P1, otrzymuje dokładnie **jeden wybór** w mulliganie:
  1. Chorąży 2 ATK / 5 PŻ, flavor „Chorąży zawsze zdąży.”, bez zdolności i Szybkiego ataku, zajmuje pole, znika po śmierci/zastąpieniu, **bez +3 monet**.
  2. +3 monety, **bez jednostki**.
- UI człowieka: przyciski i cyfry [1], [2], osobne potwierdzenie udokumentowane komendą. AI wybiera deterministycznie na podstawie tylko własnych kart. Tylko po wyborze drugi gracz może zatwierdzić mulligan.
- `starting_compensation='choice_2_5_or_coins'`, audyt schema **4** podpisuje wybór przed i po decyzji.
- Trzy tryby archiwalne: `coins`, `unit_5_5`, `unit_3_5`; żaden z ich początkowych snapshotów ani reguł nie jest zmieniony. Starsze savy bez pola trybu defaultują do `coins`.

## Uwagi z przesłanej paczki
- **A1 wdrożone:** `ImageAssets.fit_art` zachowuje proporcje grafiki, tryb cover/contain z focus, cache i ostrzeżenia o brakującym/uszkodzonym pliku; bez zmian istniejących 7 PNG.
- **A2 wdrożone:** na 125×195 hand art statusy są na zewnętrznej krawędzi, a nie na emblemacie i pasku postępu; planszowe filtry Tarcza > Prowokacja > Podwójny atak zachowane.
- **B1 wdrożone:** modal I ma [G] ilustracja/karta i klikany przełącznik; pełny kadr istniejących PNG przez contain oraz fallback proceduralny; nie duplikuje danych z katalogu.
- **B2 wdrożone:** w szczegółach porównanie ATK BAZA → TERAZ, MAX PŻ BAZA → TERAZ, oddzielone bieżące PŻ; brak fałszywego skalowania u tokena SUM.
- **B3 istnieje:** przewijalna lista statusów z detalem, czasem i źródłem; wymaga manualnego sprawdzenia przy dużej liczbie statusów.
- **C wdrożone:** etykieta gry 0.9.41/ruleset v23 i usunięty duplikat CTA Nowy mecz z panelu za nakładką zakończenia; skróty H/P/M dostępne również przed wyborem rekompensaty.
- **D niewdrożone celowo:** podgląd liczbowej walki na hover wymagałby pełnej izolacji wszelkich wyborów `Pending`, fal śmierci, RNG i audytu; bez dowodu dokładności nie pokazujemy prognozowanego PŻ.
- Nie zmieniono żadnego assetu, plików `assets/`, kodu aukcji, muzyki ani danych kart.

## Rejestr QA (przed finalnym odbiorem)
| Grupa | Status | Dowód / ograniczenie |
| --- | --- | --- |
| A: 7 PNG + 63 proceduralne, bez deformacji | ZAUTOMATYZOWANE | testy `tests/test_second_player_choice_0941.py` + istniejący renderer; ręczna ocena kadru pozostaje NOT TESTED |
| A: emblem/hand grants/progress | ZAUTOMATYZOWANE | test pasów statusowych na brzegu karty; Windows 100/125/150% DPI NOT TESTED |
| B: zoom G i poprawne statystyki | ZAUTOMATYZOWANE | test read-only snapshot; przewijanie dużej listy efektów sprawdzane istniejącymi testami |
| C: wersja, CTA, globalne skróty | ZAUTOMATYZOWANE | CI unittest i testy interfejsu; fizyczna mysz NOT TESTED |
| Silnik: trzy historyczne tryby + wybór | ZAUTOMATYZOWANE | save/load, audyt/replay i 1000 pełnych meczów po PASS workflow |
| D: liczbowy podgląd walki | BLOCKED | Brak gwarancji dokładności w stanach wymagających wyboru |
| Prawdziwy Windows, audio, DPI, rollback aktualizatora, muzyka | NOT TESTED / W OSOBNYM ZADANIU | wymagają odbioru odrębnego od 0.9.41 |

## Badanie balansu
Trzy warianty na tych samych seedach v23: stare +3 monety, wymuszony Chorąży 2/5 oraz AI wybierające samo. Zapis CSV/JSON i Wilson + sparowany McNemar: `tools/balance_choice_0941.py`. Wyniki AI-vs-AI nie dowodzą wyrównania PvP. Starsze 75,5–77% pierwszego pochodziło z v22 i nie jest porównaniem na identycznej rewizji.

## Wymagania do scalenia
- Zielone pełne testy, w tym 1000/1000 podpisanych replayów i sparowane A/B bez błędów.
- Artefakt z obrazami wygenerowanymi przez `tools/render_minimal_fantasy_preview.py`.
- Ręczny Windows test pozostaje oznaczony NOT TESTED — nie oznaczać go PASS bez przeprowadzenia.
- Kategorycznie nie usuwać plików źródłowych PNG ani nie pobierać grafik z innych gier.

### Korekta heurystyki AI po pierwszym badaniu A/B
Bazowe karty mają ATK 1–4. Początkowy próg AI `>=5` był niemożliwy do osiągnięcia — AI zawsze wybierał 2/5 (400/400). Poprawiono go do `>=4`, odpowiadającego mocnej początkowej ręce, a do testów dodano wymóg faktycznego wykorzystania **obu** opcji przez AI. Pierwotne A/B zmuszonego 2/5 pozostaje ważne, ale wynik adaptacyjny dla starej heurystyki został unieważniony i musi zostać policzony ponownie.
