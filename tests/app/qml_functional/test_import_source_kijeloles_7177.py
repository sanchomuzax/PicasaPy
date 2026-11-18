"""A #7177 kijelölt importja, gyorsbillentyűi és tippsora valós QML-ben."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.varakozas import var_feltetelre

_FOABLAK = None


def _elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    if talalat is None:
        talalat = next(
            (item for item in _bejara(gyoker) if item.objectName() == nev), None
        )
    assert talalat is not None, f"{nev} nem található"
    return talalat


def _bejara(gyoker):
    yield gyoker
    if hasattr(gyoker, "childItems"):
        for gyermek in gyoker.childItems():
            yield from _bejara(gyermek)


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0):
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _kattint(ablak, elem, qt_app):
    assert elem.property("enabled") is True, f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()} nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        _FOABLAK,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _uj_forras(gyoker: Path, nev: str, darab: int):
    source = gyoker / f"forras-{nev}"
    dest = gyoker / f"cel-{nev}"
    source.mkdir()
    dest.mkdir()
    fajlok = []
    for index in range(darab):
        fajl = source / f"kep-{index}.jpg"
        make_jpeg(fajl, taken_at=f"2024:03:{5 + index:02d} 10:00:00")
        fajlok.append(fajl)
    return source, dest, fajlok


def _beolvas(ablak, vezerlo, qt_app, source: Path, dest: Path, darab: int):
    ablak.setProperty("sourceFolder", str(source))
    ablak.setProperty("sourceFiles", [])
    ablak.setProperty("destFolder", str(dest))
    ablak.setProperty("namingMode", "date")
    ablak.setProperty("afterCopying", "leave")
    assert QMetaObject.invokeMethod(
        ablak, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    _varj(
        qt_app,
        lambda: not ablak.property("scanning")
        and int(ablak.property("previewCount")) == darab,
        "a tesztképek beolvasása nem fejeződött be",
    )
    qt_app.processEvents()


def _kepkartyak(ablak, darab: int):
    racs = _elem(ablak, "importSourcePreviewGrid")
    kartyak = {
        int(str(item.objectName()).split(":")[-1]): item
        for item in _bejara(racs)
        if str(item.objectName()).startswith("importSourceThumb:")
    }
    assert set(kartyak) == set(range(darab)), (
        f"a bélyegképrács kártyái hiányosak: {sorted(kartyak)}"
    )
    return kartyak


def _kattints_kartyara(ablak, kartya, qt_app):
    racs = _elem(ablak, "importSourcePreviewGrid")
    racs.setProperty("contentY", kartya.y())
    qt_app.processEvents()
    kartya_teteje = kartya.mapToItem(racs, QPointF(0, 0)).y()
    assert kartya_teteje >= 0 and kartya_teteje + kartya.height() <= racs.height(), (
        f"{kartya.objectName()} nem fér el a görgetett előnézeti rácsban"
    )
    kepernyokozeppont = kartya.mapToGlobal(
        QPointF(kartya.width() / 2, kartya.height() / 2)
    )
    kozep = _FOABLAK.mapFromGlobal(
        QPoint(round(kepernyokozeppont.x()), round(kepernyokozeppont.y()))
    )
    QTest.mouseClick(
        _FOABLAK,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _billentyu(ablak, kulcs, qt_app):
    foablak = _FOABLAK
    foablak.requestActivate()
    foablak.contentItem().forceActiveFocus()
    qt_app.processEvents()
    QTest.keyClick(foablak, kulcs)
    qt_app.processEvents()


def _varj_importvegere(ablak, qt_app):
    _varj(
        qt_app,
        lambda: not ablak.property("importing")
        and int(ablak.property("lastCopiedCount")) >= 0,
        "az importálás nem fejeződött be",
    )


def _ellenoriz_masolatok(dest: Path, fajlok, indexek):
    celok = list(dest.rglob("*.jpg"))
    vart_nevek = {fajlok[index].name for index in indexek}
    assert {cel.name for cel in celok} == vart_nevek
    assert len(celok) == len(indexek)


def test_valodi_kijeloles_gombok_enter_es_esc(qml_app, qt_app, tmp_path, monkeypatch):
    global _FOABLAK
    fobl, _fovezerlo, engine = qml_app
    _FOABLAK = fobl
    fobl.resize(1280, 800)
    fobl.show()
    qt_app.processEvents()
    eszkoztar_import = _elem(fobl, "toolbarImportButton")
    _kattint(fobl, eszkoztar_import, qt_app)
    ablak = _elem(fobl, "importSourceDialog")
    _varj(qt_app, lambda: ablak.property("visible"), "az importablak nem nyílt meg")
    vezerlo = engine.rootContext().contextProperty("importSourceController")

    minden = _elem(ablak, "importSourceStartButton")
    kijelolt = _elem(ablak, "importSourceSelectedButton")
    zaras = _elem(ablak, "importSourceCloseButton")
    tipp = _elem(ablak, "importSourceManualTipText")
    ablak.setProperty("namingMode", "manual")
    ablak.setProperty("manualFolderName", "")
    assert str(tipp.property("text")) == (
        "Enter new folder title or choose existing folder to continue"
    )
    ablak.setProperty("manualFolderName", "kezzel-valasztott")

    eredeti_magassag = fobl.height()
    for elteres in (-5, 0, 5):
        fobl.setProperty("height", eredeti_magassag + elteres)
        qt_app.processEvents()
        for elem in (minden, kijelolt, zaras):
            fent = elem.mapToItem(ablak, QPointF(0, 0)).y()
            assert fent >= -3 and fent + elem.height() <= ablak.height() + 3, (
                f"{elem.objectName()} kilóg {elteres:+} px ablakmagasságnál"
            )
    fobl.setProperty("height", eredeti_magassag)

    ablak.setProperty("namingMode", "date")
    assert str(tipp.property("text")) == (
        "Import into separate folders for each date taken"
    )
    ablak.setProperty("namingMode", "today")
    assert str(tipp.property("text")) == "Import into folder with today's date"
    ablak.setProperty("namingMode", "manual")

    source, dest, fajlok = _uj_forras(tmp_path, "enter-kijelolt", 3)
    ablak.setProperty("manualFolderName", "")
    _beolvas(ablak, vezerlo, qt_app, source, dest, 3)
    ablak.setProperty("namingMode", "manual")
    ablak.setProperty("manualFolderName", "kezzel-valasztott")
    assert kijelolt.property("enabled") is False
    _kattints_kartyara(ablak, _kepkartyak(ablak, 3)[0], qt_app)
    assert int(ablak.property("selectedPreviewCount")) == 1
    _kattints_kartyara(ablak, _kepkartyak(ablak, 3)[2], qt_app)
    assert str(kijelolt.property("text")) == "Import Selected (2)"
    assert kijelolt.property("enabled") is True
    assert str(tipp.property("text")) == "Click Import All or Import Selected"
    ablak.setProperty("namingMode", "date")
    _billentyu(ablak, Qt.Key.Key_Return, qt_app)
    _varj_importvegere(ablak, qt_app)
    _ellenoriz_masolatok(dest, fajlok, (0, 2))

    source, dest, fajlok = _uj_forras(tmp_path, "enter-egy", 3)
    _beolvas(ablak, vezerlo, qt_app, source, dest, 3)
    _kattints_kartyara(ablak, _kepkartyak(ablak, 3)[1], qt_app)
    _billentyu(ablak, Qt.Key.Key_Return, qt_app)
    _varj_importvegere(ablak, qt_app)
    _ellenoriz_masolatok(dest, fajlok, (0, 1, 2))

    source, dest, fajlok = _uj_forras(tmp_path, "import-all", 3)
    _beolvas(ablak, vezerlo, qt_app, source, dest, 3)
    _kattint(ablak, minden, qt_app)
    _varj_importvegere(ablak, qt_app)
    _ellenoriz_masolatok(dest, fajlok, (0, 1, 2))

    source, dest, fajlok = _uj_forras(tmp_path, "kattintott-kijelolt", 3)
    _beolvas(ablak, vezerlo, qt_app, source, dest, 3)
    kartyak = _kepkartyak(ablak, 3)
    _kattints_kartyara(ablak, kartyak[0], qt_app)
    _kattints_kartyara(ablak, kartyak[1], qt_app)
    _kattint(ablak, kijelolt, qt_app)
    _varj_importvegere(ablak, qt_app)
    _ellenoriz_masolatok(dest, fajlok, (0, 1))

    source, dest, _fajlok = _uj_forras(tmp_path, "esc-import-kozben", 1)
    _beolvas(ablak, vezerlo, qt_app, source, dest, 1)
    import picasapy.app.import_source_controller as import_modul

    eredeti_masolas = import_modul.copy_photo
    masolas_elindult = threading.Event()
    folytatas = threading.Event()

    def lassu_masolas(*args, **kwargs):
        masolas_elindult.set()
        assert folytatas.wait(10), "az Esc-próba nem engedte tovább az importot"
        return eredeti_masolas(*args, **kwargs)

    monkeypatch.setattr(import_modul, "copy_photo", lassu_masolas)
    try:
        _kattint(ablak, minden, qt_app)
        assert masolas_elindult.wait(10), "a háttérmásolás nem indult el"
        qt_app.processEvents()
        assert ablak.property("importing") is True
        _billentyu(ablak, Qt.Key.Key_Escape, qt_app)
        assert ablak.property("visible") is False
        assert vezerlo.waitForBackgroundWorkers(0.01) is False, (
            "az Esc megszakította a háttérben futó importot"
        )
    finally:
        folytatas.set()
    assert vezerlo.waitForBackgroundWorkers(30.0), "a másolószál nem állt le"
    qt_app.processEvents()
    assert len(list(dest.rglob("*.jpg"))) == 1
    assert minden.property("enabled") is True
    assert kijelolt.property("enabled") is False
    assert zaras.property("enabled") is True
