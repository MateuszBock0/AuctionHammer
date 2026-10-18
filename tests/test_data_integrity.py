"""Kontrola integralności aktualnego katalogu i zasad v19; archiwum v17 pozostaje historyczne."""
from pathlib import Path
import unittest, json, random, sys
ROOT = Path(__file__).resolve().parents[1]
def load(name): return json.loads((ROOT/'data'/name).read_text('utf-8'))

class DataIntegrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cards=load('cards_base_70.json')
  cls.rules=load('game_rules_v19.json')
  cls.old_rules=load('game_rules_v17.json')
  cls.bank=load('starter_bank_v17.json')
  cls.events=load('event_order_v19.json')
  cls.events_v17=load('event_order_v17.json')
  cls.master=load('GAME_MASTER.json')
  cls.status=load('PROJECT_STATUS_v17.json')
 def test_counts(self):
  self.assertEqual(len(self.cards),70)
  self.assertEqual(len(set(x['id'] for x in self.cards)),70)
  self.assertEqual(len(set(x['name'] for x in self.cards)),70)
  self.assertEqual(len(self.bank['unique_archetype_ids']),70)
  self.assertEqual(set(self.bank['unique_archetype_ids']),set(c['id'] for c in self.cards))
  self.assertEqual(self.bank['copies_per_archetype'],1)
  self.assertEqual(self.rules['initial']['starter_physical_copies'],70)
 def test_matrix(self):
  expected={'Elfy':'Przy wystawieniu','Dzikie bestie':'Przy ataku','Potwory':'Przy śmierci','Krasnoludy':'Na koniec tury','Ludzie':'Pasywna'}
  combinations=set()
  for c in self.cards:
   self.assertEqual(c['trigger'],expected[c['faction']])
   self.assertEqual(c['hand_growth']['atk_per_hand_turn']+c['hand_growth']['hp_per_hand_turn'],2)
   self.assertTrue(c['effect'])
   combinations.add((c['faction'],c['family']))
  self.assertEqual(len(combinations),70)
  for f in expected:self.assertEqual(sum(c['faction']==f for c in self.cards),14)
 def test_start_and_mulligan(self):
  self.assertEqual(self.rules['initial']['second_player_coins'],3)
  self.assertEqual(self.rules['initial']['hero_start_hp'],100)
  self.assertEqual(self.rules['initial']['initial_hero_armor'],0)
  self.assertEqual(self.rules['initial']['initial_mulligan_max'],3)
  m=self.rules['initial']['mulligan_protocol']
  self.assertEqual(m['rejected_cards_destination'],'EXCLUDED_FROM_MATCH')
  self.assertFalse(m['rejected_cards_return_to_pool'])
  self.assertFalse(m['rejected_cards_accessible_to_any_player'])
  self.assertTrue(m['excluded_cards_do_not_reenter_match'])
 def test_no_timer(self):
  d=self.rules['time_limits']
  self.assertFalse(d['enabled'])
  for key in ('mulligan_seconds','turn_seconds','target_choice_seconds','auction_bid_seconds','auction_pick_seconds'):
   self.assertIsNone(d[key])
  for key in ('timeout_events_enabled','automatic_pass_on_inactivity','automatic_end_turn_on_inactivity','loss_on_inactivity'):
   self.assertFalse(d[key])
 def test_locked_event_order(self):
  self.assertEqual(self.events['status'],'LOCKED_GLOBAL_PRIORITY')
  self.assertEqual(len(self.events['authoritative_priority']),10)
  self.assertEqual(self.events['version'],'19.0')
  self.assertEqual(self.events_v17['version'],'17.0')
  self.assertEqual(self.master['canonical_event_order_file'],'data/event_order_v19.json')
  self.assertEqual(self.rules['canonical_event_order_file'],'data/event_order_v19.json')
 def test_consistent_rule_sources(self):
  self.assertEqual(self.rules['version'],'19.0')
  self.assertEqual(self.old_rules['version'],'17.0')
  self.assertEqual(self.master['rules'],self.rules)
  self.assertEqual(self.master['starter_cards'],self.cards)
  self.assertEqual(self.status['canonical_files']['cards'],'data/cards_base_70.json')
  self.assertEqual(self.status['base_design_status'],'LOCKED_FOR_MVP')
  self.assertEqual(self.master['status'],'BASE_GAME_DESIGN_LOCKED_FOR_IMPLEMENTATION_AUCTIONS_PENDING')
 def test_repeated_mulligan_without_duplicates(self):
  rng=random.Random(17)
  ids=self.bank['unique_archetype_ids']
  for _ in range(3000):
   dealt=rng.sample(ids,20)
   initial_hand_a, initial_deck_a=dealt[:5],dealt[5:10]
   initial_hand_b, initial_deck_b=dealt[10:15],dealt[15:20]
   bank=[x for x in ids if x not in dealt]
   na,nb=rng.randint(0,3),rng.randint(0,3)
   removed_a=rng.sample(initial_hand_a,na)
   removed_b=rng.sample(initial_hand_b,nb)
   excluded=set(removed_a+removed_b)
   added=rng.sample(bank,na+nb)
   hand_a=[x for x in initial_hand_a if x not in excluded]+added[:na]
   hand_b=[x for x in initial_hand_b if x not in excluded]+added[na:]
   available=set(ids)-set(dealt)-set(added)
   all_in_play=hand_a+initial_deck_a+hand_b+initial_deck_b
   self.assertEqual(len(all_in_play),20)
   self.assertEqual(len(set(all_in_play)),20)
   self.assertFalse(excluded & set(all_in_play))
   self.assertFalse(excluded & available)
   self.assertEqual(len(available),50-na-nb)
   self.assertEqual(len(available)+len(excluded)+len(all_in_play),70)

if __name__=='__main__':unittest.main(verbosity=2)
