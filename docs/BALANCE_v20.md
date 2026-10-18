# AuctionHammer — BALANCE v20 (kandydat zmian)

Data: 18.10.2026. Podstawa: Game Master v19; **70 kart podstawowych, bez zmian ATK/HP**.

## Zasada
- Jednorazowe obrażenia przy wystawieniu/śmierci: +2 do bazowej wartości S01 (5), S21 (6), S59 (3), S84 (4).
- Powtarzalne efekty przed walką / na koniec tury / pasywne: ostrożne +1 bazowe S09 (2), S27 (2), S103 (2), S15 (1), S95 (1), S108 (1).
- Użyteczne alternatywy: S12 zdejmuje pancerz lub zadaje 2 obrażenia bez pancerza także przeciw bohaterowi; S74 zadaje 3 po skutecznym rozproszeniu lub 2 bez buffa; S78 gdy brak świeżo wystawionego sojusznika nadaje Szybki atak wskazanej karcie w ręce; S85 bez sojusznika leczy bohatera o 4; S97 leczy 2 po oczyszczeniu albo 1 bez niego; S99 obok odporności na truciznę nadaje 1 tymczasowego pancerza.
- Premie jakości co trzy własne tury na ręce pozostają zgodne z aktualnymi opisami w `data/cards_base_70.json`.
- Ogłuszenie nie wydłuża czasu trwania; S15/S95/S108 zadają obrażenia tylko po skutecznym ogłuszeniu.
- Jedno wystawienie z ręki na turę, limit pięciu jednostek i rozstrzyganie wspólnych fal śmierci pozostają bez zmian.

## Aukcje
12 archetypów × trzy warianty = 36 efektów w katalogu roboczym `AuctionHammer_AUKCJE_12_v4_WERYFIKACJA` (dostępny jako osobny pakiet w bibliotece projektu). **Nie należy integrować kart aukcyjnych z podstawowym katalogiem 70 ani zastępować ofert trzech kart trzema wystawieniami.**

## Migracja
Zmiany zapisano w trzech źródłach gry: `data/cards_base_70.json`, `data/GAME_MASTER.json`, `game/core/engine.py` i `game/core/effects.py`. Zaktualizowano regresję danych i fal śmierci oraz dodano `tests/test_balance_v20.py`.

Dopóki Pull Request nie zostanie scalony, gałąź `main` pozostaje działającą wersją bez tej korekty. **Zielone CI** potwierdza testy, ale nie stanowi pełnej walidacji balansu PvP ani wydajności aukcji.
