# AuctionHammer 0.9.42 — Visual & Interaction Polish

## Scope i zasada wizualna

Podstawą jest 0.9.41 (PR #58). 0.9.42 skupia się **wyłącznie** na prezentacji i sterowaniu. Zachowuje obecny średniowieczno-karczemny charakter: stonowane drewno, ciepłe złoto, mosiądz, przygaszoną zieleń, existing `tavern_scene.jpg`, ikony i pełny katalog 70 kart podstawowych oraz 51 zdolności aukcyjnych.

Żaden plik w `game/core/`, `data/`, `assets/` ani pliki muzyki nie są zmieniane. Hover nigdy nie wywołuje `attack`, `play`, `end_turn` i nie generuje podpisanej komendy audytu.

## Wdrożone elementy

| Funkcja | Co pokazuje | Bezpiecznik |
|---|---|---|
| Podgląd karty na ręce | Po 420 ms bez ruchu kursora prezentuje autentyczny renderer 255×380 i wskazówkę otwarcia pełnego opisu [I] | Nie zmienia hitboxów, nie działa przy aktywnym wyborze zdolności, podczas drag, aukcji, modalnych menu, replayów i ekranu końca |
| Podpowiedzi efektów | Hover nad realnym znacznikiem efektu pokazuje nazwę, opis i źródło; `+N` przedstawia kolejne efekty | Statusy pochodzą wyłącznie z `active_statuses()` lub `hand_grants()` |
| Atak gotowy | Delikatna zielona ramka wokół własnej jednostki zdolnej zaatakować | `attack_display().ready` odzwierciedla wyłącznie `Match.legal_attacks()`; brak fikcyjnej prognozy obrażeń |
| Karta gotowa do zagrania | Stonowana złota ramka na dostępnej karcie ręki | `Match.can_play()` uwzględnia zajęte pola i legalność zastąpienia |
| Wybór drugiego gracza | Dwie karczemne tablice: Chorąży 2/5 z istniejącą ilustracją S34 i tekstem „Chorąży zawsze zdąży.” lub +3 monety | Dokładnie te same przyciski / skróty 1–2, żadna zmiana rekompensat |
| Koniec gry | Ukryto zbędny przycisk `NOWY MECZ [R]` w panelu bocznym pod ekranem końcowym | Główny CTA nadal działa, podpisy audytu i R/Q bez zmian |
| Szczegóły ATK/MAX PŻ | Gdy baza = aktualne statystyki, nie pokazuje fałszywego „wzrostu” | Aktualne PŻ i MAX PŻ pozostają osobnymi polami |
| Wersje | `VERSION.json`, tytuł okna i README ustawiono na 0.9.42; poprawiono dostępne historyczne tryby i audyt schema 4 | Bez ingerencji w reguły v23 i aukcje v22 |

## Granice i decyzje

- Nie dodano hover `HP - ATK` i nie określamy wyniku walki bez pełnego rozstrzygania silnika. Combat Preview pozostaje **BLOCKED** z powodu różnorodnych zdolności, tarcz, prowokacji i `Pending`.
- Nie przebudowano okna ani rozmiarów fizycznych trzech kart (125×195, 148×220 i 255×380).
- Nie pobierano obcych ilustracji, nie dodawano nowych ikon ani innych oryginalnych plików źródłowych.
- Nie zrealizowano jeszcze nowego samouczka, odtwarzacza archiwalnych meczów ani personalizowanego skalowania fontów: to osobne etapy produktu.

## Dowody automatyczne i screenshoty

- `python -m unittest discover -s tests -v` — pełna regresja, w tym `tests/test_ui_hover_polish_0942.py`.
- `python tools/render_ui_hover_0942.py` — cztery oryginalne renderingi Pygame w `preview/ui_0942/`:
  - `01_wybor_rekompensaty_tawerna.png`
  - `02_duzy_podglad_karty_po_najechaniu.png`
  - `03_wyjasnienie_statusu_i_zrodla.png`
  - `04_legalne_akcje_karty_i_tura.png`
- `.github/workflows/ui-polish-0942.yml` — publikuje pliki jako `AuctionHammer0942-UI-review` i wymaga ich niepustości.
- Testy `state_snapshot` porównują digest przed i po podglądzie, a test statusów porównuje hitbox z rzeczywiście rysowaną geometrią.

## Odbiór manualny — nadal NOT TESTED

Wymagany rzeczywisty Windows 10/11 (nie tylko `SDL_VIDEODRIVER=dummy`) przy 1366×768, 1536×864 i 1920×1080 oraz DPI 100/125/150%. Należy obejrzeć siedem istniejących PNG, czytelność podglądu nad ręką, długie polskie nazwy, tooltipy `+N`, F11, drag-and-drop, mulligan, modalny wybór, historię H, replay P oraz Zakończenie gry. Drobne korekty pozycji można wprowadzić w osobnym PR po realnej ocenie.

## Relacja do pozostałych prac

Gałąź `feature/0942-ui-visual-interaction-polish` jest **zależna od** `feature/0941-second-player-choice-uiux` (PR #58). Do czasu zmergowania PR #58 nie scalać samej warstwy UI na starą wersję `main` 0.9.39, bo brakowałoby istniejącego wyboru rekompensaty.
