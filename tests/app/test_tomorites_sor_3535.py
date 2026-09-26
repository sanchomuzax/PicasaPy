"""#3535: a Tulajdonságok panel Tömörítés sora az eredeti 36 kódos táblája.

Forrás: `docs/specs/picasa-metaadat-tulajdonsagok.md` 14. szakasz — a
`0x009f23a0` formázó minden ága programmal kiolvasva, a magyar szöveg a
`stringres` szövegtárból. Ismeretlen kódnál az eredeti a SZÁMOT írja
(`sprintf("%ld")`), nem hagyja üresen a sort.

⚠️ Az eredeti táblája a 0/1-nél EL VAN TOLVA (0 → Tömörítetlen, 1 → CCITT 1D,
a 2-esnek nincs ága), a TIFF-szabvány szerint viszont 1 = tömörítetlen,
2 = CCITT 1D. A felület az eredetit követi (`docs/decisions/
szerkeszto-bal-panel.md` elve) — ez a teszt ezt KIMONDOTTAN rögzíti.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QLocale

piexif = pytest.importorskip("piexif")

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"

#: kód → (alapszöveg, magyar `stringres`) — a spec 14. táblája, mind a 36 sor
_TABLA = {
    0: ("Uncompressed", "Tömörítetlen"),
    1: ("CCITT 1D", "CCITT 1D"),
    3: ("T4/Group 3 Fax", "T4/Group 3 fax"),
    4: ("T6/Group 4 Fax", "T6/Group 4 fax"),
    5: ("LZW", "LZW"),
    6: ("JPEG (old-style)", "JPEG (régi típusú)"),
    7: ("JPEG", "JPEG"),
    8: ("Adobe Deflate", "Adobe Deflate"),
    9: ("JBIG B&W", "JBIG B&W"),  # nincs magyar szövege → az alapszöveg
    10: ("JBIG Color", "JBIG színes"),
    99: ("JPEG", "JPEG"),
    262: ("Kodak 262", "Kodak 262"),
    32766: ("Next", "Következő"),
    32767: ("Sony ARW Compressed", "Sony ARW-tömörítésű"),
    32769: ("Epson ERF Compressed", "Epson ERF-tömörítésű"),
    32773: ("PackBits", "PackBits"),
    32809: ("Thunderscan", "Thunderscan"),
    32867: ("Kodak KDC Compressed", "Kodak KDC-tömörítésű"),
    32895: ("IT8CTPAD", "IT8CTPAD"),
    32896: ("IT8LW", "IT8LW"),
    32897: ("IT8MP", "IT8MP"),
    32898: ("IT8BL", "IT8BL"),
    32908: ("PixarFilm", "PixarFilm"),
    32909: ("PixarLog", "PixarLog"),
    32946: ("Deflate", "Veszteség nélküli tömörítés"),
    32947: ("DCS", "DCS"),
    34661: ("JBIG", "JBIG"),
    34676: ("SGILog", "SGILog"),
    34677: ("SGILog24", "SGILog24"),
    34712: ("JPEG 2000", "JPEG 2000"),
    34713: ("Nikon NEF Compressed", "Nikon NEF-tömörítésű"),
    34718: ("MDI Binary Level Codec", "MDI bináris szintű kodek"),
    34719: ("MDI Progressive Transform Codec", "MDI progresszív transzformációs kodek"),
    34720: ("MDI Vector", "MDI-vektor"),
    65000: ("Kodak DCR Compressed", "Kodak DCR-tömörítésű"),
    65535: ("Pentax PEF Compressed", "Pentax PEF-tömörítésű"),
}


def _photo(folder, name):
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name, folder_path=str(folder), size=1024, width=4, height=4,
        taken_at=None, kind="photo", keywords=(),
    )


def _tomorites(tmp_path, kod, tr=lambda t: t):
    """A panel „Compression" sora egy `kod` tömörítésű (EXIF 259) képre."""
    from PIL import Image

    from picasapy.app.formatting import properties_entries

    path = tmp_path / f"k{kod}.jpg"
    Image.new("RGB", (4, 4), "red").save(path, "JPEG")
    piexif.insert(
        piexif.dump({"0th": {piexif.ImageIFD.Compression: kod}}), str(path)
    )
    sorok = dict(properties_entries(_photo(tmp_path, path.name), QLocale("en"), tr))
    return sorok.get(tr("Compression"))


def test_a_tabla_36_kodos():
    assert len(_TABLA) == 36


@pytest.mark.parametrize("kod", sorted(_TABLA))
def test_minden_kod_az_eredeti_alapszovegevel(tmp_path, kod):
    assert _tomorites(tmp_path, kod) == _TABLA[kod][0]


@pytest.mark.parametrize(
    ("kod", "vart"),
    [
        (0, "Uncompressed"),
        # az eredeti eltolása: a TIFF-szabvány szerinti tömörítetlen (1) is
        # „CCITT 1D" — a felület az eredetit követi, szándékosan
        (1, "CCITT 1D"),
        # a 2-esnek nincs ága → a szám
        (2, "2"),
        (6, "JPEG (old-style)"),
        (7, "JPEG"),
        (99, "JPEG"),
        (32773, "PackBits"),
        (65535, "Pentax PEF Compressed"),
        # ismeretlen kód → a szám (`%ld`), nem üres sor
        (12345, "12345"),
    ],
)
def test_jegyben_kert_kodok(tmp_path, kod, vart):
    assert _tomorites(tmp_path, kod) == vart


def test_magyar_felirat_a_szovegtar_szerint(tmp_path):
    """A lefordított `.qm`-en át: minden kód a `stringres` magyar szövegét adja.

    A kontextus a `formatting.py` többi Tulajdonságok-szövegéé (a `.ts`
    névtelen kontextusa). ⚠️ A vezérlő ma `AppController.tr`-rel hívja a
    panelt, abban a kontextusban viszont a panel szövegei nincsenek meg —
    ez a #3535-től független, a teljes panelt érintő hiány.
    """
    from PySide6.QtCore import QCoreApplication, QTranslator

    _app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N))

    def tr(text):
        return translator.translate("", text) or text

    kulonbseg = {
        kod: (_tomorites(tmp_path, kod, tr), magyar)
        for kod, (_, magyar) in _TABLA.items()
        if _tomorites(tmp_path, kod, tr) != magyar
    }
    assert not kulonbseg
    assert _tomorites(tmp_path, 2, tr) == "2"
