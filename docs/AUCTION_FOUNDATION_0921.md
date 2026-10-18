# AuctionHammer 0.9.21 — etap 2: fundament katalogu aukcyjnego v3

## Cel i źródła

Implementacja tego etapu korzysta z roboczego dokumentu
[`KATALOG_AUKCYJNY_12_v3.md`](KATALOG_AUKCYJNY_12_v3.md)
(12 archetypów × 3 warianty rzadkości), w powiązaniu z nadrzędnymi
zasadami kolejności Game Master v19.

**Ścisła granica:** nazwy, docelowe opisy 36 zdolności, statystyki,
rarities i ewolucja są dostępne w danych i UI, ale złożone zdolności
A001–A012 **nie są wykonywane przez silnik w 0.9.21**. Na kartach
wyświetlane jest **NIEAKTYWNA / PLANOWANA**, również po ewolucji.
Nie deklarujemy gotowej funkcji kopiowania, wyciszenia, przejęcia
czy wskrzeszania przed testami i wydaniem kolejnych etapów.

## Katalog — zasady dostępne w grze

1. Po pełnych rundach 3, 6, 9… losujemy **3 różne archetypy**
   spośród 12 A001–A012 (bez duplikatów w tej samej aukcji).
2. Dla każdej oferty niezależnie losujemy rzadkość:
   **60% podstawowa, 30% rzadka, 10% legendarna**.
3. Dla każdej oferty w rundzie R (R to *ukończona runda zakupu*)
   obliczamy **ATK + bazowe MAX PŻ = R + 8**.
   Bazowy ATK archetypu jest stały, a pozostała część przypada
   na PŻ. Rzadkość nie mnoży statystyk.
4. Zwycięzca licytacji opłaca pierwszy wybór, przeciwnik bierze
   drugi bez dodatkowego kosztu. Trzecia oferta pozostaje
   niewybrana i może zostać ponownie wylosowana na późniejszej aukcji.
5. Wybrana fizyczna karta trafia do ręki; można ją rozegrać jako
   jednostkę o zakupionych statystykach, ale nie uruchamia
   opisanej zdolności specjalnej w tym etapie.
   Zagranie nadal kosztuje zero monet; obowiązują limity tur i planszy.
6. W każdą trzecią **ukończoną rundę od zakupu** jednostka awansuje:
   podstawowa → rzadka → legendarna. Legendarna pozostaje
   legendarna. Ewolucja zachodzi także, jeśli karta jest na
   ręce, planszy lub cmentarzu.
   **ATK i MAX PŻ pozostają równe wartościom z chwili zakupu.**
7. Zgon daje przeciwnikowi obecnego właściciela 1 / 2 / 3
   monety zależnie od *aktualnej* rzadkości karty aukcyjnej,
   zgodnie z Game Master v19. Podstawowe karty dają nadal 1 monetę.

## Zgodność i śledzenie

- W grze istnieje nadal dokładnie 70 oryginalnych podstawowych
  egzemplarzy, niezależnie od nabytych kart `AUC...`.
- Wczytywanie meczów z **0.9.19 / 0.9.20** domyślnie zachowuje
  ich pierwotny tryb `auction_catalog=placeholders`:
  Strażnicy 3/6/12 PŻ, 3 ATK, Prowokacja + Tarcza.
  Nie zmieniamy im reguł w środku zapisanego meczu.
- **Nowe mecze** używają `auction_catalog=v3` i losują 12 archetypów.
- Tryb katalogu, oferty, wylosowane rzadkości, poziomy, moment
  nabycia, zmiany rzadkości i pieniądze znajdują się w JSON audytu.
  Mechanizm `verify_last_match.py` obsługuje teraz identyfikator
  trybu katalogu podczas odtwarzania.
- Numer aukcji (`level`) pozostaje osobny od rzadkości;
  zmiana rzadkości nie podnosi go i nie zmienia ATK/PŻ.

## Co pozostaje na etapy 0.9.22–0.9.25

- A005/A006/A012: ekonomia, wyciszenie i manipulacja PŻ bohaterów
- A002/A007/A011: aury, ratunek bohatera, masowe fale zgonów
- A001/A003/A008/A009: przejęcia, cmentarze, wygnanie, zmiana właściciela
- A004/A010: kopie efemeryczne, dodatkowe przywołania i buffy

Cztery sporne interpretacje katalogu v3 **pozostają otwarte**:
A002 (retargetowanie rzadkiego Generała), A012 (kierunek kopiowania HP),
A004 (wywołania przy wystawieniu kopii i zapętlenia),
A010 (trwałe narastanie bonusów). Nie są utrwalane
w działającym silniku przez ten etap.

## Testowanie i obrazy

`python -m unittest discover -s tests -v`

`python tools/render_minimal_fantasy_preview.py`

Nowe podglądy: `VISUAL_0921_KATALOG_12_OFERTY.png`,
`VISUAL_0921_NIEAKTYWNE_ZDOLNOSCI_KART.png`.

Testy obejmują: 12 unikalnych ID × 3 opisy, wartości statystyk
w rundach 3/6/9/12/21, progi 60/30/10, brak duplikatów ofert,
ewolucję rzadkości, niezmienność bazowych statystyk, nagrody 1/2/3
za zgon, brak niezatwierdzonych efektów na planszy,
kompletność puli 70 kart, zachowanie poprzednich zapisów, AI,
stan aukcji w JSON oraz pełne deterministyczne odtworzenie
**zarejestrowanych komend** obejmujących rzeczywistą aukcję.

Z uwagi na robocze, jeszcze nieaktywne zdolności nie przedstawiamy
etapu 0.9.21 jako ostatecznie zbalansowanego katalogu ani nie
uznajemy go za dowód ukończonej gry z aukcjami.
