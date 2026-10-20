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
    return '<div class="metrics">{}</div><p><b>Statusy:</b> {}</p>'.format(
        details, _statuses(state.get("effects", [])))


def _participant(role, participant):
    return ('<section class="participant"><h3>{} · {} <small>{}</small></h3>'
            '<div class="comparison"><div><h4>PRZED</h4>{}</div>'
            '<div><h4>PO</h4>{}</div></div></section>').format(
        _e(role), _e(participant["name"]), _e(participant["uid"]),
        _stats(participant["before"]), _stats(participant["after"]))


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
    death = (attacker["after"] is None or defender["after"] is None)
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


def render_combat_html(payload):
    """Render a searchable, standalone local HTML with no external dependencies."""
    combat = payload.get("combat_analysis", {})
    attacks = combat.get("attacks")
    if attacks is None:
        attacks = build_combat_analysis(payload)
    total = len(attacks)
    resolved_choices = sum(len(item["actions"]) > 1 for item in attacks)
    death_attacks = sum(item["defender"]["after"] is None for item in attacks)
    cards = "\n".join(_battle(item) for item in attacks)
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
<div class="count"><strong>__DEATHS__</strong>ataków ze zgonem obrońcy</div></div>
<p class="note">PRZED oznacza stan przed komendą attack, PO oznacza stan po pełnym rozstrzygnięciu, także po późniejszym choose. Brak jednostki nie jest zerowym HP. Każda mikrooperacja zawiera rzeczywiste dane silnika przed/po; rozróżniamy żądane obrażenia i wynik w punktach życia. Raport nie symuluje walk.</p>
<div class="toolbar"><input id="search" placeholder="Szukaj kart, ID lub zdarzeń..." type="search">
<select id="owner"><option value="all">Wszyscy atakujący</option><option value="0">Gracz</option>
<option value="1">Komputer</option><option value="death">Zgon</option></select>
<button id="expand">Rozwiń</button><button id="close">Zwiń</button></div><p id="visible" class="note"></p>
<section id="battles">__CARDS__</section></main><script>
(()=>{const cards=[...document.querySelectorAll('.battle')],q=document.getElementById('search'),
o=document.getElementById('owner');function update(){let n=0;for(const x of cards){
const ok=x.dataset.search.includes(q.value.toLocaleLowerCase('pl').trim())&&
(o.value==='all'||(o.value==='death'?x.dataset.death==='1':x.dataset.owner===o.value));
x.hidden=!ok;if(ok)n++;}document.getElementById('visible').textContent='Widoczne walki: '+n+' / '+cards.length;}
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
