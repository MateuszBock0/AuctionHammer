# Wyniki badania przewagi pierwszego gracza — AuctionHammer v22

**Data:** 19.10.2026 · **Status:** pomiar zakończony · **Zmiany balansu produkcyjnego:** brak.

**Źródła pierwotne:** [3000 meczów i pliki CSV/JSON](https://github.com/MateuszBock0/AuctionHammer/actions/runs/39247235433/artifacts/12184687478), [100 audytowanych meczów v22](https://github.com/MateuszBock0/AuctionHammer/actions/runs/39245756098/artifacts/12183835795). Metodyka: [QA_FIRST_PLAYER_V22.md](QA_FIRST_PLAYER_V22.md).

## 1. Stabilność eksperymentu

- **3000/3000 meczów ukończonych**, 0 błędów silnika, kontrola integralności po każdej komendzie AI.
- **414/414 testów automatycznych PASS**.
- 200 tych samych seedów 220000–220199 dla każdego z 15 scenariuszy; rozgrywka przeciw temu samemu poziomowi AI po obu stronach, aktywne aukcje v22.
- Wszystkie warianty bonusa inne niż +3 są testami *what-if*, bez zmiany kodu produkcyjnego. Wersja +3 reprodukuje 77 zwycięstw pierwszego gracza dla pierwszych 100 seedów znanych z poprzedniego audytowanego turnieju.
- Nowe 3000 meczów **nie otrzymało osobnych plików audytu do pełnego replay**; weryfikowane było zachowanie integralności silnika po każdej akcji. Osobny poprzedni turniej 100 partii zachowuje pełne hashowane audyty i 11 sprawdzonych replayów.

## 2. Wskaźnik: zwycięstwa gracza rozpoczynającego

**W tabeli każda komórka to odsetek zwycięstw pierwszego gracza; 200 meczów na wariant.** Idealny wynik symetrycznych botów i zbalansowanej kolejności byłby bliski 50%.

| Bonus drugiego gracza | Normalny, standardowe oferty | Trudny, standardowe oferty | Normalny, oferty +4 limitu |
| ---: | ---: | ---: | ---: |
| +0 | 73,5% (147/200) | 71,5% (143/200) | 69,0% (138/200) |
| **+3 (obecna reguła)** | **75,5% (151/200)** | **76,0% (152/200)** | **67,5% (135/200)** |
| +5 | 78,0% (156/200) | 77,0% (154/200) | 70,5% (141/200) |
| +7 | 79,0% (158/200) | 75,5% (151/200) | 73,0% (146/200) |
| +10 | 79,0% (158/200) | 79,0% (158/200) | 73,5% (147/200) |

Obecny wariant normalny/+3: 151/200, 95% Wilson CI **69,1–80,9%**; pierwsze miejsce przypadało indeksowi P0 w 102 przypadkach, P1 w 98 (symetryczny rozkład miejsc). **Nie ma dowodu, że zwiększenie samej rekompensaty monetarnej wyrównuje przebieg.** W tej próbie wskaźnik przy +5/+7/+10 jest często wyższy niż przy +3, ale zmiany względem +3 nie są samodzielnie istotne statystycznie przy 200 dopasowanych seedach.

Porównanie tych samych seedów dla normalnego AI: dla +10 zamiast +3 **3 mecze zmieniły wynik na korzyść drugiego gracza, a 10 na korzyść pierwszego** (dwustronny dokładny test McNemara p≈0,092; interpretacja eksploracyjna). W wariancie normalnym z limitem ofert wyższym o 4 przy +3 pierwsze miejsce wygrało 135 zamiast 151 gier: zmiany 29 na korzyść drugiego wobec 13 w przeciwną stronę (p≈0,0195 przed korektą na wiele porównań). Nadal 67,5% nie oznacza równowagi.

## 3. Obserwacje rozstrzygające

### Przewaga nie zaczyna się od większego PŻ przy pierwszej aukcji

Dla normalnego AI i +3, średnia różnica `PŻ pierwszego − PŻ drugiego` wynosi:

| Moment pomiaru | Średnia różnica PŻ |
| --- | ---: |
| Tuż przed aukcją po rundzie 3 | **−0,48 PŻ** |
| Tuż przed aukcją po rundzie 6 | **+7,37 PŻ** |
| Tuż przed aukcją po rundzie 9 | **+20,775 PŻ** |

Na koniec trzeciej rundy średnia różnica liczby jednostek na planszy wynosiła zaledwie **+0,01** na korzyść pierwszego. Zasadnicza różnica PŻ **narasta później**, w okresie między pierwszymi aukcjami. To wskazuje, że warto izolować efekty kolejności tur, wystawienia i wykorzystania kart aukcyjnych — nie wyjaśnia jeszcze *mechanizmu przyczynowego*.

### Pierwszy gracz niemal nie wygrywa licytacji

Przy normalnym AI i +3 pierwszy gracz wygrał jedynie **17,3% wszystkich aukcji** (200 gier), a mimo to wygrał 75,5% meczów.

Kontrola na **100 kompletnych audytach** (te same seedy 220000–220099) potwierdza:

- **0/100 pierwszych aukcji** wygrał gracz rozpoczynający mecz; mimo to wygrał **77/100 meczów**.
- 525 zakończonych aukcji dało **525 zakupionych kart każdej stronie**. Zwycięzca licytacji dostaje pierwszeństwo wyboru, ale **obie strony otrzymują po jednej karcie**, zatem wygranie aukcji nie daje przewagi liczebnej kart.
- Pierwszy wygrał 92/525 wszystkich aukcji i wydał łącznie **901 monet**, drugi wydał **3339 monet**.
- Spośród otrzymanych kart aukcyjnych w tych 100 meczach zagrano przynajmniej raz: **417/525 kart gracza pierwszego** oraz **385/525 kart gracza drugiego**. To opis działania heurystyki AI i czasu dostępnego na zagranie, nie dowód jakości poszczególnych kart.

### Bonus pieniędzy ogranicza strategia botów

W standardowej heurystyce `ComputerOpponent` limit oferty wynosi `2 + 2 × numer_aukcji`: w pierwszej aukcji maksymalnie **4 monety**, bez względu na faktyczny kapitał. Obaj gracze otrzymują nowe monety co pełną rundę. Zwiększanie początkowych środków ponad to, co jest potrzebne do limitu, często nie wpływa na bieżące oferty.

W kontrolnym wariancie `auction_plus4` obaj gracze otrzymują limit większy o cztery monety, ale mechanika aukcji i decyzje o walce są identyczne. Dla +3 odsetek wygranych pierwszego zmalał z 75,5% do 67,5%, jednak nie osiągnął równowagi. **Decyzje AI o licytacji istotnie wpływają na wynik modelowej rozgrywki.**

## 4. Wnioski i kolejne testy

**Nie zmieniać teraz produkcyjnego bonusu +3.** Eksperyment nie uzasadnia podnoszenia go do +5, +7 ani +10. Co więcej, poprawianie odsetków zwycięstw przez mechaniczne dodawanie monet mogłoby ukrywać problem kolejności i wyceny ofert przez AI.

Rekomendowane dalsze eksperymenty, bez naruszania zatwierdzonych statystyk kart:

1. **Pierwsza tura po aukcji:** izolowany wariant kontroli inicjatywy po zakończeniu aukcji, z zachowaniem wszystkich pozostałych zasad (wyłącznie symulator badawczy).
2. **Wartość pierwszego wyboru w aukcji:** porównać rzeczywisty wkład statystyk i zdolności kupionych kart z zapłaconą ceną oraz wyborem za 0 monet.
3. **Heurystyka zagrywania kart:** zbadać przyczyny różnicy 417 vs 385 zagranych kart aukcyjnych i sprawdzić, czy AI adekwatnie wycenia rzadkość i zdolności zamiast samej wartości ATK/PŻ.
4. **Więcej seedów i gracze ludzcy:** potwierdzić hipotezy na większej próbie oraz podczas praktycznego playtestingu.

**Zakres zaufania:** wynik dotyczy AI vs AI, nie jest automatycznym dowodem balansu PvP. Brak błędów silnika w symulacji nie oznacza kompletnego testu każdej możliwej interakcji wszystkich kart.
