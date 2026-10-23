# AuctionHammer — obowiązujące zasady MVP 0.9.64 (23.10.2026)

**Status:** bieżący przewodnik dla lokalnej gry `SoloApp` (jeden gracz kontra komputer), uzupełniający bazową specyfikację silnika Game Master v19, aneks zasad v23 oraz **aktywny katalog aukcyjny v22**. Starsze dokumenty v14/v17/v19 i sekcje changelogu pozostają świadectwem historycznych decyzji. W razie rozbieżności co do zachowania wydania 0.9.64 rozstrzygające są testy i kod pod `game/core/`, `game/ui/` i `VERSION.json`.

## 1. Najważniejsza nowa reguła: kto zaczyna mecze

**W jednej sesji uruchomionej aplikacji:**

| Numer NOWEGO meczu | Pierwszy ruch | Drugi ruch i rekompensata |
| --- | --- | --- |
| 1 | **KOMPUTER** (indeks 1) | **GRACZ** (indeks 0) |
| 2 | **GRACZ** (indeks 0) | **KOMPUTER** (indeks 1) |
| 3 | **KOMPUTER** | **GRACZ** |
| 4 | **GRACZ** | **KOMPUTER** |
| N | nieparzysty: komputer, parzysty: gracz | drugi gracz z odpowiedniego wiersza |

- Po ponownym **uruchomieniu programu** licznik sesji zaczyna się od meczu nr 1: pierwsze otwarcie zawsze ma gracza na drugim miejscu. Nie przechowujemy licznika między uruchomieniami programu.
- **NOWY MECZ** z ekranu otwierającego aplikację korzysta z przygotowanego pierwszego meczu (nie przeskakuje automatycznie do nr 2). **KONTYNUUJ** oraz uruchomienie pierwszego samouczka analogicznie nie zużywają dodatkowego meczu.
- Każdy kolejny rzeczywiście stworzony **NOWY MECZ** (także `R`, po zakończeniu, po potwierdzeniu przerwania lub nowy samouczek w trakcie sesji) przełącza strony. Anulowanie potwierdzenia nie zmienia kolejności.
- **WCZYTAJ ZAPIS** przywraca bez zmian oryginalnego pierwszego gracza w pliku; nie przepisuje rozpoczętej partii. Następny nowy mecz otrzymuje odwrotną kolejność niż w załadowanej partii.
- Ważne rozróżnienie architektoniczne: niezależny silnik `Match`, symulacje oraz `verify_replay` **nadal losują pierwszego gracza z deterministycznego ziarna**. Klient wybiera świeże losowe ziarno tak długo, aż silnik wskaże wymagany indeks. Dzięki temu zapisany seed i cała kolejność RNG pozwalają bitowo odtworzyć mecz, bez dodatkowego wyjątku w schemacie audytu.
- To reguła UX **przypisania pierwszeństwa w aplikacji solo**, nie globalna zmiana zasad Game Master v19 dla potencjalnego multiplayera i nie zmiana przewagi w symulacjach balansu.

## 2. Startowa rekompensata drugiego gracza (0.9.63)

W trybie obecnego klienta drugi w kolejności wykonuje **jeden wybór przed własnym mulliganem**: **+3 monety** albo **Chorąży „Zawsze zdąży”** (`SUM_START_GUARD`) startujący z **2 ATK, 1 maks. i bieżącym PŻ oraz 4 trwałego pancerza**. Jednostka zajmuje jedno z pięciu stałych pól, nie atakuje w swojej pierwszej turze i po odejściu nie wraca do talii. W pierwszym meczu wybiera **człowiek**, w drugim **AI**, potem na zmianę.

Za każde z **pierwszych trzech** bezpośrednich zabójstw wrogiej jednostki **własnym zwykłym atakiem**, gdy Chorąży przeżyje starcie, otrzymuje **+1 ATK / +2 maks. PŻ / +2 bieżące PŻ**. Nie liczy się kontratak, trucizna, inne efekty, zabicie bohatera ani obustronna śmierć. Pancerz pochłania obrażenia po zasadach silnika i **nie odnawia się** po zabójstwie.

| Zabójstwa | ATK | Maks. PŻ | Ilustracja Chorążego |
|---:|---:|---:|---|
| 0 | 2 | 1 | `chorazy.png` |
| 1 | 3 | 3 | `chorazy_rzadka.png` |
| 2 | 4 | 5 | `chorazy_legendarna.png` |
| 3 (limit) | 5 | 7 | `chorazy_legendarna.png` |

Powyższe liczby nie obejmują innych aur/statusów. **S34 — Chorąży Królewskiej Kompanii** to **odrębna** karta podstawowa, z oryginalną i niezmienną grafiką `chorazy_krolewskiej_kompanii.png`, bez premii za zabójstwa.

**Zgodność:** zapisy i audyty z 0.9.62 i starszych wersji zachowują odpowiednie dawne zasady (m.in. 2/5 bez nowego pancerza, starsze 3/5). Nowy wariant jest oznaczony podpisanym `starter_guard_armor_rule`; premia za zabójstwa ma oddzielny `starter_guard_kill_rule` oraz `starter_guard_kills`.

## 3. Plansza, walka, karty i ekonomia

- **100 PŻ bohatera** po obu stronach, **pięć stałych pól** na planszę, **70 różnych kart podstawowych**, jedna zwykła karta z ręki na własną turę, brak kosztu monet za zwykłe karty; startowe ręce po 5 kart.
- Mulligan: maksymalnie **3 karty do wymiany** (włącznie z 0). Dochód za **własne wolne pola** jest naliczany po ostatecznym rozstrzygnięciu końca tury w aktualnej wersji v23; na koniec pełnej rundy obaj dostają po **1 monecie**.
- Walka: aktywne statusy (m.in. ogłuszenie, prowokacja, szybki/podwójny atak), tarcze i pancerz są rozstrzygane przez silnik. **Ogłuszenie blokuje atak**, nawet z Szybkim Atakiem; UI pokazuje komunikat `OGŁUSZONY`.
- Zdolność **Królowej Tysiąca Twarzy (A010)**: podczas jej oczekującego wyboru kliknięcie samej Królowej wybiera `grow` (wzmocnij), kliknięcie pustego własnego pola — `summon` (przywołaj), tylko przy legalnej opcji. Przyciski w prawym panelu nadal działają.
- **17 aktywnych archetypów aukcyjnych, 51 wariantów**, aukcje co trzy pełne rundy jeśli istnieją oferty; licytuje się prawo pierwszego wyboru karty. Rzadkości podstawowa/rzadka/legendarna mają odrębne ilustracje.
- Statusy i **Księga Starć** ujawniają aktywne premie (np. mnożnik standardowych obrażeń ×2 od Generała A002) i ich źródła; księga nie przelicza stanu walki, tylko prezentuje zapisane zmiany. Starsze audyty nie są modyfikowane podczas podglądu.

## 4. Artefakty i aktualne źródła

| Lokalizacja | Rola |
| --- | --- |
| `game/core/engine.py` | zasady mechaniki, podpisywany stan meczu, rozliczanie zabójstw |
| `game/ui/app.py` | sekwencja pierwszego gracza w sesji, menu, tutorial, renderowanie, interakcje |
| `game/core/audit.py` i `game/core/persistence.py` | replaye, integralność archiwów, zapis i wczytywanie |
| `data/cards_base_70.json` | definicje 70 podstawowych kart |
| `data/auction/KATALOG_AUKCYJNY_17_v22.json` | katalog aukcyjny |
| `assets/branding/manifest.json` | sumy SHA-256 ilustracji Chorążego i ikon |
| `tests/test_first_match_order_0964.py` | nowa kolejność: pierwszy mecz, restart, menu, samouczek, wczytanie, seed |
| `tests/test_chorazy_armor_0963.py`, `tests/test_chorazy_kills_0962.py` | 2/1 +4 pancerza, zabójstwa, stare i nowe replaye |
| `VERSION.json` i `README.md` | bieżące wydanie i podstawowe zasady |
| `AUCTIONHAMMER_MASTER.md`, `docs/GAME_MASTER_v23_ADDENDUM.md` | specyfikacja historyczna z dołączanymi aneksami |

Zachowane wersje Game Master v14/v19 oraz ich JSON-y stanowią **materiał historyczny**; **nie należy nadpisywać ich deklaracji `first_player=random`** z uwagi na archiwalne zasady i powtarzalność. Aktualne reguły interfejsu solo są nadrzędnie opisane w niniejszym aneksie.

## 5. Kryteria odbioru 0.9.64

1. Pierwsze uruchomienie solo: `first=1` (AI), drugi nowy mecz `first=0` (gracz), dalej naprzemiennie.
2. Otwarcie menu i kliknięcie NOWY MECZ/SAMOUCZEK/KONTYNUUJ nie pomija meczu nr 1.
3. Po potwierdzeniu restartu kolejność zmienia się dokładnie raz; samo pytanie o potwierdzenie nie zmienia stanu meczu.
4. Wczytanie starszego meczu zachowuje jego `first` i zapisane prawa rekompensaty; następny nowy mecz odwraca role.
5. Ziarno nowego meczu odtwarza oryginalne `Match.first` bez specjalnego parametru, więc audyt podpisany przez silnik nie wymaga migracji.
6. Windows ZIP, render Pygame, testy GUI, testy mechaniki, replaye i walidacja sumy SHA-256 są wymagane przed ogłoszeniem gotowej paczki. Ręczny odbiór na fizycznym Windows przy DPI 100%, 125%, 150% pozostaje odrębny.

**Nota o wersjonowaniu:** plik dokumentuje zamierzony stan po wdrożeniu 0.9.64. Informacja, że kod jest na `main` lub paczka opublikowana, musi zostać osobno potwierdzona przez GitHub.
