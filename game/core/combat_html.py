"""Self-contained offline HTML combat viewer; signed JSON remains authoritative."""
from __future__ import annotations

from html import escape
from pathlib import Path
import argparse
import json

from .combat_analysis import build_combat_analysis

FILENAME = "AuctionHammer-KSIEGA-STARC.html"


def _e(value):
    return escape(str(value), quote=True)


def _statuses(effects):
    if not effects:
        return '<span class="quiet">Brak</span>'
    return " ".join(
        '<span class="status">{kind} {value} · {source} · pozostało {ticks}</span>'.format(
            kind=_e(effect.get("kind", "?")),
            value=_e(effect.get("value", 0)),
            source=_e(effect.get("source") or "nieznane źródło"),
            ticks=_e(effect.get("remaining", "—"))
        ) for effect in effects
    )


def _stats(state):
    if state is None:
        return '<span class="dead">Jednostka nieobecna po rozstrzygnięciu (zgon/usunięcie)</span>'
    bits = (
        ("HP", str(state.get("hp")) + "/" + str(state.get("max_hp"))),
        ("ATK", state.get("attack")),
        ("Pancerz", state.get("armor")),
        ("Tarcza", state.get("shield")),
        ("Ataki wykonane", state.get("attacks_used"))
    )
    details = "".join(
        '<span class="metric"><b>{}</b> {}</span>'.format(_e(label), _e(value if value is not None else "—"))
        for label, value in bits
    )
    effects = state.get("effects", [])
    status_html = _statuses(effects)
    # Audits store General grants outside Unit.effects; the combat analysis
    # reads signed general_targets/general_grants and adds source-linked text.
    bonuses = state.get("combat_bonuses", [])
    if bonuses:
        bonus_html = " ".join('<span class="status">{}</span>'.format(_e(x))
                              for x in bonuses)
        status_html = (status_html + " " if effects else "") + bonus_html
    return '<div class="metrics">{}</div><p><b>Statusy i premie:</b> {}</p>'.format(
        details, status_html)


def _participant(role, participant):
    return ('<section class="participant"><h3>{} · {} <small>{}</small></h3>'
            '<div class="comparison"><div><h4>PRZED</h4>{}</div>'
            '<div><h4>PO</h4>{}</div></div></section>').format(
        _e(role), _e(participant["name"]), _e(participant["uid"]),
        _stats(participant["before"]), _stats(participant["after"]))


def _participant_died(participant):
    """A removed unit or a hero reduced to <=0 HP counts as a fatal outcome.

    Heroes remain in the signed state after death; unlike units, their
    participant.after is not None. Only inspect documented audit snapshots.
    """
    if participant.get("before") is None:
        return False
    after = participant.get("after")
    if after is None:
        return True
    hp = after.get("hp")
    return (after.get("type") == "hero"
            and isinstance(hp, (int, float)) and not isinstance(hp, bool)
            and hp <= 0)


def _micro(step):
    title = _e(step.get("operation", "?"))
    if step.get("operation") == "_damage":
        title += (" · cel: {} · żądane obrażenia: {} · "
                  "wynik funkcji (utrata HP): {}").format(
            _e(step.get("target")), _e(step.get("damage_requested")),
            _e(step.get("hp_damage_reported")))
    before = json.dumps(step.get("before"), ensure_ascii=False, indent=2)
    after = json.dumps(step.get("after"), ensure_ascii=False, indent=2)
    return ('<li><details><summary><b>#{}</b> {}</summary>'
            '<div class="micro"><div><b>PRZED mikrooperacją</b><pre>{}</pre></div>'
            '<div><b>PO mikrooperacji</b><pre>{}</pre></div></div></details></li>').format(
        _e(step.get("seq")), title, _e(before), _e(after))


def _battle(item):
    attacker = item["attacker"]
    defender = item["defender"]
    death = (_participant_died(attacker) or _participant_died(defender))
    title = "{} → {}".format(attacker["name"], defender["name"])
    searchable = (title + " " + attacker["uid"] + " " + defender["uid"]
                  + " " + " ".join(item["events"])).lower()
    steps = "".join(_micro(step) for step in item["steps"])
    events = "".join("<li>{}</li>".format(_e(event)) for event in item["events"])
    tag = '<span class="tag dead">Zgon</span>' if death else ""
    return ('<details class="battle" data-owner="{}" data-death="{}" data-search="{}">'
            '<summary><span class="round">R{} · ATAK #{}</span>'
            '<b>{}</b> <span class="tag">{} komend</span>{}</summary>'
            '<div class="body">{}{}<h3>Mikrooperacje silnika</h3><ol>{}</ol>'
            '<h3>Oryginalny dziennik zdarzeń</h3><ol>{}</ol></div></details>').format(
        _e(item["active_player"]), "1" if death else "0", _e(searchable),
        _e(item["round"]), _e(item["number"]), _e(title), len(item["actions"]), tag,
        _participant("Atakujący", attacker), _participant("Obrońca", defender),
        steps or "<li>Brak mikrooperacji</li>", events)


def _brawl_records(payload):
    """Visible brawl ticks, sourced only from the signed event journal."""
    groups={}
    for event in payload.get('event_journal',[]):
        message=event.get('text','')
        if not (message.startswith('KARCZEMNA BURDA:') or
                message.startswith('BURDA — ')):
            continue
        key=event.get('action_seq')
        if key is None:
            key=event.get('seq') if message.startswith('KARCZEMNA BURDA:') else None
        if key is None:
            continue
        group=groups.setdefault(key,{'round':event.get('round',0),
                                    'active':event.get('active',0),
                                    'messages':[], 'has_tick':False})
        if message.startswith('KARCZEMNA BURDA:'):
            group['has_tick']=True
        group['messages'].append(message)
    groups=[group for group in groups.values() if group['has_tick']]
    rendered=[]
    for index,group in enumerate(groups,1):
        descriptions=''.join('<li>{}</li>'.format(_e(s))
                             for s in group['messages'])
        searchable=' '.join(group['messages']).lower()
        rendered.append(
            '<details class="battle" data-owner="{}" data-death="0" '
            'data-search="{}"><summary><span class="round">R{} · BURDA #{}</span>'
            '<b>Obrażenia obszarowe obu plansz</b></summary>'
            '<div class="body"><ol>{}</ol></div></details>'.format(
                _e(group['active']),_e(searchable),_e(group['round']),
                index,descriptions))
    return groups,''.join(rendered)


def render_combat_html(payload):
    """Render a searchable, standalone local HTML with no external dependencies."""
    combat = payload.get("combat_analysis") or {}
    cached_attacks = combat.get("attacks")
    # Embedded battle summaries are derived presentation, not the signed
    # source of truth. Rebuild from recorded command deltas when available:
    # pre-0.9.59 summaries did not include General A002 combat bonuses.
    # Preserve original participant names where they are available.
    if isinstance(payload.get("initial_state"), dict) and isinstance(payload.get("actions"), list):
        names = {}
        for item in cached_attacks or ():
            for role in ("attacker", "defender"):
                participant = item.get(role) or {}
                if participant.get("uid") and participant.get("name"):
                    names[participant["uid"]] = participant["name"]
        attacks = build_combat_analysis(payload, names)
    else:
        attacks = cached_attacks if cached_attacks is not None else []
    total = len(attacks)
    resolved_choices = sum(len(item["actions"]) > 1 for item in attacks)
    death_attacks = sum(_participant_died(item["defender"]) for item in attacks)
    cards = "\n".join(_battle(item) for item in attacks)
    brawls,brawl_cards=_brawl_records(payload)
    document = r"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AuctionHammer — Księga Starć</title>
<style>
:root{color-scheme:dark;--gold:#d9b16e;--cream:#f2e4cc;--muted:#bdad95;--wood:#372618}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#684524 0,transparent 50%),#241a12;color:var(--cream);font:15px/1.5 Segoe UI,Arial,sans-serif}
main{max-width:1180px;margin:auto;padding:25px 23px 85px}header{text-align:center;padding:27px 0 35px;border-bottom:1px solid #8e6e46}
h1{font:46px Georgia,serif;color:var(--gold);margin:4px 0}h2{font:23px Georgia,serif;color:var(--gold)}h3{color:var(--gold)}h3 small{font-size:12px;color:var(--muted)}
.note,.quiet{color:var(--muted)}.counts{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}.count{flex:1;min-width:125px;border:1px solid #9d7849;background:var(--wood);padding:14px;border-radius:9px;text-align:center}.count strong{display:block;color:var(--gold);font-size:27px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}.toolbar>*{padding:11px 13px;border-radius:8px;background:#39291b;border:1px solid #907046;color:var(--cream);font:inherit}.toolbar input{flex:1;min-width:210px}
.battle{border:1px solid #8a6941;background:#352619;border-radius:10px;margin:9px 0;overflow:hidden}.battle[open]{border-color:#d1a664}
.battle>summary{padding:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;cursor:pointer}
.round{color:var(--gold);font-weight:bold;min-width:113px}.battle>summary>b{flex:1;min-width:200px}.tag{font-size:12px;color:var(--muted);border:1px solid #786248;border-radius:12px;padding:3px 8px}.dead{color:#efac9a}.body{padding:4px 16px 20px}
.participant{border-top:1px solid #7c5a35}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:12px}.comparison>div{background:#291f16;border:1px solid #665038;padding:14px;border-radius:8px}.comparison h4{font-size:11px;letter-spacing:.12em;color:var(--gold);margin:0 0 13px}
.metrics{display:flex;gap:7px;flex-wrap:wrap}.metric,.status{border:1px solid #735b40;border-radius:7px;padding:4px 8px;display:inline-block;margin:2px 1px}.metric b{color:var(--gold)}
ol li{margin:6px 0}li details summary{cursor:pointer;color:#e8ce9b}pre{white-space:pre-wrap;overflow-wrap:anywhere;color:#c8dcc8;font-size:12px}.micro{display:grid;grid-template-columns:1fr 1fr;gap:12px}.micro>div{background:#271c14;padding:8px;border-radius:6px}.micro b{color:var(--gold)}
@media(max-width:680px){.comparison,.micro{grid-template-columns:1fr}h1{font-size:31px}}
</style></head><body><main><header><h1>AuctionHammer</h1><h2>Księga Starć</h2>
<div class="note">Seed: __SEED__ · Build: __BUILD__ · analiza zakończonego meczu</div></header>
<div class="counts"><div class="count"><strong>__COUNT__</strong>ataków</div>
<div class="count"><strong>__CHOICES__</strong>ataków z wyborem zdolności</div>
<div class="count"><strong>__DEATHS__</strong>ataków ze zgonem obrońcy</div>
<div class="count"><strong>__BRAWLS__</strong>ticków Karczemnej Burdy</div></div>
<p class="note">PRZED oznacza stan przed komendą attack, PO oznacza stan po pełnym rozstrzygnięciu, także po późniejszym choose. Brak jednostki nie jest zerowym HP. Każda mikrooperacja zawiera rzeczywiste dane silnika przed/po; rozróżniamy żądane obrażenia i wynik w punktach życia. Raport nie symuluje walk. Premie Generała pochodzą ze stanu zapisanych powiązań i nie zmieniają odnotowanych statystyk ATK.</p>
<div class="toolbar"><input id="search" placeholder="Szukaj kart, ID lub zdarzeń..." type="search">
<select id="owner"><option value="all">Wszyscy atakujący</option><option value="0">Gracz</option>
<option value="1">Komputer</option><option value="death">Zgon</option></select>
<button id="expand">Rozwiń</button><button id="close">Zwiń</button></div><p id="visible" class="note"></p>
<h2>Karczemna Burda — zapisane obrażenia obu plansz</h2>
<p class="note">Wpisy pochodzą z podpisanego dziennika; wartości PŻ, Tarcza i pancerz są rozliczane przez silnik.</p>
<section id="brawls">__BRAWL_CARDS__</section>
<h2>Ataki jednostek</h2><section id="battles">__CARDS__</section></main><script>
(()=>{const cards=[...document.querySelectorAll('.battle')],q=document.getElementById('search'),
o=document.getElementById('owner');function update(){let n=0;for(const x of cards){
const ok=x.dataset.search.includes(q.value.toLocaleLowerCase('pl').trim())&&
(o.value==='all'||(o.value==='death'?x.dataset.death==='1':x.dataset.owner===o.value));
x.hidden=!ok;if(ok)n++;}document.getElementById('visible').textContent='Widoczne wpisy: '+n+' / '+cards.length;}
q.addEventListener('input',update);o.addEventListener('change',update);
document.getElementById('expand').onclick=()=>cards.filter(x=>!x.hidden).forEach(x=>x.open=true);
document.getElementById('close').onclick=()=>cards.forEach(x=>x.open=false);update();})();
</script></body></html>"""
    build = payload.get("environment", {}).get("build", {}).get("commit") or "nieznany"
    return (document.replace("__SEED__", _e(payload.get("seed", "—")))
            .replace("__BUILD__", _e(str(build)[:8]))
            .replace("__COUNT__", str(total))
            .replace("__CHOICES__", str(resolved_choices))
            .replace("__DEATHS__", str(death_attacks))
            .replace("__BRAWLS__", str(len(brawls)))
            .replace("__BRAWL_CARDS__", brawl_cards)
            .replace("__CARDS__", cards))


def main():
    parser = argparse.ArgumentParser(description="Offline viewer for signed AuctionHammer JSON/GZ audits")
    parser.add_argument("audit", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    from .audit import read_report
    payload = read_report(args.audit)
    output = args.output or args.audit.with_name(FILENAME)
    output.write_text(render_combat_html(payload), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
