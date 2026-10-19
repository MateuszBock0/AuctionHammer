# AuctionHammer 0.9.35 — czytelność stałych cech jednostek i animacji walki

## Dokładnie trzy filtry zatwierdzone przez użytkownika

| Cecha na jednostce | Filtr na całej karcie | Przezroczystość | Priorytet |
| --- | --- | --- | --- |
| **Tarcza / Ochrona** | delikatny żółto-złoty `RGBA(255,210,64,37)` | ok. 15% | 1 |
| **Prowokacja** | delikatny srebrnoszary `RGBA(184,192,205,43)` | ok. 17% | 2 |
| **Podwójny atak** | delikatny czerwony `RGBA(227,69,78,37)` | ok. 15% | 3 |

Inne statusy **nie otrzymują żadnych dodatkowych pełnokartowych filtrów**: trucizna, ogłuszenie, regeneracja, wyciszenie, pancerz i Szybki atak zachowują dotychczasowe etykiety/informacje w panelu i szczegółach. Filtr dotyczy jedynie jednostek fizycznie wystawionych na planszę; karty na ręce nie zostają zabarwione.

Gdy jednostka ma kilka spośród trzech wymienionych cech, wyświetlany jest **jeden** filtr o najwyższym priorytecie, nie suma filtrów. Wszystkie efekty pozostają dostępne w istniejącym panelu statusów. Kolory nie modyfikują żadnej zasady silnika.

## Animacja pojedynku (tylko warstwa prezentacyjna)

1. Najpierw silnik rozstrzyga atak, zgon, prowokację, tarczę, pancerz i następstwa śmierci; zapisane stany są autorytatywne.
2. Na podstawie zatwierdzonego komunikatu `atakuje:` podświetlane są obie walczące jednostki (a przy ataku bohatera — karta atakująca). Obwódka trwa do ok. 430 ms.
3. Wartość PŻ na karcie zmienia się płynnie od poprzedniego do nowego stanu (ok. 55–240 ms). Silnik **nie przelicza ani nie opóźnia** obrażeń na potrzeby animacji; dotyczy tylko liczby wyświetlonej.
4. Jeśli faktycznie wydarzył się `Zgon <nazwa>.`, zapamiętywany jest jedynie **wizualny** obraz jednostki, który pokazuje PŻ spadające do zera, a po ~220 ms rozpoczyna wyszarzanie (ok. 145 ms) i zanika do 440 ms. Karta została już usunięta ze stanu silnika.
5. Zastąpienie, wygnanie lub inne usunięcie bez rzeczywistego `Zgon` **nie** uruchamia ani napisu `ZGON`, ani szarej animacji zgonu.
6. Wyłączenie animacji w menu ukrywa dodatkowe efekty i interpolację PŻ, zachowując autorytatywny stan gry oraz trzy filtry cech. Powtórka oglądana klatka po klatce nadal prezentuje zatwierdzone stany.

## Pozostałe uzgodnione poprawki UI

- **Historia meczów:** w przycisku każdego zapisanego meczu pokazywana jest wersja (`v0.9.32`, `v0.9.34` itd.); osobna informacja wyjaśnia, że archiwum może zawierać różne wersje i historyczne zasady. **Nie** rozbijamy obecnego indeksu: mogłoby to utrudnić istniejącym graczom odnajdywanie starych meczów.
- **PŻ bohaterów:** ekran gry i ekran końcowy już clampowały PŻ do 0. Do podpisanej sekcji `summary` audytu dodano wyłącznie pole **`hero_hp_display`** z `max(0, raw_hp)`; historyczne dokładne `hero_hp` oraz `final_state` pozostają bez zmian dla replaya.
- **Brak legalnego celu:** zdolność bez celów na początku kolejki lub w fali śmierci może jawnie podać przyczynę braku aktywacji. Nie dodano wymyślonego efektu zastępczego ani zmian w statystykach.
- **Otwarte kwestie projektowe, nie bugi wykonania:** A018 przy ostatniej aukcji; S86/S87/S88 bez sojuszników; interpretacje szczególnych zdolności A014/A015. To oddzielny backlog, nie część niniejszego release.
- **Kompatybilność:** pola wersji i `hero_hp_display` są wyłącznie dodatkowymi danymi w nowych audytach. Archiwa dawnych wersji pozostają czytelne.

## Kontrola jakości

`tests/test_signature_overlays_and_combat_0935.py` testuje dokładnie trzy filtry i ich kolejność, brak filtra od krótkich statusów, animację obu walczących, malejące PŻ, prawdziwy zgon, brak fałszywego zgonu po usunięciu karty i wersję w menu archiwum. Zmieniono przestarzały scenariusz `test_game_experience_0914.py`, który wcześniej uznawał dowolne usunięcie jednostki za zgon.

Testy UI używają pygame-ce z driverem SDL dummy; brak klatek lub ręcznego GUI na Windows nie powinien być mylony z pełną walidacją estetyki na ekranie użytkownika.
