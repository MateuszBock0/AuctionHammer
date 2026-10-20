"""Read-only first-match coach and rules reference for AuctionHammer v23.

Never drives game commands, changes engine objects or calculates legal targets
independently. The coach observes successful audited actions and public state.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialHint:
    title: str
    detail: str
    stage: int


@dataclass(frozen=True)
class HelpPage:
    title: str
    intro: str
    sections: tuple[tuple[str, str], ...]


HELP_PAGES = (
    HelpPage(
        "PIERWSZY MECZ",
        "Cel: sprowadź PŻ bohatera przeciwnika do zera. Obaj zaczynacie ze 100 PŻ.",
        (
            ("1. START", "Masz pięć kart na ręce i pięć w talii. Możesz wymienić do trzech kart, a potem zatwierdzić Enterem."),
            ("2. ZAGRYWANIE", "Zazwyczaj raz na własną turę wybierz kartę z ręki i kliknij wolne pole. Plansza mieści pięć jednostek. Zwykłe karty nie kosztują monet."),
            ("3. ROZWÓJ", "Karty podstawowe rosną przez ukończone własne tury spędzone na ręce. Przyrost zależy od karty; co trzy takie tury mogą ulepszyć zdolność."),
            ("4. TURA", "Kliknij jednostkę i legalny, podświetlony cel. Nowa jednostka zwykle czeka z atakiem do następnej własnej tury. Spacja kończy turę."),
        ),
    ),
    HelpPage(
        "WALKA I STATUSY",
        "Legalne cele określa silnik. Zwykła walka jednostek rozstrzyga wzajemne trafienia.",
        (
            ("PROWOKACJA", "Żywa jednostka z aktywną Prowokacją ogranicza wybór celów przeciwnika. Podświetlenie pokazuje cele dostępne TERAZ."),
            ("TARCZA I PANCERZ", "Tarcza pochłania trafienie, a pancerz zmniejsza przyjmowane obrażenia. Raport pokazuje rzeczywistą utratę PŻ."),
            ("OGŁUSZENIE I TRUCIZNA", "Ogłuszenie blokuje atak; trucizna i inne statusy działają zgodnie z opisem i czasem trwania widocznym pod [I]."),
            ("SZYBKI / PODWÓJNY ATAK", "Szybki atak może ominąć oczekiwanie po wystawieniu. Podwójny daje drugą możliwość ataku, o ile nadal istnieje legalny cel."),
            ("ZDOLNOŚCI", "Efekt może uruchamiać się przy wystawieniu, ataku, śmierci, na końcu tury albo pasywnie. [I] wyświetla bieżące liczby i źródła statusów."),
        ),
    ),
    HelpPage(
        "MONETY I AUKCJE",
        "Po każdej trzeciej pełnej rundzie, gdy dostępne są co najmniej trzy oferty, rozpoczyna się aukcja.",
        (
            ("O CO LICYTUJESZ?", "Stawką jest PIERWSZY wybór jednej z trzech kart. Wygrywający płaci własną ofertę. Drugi gracz wybiera za darmo jedną z dwóch pozostałych."),
            ("LICYTACJA", "Suwak i strzałki zmieniają kwotę; Enter składa ofertę, Esc pasuje. Bonus do skutecznej oferty nie jest automatycznie wydatkiem w monetach."),
            ("NIEWYBRANA KARTA", "Pozostały archetyp wraca do aukcyjnej puli. Kupione archetypy już do niej nie wracają."),
            ("RZADKOŚĆ", "Wariant podstawowy, rzadki lub legendarny określa zdolność. Po zakupie może awansować co trzy ukończone rundy bez wzrostu ATK / maks. PŻ."),
            ("DOCHÓD", "Po pełnej rundzie obaj otrzymują +1 monetę. W nowych meczach v22 koniec własnej tury daje dodatkowo 5 minus liczba własnych jednostek."),
        ),
    ),
    HelpPage(
        "STEROWANIE I ANALIZA",
        "Podpowiedzi, opisy i samouczek są tylko wizualne i nie zmieniają wyniku meczu.",
        (
            ("KARTY", "Lewy przycisk: zaznacz i zagraj / atakuj. [I]: pełny opis wybranej karty. Przytrzymaj kursor na karcie z ręki, by zobaczyć większy podgląd."),
            ("SZYBKIE KLAWISZE", "Spacja: zakończ turę. [M]: menu i zapis. [H]: dziennik. [P]: powtórka. [R]: nowy mecz (z potwierdzeniem)."),
            ("POMOC", "[F1]: otwórz lub zamknij ten podręcznik. Strzałki: następna / poprzednia strona. [T]: pokaż lub wyłącz wskazówki samouczka."),
            ("KSIĘGA STARC", "Po zakończeniu partii przycisk i [W] otwierają szczegóły każdego ataku: PŻ, ATK, pancerz, statusy, zdarzenia i operacje silnika."),
            ("DOKŁADNE ZASADY", "W razie wątpliwości aktualny opis w [I], statusy i legalne cele w silniku mają pierwszeństwo przed ogólnymi przykładami w samouczku."),
        ),
    ),
)

ATTACK_EXPLANATIONS = {
    "OGŁUSZONA": "Ogłuszenie blokuje atak, dopóki efekt nie wygaśnie.",
    "CZEKA NA TURĘ": "Atakować można podczas własnej tury.",
    "TRWA WYBÓR": "Najpierw rozstrzygnij oczekujący wybór zdolności.",
    "NOWA JEDNOSTKA": "Odczekaj do kolejnej własnej tury albo uzyskaj Szybki atak.",
    "ATAKI WYKORZYSTANE": "Limit ataków na tę turę został wykorzystany.",
    "BRAK LEGALNEGO CELU": "Cel jest niedostępny według zasad silnika, np. przez Prowokację.",
    "GOTOWA": "Wybierz podświetlony, legalny cel ataku.",
}


def attack_reason_help(reason: str) -> str:
    """Explanations decorate the authoritative attack_display() result only."""
    clean=reason.partition(" · ")[0]
    return ATTACK_EXPLANATIONS.get(clean, "Sprawdź opis zdolności [I] i legalne cele.")


class TutorialProgress:
    """A per-session, opt-in observer. The Match and signed audit stay unchanged."""

    def __init__(self):
        self.active=False
        self.play_seen=False
        self.attack_seen=False
        self.auction_seen=False
        self._observed=0

    def start(self, game):
        self.active=True
        self.play_seen=False
        self.attack_seen=False
        self.auction_seen=False
        self._observed=0
        self.observe(game)

    def observe(self, game):
        if not self.active:
            return
        actions=getattr(game,"audit_actions",[]) or []
        # Reopening the coach against a new/loaded match reindexes safely.
        if self._observed>len(actions):
            self._observed=0
        for action in actions[self._observed:]:
            if action.get("result")!="ok" or action.get("command_owner")!=0:
                continue
            operation=action.get("operation")
            if operation=="play":
                self.play_seen=True
            elif operation=="attack":
                self.attack_seen=True
        self._observed=len(actions)
        if getattr(game,"auction_history",None):
            self.auction_seen=True

    def hint(self, game) -> TutorialHint | None:
        if not self.active:
            return None
        if game.phase=="finished":
            return TutorialHint("KONIEC PARTII", "Otwórz Księgę Starć [W], sprawdź historię [H] lub zagraj ponownie [R].",5)
        if game.phase=="mulligan":
            if (game.first==1
                    and getattr(game,"starting_compensation",None)=="choice_2_5_or_coins"
                    and getattr(game,"starting_compensation_choice",None) is None):
                return TutorialHint("SAMOUCZEK 1/5 · REKOMPENSATA", "Drugi gracz wybiera Chorążego 2/5 albo +3 monety.",1)
            return TutorialHint("SAMOUCZEK 1/5 · WYMIANA", "Zaznacz do 3 kart z ręki i zatwierdź [ENTER]. Możesz nie wymieniać żadnej.",1)
        if game.phase=="auction":
            a=getattr(game,"auction",None)
            if a is None:
                return TutorialHint("SAMOUCZEK 4/5 · AUKCJA", "Trzy karty: licytujesz prawo pierwszego wyboru.",4)
            if a.phase=="bidding":
                return TutorialHint("SAMOUCZEK 4/5 · LICYTACJA", "Suwak / strzałki: kwota. [ENTER] oferta, [ESC] pas. Wygrywający płaci.",4)
            return TutorialHint("SAMOUCZEK 4/5 · WYBÓR", "Wybierz jedną kartę. Drugi gracz wybiera za darmo; trzecia oferta wraca do puli.",4)
        if getattr(game,"pending",None) is not None:
            if game.pending.owner!=0:
                return TutorialHint("SAMOUCZEK · RUCH KOMPUTERA", "Komputer rozstrzyga własną zdolność. Twoje akcje pozostają chwilowo zablokowane.",3)
            return TutorialHint("SAMOUCZEK · ZDOLNOŚĆ", "Wybierz legalny cel lub wariant w panelu po prawej. [I] pokazuje pełny opis.",3)
        if not self.play_seen:
            if game.active!=0:
                return TutorialHint("SAMOUCZEK 2/5 · TURA RYWALA", "Obserwuj ruch komputera. Zobaczysz swoje karty, gdy nadejdzie Twoja tura.",2)
            return TutorialHint("SAMOUCZEK 2/5 · ZAGRAJ KARTĘ", "Kliknij kartę z ręki, a potem wolne pole w dolnym rzędzie. Bez kosztu monet.",2)
        if not self.attack_seen:
            if game.active!=0:
                return TutorialHint("SAMOUCZEK 3/5 · PRZYGOTOWANIE", "Gdy nadejdzie Twoja tura, wybierz jednostkę gotową do ataku.",3)
            ready=any(game.legal_attacks(uid) for uid in game.players[0].board)
            if ready:
                return TutorialHint("SAMOUCZEK 3/5 · ATAK", "Kliknij gotową jednostkę i jeden z podświetlonych celów.",3)
            return TutorialHint("SAMOUCZEK 3/5 · ZAKOŃCZ TURĘ", "Nowa jednostka zwykle nie atakuje od razu. [SPACJA] kończy turę.",3)
        if not self.auction_seen:
            return TutorialHint("SAMOUCZEK 4/5 · CZEKAJ NA AUKCJĘ", "Po 3 pełnych rundach zobaczysz trzy oferty. Monety oszczędzaj na licytację.",4)
        return TutorialHint("SAMOUCZEK 5/5 · UKOŃCZONY", "Znasz już podstawy! [F1] otwiera zasady i statusy, [T] ukrywa podpowiedzi.",5)
