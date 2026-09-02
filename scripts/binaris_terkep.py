#!/usr/bin/env python3
"""Bináris visszafejtési térkép — MÉRT adatból, nem beégetve.

Párja az `allapotlap.py`-nak. Az a projekt állapotát méri, ez azt, hogy a
`Picasa3.exe` mekkora és mely részeit fejtettük vissza.

**Miért generált.** Az első változat kézzel írt HTML volt, beégetett
számokkal — a tulajdonos kérdezett rá (2026-08-27): *„Van már beépített
scripted, ami kényszeríti a bináris artifactok frissítését?"* Nem volt, és a
lap pontosan úgy avult volna el, mint a listás jegyek, amiket lecseréltünk.

**Mit mér, és mit nem:**

* **mért** — a függvények száma és mérete (bináris index), hány függvényre
  hivatkozik a `docs/specs/`, az osztálycsaládok aránya, és hogy melyik
  címsávot érintik a `next-up`/`P1` jegyek;
* **kézzel gondozott** — a sávok EMBERI címkéi (`SAV_CIMKEK`) és az idegen
  kód besorolása (`IDEGEN_SAVOK`). Ez szemantikus tudás, mérésből nem jön ki;
  ha egy sáv tartalma megváltozik, ITT kell átvezetni.

⚠️ A bináris index a PRIVÁT agent-repóban él. Ha nincs meg (friss klón, CI),
a szkript ezt megmondja és `3`-mal kilép — nem ír féllábú lapot.

Használat:

    python3 scripts/binaris_terkep.py
    python3 scripts/binaris_terkep.py --ki /tmp/terkep.html
    python3 scripts/binaris_terkep.py --url
"""

from __future__ import annotations

import argparse
import bisect
import html
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
#: A privát agent-repó lehetséges helyei. A `bootstrap_env.sh` és a CLAUDE.md
#: szerint felhős munkamenetben `/workspace/picasapy-agent`, helyi gépen
#: `~/picasapy-agent` — ezért MINDKETTŐT nézni kell. Amíg csak a home-ot
#: néztük, egy felhős kör hiába klónozta a repót: a lap csendben kimaradt, és
#: emiatt csúszott el a bináris térkép frissítése az állapotlapétól.
AGENT_HELYEK = (Path.home() / "picasapy-agent", Path("/workspace/picasapy-agent"))
INDEX_RESZUT = Path("referencia") / "binary-index" / "picasa3-index.sqlite"


def _index_utvonal() -> Path:
    """Az első létező bináris index; ha egyik sincs meg, az elsődleges hely."""
    for gyoker in AGENT_HELYEK:
        jelolt = gyoker / INDEX_RESZUT
        if jelolt.exists():
            return jelolt
    return AGENT_HELYEK[0] / INDEX_RESZUT


INDEX = _index_utvonal()
REPO_URL = "https://github.com/sanchomuzax/PicasaPy"

SPEC_DIR = REPO / "docs" / "specs"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from szakasz_eredet import eredet_sor, forras_ideje  # noqa: E402


#: A publikált artifact címe. MÁSIK munkamenetből frissítve EZT kell átadni az
#: `Artifact` hívás `url` mezőjében, különben új lap jön létre.
ARTIFACT_URL = "https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e"  # az ÖSSZEVONT lap (2026-09-01 óta)

SAVOK = 32

#: A címsávok EMBERI címkéi. Kézzel gondozott: a sávban található osztály- és
#: szövegnevekből származik, mérésből nem jön ki. Kulcs: a sáv kezdőcíme
#: kerekítve — a szkript a legközelebbi sávhoz rendeli.
SAV_CIMKEK: dict[int, str] = {
    0x00401000: "indulás, adatbázis-betöltés",
    0x00484340: "arcfelismerés",
    0x004C5CE0: "helyi webszerver, mappa-szkenner",
    0x00507680: "indexkép-katalógus",
    0x00549020: "menük, mappanézet",
    0x0058A9C0: "mentés, export, névjegyek",
    0x005CC360: "parancskezelő (235 ág)",
    0x0064F6A0: "emberek-panel, értesítősáv",
    0x00714380: "helyi menük, mappakezelés",
    0x007976C0: "párbeszédek",
    0x0081AA00: "képmegjelenítés",
    0x0085C3A0: "effektek magja",
    0x008DF6E0: "színkezelés, finomhangolás",
    0x00921080: "Google Fotók feltöltés",
    0x00962A20: "hálózat, HTTP",
    0x009A43C0: "képformátumok",
    0x009E5D60: "színkeresés",
    0x00A27700: "socket, rajzolás",
    0x00A690A0: "menüépítő rekordok",
    0x00AAAA40: "elrendezés-motor",
    0x00AEC3E0: "idegen könyvtárak",
    0x00B2DD80: "PNG, zlib",
    0x00B6F720: "TIFF-dekóder",
    0x00BB10C0: "JPEG, színprofilok",
    0x00BF2A60: "C-futtatókörnyezet",
}

#: Amit SOSEM kell visszafejtenünk: idegen könyvtár és futtatókörnyezet.
#: Nyílt megfelelőik nálunk már használatban vannak.
IDEGEN_SAVOK = {0x00AEC3E0, 0x00B2DD80, 0x00B6F720, 0x00BB10C0, 0x00BF2A60}

#: A kiemelt jegyek → melyik sávot indokolják. Kézzel gondozott, mert a
#: jegy szövegéből gépileg nem dönthető el, melyik címtartományt érinti.
#: A szkript ELLENŐRZI, hogy a jegy tényleg nyitott és kiemelt-e.
KIEMELT_SAVOK: dict[int, tuple[int, str]] = {
    0x00401000: (449, "indulás és adatbázis"),
    0x00484340: (26, "arcfelismerés, Emberek"),
    0x004C5CE0: (449, "beolvasás, karbantartás"),
    0x00507680: (449, "indexkép-katalógus"),
    0x0058A9C0: (444, "mentés-szemantika"),
    0x0064F6A0: (455, "Képtálca"),
    0x00714380: (457, "fájlműveletek"),
    0x0081AA00: (1657, "megjelenítési módok"),
    0x0085C3A0: (317, "EFFEKT-kalibráció"),
    0x008DF6E0: (539, "színhúzás, finomhangolás"),
    0x009E5D60: (317, "színkeresés"),
}


# --- mérés -----------------------------------------------------------------


def _spec_cimek() -> set[int]:
    """A `docs/specs/` összes `0x00xxxxxx` alakú címhivatkozása."""
    szoveg = "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in SPEC_DIR.glob("*.md")
    )
    return {int(m, 16) for m in re.findall(r"0x00[0-9a-fA-F]{6}", szoveg)}


def _kiemelt_jegyek() -> set[int]:
    """A `next-up` és `P1` címkéjű NYITOTT jegyek száma.

    Hálózati hiba esetén üres halmaz — a lap ilyenkor kiemelés nélkül készül
    el, és ezt a fejlécében jelzi.
    """
    try:
        nyers = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--limit", "300",
             "--json", "number,labels"],
            cwd=REPO, capture_output=True, text=True, timeout=90, check=True,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return set()
    ki = set()
    for jegy in json.loads(nyers):
        cimkek = {c["name"] for c in jegy["labels"]}
        if "next-up" in cimkek or "P1" in cimkek:
            ki.add(jegy["number"])
    return ki


def gyujts() -> dict:
    if not INDEX.exists():
        raise FileNotFoundError(
            "A bináris index nincs meg. Keresett helyek:\n  "
            + "\n  ".join(str(gy / INDEX_RESZUT) for gy in AGENT_HELYEK)
            + "\nEz a PRIVÁT agent-repóban él; klónozd a `picasapy-agent`-et."
        )
    con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
    try:
        fv = sorted(
            (int(c, 16), int(m))
            for c, m in con.execute("SELECT address, size FROM functions")
            if str(m).isdigit()
        )
        rtti = list(con.execute("SELECT name, kind FROM rtti"))
        elek = con.execute("SELECT COUNT(*) FROM xrefs").fetchone()[0]
    finally:
        con.close()

    cimek = _spec_cimek()
    kezdetek = [k for k, _ in fv]
    erintett: set[int] = set()
    for c in cimek:
        i = bisect.bisect_right(kezdetek, c) - 1
        if i >= 0 and fv[i][0] <= c < fv[i][0] + fv[i][1]:
            erintett.add(fv[i][0])

    # osztálycsaládok
    csalad, csalad_erintett = Counter(), Counter()
    for nev, kind in rtti:
        n = nev.split("::")[0]
        pre = ("Fen" if n.startswith("Fen") else
               "glimmer" if n.startswith("glimmer") else
               "yt" if n.startswith("yt") else
               "C" if n.startswith("C") else "egyéb")
        csalad[pre] += 1
        metodusok = [int(x, 16) for x in (kind or "").split(";") if x.startswith("0x")]
        if any(m in erintett for m in metodusok):
            csalad_erintett[pre] += 1

    # címsávok
    lo, hi = kezdetek[0], fv[-1][0] + fv[-1][1]
    szel = (hi - lo) // SAVOK
    savok = []
    for s in range(SAVOK):
        a, b = lo + s * szel, lo + (s + 1) * szel
        benne = [k for k in kezdetek if a <= k < b]
        e = sum(1 for k in benne if k in erintett)
        savok.append({"cim": a, "ossz": len(benne), "fel": e,
                      "arany": round(100 * e / len(benne)) if benne else 0})

    return {
        "fv_ossz": len(fv),
        "fv_fel": len(erintett),
        "byte_ossz": sum(m for _, m in fv),
        "byte_fel": sum(m for k, m in fv if k in erintett),
        "elek": elek,
        "osztaly": len(rtti),
        "csalad": csalad,
        "csalad_erintett": csalad_erintett,
        "savok": savok,
        "spec_lapok": len(list(SPEC_DIR.glob("*.md"))),
        "kiemelt_jegyek": _kiemelt_jegyek(),
        "ideje": datetime.now(timezone.utc).astimezone(),
    }


# --- megjelenítés ----------------------------------------------------------


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def _sz(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _kozeli(cim: int, tabla: dict) -> int | None:
    """A sáv kezdőcíméhez legközelebbi gondozott bejegyzés (fél sávon belül)."""
    if not tabla:
        return None
    jelolt = min(tabla, key=lambda k: abs(k - cim))
    return jelolt if abs(jelolt - cim) < 0x20000 else None


def _terep(a: dict) -> str:
    sorok = []
    for sav in a["savok"]:
        cim = sav["cim"]
        ide = _kozeli(cim, {k: 1 for k in IDEGEN_SAVOK})
        kiem_kulcs = _kozeli(cim, KIEMELT_SAVOK)
        jegy = KIEMELT_SAVOK.get(kiem_kulcs) if kiem_kulcs else None
        # a kiemelés CSAK akkor él, ha a jegy tényleg nyitott és kiemelt
        aktiv = jegy and (not a["kiemelt_jegyek"] or jegy[0] in a["kiemelt_jegyek"])
        cimke_kulcs = _kozeli(cim, SAV_CIMKEK)
        cimke = SAV_CIMKEK.get(cimke_kulcs, "—") if cimke_kulcs else "—"

        sor_o, oszlop_o, mi = "", "", f'<span class="mi halvany">{_e(cimke)}</span>'
        if ide:
            sor_o, oszlop_o = " idegen-sor", " idegen"
        elif aktiv:
            sor_o, oszlop_o = " kiemelt-sor", " kiemelt"
            hivatkozas = (f'<a href="{REPO_URL}/issues/{jegy[0]}">'
                          f'#{jegy[0]}</a>')
            mi = f'<span class="mi">{hivatkozas} · {_e(jegy[1])}</span>'
        elif cimke != "—":
            mi = f'<span class="mi">{_e(cimke)}</span>'

        sorok.append(
            f'      <div class="terepsor{sor_o}">'
            f'<span class="cim">{cim:#010x}</span>'
            f'<span class="oszlop{oszlop_o}"><i style="width:{sav["arany"]}%"></i></span>'
            f'<span class="szam">{sav["fel"]}/{sav["ossz"]}</span>{mi}</div>'
        )
    return "\n".join(sorok)


def _csaladok(a: dict) -> str:
    LEIRAS = {
        "Fen": "felületleíró keretrendszer",
        "glimmer": "képfeldolgozás, effektek",
        "yt": "platformréteg: fájl, hálózat, rajzolás",
        "C": "az alkalmazás saját osztályai",
        "egyéb": "névtér nélküli és idegen osztályok",
    }
    sorok = []
    rendezett = sorted(
        a["csalad"],
        key=lambda k: -(100 * a["csalad_erintett"][k] // max(a["csalad"][k], 1)),
    )
    for k in rendezett:
        ossz, fel = a["csalad"][k], a["csalad_erintett"][k]
        arany = round(100 * fel / ossz) if ossz else 0
        nev = f"{k}::" if k in ("Fen", "glimmer") else f"{k}*" if k in ("yt", "C") else k
        sorok.append(
            f'      <div class="csalad"><div class="nev">{_e(nev)}'
            f'<span class="mit">{_e(LEIRAS.get(k, ""))}</span></div>'
            f'<div class="savtart"><div class="sav" style="width:{arany}%"></div></div>'
            f'<div class="ertek">{fel} / {_sz(ossz)}</div></div>'
        )
    return "\n".join(sorok)


def epits(a: dict) -> str:
    ideje = a["ideje"].strftime("%Y. %m. %d. %H:%M")
    fv_arany = 100 * a["fv_fel"] / a["fv_ossz"]
    b_arany = 100 * a["byte_fel"] / a["byte_ossz"]
    fig = "" if a["kiemelt_jegyek"] else (
        '  <div class="doboz"><p><b>A jegyek nem voltak lekérdezhetők ehhez a '
        'futáshoz</b>, ezért a narancs kiemelés a gondozott alapértelmezést '
        'mutatja, nem a mai címkéket.</p></div>')
    return f"""<title>Picasa 3.9 — hol tart a visszafejtés</title>
{_STILUS}
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Picasa 3.9.141.259 · visszafejtési térkép · frissítve {_e(ideje)}</p>
    <h1>Merre jártunk a binárisban</h1>
    <p class="standfirst">
      A Picasa programfájlja <strong>{_sz(a['fv_ossz'])} függvényből</strong> áll.
      Ez a lap azt mutatja, mekkora részét fejtettük vissza — és ami fontosabb:
      <strong>hol</strong>. Minden szám mérésből jön: a bináris indexéből és a
      specifikációink címhivatkozásaiból.
    </p>
  </header>

  <div class="stats">
    <div class="stat"><b>{_sz(a['fv_ossz'])}</b><span>függvény a programfájlban</span></div>
    <div class="stat jo"><b>{_sz(a['fv_fel'])}</b><span>ezekből visszafejtve és dokumentálva</span></div>
    <div class="stat fel"><b>{str(round(b_arany,1)).replace(".", ",")}%</b><span>a kód <em>terjedelmének</em> aránya</span></div>
    <div class="stat"><b>{str(round(fv_arany,1)).replace(".", ",")}%</b><span>a függvények <em>darabszámának</em> aránya</span></div>
    <div class="stat jo"><b>{_sz(a['osztaly'])}</b><span>azonosított osztály (RTTI)</span></div>
    <div class="stat"><b>{a['spec_lapok']}</b><span>specifikációs lap épült ebből</span></div>
  </div>
{fig}
  <div class="doboz">
    <p><b>Miért más a két százalék?</b> Mert nem véletlenszerűen haladtunk. A
    darabszám {str(round(fv_arany,1)).replace(".", ",")}%, a kódterjedelem viszont {str(round(b_arany,1)).replace(".", ",")}% — vagyis rendre a
    <strong>nagy, sűrű függvényeket</strong> vettük elő, amelyekben a valódi
    logika lakik, nem a több ezer apró segédfüggvényt.</p>
  </div>

  <section>
    <div class="section-head">
      <h2>A program nagy birodalmai</h2>
      <p>A Picasa osztályai jól elkülönülő családba esnek. A sáv azt mutatja,
         hányat érintettünk közülük.</p>
{eredet_sor(forras_ideje(_index_utvonal()), "egy bináris kutatási kör új eredményt importál az indexbe")}
    </div>
    <div class="csaladok">
{_csaladok(a)}
    </div>
  </section>

  <section>
    <div class="section-head">
      <h2>Domborzat: hol jártunk a címtartományban</h2>
      <p>A programfájl elejétől a végéig, {SAVOK} egyenlő sávra osztva. A csík
         hossza a feltárt függvények aránya azon a szakaszon.
         <b style="color:var(--kiemelt)">Naranccsal</b> a kiemelt jegyeink által
         érintett sávok — a jobb szélen a jegy számával.
{eredet_sor(forras_ideje(_index_utvonal()), "egy bináris kutatási kör új eredményt importál az indexbe")}
         <b>Szürke sraffozással</b> az, amit sosem kell visszafejtenünk.</p>
    </div>
    <div class="terep">
{_terep(a)}
    </div>
    <div class="jelmagy">
      <span><i class="kocka kiem"></i> <b>kiemelt</b> — most ezen dolgozunk</span>
      <span><i class="kocka fel"></i> feltárt, de nem kiemelt</span>
      <span><i class="kocka nincs"></i> feltáratlan</span>
      <span><i class="kocka ide"></i> soha nem kell — idegen könyvtár</span>
    </div>
    <div class="doboz">
      <p><b>A szürke sraffozás: amit sosem kell visszafejtenünk.</b> Az utolsó
      sávok nem a Picasa saját kódja, hanem <b>idegen könyvtár</b>: PNG-, TIFF-
      és JPEG-dekóderek, színprofil-kezelő, és a C futtatókörnyezet. Nyílt
      megfelelőik nálunk már használatban vannak. Ezért nem üres csíkot kaptak:
      az „nulla százalék" azt sugallná, hogy van itt tennivaló. Nincs.</p>
      <p><b>A narancs: amin most dolgozunk.</b> Nem szubjektív válogatás — a
      <code>next-up</code> címkéjű jegyek és a nyitott P1-esek adják, tehát
      ugyanaz a rangsor, ami a fejlesztést vezeti. Ha egy jegy lekerül a
      listáról, a narancs is eltűnik a következő frissítéskor.</p>
    </div>
  </section>

  <section>
    <div class="section-head">
      <h2>Amit ez a lap NEM mutat</h2>
      <p>Három korlát, hogy a szám ne látsszon többnek, mint ami.</p>
{eredet_sor(forras_ideje(SPEC_DIR), "egy kutatási kör újabb címeket köt specifikációhoz")}
    </div>
    <div class="doboz">
      <p><b>A „feltárt" itt annyit tesz: valamelyik specifikációnk hivatkozik
      rá.</b> Ez lehet egyetlen mondat is — nem jelenti, hogy a függvény teljes
      egészében meg van értve.</p>
      <p><b>A hívási gráf nincs ábrázolva.</b> A {_sz(a['elek'])} él egy ábrán
      olvashatatlan lenne; ez a lap ezért területet mutat, nem hálózatot.</p>
      <p><b>A sávcímkék kézzel gondozottak.</b> A számok mérésből jönnek, de
      hogy egy sávban „mi lakik", azt ember írta le — ha egy terület tartalma
      megváltozik, a <code>scripts/binaris_terkep.py</code>-ban kell átvezetni.</p>
    </div>
  </section>

  <footer class="colophon">
    <p>
      Forrás: a <code>Picasa3.exe</code> 3.9.141.259 bináris indexe
      ({_sz(a['fv_ossz'])} függvény, {_sz(a['elek'])} hivatkozás,
      {_sz(a['osztaly'])} osztály) és a <code>docs/specs/</code>
      {a['spec_lapok']} lapjának címhivatkozásai. A programfájlt nem közöljük.
    </p>
    <p>
      Ezt a lapot a <code>scripts/binaris_terkep.py</code> állítja elő.
      Frissítéshez futtasd, majd publikáld ugyanerre a címre.
    </p>
  </footer>
</div>
"""


_STILUS = """<style>
  :root {
    --ground:#E9EDEE; --surface:#F7F9F9; --rule:#C3CDD0; --rule-soft:#D8E0E1;
    --ink:#16232A; --ink-soft:#4E6068; --ink-faint:#7C8E95;
    --accent:#1F6F63; --accent-wash:#DCE8E5;
    --warn:#8A5B14;
    --idegen:#AEB9BC; --idegen-halvany:#DDE3E4;
    --kiemelt:#C2622A;
    --font-display:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
    --font-body:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
    --font-mono:ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground:#101A1E; --surface:#17242A; --rule:#2C3F47; --rule-soft:#223138;
      --ink:#DDE7E9; --ink-soft:#9DB1B8; --ink-faint:#6E858D;
      --accent:#56B9A7; --accent-wash:#17332F; --warn:#D6A755;
      --idegen:#5C6D74; --idegen-halvany:#1B282D; --kiemelt:#E8894F;
    }
  }
  :root[data-theme="dark"] {
    --ground:#101A1E; --surface:#17242A; --rule:#2C3F47; --rule-soft:#223138;
    --ink:#DDE7E9; --ink-soft:#9DB1B8; --ink-faint:#6E858D;
    --accent:#56B9A7; --accent-wash:#17332F; --warn:#D6A755;
    --idegen:#5C6D74; --idegen-halvany:#1B282D; --kiemelt:#E8894F;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--ground); color:var(--ink);
         font-family:var(--font-body); font-size:16px; line-height:1.6;
         -webkit-font-smoothing:antialiased; }
  .wrap { max-width:64rem; margin:0 auto; padding:3.5rem 1.5rem 6rem;
          display:flex; flex-direction:column; gap:3.5rem; }
  .eyebrow { font-family:var(--font-mono); font-size:0.7rem; letter-spacing:0.14em;
             text-transform:uppercase; color:var(--ink-faint); margin:0; }
  h1 { font-family:var(--font-display); font-weight:600;
       font-size:clamp(2rem,5vw,2.9rem); line-height:1.12; letter-spacing:-0.015em;
       text-wrap:balance; margin:0; }
  .masthead { display:flex; flex-direction:column; gap:1.1rem; }
  .standfirst { font-size:1.05rem; color:var(--ink-soft); max-width:46rem; margin:0; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));
           gap:1px; background:var(--rule); border-block:1px solid var(--rule); }
  .stat { background:var(--surface); padding:1.05rem 1.15rem 1.15rem;
          display:flex; flex-direction:column; gap:0.2rem; border-top:3px solid var(--rule); }
  .stat b { font-family:var(--font-mono); font-size:1.7rem; font-weight:500;
            font-variant-numeric:tabular-nums; letter-spacing:-0.02em; line-height:1.1; }
  .stat span { font-size:0.78rem; color:var(--ink-soft); line-height:1.4; }
  .stat.jo { border-top-color:var(--accent); } .stat.jo b { color:var(--accent); }
  .stat.fel { border-top-color:var(--warn); } .stat.fel b { color:var(--warn); }
  section { display:flex; flex-direction:column; gap:1.4rem; }
  h2 { font-family:var(--font-display); font-size:1.5rem; font-weight:600;
       letter-spacing:-0.01em; margin:0; text-wrap:balance; }
  .section-head { display:flex; flex-direction:column; gap:0.35rem; }
  .eredet { margin:0; font-family:var(--font-mono); font-size:0.72rem;
            color:var(--ink-faint); }
  .section-head p { margin:0; color:var(--ink-soft); max-width:46rem; font-size:0.93rem; }
  .csaladok { display:flex; flex-direction:column; }
  .csalad { display:grid; grid-template-columns:9rem 1fr 5.5rem; gap:0 1rem;
            align-items:center; padding:0.65rem 0; border-top:1px solid var(--rule-soft); }
  .csalad:last-child { border-bottom:1px solid var(--rule-soft); }
  .csalad .nev { font-family:var(--font-mono); font-size:0.85rem; font-weight:600; }
  .csalad .mit { display:block; font-family:var(--font-body); font-size:0.72rem;
                 font-weight:400; color:var(--ink-faint); letter-spacing:0; }
  .savtart { background:var(--rule-soft); height:1.35rem; }
  .sav { background:var(--accent); height:100%; }
  .csalad .ertek { font-family:var(--font-mono); font-size:0.85rem; text-align:right;
                   font-variant-numeric:tabular-nums; color:var(--ink-soft); }
  .terep { display:flex; flex-direction:column; gap:0.15rem; overflow-x:auto; }
  .terepsor { display:grid; grid-template-columns:6.5rem 1fr 4.2rem 1fr;
              gap:0 0.7rem; align-items:center; font-size:0.78rem; min-width:34rem; }
  .terepsor .cim { font-family:var(--font-mono); color:var(--ink-faint); font-size:0.72rem; }
  .oszlop { height:0.85rem; background:var(--rule-soft); }
  .oszlop i { display:block; height:100%; background:var(--accent); }
  .oszlop.idegen { background:var(--idegen-halvany);
                   background-image:repeating-linear-gradient(45deg,
                     transparent 0 4px, var(--idegen) 4px 5px); }
  .oszlop.idegen i { background:none; }
  .oszlop.kiemelt i { background:var(--kiemelt); }
  .terepsor.kiemelt-sor .cim, .terepsor.kiemelt-sor .mi {
      color:var(--kiemelt); font-weight:600; }
  .terepsor.idegen-sor .cim, .terepsor.idegen-sor .szam { opacity:0.55; }
  .terepsor .szam { font-family:var(--font-mono); text-align:right;
                    font-variant-numeric:tabular-nums; color:var(--ink-soft); font-size:0.72rem; }
  .terepsor .mi a { color:inherit; text-decoration:none;
                    border-bottom:1px dotted currentColor; }
  .terepsor .mi { color:var(--ink-soft); font-size:0.76rem; overflow:hidden;
                  text-overflow:ellipsis; white-space:nowrap; }
  .terepsor .mi.halvany { color:var(--ink-faint); font-style:italic; }
  .jelmagy { display:flex; gap:1.5rem; flex-wrap:wrap; font-size:0.78rem;
             color:var(--ink-soft); padding-top:0.4rem; }
  .jelmagy span { display:flex; align-items:center; gap:0.4rem; }
  .kocka { width:0.8rem; height:0.8rem; display:inline-block; }
  .kocka.fel { background:var(--accent); }
  .kocka.kiem { background:var(--kiemelt); }
  .kocka.ide { background:var(--idegen-halvany);
               background-image:repeating-linear-gradient(45deg,
                 transparent 0 3px, var(--idegen) 3px 4px); }
  .kocka.nincs { background:var(--rule-soft); }
  .doboz { background:var(--surface); border-left:2px solid var(--warn);
           padding:0.9rem 1.1rem; font-size:0.9rem; color:var(--ink-soft);
           display:flex; flex-direction:column; gap:0.5rem; }
  .doboz b { color:var(--ink); }
  .doboz p { margin:0; }
  code { font-family:var(--font-mono); font-size:0.85em; background:var(--accent-wash);
         color:var(--ink); padding:0.1em 0.32em; border-radius:2px; }
  .colophon { border-top:1px solid var(--rule); padding-top:1.4rem; font-size:0.83rem;
              color:var(--ink-faint); display:flex; flex-direction:column; gap:0.4rem; }
  .colophon p { margin:0; max-width:46rem; }
  @media (max-width:38rem) {
    .csalad { grid-template-columns:1fr; gap:0.25rem; }
    .csalad .ertek { text-align:left; }
  }
  @media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
</style>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ki", type=Path, default=REPO / "docs" / "binaris-terkep.html")
    ap.add_argument("--url", action="store_true", help="csak az artifact címét írja ki")
    args = ap.parse_args()

    if args.url:
        print(ARTIFACT_URL)
        return 0

    try:
        adat = gyujts()
    except FileNotFoundError as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # noqa: BLE001 — a lap sosem lehet félkész
        print(f"A mérés nem futott le: {exc.__class__.__name__}: {exc}", file=sys.stderr)
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
