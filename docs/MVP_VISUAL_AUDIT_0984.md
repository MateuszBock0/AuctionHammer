# AuctionHammer 0.9.84 — audyt wizualny czterech filarów MVP

**Zakres:** tylko pixel art, walka, aukcja, nakładki i HUD. Bez nowych trybów,
kart, zdolności, zasad, narzędzi progresji ani zmian algorytmu AI.

## 1. Pixel art — ustalenia i poprawki

- Karty podstawowe pixel art i 51 finalnych wariantów aukcyjnych już mają
  własną ścieżkę nearest-neighbor. **Potwierdzona luka:** `SoloApp._present`
  skalował *gotowy ekran* przez `pygame.transform.smoothscale`; przy
  rozdzielczości okna różnej od logicznego płótna rozmywało to piksele.
- **Naprawa:** finalne wyświetlanie używa `transform.scale` dla dowolnego
  wymiaru okna; zachowuje logikę letterbox, viewport i przeliczania hitboxów.
  Tak samo najbliższym sąsiadem są skalowane starsze, zastępcze ilustracje
  aukcyjne (pełne finalne ilustracje wciąż mają priorytet).
- Nie zmieniono oryginalnych plików PNG ani proporcji postaci. Świadomie
  pozostawiono obecny wygląd tradycyjnego tła i okien; nie robimy przebudowy
  graficznej MVP ani nie dokładamy wygładzonych tekstur.

## 2. Walka — ustalenia i poprawki

- **Potwierdzona kolizja:** znacznik `ATAKUJ` na legalnym celu znajdował
  się w górnej strefie ilustracji (około `slot.top+53`), potencjalnie
  zasłaniając twarz/postać.
- **Naprawa:** usunięto tylko tę nakładkę. Nadal widoczne są mocniejsze
  obramowanie wybranego legalnego celu i 8-bitowe narożniki; nadal używane
  jest `Match.legal_attacks()`. Delikatna przezroczysta czerwona strzałka
  ataku z 0.9.82 pozostaje.
- Efekt zatwierdzonego trafienia zmieniono na krótki, ostry pocisk z prostych
  prostokątów i pikselowych odłamków zamiast dużego okrągłego halo.
  Uczestników ataku wyróżniają krótkie narożniki poza kartą — bez
  zasłaniania statystyk. Wyliczanie efektów nadal opiera się wyłącznie
  na zatwierdzonym stanie silnika.

## 3. Aukcja — ustalenia i poprawki

- W 0.9.83 wprowadzono już 51 wariantów, pełne portrety z prostym
  przedłużeniem tła, dwie ostre ikonki i rozdzielenie oferty skutecznej
  od faktycznej ceny. Zachowano cały ten układ, zamiast ponownie
  przemieszczać opisy.
- **Luka interakcji:** trzy oferty używały niemal identycznej ramki
  niezależnie od tego, czy gracz może kliknąć wybraną kartę.
- **Naprawa:** podczas fazy `picking` dostępna, wskazana oferta ma
  dyskretne, ostre narożniki. Karta niedostępna, wybrana przez kogoś
  albo pokazana w fazie licytacji nie sugeruje aktywnego kliknięcia.
  Oznaczenia triggerów, frakcji/rodzin zdolności i ceny są bez zmian.

## 4. Układ, podglądy i aury — ustalenia i poprawki

- **Potwierdzona kolizja:** kanał strzałek aur przy `y=416` przechodził
  przez panel tury `Rect(96,372,952,56)`; strzałki między dwoma
  rzędami przebiegały przez środek tego samego panelu.
- **Naprawa:** linie aur wewnątrz jednego rzędu biegną tylko w 5-pikselowej
  szczelinie między kartami a paskiem PŻ własnego bohatera (`y=656`)
  lub przeciwnika (`y=147`). Aury przechodzące między stronami nadal
  pokazują spójne kolorem obramowania źródła i odbiorcy oraz dokładną
  wartość efektu, ale nie rysują długiej kreski przez komunikat tury.
  Zasady i liczby aur pozostają identyczne.
- **Kolizja interakcji:** wielki automatyczny podgląd 286×439 mógł
  zasłaniać inne karty przy wskazywaniu celu.
- **Naprawa:** gdy wybrany atakujący ma choć jeden legalny cel, duży
  hover-podgląd innych kart zostaje tymczasowo ukryty. Pełna inspekcja
  pod `I` i prawym kliknięciem nadal działa. Bez wybranego atakującego
  podglądy działają jak wcześniej.

## Walidacja automatyczna i granice

`tests/test_mvp_visual_consistency_0984.py` sprawdza dziewięć scenariuszy:
- geometrię każdego z 20 skierowanych połączeń w obu rzędach;
- aurę między rzędami i brak kreski przez HUD oraz brak mutacji audytu;
- dostępność podglądu przy zwykłym hoverze i blokadę podczas ataku;
- końcowe skalowanie okna bez wygładzania;
- rzeczywistą wybieralność kart aukcyjnych i niemutowalność renderowania;
- brak rysowania tekstu na środku portretu celu ataku;
- ostre skalowanie starszych sprite'ów aukcyjnych;
- kwadratowy pocisk ataku i narożniki trafionych kart.

**Pozostała ręczna kontrola:** na fizycznym Windows 10/11 należy sprawdzić
1366×768, Full HD i DPI 100/125/150%, obejrzeć wszystkie trzy oferty
aukcyjne oraz kadrowanie postaci, przetestować czytelność małych napisów
przy niestandardowym rozmiarze okna i pełną partię od startu do końca.
Automatyczny zielony test Pygame nie zastępuje oceny wyglądu na ekranie.
