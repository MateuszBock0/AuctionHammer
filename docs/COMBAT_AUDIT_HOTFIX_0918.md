# AuctionHammer 0.9.18 — audyt techniczny i regresje walki

**Punkt odniesienia:** Game Master v19, 70 kart podstawowych, gra jednoosobowa vs AI.
Nie zmieniono definicji kart, balansu, AI, ekonomii, kolejności zdarzeń
ani logiki fal śmierci. Brak aukcji i kosztów zagrywania kart.

## 1. PŻ pokazywane graczowi

Po śmiertelnych obrażeniach silnik może przechowywać rzeczywiste ujemne
PŻ (np. -5). Jest to przydatne do audytu overkill.

Wersja 0.9.18 nie zmienia PŻ w silniku ani w pliku audytu. Jedynie
licznik na pasku bohatera i końcowe podsumowanie meczu wyświetlają
`max(0,min(100,hp))`. Dla -5 wynosi on **0/100**.

Test regresji sprawdza jednocześnie obie wartości, żeby żadna kosmetyczna
poprawka nie zmieniła danych mechaniki.

## 2. Regresje zdolności v19

`tests/test_combat_regressions_0918.py` zawiera zestaw izolowanych,
deterministycznych stanów silnika:

- **Oczyszczanie**: efekty tymczasowe vs permanentne, pozytywne vs
  negatywne, użyteczne i bezskuteczne oczyszczenie, wartości
  ulepszonej zdolności S07; brak dopisywania bonusu bez trafionego efektu.
- **Trucizna**: zadawanie obrażeń ignorujących tarczę i pancerz,
  zużywanie czasu trwania, usunięcie jednostki po zgonie, odporność
  wrodzona S39 oraz statusowa odporność na truciznę.
- **Ogłuszenie**: blokowanie wszystkich ataków, usuwanie przy końcu
  odpowiedniej tury oraz ignorowanie próby nałożenia przy odporności.
- **Podwójny atak**: S115 ma dwa, lecz nigdy trzy ataki; S79 odblokowuje
  drugi atak po pierwszym; S67 daje zdolność wybranemu sojusznikowi,
  nie całej planszy; ogłuszenie i choroba przywołania nie są obchodzone.
- **UI**: ujemne rzeczywiste PŻ w JSON i poprawne 0/100 w interfejsie.

Testy nie służą do poprawiania zasad „pod wynik”. Każde stwierdzenie
dotyczy dokładnie zadanego stanu początkowego.

## 3. Wiarygodna identyfikacja builda i poziomu AI w audycie

Od tego wydania w `payload.environment` są:

```json
{
  "ai_difficulty_initial": "normalny",
  "ai_difficulty_current": "trudny",
  "ai_difficulty_history": [
    {"after_action_seq": 7, "round": 2, "from": "normalny", "to": "trudny"}
  ],
  "build": {
    "commit": "<40-znakowy SHA bieżącego buildu>",
    "source": "embedded-ci",
    "version": "0.9.18"
  }
}
```

Każda komenda w `payload.actions` otrzymuje także `ai_difficulty`
obowiązujący w chwili polecenia. Po wczytaniu meczu gra przywraca poziom
AI zapisany wraz z rozgrywką.

**Pochodzenie SHA:** podczas GitHub Actions generowany jest
`data/BUILD_INFO.json` z pełnym identyfikatorem `github.sha`,
przed spakowaniem plików do EXE. Workflow dodatkowo sprawdza, czy
uruchomiony Python odczytuje dokładnie tę samą wartość. Nie zgadujemy
commita na podstawie najnowszej wersji w internecie.

Jeżeli oryginalnego commita nie można ustalić (np. starszy zapis),
pole `commit` ma wartość `null` oraz odpowiedni znacznik źródła.
Audyt starego meczu **nie zostaje fałszywie oznaczony najnowszą wersją**.

Ponowne odtworzenie komend na silniku v19 działa jak dotąd.
Same preferencje AI nie są częścią autorytatywnego stanu silnika;
nie zmieniają zapisanych hashy ani kolejności zdarzeń. Odtwarzanie
potwierdza wykonywane komendy, a nie wewnętrzny tok punktowania AI.

## 4. Kontrola i demonstracja

```powershell
python -m unittest discover -s tests -v
python tools/render_minimal_fantasy_preview.py
```

Nowy obraz: `preview/VISUAL_0918_KONIEC_0_PZ.png`.

Automatyczna kontrola obejmuje Pygame, źródłowe dane builda,
pełny roundtrip metadanych przez save/load, zmianę AI podczas gry
oraz działania czterech rodzin zdolności.

Po aktualizacji może zostać przesłany następny
`AuctionHammer-OSTATNI-MECZ.json` — nowa sekcja environment pozwoli
wskazać dokładny build przy diagnostyce. Stare pliki 0.9.17 nadal
są akceptowanymi audytami, o ile zachowano ich dotychczasowy schemat.
