"""#5294: a program saját neve a felületen PicasaPy, nem Picasa.

Az őr a QML-literálokat és a `.ts` katalógusok forrás- és fordítás-szövegeit
nézi. Csak az ÖNÁLLÓ „Picasa” számít a program saját nevének: a „PicasaPy”,
„PicasaWeb”, „Picasa2” és az azonosítók (például `menuToolsImportFromPicasa`)
nem.

Az eredeti Picasa neve megmarad ott, ahol a szöveg az eredeti programra
utal: az importálásnál, a verzióknál, a megszűnt Picasa Web Albums
szolgáltatásnál és a fájl- vagy mappanevekben. Ezeket a KIVETEL lista
nevesíti, mindegyiket indokolva.

A PENDING lista a fordításokat mentesíti abban az egy esetben, ha a magyar
(vagy más) fordításban a ragozott alak („Picasából”, „Picasában”) nem
gépi keresés-cserével javítható, mert a helyes alakhoz nyelvi ítélet kell.
Ha egy fordítást kijavítottak, a bejegyzését törölni kell, különben a
második teszt nem fut le róla.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_QML = _GYOKER / "src" / "picasapy" / "app" / "qml"
_I18N = _GYOKER / "src" / "picasapy" / "app" / "i18n"

# A program saját nevét jelöli: önálló „Picasa", nem „PicasaPy"/„Picasa2"-féle.
_SAJAT = re.compile(r"(?<!\w)Picasa(?!\w)")
# Fordításban minden alak hiba, amely nem PicasaPy: a ragozott („Picasából",
# „Picasie", „Picasa’da") is, mert a magyar tő az ékezetet is átveheti.
_FORDITAS = re.compile(r"Picas(?!a?Py)")
_QML_LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

# Az eredeti Picasa neve, amely MARAD. Kulcs: a szövegrészlet, érték: az indok.
KIVETEL = {
    "Web Albums": "Google Picasa Web Albums: a megszűnt külső szolgáltatás neve.",
    "Web albums": "Ugyanez kisbetűvel, az eredeti Remove People ablak jelölőnégyzetében (#5391).",
    "Import from Picasa": "az eredeti Picasa adatainak átvétele (menüpont, ablak).",
    "previous Picasa installation": "a gépen korábban telepített eredeti Picasa.",
    "Picasa2": "az eredeti Picasa2 adatmappa neve.",
    "places from Picasa": "az eredeti Picasa nevei, kulcsszavai és helyei.",
    "No Picasa data": "az eredeti Picasa adatainak hiánya a gépen.",
    "taken over from Picasa": "az eredeti Picasa adataiból átvett dátum.",
    "could not be taken over": "az eredeti Picasa adataiból átvett dátum sikertelen átvétele.",
    "Picasa 1": "az eredeti Picasa 1-es verziója.",
    "Picasa 3": "az eredeti Picasa 3-as verziója (3.9 is).",
    "older version of Picasa": "az eredeti Picasa régebbi verziója.",
    "older Picasa versions": "az eredeti Picasa régebbi verziói.",
    "Today's Picasa": "a mai eredeti Picasa képességei.",
    "Picasa can read this filter": "az eredeti Picasa képessége.",
    "Picasa engine": "az eredeti Picasa motorja.",
    "successor": "az eredeti Picasa utódjaként írja le magát (névjegy).",
    "original Picasa": "az eredeti Picasa említése.",
    "implemented yet": "a SplashScreen mondatának része: az eredeti Picasa effektjei.",
    "Adopt Picasa folders": "az eredeti Picasa által figyelt mappák átvétele.",
    "cannot open it": "az eredeti Picasa nem nyitja meg a rejtett mappát. KÉTES.",
    "marked for Picasa": "a .picasa.ini eredeti formátuma. KÉTES.",
    "same folder is open in Picasa": "az eredeti Picasa írásai. KÉTES.",
    "Forums": "a visszavont (retired) Picasa-fórumok menüpont. KÉTES.",
    "Include Picasa": "rejtett égetési jelölőnégyzet, az eredeti telepítő. KÉTES.",
    "Picasa Backup": "a lemezen lévő mentési mappa neve (fájlrendszer).",
}

# Ragozott fordítások: a forrásszöveg, amelynek a fordításában a Picasa-név
# még a régi alakban áll, mert a javításhoz nyelvi ítélet kell (Sonnet-szint).
PENDING: frozenset[str] = frozenset()


def _kivetel(szoveg: str) -> bool:
    return any(kulcs in szoveg for kulcs in KIVETEL)


def _ts_fajlok() -> list[Path]:
    return sorted(_I18N.glob("picasapy_*.ts"))


def _uzenetek(fajl: Path):
    for uzenet in ET.parse(fajl).getroot().iter("message"):
        forras = uzenet.findtext("source") or ""
        forditas = uzenet.find("translation")
        szoveg = "".join(forditas.itertext()) if forditas is not None else ""
        yield forras, szoveg


def _qml_literalok() -> list[str]:
    """A QML kódsorok szövegliterálai; a `//` megjegyzéssorok kimaradnak."""
    literalok: list[str] = []
    for fajl in sorted(_QML.rglob("*.qml")):
        for sor in fajl.read_text(encoding="utf-8").splitlines():
            if sor.lstrip().startswith("//"):
                continue
            literalok.extend(_QML_LITERAL.findall(sor))
    return literalok


def test_qml_forras_nem_tartalmaz_regi_sajat_nevet():
    hibak = sorted(
        {
            literal
            for literal in _qml_literalok()
            if _SAJAT.search(literal) and not _kivetel(literal)
        }
    )
    assert not hibak, f"a program saját neve még „Picasa” a QML-ben: {hibak}"


def test_ts_forras_nem_tartalmaz_regi_sajat_nevet():
    hibak = sorted(
        {
            forras
            for fajl in _ts_fajlok()
            for forras, _ in _uzenetek(fajl)
            if _SAJAT.search(forras) and not _kivetel(forras)
        }
    )
    assert not hibak, f"a .ts forrásában még „Picasa” a saját név: {hibak}"


def test_ts_forditas_nem_tartalmaz_regi_sajat_nevet():
    hibak = sorted(
        {
            (fajl.name, forras[:70])
            for fajl in _ts_fajlok()
            for forras, forditas in _uzenetek(fajl)
            if forras not in PENDING
            and not _kivetel(forras)
            and _FORDITAS.search(forditas)
        }
    )
    assert not hibak, f"fordításban még a régi saját név áll: {hibak}"


def test_kivetel_es_fuggo_lista_nem_avult():
    szovegek = _qml_literalok() + [
        szoveg
        for fajl in _ts_fajlok()
        for szoveg, _ in _uzenetek(fajl)
    ]
    for kulcs in KIVETEL:
        assert any(kulcs in szoveg for szoveg in szovegek), (
            f"a kivétellista eleme már nincs a szövegekben: {kulcs!r}"
        )
    forrasok = {forras for fajl in _ts_fajlok() for forras, _ in _uzenetek(fajl)}
    assert PENDING <= forrasok, "a PENDING listában olyan forrás van, ami nincs a .ts-ben"
