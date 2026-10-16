# AUCTIONHAMMER — PLAN IMPLEMENTACJI (v17, 2026-10-16)

## Stan
Specyfikacja podstawowej gry jest zatwierdzona. **Nie oznacza to, że silnik jest napisany lub pełna gra zbalansowana.** Nie wprowadzamy dodatkowych pytań o zakończone mechaniki; implementujemy dane i deterministyczną kolejkę z Game Master v17.

## Etap 1 — MVP bez aukcji
1. Dane: wczytaj `data/cards_base_70.json`; utwórz dokładnie 70 fizycznych kart, bez duplikatów. Gracze dostają 5+5, pozostałe 50 tworzy bank zamienników; odrzucone w mulliganie trafiają do `EXCLUDED_FROM_MATCH`.
2. Silnik autorytatywny i deterministyczny: model gry, walidacja akcji, dokładna kolejka `data/event_order_v17.json`, historia zdarzeń, rozstrzyganie fal zgonów.
3. Wszystkie 70 tekstów zdolności przełóż na deklaratywne efekty/handler'y. Nie wyciągaj reguł kolejności z tekstu jednej karty.
4. Reguły walki, HP/ATK, zasłony, tarcze/pancerz, trucizna, ogłuszenie, regeneracja, aura, wyciszenie, prowokacja i czyszczenie.
5. Karty na ręce +2 statystyk co własną turę i specyficzne progi zdolności co 3 tury, reset stanu po opuszczeniu planszy.
6. Ekonomia: 0/+3 monety na start, +1 każdemu po rundzie, monety za zgony i progi bohatera. Bez płatnych kart startowych.
7. Interfejs lokalny dla dwóch osób, bez timerów. Dla MVP **nie generuj kart ani ofert aukcyjnych**.
8. Testy jednostkowe, testy interakcji, losowe partie z logowaniem i regresja 70 definicji.

## Etap 2 — dopiero po MVP
Odrębnie zaprojektować ok. 36 archetypów aukcyjnych, trzy rzadkości i poziomowanie, koszty płatnych umiejętności. Następnie wdrożyć ustaloną procedurę aukcji co 3 pełne rundy.

## Etap 3 — testy rozgrywki i produkt
Walidacja rzeczywistej przewagi pierwszego gracza przy +3 monetach dla drugiego, balans synergii, sieć multiplayer, lobby, UI, grafika, historia rozgrywek.

## Niewymagające ponownej decyzji
Jedna wspólna pula 70 niepowtarzalnych kart; odrzucone w mulliganie niedostępne dla obu graczy; 100 HP, 0 pancerza; premia +3 monet drugiego; brak limitów czasu; nadrzędna kolejka w sekcji 7; skalowanie i przyrost zdolności. Historyczne wyniki symulatora nie stanowią obowiązującej oceny balansu.
