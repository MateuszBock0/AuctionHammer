# AuctionHammer 0.9.39 — implementacja UX i zmiana rekompensaty

## Nowa reguła produkcyjna (tylko świeże mecze)

Gracz ruszający jako **drugi**, niezależnie czy P0 czy P1, otrzymuje od razu **jednego Strażnika Drugiego Gracza 5 ATK / 5 PŻ** na planszy. Nie dostaje +3 monet na start. Strażnik jest neutralnym tokenem bez zdolności, zajmuje 1 z 5 pól, nie może atakować w pierwszej własnej turze. Przy śmierci/zastąpieniu znika z obiegu; nigdy nie należy do 70 kart bazowych, nie jest dobierany ani kupowany na aukcji. Zwykły wzrost monet w toku meczu zostaje bez zmian.

Kontrakt serializacji: nowe `Match` wywołane przez UI używa `starting_compensation="unit_5_5"`, schema audytu 3 podpisuje tę decyzję, stare zapisy defaultują do `coins` i starego schematu. Nowe eksperymenty mają jawny przełącznik `--starting-compensation unit_5_5`, historyczne symulacje pozostają domyślnie `coins` dla odtwarzalności.

## UX wdrożone

- F11/A działają globalnie również w menu; `A` nie modyfikuje silnika. Stan animacji nie resetuje się przy nowym meczu.
- Obsługa `VIDEORESIZE` działa przed menu i panelami modalnymi.
- `R`, `Q`, systemowe zamknięcie i przycisk Nowy mecz w aktywnej partii pokazują wybór: **S** (zapisz i kontynuuj), **D** (bez zapisu), **Esc** (anuluj). Błąd zapisu nie zamyka aplikacji.
- Podpowiedź etapu rozgrywki jest dwuwierszowa, w osobnym korytarzu między planszami; fazy i dozwolone akcje wynikają z silnika.
- Historia bieżąca nadal jest pod H, migawki bieżącej partii pod P, archiwum ukończonych partii w menu. To trzy **odrębne** funkcje. Odtwarzacz pełnych archiwalnych audytów wewnątrz gry nie jest jeszcze dostępny.
- Zwykły przebieg pozostaje: wymiana do 3 kart, zagranie/atak w dowolnej kolejności, wybór zdolności, Spacja koniec tury.

## Nie zmieniono

Zdolności i statystyk 70 kart bazowych/51 wariantów aukcyjnych, legalności ataków, kolejki śmierci, heurystyk AI, zachowania starszych audytów i historii.

## Kryteria QA

1. Zwykłe starsze mecze nadal mają +3 monety i odtwarzają się bez tokena.
2. Nowe mecze: 70 kart podstawowych + 1 token, 5/5, 0 monet od startu, brak ataku w pierwszej własnej turze i zniknięcie po usunięciu.
3. Zapis/wczytanie w mulliganie i turze zachowuje token i podpisaną regułę.
4. F11 w menu, A przed i po nowym meczu, resizing na ekranach modalnych.
5. Restart/wyjście nigdy nie gubią aktywnej partii bez wyraźnego wybrania D.
6. Testy automatyczne, render offscreen oraz 1000 pełnych replayów w nowym trybie na ustalonym SHA; odbiór fizyczny Windows pozostaje odrębny.

## Ryzyko balansu

Stała jednostka 5/5 może dawać istotnie inną przewagę niż +3 monety. Nie nazywać nowego wariantu zbalansowanym, dopóki benchmark na sparowanych seedach, naprzemiennym rozpoczynaniu i trzech trudnościach nie wykaże akceptowalnej inicjatywy. Zmianę można cofnąć per nowy mecz bez modyfikacji historii.
