# AuctionHammer 0.9.52 — odbiór UX stałych pól i rzadkości

## Poprawki w kodzie
- Upuszczenie karty w przerwie między polami nie powoduje niejawnego wystawienia na pierwsze wolne pole.
- Przeciąganie karty podświetla legalne miejsca bez konieczności wcześniejszego kliknięcia.
- Bez zmian w silniku, aukcjach, ekonomii, RNG, danych kart i zapisach audytu.

## Automatyczna walidacja
Nowy plik `tests/test_board_ux_0952.py` obejmuje:
1. Przeciągnięcie na ostatnie pole przy oknach 1480×980, 1184×784 i 986×653.
2. Upuszczenie pomiędzy polami, bez niejawnej komendy silnika.
3. Upuszczenie na planszę przeciwnika, bez wykonania zagrania.
4. Próbę zajęcia istniejącej jednostki bez pełnej planszy.
5. Legalną wymianę przy pełnej planszy, bez przesunięcia pozostałych jednostek.
6. Wystawienie nowej jednostki w luce po śmierci, bez przesunięcia sąsiadów.
7. Podświetlenie legalnych pól podczas trzymania nieklikniętej wcześniej karty.
8. Oddzielne ramki brązowe, srebrno-błękitne i złote bez zamalowywania wnętrza karty.

Pozostałe CI: pełne testy `unittest`, renderowanie Pygame, 20 kompletów fixed-board z podpisanymi audytami, 100 meczów AI z audytami i Windows ZIP / launcher.

## Ręczne testy na fizycznym komputerze z Windows (PENDING)
- [ ] Uruchomić gotowy ZIP przy skali DPI 100%.
- [ ] Powtórzyć przy 125%.
- [ ] Powtórzyć przy 150%.
- [ ] Kliknąć każde wolne pole, upuścić kartę w przerwie, ponowić po śmierci jednostki.
- [ ] Zweryfikować podmianę na pełnej planszy oraz wskazania S34/S108.
- [ ] Porównać podstawowe, rzadkie i legendarne oprawy na ręce, planszy i aukcji.
- [ ] Sprawdzić długie opisy, statusy, animacje ON/OFF, zapis/odczyt i historyczne audyty.

**Nie oznaczać ręcznej akceptacji jako PASS bez fizycznego testu.**
Geometryczne symulowanie DPI w CI nie jest ekwiwalentem rzeczywistego renderingu monitora.
