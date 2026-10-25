# AUCTIONHAMMER — AKTUALNY KONTEKST PROJEKTU 0.9.90 (patch v24)

**Wersja:** 0.9.90, balans aukcyjny v24 (sześć zatwierdzonych buffów). **Data:** 25.10.2026.

## Źródła prawdy
1. Kod silnika `game/core/engine.py`, `game/core/auction_abilities.py` i katalog `data/auction/KATALOG_AUKCYJNY_17_v22.json`.
2. `VERSION.json` to bieżący numer MVP; `docs/BALANCE_PATCH_V24_0990.md` zawiera wszystkie parametry tego patcha.
3. Historyczne `GAME_MASTER.md`, `GAME_MASTER.json` i macierz v14 oraz archiwalne `AUDYT_KRYTYCZNY.md` / `DECYZJE_DO_ZATWIERDZENIA.md` **nie są nadpisywane**. Wersja zatwierdzonego planu v24 to tylko sześć ostatnich zmian.
4. W projekcie ChatGPT aktualnym suplementem do historycznego GAME_MASTER jest `GAME_MASTER_PATCH_v24_0.9.90.md` i JSON z nowej paczki.

## Zakres niezmieniony
MVP offline Windows, solo-vs-AI, Python 3.12 + pygame-ce, 70 podstawowych kart po jednej, 17 archetypów aukcyjnych / 51 wariantów, pięć pól na stronę, rzadkość: podstawowa/rzadka/legendarna. Legendarne mają być celowo **OP**, aukcja ma być wydarzeniem; **żadnych nerfów**.

## Wprowadzone buffy
- **A014:** R co własny koniec tury regen 2 HP przez 2 tury losowej własnej jednostce, L całej własnej planszy, w tym sobie. Nakładanie dozwolone. Stare pasywne antyleczenie zostaje.
- **A003:** gdy brak innej podstawowej karty w cmentarzu, Szkielet bez zdolności minimum P6/6 R7/7 L8/8 albo wyższe statystyki jednej najlepszej karty w ręce. Limit planszy 5.
- **A004 / A016:** przy braku pola na kopię/zagranie P Tarcza, R Tarcza i połowa statystyk wybranej innej jednostki, L Tarcza i pełne statystyki. Plus MAX HP uzupełnia aktualne HP. A016 zachowuje legalny dobór.
- **A009:** przy wymianie premia dla WSZYSTKICH kart w NOWEJ własnej ręce +1/+1 P, +2/+2 R, +3/+3 L. Stała. Przy braku wymiany P/R również buff ręki.
- **A002:** P Tarcza, R Tarcza i 2 pancerza, L Tarcza i 4 pancerza. Brak odnowienia każdego końca tury; awans na planszy dopłaca tylko różnicę do nowej jakości.

## Reguły zapisów i podpisanych audytów
- `Match.balance_patch_v24=True` dla nowo tworzonych gier v22. Stare zapisy nie mają tego pola, więc brakujące pole traktowane jest jak `False`.
- Nowe podpisane audyty zawierają marker `balance_patch_v24` w `ruleset_state`; stare odtwarzane są bez tej flagi.
- Nie mieszać w żadnym wypadku niezatwierdzonych wariantów A/B/C z archiwalnego audytu z aktywnym patchem.

## Do QA
`tests/test_balance_buff_v24_0990.py`, cała regresja CI, archiwa replay, 100 meczów oraz odbiór Windows. Nie oznaczać „wydane” do potwierdzenia ich wyników.
