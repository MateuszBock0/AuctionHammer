# AuctionHammer MVP 0.9.14 — Game Experience

**Specyfikacja:** Game Master v19. **Aukcje:** wyłączone. **Koszty kart:** brak.

## Wdrożone funkcjonalności

1. **Animacje walki** — lekkie pociski ataku, unoszące się liczby obrażeń i leczenia,
   efekty trucizny, tarczy, pancerza, ogłuszenia, regeneracji, Szybkiego i
   Podwójnego ataku, a także rozsypanie punktów przy śmierci jednostki.
   Warstwa tylko odczytuje zatwierdzone stany i dziennik silnika.
   Klawisz **A** wyłącza/włącza animacje.
2. **Pakiet ikon Minimal Fantasy** — 14 rodzin, 16 typów statusów, 5 frakcji
   w spakowanym atlasie PNG (`assets/ui/icons/icon_atlas_35.png`).
   Konwersja z dostarczonych ikon 64 px do 24 px, 24 kolory; bez zmian
   semantycznych. Oryginalne pliki 64/128/256 px można później dołączyć
   do katalogów `assets/ui/icons/`, a loader automatycznie je wybierze.
   Nazwy odporności na truciznę i ogłuszenie są rozróżnione.
3. **Pełna historia zdarzeń** — nieograniczony licznik w pamięci żywego
   meczu, niezależny od dawnych 160 pozycji podręcznego logu.
   **H** otwiera widok, strzałki/kółko myszy przewijają.
4. **Powtórki stanów** — po każdym rozstrzygniętym kroku silnika zapisujemy
   migawkę do oglądania bez modyfikacji meczu. **P** otwiera, strzałki
   lewo/prawo przewijają, **Esc/P** wraca. Limit 480 klatek w pamięci.
5. **Menu główne i ustawienia** — start aplikacji, Nowy mecz, Kontynuuj,
   Wczytaj zapis, Ustawienia, efekty WŁ/WYŁ, F11 i poziomy AI.
   **M** otwiera menu bez kończenia meczu.
6. **Bezpieczny zapis/wczytanie** — JSON do folderu danych użytkownika,
   z kontrolą sumy i zgodności v19, stanem RNG, statusami, kolejkami i
   aktywnymi wyborami. Nie korzysta z niebezpiecznego pickle.
7. **AI** — Łatwy / Normalny / Trudny. Trudny priorytetyzuje synergiczne
   wystawianie kart, zabójcze ataki na bohatera i sytuację na planszy.
   `python tools/simulate_ai_levels.py --games 1000` wykonuje
   reprodukowalne pojedynki na silniku v19.
8. **Podsumowanie meczu** — runda, PŻ, poległe jednostki, monety,
   liczba zdarzeń i zapisanych stanów.

## Pliki

- `game/ui/combat_visuals.py`: animacje i efekty tylko-do-odczytu.
- `game/ui/game_icons.py`, `assets/ui/icons/icon_atlas_35.png`: ikony.
- `game/ui/match_history.py`, `game/core/engine.py`: dziennik i powtórki.
- `game/core/persistence.py`: zapis i wczytywanie.
- `game/core/ai.py`, `tools/simulate_ai_levels.py`: AI i benchmark.
- `game/ui/app.py`: ekrany menu, historii, odtwarzania i integracja UI.
- `tests/test_game_experience_0914.py`: kontrola regresji.
- `tools/render_minimal_fantasy_preview.py`: rzeczywiste zrzuty Pygame.

## Uczciwie opisane ograniczenia

- Powtórka służy do oglądania **zatwierdzonych stanów**, a nie każdej
  mikrooperacji podczas wspólnej fali zgonów. Migawki nie trafiają do
  pliku zapisu, zatem po wczytaniu dostępne są nowe migawki od tego
  momentu; pełen tekstowy dziennik jest zachowany.
- Efekty VFX są wynikiem różnic dwóch ukończonych kroków, więc jeżeli
  jednostka zostaje zabita i usunięta w jednym kroku, najpierw
  wyświetlamy śmierć, a nie wszystkie pośrednie obrażenia.
- AI Trudny ma rozbudowaną heurystykę, ale nie jest minimax/MCTS.
  Wyniki rzeczywistego benchmarku decydują o jakości. Nie deklarujemy
  ostatecznego balansu.
- Tryb wyboru przeciwnika dotyczy obecnie wyłącznie AI. Lokalny PvP
  i multiplayer nie są częścią wydania.
- Spakowany atlas 24 px jest zoptymalizowany do małych kart, nie jest
  oryginałem 256 px.
- Testy Pygame/Windows wymagają uzupełniającej kontroli czytelności przy
  DPI 100%, 125% i 150%.

## Wymagania odbiorcze

`python -m unittest discover -s tests -v`

`python tools/render_minimal_fantasy_preview.py`

Przed wydaniem wymagamy zielonego CI oraz pomyślnie zbudowanego
`AuctionHammer.exe`. Użytkownik otrzyma aktualizację przez standardowy BAT.
