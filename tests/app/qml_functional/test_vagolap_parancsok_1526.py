"""#1526: a Szerkesztés menü vágólap-parancsai a FELÜLETRŐL — Kivágás,
Másolás, Beillesztés, Szöveg másolása/beillesztése.

## Miért a menütételről és a VÁGÓLAPRÓL mér

A jegy „Kész, ha" listájának utolsó pontja szó szerint ezt kéri: a teszt
*„a menüpontra kattint, és a vágólap tartalmát nézi — nem azt, hogy a
jelzés kiment"*. Egy `signalSpy`-os teszt zöld maradna akkor is, ha a
menüpont helyfoglaló (ez volt a #1526 kiinduló állapota: MIND AZ ÖT tétel
`placeholder: true` volt), vagy ha a vezérlő üres hasznos terhet tesz fel.

Ezért minden vizsgálat így épül fel:

1. a VALÓDI menütétel — előbb megkövetelve, hogy ne legyen helyfoglaló és
   a felhasználó rá tudjon kattintani;
2. a hatás a **rendszer-vágólapon** (`QGuiApplication.clipboard()`) vagy a
   **lemezen** mérve, nem a jelzésen.

## A vágólap fejetlen környezetben

A tesztkörnyezet `QT_QPA_PLATFORM=offscreen` (ld. `tests/app/conftest.py`),
ahol a Qt vágólapja **folyamaton belüli** — nem a felhasználó valódi
vágólapja, és nem osztott a párhuzamosan futó tesztfolyamatokkal. Mérve
(2026-08-27): a `setMimeData` → `mimeData()` körút mind a `text/uri-list`,
mind az `x-special/gnome-copied-files` adatot bájtra pontosan visszaadja,
egymás utáni írásokkal is. Ezért itt a VALÓDI vágólapot használjuk — a
`fileops_controller._clipboard()` fogantyú (a `_run`/`_stat` mintája) a
determinisztikus, vezérlő-szintű méréseké (`test_vagolap_vezerlo_1526.py`).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QMimeData, QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication

from picasapy.fileops.clipboard import (
    COPY,
    CUT,
    GNOME_COPIED_FILES,
    URI_LIST,
    parse_gnome_payload,
    paths_from_uri_list,
)
from support.qt_wait import wait_for_photo_op

import pytest


# A vágólapot tesztenként el kell engedni, különben a folyamat SIGSEGV-vel
# áll le (#1526) — az indoklás a fixture docstringjében.
pytestmark = pytest.mark.usefixtures("vagolap_elengedese")

def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elsut(window, qt_app, nev: str) -> None:
    """A VALÓDI menütétel aktiválása — előbb megkövetelve, hogy a
    felhasználó egyáltalán rá tudjon kattintani (#1526 „Kész, ha")."""
    tetel = _elem(window, nev)
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    assert tetel.property("enabled") is True, (
        f"a(z) {nev} menüpont le van tiltva — a felhasználó nem éri el"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _vagolap_urlap() -> list[str]:
    adat = QGuiApplication.clipboard().mimeData()
    return list(adat.formats()) if adat is not None else []


def _vagolap_utak() -> list[Path]:
    adat = QGuiApplication.clipboard().mimeData()
    if adat is None or not adat.hasFormat(URI_LIST):
        return []
    return paths_from_uri_list(bytes(adat.data(URI_LIST)))


def _vagolap_muvelet() -> str:
    adat = QGuiApplication.clipboard().mimeData()
    if adat is None or not adat.hasFormat(GNOME_COPIED_FILES):
        return ""
    return parse_gnome_payload(bytes(adat.data(GNOME_COPIED_FILES)))[0]


def _vagolapra(utak, muvelet: str) -> None:
    """Idegen forrás (pl. fájlkezelő) szimulálása: a teszt maga tölti fel a
    vágólapot, a termékkód megkerülésével."""
    csomag = QMimeData()
    csomag.setUrls([QUrl.fromLocalFile(str(u)) for u in utak])
    sorok = [muvelet, *(QUrl.fromLocalFile(str(u)).toString() for u in utak)]
    csomag.setData(GNOME_COPIED_FILES, "\n".join(sorok).encode("utf-8"))
    QGuiApplication.clipboard().setMimeData(csomag)


def _vagolap_urites() -> None:
    QGuiApplication.clipboard().clear()


def _mappa(controller, sor: int = 0) -> Path:
    return Path(str(controller.photos.filePathAt(sor))).parent


class TestAzOtTetelElo:
    """1. „Kész, ha": egyik vágólap-parancs sem helyfoglaló többé."""

    def test_egyik_vagolap_tetel_sem_helyfoglalo(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        for nev in (
            "menuEditCut",
            "menuEditCopy",
            "menuEditPaste",
            "menuEditCopyText",
            "menuEditPasteText",
        ):
            tetel = _elem(window, nev)
            assert not tetel.property("placeholder"), nev

    def test_kijeloles_nelkul_a_masolas_es_kivagas_TILTOTT(self, qml_app, qt_app):
        """Félkész, néma vezérlőt nem hagyunk: kijelölés nélkül nincs mit
        a vágólapra tenni, tehát a tétel legyen szürke."""
        window, _controller, _engine = qml_app
        _vagolap_urites()
        _kijelol(window, qt_app, [])
        assert _elem(window, "menuEditCut").property("enabled") is False
        assert _elem(window, "menuEditCopy").property("enabled") is False
        assert _elem(window, "menuEditCopyText").property("enabled") is False

    def test_ures_vagolapnal_a_beillesztes_TILTOTT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _vagolap_urites()
        qt_app.processEvents()
        assert _elem(window, "menuEditPaste").property("enabled") is False

    def test_fajlos_vagolapnal_a_beillesztes_ENGEDELYEZETT(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        idegen = tmp_path / "idegen.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], COPY)
        qt_app.processEvents()
        assert _elem(window, "menuEditPaste").property("enabled") is True


class TestMasolasEsKivagas:
    """2–3. „Kész, ha": a Másolás a FÁJLOKAT teszi a vágólapra, a Kivágás
    ugyanezt, de MOZGATÁSKÉNT jelölve."""

    def test_a_masolas_a_kijelolt_kep_fajljat_teszi_fel(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _vagolap_urites()
        _kijelol(window, qt_app, [0])
        vart = Path(str(controller.photos.filePathAt(0)))

        _elsut(window, qt_app, "menuEditCopy")

        assert _vagolap_utak() == [vart]

    def test_a_masolas_uri_list_formatumot_ad(self, qml_app, qt_app):
        """Enélkül egy fájlkezelőbe nem lehetne beilleszteni."""
        window, _controller, _engine = qml_app
        _vagolap_urites()
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopy")
        assert URI_LIST in _vagolap_urlap()

    def test_a_masolas_jelzese_copy(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _vagolap_urites()
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopy")
        assert _vagolap_muvelet() == COPY

    def test_a_kivagas_jelzese_cut(self, qml_app, qt_app):
        """A `Preferred DropEffect` linuxos megfelelője — enélkül a
        Kivágás semmiben nem térne el a Másolástól."""
        window, _controller, _engine = qml_app
        _vagolap_urites()
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCut")
        assert _vagolap_muvelet() == CUT

    def test_a_kivagas_NEM_torol_a_lemezrol(self, qml_app, qt_app):
        """A kivágás önmagában nem visz el semmit: a fájl csak a
        beillesztéskor költözik."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))
        _elsut(window, qt_app, "menuEditCut")
        assert forras.exists()

    def test_a_ket_muvelet_UGYANAZT_az_utat_teszi_fel(self, qml_app, qt_app):
        """A jegy lelete: a Kivágás és a Másolás ugyanazt az adatot teszi
        fel, csak a művelet-jelzésük tér el."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        _elsut(window, qt_app, "menuEditCopy")
        masolas = _vagolap_utak()
        _elsut(window, qt_app, "menuEditCut")
        assert _vagolap_utak() == masolas
        assert len(masolas) == 2

    def test_tobb_kijelolt_kep_mindegyike_felkerul(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        vart = {
            Path(str(controller.photos.filePathAt(0))),
            Path(str(controller.photos.filePathAt(1))),
        }
        _elsut(window, qt_app, "menuEditCopy")
        assert set(_vagolap_utak()) == vart


class TestBeillesztes:
    """4. „Kész, ha": a Beillesztés fájlokat fogad — KÍVÜLRŐL is."""

    def test_kivulrol_masolt_fajl_bekerul_a_mappaba(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        idegen = tmp_path / "kivulrol.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], COPY)
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditPaste")

        assert (cel / "kivulrol.jpg").exists()
        # másolás: a forrás a helyén marad
        assert idegen.exists()

    def test_kivagott_fajl_ELKOLTOZIK(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        idegen = tmp_path / "koltozo.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], CUT)
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditPaste")

        assert (cel / "koltozo.jpg").exists()
        assert not idegen.exists(), "kivágás után a forrásnak el kell tűnnie"

    def test_nevutkozeskor_MEGKERDEZ_es_nem_ir_felul(
        self, qml_app, qt_app, tmp_path
    ):
        """Adatbiztonság: azonos nevű fájl a célban nem veszhet el. A
        beillesztés a meglévő, ütközés-kezelt kötegen megy, tehát a
        „Átnevezés / Kihagyás" párbeszéd nyílik — és amíg a felhasználó nem
        döntött, a lemezen SEMMI nem változik."""
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        meglevo = cel / "a.jpg"
        eredeti_tartalom = meglevo.read_bytes()
        idegen = tmp_path / "a.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], COPY)
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditPaste")

        parbeszed = _elem(window, "duplicateNamesDialog")
        assert parbeszed.property("visible") is True, (
            "névütközésnél meg kell kérdezni, mi legyen"
        )
        assert meglevo.read_bytes() == eredeti_tartalom, "a meglévő fájl elveszett!"

    def test_az_atnevezes_valasztassal_uj_nevet_kap(
        self, qml_app, qt_app, tmp_path
    ):
        """A párbeszéd „Másodpéldányok átnevezése" gombja után a
        beillesztett példány új néven jelenik meg, a meglévő érintetlen."""
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        meglevo = cel / "a.jpg"
        eredeti_tartalom = meglevo.read_bytes()
        idegen = tmp_path / "a.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], COPY)
        qt_app.processEvents()
        _elsut(window, qt_app, "menuEditPaste")

        gomb = _elem(window, "duplicateRenameButton")
        QMetaObject.invokeMethod(
            gomb, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert meglevo.read_bytes() == eredeti_tartalom, "a meglévő fájl elveszett!"
        assert (cel / "a-1.jpg").exists(), "a beillesztett példány nem jött létre"

    def test_kivagas_utan_a_vagolap_urul(self, qml_app, qt_app, tmp_path):
        """A mozgatás egyszer hajtható végre: a fájl a második
        beillesztéskor már nem lenne a forráson."""
        window, _controller, _engine = qml_app
        idegen = tmp_path / "egyszer.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], CUT)
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditPaste")

        assert _elem(window, "menuEditPaste").property("enabled") is False

    def test_masolas_utan_a_vagolap_MARAD(self, qml_app, qt_app, tmp_path):
        """A másolás többször is beilleszthető."""
        window, _controller, _engine = qml_app
        idegen = tmp_path / "tobbszor.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra([idegen], COPY)
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditPaste")

        assert _elem(window, "menuEditPaste").property("enabled") is True

    def test_sajat_mappaba_kivagas_TELJESEN_hatastalan(self, qml_app, qt_app):
        """Ugyanabba a mappába „mozgatni" értelmetlen — a fájl NEM kaphat
        `-1` utótagot csak azért, mert saját magával ütközik, és a
        felhasználót sem szabad fölöslegesen megkérdezni róla."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))
        elotte = sorted(p.name for p in forras.parent.iterdir())

        _elsut(window, qt_app, "menuEditCut")
        _elsut(window, qt_app, "menuEditPaste")

        assert sorted(p.name for p in forras.parent.iterdir()) == elotte
        assert (
            _elem(window, "duplicateNamesDialog").property("visible") is False
        ), "saját mappába kivágásnál nincs mit eldönteni, nem szabad kérdezni"


class TestSzovegMasolasaEsBeillesztese:
    """5. „Kész, ha": a Szöveg másolása/beillesztése a FELIRATRA hat, nem a
    fájlra."""

    def test_a_szoveg_masolasa_a_feliratot_teszi_a_vagolapra(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        wait_for_photo_op(controller, lambda: controller.setCaption(0, "Nyári kép"))
        qt_app.processEvents()

        _elsut(window, qt_app, "menuEditCopyText")

        assert QGuiApplication.clipboard().text() == "Nyári kép"

    def test_a_szoveg_masolasa_NEM_tesz_fajlt_a_vagolapra(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        wait_for_photo_op(controller, lambda: controller.setCaption(0, "Csak szöveg"))
        _elsut(window, qt_app, "menuEditCopyText")
        assert _vagolap_utak() == []

    def test_a_szoveg_beillesztese_a_feliratot_irja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        QGuiApplication.clipboard().setText("Beillesztett felirat")
        qt_app.processEvents()
        _kijelol(window, qt_app, [0])

        wait_for_photo_op(
            controller, lambda: _elsut(window, qt_app, "menuEditPasteText")
        )

        assert controller.photos.captionAt(0) == "Beillesztett felirat"

    def test_a_szoveg_beillesztese_a_TELJES_kijelolesre_hat(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        QGuiApplication.clipboard().setText("Közös felirat")
        qt_app.processEvents()
        _kijelol(window, qt_app, [0, 1])

        wait_for_photo_op(
            controller, lambda: _elsut(window, qt_app, "menuEditPasteText")
        )

        assert controller.photos.captionAt(0) == "Közös felirat"
        assert controller.photos.captionAt(1) == "Közös felirat"

    def test_a_beillesztett_felirat_a_LEMEZRE_kerul(self, qml_app, qt_app):
        """A felirat igazságforrása a fájl (JPEG: IPTC) — a rács sora
        önmagában nem bizonyítja, hogy megmarad."""
        import configparser

        from picasapy.metadata import read_file_metadata

        window, controller, _engine = qml_app
        QGuiApplication.clipboard().setText("Lemezre írva")
        qt_app.processEvents()
        _kijelol(window, qt_app, [0])
        ut = Path(str(controller.photos.filePathAt(0)))

        wait_for_photo_op(
            controller, lambda: _elsut(window, qt_app, "menuEditPasteText")
        )

        ini = ut.parent / ".picasa.ini"
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        if ini.exists():
            parser.read(ini, encoding="utf-8")
        a_lemezen = read_file_metadata(ut).caption or parser.get(
            ut.name, "caption", fallback=""
        )
        assert a_lemezen == "Lemezre írva"

    def test_ures_vagolapnal_a_szoveg_beillesztese_TILTOTT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _vagolap_urites()
        qt_app.processEvents()
        _kijelol(window, qt_app, [0])
        assert _elem(window, "menuEditPasteText").property("enabled") is False
