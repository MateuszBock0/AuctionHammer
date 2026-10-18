# Walidacja balansu AuctionHammer v20

- Statycznie zweryfikowano **70** niepowtarzalnych kart podstawowych.
- Zaktualizowano **16** zdolności; **0** zmian bazowego ATK/HP i wzrostu na ręce.
- Katalog aukcyjny zawiera **12** archetypów i **36** wersji zdolności (v4).
- W gałęzi GitHub `balance-v20-one-shot-fallbacks` zintegrowano aktualne katalogi, silnik i testy regresji; zielone GitHub Actions oznacza przejście istniejącej automatycznej suite, w tym testów scenariuszowych S12, S74, S78, S85, S97 i S27.
- Nie przeprowadzono pełnego badania balansu PvP z aukcjami: brak potwierdzonej integracji aukcyjnej.
- Pełny kod istniejącej gry pozostaje w repozytorium GitHub; ten ZIP zawiera kompletne **dane, dokumentację, instrukcje i aktualizację PR**, a nie spakowany plik `.exe`.
- Nie dokonano automatycznego scalenia PR do `main`.
