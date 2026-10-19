# Audyt 100 historii meczów v22: usterki i przewaga pełnej planszy

Badane: 100 pełnych audytów (seedy 220000–220099, commit 8a0ece39), osobny audyt użytkownika seed 1571013625 oraz bieżący kod silnika. Data: 19.10.2026. To przegląd śledczy, NIE aktualizacja zasad.

## Weryfikacja

100/100 archiwów JSON.GZ ma poprawny SHA-256. Odtworzenie zmian stanu obu graczy z 21 113 komend od początku do końca daje zgodne stany końcowe w 100/100 meczach. 0 komend odrzuconych, 39 384 operacje wewnętrzne, 46 200 zdarzeń.

## Potwierdzone błędy

1. **S11, Jadowita Żmija.** 13 aplikacji trucizny na bohatera przekazuje bonus jakości 1, ale zapisuje bonus_once=0; 12 aplikacji na jednostki poprawnie zapisuje bonus_once=1. Reproducer: seed 220051, internal_events seq 84, action_seq 41. Usterka: engine._add_poison w gałęzi hero nie ustawia bonus_once.

2. **A015, Wieszczka.** Silnik anuluje zdolność S04/S08 przed wyborem jej wariantu i celu, ponieważ dowolna dostępna opcja ofensywna oznacza cały efekt jako ofensywny. Udokumentowano trzy zdarzenia: seed 220005 seq 235 (S04), seed 220037 seq 415 (S04), seed 220023 seq 278 (S08). Gracz nie mógł wybrać przyjaznego wzmocnienia, lecz nie wiadomo, co wybrałby po udostępnieniu takiej decyzji.

3. **S85, Życiodajne Widmo.** Etykieta efektu po śmierci dla własnego bohatera mówi o ochronie, choć silnik wykonuje leczenie o 4 HP (+ poziom). Błąd opisu.

## Wady AI i problem planszy

- W 181 turach aktywny gracz kończył przeciwko 5 wrogim jednostkom; we wszystkich tych przypadkach był późniejszym przegranym. Miał własnych jednostek: 0 (1 raz), 1 (173 razy), 2 (7 razy). Zwycięzcy kończyli turę ze średnio 2,812 jednostki; przegrani z 1,466.
- AI nie wybrało A011 ani razu, choć oferowano je 151 razy. Algorytm wyboru aukcyjnego maksymalizuje HP, a następnie rzadkość, nie wycenia ATK i efektu.
- Karty wybrane przez zwycięzców aukcji miały średnio 4,57 ATK i 13,59 HP; karty drugich wybierających 5,38 ATK i 12,78 HP. W obu grupach średnia suma ATK+HP wynosiła 18,16. Ten wybór AI może zwiększać siłę ofensywną gracza przegrywającego licytację.
- Średnie końcowe portfele wynosiły 24,63 monet u zwycięzcy i 15,25 u przegranego. W 29/100 meczów jedna ze stron kończyła z ponad 30 monetami.

## Proponowane dodatkowe monety za wolne pola

Reguła badana: po wszystkich efektach końca własnej tury przyznać 5 - liczba własnych jednostek dodatkowych monet, niezależnie od istniejących źródeł dochodu.

Wsteczne oszacowanie na 3494 turach: 10 011 dodatkowych monet, z czego 6212 dla późniejszych przegranych i 3799 dla późniejszych zwycięzców. Wynik ten nie uwzględnia zmiany decyzji aukcyjnych i nie jest prognozą nowej reguły.

**Kontrolowane A/B: 800 ukończonych meczów v22, 0 awarii.** Na 200 identycznych seedach dla normalnego AI pierwszy gracz wygrywał 75,5% meczów bez bonusu i 82,0% z bonusem; dla trudnego AI 76,0% i 79,0%. Przy normalnym AI udział pierwszego gracza w wygranych aukcjach zmalał z 17,3% do 0,18%, ale nie uratowało to równowagi meczu.

Wniosek: nie wprowadzać tej zmiany do produkcji jako mechaniki wyrównującej w obecnej konfiguracji AI. Priorytet: usterki S11/A015, następnie wycena kart i ofert w AI, następnie ponowny test ekonomii. To nie jest dowód, że propozycja nie działałaby podczas rozgrywki człowiek–człowiek.

## Powtarzalność

- Pełne audyty: https://github.com/MateuszBock0/AuctionHammer/actions/runs/39245756098
- Badanie A/B: https://github.com/MateuszBock0/AuctionHammer/actions/runs/39252260139
- Kod badawczy i testy: PR #41
