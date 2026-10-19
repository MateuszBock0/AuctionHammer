# AuctionHammer — druga kontrola wersji v23 / 0.9.36 → 0.9.37

**Data:** 19.10.2026  
**Źródło wymagań:** użytkownika `AuctionHammer_v23_SPECYFIKACJA_I_PLAN(2).zip`: 14 decyzji, 39 przypadków testowych (T-001…T-039), archiwum ze zgodnymi sumami SHA256.  
**Punkt odniesienia kodu:** release 0.9.36, commit `a60ac8322af7d70fcaa4574c41c0d8d7878159f8`.

## 1. Weryfikacja gotowego wydania 0.9.36

Potwierdzono niezależnie w GitHub Actions:

- Windows PyInstaller + publiczny asset: workflow `39294472336`, **SUCCESS**.
- Unit/integration/Pygame offscreen: workflow `39294472120`, **SUCCESS**, 476 testów.
- Standardowe 100 meczów v22 (z aktywnymi regułami v23): workflow `39294472335`, **100/100**, zero błędów, ale **tylko 11/100 pełnych replayów**.
- Seria weryfikacyjna 100/100 replayów: workflow `39294052673`, **SUCCESS**, jednak pochodzi z wcześniejszej rewizji gałęzi PR #45, a nie dokładnie końcowego SHA release.
- Dołączony utwór: `assets/music/music_auctionhammer.mp3` rzeczywiście istnieje w repozytorium; poprzednie CI pomyślnie dekodowało plik przez SDL dummy. `FantasyTavernMusic` zapętla pojedynczy pełny album, głośność początkowa 0,30; wersja Windows kopiuje utwór obok EXE (bez dodatkowej kopii w `_internal`).
- **Nie wykonano manualnego odsłuchu i wielorozdzielczościowego testu GUI na fizycznym Windows**. Automatyczny rendering Pygame nie zastępuje tych odbiorów.

## 2. Trzy rzeczywiste luki wykryte w drugim audycie

### A. Podpisana migawka v23 była niekompletna

W 0.9.36 `state_snapshot` podpisywał planszę, stosy, ręce i kolejki, ale **nie podpisywał** `ruleset_version` ani `pending_vacant_income`. Możliwa była więc zmiana oczekującej wypłaty bez natychmiastowej zmiany SHA stanu. Sam silnik poprawnie serializował tę flagę.

**Poprawka:** opt-in `audit_state_schema=2` dla świeżych rozgrywek v23; podpisany `ruleset_state` zawiera nazwę rulesetu, oczekującego odbiorcę, flagę dochodu i numer schematu. `verify_replay` rozpoznaje wersję schematu z samej oryginalnej migawki i porównuje odpowiedni zestaw pól. Migrator starych zapisów wybiera schemat 1 — bez przepisania historii i starych hashy.

### B. Istotne wyjątki A014/A015/A018 były na końcu długiego opisu

Podgląd trzech kart na aukcji renderował **maksymalnie cztery linie** opisu. Zasady v23 dopisano na końcu `v23_variant`, co mogło ukryć je przed kupującym.

**Poprawka:** informacje o konwersji leczenia, blokowaniu tylko przeciwnika oraz awaryjnym `+5/+5` legendarnej A018 znajdują się **na początku opisu**.

### C. Pięć bazowych kart miało nieaktualny opis główny

Podstawowe `effect` z v19 nie wyjaśniało alternatyw v23 dla S86/S87/S88/S32/S95, choć silnik już je wykonywał.

**Poprawka:** dodatkowe, warunkowe informacje v23 wyświetlane są w pełnym podglądzie. Oryginalny plik v19 i wcześniejsze opisy nie są nadpisywane, aby nie łamać znaczenia archiwalnych gier.

## 3. Zweryfikowane funkcje v23

| Obszar | Oparcie kontroli |
| --- | --- |
| Suwak aukcyjny | testy min/max, A018 skuteczny bid, brak monet, klawiatura / wskaźnik; tylko silnik zmienia saldo |
| Skalowanie 10 kart | zgodność `scaling` z wzorem wzrostu v21, bez zmian ATK/HP |
| Dochód za puste pola | A003 wskrzeszenie, A001 przejęcie, Pending, save/load i jednorazowa wypłata po falach |
| A018 | obie gałęzie gwarancji i awaryjnego bonusu, brak podwójnej wypłaty |
| A014 | nominalne leczenie przy pełnym PŻ, Tarcza, konwersja rzadka/legendarna i interakcja z S87 |
| A015 | tylko przeciwnik, sojusznicza zdolność, cisza, śmierci z jednej migawki; wariant dwóch Wieszczek |
| S86–S88 | dokładnie jeden efekt śmierci i wariant bez sojusznika |
| S32/S95 | brak legalnego celu, wybór najsłabszego wroga i brak fałszywego ogłuszenia |
| A010 | brak powrotu do kopiowania najsilniejszej karty |
| Save/replay | v22, v23 schema 1, v23 schema 2; podpisany stan czekającej wypłaty |
| Historia | stronicowanie po 4 rekordy; wybór właściwego pliku; brak nadpisywania archiwum |
| Muzyka | rzeczywisty MP3, SDL dummy, pętla w menu i pomiędzy grami, credits |

## 4. Pozostałe ograniczenia audytu (nie „PASS”)

- **AH35-09/T-031:** nie wykonano jeszcze pełnego, osobnego eksperymentu A/B nowych limitów ofert AI (`value_budget` i `value_budget_underdog`). Produkcyjny limit jest zgodnie ze specyfikacją **niezmieniony**.
- **T-039:** brak manualnego odbioru myszy/suwaka, polskich znaków i audio na docelowym fizycznym Windows przy różnych DPI. Automatyczny build/SDL dummy jest potwierdzony.
- **T-012:** algorytm A018 bez przyszłej aukcji ma test jednostkowy wymuszający strukturalny brak następnej aukcji. Nie jest to jeszcze osobny pełny test odtworzenia dokładnie ósmej aukcji z losowo wylosowaną A018.
- **Historyczne, zewnętrzne archiwa:** testy potwierdzają stary schemat podpisu i odtwarzanie syntetycznie zbudowanych rzeczywistych meczów z tą semantyką; nie udowadnia to bitowej zgodności wszystkich archiwów starszych wersji z późniejszymi poprawkami.
- Nie istnieje dowód matematyczny na brak wszystkich możliwych błędów w kombinacjach 70/17/51 ani gwarancja jakości dźwięku na każdym urządzeniu.

## 5. Bramka wydania 0.9.37

Nie scalać PR #46 bez: kompletnego `unittest discover`, audytu 100 nowych meczów z replayem **100/100** w tej samej rewizji, testów standardowych 100 i pozytywnego renderu Pygame na CI. Po scaleniu osobna weryfikacja Windows ZIP i wersji artefaktu w Releases.

**Zmiany w tym patchu mają charakter audytowy i prezentacyjny. Nie zmieniają ekonomii, AI ani działania zdolności.**
