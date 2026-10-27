"""Additional presentation-only v23 rule descriptions for base cards.

Never attach these to older v22/v4 savegames. Game definitions are immutable.
"""
_V23_COPY={
    "S86": {
        "short": "Po śmierci: Prowokacja sojusznika / +3 pancerza bohatera",
        "full": "Przy śmierci nadaj Prowokację innej własnej jednostce do opuszczenia planszy. Jeżeli nie ma innego sojusznika, bohater otrzymuje +3 pancerza."
    },
    "S87": {
        "short": "Po śmierci: oczyszczanie+pancerz / leczenie bohatera 4 PŻ",
        "full": "Przy śmierci oczyść innego sojusznika z czasowych negatywnych efektów i daj mu 2 trwałego pancerza (+1 PŻ leczenia za poziom tylko po skutecznym oczyszczeniu). Jeśli brak innego sojusznika, ulecz bohatera o 4 PŻ."
    },
    "S88": {
        "short": "Po śmierci: odporność sojusznika / Tarcza bohatera",
        "full": "Przy śmierci nadaj innej własnej jednostce odporność na truciznę i ogłuszenie do jej opuszczenia planszy. Jeśli nie ma innego sojusznika, daj własnemu bohaterowi efekt Tarcza (1 ładunek)."
    },
    "S32": {
        "short": "Trucizna; jeśli wszyscy już zatruci: 2 obr. wrogowi z min. PŻ",
        "full": "Na koniec tury nałóż na wroga bez trucizny tego Alchemika truciznę: 1 obrażenie przez 2 własne tury celu. Jeśli wrogowie są, lecz wszyscy mają już jego truciznę, zadaj 2 zwykłe obrażenia wrogowi o najniższym bieżącym PŻ (remis: najbardziej po lewej)."
    },
    "S95": {
        "short": "Ogłuszenie (+obr. gdy skuteczne); brak celu: 2 obr. bez ogłuszenia",
        "full": "Koniec tury: ogłusz na 1 turę dostępnego wroga o najniższym ATK; przy sukcesie zadaj 1 + poziom obrażeń. Nie wybieraj tego samego celu dwie tury z rzędu. Jeśli brak nowego celu, ale są wrogowie, zadaj 2 zwykłe obrażenia wrogowi o najniższym ATK (bez ogłuszenia i zmiany zapamiętanego celu)."
    },
    "S108": {
        "short": "Pierwszy wróg naprzeciw: ogłuszenie + obrażenia",
        "full": "Gdy wróg po raz pierwszy stanie naprzeciw Trębacza, spróbuj ogłuszyć go na 1 jego turę. Przy sukcesie zadaj 1 bazowe + poziom obrażeń, inaczej 0. Ten sam wróg nie uruchomi tej zdolności ponownie podczas tego wystawienia."
    },
    "S99": {
        "short": "Odporność + pancerz czasowy i trwały",
        "full": "Na koniec własnej tury: daj sojusznikowi odporność na truciznę i 1 tymczasowego pancerza do końca jego najbliższej własnej tury. Przy pierwszej aktywacji po wystawieniu dodaj za rozwój +poziom trwałego pancerza."
    },
}

def v23_base_card_note(card_id: str, ruleset: str = 'v22') -> str:
    return _V23_COPY.get(card_id,{}).get('full','') if ruleset=='v23' else ''

def v23_base_card_short_note(card_id: str, ruleset: str = 'v22') -> str:
    return _V23_COPY.get(card_id,{}).get('short','') if ruleset=='v23' else ''
