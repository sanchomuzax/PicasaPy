"""A Név nélküliek KIBONTOTT nézete VALÓDI kattintással (#5214).

A táblázat (picasa-colab-jobs job-180 és job-183) szerint:
- csoportosítva: nincs fejléc-névmező és Ignore gomb; a csempén van saját
  mező és X;
- kibontva („Group by face"): a fejléc második sorában „Add a name" mező és
  „Ignore Selected" gomb; a csempén nincs saját mező és X.

Lefedve:
- a váltógomb valódi kattintása kibontja, és a felirat, az útmutató és a
  láthatóság a táblázat szerint jelenik meg;
- kijelölés nélkül az „Ignore Selected" tiltott;
- egy csempe kijelölése után a fejléc mezőjébe gépelt név Enterre a kijelölt
  arcot nevezi meg (a csempe útján: `nameSubmitted`);
- az „Ignore Selected" a megerősítést nyitja, és megerősítve a kijelölt arcot
  mellőzi;
- visszaváltva a csoportosított mód változatlan;
- kibontva a „N Face(s)" sorában, az útmutató fölött áll a névmező és a gomb,
  jobbra, a felső gombpár jobb széléhez igazítva;
- kibontva a csoport minden arca csempe; csoportosítva csak az előnézet.

Rontás-kontroll (cmp-vel visszaellenőrizve): a régi elhelyezés (a mezősor az
útmutató alatt) pirosra viszi az elhelyezés-tesztet; a hibás
`unnamedGroups(True, root.grouped)` hívás a két csempeszám-tesztet.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.app.qml_functional._utolso_maradek_5150_helpers import gepel

_KEEPALIVE: list = []

_CSOPORTOSITVA_UTMUTATO = (
    'Select someone you know and add a name, or click the "x" to ignore that person.'
)
_KIBONTVA_UTMUTATO = "Select someone you know and add a name"

# A valódi `FaceScanController.unnamedGroups` dönt a csempékről: csoportosítva
# csoportonként csak az előnézet látszik (ő a `_COLLAPSED_GROUP_PREVIEW`, itt
# `_ELONEZET`), kibontva a csoport minden arca. A 6-os arc ezért csak kibontva
# jelenik meg; a 4-es és az 5-ös mindkét módban látszik.
_CSOPORT_ARCAI = (4, 5, 6)
_ELONEZET = 2


class _Sztub(QObject):
    """A `FaceScanController` helyett: a felület hívásait rögzíti."""

    def __init__(self):
        super().__init__()
        self.calls: list = []

    @Slot(result=bool)
    def unnamedWelcomeHasBeenShown(self):  # noqa: N802
        return True

    @Slot()
    def markUnnamedWelcomeShown(self):  # noqa: N802
        pass

    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face, expand_groups):  # noqa: N802
        self.calls.append(("unnamedGroups", group_by_face, expand_groups))
        arcok = _CSOPORT_ARCAI if expand_groups else _CSOPORT_ARCAI[:_ELONEZET]
        return [{
            "label": "Csoport 1",
            "faces": [
                {"faceId": arc, "thumbUrl": "", "suggestedName": ""}
                for arc in arcok
            ],
        }]

    @Slot(result="QVariantList")
    def ignoredGroups(self):  # noqa: N802
        return []

    @Slot("QVariantList", str, result=bool)
    def assignNameToFaces(self, face_ids, name):  # noqa: N802
        self.calls.append(("assignNameToFaces", list(face_ids), name))
        return True

    @Slot("QVariantList", result=int)
    def ignoreFaces(self, face_ids):  # noqa: N802
        self.calls.append(("ignoreFaces", list(face_ids)))
        return len(list(face_ids))


def _montaz(qt_app):
    """A nézet valódi (offscreen) ablakban, a stub controllerrel."""
    import picasapy.app.application as app_module

    motor = QQmlEngine()
    motor.addImportPath(str(app_module._APP_DIR / "qml"))
    sztub = _Sztub()
    komponens = QQmlComponent(
        motor,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "UnnamedFacesView.qml")
        ),
    )
    nezet = komponens.createWithInitialProperties({"faceScanController": sztub})
    assert [e.toString() for e in komponens.errors()] == []
    assert nezet is not None
    QQmlEngine.setObjectOwnership(nezet, QQmlEngine.ObjectOwnership.CppOwnership)

    ablak = QQuickWindow()
    ablak.resize(1000, 600)
    nezet.setParentItem(ablak.contentItem())
    nezet.setProperty("width", 1000)
    nezet.setProperty("height", 600)
    ablak.show()
    QTest.qWaitForWindowExposed(ablak)
    ablak.requestActivate()
    QTest.qWaitForWindowActive(ablak)
    qt_app.processEvents()
    _KEEPALIVE.extend([motor, komponens, nezet, ablak, sztub])
    return nezet, ablak, sztub


@pytest.fixture
def nezet(qt_app):
    nezet, ablak, sztub = _montaz(qt_app)
    yield nezet, ablak, sztub
    ablak.close()


def _bejar(elem):
    for gyermek in elem.childItems():
        yield gyermek
        yield from _bejar(gyermek)


def _todos(ablak, nev):
    """Minden elem a nevével, a láthatóságtól függetlenül (a rácsok és a
    csoportlista is ugyanazokat az objectName-eket adja)."""
    return [e for e in _bejar(ablak.contentItem()) if e.objectName() == nev]


def _varj(qt_app, feltetel, ido=10.0):
    for _ in range(int(ido / 0.02)):
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(20)
    return False


def _latszik(qt_app, ablak, nev):
    """A látszó elem a nevével; megvárja, amíg a rács felépül."""
    talalt = []

    def latszo():
        talalt[:] = [e for e in _todos(ablak, nev) if e.isVisible() and e.width() > 0]
        return bool(talalt)

    assert _varj(qt_app, latszo), f"{nev} nem látszik"
    return talalt[0]


def _elem(ablak, nev):
    talalt = _todos(ablak, nev)
    assert len(talalt) == 1, f"{nev}: {len(talalt)} elem (egy kellene)"
    return talalt[0]


def _klikk(ablak, qt_app, elem):
    qt_app.processEvents()
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _dialogus_gomb(ablak, qt_app, felirat):
    """A megerősítő párbeszéd gombja felirat szerint (a Popup az ablak
    overlay-ében él, a nézet elemfáján kívül)."""
    def van():
        return any(
            e.property("text") == felirat and e.isVisible() and e.width() > 0
            and e.metaObject().indexOfSignal("clicked()") >= 0
            for e in _bejar(ablak.contentItem())
        )

    assert _varj(qt_app, van), f"a(z) {felirat!r} gomb nem látszik"
    return next(
        e for e in _bejar(ablak.contentItem())
        if e.property("text") == felirat and e.isVisible() and e.width() > 0
        and e.metaObject().indexOfSignal("clicked()") >= 0
    )


def _megerosites_nyitva(nezet):
    return nezet.findChild(QObject, "ignoreFacesDialog").property("visible") is True


def _kibont(ablak, qt_app, nezet):
    _klikk(ablak, qt_app, _elem(ablak, "clusterToggleButton"))
    assert nezet.property("grouped") is False


def test_a_valtogomb_kibontja_a_tablazat_szerint(nezet, qt_app):
    nezet, ablak, _sztub = nezet
    valtogomb = _latszik(qt_app, ablak, "clusterToggleButton")
    assert valtogomb.property("text") == "Expand groups"
    assert _elem(ablak, "unnamedNameField").isVisible() is False
    assert _elem(ablak, "ignoreFacesButton").isVisible() is False
    assert _latszik(qt_app, ablak, "faceTile_4") is not None
    assert _latszik(qt_app, ablak, "unnamedFaceNameField_4") is not None
    assert _latszik(qt_app, ablak, "faceIgnoreX_4") is not None

    _klikk(ablak, qt_app, valtogomb)

    assert valtogomb.property("text") == "Group by face"
    assert _elem(ablak, "unnamedInstructions").property("text") == _KIBONTVA_UTMUTATO
    nev_mezo = _latszik(qt_app, ablak, "unnamedNameField")
    assert nev_mezo.property("placeholderText") == "Add a name"
    ignore = _latszik(qt_app, ablak, "ignoreFacesButton")
    assert ignore.property("text") == "Ignore Selected"
    assert not any(e.isVisible() for e in _todos(ablak, "faceIgnoreX_4"))
    assert not any(e.isVisible() for e in _todos(ablak, "unnamedFaceNameField_4"))
    assert not any(e.isVisible() for e in _todos(ablak, "moreSuggestionsButton"))
    assert _todos(ablak, "addNameButton") == []


def test_kijeloles_nelkul_az_ignore_selected_tiltott(nezet, qt_app):
    nezet, ablak, sztub = nezet
    _kibont(ablak, qt_app, nezet)
    ignore = _latszik(qt_app, ablak, "ignoreFacesButton")
    assert ignore.property("enabled") is False

    _klikk(ablak, qt_app, ignore)

    assert not _megerosites_nyitva(nezet)
    assert [c for c in sztub.calls if c[0] == "ignoreFaces"] == []


def test_csempe_kijeloles_utan_a_fejlec_mezoje_enterre_a_kijelolt_arcot_nevezi_meg(
    nezet, qt_app
):
    nezet, ablak, sztub = nezet
    _kibont(ablak, qt_app, nezet)
    kuldott: list = []
    nezet.nameSubmitted.connect(lambda arc, nev: kuldott.append((arc, nev)))

    _klikk(ablak, qt_app, _latszik(qt_app, ablak, "faceTile_5"))
    assert nezet.property("selectedCount") == 1
    nev_mezo = _latszik(qt_app, ablak, "unnamedNameField")
    _klikk(ablak, qt_app, nev_mezo)
    gepel(ablak, qt_app, "Anna")
    QTest.keyClick(ablak, Qt.Key.Key_Return)

    assert _varj(qt_app, lambda: kuldott == [(5, "Anna")]), (
        f"az Enter nem a kijelölt arcot nevezte meg: {kuldott}"
    )
    assert nev_mezo.property("text") == ""
    assert [c for c in sztub.calls if c[0] == "assignNameToFaces"] == []


def test_az_ignore_selected_a_megerositeset_nyitja_es_megerositve_mellozi(
    nezet, qt_app
):
    nezet, ablak, sztub = nezet
    _kibont(ablak, qt_app, nezet)
    _klikk(ablak, qt_app, _latszik(qt_app, ablak, "faceTile_5"))
    ignore = _latszik(qt_app, ablak, "ignoreFacesButton")
    assert _varj(qt_app, lambda: ignore.property("enabled") is True)

    _klikk(ablak, qt_app, ignore)

    assert _varj(qt_app, lambda: _megerosites_nyitva(nezet)), (
        "az Ignore Selected nem nyitotta meg a megerősítést"
    )
    assert [c for c in sztub.calls if c[0] == "ignoreFaces"] == []
    _klikk(ablak, qt_app, _dialogus_gomb(ablak, qt_app, "Ignore Person"))
    assert _varj(qt_app, lambda: ("ignoreFaces", [5]) in sztub.calls)


def test_visszavaltva_a_csoportositott_mod_valtozatlan(nezet, qt_app):
    nezet, ablak, sztub = nezet
    _kibont(ablak, qt_app, nezet)
    _klikk(ablak, qt_app, _latszik(qt_app, ablak, "faceTile_5"))
    assert nezet.property("selectedCount") == 1

    _klikk(ablak, qt_app, _elem(ablak, "clusterToggleButton"))

    assert nezet.property("grouped") is True
    assert nezet.property("selectedCount") == 0
    assert _elem(ablak, "clusterToggleButton").property("text") == "Expand groups"
    assert _elem(ablak, "unnamedInstructions").property("text") == _CSOPORTOSITVA_UTMUTATO
    assert _elem(ablak, "unnamedNameField").isVisible() is False
    assert _elem(ablak, "ignoreFacesButton").isVisible() is False
    assert _latszik(qt_app, ablak, "faceIgnoreX_4") is not None
    assert _latszik(qt_app, ablak, "unnamedFaceNameField_4") is not None


def _fuggoleges(elem):
    """Az elem felső és alsó széle a jelenetben (y-koordináták)."""
    felso = elem.mapToScene(QPointF(0, 0)).y()
    return felso, felso + elem.height()


def _vizszintes(elem):
    """Az elem bal és jobb széle a jelenetben (x-koordináták)."""
    bal = elem.mapToScene(QPointF(0, 0)).x()
    return bal, bal + elem.width()


def test_csoportositva_csak_az_elonezet_latszik(nezet, qt_app):
    nezet, ablak, sztub = nezet
    assert _latszik(qt_app, ablak, "faceTile_4") is not None
    assert _latszik(qt_app, ablak, "faceTile_5") is not None
    assert not any(e.isVisible() for e in _todos(ablak, "faceTile_6"))
    assert ("unnamedGroups", True, False) in sztub.calls


def test_kibontva_a_csoport_minden_arca_csempekent_latszik(nezet, qt_app):
    nezet, ablak, sztub = nezet
    _kibont(ablak, qt_app, nezet)

    for arc in (4, 5, 6):
        assert _latszik(qt_app, ablak, f"faceTile_{arc}") is not None
    assert ("unnamedGroups", True, True) in sztub.calls


def test_kibontva_a_mezo_es_a_gomb_a_felirat_sorában_az_utmutato_felett_van(
    nezet, qt_app
):
    nezet, ablak, _sztub = nezet
    _kibont(ablak, qt_app, nezet)
    felirat = _latszik(qt_app, ablak, "unnamedAlbumFaceCount")
    valtogomb = _latszik(qt_app, ablak, "clusterToggleButton")
    utmutato = _latszik(qt_app, ablak, "unnamedInstructions")
    nev_mezo = _latszik(qt_app, ablak, "unnamedNameField")
    ignore = _latszik(qt_app, ablak, "ignoreFacesButton")
    kontener = _elem(ablak, "unknownFaceViewTypeContainer")

    felirat_felso, felirat_also = _fuggoleges(felirat)
    for elem in (nev_mezo, ignore):
        felso, also = _fuggoleges(elem)
        assert felirat_felso <= (felso + also) / 2 <= felirat_also, (
            f"{elem.objectName()} nem a Face(s) sorában van"
        )
        assert _fuggoleges(valtogomb)[1] <= felso, (
            f"{elem.objectName()} nem a gombpár alatt van"
        )
        assert also <= _fuggoleges(utmutato)[0], (
            f"{elem.objectName()} nem az útmutató fölött van"
        )

    nezet_bal = nezet.mapToScene(QPointF(0, 0)).x()
    assert _vizszintes(nev_mezo)[0] - nezet_bal > nezet.width() / 2
    assert abs(_vizszintes(ignore)[1] - _vizszintes(kontener)[1]) <= 2
