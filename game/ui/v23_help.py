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
        "full": "Przy śmierci oczyść inną własną jednostkę z tymczasowych negatywnych efektów i przyznaj jej 2 trwałego pancerza (przy skutecznym oczyszczeniu dodatkowo +1 PŻ leczenia za poziom). Jeśli nie ma innego sojusznika, spróbuj uleczyć własnego bohatera o 4 PŻ."
    },
    "S88": {
        "short": "Po śmierci: odporność sojusznika / Tarcza bohatera",
        "full": "Przy śmierci nadaj innej własnej jednostce odporność na truciznę i ogłuszenie do jej opuszczenia planszy. Jeśli nie ma innego sojusznika, daj własnemu bohaterowi efekt Tarcza (1 ładunek)."
    },
    "S32": {
        "short": "Trucizna; jeśli wszyscy już zatruci: 2 obr. wrogowi z min. PŻ",
        "full": "Na koniec własnej tury nałóż truciznę (1 obrażenie przez 2 własne tury celu) na wroga, który jeszcze nie jest zatruty przez tego Alchemika. Jeśli istnieją wrogowie, ale wszyscy mają już jego truciznę, zadaj zamiast tego 2 zwykłe obrażenia jednostce z najniższym bieżącym PŻ; remis rozstrzyga pozycja od lewej."
    },
    "S95": {
        "short": "Ogłuszenie (+obr. gdy skuteczne); brak celu: 2 obr. bez ogłuszenia",
        "full": "Na koniec własnej tury spróbuj ogłuszyć wroga o najniższym ATK spośród legalnych nowych celów na 1 jego turę. Przy skutecznym ogłuszeniu zadaj 1+poziom obrażeń. Nie wybieraj tego samego celu w dwóch kolejnych własnych turach. Jeśli są wrogowie, ale brak legalnego nowego celu, zadaj zamiast tego 2 zwykłe obrażenia jednostce o najniższym ATK, bez ponownego ogłuszenia i bez aktualizowania pamięci celu."
    }
}

def v23_base_card_note(card_id: str, ruleset: str = 'v22') -> str:
    return _V23_COPY.get(card_id,{}).get('full','') if ruleset=='v23' else ''

def v23_base_card_short_note(card_id: str, ruleset: str = 'v22') -> str:
    return _V23_COPY.get(card_id,{}).get('short','') if ruleset=='v23' else ''
