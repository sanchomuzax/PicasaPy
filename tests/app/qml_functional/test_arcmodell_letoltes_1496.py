"""A modellfájl LETÖLTÉSE a felületről — a szürke gomb mellől (#1496).

## A lelet

A #1473 óta az `Eszközök ▸ Arcok keresése…` megnyílik, és modell nélkül
MEGMONDJA, mi hiányzik. A felhasználó (aki nem programozó) viszont ettől
még nem jutott modellhez: a `download_model()` a termékkódból SEHONNAN nem
hívódott, a `~/.local/share/picasapy/models/` mappa létre sem jött. Friss
telepítésen a gomb tehát VÉGIG szürke maradt.

## Miért a párbeszéden át mérünk

A `tests/faces/test_model_download_1496.py` a letöltő MAGJÁT méri
(épség-ellenőrzés, megszakítás, hálózat nélküli ág). Ez a fájl azt a
kérdést teszi fel, amit az a másik nem tud: **rá tud-e a felhasználó
kattintani, és attól élővé válik-e a keresés.** Ezért itt egyetlen
vezérlő-metódus sincs közvetlenül hívva — csak a párbeszéd valódi
gombjai, előbb megkövetelve, hogy engedélyezettek legyenek.

## Hálózat SEHOL

A letöltés egy `127.0.0.1`-en futó, eldobható HTTP-kiszolgálóra megy
(`PICASAPY_MODEL_BASE_URL`), apró, hamis „modellekkel" — a CI-nek hálózat
nélkül is zöldnek kell lennie.
"""

from __future__ import annotations

import hashlib
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

import picasapy.app.application as app_module
from picasapy.faces import model_download

_KEEPALIVE: list = []


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattint(gomb, qt_app, mit="a gomb"):
    """Csak ENGEDÉLYEZETT gombot „nyomunk meg" — egy letiltotton a
    `clicked` kibocsátása sikerülne, miközben a felület néma (#1473)."""
    assert gomb.property("enabled") is True, f"{mit} le van tiltva"
    assert gomb.property("visible") is True, f"{mit} nem látszik"
    QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _var(qt_app, feltetel, masodperc=15.0, uzenet="időtúllépés"):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert feltetel(), uzenet


class _Kiszolgalo:
    """Eldobható loopback HTTP-kiszolgáló (a modul-teszt mintája)."""

    def __init__(self, tartalom: dict[str, bytes], lassito: threading.Event | None = None):
        self.tartalom = tartalom
        self.lassito = lassito
        kiszolgalo = self

        class _Kezelo(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 — a BaseHTTPRequestHandler neve
                payload = kiszolgalo.tartalom.get(self.path)
                if payload is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                felezo = max(1, len(payload) // 2)
                self.wfile.write(payload[:felezo])
                self.wfile.flush()
                if kiszolgalo.lassito is not None:
                    kiszolgalo.lassito.wait(15.0)
                self.wfile.write(payload[felezo:])

            def log_message(self, *args):
                return

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Kezelo)
        self._httpd.daemon_threads = True
        self._szal = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self) -> _Kiszolgalo:
        self._szal.start()
        return self

    def __exit__(self, *_):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._szal.join(5.0)

    @property
    def alap_url(self) -> str:
        cim, port = self._httpd.server_address[:2]
        return f"http://{cim}:{port}"


class _HamisDetektor:
    """A `FaceDetector` felülete — az `available` kívülről állítható."""

    def __init__(self, available=True):
        self.available = available

    def detect(self, image):
        return ()


class _HamisLenyomatolo:
    def __init__(self, available=True):
        self.available = available

    def compute(self, image, detection):
        return None


@pytest.fixture
def modell_mappa(tmp_path, monkeypatch):
    """Üres, IDEIGLENES modell-mappa — a felhasználó valódi mappájához
    (`~/.local/share/picasapy/models`) egyetlen teszt sem nyúlhat."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
    monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
    return tmp_path / "xdg" / "picasapy" / "models"


@pytest.fixture
def apro_specek(monkeypatch):
    """A két modell HELYETT két apró fájl — valódi mérettel és valódi
    SHA-256-tal, hogy az épség-ellenőrzés ténylegesen lefusson."""
    specek = []
    tartalom: dict[str, bytes] = {}
    for eredeti in model_download.MODEL_SPECS:
        payload = (eredeti.key.encode() + b"-hamis-onnx") * 11
        spec = eredeti.masolat(
            size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
        )
        specek.append(spec)
        tartalom["/" + spec.relative_url] = payload
    monkeypatch.setattr(model_download, "MODEL_SPECS", tuple(specek))
    return tuple(specek), tartalom


def _vezerlo(tmp_path, detektor, lenyomatolo, detektor_gyar=None, lenyomat_gyar=None):
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.index import open_index, sync_tree

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir(exist_ok=True)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, str(konyvtar))
    return FaceScanController(
        tmp_path / "index.db",
        detector=detektor,
        embedder=lenyomatolo,
        detector_factory=detektor_gyar,
        embedder_factory=lenyomat_gyar,
    )


def _parbeszed(qt_app, vezerlo):
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


class TestAutomatikusSfaceFolyamatjelzes:
    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_automatikus_letoltes_lathato_folyamatot_mutat(
        self, qt_app, tmp_path, monkeypatch, height_offset
    ):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        vezerlo = _vezerlo(
            tmp_path,
            _HamisDetektor(available=True),
            _HamisLenyomatolo(available=False),
            lenyomat_gyar=lambda: _HamisLenyomatolo(available=True),
        )
        parbeszed = _parbeszed(qt_app, vezerlo)
        parbeszed.setHeight(parbeszed.height() + height_offset)
        qt_app.processEvents()

        megkezdodott = threading.Event()
        folytathato = threading.Event()

        def hamis_letoltes(**kwargs):
            haladas = kwargs.get("progress")
            if haladas is not None:
                haladas(42, 100)
            megkezdodott.set()
            folytathato.wait(5.0)
            return (
                model_download.DownloadResult(
                    status=model_download.STATUS_OK,
                    spec=model_download.EMBEDDER_SPEC,
                    path=tmp_path / model_download.EMBEDDER_SPEC.filename,
                ),
            )

        monkeypatch.setattr(model_download, "download_missing", hamis_letoltes)
        try:
            _kattint(_elem(parbeszed, "faceScanGroupButton"), qt_app)
            assert megkezdodott.wait(2.0), "az automatikus SFace-letöltés nem indult"
            qt_app.processEvents()

            assert parbeszed.property("downloading") is True
            assert _elem(parbeszed, "faceScanDownloadProgressPanel").property(
                "visible"
            ) is True
            assert parbeszed.property("downloadPercent") == 42
        finally:
            folytathato.set()

        _var(
            qt_app,
            lambda: parbeszed.property("grouping") is False,
            uzenet="a letöltés után a csoportosítás nem fejeződött be",
        )
        assert vezerlo.waitForBackgroundWorkers(10.0)


class TestAGombOttVanAhonnanHianyzott:
    """A jegy lényege: modell nélkül legyen MIT megnyomni."""

    def test_modell_nelkul_a_letoltes_gomb_lathato_es_elerheto(
        self, qt_app, tmp_path, modell_mappa
    ):
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False, (
            "a keresés gombja modell nélkül NEM lehet aktív"
        )
        letoltes = _elem(parbeszed, "faceScanDownloadButton")
        assert letoltes.property("visible") is True, (
            "modell nélkül nincs letöltés-gomb — a felhasználó zsákutcában van"
        )
        assert letoltes.property("enabled") is True

    def test_a_gomb_mellett_ott_a_forras_a_meret_es_a_licenc(
        self, qt_app, tmp_path, modell_mappa
    ):
        """A letöltési ajánlat csak a hiányzó SFace modellt sorolja fel."""
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        ajanlat = _elem(parbeszed, "faceScanDownloadOfferText")
        assert ajanlat.property("visible") is True
        szoveg = str(ajanlat.property("text"))
        assert "OpenCV Zoo" in szoveg, szoveg
        # A YuNet a program része, ezért a letöltési ajánlat csak az SFace
        # Apache-2.0 licencét mutatja; a korábbi kétmodell-elvárás elavult.
        assert "Apache" in szoveg, szoveg
        assert "MIT" not in szoveg, szoveg
        assert "MB" in szoveg, "a letöltés mérete nincs kiírva: " + szoveg
        assert str(model_download.DETECTOR_SPEC.default_path().parent) in szoveg, (
            "nincs kiírva, hova kerül a fájl: " + szoveg
        )

    def test_a_letolto_resz_BELEFER_az_ablakba(self, qt_app, tmp_path, modell_mappa):
        """A letöltő rész (gomb + sáv + forrás/méret/licenc) 439 képpontnyi
        tartalmat tett a korábbi 420 képpontos ablakba — a magyarázat alja
        levágódott volna. A magyar fordítás az angolnál hosszabb, ezért az
        őr a MÉRT tartalmat veti össze az ablak magasságával."""
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        elrendezes = _elem(parbeszed, "faceScanDownloadRow").parent()
        tartalom = float(elrendezes.property("implicitHeight"))
        assert tartalom > 0, "a tartalom magassága nem mérhető"
        assert tartalom <= float(parbeszed.property("height")), (
            f"a párbeszéd tartalma ({tartalom}) magasabb az ablaknál "
            f"({parbeszed.property('height')}) — a magyarázat alja levágódik"
        )

    def test_meglevo_modell_mellett_a_letoltes_gomb_eltunik(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, _HamisDetektor(), _HamisLenyomatolo())
        parbeszed = _parbeszed(qt_app, vezerlo)

        assert _elem(parbeszed, "faceScanDownloadButton").property("visible") is False
        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is True


class TestLetoltesUtanElo:
    """A jegy „kész, ha" 5. pontja: letöltés után a keresés INDÍTHATÓ."""

    def test_a_letoltes_utan_a_kereses_gombja_eloved_valik(
        self, qt_app, tmp_path, modell_mappa, apro_specek, monkeypatch
    ):
        specek, tartalom = apro_specek
        # A letöltés UTÁN újraépített modellek — a valódi kódban ez a
        # `FaceDetector()`/`FaceEmbedder()`, itt a teszt-dupla „elérhető"
        # változata.
        vezerlo = _vezerlo(
            tmp_path,
            _HamisDetektor(available=False),
            _HamisLenyomatolo(available=False),
            detektor_gyar=lambda: _HamisDetektor(available=True),
            lenyomat_gyar=lambda: _HamisLenyomatolo(available=True),
        )
        parbeszed = _parbeszed(qt_app, vezerlo)
        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False

        with _Kiszolgalo(tartalom) as kiszolgalo:
            monkeypatch.setenv(
                model_download.MODEL_BASE_URL_ENV_VAR, kiszolgalo.alap_url
            )
            _kattint(
                _elem(parbeszed, "faceScanDownloadButton"), qt_app, "a Letöltés gomb"
            )
            _var(
                qt_app,
                lambda: parbeszed.property("downloading") is False,
                uzenet="a letöltés nem fejeződött be",
            )
            assert vezerlo.waitForBackgroundWorkers(15.0)

        # #4315: a detektor a csomaggal érkezik, csak a felismerő töltődik le.
        for spec in (s for s in specek if s.key != "detector"):
            assert (modell_mappa / spec.filename).is_file(), (
                f"a {spec.filename} nem került a helyére"
            )
        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is True, (
            "a letöltés után is szürke maradt a keresés gombja"
        )
        assert _elem(parbeszed, "faceScanDownloadButton").property("visible") is False
        assert str(parbeszed.property("statusText")).strip(), (
            "a sikeres letöltés nem látszik a felületen"
        )

    def test_a_haladas_vegigfut_es_lathato(
        self, qt_app, tmp_path, modell_mappa, apro_specek, monkeypatch
    ):
        _specek, tartalom = apro_specek
        vezerlo = _vezerlo(
            tmp_path,
            _HamisDetektor(available=False),
            _HamisLenyomatolo(available=False),
            detektor_gyar=lambda: _HamisDetektor(available=True),
            lenyomat_gyar=lambda: _HamisLenyomatolo(available=True),
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        szazalekok: list[int] = []
        vezerlo.modelDownloadPercentChanged.connect(
            lambda: szazalekok.append(vezerlo.modelDownloadPercent),
            Qt.ConnectionType.DirectConnection,
        )

        with _Kiszolgalo(tartalom) as kiszolgalo:
            monkeypatch.setenv(
                model_download.MODEL_BASE_URL_ENV_VAR, kiszolgalo.alap_url
            )
            _kattint(_elem(parbeszed, "faceScanDownloadButton"), qt_app)
            assert _elem(parbeszed, "faceScanDownloadProgressPanel").property(
                "visible"
            ) is True, "a letöltés alatt nincs haladásjelző"
            _var(qt_app, lambda: parbeszed.property("downloading") is False)
            assert vezerlo.waitForBackgroundWorkers(15.0)

        assert 100 in szazalekok, "a haladás nem futott végig: " + repr(szazalekok)
        assert vezerlo.modelDownloadPercent == -1, (
            "a haladásjelző beragadt a letöltés után"
        )
        assert _elem(parbeszed, "faceScanDownloadProgressPanel").property(
            "visible"
        ) is False

    @pytest.mark.parametrize("gyarto_hibat_dob", [False, True])
    def test_betolthetetlen_modellnel_nem_jelez_sikert(
        self,
        qt_app,
        tmp_path,
        modell_mappa,
        apro_specek,
        monkeypatch,
        gyarto_hibat_dob,
    ):
        """A letöltés épsége önmagában nem jelenti, hogy az OpenCV be is
        tudta tölteni a modellfájlokat. Ilyenkor ne maradjon „sikeres” a
        felületi üzenet, és a letöltő szál is záruljon le."""
        specek, tartalom = apro_specek
        betoltott_fajlok: dict[str, bytes | None] = {}

        def gyarto(spec, modell_tipus):
            def letrehoz():
                ut = modell_mappa / spec.filename
                betoltott_fajlok[spec.key] = ut.read_bytes() if ut.is_file() else None
                if gyarto_hibat_dob and spec.key == "detector":
                    raise RuntimeError("a próba ONNX-olvasója elutasította a fájlt")
                return modell_tipus(available=False)

            return letrehoz

        vezerlo = _vezerlo(
            tmp_path,
            _HamisDetektor(available=False),
            _HamisLenyomatolo(available=False),
            detektor_gyar=gyarto(specek[0], _HamisDetektor),
            lenyomat_gyar=gyarto(specek[1], _HamisLenyomatolo),
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        def hamis_ellenorzott_letoltes(**kwargs):
            """A letöltő szerződését utánzó, kimenetet készítő adatforrás."""
            eredmenyek = []
            for spec in specek:
                cel = modell_mappa / spec.filename
                cel.parent.mkdir(parents=True, exist_ok=True)
                cel.write_bytes(tartalom["/" + spec.relative_url])
                eredmenyek.append(
                    model_download.DownloadResult(
                        status=model_download.STATUS_OK, spec=spec, path=cel
                    )
                )
            haladas = kwargs.get("progress")
            if haladas is not None:
                osszmeret = sum(spec.size_bytes for spec in specek)
                haladas(osszmeret, osszmeret)
            return tuple(eredmenyek)

        monkeypatch.setattr(
            model_download, "download_missing", hamis_ellenorzott_letoltes
        )
        _kattint(_elem(parbeszed, "faceScanDownloadButton"), qt_app)
        _var(
            qt_app,
            lambda: parbeszed.property("downloading") is False,
            masodperc=1.0,
            uzenet="a modellbetöltés hibája után beragadt a párbeszéd",
        )
        assert vezerlo.waitForBackgroundWorkers(15.0)

        assert betoltott_fajlok.get("detector") == tartalom[
            "/" + specek[0].relative_url
        ], "a YuNet-gyár nem a letöltött ellenőrzött fájlt kapta"
        if not gyarto_hibat_dob:
            assert betoltott_fajlok.get("embedder") == tartalom[
                "/" + specek[1].relative_url
            ], "az SFace-gyár nem a letöltött ellenőrzött fájlt kapta"
        uzenet = str(parbeszed.property("statusText")).lower()
        assert "could not load" in uzenet or "couldn't load" in uzenet, (
            "a felület sikeresnek mondta a letöltést, pedig a modellek nem "
            f"tölthetők be: {uzenet}"
        )
        assert "could not load" in str(parbeszed.property("detectorReason")).lower()
        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False


class TestMegszakitas:
    def test_a_futo_letoltes_megszakithato(
        self, qt_app, tmp_path, modell_mappa, apro_specek, monkeypatch
    ):
        specek, tartalom = apro_specek
        lassito = threading.Event()
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        with _Kiszolgalo(tartalom, lassito) as kiszolgalo:
            monkeypatch.setenv(
                model_download.MODEL_BASE_URL_ENV_VAR, kiszolgalo.alap_url
            )
            _kattint(_elem(parbeszed, "faceScanDownloadButton"), qt_app)
            megse = _elem(parbeszed, "faceScanDownloadCancelButton")
            _var(
                qt_app,
                lambda: megse.property("visible") is True,
                uzenet="futó letöltés közben nincs látható Mégse gomb",
            )
            _kattint(megse, qt_app, "a letöltés Mégse gombja")
            lassito.set()
            _var(qt_app, lambda: parbeszed.property("downloading") is False)
            assert vezerlo.waitForBackgroundWorkers(15.0)

        assert not (modell_mappa / specek[0].filename).exists(), (
            "a megszakított letöltés fájlt hagyott a modell helyén"
        )
        assert str(parbeszed.property("statusText")).strip(), (
            "a megszakítás nem látszik a felületen"
        )
        assert vezerlo.modelDownloadPercent == -1


class TestHalozatNelkul:
    """3. „kész, ha" pont: érthető üzenet, nem néma bukás."""

    def test_elerhetetlen_forras_eseten_a_parbeszed_MEGMONDJA(
        self, qt_app, tmp_path, modell_mappa, monkeypatch
    ):
        monkeypatch.setenv(
            model_download.MODEL_BASE_URL_ENV_VAR, "http://127.0.0.1:1/nincs"
        )
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        _kattint(_elem(parbeszed, "faceScanDownloadButton"), qt_app)
        _var(
            qt_app,
            lambda: parbeszed.property("downloading") is False,
            uzenet="a sikertelen letöltés után beragadt a felület",
        )
        assert vezerlo.waitForBackgroundWorkers(15.0)

        uzenet = str(parbeszed.property("statusText"))
        assert uzenet.strip(), "a hálózati hiba NÉMA maradt"
        assert "internet" in uzenet.lower() or "network" in uzenet.lower(), (
            "az üzenet nem mondja meg, hogy a hálózattal van baj: " + uzenet
        )
        # A gomb újra nyomható — a hiba nem zárja ki a második próbát.
        assert _elem(parbeszed, "faceScanDownloadButton").property("enabled") is True

    def test_csonka_valasz_eseten_sem_kerul_fajl_a_modell_helyere(
        self, qt_app, tmp_path, modell_mappa, apro_specek, monkeypatch
    ):
        """⚠️ A jegy legfontosabb pontja a FELÜLETRŐL nézve: a romlott
        modell nem kerülhet a helyére, és a felhasználó megtudja."""
        specek, tartalom = apro_specek
        # a kiszolgáló KEVESEBBET ad, mint amennyit a spec ígér
        romlott = {ut: adat[: len(adat) // 3] for ut, adat in tartalom.items()}
        vezerlo = _vezerlo(
            tmp_path, _HamisDetektor(available=False), _HamisLenyomatolo(available=False)
        )
        parbeszed = _parbeszed(qt_app, vezerlo)

        with _Kiszolgalo(romlott) as kiszolgalo:
            monkeypatch.setenv(
                model_download.MODEL_BASE_URL_ENV_VAR, kiszolgalo.alap_url
            )
            _kattint(_elem(parbeszed, "faceScanDownloadButton"), qt_app)
            _var(qt_app, lambda: parbeszed.property("downloading") is False)
            assert vezerlo.waitForBackgroundWorkers(15.0)

        for spec in specek:
            assert not (modell_mappa / spec.filename).exists(), (
                f"a csonka {spec.filename} a modell helyére került"
            )
        assert _elem(parbeszed, "faceScanStartButton").property("enabled") is False
        assert str(parbeszed.property("statusText")).strip(), (
            "a romlott letöltés NÉMÁN bukott el"
        )


@pytest.fixture(autouse=True)
def _takarits():
    yield
    _KEEPALIVE.clear()
