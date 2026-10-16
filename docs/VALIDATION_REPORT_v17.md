# WALIDACJA PAKIETU — v17 (2026-10-16)

## Dane sprawdzone
- Katalog: dokładnie 70 unikatowych ID i nazw.
- Macierz: 5 frakcji × 14 rodzin bez duplikatu kombinacji.
- Pula: dokładnie 70 unikatowych egzemplarzy, 1 na archetyp.
- Profile statystyk: dla każdej karty suma przyrostów na ręce wynosi +2 ATK/HP na własną turę.
- Reguły: 100 HP obydwu graczy, 0 pancerza, 3 monety startowe drugiego.
- Mulligan: maksymalnie 3, karty oddane do EXCLUDED_FROM_MATCH, bez możliwości ich dobierania.
- Brak limitów czasu na mulligan, turę, wybory i przyszłą aukcję.
- Nadrzędna kolejka zdarzeń: identyczna struktura reguł v15, maszynowy kontrakt v17.
- `GAME_MASTER.json` i `game_rules_v17.json`: pełna zgodność sekcji `rules`.
- Excel: nowy arkusz ZASADY v17 i poprawione przestarzałe komunikaty w macierzy/katalogu. Brak wykrytych błędów #REF!, #VALUE!, #N/A itd.

## Automatyzacja
`python -m unittest discover -s tests -v`: **7 / 7 testów zaliczonych**; test mulliganu wykonany dodatkowo na **3000 losowych scenariuszy** z zachowaniem liczby kart i brakiem duplikatów.

## Ważne ograniczenie
To są kontrole spójności PLIKÓW i matematyki przydziału, **nie testy działającego silnika gry**. Historyczny prototyp bitew i aukcji nie implementuje wszystkich 70 efektów zgodnie ze specyfikacją. Nie zweryfikowano jeszcze rzeczywistego balansu PvP ani produkcyjnego netcode'u. Katalog aukcyjny nadal odłożony na późniejszy etap.
