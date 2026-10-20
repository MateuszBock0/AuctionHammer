# AuctionHammer 0.9.49 — realizacja audytu 0.9.48

Źródło: przesłany plik `AuctionHammer_AUDYT_0.9.48_2026-10-20(1).zip`. Manifest SHA-256: **5/5 PASS**. Bazowe wydanie: `cbdc7b7b5bf0638edfdf1294e778d74c81352cc5`.

## Wdrożenie

- **AH48-CARD-01 (P1)**: parser liczb w `highlighted_numeric_ranges()` obsługuje „1 dodatkowe obrażenie” S15, a nie myli go z czasem ogłuszenia. Wartości dla poziomów 0,1,3: 1,2,4.
- **AH48-CARD-02 (P2)**: infografiki S15, S59, S84, S108 i S95 pokazują `nieskuteczne ogłuszenie → skuteczne ogłuszenie`. Dla S95 v23 osobna notatka nadal wyjaśnia 2 zwykłe obrażenia, gdy brak nowego celu. Nie zmieniono reguł.
- **Poprzedni audyt UX**: podświetlenia samouczka nie przenikają przez okno pełnego podglądu aukcji; ticker mieści się w prawym panelu (zawijanie do dwóch wierszy, historia H zachowana).
- **Regresje**: testy poziomów S15 0/1/3, opisów warunkowych, geometrii panelu i modalu aukcji.

## Zakres po walidacji

Nie modyfikujemy katalogów `data/`, silnika `game/core/`, reguł, `CardDefinition.effect`, mechanizmu audytu czy historii zapisów. Poziomy i opisy są obliczane do wyświetlenia.

**Niezakończone ręcznie:** AH48-UX-03 — fizyczny odbiór Windows DPI 100%, 125%, 150%. AH48-REPLAY-04 — reprezentatywne *zewnętrzne* archiwalne zapisy nie zostały dostarczone w tym ZIP; automatyczne aktualne audytowane odtworzenia nie zastępują sprawdzenia nieudostępnionych plików.
