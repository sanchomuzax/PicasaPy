"""Az „arcos képek" szűrő a felületen (#1830).

Az eredeti keresősávján ez a `facesearch` gomb, buboréksúgója
„Show only photos with faces". A film-szűrő (`movieFilter`) mintáját
követi: szűrt nézet, ugyanaz a be/ki logika.

## A foga

A gomb ne csak LÉTEZZEN: hívja is a vezérlőt, és a bekapcsolt állapota a
tényleges nézetmódra kössön — különben ugyanaz a néma vezérlő lenne, ami
eddig volt (helyfoglaló `☺` glif).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_QML = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "MainToolbar.qml"
).read_text(encoding="utf-8")


def _blokk() -> str:
    kezdet = _QML.index('objectName: "faceFilter"')
    return _QML[kezdet : kezdet + 2600]


class TestAGombOttVan:
    def test_van_arc_szuro(self):
        assert 'objectName: "faceFilter"' in _QML, (
            "a szűrő-zónából hiányzik az arcos képek szűrője"
        )

    def test_az_EREDETI_buboreksugot_hasznalja(self):
        """`facesearch` — nem saját fogalmazás."""
        assert 'qsTr("Show only photos with faces")' in _blokk()


class TestABekotes:
    def test_a_gomb_NEM_nema(self):
        """A #1798 osztálya: eddig egy `☺` glif állt itt, ami semmit nem
        csinált."""
        assert "controller.showFacesOnly()" in _blokk()

    def test_ujra_kattintva_KIKAPCSOL(self):
        assert "controller.clearFilter()" in _blokk()

    def test_az_aktiv_allapot_a_NEZETMODRA_kot(self):
        """Nem saját logikai jelzőre: a pipa akkor is helyes legyen, ha a
        szűrőt máshonnan kapcsolják ki (a #1468 rádió-csapdájának
        rokona)."""
        blokk = _blokk()
        assert 'controller.viewModeName === "faces"' in blokk

    def test_a_helyfoglalo_glif_ELTUNT(self):
        """A foga: ha valaki visszateszi a néma `Text { text: "☺" }`
        helyfoglalót, ez bukik."""
        assert 'text: "☺"; font.pixelSize: 13; color: Theme.placeholderText' \
            not in _QML


class TestAVezerloOldal:
    def test_a_vezerlonek_van_showFacesOnly_slotja(self):
        from picasapy.app.controller import AppController

        assert hasattr(AppController, "showFacesOnly")

    def test_a_MEGLEVO_ini_adatra_epul_nem_a_felismeresre(self):
        """A jegy kikötése: „nem igényel arcfelismerést". A `face` tábla a
        felismerő motoré (`index/faces_detected.py`); ez a szűrő az
        ini-söprésen álló `photos_with_faces`-t hívja."""
        import inspect

        from picasapy.app.controller import AppController

        forras = inspect.getsource(AppController.showFacesOnly)
        kod = "\n".join(
            sor for sor in forras.splitlines()
            if not sor.lstrip().startswith("#")
        )
        assert "photos_with_faces(" in kod
