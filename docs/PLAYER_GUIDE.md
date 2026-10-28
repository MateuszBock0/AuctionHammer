# Jak grać w AuctionHammer?

**AuctionHammer** to jednoosobowa, turowa gra karciana fantasy przeciwko komputerowi. Na każdej planszy jest pięć pól na jednostki. Celem jest sprowadzenie PŻ bohatera przeciwnika do **0**, zanim Twój bohater zostanie pokonany.

> Chcesz najpierw zobaczyć grę? [Pobierz wersję Windows](https://github.com/MateuszBock0/AuctionHammer/releases/latest) i uruchom **SAMOUCZEK** z głównego menu.

## Pierwsza partia

1. **Kto zaczyna?** W pierwszej nowej partii po uruchomieniu aplikacji zaczyna komputer; w drugiej Ty. Kolejne mecze zmieniają tę kolejność naprzemiennie.
2. **Rekompensata drugiego gracza.** Drugi uczestnik wybiera bonus: **+3 monety** lub specjalnego Chorążego (2 ATK, 1 PŻ, 4 trwałego pancerza).
3. **Wymiana początkowa.** Możesz wymienić do trzech kart z ręki, w tym zero kart.
4. **Twoja tura.** Zasadniczo możesz wystawić jedną kartę. Po wskazaniu karty zobaczysz dozwolone własne pola lub legalną zamianę na pełnej planszy.
5. **Ataki.** Kliknij swoją jednostkę, a następnie dozwolony cel, albo przytrzymaj i przeciągnij jednostkę na cel, po czym puść przycisk myszy. Podświetlone ramki i ostre narożniki wskazują legalne cele bez zasłaniania ilustracji. Podczas wyboru celu duży automatyczny podgląd innej karty nie blokuje planszy. Podczas przeciągania widoczna jest bardzo delikatna, półprzezroczysta czerwona strzałka — nie zasłania już kart tak jak dawna gruba linia. Prowokacja, ogłuszenie, osłony i inne efekty mogą ograniczać ataki.
6. **Koniec tury.** Kliknij **ZAKOŃCZ TURĘ** lub naciśnij **SPACJĘ**. Jeśli pozostały legalne zagrania lub ataki, musisz potwierdzić chęć ich pominięcia.

## Karty i pięć frakcji

W talii podstawowej jest **70 niepowtarzalnych kart**. Ich frakcje sugerują moment działania zdolności:

| Frakcja | Najczęstszy moment aktywacji |
|---|---|
| Elfy | Wystawienie jednostki |
| Dzikie bestie | Atak jednostki |
| Potwory | Śmierć jednostki |
| Krasnoludy | Koniec tury |
| Ludzie | Pasywny efekt na planszy |

Karty podstawowe mogą zyskiwać statystyki podczas tur spędzonych **na ręce** i rozwijać zdolność co trzy takie tury. Pasek rozwoju pokazuje postęp, a krótka animacja — rzeczywiste osiągnięcie nowego poziomu.

Przy kartach z aurami (np. Chorąży `S34`, Komendant `S35` i Zbrojmistrz `S105`) wskazanie ich lub wspieranej jednostki pokazuje faktyczne powiązania i aktualne modyfikatory. Premie z kilku źródeł mogą się sumować; widoczna etykieta przy połączeniu jest wkładem **jednego źródła**.

## Jak działa plansza?

Obie strony mają po **pięć fizycznych miejsc**. Po śmierci jednostki inne karty nie przesuwają się automatycznie. Położenie ma znaczenie dla części efektów, zwłaszcza aur sąsiednich i reakcji na przeciwnika stojącego naprzeciwko.

ATK to siła ataku, PŻ to bieżące zdrowie, a MAX PŻ określa maksymalne zdrowie. Tarcza, pancerz oraz statusy działają według zasad konkretnej karty. Zielone i czerwone zmiany statystyk oraz liczby obrażeń odzwierciedlają aktualny stan, nie obiecują przyszłego rezultatu.

## Po co są monety?

**Zwykłe karty nie kosztują monet.** Monety przydają się przede wszystkim podczas aukcji. Co trzy ukończone rundy może odbyć się aukcja trzech ofert, o ile pula aukcyjna na to pozwala. Licytujesz pierwszeństwo wyboru, a nie komplet trzech kart. Dostępne jest **17 archetypów** aukcyjnych, w trzech rzadkościach (podstawowa, rzadka, legendarna) — łącznie **51 wariantów zdolności**.

Rzadkość kupionej karty może awansować w miarę upływu kolejnych pełnych rund. O wyborach i potencjalnych skutkach czytaj bezpośrednio na ekranie aukcji; dłuższe opisy znajdziesz przez **PEŁNA ZDOLNOŚĆ**.

## Czytelne aktywacje zdolności (0.9.92)

Gdy zadziała potwierdzony efekt, gra krótko podświetla jego źródło i rzeczywistych odbiorców. W wolnym pasku między własnym bohaterem a ręką pokazuje **ŹRÓDŁO → CEL → SKUTEK** (np. `Kapłan → 5 celów · REGEN 2/2`). Regeneracja, wzrost ATK, wzmocnienia MAX PŻ, statusy i potwierdzone zmiany zdrowia nie są prognozą — pochodzą z zatwierdzonych działań. Gdy gra nie potrafi jednoznacznie przypisać skutku do konkretnej zdolności, nie rysuje mylącego powiązania. Przy wzmocnieniu wszystkich sojuszników pokazuje jedną zbiorczą etykietę. Naciskając **A**, wyłączasz te animacje razem z innymi efektami wizualnymi; nie zmienia to wyniku partii.

## Głośność muzyki i efektów

W menu **USTAWIENIA** są dwa niezależne przyciski: **MUZYKA** (domyślnie **40%**) oraz **EFEKTY** (domyślnie **10%**). Każde kliknięcie podnosi poziom o 10 punktów procentowych; po 100% następuje 0%, czyli wyciszenie. Wartości są zapamiętywane lokalnie, także po zamknięciu gry. Dźwięki nie wpływają na wynik meczu.

## Karczemna Burda — wizualizacje i zakupy komputera (od 0.9.96)

Po zamówieniu piwa, jeśli animacje są włączone, przez 600 ms nalewa się piwo. Od 0.9.99 świeczki stoją na ramie planszy, ale nie ma już wiszącego kufla po lewej. Opłacony kufel pojawia się na prawo od dolnego rzędu kart, przechyla się i wylewa piwo na dolne obrzeże planszy. Po około 1,45 sekundy znika. Ogień dociera do wszystkich 10 pól jednostek (pustych i zajętych) jako migoczące płomyki. Od 0.9.101 ich kontury, jasne rdzenie i iskry są wyraźniejsze, ale nie zasłaniają kart. Płomyki każdej ramki poruszają się w innej fazie i słabną wraz z licznikiem: przy 3+ turach silny ogień, przy 2 średni, przy 1 żar. Gasną dokładnie przy zero turach. Kolejny zakup przedłuża Burdę o 3 tury. **[A]** wyłącza animacje. Karty i pola kliknięcia nie obracają się ani nie przesuwają, więc nadal można grać w swoim tempie.

Od 0.9.101 **każdy poziom AI w nowych grach ze skalowaną Burdą** może kupić kufel: porównuje dodatkowe obrażenia jednostek na obu planszach po dodaniu 3 tur, liczy Tarcze i pancerz, uwzględnia cenę oraz rezerwę na aukcję. Łatwe AI potrzebuje większej przewagi niż normalne, a trudne wykorzystuje nawet mniejsze okazje. AI nie patrzy w rękę ani talię przeciwnika, nie kupuje piwa w nieskończoność i oszczędza na licytacje. Stare wczytane partie z 1 DMG na turę zachowują wcześniejszą politykę AI (tylko trudne kupuje automatycznie). Od 0.9.97 normalne AI jest też bardziej zdecydowane podczas licytowania kart aukcyjnych.

## Podgląd decyzji w walce i przy wymianie (od 0.9.104)

Po zaznaczeniu jednostki zdolnej do ataku najedź na **legalny, podświetlony cel** (możesz także przeciągać atakującego). Panel po prawej pokaże **szacunek zwykłego ataku i odwetu**, z obecną Tarczą, pancerzem i pozostałymi PŻ. Nie jest to gwarancja wyniku: zdolności, ataki wyzwalane i skutki po śmierci mogą zmienić rozstrzygnięcie.

Gdy wszystkie pięć Twoich pól jest zajętych, wybierz kartę z ręki i wskaż legalną jednostkę do zastąpienia. Zobaczysz **porównanie bieżących ATK/PŻ starej jednostki i startowych ATK/PŻ nowej karty**. Gra ostrzeże przed utratą aury i przypomni, że zastąpienie nie wyzwala efektu śmierci. Wystawienie nowej karty może aktywować aury i zdolności, więc porównanie nie jest ostatecznym wynikiem zagranej karty.

Gdy Burda jest aktywna, **mały czerwony wykrzyknik poza ramką pola** oznacza jednostkę na której obecnym zdrowiu następne obrażenia Burdy *mogą* okazać się śmiertelne. Uwaga: efekty na koniec tury mogą wcześniej zmienić PŻ lub obronę. Ostrzeżenia działają na obu planszach i pozostają widoczne przy wyłączonych animacjach.

## Karczemna Burda — podpowiedź po najechaniu (od 0.9.103)

**Najedź kursorem na napis `BURDA: N TUR` po lewej stronie planszy.** Zostanie podświetlony złotą ramką, a w panelu karty po prawej pojawi się informacja o aktualnej zasadzie dla **tej konkretnej partii**. W nowej grze opis uwzględnia minimalne 10% MAX PŻ każdej jednostki (zaokrąglone w górę), oprócz licznika Burdy. Wyjaśnia, jak chronią Tarcza i pancerz, dlaczego bohaterowie i karty na ręce są bezpieczne oraz co zmieni kolejny kufel. Etykieta działa również przy `0 TUR`. Po wczytaniu historycznej partii podpowiedź zachowuje właściwą dla niej regułę: malejące 3→2→1 lub starsze stałe 1 DMG/turę. Dymek nie zasłania kart i znika po odsunięciu kursora.

## Karczemna Burda — zamawianie piwa i obrażenia

W swojej aktywnej turze możesz kliknąć **KUP [B]** lub nacisnąć **B**, jeżeli masz wystarczająco monet. Każdy kufel przedłuża Burdę o **3 końce tur**; nie zadaje natychmiastowego ciosu. Na koniec tury, po rozstrzygnięciu zwykłych efektów końca tury, ogień trafia jednostki **obu graczy** stojące na planszy, a następnie licznik Burdy maleje o 1. Bohaterowie i karty na ręce nie otrzymują obrażeń od Burdy.

### Aktualne zasady obrażeń (nowe partie od 0.9.105, również 1.0.0)

**Każda jednostka otrzymuje własne obrażenia surowe**, obliczane na podstawie jej obecnego *maksymalnego* PŻ (MAX PŻ), a nie bieżącego zdrowia:

`obrażenia = max(licznik tur Burdy, ceil(MAX PŻ jednostki / 10))`

- **Licznik tur** odczytuje się **przed** zmniejszeniem go o 1. Przy pojedynczym kuflu ma wartości 3, potem 2 i 1.
- **Minimum 10% MAX PŻ** jest liczone osobno dla każdej jednostki i **zaokrąglane w górę**. Dotyczy także ostatniego ticku Burdy z licznikiem 1.
- Najpierw wyznaczane są obrażenia surowe, **potem Tarcza i pancerz** pochłaniają obrażenia zgodnie ze zwykłymi zasadami walki. Dlatego rzeczywisty ubytek PŻ może być mniejszy lub zerowy.
- **Przykład:** przy liczniku 3, 2, 1 jednostka z 10 MAX PŻ dostaje odpowiednio **3, 2, 1** surowych obrażeń, a jednostka ze 101 MAX PŻ — **11, 11, 11**. Te wartości mogą być zmniejszone przez osłony.
- Kolejny kufel **dodaje 3 do pozostałego licznika**, więc może od razu zwiększyć podstawę następnego ticku. Nadal stosuje się większą z dwóch wartości: licznik albo minimum 10% MAX PŻ danej jednostki.

### Cena kufla i zgodność starszych partii

- W nowych partiach od **0.9.97** pierwszy kufel danego gracza ma cenę bazową **10 monet**, drugi **20**, trzeci **30** itd. Do ceny dodawana jest **1 moneta za każde 2 rozpoczęte tury obu graczy łącznie**: `10 + 10 × (wcześniejsze własne kufle) + floor(rozpoczęte tury obu graczy/2)`. Przykład: po 12 turach pierwszy kufel kosztuje 16, a drugi 26 monet, niezależnie od posiadanego salda.
- Partie rozpoczęte w **0.9.100–0.9.104** zachowują dawną zasadę **malejących obrażeń równych licznikowi**: po jednym kuflu 3→2→1 surowych obrażeń na jednostkę, niezależnie od MAX PŻ.
- Jeszcze starsze partie z **0.9.95–0.9.99** zachowują **1 surowe obrażenie na jednostkę na koniec tury**, niezależnie od licznika. W meczach rozpoczętych w **0.9.95–0.9.96** pozostaje również stary cennik `max(10 + rozpoczęte tury, ceil(monety/10))`.
- **Wczytanie zapisu lub podpisanej powtórki nie zmienia historycznych reguł.** Nowe minimum 10% nie jest dopisywane wstecz do już rozpoczętych gier.

Podczas animacji kupiony kufel pojawia się po prawej krawędzi planszy, wylewa piwo na ramę i zapala ogień przy polach jednostek. Płomienie są wizualizacją aktywnej Burdy i nie zadają osobnego natychmiastowego obrażenia. **A** wyłącza animacje bez wpływu na wynik rozgrywki.

## Jak działa Generał A002? (od 0.9.93)

**Generał Oddziału Natarcia zawsze premiuje wyłącznie własną planszę:**
- Podstawowy: +1 ATK wszystkim własnym jednostkom na planszy, w tym Generałowi, dopóki pozostaje aktywny.
- Rzadki: tylko jedna wybrana własna jednostka otrzymuje możliwość do dwóch ataków i podwójne obrażenia swoich standardowych ataków.
- Legendarny: tylko NOWO zagrani/przywołani sojusznicy po jego awansie lub wystawieniu otrzymują podwójny atak i podwójne obrażenia standardowe. Nie obejmuje wrogów ani starszych sojuszników.
- Każdy wariant v24 przy wejściu dostaje Tarczę; rzadki +2, legendarny +4 trwałego pancerza.

Starsze podpisane partie, których reguły miały premię podstawowego Generała na obu planszach, są nadal odtwarzane według **oryginalnej** wersji. W nowych partiach taka premia nie wzmacnia przeciwnika.

## Jak licytuje komputer? (0.9.91)

Na poziomie **trudnym**, od 0.9.94, dodatkowa szybka analiza kilku ataków potrafi wykorzystać kombinację zdjęcia Tarczy i zadania końcowego ciosu, bez długiego namysłu lub podglądania ręki gracza. 

Na poziomie **trudnym**, od 0.9.93, komputer dodatkowo ocenia wszystkie legalne pary atakujący–cel, planuje potencjalne zakończenie meczu, porównuje odwet i ryzyko uruchomienia zdolności śmierci.

Na poziomie **łatwym** komputer wydaje na jedną aukcję najwyżej połowę monet, które ma w chwili licytacji (zaokrąglenie w dół). Na **normalnym**, od 0.9.102, licytuje tylko wtedy, gdy pierwszy wybór daje sensowną przewagę nad drugą kartą za darmo lub pozwala odebrać przeciwnikowi ważny wybór. Nie zwiększa już budżetu tylko z powodu numeru aukcji, potrafi pasować przy podobnych ofertach, a o mocną kartę walczy zdecydowanie, zachowując monety na przyszłe aukcje. Na **trudnym** uwzględnia dodatkowo publiczny stan planszy przeciwnika, wartość zachowania monet i to, jakie archetypy pozostają w puli. AI nie podgląda ręki ani talii gracza. Żaden poziom nie gwarantuje zwycięstwa lub porażki w każdej partii.

## Najważniejsze skróty

| Klawisz | Znaczenie |
|---|---|
| `SPACJA` | Koniec tury lub potwierdzenie ostrzeżenia |
| `I` | Szczegóły wybranej karty |
| `F1` | Wbudowana instrukcja |
| `T` | Wskazówki i samouczek |
| `H` | Historia zdarzeń |
| `P` | Powtórka |
| `M` | Menu |
| `R` | Nowy mecz |
| `A` | Animacje |
| `B` | Zamów piwo za wyświetloną cenę podczas swojej tury |
| `F8` | Szybkość prezentacji ruchów AI |
| `F11` | Tryb pełnoekranowy |

## Koniec meczu, zapisy i statystyki

Po zakończeniu gry zobaczysz zwycięzcę, długość meczu, statystyki działań i najciekawsze osiągnięcia. Szczegóły wymagające pełnej historii są pomijane przy starszych, niekompletnych zapisach, aby nie podawać niepewnych wartości. Możesz otworzyć **Księgę Starć** oraz zapisane audyty.

Na Windows zapisy, diagnostyka i historia pozostają lokalnie w `%LOCALAPPDATA%\AuctionHammer\`. Komputer ma poziomy trudności **łatwy, normalny i trudny**. Nie ma trybu wieloosobowego ani logowania.

**Pomoc:** [Problemy i FAQ](TROUBLESHOOTING.md) · [Bieżące szczegółowe zasady](CURRENT_MVP_RULES_0964.md) · [Historia wydań](../CHANGELOG.md).
