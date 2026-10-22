# AuctionHammer 0.9.53 — dopasowanie tekstów, UI/UX i odbiór Windows

## Założenia
W tej wersji nie zmieniamy mechaniki, kart, ekonomii ani AI. Wszystkie zmiany dotyczą prezentacji i dokumentacji. Długie słowa, adresy i napisy bez spacji nie mogą wychodzić poza obrys karty lub okna. Nie wolno ukrywać skrótu bez sygnału, że istnieje dalsza część tekstu.

## Zmiany implementacyjne
- `game/ui/text_fit.py`: wspólny pomiar szerokości w pikselach, dzielenie długich tokenów, jawny wielokropek po przekroczeniu maksymalnej liczby linii.
- `game/ui/card_view.py`: opisy rodzin i zdolności dopasowane do stref `card_zones`, bez naruszania paneli ATK, PŻ ani rozwoju.
- `game/ui/app.py`: ujednolicone zawijanie w panelach; krótkie opisy aukcji są limitowane do czterech czytelnych linii.
- Pełny podgląd aukcji zawiera cały tekst dzięki przewijaniu kółkiem myszy lub klawiszami ↑/↓ i PageUp/PageDown; wybór podglądu nie jest zakupem karty.
- README jest zorientowane na nowych graczy Windows, a dokumentacja techniczna została przeniesiona do linkowanych plików.

## Automatyczna macierz akceptacji
`tests/test_text_fit_0953.py` sprawdza:
1. **121 definicji/podwariantów:** 70 kart bazowych + 17×3 aktywne opisy aukcyjne.
2. **3 rzeczywiste prostokąty:** ręka 125×195, plansza 148×220, podgląd 255×380.
3. Każda linia opisu mieści się w rzeczywistej szerokości fontu; `family/main/footer/boxes` są wewnątrz `info`.
4. Długie niepodzielne ciągi z polskimi znakami są dzielone lub jawnie skracane.
5. Karty aukcyjne mają maksymalnie cztery linie w ofercie; pełny opis pozostaje przewijalny.
6. Ogólny zestaw testów jednostkowych, symulacji fixed-board, renderów Pygame i budowy ZIP Windows.

## Test na fizycznym komputerze Windows — PENDING
- [ ] Rozpakować wydanie ZIP, sprawdzić EXE i aktualizator.
- [ ] Powtórzyć UI przy DPI **100%, 125%, 150%**; przełączyć pełny ekran F11.
- [ ] Na każdej skali obejrzeć rękę, planszę, pełny opis i wszystkie trzy oprawy rzadkości; żadna litera nie wychodzi poza kartę.
- [ ] Otworzyć długie zdolności aukcyjne, przewinąć na koniec i zamknąć bez zakupu.
- [ ] Sprawdzić polskie znaki, długie nazwy, statusy, wielokropki i etykiety ATK/PŻ.
- [ ] Zagrać kartę kliknięciem i przeciągnięciem na wszystkie pola, w tym po śmierci jednostki i przy pełnej planszy.
- [ ] Sprawdzić klawiaturę, suwak aukcji, zapis/wczytanie oraz odsłuch muzyki.
- [ ] Potwierdzić brak błędów w odtwarzaniu podpisanej historii.

**Nie deklarujemy fizycznego PASS bez wykonania tych czynności na rzeczywistym systemie.**
