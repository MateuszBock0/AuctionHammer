# AuctionHammer 0.9.50 — weryfikacja braków audytu 0.9.48

Źródło: AuctionHammer_AUDYT_0.9.48_2026-10-20(1).zip, manifest SHA-256 5/5 PASS. Baza: 0.9.49 / 36f98d9d67fe98f4013c7060bc49759b8d75b20b.

## Już wdrożone w 0.9.49

- AH48-CARD-01: S15 1/2/4 na poziomach 0/1/3.
- AH48-CARD-02: infografiki warunkowe S15/S59/S84/S95/S108, wersjonowany opis S95 v23.
- Dwa błędy UX: nakładające się obrysy w modalnym podglądzie aukcji i granice panelu walki.
- 25 zweryfikowanych opisów wersjonowanych pozostaje w UI; modele i historyczne efekty są niezmienione.
- Indeks 121 opisów istniał jako generator, ale nie jako publikowany raport przy każdym PR.

## Dodane w 0.9.50

- T04–T08: prawdziwe silnikowe rozstrzygnięcia S15, S59, S84, S95, S108 dla poziomów 0/1/3 z odpornością i bez; brak premii za nieskuteczne ogłuszenie, warunkowy fallback S95 tylko v23 i jednorazowa reakcja S108.
- T10: syntetyczne historyczne tryby v4 i v22 w 3 rzadkościach karty A010; save/load, digest state_snapshot i niezmienny tekst CardDefinition.effect.
- AH48-CATALOG-05: GitHub Actions generuje przy każdym push/PR plik reports/card-copy-coverage-121.csv i publikuje artefakt AuctionHammer-Card-Copy-Coverage-121.
- Utrzymane regresje jednostkowe, Windows i 100 pełnych audytowanych meczów.

## Granice weryfikacji

- AH48-UX-03/T13: rzeczywisty manualny Windows DPI 100/125/150% pozostaje niewykonany. Test SDL lub render na CI nie dowodzi fizycznej czytelności.
- AH48-REPLAY-04: oryginalne zewnętrzne archiwalne podpisane zapisy v22/v23/A010 NIE znajdują się w przesłanym ZIP. Testy syntetyczne oraz autentyczne nowo wygenerowane audyty nie zastępują kontroli obcego pliku.
- Issue #57 — pełny odtwarzacz historycznych meczów w aplikacji — to osobny feature poza zakresem wersji.
- Raport CSV to kontrola identyfikatorów i opisów prezentacyjnych, nie dowód semantycznej zgodności wszystkich efektów silnika.

## Integralność

Brak zmian w game/core, data, skompilowanych zdolnościach, RNG i serializacji; wyłącznie testy, workflow, dokumentacja i wersja.
