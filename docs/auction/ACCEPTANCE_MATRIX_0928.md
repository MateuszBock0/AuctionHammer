# AuctionHammer 0.9.28 — macierz weryfikacji 36 wariantów i wyników walki

## Cel i granice

Wyłącznie stabilizacja lokalnej gry przeciwko dotychczasowemu AI. **Nie zmieniano AI, nie dodano multiplayera, nowych kart ani obcych ekonomii.**

Poprzedni zestaw 0.9.27 liczył 320 testów, ale zasadniczy test macierzy 36 wariantów sprawdzał przede wszystkim wykonanie zdolności bez błędu i zakończenie kolejki `pending`. W 0.9.28 każdy wariant otrzymał **osobny scenariusz oczekiwanego wyniku** jako `unittest.subTest` w `tests/test_auction_v4_semantics_0928.py`.

## Kontrakt umiejętności i przyjęte asercje

Poniższe oczekiwania pochodzą z tekstu wariantów w
`data/auction/KATALOG_AUKCYJNY_12_v4.json`. Większe scenariusze
sprawdzają także interakcje i ograniczenia.

| Karta | Podstawowa | Rzadka | Legendarna |
|---|---|---|---|
| A001 — Władca Dusz | Zgon celu i jego własne wyzwalacze | Przejęcie: właściciel, PŻ, statusy | Nadanie łańcucha, drugi rzeczywisty zgon |
| A002 — Generał Natarcia | ATK +1 obu stron i samego źródła | Wybrany sojusznik: 2 ataki, x2 standardowych obrażeń | Tylko nowo wystawieni; brak retroaktywności |
| A003 — Matka Kości | Przeniesienie własnej podstawowej z cmentarza na rękę | Wskrzeszenie 1 PŻ bez Przy wystawieniu | Wskrzeszenie pełnym PŻ + inna na rękę |
| A004 — Regent Zwierciadeł | Kopia wyłącznie sojusznika | Kopia także wroga, bez jego bonusów | Bieżące parametry i Tarcza, kopia efemeryczna |
| A005 — Bankier Widm | Min(3, monety wroga) +3 nowe | Max(3, połowa zaokr. w górę) +4 | Całe saldo wroga +5 |
| A006 — Królowa Zakazanych Słów | Wyciszenie jednego wroga | Wyciszenie dwóch różnych | Wyciszenie wszystkich aktualnych wrogów |
| A007 — Strażnik Ostatniego Tchnienia | Ratunek do 1 PŻ, bez zgonu jednostki | Ratunek do 20 PŻ | Ratunek do 25 PŻ i ogłuszenie wrogów |
| A008 — Architekt Pustki | Znamię i wygnanie po turze celu | Natychmiast: jedna jednostka + losowa karta ręki | Do trzech jednostek + jedna losowa karta |
| A009 — Złodziej Wspomnień | Wymiana z losową kartą ręki rywala | Wymiana z konkretną wybraną kartą | Wymiana całych rąk + dokładnie do 2 odrzutów |
| A010 — Królowa Tysiąca Twarzy | 1/1 lub trwałe +1/+1 | 2×2/2 z Prowokacją lub +4/+4 | Statystyki najlepszego sojusznika, bez zdolności |
| A011 — Jeździec Czarnej Komety | Równoczesne 5 obrażeń jednostkom wroga | 5 obrażeń także bohaterowi | Wspólna fala zabija wszystkie inne +10 bohaterowi |
| A012 — Tkaczka Drugiego Losu | Średnia PŻ w dół, własny bohater +10 | Wybór kierunku kopiowania PŻ i +10 leczenia | -20 przeciwnikowi i +20 sobie |

**Ważne rozróżnienie:** 36 scenariuszy wywołanych przez `subTest`
nie oznacza 36 oddzielnych metod `unittest` w liczniku `Ran N tests`.
Wszystkie trzy rzadkości są sprawdzane oddzielnie z asercjami
konkretnego wyniku, a niezależnie nadal działa poprzednia macierz
`test_auction_v4_matrix_and_replay.py` i wiele osobnych testów
poszczególnych zdolności.

## Interakcje i przypadki graniczne

- **A006 → A011**: wyciszenie przy śmierci blokuje wywołanie
  destrukcyjnego efektu Jeźdźca.
- **A001**: łańcuch przejęcia aktywuje się tylko po realnym zgonie,
  a przejęte jednostki zachowują PŻ i statusy.
- **A002**: premia Generała dotyczy wyłącznie aktualnego sojusznika.
  Śmierć, wygnanie, przejęcie lub zastąpienie beneficjenta usuwa
  przypisanie do tej fizycznej obecności na planszy. Gdy karta zostanie
  ponownie wystawiona, bonus nie powraca samoczynnie.
- **A003**: wskrzeszenie na pełnej planszy przekierowuje kartę na rękę,
  bez złamania limitu pięciu jednostek.
- **A004 + A002**: kopia legendarnego Regenta potrafi skopiować
  istniejący generator aury, nie zapisuje natomiast bonusów z czasowych
  pól bitwy dwukrotnie we własnych efektach.
- **A008**: wygnanie nie jest śmiercią i nie uruchamia pośmiertnych
  nagród/zdolności.
- **A009**: zamiana rąk nie powoduje nowych fizycznych egzemplarzy;
  odrzucanie karty aukcyjnej zachowuje osobny woreczek.
- **A010**: bonus do MAX PŻ zwiększa bieżące zdrowie dokładnie **raz**.
  W 0.9.27 uszkodzona Królowa mogła być uleczona dodatkowo, ponieważ
  `_add_effect('max_hp')` już dodawała HP, a kod karty dodawał je ponownie.

## Czytelne, liczbowe rozstrzygnięcia walki

W trybie v4 wpisy do rzeczywistego dziennika zdarzeń Match obejmują:

1. **Tarcza**: „Tarcza blokuje X obrażeń i zostaje zużyta”.
2. **Pancerz jednostki i bohatera**: ile z X rzeczywiście pochłonął.
3. **PŻ jednostki/bohatera**: dokładne zadane obrażenia oraz PŻ przed → po.
4. **Leczenie**: rzeczywista odzyskana liczba PŻ, po uwzględnieniu limitu.
5. **Status**: nazwa („Ogłuszenie”, „Wyciszenie”, „Trucizna”,
   „Prowokacja”, „Podwójny atak”) zamiast identyfikatora technicznego,
   możliwy znacznik czasu i źródło.
6. **Aura**: zmiana ATK i MAX PŻ (+/−), raportowana tylko po rzeczywistej
   zmianie stanu, nie przy każdym wywołaniu przeliczenia aury.
7. **Brak obrażeń**: zero ATK / 0 PŻ obrażeń jest objaśnione bez
   udawania, że przeciwnik stracił zdrowie.

W pasku historii widać trzy najnowsze wpisy; pełne zdarzenia
pozostają dostępne pod klawiszem **H**. Kolory dyskretnie rozróżniają
blokadę (niebieski), obrażenia (czerwony) i leczenie (zielony).
Wyjaśnienie jest **pochodną autorytatywnego silnika**, nie osobnym
symulatorem obrażeń w UI.

Stare mecze `auction_catalog='v3'` zachowują dawny format historii,
więc nowe komunikaty nie zmieniają historycznego sposobu weryfikowania
zapisów v3.

## Testowanie i bramki wydania

- `python -m unittest discover -s tests -v`, Python 3.12, pygame-ce.
- `tests/test_auction_v4_semantics_0928.py` — 12 metod × 3 rzadkości,
  kilkanaście testów kombinacji i nieoczywistych stanów.
- `tests/test_combat_explanations_0928.py` — testy rzeczywistego
  tłumaczenia Tarczy, pancerza, obrażeń, leczenia, statusów i aury,
  koloru feedbacku oraz niezmienności starego v3.
- Dotychczasowe testy zapisów, AI, audytu, 70 kart podstawowych,
  renderowania Pygame i aukcji v4 muszą nadal przechodzić.
- Po pozytywnym CI gałęzi i PR: scalanie do `main`;
  dopiero po ponownym CI na `main` publikacja Windows portable.

**Granica zapewnienia jakości:** jest to deterministyczna walidacja
opisanych scenariuszy i wykrytych kolizji, nie formalny dowód
poprawności *każdej możliwej* sekwencji kombinacji w dowolnie długim
meczu ani statystyczna kalibracja balansu.
