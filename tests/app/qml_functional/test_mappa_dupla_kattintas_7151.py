"""#7151: a mappalista dupla kattintása az almappa nélküli mappán a Folder
Properties ablakot nyitja.

Az eredetiben a `0x00765d30` az `lb_predouble` eseményre, 1-es vagy 5-ös
rekordtípusnál és `+0x18 == 0` esetén a `0x006db580` Folder Properties útját
indítja. A fizikai mappasor rekordja 5-ös, ha nincs gyermeke, és 6-os, ha van;
a 6-os sor a `0x004ab9a0` kinyit/becsuk ágára fut, tulajdonságablak nélkül.

## Mit mér

VALÓDI dupla kattintás (`QTest.mouseDClick`) a kirajzolt sorra, a függvény
hívása nélkül:

* lapos lista: a mappa sorára az ablak a mappa nevével, dátumával, helyével és
  leírásával nyílik, és a KIRAJZOLT mezők is ezt mutatják;
* fa nézet: ugyanez az almappa nélküli sorra; az almappás sorra a dupla
  kattintás kinyit/becsuk, ablak nincs;
* az egyszeres kattintás csak kijelöl; a nyíl, a jobb gombos menü és a
  fejléc/gyökér/év sorok viselkedése változatlan;
* mentés-szűrő módban (a sor ott pipa) a dupla kattintás nem nyit ablakot.

## Amit NEM mér

Az ablak képi egyezését az eredetivel: a Folder Properties kirajzolását a
saját tesztjei mérik (`test_mappa_datum_naptar_4494.py`). Itt azt mérjük, hogy
az ablak az adott mappa adataival megnyílik, és a mezők kirajzolt szövege az.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QLocale, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app

#: mappa -> képek. A `fotok` almappás (van `fotok/reszlet`), a `levelnev` és a
#: `fotok/reszlet` almappa nélküli.
_MAPPAK = {
    "fotok": ("a.jpg",),
    "fotok/reszlet": ("b.jpg",),
    "levelnev": ("c.jpg",),
}
#: mappa -> (ISO dátum, a kirajzolt dátummező szövege magyar nyelven). A
#: `fotok/reszlet` KÜLÖN évben áll: a lapos lista csak akkor rajzol év-fejlécet,
#: ha legalább két különböző év van.
_DATUMOK = {
    "levelnev": ("2023-05-17", "2023. 05. 17."),
    "fotok": ("2023-05-17", "2023. 05. 17."),
    "fotok/reszlet": ("2021-03-04", "2021. 03. 04."),
}
_LEIRAS = "Nyári kirándulás a tónál"
_HELY = "Balatonfüred"


def _keszit(lib) -> None:
    for mappa, fajlok in _MAPPAK.items():
        (lib / mappa).mkdir(parents=True, exist_ok=True)
        for fajl in fajlok:
            make_jpeg(lib / mappa / fajl, size=(64, 48))


@pytest.fixture
def hu_locale():
    """A magyar nyelvi beállítás: a dátummező szövege ettől függ."""
    eredeti = QLocale()
    QLocale.setDefault(QLocale(QLocale.Language.Hungarian, QLocale.Country.Hungary))
    yield
    QLocale.setDefault(eredeti)


@pytest.fixture
def app(qt_app, tmp_path, hu_locale):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszit)
    window, controller, engine = next(gen)
    try:
        window.resize(1280, 900)
        window.show()
        qt_app.processEvents()
        lib = tmp_path / "kepek"
        for mappa, (iso, _hu) in _DATUMOK.items():
            ut = str(lib / mappa)
            controller.setFolderDate(ut, iso)
            controller.setFolderDescriptionOf(ut, _LEIRAS + " " + mappa)
            controller.setFolderLocationOf(ut, _HELY + " " + mappa)
        _varj_stabil_lista(window, controller, qt_app)
        yield window, controller, engine, lib
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


# -- segédek: a KIRAJZOLT elemek, valódi egér --------------------------------


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _tenyleg_latszik(elem: QQuickItem) -> bool:
    if elem.width() <= 0 or elem.height() <= 0:
        return False
    os_ = elem
    while os_ is not None:
        if not os_.isVisible():
            return False
        os_ = os_.parentItem()
    return True


def _latszo(window, nev: str) -> list[QQuickItem]:
    talalat = [
        e for e in _walk(window.contentItem())
        if e.objectName() == nev and _tenyleg_latszik(e)
    ]
    return sorted(talalat, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _egyetlen_sor(window, qt_app, keres, leiras: str) -> QQuickItem:
    """Megvárja, hogy pontosan EGY látható sor legyen: a nézet átépülése (kapcsolás,
    átrendezés) után a delegátum egy pillanatra méret nélkül állhat."""
    sorok: list[QQuickItem] = []

    def van() -> bool:
        sorok[:] = keres()
        return len(sorok) == 1

    assert varj_feltetelre(qt_app, van), (
        f"{leiras} nem látszik ({len(sorok)} db)"
    )
    return sorok[0]


def _lapos_sor(window, qt_app, ut: str) -> QQuickItem:
    """A lapos lista mappasorának egérterülete (a sor `folderPath`-ja szerint)."""
    return _egyetlen_sor(
        window, qt_app,
        lambda: [
            e for e in _latszo(window, "folderRowMouse")
            if e.property("folderPath") == ut
        ],
        f"a lapos lista {ut} sora",
    )


def _fa_sor(window, qt_app, ut: str) -> QQuickItem:
    return _egyetlen_sor(
        window, qt_app,
        lambda: _latszo(window, "hierRowMouse:" + ut),
        f"a fa {ut!r} sora",
    )


def _kozep(elem: QQuickItem) -> QPoint:
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    return QPoint(round(kozep.x()), round(kozep.y()))


def _egyszeres(window, qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    pont = _kozep(elem)
    QTest.mouseMove(window, pont)
    qt_app.processEvents()
    QTest.mouseClick(window, gomb, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _dupla(window, qt_app, elem) -> None:
    """VALÓDI dupla kattintás: a hover előbb odaér, utána nyom, elenged, nyom, elenged."""
    pont = _kozep(elem)
    QTest.mouseMove(window, pont)
    qt_app.processEvents()
    QTest.mouseDClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()


def _parbeszed(window) -> QObject:
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None, "a Folder Properties ablak nem található"
    return dialog


def _nyitva(window) -> bool:
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    return dialog is not None and dialog.property("opened") is True


def _zar(window, qt_app) -> None:
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    if dialog is not None and dialog.property("opened") is True:
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()
        varj_feltetelre(qt_app, lambda: dialog.property("opened") is False)


def _mezo(window, nev: str) -> str:
    mezo = window.findChild(QObject, nev)
    assert mezo is not None, f"{nev} mező nem található"
    return str(mezo.property("text"))


def _fa(engine):
    return engine.rootContext().contextProperty("folderHierarchyController")


def _fanezet(engine, qt_app) -> None:
    """Fa nézet, egyszerűsített alakban (a köztes, üres szinteket elhagyja, így
    a sorok a látható hasábon belül állnak), minden ág kinyitva."""
    fa = _fa(engine)
    fa.setSimplified(True)
    fa.setTreeView(True)
    fa.expandAll()
    qt_app.processEvents()
    assert varj_feltetelre(
        qt_app,
        lambda: any(
            str(r["path"]).endswith("/fotok/reszlet") for r in fa.property("rows")
        ),
    ), "a fa nem mutatja a fotok/reszlet sort kinyitva"


def _fa_sor_adat(engine, ut: str) -> dict:
    sorok = [s for s in _fa(engine).property("rows") if s["path"] == ut]
    assert len(sorok) == 1, f"a fa modelljében nincs egyértelmű {ut} sor"
    return sorok[0]


def _a_mappa_adataival_nyilt(window, qt_app, mappa: str, ut: str) -> None:
    """A Folder Properties az ADOTT mappa adataival nyílt meg: a tulajdonságok
    ÉS a kirajzolt mezők is."""
    assert varj_feltetelre(qt_app, lambda: _nyitva(window)), (
        "a dupla kattintás nem nyitotta meg a Folder Properties ablakot"
    )
    dialog = _parbeszed(window)
    assert dialog.property("mode") == "folder"
    assert dialog.property("newFolderCreation") is False
    assert dialog.property("folderPath") == ut
    assert dialog.property("folderName") == mappa.rsplit("/", 1)[-1]
    iso, hu = _DATUMOK[mappa]
    assert dialog.property("currentDate") == iso
    assert dialog.property("folderLocation") == _HELY + " " + mappa
    assert dialog.property("currentDescription") == _LEIRAS + " " + mappa
    assert _mezo(window, "folderPropertiesNameField") == mappa.rsplit("/", 1)[-1]
    assert _mezo(window, "folderPropertiesDateField") == hu
    assert _mezo(window, "folderPropertiesLocation") == _HELY + " " + mappa
    assert _mezo(window, "folderPropertiesDescription") == _LEIRAS + " " + mappa


def _sorrend(window) -> list[tuple[str, int]]:
    """A lapos lista kirajzolt mappasorai és fejlécei, fentről lefelé."""
    elemek = [
        (str(e.property("kind")) + ":" + str(e.property("name")),
         round(e.mapToScene(QPointF(0, 0)).y()))
        for e in _walk(window.contentItem())
        if e.property("kind") in ("year", "folder")
        and e.property("isHeaderRow") is not None and _tenyleg_latszik(e)
    ]
    return sorted(elemek, key=lambda e: e[1])


def _varj_stabil_lista(window, controller, qt_app) -> None:
    """Megvárja, amíg a háttér-újraszinkron (a dátum-felülírás indítja) lefut és
    a lapos lista átrendeződése megáll. Enélkül a dupla kattintás első
    kattintása és a sorkeresés közt a sorok elmozdulnak, és a másodikra másik
    sor kerülhet az egér alá (ingadozó teszt)."""
    assert varj_feltetelre(
        qt_app, lambda: controller.waitForBackgroundWorkers(0.05)
    ), "a háttérmunkák nem értek véget"
    assert varj_feltetelre(
        qt_app,
        lambda: {"year:2023", "year:2021"} <= {n for n, _y in _sorrend(window)},
        60.0,
    ), "a lapos lista nem rendeződött át a felülírt dátumok szerint"
    elozo = None
    for _ in range(20):
        qt_app.processEvents()
        mostani = _sorrend(window)
        if mostani == elozo:
            return
        elozo = mostani
        QTest.qWait(50)
    raise AssertionError("a lapos lista sorrendje nem állt meg")


# -- lapos lista ------------------------------------------------------------


class TestLaposLista:
    @pytest.mark.parametrize("mappa", ["levelnev", "fotok"])
    def test_a_mappasor_dupla_kattintasa_megnyitja_a_folder_propertiest(
        self, app, qt_app, mappa
    ):
        window, _c, _e, lib = app
        ut = str(lib / mappa)
        assert not _nyitva(window)

        _dupla(window, qt_app, _lapos_sor(window, qt_app, ut))

        _a_mappa_adataival_nyilt(window, qt_app, mappa, ut)
        _zar(window, qt_app)

    def test_az_egyszeres_kattintas_csak_kijelol(self, app, qt_app):
        window, controller, _e, lib = app
        ut = str(lib / "levelnev")

        _egyszeres(window, qt_app, _lapos_sor(window, qt_app, ut))

        assert varj_feltetelre(
            qt_app, lambda: controller.property("currentFolder") == ut
        ), "az egyszeres kattintás nem jelölte ki a mappát"
        assert not _nyitva(window), "az egyszeres kattintás ablakot nyitott"

    def test_a_dupla_kattintas_a_mappat_is_kijeloli(self, app, qt_app):
        window, controller, _e, lib = app
        ut = str(lib / "levelnev")

        _dupla(window, qt_app, _lapos_sor(window, qt_app, ut))

        assert varj_feltetelre(qt_app, lambda: _nyitva(window))
        assert controller.property("currentFolder") == ut
        _zar(window, qt_app)

    def test_a_jobb_gombos_menu_valtozatlan(self, app, qt_app):
        window, _c, _e, lib = app
        ut = str(lib / "levelnev")

        _egyszeres(window, qt_app, _lapos_sor(window, qt_app, ut), Qt.MouseButton.RightButton)

        menu = window.findChild(QObject, "folderContextMenu")
        assert menu is not None
        assert varj_feltetelre(
            qt_app, lambda: menu.property("opened") is True
        ), "a jobb gombos kattintás nem nyitotta meg a mappa menüjét"
        assert not _nyitva(window), "a jobb gombos kattintás ablakot nyitott"
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()

    def test_az_ev_fejlec_dupla_kattintasa_nem_nyit_ablakot(self, app, qt_app):
        window, controller, _e, _lib = app
        evek = [
            e for e in _walk(window.contentItem())
            if e.property("kind") == "year" and _tenyleg_latszik(e)
        ]
        assert len(evek) >= 2, "a lapos listán nem látszanak az év-fejlécek"
        elotte = controller.property("currentFolder")

        for fejlec in evek:
            _dupla(window, qt_app, fejlec)

        assert not _nyitva(window), "az év-fejlécre dupla kattintás ablakot nyitott"
        assert controller.property("currentFolder") == elotte

    def test_a_rejtett_mappak_fejlec_dupla_kattintasa_nem_nyit_ablakot(
        self, app, qt_app
    ):
        window, controller, _e, lib = app
        controller.toggleFolderHidden(str(lib / "levelnev"))
        ajanlat = window.findChild(QObject, "hiddenPasswordOfferDialog")
        if ajanlat is not None and varj_feltetelre(
            qt_app, lambda: ajanlat.property("visible") is True, 2.0
        ):
            nem = window.findChild(QObject, "hiddenPasswordOfferNoButton")
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                _kozep(nem),
            )
            qt_app.processEvents()
        controller.setShowHidden(True)
        assert varj_feltetelre(
            qt_app, lambda: len(_latszo(window, "hiddenCollectionHeader")) == 1
        ), "a Rejtett mappák fejléce nem jelent meg"

        _dupla(window, qt_app, _latszo(window, "hiddenCollectionHeader")[0])

        assert not _nyitva(window), "a Rejtett mappák fejlécére dupla kattintás ablakot nyitott"

    def test_a_beepitett_sor_dupla_kattintasa_nem_nyit_ablakot(self, app, qt_app):
        window, _c, _e, _lib = app
        beepitett = _egyetlen_sor(
            window, qt_app,
            lambda: _latszo(window, "starredItem"),
            "a Csillagozott fotók sor",
        )

        _dupla(window, qt_app, beepitett)

        assert not _nyitva(window), "a beépített sor dupla kattintása ablakot nyitott"


# -- fa nézet ---------------------------------------------------------------


class TestFaNezet:
    @pytest.mark.parametrize("mappa", ["levelnev", "fotok/reszlet"])
    def test_az_almappa_nelkuli_sor_dupla_kattintasa_megnyitja_a_folder_propertiest(
        self, app, qt_app, mappa
    ):
        window, controller, engine, lib = app
        _fanezet(engine, qt_app)
        ut = str(lib / mappa)
        assert _fa_sor_adat(engine, ut)["hasChildren"] is False

        _dupla(window, qt_app, _fa_sor(window, qt_app, ut))

        _a_mappa_adataival_nyilt(window, qt_app, mappa, ut)
        _zar(window, qt_app)

    def test_az_almappas_sor_dupla_kattintasa_kinyit_becsuk_ablak_nelkul(
        self, app, qt_app
    ):
        window, _c, engine, lib = app
        _fanezet(engine, qt_app)
        ut = str(lib / "fotok")
        elotte = _fa_sor_adat(engine, ut)
        assert elotte["hasChildren"] is True

        _dupla(window, qt_app, _fa_sor(window, qt_app, ut))

        assert varj_feltetelre(
            qt_app, lambda: _fa_sor_adat(engine, ut)["expanded"] != elotte["expanded"]
        ), "az almappás sor dupla kattintása nem nyitott/csukott"
        assert not _nyitva(window), "az almappás sor dupla kattintása ablakot nyitott"

    def test_az_egyszeres_kattintas_csak_kijelol(self, app, qt_app):
        window, controller, engine, lib = app
        _fanezet(engine, qt_app)
        ut = str(lib / "levelnev")

        _egyszeres(window, qt_app, _fa_sor(window, qt_app, ut))

        assert varj_feltetelre(
            qt_app, lambda: controller.property("currentFolder") == ut
        ), "az egyszeres kattintás nem jelölte ki a mappát"
        assert not _nyitva(window), "az egyszeres kattintás ablakot nyitott"

    def test_a_nyil_kattintasa_valtozatlanul_kinyit_becsuk(self, app, qt_app):
        window, _c, engine, lib = app
        _fanezet(engine, qt_app)
        ut = str(lib / "fotok")
        elotte = _fa_sor_adat(engine, ut)["expanded"]
        nyil = _egyetlen_sor(
            window, qt_app,
            lambda: _latszo(window, "hierArrowMouse:" + ut),
            "az almappás sor nyila",
        )

        _egyszeres(window, qt_app, nyil)

        assert varj_feltetelre(
            qt_app, lambda: _fa_sor_adat(engine, ut)["expanded"] != elotte
        ), "a nyíl kattintása nem nyitott/csukott"
        assert not _nyitva(window)

    def test_a_jobb_gombos_menu_valtozatlan(self, app, qt_app):
        window, _c, engine, lib = app
        _fanezet(engine, qt_app)
        ut = str(lib / "levelnev")

        _egyszeres(window, qt_app, _fa_sor(window, qt_app, ut), Qt.MouseButton.RightButton)

        menu = window.findChild(QObject, "folderContextMenu")
        assert menu is not None
        assert varj_feltetelre(
            qt_app, lambda: menu.property("opened") is True
        ), "a jobb gombos kattintás nem nyitotta meg a mappa menüjét"
        assert not _nyitva(window)
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()

    def test_a_gyokersor_viselkedese_valtozatlan_ablak_nelkul(self, app, qt_app):
        """A gyökérsoron az egyszeres kattintás kapcsol (ez a sor egyetlen
        kezelése), a dupla kattintás az első kattintás kapcsolását még
        egyszer kapcsolja: a nettó állapot változatlan. Ablak sosem nyílik."""
        window, _c, engine, _lib = app
        _fanezet(engine, qt_app)
        gyoker = [s for s in _fa(engine).property("rows") if s["kind"] == "root"]
        assert len(gyoker) == 1, "a fa gyökérsora nincs a modellben"
        ut = gyoker[0]["path"]
        elotte = gyoker[0]["expanded"]

        _egyszeres(window, qt_app, _fa_sor(window, qt_app, ut))
        assert varj_feltetelre(
            qt_app, lambda: _fa_sor_adat(engine, ut)["expanded"] != elotte
        ), "a gyökérsor egyszeres kattintása nem kapcsol"
        assert not _nyitva(window)
        _egyszeres(window, qt_app, _fa_sor(window, qt_app, ut))
        assert varj_feltetelre(
            qt_app, lambda: _fa_sor_adat(engine, ut)["expanded"] == elotte
        )

        _dupla(window, qt_app, _fa_sor(window, qt_app, ut))

        assert not _nyitva(window), "a gyökérsor dupla kattintása ablakot nyitott"
        assert _fa_sor_adat(engine, ut)["expanded"] == elotte
