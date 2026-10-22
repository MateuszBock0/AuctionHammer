# AUCTIONHAMMER — AKTUALNY KONTEKST PROJEKTU CHATGPT

**Data:** 22.10.2026  
**Projekt:** AuctionHammer (repozytorium: https://github.com/MateuszBock0/AuctionHammer)  
**Aktualna linia:** MVP 0.9.53, kontynuacja wydanego 0.9.52.

> Ten plik jest bieżącą nakładką informacyjną. Stare załączniki `GAME_MASTER.md`, `GAME_MASTER.json` oraz `karty_startowe_macierz_efektow_v14.xlsx` są **historycznymi źródłami v14** i nie mogą nadpisywać nowych reguł. Nie usuwamy ich zawartości ani nie aktualizujemy ich kart metodą zgadywania.

## 1. Wymagania nienegocjowalne dla MVP

- **Jedna osoba przeciw AI; offline Windows.** Nie projektować multiplayera, lokalnego trybu dwuosobowego, lobby ani infrastruktury sieciowej jako części MVP.
- Silnik w **Python 3.12**, interfejs **pygame-ce**, nazwa folderu i repozytorium **AuctionHammer**.
- **70 różnych kart bazowych po 1 egzemplarzu**; wszystkie są obecne w `data/cards_base_70.json`, normalne zagranie nie kosztuje monet.
- **17 archetypów aukcyjnych** × 3 poziomy rzadkości = **51 działających wariantów zdolności** w aktywnym katalogu v22; aukcje co 3 pełne rundy (zależnie od dostępności).
- **100 PŻ** każdego bohatera na początku, 5 kart na ręce i 5 w talii; mulligan do 3 kart.
- **Maksymalnie 5 stałych fizycznych pól** po każdej stronie. Śmierć nie przesuwa jednostek; nową kartę wybiera się na konkretne wolne pole, na pełnej planszy obowiązują reguły zastępowania. S34 działa na faktycznych sąsiadów, S108 na faktycznego przeciwnika naprzeciw.
- **Drugi gracz wybiera** na początku Chorążego 2 ATK / 5 PŻ albo **+3 monety**. Chorąży zajmuje pole i nie atakuje w swojej pierwszej turze. Starsze podpisane mecze odtwarzają swoje wcześniejsze zasady.
- Monety: +1 każdemu po pełnej rundzie, dodatkowy dochód za własne wolne pola na koniec tury w aktywnej ekonomii v22. Zasady i kolejność zdarzeń określa silnik v23.
- Gra ma historię starć, podpisane audyty, zapis/wczytanie, samouczek, 3 poziomy trudności AI i instalator Windows z SHA-256 oraz rollbackiem.

## 2. Źródła pierwszeństwa przy sprzecznościach

1. **Aktualny, przetestowany kod silnika:** `game/core/`, aktywna konfiguracja `SoloApp`, `VERSION.json`.
2. **Aktualne dane:** `data/cards_base_70.json`, `data/auction/KATALOG_AUKCYJNY_17_v22.json`, `data/GAME_MASTER.json`, `data/event_order_v19.json`.
3. **Obowiązujące aneksy:** `docs/GAME_MASTER_v23_ADDENDUM.md`, `docs/BOARD_CARD_IDENTITY_0951.md`, `docs/CHOICE_AND_UI_0941.md` oraz README.
4. Historyczne `GAME_MASTER_v14`, v17 i starsze raporty — tylko do prześledzenia ewolucji decyzji, **nie** do przywracania starych mechanik.

Nie zmieniać arbitralnie nazw, parametrów ani opisów istniejących kart. Opisy UI powinny być zgodne z realnym działaniem silnika; testy nie zastępują walidacji treści danych.

## 3. Status implementacji

- **0.9.52 wydane**: stałe pola, rozpoznawalne kolory rzadkości, poprawiony drag-and-drop, 645 testów, symulacje 20 meczów z podpisanym replayem, Windows ZIP.
- **0.9.53 zakres**: czytelność kart i aukcji, zawijanie według pikseli, przewijany pełny opis zdolności, czytelniejsze README, testy 70+51 wariantów w trzech rozmiarach, aktualizacja kontekstu projektu.
- Odbiór fizycznego Windows 100/125/150% DPI, audio i myszy **PENDING** do wykonania przez człowieka na rzeczywistym sprzęcie. Nie deklarować PASS za symulację w CI.
- Rozszerzone badania balansu pierwszego gracza/heurystyk AI są odrębne od zmian kosmetycznych; nie zmieniać monet czy statystyk tylko na podstawie starych symulacji.

## 4. Zakres kolejnych prac

1. Domknąć UI/UX oraz zweryfikować czytelność kart na ekranie Windows.
2. Analizować zachowanie i jakość AI w grach solo.
3. Oceniać balans bez zgadywania wartości kart.
4. Stabilizować wydanie single-player MVP; nie rozszerzać prac o multiplayer.

## 5. Zasada synchronizacji

Jeżeli ten plik jest starszy od bieżącego `VERSION.json` albo rzeczywistego kodu, **GitHub na `main` ma pierwszeństwo**. Nie twierdzić, że projekt ChatGPT automatycznie aktualizuje załączniki z GitHubem. Aktualne pliki dostarczone do ChatGPT należy wymienić lub uzupełnić ręcznie w ustawieniach projektu.
