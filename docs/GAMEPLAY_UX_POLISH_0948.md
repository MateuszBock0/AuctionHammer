# AuctionHammer 0.9.48 — Gameplay UX Polish + verified card copy

## Podstawa i integralność
- Punkt wyjścia: wersja 0.9.47, commit 75c6415b23d596a015de1881116975f7e24e487b.
- Paczka autora: AuctionHammer_OPISY_KART_POPRAWKI_ZWERYFIKOWANE_0.9.46.1(2).zip, poprzedni commit da6da01a93e34570ac5596428d3fc6bf96fdb853.
- Manifest SHA-256: wszystkie 13 z 13 plików poprawne.
- Żadnej edycji game/core, data, modelu kart, aukcji, schematów save i audytu.

## UX 0.9.48
1. Wspólny HUD: samouczek i licznik kart/ataków są widoczne jednocześnie podczas tury.
2. Wystawianie: złoty obrys tylko na faktycznym miejscu dopisania jednostki (Match.play dopisuje ją do końca planszy). Pełna plansza oznacza prawdziwe cele zastąpienia.
3. Komunikaty walki: bounded FIFO maksymalnie 24 pozycji, każda przez 2.6 s, w panelu 2 wiersze i odnośnik H do pełnego, nieograniczonego event_journal.
4. Karta: czytelna reguła dodatkowa v23 na panelu, spójny pełny opis w szczegółach zamiast zduplikowanych technicznych opisów.
5. Aukcja: przycisk PEŁNA ZDOLNOŚĆ na każdej z trzech ofert, modal podglądu nie powoduje złożenia oferty ani zakupu.

## Zweryfikowane opisy
- 13 bazowych SPECS: S05, S07, S12, S15, S27, S59, S74, S78, S84, S85, S97, S99, S108.
- 5 dodatkowych reguł tylko v23: S86, S87, S88, S32, S95.
- 7 wariantów aukcyjnych: A014 wszystkie trzy rzadkości; A015 wszystkie trzy; A018 legendarna.
- Rozpoznanie wariantów v22/v4 na podstawie dokładnie kanonicznych tekstów, nie samej etykiety poziomu.
- Wszelkie stare CardDefinition.effect pozostają niezmienione; nowa warstwa wyłącznie zwraca tekst renderowania.

## Testy
- test_card_copy_contract_0948.py: 70 kart i poziomy 0/1/3, 13 gałęzi, siedem opisów v23, brak wycieków do v22/v4, historyczne A010, niekanoniczne opisy nie mogą udawać AKTYWNYCH.
- test_gameplay_clarity_0947.py: samouczek + HUD, pojedyncze faktyczne pole, sekwencja potwierdzonych zdarzeń.
- pełny unittest/pygame, Windows EXE/ZIP/launcher, 100 pełnych audytów i historyczne replays na CI.

## Ograniczenie odbioru
Żaden test automatyczny nie zastępuje wizualnego odbioru na Windows DPI 100/125/150%, zwłaszcza panelu kart o długich polskich nazwach. Podgląd aukcji pozostaje prezentacją, nie ingeruje w mechanikę licytacji.
