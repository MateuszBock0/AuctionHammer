"""Complete Game Master v17 scaling audit for all 70 distinct starter cards.

The expected values are independent of the engine and are taken from the
canonical starter card descriptions: per-own-turn stat growth, a quality
threshold every 3 completed own hand turns, and exactly one quality bonus
per tier (never one bonus per poison/regeneration tick).
"""
import unittest
from game.core.models import Choice
from test_engine import setup_game,force_unit

BASE = {
    "Obrażenia":dict(S01=3,S09=1,S21=4,S27=1,S103=1),
    "Leczenie":dict(S02=4,S10=2,S17=6,S25=2,S104=4),
    "ATK ±":dict(S04=1,S68=1,S23=2,S28=1,S34=1),
    "MAX HP ±":dict(S08=4,S69=1,S81=5,S93=1,S35=1),
    "Pancerz":dict(S03=4,S12=2,S82=6,S26=2,S105=2),
    "Ogłuszenie":dict(S59=1,S15=0,S84=2,S95=0,S108=0),
    "Oczyszczanie":dict(S07=1,S74=0,S87=0,S97=0,S111=0),
    "Odporność":dict(S64=0,S76=0,S88=0,S99=0,S39=0),
    "Trucizna":dict(S58=(2,2),S11=(1,2),S83=(2,3),S32=(1,2),S107=(1,2)),
    "Regeneracja":dict(S60=(3,2),S71=(1,2),S85=(3,3),S31=(1,2),S109=2),
}
STAT_ONLY=("Tarcza","Prowokacja","Szybki atak","Podwójny atak")


def scenario(cid, turns):
    g=setup_game(605)
    g.cards[cid].hand_turns=turns
    ally_id=next(i for i in ("S02","S05","S31","S39","S67") if i!=cid)
    enemy_id=next(i for i in ("S33","S72","S86","S79","S103") if i!=cid)
    if cid=="S39":
        # The S39 armour bonus is activated automatically on *real* play.
        for pl in g.players:
            for zone in ("hand","deck","grave","board"):
                if cid in getattr(pl,zone):getattr(pl,zone).remove(cid)
        if cid in g.bank:g.bank.remove(cid)
        g.cards[cid].owner=0;g.cards[cid].zone="hand";g.players[0].hand.append(cid)
        g.play(cid)
        source=g.units[cid]
    else:
        source=force_unit(g,cid,0)
    ally=force_unit(g,ally_id,0)
    enemy=force_unit(g,enemy_id,1)
    ally.base_max_hp=200;ally.hp=100
    enemy.base_max_hp=200;enemy.hp=100
    source.base_max_hp=200;source.hp=100
    g.players[0].hp=40;g.players[1].hp=100
    return g,source,ally,enemy,ally_id,enemy_id


def observed_quality(cid,turns):
    g,source,ally,enemy,aid,eid=scenario(cid,turns)
    level=turns//3
    faction=g.cards[cid].definition.faction
    context={"Elfy":"play","Dzikie bestie":"attack","Potwory":"death",
             "Krasnoludy":"end","Ludzie":"play"}[faction]
    def execute(mode="auto",target=None,attacked=None):
        g._execute(cid,context,Choice(mode,target,""),attacked=attacked)
    if cid in ("S01","S09","S21","S27","S103"):
        if cid=="S01":execute("Cel wrogi",eid)
        elif cid=="S09":execute(target=eid,attacked=eid)
        elif cid=="S21":execute()
        elif cid=="S27":execute()
        else:g._finish_attack(eid,cid)
        if cid=="S21":return 100-g.players[1].hp
        if cid=="S103":return 100-enemy.hp-source.atk
        return 100-enemy.hp
    if cid in ("S02","S10","S17","S25","S104"):
        if cid=="S02":execute("Leczenie",aid)
        elif cid=="S10":execute(attacked=eid)
        elif cid=="S17":execute()
        elif cid=="S25":execute("Cel sojuszniczy",aid)
        else:g._heal(aid,2)
        if cid=="S10":return source.hp-100
        if cid=="S17":return g.players[0].hp-40
        return ally.hp-100
    if cid in ("S04","S68","S23","S28","S34"):
        old_ally=ally.atk;old_src=source.atk
        if cid=="S34":execute("ally")
        elif cid=="S68":execute("Wzmocnij siebie",cid,attacked=eid)
        else:execute("Wzmocnij",aid)
        return source.atk-old_src if cid=="S68" else ally.atk-old_ally
    if cid in ("S08","S69","S81","S93","S35"):
        if cid=="S35":execute("ally")
        elif cid=="S69":execute("Wzmocnij siebie",cid,attacked=eid)
        else:execute("Wzmocnij",aid)
        return source.max_hp-source.base_max_hp if cid=="S69" else ally.max_hp-ally.base_max_hp
    if cid in ("S03","S12","S82","S26","S105"):
        if cid=="S12":
            enemy.armor_perm=20
            execute(target=eid,attacked=eid)
            return 20-enemy.armor
        if cid=="S105":g._update_auras()
        else:execute("Cel sojuszniczy" if cid in ("S03","S26") else "Pozostała jednostka",aid)
        return ally.armor
    if cid in ("S58","S11","S83","S32","S107"):
        if cid in ("S58","S83","S32"):execute("Cel wrogi",eid)
        elif cid=="S11":execute(target=eid,attacked=eid)
        else:g._finish_attack(eid,cid)
        portions=[e for e in enemy.effects if e.kind=="poison" and e.source==cid]
        assert len(portions)==1,(cid,portions)
        portion=portions[0]
        return portion.bonus_once,portion.value,portion.remaining
    if cid in ("S59","S15","S84","S95","S108"):
        if cid in ("S59","S84"):execute("Cel wrogi",eid)
        elif cid=="S15":execute(target=eid,attacked=eid)
        elif cid=="S95":execute()
        else:g._update_auras()
        assert any(e.kind=="stun" for e in enemy.effects),cid
        return 100-enemy.hp
    if cid in ("S60","S71","S85","S31","S109"):
        if cid=="S109":
            g._finalize_end_turn()
            return source.hp-100
        if cid=="S71":execute(attacked=eid)
        else:execute("Pozostała jednostka" if cid=="S85" else "Cel sojuszniczy",aid)
        target=source if cid=="S71" else ally
        portions=[e for e in target.effects if e.kind=="regen" and e.source==cid]
        assert len(portions)==1,cid
        portion=portions[0]
        return portion.bonus_once,portion.value,portion.remaining
    if cid in ("S07","S74","S87","S97","S111"):
        target_id=eid if cid=="S74" else cid if cid=="S111" else aid
        target=g.units[target_id]
        target.hp=100
        if cid=="S74":
            g._add_effect(target_id,"atk",3,expires=3,source="S04",positive=True)
        else:
            g._add_effect(target_id,"stun",expires=3,source="S59",positive=False)
        if cid=="S07":execute("Oczyść własną",target_id)
        elif cid=="S74":execute(target=target_id,attacked=target_id)
        elif cid=="S87":execute("Pozostała jednostka",target_id)
        elif cid=="S97":execute("Cel sojuszniczy",target_id)
        # S111 is a passive: it must remove the debuff on application itself.
        return (100-target.hp) if cid=="S74" else target.hp-100
    if cid in ("S64","S76","S88","S99","S39"):
        if cid=="S64":execute("Cel sojuszniczy",aid)
        elif cid=="S76":execute(attacked=eid)
        elif cid=="S88":execute("Pozostała jednostka",aid)
        elif cid=="S99":execute("Cel sojuszniczy",aid)
        return source.armor if cid in ("S76","S39") else ally.armor
    raise AssertionError("Card not included in quality audit: "+cid)


class FullScalingAudit(unittest.TestCase):
    def test_every_card_covered_by_one_of_14_families(self):
        g=setup_game(605)
        self.assertEqual(len(g.defs),70)
        self.assertEqual(len({c.family for c in g.defs.values()}),14)
        self.assertEqual(set(g.defs),{
            id for entries in BASE.values() for id in entries
        } | {id for id,c in g.defs.items() if c.family in STAT_ONLY})
        for family in {c.family for c in g.defs.values()}:
            self.assertEqual(sum(c.family==family for c in g.defs.values()),5)

    def test_all_70_card_stats_at_every_threshold(self):
        g=setup_game(606)
        for cid,definition in g.defs.items():
            for turns in (0,1,2,3,4,5,6,8,9,12):
                with self.subTest(card=cid,turns=turns):
                    c=g.cards[cid]
                    c.hand_turns=turns
                    level=turns//3
                    atk_bonus=2*level if definition.family in ("Szybki atak","Podwójny atak") else 0
                    hp_bonus=(3*level if definition.family in ("Tarcza","Prowokacja")
                              else level if definition.family=="Szybki atak" else 0)
                    self.assertEqual(c.ability_level,level)
                    self.assertEqual(c.attack,definition.atk + turns*definition.growth_atk + atk_bonus)
                    self.assertEqual(c.max_hp,definition.hp + turns*definition.growth_hp + hp_bonus)

    def test_active_quality_scaling_all_50_cards_0_3_6_9(self):
        for family,entries in BASE.items():
            for cid,base in entries.items():
                for turns in (0,3,6,9):
                    with self.subTest(family=family,card=cid,turns=turns):
                        tier=turns//3
                        observed=observed_quality(cid,turns)
                        if family in ("Trucizna","Regeneracja") and cid!="S109":
                            expected=(tier,base[0],base[1])
                        else:
                            expected=base+tier
                        self.assertEqual(observed,expected)

    def test_ability_is_frozen_when_unit_leaves_hand(self):
        g=setup_game(607)
        card=g.cards["S01"]
        card.hand_turns=6
        unit=force_unit(g,"S01",0)
        self.assertEqual(unit.ability_level,2)
        card.hand_turns=12
        self.assertEqual(unit.ability_level,2)
        g._remove_unit("S01",death=False)
        self.assertEqual(card.hand_turns,0)

    def test_only_own_completed_hand_turn_increases_quality(self):
        g=setup_game(608)
        cid=g.players[0].hand[0]
        card=g.cards[cid]
        self.assertEqual(card.hand_turns,0)
        g.active=1
        g._finalize_end_turn()
        self.assertEqual(card.hand_turns,0)
        g.active=0
        for own_turn in (1,2,3,4,5,6):
            g._finalize_end_turn()
            self.assertEqual(card.hand_turns,own_turn)
            self.assertEqual(card.ability_level,own_turn//3)

    def test_s111_cleanses_temporary_not_permanent_negative(self):
        g,s,_,_,_,_=scenario("S111",6)
        before=s.hp
        accepted=g._add_effect("S111","atk",-2,source="S04",positive=False)
        self.assertTrue(accepted)
        self.assertEqual(s.atk,g.cards["S111"].attack-2)
        self.assertEqual(s.hp,before)
        accepted=g._add_effect("S111","atk",-1,source="S68",positive=False,expire_action=g.action_turn)
        self.assertFalse(accepted)
        self.assertEqual(s.hp,before+2)
        self.assertEqual(s.atk,g.cards["S111"].attack-2)

    def test_s111_poison_immediately_cleaned_and_qualifies_for_healing(self):
        g,s,_,_,_,_=scenario("S111",3)
        s.hp=100
        g._add_poison("S111",1,2,"S58")
        self.assertFalse(any(e.kind=="poison" for e in s.effects))
        self.assertEqual(s.hp,101)

    def test_action_lifetime_buff_is_a_valid_cleanse_target(self):
        g,s,_,enemy,_,eid=scenario("S74",3)
        enemy.hp=100
        g._add_effect(eid,"atk",2,source="S68",positive=True,expire_action=g.action_turn)
        g._execute("S74","attack",Choice("auto",eid,""),attacked=eid)
        self.assertFalse(any(e.kind=="atk" for e in enemy.effects))
        self.assertEqual(enemy.hp,99)

    def test_stat_only_family_abilities_do_not_gain_extra_uses(self):
        """The other 20 cards gain stats, not extra shields, attacks or triggers."""
        all_ids={
            "Tarcza":("S05","S70","S20","S94","S106"),
            "Prowokacja":("S61","S72","S86","S96","S33"),
            "Szybki atak":("S66","S78","S90","S101","S114"),
            "Podwójny atak":("S67","S79","S91","S102","S115"),
        }
        for family,ids in all_ids.items():
            for cid in ids:
                for turns in (0,3,6,9):
                    with self.subTest(family=family,card=cid,turns=turns):
                        g,source,ally,enemy,aid,eid=scenario(cid,turns)
                        def skill(context, mode="auto", target=None, attacked=None):
                            g._execute(cid,context,Choice(mode,target,""),attacked=attacked)
                        if family=="Tarcza":
                            if cid=="S05":skill("play","Cel sojuszniczy",aid)
                            elif cid=="S70":skill("attack",attacked=eid)
                            elif cid=="S20":skill("death","Pozostała jednostka",aid)
                            elif cid=="S94":skill("end","Cel sojuszniczy",aid)
                            else:
                                # Automatic S106 shield is granted during PLAY_CARD.
                                g.players[0].board.remove(cid)
                                del g.units[cid]
                                g.players[0].hand.append(cid)
                                g.cards[cid].zone="hand"
                                g.players[0].played_this_turn=False
                                g.play(cid)
                                source=g.units[cid]
                            shield=source.shield if cid in ("S70","S106") else ally.shield
                            self.assertEqual(shield,1)
                        elif family=="Prowokacja":
                            if cid=="S61":skill("play","Cel sojuszniczy",aid)
                            elif cid=="S72":skill("attack",attacked=eid)
                            elif cid=="S86":skill("death","Pozostała jednostka",aid)
                            elif cid=="S96":skill("end","Cel sojuszniczy",aid)
                            recipient=source if cid in ("S72","S33") else ally
                            self.assertTrue(g._taunt(recipient))
                        elif family=="Szybki atak":
                            if cid=="S78":
                                skill("attack","Nadaj szybki atak",aid,attacked=eid)
                                self.assertTrue(g._fast(ally))
                            elif cid=="S90":
                                skill("death")
                                self.assertTrue(g.players[0].next_fast)
                            elif cid=="S101":
                                held=g.players[0].hand[0]
                                skill("end","Szybki atak w kolejnej turze",held)
                                self.assertEqual(g.cards[held].quick_next_turn,
                                                 g.players[0].turn_count+1)
                            else:self.assertTrue(g._fast(source))
                            if cid in ("S66","S114"):
                                self.assertEqual(2 if g._double(source) else 1,1)
                        else:
                            if cid=="S79":source.attacks=1
                            elif cid=="S91":skill("death","Pozostała jednostka",aid)
                            elif cid=="S102":skill("end","Podwójny atak na następną turę",aid)
                            recipient=ally if cid in ("S91","S102") else source
                            self.assertTrue(g._double(recipient))
                            self.assertEqual(2 if g._double(recipient) else 1,2)

    def test_poison_ability_bonus_occurs_once_not_each_tick(self):
        g,s,_,enemy,_,eid=scenario("S58",6)
        g._execute("S58","play",Choice("Cel wrogi",eid,""))
        before=enemy.hp
        g._tick_poison(1)
        g._tick_poison(1)
        self.assertEqual(before-enemy.hp,2*2+2)

    def test_regen_ability_bonus_occurs_once_not_each_tick(self):
        g,s,ally,enemy,aid,eid=scenario("S60",6)
        g._execute("S60","play",Choice("Cel sojuszniczy",aid,""))
        old=ally.hp
        g._finalize_end_turn()
        g._finalize_end_turn()
        self.assertEqual(ally.hp-old,3*2+2)


if __name__=="__main__":
    unittest.main()
