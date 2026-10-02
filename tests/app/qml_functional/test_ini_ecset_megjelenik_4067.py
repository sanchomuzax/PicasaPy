"""Az ecset QML-kötése a teljes szerkesztési láncot követi (#4067).

A tesztek a valódi `Main.qml`-t, `EditController`-t és főablakot használják.
Az ecsetblokk renderelését a Brush Size sín szöveg nélküli pontjain mérik:
az ablak képe normál és nullázott ecsetblokk-átlátszatlansággal készül.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QColor

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


_VAMPIRE = "ReanimatedEyeColor=1,6.000000,20.000000;"
_BOOST = "Boost=1,50.000000;"
_PIXELATE = "Pixelate=1,20.000000;"
_SOFTEN = "Soften=1,50.000000,50.000000;"
_PICNIK_TINT = "PicnikTint=1,0.000000,80cfff;"
_INI_EFFEKTEK = (
    ("a.jpg", _VAMPIRE, True),
    ("b.jpg", _BOOST, False),
    ("c.jpg", _PIXELATE, False),
    ("d.jpg", _SOFTEN, False),
    ("e.jpg", _PICNIK_TINT, False),
)


def _gyerek(gyoker, nev: str) -> QObject:
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"a valódi Main.qml-fából hiányzik: {nev}"
    return elem


def _filters_sor(ertekek) -> str:
    return "\n\n".join(
        f"[{nev}]\nfilters={lanc}" for nev, lanc, _tamogatott in ertekek
    ) + "\n"


def _foablak_ini_lancok(qml_app, qt_app, tmp_path, ertekek):
    ablak, controller, engine = qml_app
    konyvtar = tmp_path / "kepek"
    for nev, _lanc, _tamogatott in ertekek:
        ut = konyvtar / nev
        if not ut.exists():
            make_jpeg(ut, size=(320, 160))

    (konyvtar / ".picasa.ini").write_text(
        _filters_sor(ertekek), encoding="utf-8"
    )
    # A fixture után létrejött képek kerüljenek a valódi könyvtármodellbe.
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, konyvtar)
    controller._reload()
    controller.selectFolder(str(konyvtar))
    qt_app.processEvents()

    edit = engine.rootContext().contextProperty("editController")
    ablak.setProperty("viewerOpen", True)
    qt_app.processEvents()
    viewer = _gyerek(ablak, "photoViewer")
    _valts_fotora(viewer, qt_app, ertekek[0][0])
    return ablak, viewer, edit


def _valts_fotora(viewer, qt_app, nev: str) -> None:
    modell = viewer.property("photosModel")
    sorok = int(modell.rowCount())
    sor = next(
        index
        for index in range(sorok)
        if Path(modell.filePathAt(index)).name == nev
    )
    viewer.setProperty("currentIndex", sor)
    qt_app.processEvents()


def _ecset_keppontok(ablak, ecset, csuszka, qt_app):
    """Három szöveg nélküli sínpont normál és átlátszó ecsetblokknál."""
    ablak.show()
    ecset.setProperty("opacity", 1.0)
    qt_app.processEvents()
    rajzolt = ablak.grabWindow()
    assert not rajzolt.isNull(), "a valódi főablak képe nem renderelődött"

    ecset.setProperty("opacity", 0.0)
    qt_app.processEvents()
    atlatszo = ablak.grabWindow()
    ecset.setProperty("opacity", 1.0)
    qt_app.processEvents()
    assert not atlatszo.isNull(), "az átlátszó főablak képe nem renderelődött"

    hatter = csuszka.property("background")
    assert hatter is not None, "a Brush Size csúszkának nincs sínje"
    vart_sin = QColor(hatter.property("color"))
    arany = rajzolt.devicePixelRatio() or 1.0
    meresek = []
    for x_arany in (0.70, 0.75, 0.80):
        hely = csuszka.mapToItem(
            ablak.contentItem(), QPointF(csuszka.width() * x_arany, csuszka.height() / 2)
        )
        x, y = round(hely.x() * arany), round(hely.y() * arany)
        teljes = rajzolt.pixelColor(x, y)
        nullazott = atlatszo.pixelColor(x, y)
        meresek.append((teljes, nullazott))
        if bool(ecset.property("ecsetLathato")):
            assert teljes == vart_sin, (
                "a csúszka sínjének szöveg nélküli képpontja nem jelent meg: "
                f"{teljes.name()} != {vart_sin.name()}"
            )
    return meresek


def _ellenorizd_ecset_allapot(ablak, edit, panel, ecset, csuszka, festo, qt_app, vart, nev):
    assert bool(edit.paintMaskSupported) is vart, f"Python-állapot: {nev}"
    assert bool(ecset.property("ecsetLathato")) is vart, f"QML-kötés: {nev}"
    assert bool(ecset.property("visible")) is vart, f"ecsetblokk láthatósága: {nev}"
    assert bool(festo.property("aktiv")) is vart, f"festő-réteg kötése: {nev}"
    assert bool(festo.property("visible")) is vart, f"festő-réteg láthatósága: {nev}"
    assert bool(festo.property("enabled")) is vart, f"festő-réteg engedélyezése: {nev}"

    keppontok = _ecset_keppontok(ablak, ecset, csuszka, qt_app)
    eltér = [teljes != nullazott for teljes, nullazott in keppontok]
    assert all(eltér) is vart, (
        f"a renderelt ecsetblokk képpont-különbsége nem a várt ({nev}); "
        f"eltérő sínpontok: {eltér!r}"
    )


def _ecset_vezerlok(ablak, qt_app):
    panel = _gyerek(ablak, "viewerEditorPanel")
    # A Vámpírszemnek nincs saját effektcsempéje; a valódi paraméterpanelt
    # programból nyitjuk ki, egérkattintás nélkül.
    panel.setProperty("paramPanelActive", True)
    qt_app.processEvents()
    return (
        panel,
        _gyerek(ablak, "effectParamBrushBlock"),
        _gyerek(ablak, "effectParamBrushSlider"),
        _gyerek(ablak, "paintMaskArea"),
    )


def test_ini_effektmatrix_a_valodi_foablakban(qml_app, qt_app, tmp_path):
    ablak, viewer, edit = _foablak_ini_lancok(
        qml_app, qt_app, tmp_path, _INI_EFFEKTEK
    )
    panel = _gyerek(ablak, "viewerEditorPanel")
    festo = _gyerek(ablak, "paintMaskArea")

    # A #3541 előtti QML-előzmény is közvetlenül a paintMaskSupported
    # értékére kötötte a festő-réteget, a paraméterpanel nyitásától függetlenül.
    assert panel.property("paramPanelActive") is False
    assert festo.property("aktiv") is True
    assert festo.property("enabled") is True

    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)
    for nev, _lanc, vart in _INI_EFFEKTEK:
        _valts_fotora(viewer, qt_app, nev)
        _ellenorizd_ecset_allapot(
            ablak, edit, panel, ecset, csuszka, festo, qt_app, vart, nev
        )


@pytest.mark.parametrize(
    ("eset", "indulo_lanc", "uj_lanc", "vart"),
    (
        ("ii-b", _VAMPIRE, _PIXELATE, False),
        ("ii-c", _PIXELATE, _VAMPIRE, True),
    ),
)
def test_azonos_foto_ujranyitasa_az_ini_lancvaltozasa_utan(
    qml_app, qt_app, tmp_path, eset, indulo_lanc, uj_lanc, vart
):
    egy_foto = (("a.jpg", indulo_lanc, indulo_lanc == _VAMPIRE),)
    ablak, viewer, edit = _foablak_ini_lancok(qml_app, qt_app, tmp_path, egy_foto)
    window_panel = _gyerek(ablak, "viewerEditorPanel")
    window_panel.setProperty("paramPanelActive", True)
    qt_app.processEvents()
    ecset = _gyerek(ablak, "effectParamBrushBlock")
    csuszka = _gyerek(ablak, "effectParamBrushSlider")
    festo = _gyerek(ablak, "paintMaskArea")

    ablak.setProperty("viewerOpen", False)
    qt_app.processEvents()
    assert edit.property("previewSource") == ""
    (tmp_path / "kepek" / ".picasa.ini").write_text(
        _filters_sor((("a.jpg", uj_lanc, vart),)), encoding="utf-8"
    )
    ablak.setProperty("viewerOpen", True)
    qt_app.processEvents()
    viewer = _gyerek(ablak, "photoViewer")
    _valts_fotora(viewer, qt_app, "a.jpg")
    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)

    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, vart, eset
    )


def test_ket_visszavonas_es_ujra_frissiti_a_kotest(qml_app, qt_app, tmp_path):
    lancok = (("a.jpg", f"{_VAMPIRE}{_BOOST}", True),)
    ablak, _viewer, edit = _foablak_ini_lancok(qml_app, qt_app, tmp_path, lancok)
    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)
    jelzeskori_allapotok = []
    edit.paintMaskChanged.connect(
        lambda: jelzeskori_allapotok.append(bool(edit.paintMaskSupported))
    )

    edit.undo()  # A Boost lekerül, a Vámpírszem és az ecset marad.
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "iii-c: első Visszavonás"
    )
    edit.redo()
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "iii-c: Újra"
    )

    edit.undo()
    edit.undo()  # A Boost, majd a Vámpírszem is lekerül: üres a lánc.
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, False, "iii-c: két Visszavonás"
    )
    assert jelzeskori_allapotok == [False], (
        "a festhetőség elvesztésekor egyszer, az új állapotot jelezze: "
        f"{jelzeskori_allapotok!r}"
    )

    edit.redo()
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "iii-c: Újra visszahozza"
    )
    assert jelzeskori_allapotok == [False, True]


def test_fotovaltozas_a_b_a_frissit_es_elhajitja_a_festest(qml_app, qt_app, tmp_path):
    lancok = (("a.jpg", _VAMPIRE, True), ("b.jpg", _PIXELATE, False))
    ablak, viewer, edit = _foablak_ini_lancok(qml_app, qt_app, tmp_path, lancok)
    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "a→b→a: a"
    )
    edit.paintStroke(0.25, 0.5)
    assert len(edit._paint_mask.vonasok) == 1

    _valts_fotora(viewer, qt_app, "b.jpg")
    assert edit._paint_mask.ures, "a festett maszk fotóváltáskor nem ürült ki"
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, False, "a→b→a: b"
    )
    _valts_fotora(viewer, qt_app, "a.jpg")
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "a→b→a: vissza a"
    )


def test_boost_a_vampirszerem_mellett_megtartja_az_ecsetet(qml_app, qt_app, tmp_path):
    ablak, _viewer, edit = _foablak_ini_lancok(
        qml_app, qt_app, tmp_path, (("a.jpg", _VAMPIRE, True),)
    )
    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)
    jelzesek = []
    edit.paintMaskChanged.connect(lambda: jelzesek.append(bool(edit.paintMaskSupported)))

    edit.applyEffect("boost")
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, True, "Vámpírszem + Boost"
    )
    assert jelzesek == [], "azonos paintMaskSupported értéknél ne legyen fölös jelzés"


def test_pixelate_melletti_boost_nem_kap_ecsetet(qml_app, qt_app, tmp_path):
    ablak, _viewer, edit = _foablak_ini_lancok(
        qml_app, qt_app, tmp_path, (("a.jpg", _PIXELATE, False),)
    )
    panel, ecset, csuszka, festo = _ecset_vezerlok(ablak, qt_app)
    jelzesek = []
    edit.paintMaskChanged.connect(lambda: jelzesek.append(bool(edit.paintMaskSupported)))

    edit.applyEffect("boost")
    qt_app.processEvents()
    _ellenorizd_ecset_allapot(
        ablak, edit, panel, ecset, csuszka, festo, qt_app, False, "Pixelate + Boost"
    )
    assert jelzesek == [], "a festhetetlen lánc revíziója ne jelezzen ecsetváltozást"
