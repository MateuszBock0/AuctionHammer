# AuctionHammer — badanie przewagi pierwszego gracza (v22)

## Pytanie badawcze

W bazowym turnieju 100 prawdziwych meczów `normalny` vs `normalny` (seedy 220000–220099, oba boty z tą samą heurystyką) pierwszy gracz wygrał 77/100 razy. Drugi otrzymuje **+3 monety** na start. Czy zwiększenie lub zmniejszenie tego bonusu pomaga i w jakim stopniu obserwacja zależy od heurystyki AI?

## Metoda

Eksperyment **nie zmienia gry ani zatwierdzonego balansu**. Każde spotkanie tworzy zwykły `Match(seed,auctions_enabled=True,auction_catalog="v22")`. Przed pierwszą komendą AI nadpisuje wyłącznie monety gracza zaczynającego jako drugi; dla **+3 nie wykonuje żadnej modyfikacji**. Nie przypisujemy alternatywnym zasadom standardowego hashowanego audytu produkcyjnego.

Dla każdego z tych samych **200 seedów** (220000–220199) wykonywanych jest 15 scenariuszy:

- Bonus dla drugiego gracza: 0, 3, 5, 7 lub 10 monet.
- AI normalne, standardowa licytacja (5 scenariuszy).
- AI trudne, standardowa licytacja (5 scenariuszy).
- AI normalne, agresywna licytacja *auction_plus4* (5 scenariuszy). Wyłącznie limit własnej oferty jest większy o 4: `6+2*number` zamiast `2+2*number`; wybory i walka pozostają takie same. Oba boty mają tę samą strategię.

To **3000** realnych meczów z aktywnym v22, przy czym to samo ziarno dostarcza dopasowaną obserwację A/B. Po **każdej komendzie** sprawdzana jest integralność silnika.

Mierzymy: zwycięzcę i kolejność, 95% przedział Wilsona, długość meczów, zwycięzcę i wydatki licytacji, różnicę PŻ i liczby jednostek **tuż przed pierwszą aukcją**, a także zmiany zwycięzcy w dopasowanych seedach względem zasady +3. Pozwala to zobaczyć, czy bonus monetarny realnie wpływa na wczesną przewagę lub na aukcje, a czy występuje ona jeszcze przed pierwszym wydatkiem monet.

## Uruchomienie

```powershell
python tools/analyze_first_player_advantage.py --games-per-scenario 200 --start-seed 220000 --bonuses 0 3 5 7 10
```

Pliki w `reports/first_player_v22/`:

| Plik | Znaczenie |
|---|---|
| `wyniki_scenariuszy.json` | Pełna metodyka i statystyki 15 scenariuszy + testy dopasowane |
| `wyniki_scenariuszy.csv` | Porównanie 15 scenariuszy w arkuszu |
| `wyniki_meczow.csv` | Wynik każdego z 3000 meczów, w tym wpływ pierwszej aukcji |

GitHub Actions zapisuje je w artefakcie `AuctionHammer-V22-First-Player-Study`. Wszystkie seedy i tryby są podane w raporcie.

## Ograniczenia wnioskowania

- Ta symulacja bada zachowanie **konkretnych heurystyk AI**, nie udowadnia sprawiedliwości PvP.
- Ten sam seed zapewnia porównywalną kolejność i początkowy rozkład, ale przebieg późniejszej losowości może się rozjechać po innych decyzjach aukcyjnych i zmianach efektów.
- Przedział Wilsona opisuje statystyczną niepewność odsetka wygranych dla obserwowanych seedów w hipotezie wymienialności meczów, nie kontroluje wszystkich systematycznych błędów AI.
- Bezpośrednie statystyki różnicy PŻ na pierwszej aukcji pomagają odróżnić przewagę rozstawienia/walki od korzyści z wydawania monet.
- **Nie zmieniamy domyślnej zasady +3**, dopóki nie przeanalizujemy odrębnie wyników i tego, czy heurystyka licytacji wykorzystuje pieniądze.

## Zatwierdzone zasady pozostają bez zmian

Dwaj bohaterowie mają po 100 PŻ; zaczynający jako drugi otrzymuje +3 monety. Gra i bieżące zapisy pozostają identyczne; eksperyment nie korzysta z plików użytkownika.
