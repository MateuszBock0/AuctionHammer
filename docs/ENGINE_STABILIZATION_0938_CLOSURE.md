# AuctionHammer 0.9.38 — zamknięcie techniczne etapu

**Punkt odniesienia:** produkcyjny `main` commit `f9149b7f1b530b7a5349c588e7e3b36f27c09709`.

## Materiał dowodowy

- Na `main` [workflow testów](https://github.com/MateuszBock0/AuctionHammer/actions/runs/39312435866) wykonuje 515 testów (PASS) i render pygame-ce SDL dummy (PASS).
- Na dokładnie tym samym SHA [Windows build](https://github.com/MateuszBock0/AuctionHammer/actions/runs/39312435660) zalicza testy, render, kompilację PyInstaller i publikację ZIP.
- Na **osobnej gałęzi** stabilizacyjnej, SHA `d0949930`, [workflow](https://github.com/MateuszBock0/AuctionHammer/actions/runs/39310531281) potwierdza 400/400 normalny-normalny, 300/300 łatwy-trudny i 300/300 trudny-łatwy wraz z replayem KAŻDEJ rozgrywki: 1000/1000, zero błędów.
- `docs/ENGINE_COVERAGE_MATRIX_0938.csv` ma 121 wpisów (70 podstawowych + 17×3 aukcyjne). Testy wykonują wszystkie ścieżki aktywacji, NIE dowodzą 100% pokrycia gałęzi wszystkich efektów.

## Status zamknięcia

Stabilizacja podstawowej logiki i bramek CI **potwierdzona**. Dopuszcza rozpoczęcie 0.9.39 i zamrożenie istniejącej semantyki kart. **Nie** deklaruje braku wszystkich potencjalnych błędów, fizycznego odbioru Windows ani 1000 replayów na dokładnie końcowym SHA 0.9.38. Nowa reguła Strażnika 5/5 w 0.9.39 to osobna, jawna zmiana balansu i jest odseparowana od historycznej semantyki +3 monet.

## Warunki pozostające do 1.0.0

Weryfikacja fizycznego Windows 10/11 (F11, audio, DPI, mysz, sterowniki), realnych starych zapisów i licencji muzycznej. Niespełnienie tych wymagań **nie** powinno być przemilczane jako PASS wydania 1.0.0.
