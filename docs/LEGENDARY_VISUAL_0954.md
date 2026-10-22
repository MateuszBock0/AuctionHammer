# AuctionHammer 0.9.54 — Legendary Visual Identity

## Cel

Legendarna karta aukcyjna ma być **natychmiast rozpoznawalna** bez zasłaniania ważnych informacji. Rozszerzamy istniejącą oprawę złotej ramki oraz klejnotu znaną z 0.9.51. Rozgrywka pozostaje **single-player przeciw AI**.

## Implementacja w Pygame

- `VisualTheme.legendary_underlay`: głęboki ametystowo-aksamitny podkład tylko pod istniejącymi panelami i w wąskich marginesach karty.
- `VisualTheme.legendary_artwork`: delikatna złoto-fioletowa warstwa i promienie **wewnątrz ilustracji**. Nie zmienia oryginalnego pliku graficznego. Efekt statyczny działa również bez animacji.
- `VisualTheme.legendary_offer_ornament`: narożne motywy i pełna złota ramka na legendarnej ofercie aukcyjnej oraz w jej szczegółowym podglądzie.
- `CardView.draw`: poziom rzadkości odczytywany przed renderowaniem i używany również do wyboru podkładu/wykończenia ilustracji.
- `SoloApp._draw_details`: rzadkość przekazywana jawnie z aktywnych metadanych zakupionej karty; awans rzadkości odzwierciedla się w podglądzie.
- `self.animations_enabled` kontroluje wyłącznie pulsowanie, **nie rozpoznawalność koloru i dekoracji**.

Karty podstawowe i rzadkie zachowują dotychczasowe oprawy. Nie zmieniamy nazwy, tekstu zdolności, frakcji, liczby ataków, ATK/PŻ, statusów, ani liczbowego modelu ekonomii i aukcji.

## Automatyczne testy

`tests/test_legendary_visual_0954.py`:

1. Dla rozmiarów 125×195, 148×220 i 255×380 porównuje renderowanie karty rzadkiej i legendarnej.
2. Piksele w środku paneli `name`, `trigger`, `info` i `stats` muszą pozostać identyczne, a ilustracja i rama muszą się różnić.
3. Tryb animacji OFF renderuje obraz identyczny przy powtórzeniu, bez odwołań do zegara Pygame.
4. Ornamentalny panel aukcyjny zmienia narożniki, ale zachowuje centrum obszaru opisu.
5. Warianty podstawowe/rzadkie mają identyczny obszar ilustracji; tylko wariant legendarny otrzymuje nowe wykończenie.

Obowiązują również pełne testy silnika i interfejsu, audyty fixed-board, rendering screenshotów i pipeline Windows Release. Wszystkie testy należy ocenić na **końcowym commicie**, nie na poprzednich nieudanych próbach.

## Ręczny odbiór na komputerze Windows — PENDING

- [ ] Sprawdzić aukcję z legendarną ofertą; ornamenty nie zasłaniają kwoty, tekstu, przycisku `PEŁNA ZDOLNOŚĆ` ani wyboru.
- [ ] Sprawdzić tę kartę na ręce, planszy, w pełnym opisie i po zmianie rzadkości.
- [ ] Porównać oprawy na trzech wielkościach wyświetlania Windows: DPI 100%, 125%, 150%.
- [ ] Wyłączyć animacje klawiszem `A`; sprawdzić brak pulsowania i zachowanie kontrastu.
- [ ] Sprawdzić kartę ogłuszoną/nieaktywną, z wieloma statusami oraz zaznaczoną ramką.
- [ ] Sprawdzić dostępność polskich opisów, pełnego przewijanego opisu aukcji i czytelność ATK/PŻ.

**Nie oznaczać fizycznego testu Windows jako zaliczonego bez rzeczywistego testu.**
