# AuctionHammer 0.9.38 — stabilizacja silnika

**Etap:** silnik i integralność stanu (bez nowego balansu kart, mechanik ani zmian UI/UX).  
**Wersja zasad:** nowa gra `ruleset_version=v23`, 70 bazowych kart Game Master v19 i 17 archetypów aukcyjnych v22 (3 rzadkości, 51 wariantów).  
**Podstawa:** projekt Game Master v19 + aneks v23 `docs/GAME_MASTER_v23_ADDENDUM.md`; historyczne mecze zachowują swój wariant zasad.  
**Data:** 19.10.2026.

## Co dodano w wersji 0.9.38

1. **Kompletna macierz 121 pozycji:** `ENGINE_COVERAGE_MATRIX_0938.csv` zawiera 70 kart `S` i 17×3 warianty `A` wraz z nazwą, wyzwalaczem, ścieżką silnika i deklarowanym zakresem testu. Test automatyczny sprawdza jej zgodność z żywymi katalogami JSON i uruchamia każdą pozycję poprzez `Match.play`, `Match.attack`, `_kill_batch`, `Match.end_turn` lub ścieżkę pasywną. Żadna nazwa, pochodzenie lub liczba kart nie może zostać pominięta bez błędu testu.
2. **Integralność obiektów fizycznych:** `Match.assert_integrity()` sprawdza nie tylko 70×1 kart i brak duplikatów aukcyjnych, lecz również strefę i właściciela karty w banku, ręce, talii, cmentarzu, planszy, wygnaniu i stosach aukcyjnych. Kontroluje spójność `Unit.owner` z `Card.owner` oraz to, że monety nigdy nie schodzą poniżej 0. Nie zmienia liczników HP ani efektów.
3. **Atomowość odrzuconych poleceń:** dla nielegalnego zagrania, ataku, wyboru lub licytacji test porównuje pełną migawkę audytu oraz stan RNG przed i po próbie. Zabroniona akcja nie może pobierać monet, przewijać RNG ani zmieniać planszy.
4. **Save/resume w połowie decyzji:** bezpośrednio porównywane są podpisy i dalsze rozstrzygnięcia po zapisie/wczytaniu przy wyborze S01, podwójnym wyborze Kartografa A016 i dwóch fazach aukcji. Stare historie zachowują schemat odtwarzania 0.9.36/v22.

## Co oznacza zaliczona macierz

To jest **test integracji wszystkich wejść do zdolności**, a nie dowód wyczerpującego działania każdej gałęzi każdej karty. Scenariusze korzystają ze sztucznie przygotowanych, ale fizycznie poprawnych plansz, legalnych wyborów i realnych metod silnika. Dodatkowe testy jednostkowe i scenariusze v23 pokrywają ważne kombinacje (A014/A015, A016, A018, S86–S88, S32, S95, tarcze, fale śmierci).

Nie twierdzimy, że przetestowano wszystkie możliwe układy 70 podstawowych i 51 aukcyjnych wariantów. Nie wolno mylić `smoke PASS` z `100% branch coverage` ani dopisywać niepotwierdzonych zmian w balansie. W razie wykrycia problemu należy przygotować minimalną reprodukcję w osobnym teście, dopiero potem naprawiać silnik.

## Bramka testów przed wydaniem

- `python -m unittest discover -s tests -v` — cała regresja; liczba bazowa przed 0.9.38 wynosiła 492, w 0.9.38 dochodzi łącznie **12** nowych testów (4 w macierzy + 1 kontrola CSV + 7 testów transakcji i zapisu).
- Zestaw obciążeniowy w `.github/workflows/engine-stabilization-0938.yml`: **400 normalny–normalny + 300 łatwy–trudny + 300 trudny–łatwy = 1000 pełnych rozgrywek**, `--verify-every 1`, czyli pełny replay **każdego** meczu.
- Każda partia: zakończony zwycięstwem mecz, brak odrzuconych komend, kontrole stanu po każdej akcji, zarchiwizowany zapis i równe podpisy audytu/replay. Wyniki są zachowywane przez Actions jako artefakty diagnostyczne. Nie zaliczamy bramki, jeśli choć jedna z 1000 partii lub jej odtworzenie zakończy się błędem.
- Po połączeniu PR wymagane są jeszcze testy na `main` i poprawne wydanie Windows z tej samej rewizji.

## Świadomie poza zakresem

- Nowe karty, mechaniki aukcyjne, zmiana ATK/PŻ i kosztów zagrywania.
- Zmiana heurystyk licytowania AI bez osobnego A/B.
- Dźwięk, grafika, interakcje i animacje: **następny etap 0.9.39 UI/UX**, w którym powstanie osobna lista priorytetów.
- Multiplayer online: poza zakresem celu AuctionHammer 1.0.0.

**Decyzja o zakończeniu etapu:** scalanie dopiero po potwierdzeniu przejścia testów i pełnego obciążenia. Dokument nie stanowi automatycznie potwierdzenia wyników uruchomień CI.
