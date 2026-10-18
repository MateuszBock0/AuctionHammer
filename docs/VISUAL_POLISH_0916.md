# AuctionHammer 0.9.16 — Visual Polish Pass

**Zasady:** Game Master v19, 70 kart bazowych, bez aukcji i kosztów zagrania.
**Rozmiary kart:** ręka 125×195, plansza 148×220, szczegóły 255×380.

## Wykonane zmiany

### Tło, stół i panele
- Nowy deterministyczny generator tła `game/ui/visual_theme.py`:
  kamienny kolor, drobne ziarno, grawerowane sigile i subtelne winietowanie.
  Generowany tylko raz, offline, bez pliku zależnego od serwera.
- Wizualne rozdzielenie stref AI, gracza i ręki, półprzezroczyste powierzchnie
  oraz subtelne zdobienia; tekst ma kontrastową podkładkę.
- Panele mają cienie, jasną krawędź i metaliczny bevel. Sloty otrzymały
  granice zależne od strony (zielonkawa gracz, purpurowa komputer).
- Przyciski mają wyraźne stany zwykły/hover/wciśnięty/wyłączony.

### Karty
- Złota listwa u góry ramy, dekoracje sekcji statystyk i treści
  oraz delikatne grawerowane szczegóły tła zastępczego 63 kart.
- Wszystkie 35 ikon Minimal Fantasy pozostaje z 0.9.15. Nie generowano
  nowych obrazów poszczególnych archetypów; 7 istniejących ilustracji
  pozostaje bez zmian.
- Zdolności, ATAK, PŻ, triggery i przyrosty nadal rysowane są z
  rzeczywistych wartości v19. Płyty ATAK/PŻ są nieprzezroczyste i
  rysowane po ornamentach.
- Wymiar i geometria hitboxów bez zmian.

### Animacje
- Lepszy easing pocisków, ślady ataku, cień liczby obrażeń/leczenia.
- Krótkie kręgi przy zastosowaniu statusów, iskry śmierci, wejście nowej
  jednostki oraz dyskretny krąg na bohaterze przy zmianie tury.
- Animacje mają ograniczoną liczbę cząstek, nie wywołują akcji silnika,
  dają się wyłączyć klawiszem **A** i nie zasłaniają statystyk.

### Czytelność i usunięte kolizje
- Nagłówek ma trzy rozłączne obszary: logo, tryb, pomoc klawiszowa.
  Opis skrótów jest ograniczany do szerokości swojego obszaru.
- Log jest ograniczany **szerokością fontu**, nie liczbą znaków.
- Panel boczny pokazuje dwie pozycje statusów + licznik dalszych efektów
  na osobnej linii, powyżej przycisku [I]; nie kolidują już.
- Przycisk po zakończeniu partii przeniesiono **do panelu wyniku**,
  wraz z obsługą kliknięcia w nowym miejscu.

## Testy akceptacyjne

`python -m unittest discover -s tests -v`

`python tools/render_minimal_fantasy_preview.py`

`tests/test_visual_polish_0916.py` weryfikuje:
- fizyczną szerokość napisów (font Pygame), rozłączne regiony nagłówka,
  planszy, panelu, menu, historii, powtórki i ekranu wyniku;
- brak zderzenia dodatkowych statusów i przycisku szczegółów;
- 70 kart × 3 rozmiary, statystyki w wydzielonych obszarach;
- kliknięcia przy DPI 100/125/150% (mapowanie logiczne);
- wyłącznie kosmetyczny efekt zmiany tury i renderowanie tekstur.

Dodatkowe zrzuty rzeczywistego Pygame obejmują planszę, menu, ustawienia,
historię, kartę szczegółową, VFX, powtórkę, koniec oraz trzy rozdzielczości:
1920×1080, 1536×864 i 1280×720. Pliki `VISUAL_0916_*.png`.

## Ograniczenia

- Testy rozłączności mierzą wyrenderowane prostokąty napisów aplikacji
  na logicznym płótnie oraz geometrię opisów 70 kart, a **nie**
  percepcyjną czytelność każdego szczegółu po przeskalowaniu przez sterownik DPI.
- W systemach o niskiej rozdzielczości cały canvas może zmniejszyć fonty.
  Konieczny ręczny odbiór na laptopie przy DPI 100/125/150% i fullscreen.
- Motyw to proceduralne tekstury Pygame i ulepszone obramowania,
  bez zamiany 63 ilustracji zastępczych na ręcznie rysowane postacie.
- Brak zmian logiki walki, AI, kolejek zdarzeń i definicji kart.
