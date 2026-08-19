"""`formatting.to_file_url` — lokális útvonal → `file:` URL (#1009).

Ez a függvény a #1009 windows-lábának leletéből született. A kollázs
háttérkép-előnézete a felületen `"file://" + útvonal` módon állította elő a
forrást, és a **windows-CI-láb** fogta meg, hogy ez Windowson MINDEN
útvonalra hibás: a `C:` a QUrl-nek portnak látszik, az URL érvénytelen
lesz, a QML `Image.source`-a üresre normalizálódik, és a felhasználó üres
előnézetet lát — hibaüzenet nélkül.

Az itteni állítások **platformfüggetlenek**: a QUrl *elemzése* nem
platformfüggő (csak a `toLocalFile` kimenete az), tehát a kézi fűzés
hibáját Linuxon is ki tudjuk mondani.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl

from picasapy.app.formatting import to_file_url, to_local_path

#: Egy valódi windowsos útvonal (a CI-futtató ideiglenes mappája ilyen).
WINDOWSOS = "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\Nyaralás 2026\\a.jpg"


class TestAKeziFuzesHibas:
    """Amit NEM szabad írni — és miért. A bizonyíték maga a QUrl."""

    def test_a_ketperjeles_alak_windowsos_utvonalra_ERVENYTELEN(self):
        naiv = QUrl("file://" + WINDOWSOS)
        assert not naiv.isValid()
        # a meghajtóbetű PORTNAK látszik, ezért a gazdanév „c" lesz
        assert naiv.host() == "c"

    def test_a_kettospontos_alak_a_kettos_kereszten_elvagja_a_nevet(self):
        """A `#` az URL-ben töredékjel: a fájlnév vége NÉMÁN elvész."""
        naiv = QUrl("file:/képek/kép #1.jpg")
        assert "1.jpg" not in naiv.toLocalFile()

    def test_a_to_file_url_mindkettot_megoldja(self):
        assert to_file_url(WINDOWSOS).isValid()
        assert "1.jpg" in to_file_url("/képek/kép #1.jpg").toLocalFile()


class TestKorjarat:
    def test_ekezetes_es_szokozos_utvonal(self, tmp_path):
        ut = str(tmp_path / "Nyaralás 2026" / "nyár.jpg")
        # ⚠️ `Path`-ként hasonlítunk: a `toLocalFile` Windowson PER-jeles utat
        # ad (`C:/…`), a nyers szöveg-hasonlítás ott némán bukna
        assert Path(to_file_url(ut).toLocalFile()) == Path(ut)

    def test_kettos_kereszt_a_nevben(self, tmp_path):
        ut = str(tmp_path / "kép #1.jpg")
        url = to_file_url(ut)
        assert url.isValid()
        assert Path(url.toLocalFile()) == Path(ut)
        assert "%23" in url.toString()

    def test_a_to_local_path_a_parja(self, tmp_path):
        ut = str(tmp_path / "Nyaralás 2026" / "kép #1.jpg")
        assert to_local_path(to_file_url(ut).toString()) == ut

    def test_ures_bemenetre_ures_url(self):
        assert to_file_url("").toString() == ""
        assert to_file_url("   ").toString() == ""
