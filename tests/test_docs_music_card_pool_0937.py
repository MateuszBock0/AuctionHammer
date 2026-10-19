"""Documentation/attribution smoke tests and basic-vs-auction card provenance."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class PublicDocumentationTests(unittest.TestCase):
    def test_s34_is_a_basic_card_and_a002_is_auction_only(self):
        base=json.loads((ROOT/'data/cards_base_70.json').read_text(encoding='utf-8'))
        cards={card['id']:card for card in base}
        self.assertIn('S34',cards)
        self.assertIn('Chorąży Królewskiej Kompanii',cards['S34']['name'])
        self.assertIn('+1 ATK',cards['S34']['effect'])
        self.assertIn('−1 ATK',cards['S34']['effect'])
        self.assertNotIn('A002',cards)
        auction=json.loads((ROOT/'data/auction/KATALOG_AUKCYJNY_17_v22.json').read_text(encoding='utf-8'))
        auction_cards={card['id']:card for card in auction['cards']}
        self.assertIn('A002',auction_cards)

    def test_readme_gives_complete_soundtrack_credit_without_public_license_claim(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        for term in ('Alek Kaczan','PGN Music','Paradox Gaming Network',
                     'fantasy-tavern-album','2021','S34','A002'):
            self.assertIn(term,text)
        version=json.loads((ROOT/'VERSION.json').read_text(encoding='utf-8'))['mvp']
        self.assertIn('Aktualna wersja: '+version,text)
        self.assertNotIn('Plik MP3 może być dystrybuowany razem z grą',text)
        self.assertNotIn('potwierdził uzyskanie zgody',text)

    def test_mit_license_is_not_misattributed_to_album(self):
        text=(ROOT/'LICENSE').read_text(encoding='utf-8')
        self.assertIn('MIT License',text)
        self.assertIn('Permission is hereby granted, free of charge',text)
        self.assertIn('Mateusz Boćko',text)
        self.assertIn('not relicensed under MIT',text)
        music=(ROOT/'docs/THIRD_PARTY_MUSIC.md').read_text(encoding='utf-8')
        self.assertIn('The Dancing Barmaid',music)
        self.assertIn('CC BY 4.0',music)
        self.assertIn('CC BY-SA',music)
        self.assertNotIn('Used with permission of the rights holder',music)


if __name__=='__main__':
    unittest.main()
