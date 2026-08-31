"""#1526 — a Másolás/Kivágás FÁJLOKAT tesz a vágólapra.

## A lelet a binárisból

A Picasa a vágólapra a Windows shell-fájlátvitel formátumait teszi
(`Shell IDList Array`, `FileGroupDescriptor`, `FileContents`, `FileName`),
és köztük a **`Preferred DropEffect`**-et. Ez utóbbi bizonyítja, hogy a
**Kivágás és a Másolás UGYANAZT az adatot** teszi fel, és csak ez a
formátum különbözteti meg őket (mozgatás vs. másolás).

## A linuxos megfelelő

A `Preferred DropEffect` linuxos párja a `x-special/gnome-copied-files`
MIME-típus, aminek az **első sora** `copy` vagy `cut`, utána soronként a
fájl-URI-k. A fájlkezelők (Nautilus, Dolphin, Thunar) ezt olvassák. A
`text/uri-list` mellé tesszük, mert azt viszont mindenki érti.

⚠️ **Ez a teszt nem a rendszervágólapot méri**, hanem a MIME-adatot, amit
ráteszünk: a vágólap tartalma fejlesztői gépen és CI-n is a
munkamenet-kezelőtől függ, tehát nem determinisztikus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.fileops_controller import FileOpsController


@pytest.fixture
def kepek(tmp_path: Path) -> list[Path]:
    mappa = tmp_path / "album"
    mappa.mkdir()
    utak = []
    for i in range(2):
        p = mappa / f"kep{i}.jpg"
        p.write_bytes(b"kep")
        utak.append(p)
    return utak


def _mime(vezerlo) -> object:
    """A vezérlő által ÉPPEN feltett MIME-adat — a vágólap megkerülésével."""
    return vezerlo._vagolap_adat


class TestMasolasFajlokat:
    def test_a_masolas_uri_listat_tesz_fel(self, kepek, qt_app):
        vezerlo = FileOpsController()
        vezerlo.copyFilesToClipboard([str(p) for p in kepek])

        adat = _mime(vezerlo)
        assert adat is not None, "semmit nem tettünk a vágólapra"
        assert adat.hasUrls(), "nincs URL a vágólap-adatban"
        urlek = [u.toLocalFile() for u in adat.urls()]
        assert urlek == [str(p) for p in kepek], (
            f"nem a kijelölt fájlok kerültek fel: {urlek}"
        )

    def test_a_masolas_copy_jelzest_tesz_fel(self, kepek, qt_app):
        """A fájlkezelő ebből tudja, hogy MÁSOLNI kell, nem mozgatni."""
        vezerlo = FileOpsController()
        vezerlo.copyFilesToClipboard([str(p) for p in kepek])

        nyers = bytes(
            _mime(vezerlo).data("x-special/gnome-copied-files")
        ).decode("utf-8")
        assert nyers.splitlines()[0] == "copy", (
            f"az első sor nem „copy”: {nyers.splitlines()[:1]}"
        )
        assert len(nyers.splitlines()) == 1 + len(kepek)

    def test_a_kivagas_cut_jelzest_tesz_fel(self, kepek, qt_app):
        """A pár másik fele: ugyanaz az adat, más jelzés."""
        vezerlo = FileOpsController()
        vezerlo.cutFilesToClipboard([str(p) for p in kepek])

        adat = _mime(vezerlo)
        nyers = bytes(adat.data("x-special/gnome-copied-files")).decode("utf-8")
        assert nyers.splitlines()[0] == "cut", (
            f"az első sor nem „cut”: {nyers.splitlines()[:1]}"
        )
        # az URL-ek UGYANAZOK — a Preferred DropEffect tanulsága
        assert [u.toLocalFile() for u in adat.urls()] == [
            str(p) for p in kepek
        ], "a kivágás más fájlokat tett fel, mint a másolás"

    def test_ures_kijelolesre_nem_torol_vagolapot(self, qt_app):
        """Üres kijelöléssel ne söpörjük el, ami a vágólapon van."""
        vezerlo = FileOpsController()
        vezerlo.copyFilesToClipboard([])
        assert _mime(vezerlo) is None, (
            "üres kijelölésre is feltettünk valamit a vágólapra"
        )

    def test_a_nem_letezo_fajl_kimarad(self, kepek, qt_app):
        """Az időközben eltűnt fájl ne kerüljön a vágólapra: a beillesztés
        ott hibára futna, és a felhasználó nem értené, miért."""
        vezerlo = FileOpsController()
        hianyzo = kepek[0].parent / "nincs.jpg"
        vezerlo.copyFilesToClipboard([str(kepek[0]), str(hianyzo)])

        urlek = [u.toLocalFile() for u in _mime(vezerlo).urls()]
        assert urlek == [str(kepek[0])], (
            f"a nem létező fájl is felkerült: {urlek}"
        )


class TestAMenuBekotes:
    """A VALÓDI út: menütétel → vezérlő (MEMORY: a vezérlőre kattints)."""

    def test_a_ket_tetel_mar_nem_helyfoglalo(self, qml_app):
        from PySide6.QtCore import QObject

        window, _controller, _lib, _engine = qml_app
        for nev in ("menuEditCut", "menuEditCopy"):
            tetel = window.findChild(QObject, nev)
            assert tetel is not None, f"{nev} nem található"
            assert tetel.property("placeholder") is not True, (
                f"{nev} még mindig néma helyfoglaló (#1526)"
            )

    def test_a_masolas_menupont_a_kijelolt_kepeket_teszi_fel(
        self, qml_app, qt_app
    ):
        from PySide6.QtCore import QMetaObject, QObject, Qt

        window, controller, _lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        qt_app.processEvents()

        vezerlo = engine.rootContext().contextProperty("fileOpsController")
        vezerlo._vagolap_adat = None

        tetel = window.findChild(QObject, "menuEditCopy")
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert vezerlo._vagolap_adat is not None, (
            "a Másolás menüpont nem tett semmit a vágólapra — a bekötés "
            "némán hatástalan (#1526)"
        )
        urlek = [u.toLocalFile() for u in vezerlo._vagolap_adat.urls()]
        assert urlek, "üres URL-lista"
        assert urlek[0].endswith(".jpg")


class TestFokuszErzekenyBillentyu:
    """#1571: a Ctrl+C a RÁCSON a fájlokat másolja, SZÖVEGMEZŐBEN a mezőé.

    A kézenfekvő megoldás valódi regressziót okozna: egy sima
    `WindowShortcut` elvenné a másolást a szövegmezőktől, tehát átnevezés,
    keresés vagy feliratszerkesztés közben a felhasználó nem tudná a beírt
    szöveget másolni. A kapu ezért a fókusz."""

    def test_szovegmezo_fokusszal_a_billentyu_ki_van_kapcsolva(
        self, qml_app, qt_app
    ):
        from PySide6.QtCore import QObject

        window, _controller, _lib, _engine = qml_app
        mezo = window.findChild(QObject, "searchField")
        assert mezo is not None, "searchField nem található"

        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert window.property("_szovegmezoneVanFokusz") is True, (
            "a keresőmező fókuszát nem ismerte fel a kapu — a Ctrl+C "
            "elvenné a másolást a mezőtől (#1571)"
        )

    def test_racson_a_billentyu_el(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        qt_app.processEvents()

        assert window.property("_szovegmezoneVanFokusz") is False, (
            "szövegmező nélkül is mezőfókuszt jelez a kapu — a rácson "
            "sosem sülne el a Ctrl+C (#1571)"
        )
