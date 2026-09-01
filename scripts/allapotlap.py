#!/usr/bin/env python3
"""Élő állapotlap — egyetlen, olvasható oldal arról, hol tart a projekt MOST.

A `docs/specs/` 68 lapja fejlesztőknek szól. A tulajdonosnak nincs belőle
olvasható összképe, és a korábbi próbálkozás — kézzel írt listás jegyek —
elrohadt: a 2026-08-26-i mérés szerint a nyitott jegyek fele a nyitása óta
érintetlen.

Ez a szkript ezért **nem leírja** az állapotot, hanem **méri**:

* menü-lefedettség  → `scripts/menu_lefedettseg.py` (`merd`, `kovetkezo_ot`)
* jegyek, rothadás  → `scripts/kutatas_elszamolas.py` (`_gh_issues`, `_osszesit`)
* spec-lapok        → a `docs/specs/` fájljai

Kimenete egy önhordó HTML, amit artifactként publikálunk. Mivel minden
futáskor újraszámol, a lap nem tud elavulni — legfeljebb régi, és azt a
fejlécében ki is írja.

Használat:

    python3 scripts/allapotlap.py                 # docs/allapotlap.html
    python3 scripts/allapotlap.py --ki /tmp/a.html
    python3 scripts/allapotlap.py --url           # csak az artifact URL-je

Csak OLVAS (fájlok + `gh issue list`), ezért korlátlanul ismételhető.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from kutatas_elszamolas import (  # noqa: E402
    _gh_issues,
    _osszesit,
    _spec_nyitott_kerdesek,
)
from menu_lefedettseg import kovetkezo_ot, merd  # noqa: E402
from ui_lefedettseg_lap import olvas as _ui_lefedettseg  # noqa: E402

#: A publikált artifact címe. Egy MÁSIK munkamenetből frissítve EZT kell
#: átadni az `Artifact` hívás `url` mezőjében — enélkül új, különálló lap
#: jön létre, és a régi link elavul. Ha valaha új lapot nyitunk, ITT kell
#: átírni, hogy a következő session is a jót találja.
ARTIFACT_URL = "https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e"

SPEC_DIR = REPO / "docs" / "specs"


# --- mérés -----------------------------------------------------------------


def _spec_statisztika() -> dict:
    """A `docs/specs/` lapjainak száma és összterjedelme."""
    lapok = sorted(SPEC_DIR.glob("*.md"))
    sorok = sum(
        len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        for p in lapok
    )
    return {"lapok": len(lapok), "sorok": sorok}


def _erintetlen(jegyek: list[dict]) -> list[dict]:
    """A nyitás óta hozzá nem nyúlt jegyek — ez a rothadás mérőszáma.

    Ugyanaz a feltétel, mint a `kutatas_elszamolas.py` azonos szakaszában:
    a `createdAt` és az `updatedAt` napra egyezik, és legfeljebb egy
    komment van rajta.
    """
    return [
        i for i in jegyek
        if i.get("created") and i["created"] == i.get("updated")
        and i.get("comments", 0) <= 1
    ]


def _kiadasok(darab: int = 6) -> list[dict]:
    """A legutóbbi kiadások a `gh`-ból: verzió + időpont.

    A lap fő célja, hogy a tulajdonos EGY helyen lássa, mi történt — enélkül
    a GitHubot kell böngésznie (#1695)."""
    try:
        nyers = subprocess.run(
            ["gh", "release", "list", "--limit", str(darab),
             "--json", "tagName,publishedAt"],
            cwd=REPO, capture_output=True, text=True, timeout=60, check=True,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError) as hiba:
        print(f"⚠️  A kiadások nem kérdezhetők le ({hiba.__class__.__name__}).",
              file=sys.stderr)
        return []
    return [
        {"verzio": k["tagName"], "mikor": (k.get("publishedAt") or "")[:16].replace("T", " ")}
        for k in json.loads(nyers)
    ]


def _frissen_lezart(orak: int = 24, darab: int = 20) -> list[dict]:
    """Az elmúlt `orak` órában lezárt jegyek — EZ mutatja, mi történt."""
    hatar = (datetime.now(timezone.utc) - timedelta(hours=orak)).isoformat()
    try:
        nyers = subprocess.run(
            ["gh", "issue", "list", "--state", "closed", "--limit", "120",
             "--json", "number,title,closedAt,labels"],
            cwd=REPO, capture_output=True, text=True, timeout=90, check=True,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError) as hiba:
        print(f"⚠️  A lezárt jegyek nem kérdezhetők le "
              f"({hiba.__class__.__name__}).", file=sys.stderr)
        return []
    frissek = [
        {"number": j["number"], "title": j["title"],
         "labels": {c["name"] for c in j["labels"]},
         "closed": j.get("closedAt", "")}
        for j in json.loads(nyers)
        if (j.get("closedAt") or "") >= hatar
    ]
    frissek.sort(key=lambda j: j["closed"], reverse=True)
    return frissek[:darab]


def gyujts() -> dict:
    """Minden mért adat egyetlen szótárban. Hálózati hiba esetén a
    jegy-szakasz üres marad — a lap ilyenkor is elkészül, és jelzi."""
    menu = merd()
    jegyek = _gh_issues()
    ossz = _osszesit(jegyek)
    erintetlen = _erintetlen(jegyek)
    return {
        "menu": menu,
        "kovetkezo": kovetkezo_ot(menu),
        # #1778: a menü-axis 2026-08-31-én kimerült (138/138), a következő
        # az UI-lefedettség. A COMMITOLT mérést olvassuk — az előállító a
        # privát repóban él (ld. `ui_lefedettseg_lap` docstringje).
        "ui": _ui_lefedettseg(),
        "jegyek": jegyek,
        "ossz": ossz,
        "erintetlen": erintetlen,
        "spec": _spec_statisztika(),
        "spec_kerdesek": _spec_nyitott_kerdesek(),
        "kiadasok": _kiadasok(),
        "frissen_lezart": _frissen_lezart(),
        "ideje": datetime.now(timezone.utc).astimezone(),
    }


# --- megjelenítés ----------------------------------------------------------


def _e(szoveg: object) -> str:
    """HTML-escape — minden jegycím és fájlnév ezen megy át."""
    return html.escape(str(szoveg), quote=True)


def _allapot(arany: int) -> str:
    """Egy százalékos aránynak megfelelő súlyossági osztály.

    A küszöbök szándékosan szigorúak: a lap dolga, hogy a romlás
    LÁTSZÓDJON, nem az, hogy megnyugtasson.
    """
    if arany >= 75:
        return "ok"
    if arany >= 45:
        return "warn"
    return "crit"


def _szamsor(a: dict) -> str:
    menu, ossz = a["menu"], a["ossz"]
    feltart = len(menu["viselkedes"])
    merheto = feltart + len(menu["erdemi"]) + len(menu["csak_nev"]) + len(menu["sehol"])
    arany = round(100 * feltart / merheto) if merheto else 0

    nyitott = ossz.get("osszes_nyitott", 0)
    rothado = len(a["erintetlen"])
    rothadas = round(100 * rothado / nyitott) if nyitott else 0

    tetelek = [
        (f"{arany}%", f"a menüparancsok viselkedése feltárva ({feltart}/{merheto})",
         _allapot(arany)),
        (str(nyitott), "nyitott jegy összesen", "neutral"),
        (f"{rothadas}%", f"a jegyek nyitásuk óta érintetlenek ({rothado})",
         _allapot(100 - rothadas)),
        (str(len(ossz.get("blokkolt", []))), "blokkolt jegy", "neutral"),
        (str(len(ossz.get("felhasznalora_var", []))),
         "rád vár — nélküled nem megy tovább",
         "warn" if ossz.get("felhasznalora_var") else "ok"),
        (str(a["spec"]["lapok"]),
         f"specifikációs lap · {a['spec']['sorok']:,} sor".replace(",", " "),
         "neutral"),
    ]
    cellak = "\n".join(
        f'      <div class="stat {oszt}"><b>{_e(ertek)}</b><span>{_e(cimke)}</span></div>'
        for ertek, cimke, oszt in tetelek
    )
    return f'    <div class="stats">\n{cellak}\n    </div>'


def _jegylista(cim: str, leiras: str, jegyek: list[dict], oszt: str) -> str:
    if not jegyek:
        return (f'      <div class="group"><h3>{_e(cim)}</h3>'
                f'<p class="empty">Egy sincs.</p></div>')
    sorok = "\n".join(
        f'          <li><span class="num">#{i["number"]}</span>'
        f'<span class="txt">{_e(i["title"])}</span></li>'
        for i in jegyek
    )
    return (f'      <div class="group {oszt}">\n'
            f'        <h3>{_e(cim)}</h3>\n'
            f'        <p class="note">{_e(leiras)}</p>\n'
            f'        <ul class="tickets">\n{sorok}\n        </ul>\n'
            f'      </div>')


def _mi_tortent_szakasz(a: dict) -> str:
    """„Mi történt" — kiadások és a friss lezárások EGY helyen.

    A tulajdonos kérése (2026-08-28): *„Az artifact egyik fő célja, hogy az
    ember lássam, mi történt az éjszaka. Kiment pár release, és semmit sem
    látok ebből olvasható módon, a githubot kell böngésszem."* A lap eddig
    csak az ÁLLAPOTOT mutatta, a TÖRTÉNÉST nem."""
    kiadasok = a.get("kiadasok") or []
    lezart = a.get("frissen_lezart") or []
    if not kiadasok and not lezart:
        return ""

    kiadas_sorok = "".join(
        f'          <li><span class="num">{_e(k["verzio"])}</span>'
        f'<span class="txt">{_e(k["mikor"])}</span></li>\n'
        for k in kiadasok
    ) or '          <li><span class="txt">Nincs adat.</span></li>\n'

    lezart_sorok = "".join(
        f'          <li><span class="num">#{j["number"]}</span>'
        f'<span class="txt">{_e(j["title"])}</span></li>\n'
        for j in lezart
    ) or '          <li><span class="txt">Az elmúlt napban egy sem.</span></li>\n'

    return f"""
  <section>
    <div class="section-head">
      <h2>Mi történt</h2>
      <p>A legutóbbi kiadások és az elmúlt 24 óra lezárt jegyei — hogy ne a
         GitHubot kelljen böngészni. A lezárás azt jelenti: beolvadt és
         kiment.</p>
    </div>
    <div class="groups">
      <div class="group ok">
        <h3>Kiadások</h3>
        <p class="note">A legfrissebb elöl.</p>
        <ul class="tickets">
{kiadas_sorok}        </ul>
      </div>
      <div class="group">
        <h3>Lezárt jegyek (24 óra)</h3>
        <p class="note">Összesen {len(lezart)} tétel.</p>
        <ul class="tickets">
{lezart_sorok}        </ul>
      </div>
    </div>
  </section>
"""


def _kovetkezo_bevezeto(a: dict) -> str:
    """A szakasz bevezetője — a KÉT axis másképp rendez, tehát mást is ígér.

    #1778: a menüparancs-sor ábécésorrend volt („bárki futtatja, ugyanazt
    kapja"). Az UI-sor ehelyett a fehér foltok MÉRETE szerint rendez —
    ugyanúgy nem válogatás, de más ígéret, ezért a szöveg is más."""
    if a["kovetkezo"]:
        return ('      <p>Determinisztikus sorrend a lefedettségi mérésből — '
                'nem válogatás. Ha egy kutatói kör indul, ezekkel kezd.</p>')

    meres = a.get("ui")
    if meres is None:
        return ('      <p>A menüparancsok feltárása teljes. A következő '
                'terület mérése még nincs a fában.</p>')

    # ⚠️ A „hiányzik" szám JELÖLT, nem ítélet. Két egymást követő kör
    # talált téves riasztást (tíz elem az `acquirepanel`-en, három a
    # `quicktagconfig`-on), sőt egy egész panel is tévesen látszott
    # hiánynak. A szám a felülbírálásokkal csökken — az CSÖKKENÉS MUNKA,
    # nem a mérce lazulása, ezért a felülbírálások számát is kiírjuk.
    kor = ""
    if meres.ideje is not None:
        # a magyar dátum-toldalék pont NÉLKÜL kapcsolódik: „08. 31-i”
        kor = f' A mérés {meres.ideje.strftime("%Y. %m. %d")}-i'
        if meres.elavult(datetime.now().date()):
            kor += (' — ez már régi, a lap újragenerálása előtt érdemes '
                    'újramérni')
        kor += "."
    return (
        '      <p>A menüparancsok feltárása <strong>teljes</strong> '
        '(138/138), ezért a sor mostantól a felület fehér foltjait '
        'mutatja: <strong>a legnagyobbakat, méret szerint</strong> — nem '
        'válogatás, két futás ugyanazt adja.</p>\n'
        f'      <p class="note">A {meres.hianyzik} „hiányzó" és a '
        f'{meres.bizonytalan} bizonytalan elem <strong>feltárandó '
        f'jelölt, nem megállapított hiány</strong>: eddig '
        f'{meres.felulbiralasok} elemről derült ki kézi ellenőrzéssel, '
        f'hogy valójában megvan nálunk, csak máshogy. A szám ezekkel '
        f'csökken.{kor}</p>'
    )


def _kovetkezo_szakasz(a: dict) -> str:
    """A következő kutatói körök — menüparancsok, majd UI-panelek.

    #1778: amíg volt feltáratlan menüparancs, azokat soroltuk. A menü-axis
    2026-08-31-én kimerült (138/138), ezért a lap az UI-lefedettségre vált.
    A két axis NEM keveredik: ha még van menüparancs, az megy előbb."""
    if a["kovetkezo"]:
        sorok = "\n".join(
            f'          <li><code>{_e(p)}</code></li>' for p in a["kovetkezo"]
        )
        return f'        <ol class="next">\n{sorok}\n        </ol>'

    meres = a.get("ui")
    if meres is None or not meres.kovetkezo_ot:
        return ('      <p class="empty">Nincs több feltáratlan menüparancs, '
                'és UI-lefedettségi mérés sincs a fában.</p>')

    sorok = "\n".join(
        f'          <li><code>{_e(p.nev)}</code>'
        f'<span class="txt">{_e(p.leiras)}</span>'
        f'<span class="db">{p.hiany}</span></li>'
        for p in meres.kovetkezo_ot
    )
    kihagyott = "".join(
        f'<li><code>{_e(nev)}</code><span class="txt">{_e(indok)}</span></li>'
        for nev, indok in meres.kihagyott
    )
    kihagyott_blokk = (
        f'      <p class="note">Hatókörön kívül — ezekre nem küldünk kört, '
        f'de nem is felejtettük el őket:</p>\n'
        f'      <ul class="skipped">{kihagyott}</ul>'
        if kihagyott else ""
    )
    return f'        <ol class="next">\n{sorok}\n        </ol>\n{kihagyott_blokk}'


def _spec_szakasz(a: dict) -> str:
    if not a["spec_kerdesek"]:
        return '      <p class="empty">Egyetlen lapon sincs nyitott kérdés.</p>'
    sorok = "\n".join(
        f'          <li><span class="lap">{_e(lap)}</span>'
        f'<span class="txt">{_e(allapot)}</span></li>'
        for lap, allapot in a["spec_kerdesek"]
    )
    return f'        <ul class="specs">\n{sorok}\n        </ul>'


def epits(a: dict) -> str:
    """A teljes, önhordó HTML."""
    ideje = a["ideje"].strftime("%Y. %m. %d. %H:%M")
    ossz = a["ossz"]

    # Az `_osszesit` teljes jegy-szótárakat ad vissza (nem csak számokat),
    # ezért közvetlenül átadhatók a listázónak.
    var_rank = ossz.get("felhasznalora_var") or []
    blokkolt_mind = ossz.get("blokkolt") or []
    binaris = ossz.get("binaris_kutathato") or []
    # A `binaris_kutathato` a `blokkolt` RÉSZHALMAZA. Ha mindkettőt kiírjuk,
    # ugyanaz a jegy kétszer jelenik meg a szakaszban (#1664: a #1276 és a
    # #1153 így duplázódott). Ezért particionálunk: egy jegy egy csoportba.
    _binaris_szamok = {j["number"] for j in binaris}
    blokkolt = [j for j in blokkolt_mind if j["number"] not in _binaris_szamok]
    erintetlen_regi = sorted(a["erintetlen"], key=lambda x: x["created"])[:10]

    hiba = ("" if a["jegyek"] else
            '    <p class="offline">A jegyek nem voltak lekérdezhetők ehhez a '
            'futáshoz — a jegy-szakaszok üresek. A menü- és spec-adatok '
            'érvényesek.</p>')

    return f"""<title>PicasaPy — élő állapotlap</title>
{_STILUS}
<div class="wrap">

  <header class="masthead">
    <p class="eyebrow">PicasaPy · mért állapot · frissítve {_e(ideje)}</p>
    <h1>Hol tart a projekt most</h1>
    <p class="standfirst">
      Ezen a lapon egyetlen mondat sincs kézzel írva. Minden szám mérésből jön:
      a menüparancsok feltártsága a Picasa saját parancslistájából, a jegyek a
      GitHubról, a rothadás-mutató abból, hány jegyhez nem nyúlt hozzá senki a
      nyitása óta. Ezért a lap nem tud elavulni — legfeljebb régi lehet, és a
      dátumát fent kiírja.
    </p>
  </header>
{hiba}
{_szamsor(a)}
{_mi_tortent_szakasz(a)}

  <section>
    <div class="section-head">
      <h2>Mi áll, és kin múlik</h2>
      <p>Csak az első csoport az, ami <em>nélküled</em> nem megy tovább — ott a
         jegy leírja, pontosan mi kell. A másik kettő nem rád vár; azért van
         itt, hogy lásd, mi áll és min múlik. Egy jegy csak egy csoportban
         szerepel.</p>
    </div>
    <div class="groups">
{_jegylista("Rád vár", "Legtöbbször egy export vagy egy képernyőkép a windowsos Picasából.", var_rank, "warn")}
{_jegylista("Külső akadályon áll", "Nem felejtés — valami rajtunk kívül álló hiányzik hozzá.", blokkolt, "crit")}
{_jegylista("Bináris kutatás oldja fel", "Ehhez nem a te gépedre van szükség, hanem az eredeti Picasa visszafejtésére — ezen tudunk dolgozni magunktól.", binaris, "ok")}
    </div>
  </section>

  <section>
    <div class="section-head">
      <h2>A következő öt kutatnivaló</h2>
{_kovetkezo_bevezeto(a)}
    </div>
{_kovetkezo_szakasz(a)}
  </section>

  <section>
    <div class="section-head">
      <h2>A rothadás</h2>
      <p>Jegyek, amelyekhez a nyitásuk óta senki nem nyúlt. Ez a szakasz azért
         van itt, hogy ez a szám <em>látszódjon</em> — enélkül csendben nő.</p>
    </div>
    <div class="groups">
{_jegylista("A tíz legrégebbi érintetlen", f"Összesen {len(a['erintetlen'])} ilyen jegy van.", erintetlen_regi, "warn")}
    </div>
  </section>

  <section>
    <div class="section-head">
      <h2>Specifikációs lapok nyitott kérdéssel</h2>
      <p>A <code>docs/specs/</code> kézzel karbantartott kérdés-listájából.</p>
    </div>
{_spec_szakasz(a)}
  </section>

  <footer class="colophon">
    <p>
      Ezt a lapot a <code>scripts/allapotlap.py</code> állítja elő. Frissítéshez
      futtasd a szkriptet, majd publikáld ugyanerre a címre — a link nem változik,
      és a korábbi változatok visszalapozhatók.
    </p>
    <p>
      A „feltárva” azt jelenti, hogy a parancs viselkedése bizonyítékkal
      dokumentálva van, nem azt, hogy meg is van valósítva. A hatókörön kívülre
      tett parancsokat (online szolgáltatások, lemezírás) a mérés kihagyja.
    </p>
  </footer>

</div>
"""


_STILUS = """<style>
  :root {
    --ground:#E9EDEE; --surface:#F7F9F9; --rule:#C3CDD0; --rule-soft:#D8E0E1;
    --ink:#16232A; --ink-soft:#4E6068; --ink-faint:#7C8E95;
    --accent:#1F6F63; --accent-wash:#DCE8E5;
    --warn:#8A5B14; --warn-wash:#EFE6D2;
    --crit:#9C3B2B; --crit-wash:#F0DFDA;
    --font-display:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
    --font-body:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
    --font-mono:ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground:#101A1E; --surface:#17242A; --rule:#2C3F47; --rule-soft:#223138;
      --ink:#DDE7E9; --ink-soft:#9DB1B8; --ink-faint:#6E858D;
      --accent:#56B9A7; --accent-wash:#17332F;
      --warn:#D6A755; --warn-wash:#2E2617;
      --crit:#E58067; --crit-wash:#35201B;
    }
  }
  :root[data-theme="dark"] {
    --ground:#101A1E; --surface:#17242A; --rule:#2C3F47; --rule-soft:#223138;
    --ink:#DDE7E9; --ink-soft:#9DB1B8; --ink-faint:#6E858D;
    --accent:#56B9A7; --accent-wash:#17332F;
    --warn:#D6A755; --warn-wash:#2E2617;
    --crit:#E58067; --crit-wash:#35201B;
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--ground); color:var(--ink);
         font-family:var(--font-body); font-size:16px; line-height:1.6;
         -webkit-font-smoothing:antialiased; }
  .wrap { max-width:62rem; margin:0 auto; padding:3.5rem 1.5rem 6rem;
          display:flex; flex-direction:column; gap:3.5rem; }
  .masthead { display:flex; flex-direction:column; gap:1.1rem; }
  .eyebrow { font-family:var(--font-mono); font-size:0.7rem; letter-spacing:0.14em;
             text-transform:uppercase; color:var(--ink-faint); margin:0; }
  h1 { font-family:var(--font-display); font-weight:600;
       font-size:clamp(2rem,5vw,2.9rem); line-height:1.12; letter-spacing:-0.015em;
       text-wrap:balance; margin:0; }
  .standfirst { font-size:1.05rem; color:var(--ink-soft); max-width:46rem; margin:0; }
  .offline { margin:0; padding:0.85rem 1rem; background:var(--warn-wash);
             color:var(--warn); border-left:2px solid var(--warn); font-size:0.9rem; }

  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));
           gap:1px; background:var(--rule); border-block:1px solid var(--rule); }
  .stat { background:var(--surface); padding:1.05rem 1.15rem 1.15rem;
          display:flex; flex-direction:column; gap:0.2rem;
          border-top:3px solid transparent; }
  .stat b { font-family:var(--font-mono); font-size:1.7rem; font-weight:500;
            font-variant-numeric:tabular-nums; letter-spacing:-0.02em; line-height:1.1; }
  .stat span { font-size:0.78rem; color:var(--ink-soft); line-height:1.4; }
  .stat.ok      { border-top-color:var(--accent); } .stat.ok b      { color:var(--accent); }
  .stat.warn    { border-top-color:var(--warn);   } .stat.warn b    { color:var(--warn); }
  .stat.crit    { border-top-color:var(--crit);   } .stat.crit b    { color:var(--crit); }
  .stat.neutral { border-top-color:var(--rule);   } .stat.neutral b { color:var(--ink); }

  section { display:flex; flex-direction:column; gap:1.5rem; }
  .section-head { display:flex; flex-direction:column; gap:0.35rem; }
  h2 { font-family:var(--font-display); font-size:1.5rem; font-weight:600;
       letter-spacing:-0.01em; margin:0; text-wrap:balance; }
  .section-head p { margin:0; color:var(--ink-soft); max-width:44rem; font-size:0.93rem; }
  h3 { font-family:var(--font-display); font-size:1.05rem; font-weight:600; margin:0; }

  .groups { display:grid; grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));
            gap:1.5rem; }
  .group { display:flex; flex-direction:column; gap:0.5rem; padding-left:1rem;
           border-left:2px solid var(--rule); }
  .group.warn { border-left-color:var(--warn); }
  .group.crit { border-left-color:var(--crit); }
  .group.ok { border-left-color:var(--accent); }
  .note { margin:0; font-size:0.85rem; color:var(--ink-faint); }
  .empty { margin:0; font-size:0.9rem; color:var(--ink-faint); font-style:italic; }

  ul.tickets, ol.next, ul.specs { list-style:none; margin:0; padding:0;
                                  display:flex; flex-direction:column; }
  ul.tickets li, ul.specs li { display:grid; grid-template-columns:max-content 1fr;
                gap:0 0.75rem; padding:0.5rem 0; border-top:1px solid var(--rule-soft);
                font-size:0.9rem; align-items:baseline; }
  .num { font-family:var(--font-mono); font-size:0.82rem; font-weight:600;
         color:var(--accent); font-variant-numeric:tabular-nums; }
  .lap { font-family:var(--font-mono); font-size:0.75rem; color:var(--ink-faint); }
  .txt { color:var(--ink-soft); min-width:0; overflow-wrap:anywhere; }

  ol.next { counter-reset:n; gap:0; }
  ol.next li { counter-increment:n; padding:0.6rem 0; font-size:0.9rem;
               border-top:1px solid var(--rule-soft); display:flex; gap:0.85rem;
               align-items:baseline; }
  ol.next li::before { content:counter(n); font-family:var(--font-mono);
               font-size:0.75rem; color:var(--ink-faint); min-width:1.1rem; }
  ol.next li:last-child, ul.tickets li:last-child, ul.specs li:last-child {
               border-bottom:1px solid var(--rule-soft); }
  /* #1778: az UI-axis sorai a hiány MÉRETÉT is mutatják — a szám adja a
     rangsor értelmét, enélkül a sorrend önkényesnek látszana. */
  ol.next li .db { margin-left:auto; font-family:var(--font-mono);
               font-size:0.78rem; color:var(--ink-faint); flex:none; }
  ul.skipped { list-style:none; margin:0.6rem 0 0; padding:0;
               font-size:0.83rem; color:var(--ink-faint); }
  ul.skipped li { display:flex; gap:0.6rem; padding:0.22rem 0;
               align-items:baseline; }

  code { font-family:var(--font-mono); font-size:0.85em; background:var(--accent-wash);
         color:var(--ink); padding:0.1em 0.32em; border-radius:2px; }

  .colophon { border-top:1px solid var(--rule); padding-top:1.4rem; font-size:0.83rem;
              color:var(--ink-faint); display:flex; flex-direction:column; gap:0.4rem; }
  .colophon p { margin:0; max-width:46rem; }

  @media (max-width:34rem) {
    ul.tickets li, ul.specs li { grid-template-columns:1fr; gap:0.1rem; }
  }
  @media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
</style>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ki", type=Path, default=REPO / "docs" / "allapotlap.html",
                    help="a generált HTML útvonala")
    ap.add_argument("--url", action="store_true",
                    help="csak a publikált artifact címét írja ki")
    args = ap.parse_args()

    if args.url:
        print(ARTIFACT_URL)
        return 0

    try:
        adat = gyujts()
    except Exception as exc:  # a lap sosem lehet félkész
        print(f"A mérés nem futott le: {exc.__class__.__name__}: {exc}",
              file=sys.stderr)
        return 1

    args.ki.parent.mkdir(parents=True, exist_ok=True)
    args.ki.write_text(epits(adat), encoding="utf-8")

    print(f"✅ {args.ki}")
    print(
        "   ⚠️ EZT A FÁJLT ÖNMAGÁBAN NE PUBLIKÁLD — a tulajdonos EGY lapot kap,\n"
        "      három szakasszal. Az összerakó futtatja ezt a szkriptet is:\n"
        "         cd ~/picasapy-agent && python3 eszkozok/egy_lap.py\n"
        f"      A publikálás címe:  {ARTIFACT_URL}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
