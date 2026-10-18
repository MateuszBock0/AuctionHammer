# AuctionHammer MVP 0.9.11 — Minimal Fantasy z wydłużonymi kartami

## Co zmieniono

Nowy wygląd oparto na zatwierdzonym stylu **Minimal Fantasy**. Celem jest przede wszystkim czytelność działania zdolności, aktualnych statystyk i możliwości wykonania ataku, a dopiero potem dekoracyjność. W grze pozostają obecne zasady **Game Master v19**, komplet 70 kart oraz wszystkie wcześniejsze poprawki jednoczesnych fal zgonów.

| Miejsce | Przed zmianą | Po zmianie |
| --- | --- | --- |
| Karta na ręce | 125 × 169 px | **125 × 195 px** |
| Karta na planszy | 148 × 180 px | **148 × 220 px** |
| Podgląd szczegółowy | 255 × 338 px | **255 × 380 px** |
| Logiczne płótno | 1480 × 920 px | **1480 × 980 px** |

Zmiana nie jest prostym powiększeniem grafiki: przeniesiono również strefy obu bohaterów, jednostek, ręki, komunikatów i kontrolek przewijania, a wszystkie obszary kliknięć opierają się na nowych współrzędnych. Mechanizm dopasowania do rozdzielczości Windows pozostaje aktywny.

## Porządek rysowania i informacje

1. Tło i **osobna ilustracja** (w tym dotychczasowe ilustracje oraz generowane symbole zastępcze).
2. Subtelna ramka frakcji i przyciemnienie wyłącznie ilustracji.
3. Nieprzezroczyste pola: nazwa, moment aktywacji, rodzina i liczbowy efekt zdolności.
4. Zielony pasek ulepszeń co trzy własne tury na ręce. Postęp `0/3`, `1/3`, `2/3` wyłącznie na ręce; po wystawieniu poziom zostaje utrwalony.
5. Dwa statusy o najwyższym wpływie na walkę i licznik pozostałych `+N` w obszarze ilustracji. Wszystkie efekty i ich wartości, czas i źródło są również dostępne w prawym panelu i pełnym opisie.
6. Wskaźnik `ATAKI x/y` na planszy, którego dostępność wynika z **`Match.legal_attacks()`**, a liczba z **`Match._double()`**, nie z wyglądu karty.
7. **ATAK i bieżące PŻ** z mniejszą liczbą maksymalnych PŻ są rysowane jako ostatnie w oddzielnych, nieprzezroczystych polach. Nie może ich zasłonić grafika, animacja ani status.

Kolory obramowań mają różne znaczenia: złote — zaznaczenie karty; turkusowe — legalny cel ataku; fioletowe — legalny cel zdolności; czerwony licznik ze złotą ramką — karta zaznaczona do wymiany. Niedozwolone cele nie są oznaczane jako dopuszczalne.

Jedno kliknięcie nadal **zaznacza** kartę. Klawisz `I` lub **prawy przycisk myszy** otwiera szczegóły, więc dotychczasowe zagrywanie kart i wybór ataków pozostają bez zmian.

## Co stanowi aktualne źródło danych

Wszystkie nazwy, statystyki, przyrosty i pełne opisy pochodzą z `data/cards_base_70.json`, `Card`, `Unit` oraz `game.ui.card_infographics.card_cue`. Renderer nie wpisuje statystyk do grafik PNG. Skrócone informacje wskazują rodzinę efektu, rzeczywistą wartość oraz kontekst celu rozpoznany bez zgadywania; dla niejednoznacznych wyjątków odsyłają do pełnego opisu pod `I`. Nie zastępują one obowiązujących zasad.

Zmieniono wyłącznie prezentację i jej testy oraz metadane wydania. **Nie zmieniono `game/core/`, katalogu 70 kart, balansu ani zasad aukcji.**

## Plan testów automatycznych

Polecenie: `python -m unittest discover -s tests -v`.

- Testy rozmiarów 125×195, 148×220 i 255×380 oraz rozdzielnych obszarów na kartach.
- Renderowanie każdego z 70 archetypów w każdym rozmiarze, łącznie z długimi nazwami i efektami.
- Wysokie liczby ATAK/PŻ, otrzymane obrażenia, wiele statusów, ogłuszenie, trucizna, tarcza i Podwójny atak.
- Sposób zaznaczania karty lewym przyciskiem, podgląd prawym i klawiszem `I`.
- Poprawność trafiania kursorem w kartę, także przy zmianie rozdzielczości i skali Windows.
- Zgodność rozwoju statystyk i zdolności z danymi Game Master v19.
- Testy wcześniejszych reguł silnika: fale zgonów, cele zdolności, Prowokacja, statusy, AI.
- Generowanie rzeczywistych podglądów Pygame w Windows i publikacja ich jako artefaktu GitHub Actions.

## Ręczny test odbiorczy po pobraniu wydania Windows

1. Uruchom `URUCHOM_AUCTIONHAMMER.bat`, sprawdź kompletność ekranu przy maksymalnie powiększonym oknie oraz w trybie **F11**.
2. Wybierz kartę lewym przyciskiem i wystaw ją na planszę; sprawdź, czy duże ATAK i PŻ nie są zasłonięte.
3. Otwórz `I`, zamknij, a następnie otwórz podgląd **prawym przyciskiem myszy**.
4. Sprawdź efekty na ręce po 0, 1, 2 i 3 własnych turach; karta po wystawieniu nie może otrzymywać dalszego rozwoju na ręce.
5. Rozegraj atak przeciwko Prowokacji. Tylko legalny cel powinien mieć turkusowe obramowanie. Przy zdolności wymagającej wskazania celu użyj oznaczenia fioletowego.
6. Sprawdź kartę z wieloma statusami: widoczne dwa najważniejsze + licznik, a wartości statusów w panelu po prawej.
7. Przetestuj wymianę trzech kart na początku meczu, a następnie przestawianie pełnej planszy i przewijanie ręki.
8. W systemie Windows porównaj skalowanie interfejsu 100%, 125% i 150% (jeżeli jest dostępne) oraz sprawdź, czy wszystko mieści się na ekranie bez utraty klikalności.
9. W razie błędu dołącz zrzut ekranu, identyfikator karty, wielkość okna i opis czynności.

## Architektura i cofnięcie zmian

Kluczowe pliki: `game/ui/card_view.py`, `game/ui/app.py`, `game/config.py`, `VERSION.json`, `tools/render_minimal_fantasy_preview.py` i `tests/test_minimal_fantasy_layout.py`.

Wdrożenie jest osobnym zgłoszeniem zmian GitHub. W razie problemów można wrócić do poprzedniego stabilnego wydania 0.9.10 — **nie** należy nadpisywać lokalnego katalogu starego repozytorium plikami z paczki 0.9.7. Podglądy PNG znajdują się w artefaktach przebiegu Windows i w folderze `preview/` gotowej paczki.
