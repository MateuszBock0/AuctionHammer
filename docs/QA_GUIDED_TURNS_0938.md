# Kontrola początku rozgrywki i skrótów — 0.9.38

**Zakres:** wyłącznie poprawki zgłoszone podczas stabilizacji silnika. To nie jest pełen plan prac UI/UX dla 0.9.39.

## Potwierdzone problemy i poprawki

| Zgłoszenie | Przyczyna w kodzie | Rozwiązanie |
| --- | --- | --- |
| F11 nie działa od początku | menu główne przechwytywało `KEYDOWN` przed `K_F11` | Globalna obsługa F11 przed menu, historią, powtórką, ekranem karty i aukcją; istniejący przełącznik okno/pełny ekran |
| Co robi A? | włącza/wyłącza `animations_enabled` tylko w normalnej grze, bez czytelnego potwierdzenia | Globalny A także w menu; dynamiczna informacja ANIM WŁ./WYŁ., widoczna w menu i krótka informacja o zmianie |
| Niejasna wymiana pierwszych kart | 0–3 i Enter były podane głównie w panelu po prawej | Stały pasek fazy: zaznacz do 3 kart, możesz zaznaczyć zero, potwierdź Enter; powtórzone przy przycisku |
| Co mam teraz zrobić? | brak jawnego stanu następnego kroku na planszy | Pasek instrukcji obliczany z aktualnego stanu: wymiana, aukcja, cudzy ruch, wybór zdolności, zagranie, atak, koniec tury |
| „Historia w tle” | `_draw_log` wypisywał trzy zdarzenia na otwartej planszy między strefami; zlewały się z elementami gry | Skrót ostatniego zdarzenia znajduje się w panelu bocznym; pełna przewijana historia tylko po `H`; ekran powtórki `P` pozostaje oddzielny |

## A oznacza wyłącznie efekty wizualne

`A` nie oznacza automatycznej walki, nie pomija tury, nie zmienia losowania,
nie wyłącza dźwięku ani nie zapisuje meczu. Włącza/wyłącza rysowanie
przejściowych animacji i efektów walki oraz ich podświetlanie.
Przełączenie jest lokalne dla klienta i nie dotyka podpisanej migawki silnika.

## Etapy i komunikaty

- **WYMIANA STARTOWA:** zaznacz 0–3 kart na ręce, następnie **ZATWIERDŹ** lub **Enter**.
- **TWOJA TURA — ZAGRAJ KARTĘ:** wybierz kartę z ręki i własne pole.
- **TWOJA TURA — PEŁNA PLANSZA:** wybierz jednostkę przeznaczoną do zastąpienia, jeśli możesz zagrać.
- **TWOJA TURA — ZAATAKUJ:** kliknij gotową jednostkę i jeden z legalnych podświetlonych celów.
- **TWOJA TURA — ZAKOŃCZ:** nie ma kolejnej dostępnej akcji, naciśnij **Spacja** lub przycisk.
- **WYBÓR ZDOLNOŚCI:** wybierz cel lub wariant po prawej.
- **AUKCJA:** ustaw legalną ofertę suwakiem, zalicytuj Enter albo spasuj Esc; w fazie wyboru wskaż jedną kartę.
- **RUCH KOMPUTERA:** poczekaj na akcje rywala.

Ważne: zagrana karta i atak nie mają przymusowej kolejności. Wskazówki
proponują legalny następny krok, **nie nakazują** zagrywania przed atakiem.

## Automatyczne testy UI

`tests/test_guided_turns_and_global_keys_0938.py` sprawdza obsługę klawiszy
na ekranie startowym, ekranach modalnych, podczas historii i powtórki;
brak mutacji silnika przez A; wszystkie podstawowe komunikaty etapów,
kliknięcie karty w mulliganie, brak renderowania historii nad planszą
oraz zgodność nowego paska z wolnym pasem między strefami.

## Ograniczenia odbiorowe

Testy Pygame na SDL dummy potwierdzają routing wydarzeń i układ logiczny;
nie dowodzą, że fizyczny klawisz F11, polska czcionka i skalowanie DPI
zadziałają na każdym laptopie Windows. Potrzebne są testy ręczne:
uruchomienie ZIP na czysto, F11 od pierwszego menu, F11 w połowie gry,
A przed wyborem kart i po ataku, H oraz P podczas gry, rozdzielczości
1366×768 / Full HD przy 125–150% skalowania.

**Dalsza pełna lista UI/UX:** osobny etap 0.9.39, po stabilizacji mechanik.
