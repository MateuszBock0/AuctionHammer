# AuctionHammer 0.9.20 — katalog aukcyjny v3 i karczemne UI

## Źródła i ich hierarchia

- **Game Master v19** pozostaje nadrzędny w kolejności akcji, faz, fal
  śmierci, obronie, przydzielaniu monet i limitach planszy.
- **KATALOG_AUKCYJNY_12_v3.md** w tym folderze to zachowany bez zmian
  dokument roboczy dostarczony przez użytkownika; stanowi źródło
  12 testowych archetypów i 36 tekstów zdolności. Historyczna uwaga
  „NIE DODANO DO SILNIKA” w oryginale nie została fałszowana;
  implementacja z tego wydania znajduje się w kodzie.
- Stare reguły trzech Strażników 3/6/12 PŻ to **wyłącznie prototyp
  0.9.19 i kompatybilność ze starymi zapisami**. Nowy mecz nie losuje
  tych placeholderów.
- 70 bazowych kart i ich Game Master v19 są nietknięte.

## Mechanika od 0.9.20

- Co trzy pełne rundy, po naliczeniu +1 monety, z 12 archetypów
  **losowane są trzy różne oferty**. Dla każdej losowana jest
  niezależnie rzadkość 60/30/10%.
- Karta zdobyta w rundzie R ma bazową sumę **ATK + MAX PŻ = R + 8**.
  Przykłady bazowych ATK dla dwunastu archetypów pochodzą z v3;
  wzrost z rundą trafia w MAX PŻ. Ani ATK, ani MAX PŻ nie rosną
  od przebywania na ręce.
- Rzadkość egzemplarza ewoluuje po 3 i 6 ukończonych rundach
  od nabycia (podstawowa→rzadka→legendarna). Statystyki bazowe
  pozostają zamrożone; zmienia się wariant umiejętności. Zmianę
  dokumentuje JSON audytu.
- Wybrana karta trafia na rękę, może przekroczyć pięć kart na ręce,
  nie kosztuje monet przy zagrywaniu i respektuje limit pięciu
  jednostek na planszy. Licytacja, płatność zwycięzcy,
  drugi darmowy wybór i naprzemienna bezpłatna kolejność
  pozostały jak w Game Master v19.

## Dwanaście rodzin zdolności

| ID | Archetyp | Główna implementowana mechanika |
|---|---|---|
| A001 | Władca Dusz | Zgon, zabicie/przejęcie, przekazywanie łańcucha przejęcia |
| A002 | Generał Oddziału Natarcia | Aura obu stron +1, podwójny atak i x2 standardowych obrażeń |
| A003 | Matka Kości | Wybór cmentarza, powrót na rękę, wskrzeszenie 1 PŻ / pełne PŻ |
| A004 | Regent Krzywych Zwierciadeł | Efemeryczne kopie, cel własny/wrogi, statusy i Tarcza legendy |
| A005 | Bankier Widm | Oddzielna kradzież istniejących monet i tworzenie nowych |
| A006 | Królowa Zakazanych Słów | Wyciszenie jednej, dwóch lub wszystkich wrogich jednostek |
| A007 | Strażnik Ostatniego Tchnienia | Jednorazowy ratunek bohatera, wyższe PŻ i ogłuszenie |
| A008 | Architekt Pustki | Odkładane wygnanie, wygnanie jednostek i karty z ręki |
| A009 | Złodziej Wspomnień | Wymiana pojedynczej karty i obu rąk, odrzucenie na cmentarz |
| A010 | Królowa Tysiąca Twarzy | Żołnierze, efemeryczne kopie, trwałe kumulowane wzmocnienia |
| A011 | Jeździec Czarnej Komety | Obrażenia masowe i atomowe zniszczenie całej planszy |
| A012 | Tkaczka Drugiego Losu | Średnia PŻ, kopiowanie PŻ w wybranym kierunku, drenaż |

Wszystkie rozstrzygnięcia wykorzystują istniejące `Pending`,
`Choice`, `_drain`, `_kill_batch`, `_resolve_death_wave`
oraz kontrolowane mutacje stanu silnika. Nie implementowano
odrębnych kolejek walki dla kart aukcyjnych.

## Cztery interpretacje nadal robocze

Katalog źródłowy wymienia cztery obszary wymagające potwierdzenia:

1. **A002:** podstawowa aura działa dosłownie na **obie** plansze.
   Rzadka wybiera jednego istniejącego sojusznika przy pojawieniu
   się lub ewolucji Generała; jeśli zginie, wybór nie jest automatycznie
   powtarzany. Legendarna obejmuje nowo zagrywane własne jednostki.
2. **A012:** rzadka kopiuje PŻ **w jednym wybranym kierunku**,
   a nie równocześnie zamienia dwie wartości.
3. **A004:** efemeryczna kopia zostaje wystawiona dodatkowo
   i może uruchomić „Przy wystawieniu”. Nie wolno kopiować
   samego Regenta ani istniejącej kopii, aby nie wywołać
   niekończących się rekurencji.
4. **A010:** wzmocnienia na planszy są trwałe i kumulują się;
   nie należy ich utożsamiać ze skalowaniem na ręce.

Te interpretacje nie są prezentowane jako nowa definitywna decyzja
Game Master. Można je zmienić osobnym, zatwierdzonym balansem.

## UI — dlaczego teraz wyraźnie przypomina karczmę

Poprzednia wersja korzystała z małej drewnianej faktury o
przezroczystości zaledwie 38/255; drewno było praktycznie niewidoczne.

W nowej wersji używamy oryginalnych grafik Tavern UI Pack v2:
- ciemniejszej **fotograficznej sali karczmy**, widocznej za planszą,
  z kominkiem, drewnianym stołem i oświetleniem;
- rzeczywistych **rzeźbionych drewnianych paneli** i ornamentów;
- brązowo-mosiężnych guzików, tytułów, obramowań kart i slotów.

Karty, przyciski i cały tekst pozostają nad nieprzezroczystymi
lub silnie zaciemnionymi obszarami. Nie zmieniono współrzędnych
kliknięć, rozmiarów trzech wersji kart ani rozmiaru logicznego
ekranu 1480×980.

**Brak grafiki na dysku** nie powoduje błędu: dekoracje posiadają
proceduralny fallback. Do repo włączono małe, skompresowane wycinki,
nie pełny ZIP źródłowych arkuszy.

## Audyt, zapis i testy

- `AuctionHammer-OSTATNI-MECZ.json` zapisuje pełne akcje aukcji,
  losowania, zmiany rzadkości, stany jednostek, prawa własności,
  cmentarz, wygnanie i jednostki efemeryczne.
- `tools/verify_last_match.py` odtwarza zapisaną partię z
  `Match(seed,audit_enabled=True,auctions_enabled=True)`.
- Zapis meczu w trakcie wyboru oferty i wieloetapowych zdolności
  nie gubi `Pending`. Odtwarzanie starych logów wymaga oryginalnego
  buildu, jeśli definicje aukcji zmieniły się od 0.9.19.
- Starsze zapisane mecze z 0.9.19 i prototypowymi Strażnikami
  zachowują ich dotychczasowe parametry; do historii nie są
  dopisywane wstecz licytacje katalogu v3.
- Testy: katalog i wartości R+8; ewolucja; każda rodzina zdolności
  oraz wysokiego ryzyka interakcje rzadkie/legendarne; bazowe 70
  kart; pełny mecz AI wraz z audytem; render Pygame i rozmieszczenie
  tekstu Windows.

**Do późniejszego etapu:** finalna walidacja balansu statystyk 12
archetypów, usunięcie roboczych interpretacji A002/A012/A004/A010,
ewentualna rozbudowa katalogu do ~36 archetypów i pełna gra PvP online.
