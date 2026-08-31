"""#1638 — a „Mappa törlése…" a LOMTÁRBA teszi a mappát, nem véglegesen.

**A lelet.** A mappa-menü három „nagy" parancsa közül kettő élt (áthelyezés,
eltávolítás a Picasából), a harmadik — a tényleges törlés — néma
helyfoglaló volt. Ez a legveszélyesebb kombináció: a menü teljesnek
látszik, és épp a visszafordíthatatlan művelet az, ami nem történik meg.

A három NEM ugyanaz:

| parancs | mi történik a lemezen |
|---|---|
| Eltávolítás a Picasából… | semmi — csak kikerül a figyelésből |
| Mappa áthelyezése… | a mappa átköltözik a `.picasa.ini`-vel |
| **Mappa törlése…** | **a mappa a Lomtárba kerül** |

Az eredeti megerősítő szövege (`0x005fdc30`) kimondja a célt: *„…move the
folder »%s« and its contents to the Recycle Bin?"* — ezért **lomtár**, és
nem `delete_permanently`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from picasapy.app.fileops_controller import FileOpsController


@pytest.fixture
def mappa(tmp_path: Path) -> Path:
    """Egy mappa tartalommal — a törlésnek a tartalmat is vinnie kell."""
    konyvtar = tmp_path / "kepek" / "nyaralas"
    (konyvtar / "alalbum").mkdir(parents=True)
    (konyvtar / "a.jpg").write_bytes(b"kep")
    (konyvtar / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
    (konyvtar / "alalbum" / "b.jpg").write_bytes(b"masik")
    return konyvtar


class TestMappaTorleseALomtarba:
    def test_a_mappa_a_lomtarba_kerul_es_nem_torlodik_veglegesen(
        self, mappa, tmp_path, qt_app
    ):
        vezerlo = FileOpsController()
        lomtar = tmp_path / "lomtar"
        lomtar.mkdir()

        jelzesek: list[str] = []
        vezerlo.folderDeleted.connect(jelzesek.append)

        vezerlo.deleteFolder(str(mappa), trash_dir=lomtar)

        assert not mappa.exists(), "a mappa a helyén maradt"
        assert jelzesek == [str(mappa)], (
            f"a folderDeleted jelzés nem a törölt mappát adta: {jelzesek}"
        )
        # a lényeg: MEGVAN a lomtárban, tehát visszaállítható
        atkerult = list((lomtar / "files").iterdir())
        assert len(atkerult) == 1, (
            f"a lomtár tartalma nem egyetlen tétel: {atkerult}"
        )
        assert (atkerult[0] / "a.jpg").exists(), "a mappa tartalma elveszett"
        assert (atkerult[0] / ".picasa.ini").exists(), (
            "a `.picasa.ini` nem ment a mappával — a feliratok, címkék és "
            "arc-hozzárendelések elvesznének"
        )
        assert (atkerult[0] / "alalbum" / "b.jpg").exists(), (
            "az almappa tartalma elveszett"
        )

    def test_hiba_eseten_uzenetet_kap_a_felhasznalo_nem_nema_bukast(
        self, tmp_path, qt_app
    ):
        vezerlo = FileOpsController()
        hibak: list[tuple[str, str]] = []
        vezerlo.operationFailed.connect(
            lambda muvelet, uzenet: hibak.append((muvelet, uzenet))
        )
        torolt: list[str] = []
        vezerlo.folderDeleted.connect(torolt.append)

        vezerlo.deleteFolder(str(tmp_path / "nincs-ilyen"))

        assert torolt == [], "nem létező mappára is sikert jelentett"
        assert len(hibak) == 1, f"nem jött hibaüzenet: {hibak}"
        assert hibak[0][0] == "delete_folder"
        assert hibak[0][1], "üres hibaüzenet — a felhasználó semmit nem lát"


class TestAMenutetelElo:
    def test_a_menutetel_mar_nem_helyfoglalo(self, qml_app):
        """A #416 helyfoglaló-jelölésének le kell kerülnie — különben a
        tétel kattinthatatlan marad, akármi is van mögé kötve."""
        window, _controller, _lib, _engine = qml_app
        tetel = window.findChild(QObject, "folderMenuDeleteFolder")
        assert tetel is not None, "folderMenuDeleteFolder nem található"
        assert tetel.property("placeholder") is not True, (
            "a Mappa törlése tétel még mindig helyfoglaló — a felhasználó "
            "nem tudja megnyomni (#1638)"
        )
        assert tetel.property("enabled") is True, (
            "a tétel le van tiltva, tehát a bekötése némán hatástalan"
        )


class TestAValodiUtVegigjarasa:
    """MEMORY: a vezérlőre KATTINTS, ne a metódust hívd.

    A menütétel `triggered` jelzésétől a vezérlő hívásáig minden láncszemet
    végigjárunk — a közvetlen `fileOpsController.deleteFolder(...)` hívás
    zölden hazudna, ha a menü bekötése elromlik."""

    def test_a_menutetel_megnyitja_a_megerositest_a_mappa_nevevel(
        self, qml_app, qt_app
    ):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, lib, _engine = qml_app
        pane = window.findChild(QObject, "folderPane")
        assert pane is not None, "folderPane nem található"

        mappa = str(lib)
        QMetaObject.invokeMethod(
            pane,
            "openFolderContextMenu",
            Qt.ConnectionType.DirectConnection,
            _q_arg_str(mappa),
        )
        qt_app.processEvents()

        tetel = window.findChild(QObject, "folderMenuDeleteFolder")
        assert tetel is not None
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        parbeszed = window.findChild(QObject, "deleteFolderConfirmDialog")
        assert parbeszed is not None, (
            "a menütétel nem nyitotta meg a megerősítést — a bekötés némán "
            "hatástalan (#1638)"
        )
        assert parbeszed.property("visible") is True, (
            "a megerősítő párbeszéd nem jelent meg"
        )
        felirat = window.findChild(QObject, "deleteFolderConfirmMessageLabel")
        assert felirat is not None
        szoveg = felirat.property("text")
        assert Path(mappa).name in szoveg, (
            f"a megerősítés nem mondja meg, MELYIK mappáról van szó: {szoveg!r}"
        )
        assert "Recycle Bin" in szoveg or "Lomtár" in szoveg, (
            f"a megerősítés nem mondja ki, hogy a lomtárba kerül: {szoveg!r}"
        )


def _q_arg_str(value: str):
    from PySide6.QtCore import Q_ARG

    return Q_ARG("QVariant", value)
