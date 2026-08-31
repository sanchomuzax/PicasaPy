"""Az arckeresés útja VÉGIG: menüpont → párbeszéd → vezérlő → INDEX (#1473).

## A lelet

A `face_scan_controller.py` keresési oldala kész volt — és a felhasználó
nem érte el. Minősített kereséssel (`faceScanController.<tag>`) HÉT tagra
nem volt egyetlen QML-hivatkozás sem: `scanForFaces`, `cancelScan`,
`computeEmbeddings`, `cancelEmbedding`, `isAvailable`,
`isEmbeddingAvailable`, `unnamedAlbum`. Közben a NÉVADÓ felület élt, és a
bal hasáb a `scanPercent`-et kötötte — egy sosem induló folyamat
haladását.

⚠️ A `cancelScan` a jegy eredeti táblájából NÉVÜTKÖZÉS miatt maradt ki: a
`dedupController.cancelScan()` hívásai a puszta tagnévre keresve élőnek
mutatták. Ezért mér itt minden állítás a VALÓDI felületi vezérlőn.

## Miért ilyen ez a teszt

A `tests/app/test_face_scan_controller.py` a vezérlő metódusait már mérte,
és végig zöld volt, miközben a funkciót nem lehetett elindítani. Ez a fájl
ezért soha nem hívja a vezérlő metódusait közvetlenül: a menütételt
aktiválja (előbb megkövetelve, hogy engedélyezett legyen), a párbeszéd
valódi gombjait kattintja — és a végén az INDEXBE írt arcokat, illetve a
`scanPercent` ténylegesen megtett értékeit méri.
"""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

import picasapy.app.application as app_module
from support.jpeg_factory import make_jpeg

#: A QML-oldalról hivatkozott objektumokat életben kell tartani, amíg a
#: motor él (a `test_unnamed_faces_view.py` mintája).
_KEEPALIVE: list = []


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattint(gomb, qt_app, mit="a gomb"):
    """A VALÓDI vezérlő aktiválása — előbb megkövetelve, hogy a felhasználó
    rá tudjon kattintani. Egy letiltott gombon a `clicked` kibocsátása
    „sikerülne", miközben a felület néma és hatástalan (#1473)."""
    assert gomb.property("enabled") is True, f"{mit} le van tiltva"
    QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _var(qt_app, feltetel, masodperc=10.0, uzenet="időtúllépés"):
    """Eseményhurok-pörgetés, amíg a feltétel teljesül."""
    import time

    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert feltetel(), uzenet


class _HamisDetektor:
    """A `FaceDetector` felületét másoló teszt-dupla (a
    `test_face_scan_controller.py`-beli mintája) — mindig „talál" egy
    arcot. A `kapu` eseménnyel a detektálás felfüggeszthető, hogy a
    megszakítás gombja valódi, FUTÓ keresést szakítson meg."""

    def __init__(
        self,
        available=True,
        kapu: threading.Event | None = None,
        kaputol: int = 1,
    ):
        self.available = available
        self.kapu = kapu
        #: hányadik hívástól várjon a kapura (így a keresés a haladás
        #: közepén állítható meg, nem a legelején)
        self.kaputol = kaputol
        self.hivasok = 0

    def detect(self, image):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks

        self.hivasok += 1
        if self.kapu is not None and self.hivasok >= self.kaputol:
            self.kapu.wait(10.0)
        landmarks = FaceLandmarks(
            right_eye=(10.0, 20.0),
            left_eye=(30.0, 20.0),
            nose=(20.0, 30.0),
            mouth_right=(15.0, 40.0),
            mouth_left=(25.0, 40.0),
        )
        return (
            FaceDetection(
                left=5, top=10, right=40, bottom=50, score=0.9, landmarks=landmarks
            ),
        )


class _HamisLenyomatolo:
    """A `FaceEmbedder` teszt-duplája — mindig ugyanazt a lenyomatot adja."""

    def __init__(self, available=True):
        import numpy as np

        self.available = available
        self._vektor = np.array([1.0, 0.0, 0.0], dtype="float32")
        self.hivasok = 0

    def compute(self, image, detection):
        self.hivasok += 1
        return self._vektor


def _vezerlo(tmp_path, kepszam=3, detektor=None, lenyomatolo=None):
    """Valódi `FaceScanController` HAMIS modellekkel, feltöltött indexszel."""
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.index import open_index, sync_tree

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir(exist_ok=True)
    for i in range(kepszam):
        make_jpeg(konyvtar / f"kep{i}.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, str(konyvtar))
    return FaceScanController(
        tmp_path / "index.db",
        detector=detektor if detektor is not None else _HamisDetektor(),
        embedder=lenyomatolo if lenyomatolo is not None else _HamisLenyomatolo(),
    )


def _parbeszed(qt_app, vezerlo):
    """A `FaceScanDialog.qml` ÖNÁLLÓ betöltése, injektált vezérlővel — így a
    keresés valódi lefutását is meg lehet mérni, modell nélküli gépen is."""
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    elem = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FaceScanDialog.qml")
        ),
    )
    assert elem.status() == QQmlComponent.Status.Ready, elem.errorString()
    obj = elem.createWithInitialProperties({"faceScan": vezerlo})
    hibak = [e.toString() for e in elem.errors()]
    assert hibak == [], hibak
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([engine, elem, obj, vezerlo])
    QMetaObject.invokeMethod(obj, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return obj


class TestBelepesiPont:
    """A menüpont — ez hiányzott teljesen (#1473)."""

    def test_a_menupont_letezik_es_nem_helyfoglalo(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "menuToolsFaceScan")
        assert tetel.property("enabled") is True, (
            "az arckeresés menüpontja le van tiltva — a felhasználó nem éri el"
        )
        assert not tetel.property("placeholder"), (
            "az arckeresés menüpontja helyfoglaló, tehát halott"
        )

    def test_a_menupont_megnyitja_a_parbeszedet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        # #1720: a párbeszéd HALASZTOTT — a menüpont ELŐTT létre sem jön.
        assert window.findChild(QObject, "faceScanDialog") is None, (
            "az arckeresés ablaka már a menüpont előtt felépült — a #1720 "
            "halasztása elromlott"
        )

        QMetaObject.invokeMethod(
            _elem(window, "menuToolsFaceScan"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        parbeszed = _elem(window, "faceScanDialog")
        assert parbeszed.property("visible") is True

    def test_a_parbeszed_NEM_modalis(self, qml_app, qt_app):
        """#449: a beolvasás alatt SEMMI nem blokkolhatja a felhasználót —
        a haladás a bal hasáb albumsorán is látszik, az ablak bezárható."""
        window, _controller, _engine = qml_app
        # #1720: a párbeszéd halasztott — a menüponttal nyitjuk meg.
        QMetaObject.invokeMethod(
            _elem(window, "menuToolsFaceScan"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        parbeszed = _elem(window, "faceScanDialog")
        assert parbeszed.property("modality") == Qt.WindowModality.NonModal


class TestElerhetoseg:
    """A néma tiltás visszatérő hibaosztály: a szürke gomb mondja meg, MIÉRT."""

    def test_modell_nelkul_a_gomb_szurke(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, detektor=_HamisDetektor(available=False))
        parbeszed = _parbeszed(qt_app, vezerlo)

        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False

    def test_modell_nelkul_a_parbeszed_MEGMONDJA_miert(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, detektor=_HamisDetektor(available=False))
        parbeszed = _parbeszed(qt_app, vezerlo)

        magyarazat = _elem(parbeszed, "faceScanUnavailableText")
        assert magyarazat.property("visible") is True, (
            "a keresés némán tiltott — a felhasználó nem tudja meg, miért"
        )
        szoveg = str(magyarazat.property("text"))
        from picasapy.faces.detector import MODEL_FILENAME

        assert MODEL_FILENAME in szoveg, (
            "az üzenet nem nevezi meg a hiányzó modellfájlt: " + szoveg
        )

    def test_lenyomat_modell_nelkul_a_csoportosito_gomb_szurke(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, lenyomatolo=_HamisLenyomatolo(available=False))
        parbeszed = _parbeszed(qt_app, vezerlo)

        assert _elem(parbeszed, "faceScanGroupButton").property("enabled") is False
        magyarazat = _elem(parbeszed, "faceScanGroupUnavailableText")
        assert magyarazat.property("visible") is True
        from picasapy.faces.embedder import MODEL_FILENAME

        assert MODEL_FILENAME in str(magyarazat.property("text"))

    def test_vezerlo_NELKUL_sem_dol_el_a_parbeszed(self, qt_app):
        """A `faceScan === null` ág — a `typeof`-őr mögötti eset."""
        parbeszed = _parbeszed(qt_app, None)

        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False


class TestKereses:
    """A lánc utolsó szeme: a gomb VALÓDI arcokat ír az indexbe."""

    def test_a_gomb_elinditja_a_kerest_es_arcok_kerulnek_az_indexbe(
        self, qt_app, tmp_path
    ):
        """A haladásjelző eddig egy INDÍTHATATLAN folyamat százalékát
        mutatta. Itt a keresés a HARMADIK fotónál megáll (kapu), és a
        párbeszéd feliratának ekkor 50%-ot kell mutatnia négy fotóból —
        vagyis valódi, RÉSZLEGES haladást, nem 0-t és nem 100-at."""
        kapu = threading.Event()
        detektor = _HamisDetektor(kapu=kapu, kaputol=3)
        vezerlo = _vezerlo(tmp_path, kepszam=4, detektor=detektor)
        parbeszed = _parbeszed(qt_app, vezerlo)

        # A vezérlő oldali mérés KÖZVETLEN kapcsolattal megy: a jelzés a
        # munkaszálról jön, sorba állítva a százalék már visszaállna −1-re.
        szazalekok: list[int] = []
        vezerlo.scanPercentChanged.connect(
            lambda: szazalekok.append(vezerlo.scanPercent),
            Qt.ConnectionType.DirectConnection,
        )

        _kattint(
            _elem(parbeszed, "faceScanStartButton"), qt_app, "az Arcok keresése gomb"
        )
        felirat = _elem(parbeszed, "faceScanProgressLabel")
        _var(
            qt_app,
            lambda: "50" in str(felirat.property("text")),
            uzenet=(
                "a párbeszéd nem mutatott valódi részleges haladást; a felirat: "
                + str(felirat.property("text"))
            ),
        )
        kapu.set()

        _var(
            qt_app,
            lambda: parbeszed.property("scanning") is False,
            uzenet="a keresés nem fejeződött be",
        )
        assert vezerlo.waitForBackgroundWorkers(10.0)

        assert vezerlo.unnamedCount == 4, (
            "a gombra indított keresés nem írt arcot az indexbe"
        )
        assert 100 in szazalekok, (
            "a haladásjelző nem futott végig — a scanPercent továbbra sem valódi: "
            + repr(szazalekok)
        )

    def test_a_nevtelenek_album_lekerdezese_a_talalatokat_adja(
        self, qt_app, tmp_path
    ):
        """`unnamedAlbum()` — a jegy szerint bekötetlen tag."""
        vezerlo = _vezerlo(tmp_path, kepszam=2)
        parbeszed = _parbeszed(qt_app, vezerlo)

        _kattint(_elem(parbeszed, "faceScanStartButton"), qt_app)
        _var(qt_app, lambda: parbeszed.property("scanning") is False)
        assert vezerlo.waitForBackgroundWorkers(10.0)

        talalatok = parbeszed.property("foundPhotos")
        talalatok = (
            talalatok.toVariant() if hasattr(talalatok, "toVariant") else talalatok
        )
        assert len(talalatok or []) == 2, (
            "a párbeszéd nem a Névtelenek album tényleges tartalmát mutatja"
        )


class TestMegszakitas:
    """`cancelScan` — a névütközés miatt kimaradt tag (#1476 mérése)."""

    def test_a_megse_gomb_megszakitja_a_futo_kerest(self, qt_app, tmp_path):
        kapu = threading.Event()
        detektor = _HamisDetektor(kapu=kapu)
        vezerlo = _vezerlo(tmp_path, kepszam=8, detektor=detektor)
        parbeszed = _parbeszed(qt_app, vezerlo)

        megszakadt: list[bool] = []
        vezerlo.scanCancelled.connect(lambda: megszakadt.append(True))

        _kattint(_elem(parbeszed, "faceScanStartButton"), qt_app)
        _var(
            qt_app,
            lambda: detektor.hivasok >= 1,
            uzenet="a keresés el sem indult, nincs mit megszakítani",
        )

        megse = _elem(parbeszed, "faceScanCancelButton")
        assert megse.property("visible") is True, (
            "futó keresés közben nincs látható Mégse gomb"
        )
        _kattint(megse, qt_app, "a Mégse gomb")
        kapu.set()

        _var(
            qt_app,
            lambda: bool(megszakadt),
            uzenet="a Mégse gomb nem szakította meg a keresést",
        )
        assert vezerlo.waitForBackgroundWorkers(10.0)
        assert detektor.hivasok < 8, "a keresés végigfutott a megszakítás ellenére"
        assert parbeszed.property("scanning") is False
        assert str(parbeszed.property("statusText")).strip(), (
            "a megszakítás nem látszik a felületen"
        )


class TestCsoportositas:
    """`computeEmbeddings` / `cancelEmbedding` — a második, alacsonyabb
    prioritású sor, szintén bekötetlen volt."""

    def test_a_csoportosito_gomb_lenyomatot_szamol(self, qt_app, tmp_path):
        lenyomatolo = _HamisLenyomatolo()
        vezerlo = _vezerlo(tmp_path, kepszam=2, lenyomatolo=lenyomatolo)
        parbeszed = _parbeszed(qt_app, vezerlo)

        _kattint(_elem(parbeszed, "faceScanStartButton"), qt_app)
        _var(qt_app, lambda: parbeszed.property("scanning") is False)
        assert vezerlo.waitForBackgroundWorkers(10.0)

        _kattint(
            _elem(parbeszed, "faceScanGroupButton"),
            qt_app,
            "az Arcok csoportosítása gomb",
        )
        _var(
            qt_app,
            lambda: parbeszed.property("grouping") is False,
            uzenet="a csoportosítás nem fejeződött be",
        )
        assert vezerlo.waitForBackgroundWorkers(10.0)

        assert lenyomatolo.hivasok == 2, (
            "a gomb nem indította el a lenyomat-számítást"
        )

    def test_a_csoportositas_megszakithato(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, kepszam=2)
        parbeszed = _parbeszed(qt_app, vezerlo)

        _kattint(_elem(parbeszed, "faceScanStartButton"), qt_app)
        _var(qt_app, lambda: parbeszed.property("scanning") is False)
        assert vezerlo.waitForBackgroundWorkers(10.0)

        _kattint(_elem(parbeszed, "faceScanGroupButton"), qt_app)
        megse = _elem(parbeszed, "faceScanGroupCancelButton")
        assert megse.property("visible") is True, (
            "futó csoportosítás közben nincs látható Mégse gomb"
        )
        _kattint(megse, qt_app, "a csoportosítás Mégse gombja")

        _var(qt_app, lambda: parbeszed.property("grouping") is False)
        assert vezerlo.waitForBackgroundWorkers(10.0)


@pytest.fixture(autouse=True)
def _takarits():
    """A motorok/vezérlők elengedése a teszt UTÁN — a #430 SIGSEGV-osztály
    elkerülése (a háttérszálakat maguk a tesztek várják be)."""
    yield
    _KEEPALIVE.clear()
