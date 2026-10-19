# AuctionHammer 0.9.32 — stabilizacja aukcji v22

## Cel

Poprawić dwa potwierdzone błędy w działającym lokalnym demo 0.9.31,
bez zmiany balansu v21 (70 kart), 17 archetypów aukcyjnych, 51 opisów
wariantów, przeciwnika lub interfejsu.

## P1 — A009 a oddzielny woreczek

**Usterka w 0.9.31:** przy odrzuceniu karty przez legendarną A009
sprawdzenie `game.auction_catalog=='v4'` pomijało nowy tryb
`v22`. Jeżeli po zamianie rąk przeciwnik odrzucił kartę aukcyjną,
mogła ona trafić do zwykłego cmentarza, co naruszało ochronę
`assert_integrity` przed przeciekiem kart AUC do standardowego dobierania.

**Naprawa:** dla obu trybów `v4` i `v22` fizyczna, odrzucona
karta aukcyjna trafia do `auction_used`. Nigdy nie trafia do
`grave`, `deck` ani banku 70 kart.

**Ochrona regresji:** testy odtwarzają legendarną A009, zamianę
rąk z fizyczną kartą A014, wybór odrzucenia, drugi wybór i
`assert_integrity`; powtórzone z zapisem/wczytaniem przed
wymianą oraz w środku sekwencji odrzucenia.

## P1 — ewolucja rzadkości zakupionych kart v22

**Usterka w 0.9.31:** wywołanie `auction.advance_rarity`
w `Match._finalize_end_turn` obejmowało tylko tryby `v3` i `v4`.
Karty v22 pozostawały przy rzadkości zakupu, wbrew kontraktowi
ewolucji co trzy ukończone rundy od zakupu.

**Naprawa:** do wywołania dodano `v22`, a sam istniejący mechanizm
`auction.advance_rarity` wykorzystuje bieżący katalog dla danego
trybu i podmienia definicję efektu na kanoniczny wariant rzadkości.
Zakupione ATK / MAX PŻ pozostają niezmienne. Metadane
`last_evolve_round` zabezpieczają przed powtórnym awansem na
tej samej granicy rundy.

**Ochrona regresji:** scenariusze wykonywane przez
`Match.end_turn()` na granicach pełnych rund R=6/9/12:
`podstawowa → rzadka → legendarna → legendarna`.
Sprawdzane są jednocześnie: opis karty, metadane zakupu,
niezmienność ATK/MAX PŻ, wymagane trzy oferty następnej aukcji
oraz zgodność starszego trybu v4.

**Kompatybilność zapisu:** nie zmieniano schematu pliku zapisu;
`v3`, `v4` i `v22` wczytują się zgodnie ze swoim katalogiem.
Nie przeprowadzamy wstecznego odtwarzania awansów *już pominiętych*
przez starszy silnik 0.9.31; taka operacja musiałaby rozstrzygnąć
retroaktywne aktywacje (szczególnie A002) i mogłaby zmienić
historię meczu. Istniejący zapis pozostaje odtwarzalny, a nowe
pełne rundy korzystają z naprawionego wyzwalacza. Dla całkowicie
kanonicznego przebiegu od rundy pierwszej uruchom nowy mecz
w 0.9.32.

## Wzmocnione testy granic i spójności

`tests/test_auction_v22_stabilization_0932.py` obejmuje dodatkowo:

- A015 podstawowa: jednokrotne anulowanie, następny wyzwalacz już
  bez ochrony, zapis stanu jednorazowego użycia i usunięcie źródła
- A015 rzadka: blokowanie wyzwalaczy „Przy śmierci” oraz wyciszenie
  wyłączające pasyw
- A015 legendarna: blokada trzech rodzajów wyzwalaczy także po wczytaniu,
  bez blokowania standardowych ataków i pozostałych pasywów
- A016: zapis podczas wyboru karty oraz kontynuacja bez duplikacji
- A018: zapis kuponów, ich jednorazowe zużycie na aukcji, zapis podczas
  licytacji
- 17 archetypów → maksymalnie osiem pełnych aukcji → ostatni,
  niewykupiony archetyp wyłącznie w woreczku aukcyjnym
- jawne 17/51 w metadanych i dokładnie trzy teksty każdego archetypu

## Stan dokumentacji

`data/auction/KATALOG_AUKCYJNY_17_v22.json` ma aktywne pola
`count_archetypes=17`, `count_effect_variants=51`,
`status=LIVE_V22` oraz rozróżnia **wdrożenie w demonstratorze**
od **niezweryfikowanego statystycznie balansu**. Oryginalne
dokumentacyjne zastrzeżenia DRAFT i poprzedni stan akceptacji
są zachowane w `source_proposal_metadata`. Treść 51 wariantów,
ich wartości i prawdopodobieństwa pozostają bez zmian.

## Granice weryfikacji

GitHub Actions sprawdza testy unit/integration na Pythonie 3.12
(Linux i Windows), headless Pygame, utworzenie portable Windows
i zgodność artefaktu z komitem wydania. Te kontrole nie zastępują
ręcznej sesji Windows ani nie dowodzą poprawności każdej
kombinacji kilkunastu aktywnych efektów w wielogodzinnym meczu.

Nie dodano multiplayera, wyższych poziomów trudności ani nowych
kart. Balans podstawowy v21 i katalog aukcyjny v22 pozostają bez
korekt liczbowych.
