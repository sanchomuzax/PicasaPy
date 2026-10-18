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
PENDING: frozenset[str] = frozenset(
    {
        '\nPicasaPy does not recognize %1 of the files to be deleted.\n',  # ko
        '\nPicasaPy does not recognize 1 of the files to be deleted.\n',  # ko
        '%1 files will not be imported because they are already duplicates in PicasaPy.\n',  # cs, fi, hr, ko, pl, sl, tr
        '%d Photo in PicasaPy',  # cs, fi, ko, sl, sr, tr
        '%d Photos in PicasaPy',  # cs, fi, ko, sl, sr, tr
        '%n of those are duplicates already in PicasaPy',  # cs, fi, hr, ko, pl, sl, tr
        '&Remove from PicasaPy...',  # cs, fi, hr, ko, pl, sl, tr
        '1 file will not be imported because it is already a duplicate in PicasaPy.\n',  # cs, fi, hr, ko, pl, sl, tr
        'Add &File to PicasaPy...',  # cs, fi, ko, sl, sr, tr
        'Add File to PicasaPy...',  # cs, fi, ko, sl, sr, tr
        'Add Folder to PicasaPy...',  # cs, fi, hr, ko, sl, sr, tr
        "As PicasaPy scans your photos, the faces it finds are automatically grouped for easy naming.\n\nThings to know:\n\nTo identify a person, click 'Add a name', then type in the person's name and press Enter.  A new People album will be created each time you name someone for the first time.\n\n(TIP: Sign in with your Google Account to gain access to all of your Google Account contacts while naming.)\n\nTo ignore a person, click the 'X' button on the face thumbnail.\n\nSuggestions: After you name someone, PicasaPy may suggest more matching faces for that person. Click on a person's album to view and confirm (or reject) any suggestions.\n\n\n Click 'Learn More' for information about this feature.",  # ko
        "As PicasaPy scans your photos, the faces it finds are automatically grouped for easy naming.\n\nThings to know:\n\nTo identify a person, click 'Add a name', then type in the person's name and press Enter. A new People album will be created each time you name someone for the first time.\n\n(TIP: Sign in with your Google Account to gain access to all of your contacts while naming.)\n\nTo ignore a person, click the 'X' button on the face thumbnail.\n\nSuggestions: After you name someone, PicasaPy may suggest more matching faces for that person. Click on a person's album to view and confirm (or reject) any suggestions.",  # ko
        'Change the language PicasaPy uses?\n\nIt will change the next time PicasaPy is opened.',  # fi, hr, ko, sl, tr
        'Exclude photos that are already imported into PicasaPy',  # cs, fi, hr, ko, pl, sl, tr
        'For each folder, you can choose whether or not to have PicasaPy find pictures inside it.  You can also pick folders to watch for new pictures.',  # ko, tr
        'If you remove a watched folder, new items that you add to that folder on disk will not be automatically added to PicasaPy. Are you sure you want to do this?',  # cs, fi, ko, sl, sr, tr
        'Locate in PicasaPy',  # cs, fi, hr, ko, pl, sl, tr
        'PicasaPy Notifier',  # cs, hr, sv
        'PicasaPy failed to initialize Google Maps.  Please make sure that you are connected to the Internet.',  # cs, ko
        'PicasaPy had a problem loading this file(s)\n',  # fi, ko
        'PicasaPy has found and corrected red eye(s).\n\nNote: You can click on a box to delete a change.\n\nYou can also draw a square around any red eye that PicasaPy may have missed.',  # ko, tr
        'PicasaPy is now showing the files you have not previously backed up.',  # sl
        'PicasaPy is ready to search for pictures on your computer',  # ko
        'Remove from PicasaPy',  # cs, fi, hr, ko, pl, sl, tr
        'Remove from PicasaPy...',  # cs, fi, hr, ko, pl, sl, tr
        'Scan Always keeps watching the folder: pictures you add to it later show up on their own.\n\nScan Once takes the pictures that are in the folder now and then forgets about it.\n\nRemove from PicasaPy takes the folder out of your library. The pictures stay on your disk.\n\nFace detection is separate: you can watch a folder and still keep faces in it out of the library.',  # cs, fi, hr, ko, pl, sl, tr
        'Search for these photos in PicasaPy',  # fi, hr, ko, pl, sl, tr
        'Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by PicasaPy by using the Folder Manager tool (available from the Tools menu)',  # ko, tr
        "This file is read only. In order to edit this file, PicasaPy needs to copy the file's folder. Would you like to make a copy now?",  # fi, ko, tr
        'You can also draw a square around any red eye that PicasaPy may have missed. Click, hold, and drag the mouse around each eye separately to select it. A selection box appears over the area.',  # ko, tr
    }
)


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
