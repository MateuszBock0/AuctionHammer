# Porównanie AuctionHammer MVP 0.9.1 SOLO z Game Master v17

Data źródła: 2026-10-16. Podstawą porównania były: Game Master v17 MD, `data/GAME_MASTER.json`, `game_rules_v17.json`, `starter_bank_v17.json`, `event_order_v17.json`, lista 70 kart oraz testy integralności danych. Wersja bieżąca nie implementuje aukcji ani jej katalogu kart.

## Potwierdzone i skorygowane

| Zagadnienie | Wynik |
|---|---|
| Katalog 70 kart | 70/70 identycznych z v17, bez zmian nazwy/ATK/HP/efektów/profili; oficjalna surowa lista JSON bez wrappera |
| Frakcje i rodziny | 5 × 14, unikalne archetypy, jeden fizyczny egzemplarz każdego ID |
| Początkowy bank i rozdanie | 70→20 rozdane (po 5 ręka + 5 talia) i 50 w banku |
| Mulligan | poprawiony: dwie niejawne deklaracje, następnie wymiana; odrzucone do strefy `excluded`, **bez zwrotu do banku** |
| Brak timerów | brak limitów czasu i automatycznego kończenia tury po czasie |
| Koszt wystawienia | brak kosztów, brak zakupów i płatnych zdolności |
| Priorytet reakcji S103 | poprawiony: `ON_ATTACK` atakującego przed kontrreakcją i zwykłą walką |
| Pasywne efekty po ustawieniu | reakcja S108 odłożona do zakończenia własnego `ON_PLAY` |
| Trucizna | jedna zbiorowa fala obrażeń przy początku tury; skorygowana premia S107 (+1 do sumy, nie do każdego ticku) |
| Odporność | uzupełniono bonus pierwszej aktywacji S39 i efekt „Przy śmierci” S88 |
| Aura MAX HP | poprawiono cofanie pozytywnego bonusu MAX HP wraz z HP |
| UI | stała plansza logiczna, letterbox/skalowanie okna, mapowanie kliknięć, czytelny modal pełnego efektu i skalowania |

## Przeprowadzone testy

- 7 testów integralności pakietu v17 (`tests/test_data_integrity.py`), w tym 3000 syntetycznych scenariuszy mulliganu.
- 10 dotychczasowych testów jednostkowych/symulacji (`tests/test_engine.py`).
- 7 nowych regresji v17 (`tests/test_v17_regressions.py`), w tym 3+3 wymiany, kolejność ataku, S107/S108, cofanie aury i pięć rozdzielczości.
- 300 zakończonych partii AI kontra AI z kontrolą integralności stref kart przy każdym ruchu.
- Wykonano statyczną kontrolę składni modułów Pygame; **graficznego testu okna nie wykonano** (brak zainstalowanego `pygame-ce` w środowisku wykonawczym i brak dostępu do instalacji).

## Ograniczenia pozostałe do weryfikacji

- Silnik prototypowy **nie ma jeszcze pełnej, dowiedzionej implementacji atomowych fal wielu równoczesnych zdolności „Przy śmierci” zgodnej z każdym punktem `event_order_v17.json`**. Obecna kolejka może rozpatrywać część wyzwalaczy sekwencyjnie i przy rzadkich kaskadach zmienić kolejność wyborów/konsekwencji względem v17.
- Test wywołania każdego z 70 handlerów potwierdza pokrycie kodu, lecz nie weryfikuje semantyki wszystkich złożonych interakcji 70 kart; konieczne są pełne testy przypadku per karta oraz testy kombinatoryczne aur/statusów.
- Czas trwania złożonych/nałożonych statusów, zwłaszcza ogłuszenia i premii przy „najbliższej własnej turze”, wymaga dalszych testów scenariuszowych z dokumentem v17.
- Skalowanie okna i hitboxy mają testy matematyczne, lecz wygląd dużego modala i ergonomia na konkretnych rozdzielczościach wymagają lokalnej inspekcji Pygame.
- Wyniki 300 samorozgrywek NIE są walidacją balansu PvP — komputer stosuje prostą heurystykę i rozgrywamy wariant bez aukcji.

Wniosek: aktualizacja przywraca zgodność z głównymi nowymi wymaganiami v17 i poprawia czytelność, ale nie jest uzasadnione ogłaszanie stuprocentowej wierności silnika bez wyżej opisanych dodatkowych testów.
