"""#3877: a néző (`PhotoViewer.qml`) a kép VALÓDI méretéből kér textúrát.

Két út van, és a kettő mást kér:

- **nyers `file://` út** (a két elő-betöltő, a rejtett/nem kijelölt
  `photoElotte`, és a `photo` tartaléka, ha nincs szerkesztési előnézet): a
  Qt fájlbetöltője a kért `sourceSize`-ra FELNAGYÍT, ezért itt a pontos,
  2560-as dobozba illő, natívnál nem nagyobb méret kell — a fájlban TÁROLT
  EXIF-tájolásban (`pixelSidesSwappedAt`).
- **szolgáltatós `image://editpreview/…` út**: a szolgáltató magától csak
  kicsinyít (`edit_preview.py` `_belefer`), KIVÉVE a képpontot jelölő
  megjelenítési módot (#1576): az a kis képet szándékosan a kért dobozra
  nagyítja, és a méretezés UTÁN jelöl. Ide ezért az állandó 2560×2560-as
  doboz megy (mint a `gpuPrefixImage`-nek, #3800) — natív méretet kérve a
  jelölés natív méreten készülne, és a képernyőn szétkenődne.

A `source` és a `sourceSize` EGYÜTT változik (a `SlideshowView.qml` #3832-es
`_betolt`-mintája): két külön kötésnél lépéskor mindkettő átfordul, és a Qt
mindkét változásra tölt — egyszer a rossz párral is. A próbák ezért a
betöltési KÉRÉSEKET számolják (minden nem üres `source`-változás és minden
`sourceSize`-változás nem üres forrás mellett egy kérés), a párjukkal együtt.

A valódi GPU-s textúraméretet a fájl végén álló `TestValodiGpuNezoTextura`
méri, a `test_gpu_finetune_fokusz_3755.py` GPU-s alfolyamatában.

Rontás-kontroll (2026-09-28): ld. az egyes osztályok docsztringjét.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, qmlEngine
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
    ket_kep,  # noqa: F401 — pytest-fixture
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _gyerek,
    _kep_teglalap,
    _klikk,
    _nezot_nyit,
)

#: a `PhotoViewer.qml` `texturaEl`-je — kiírva, nem a termékből olvasva
EL = 2560
DOBOZ = (EL, EL)
SZOLGALTATO = "image://editpreview/"

#: név → (a fájlban TÁROLT méret, EXIF-állás). A `d.jpg` 6-os állású: a
#: megjelenített kép 600×1000, a Qt fájlbetöltőjének viszont a tárolt
#: tájolásban kell kérni.
_LEPES_KEPEK = {
    "a.jpg": ((1440, 2560), None),
    "b.jpg": ((640, 400), None),
    "c.jpg": ((300, 500), None),
    "d.jpg": ((1000, 600), 6),
}
#: a nyers fájlos úton várt `sourceSize` (TÁROLT tájolás) — a doboz nem
#: szűkít, egyik kép sem nagyobb 2560-nál
_LEPES_FORRASMERET = {
    "a.jpg": (1440, 2560),
    "b.jpg": (640, 400),
    "c.jpg": (300, 500),
    "d.jpg": (1000, 600),
}

ELEMEK = ("viewerImage", "viewerImageElotte", "viewerPreloadNext", "viewerPreloadPrev")


def _kepeket_ir(lib, kepek, *, formatum="JPEG") -> None:
    from PIL import Image as PilImage

    for nev, ((szel, mag), allas) in kepek.items():
        exif = PilImage.Exif()
        if allas:
            exif[0x0112] = allas
        PilImage.new("RGB", (szel, mag), (90, 150, 200)).save(
            lib / nev, formatum, exif=exif.tobytes()
        )


def _esemenyek(qt_app, n=10, var_ms=150) -> None:
    for _ in range(n):
        qt_app.processEvents()
    QTest.qWait(var_ms)


# -- a betöltési kérések naplója ------------------------------------------

_NAPLO_QML = b"""
import QtQuick
QtObject {
    id: gyoker
    property var celpont: null
    property string naplo: ""
    function _jegyez(ok) {
        var kep = gyoker.celpont
        var url = kep.source.toString()
        if (ok === "keres" && url === "")
            return
        gyoker.naplo += ok + "|" + url + "|"
            + (ok === "keres" ? kep.sourceSize.width + "|" + kep.sourceSize.height
                              : kep.implicitWidth + "|" + kep.implicitHeight) + "\\n"
    }
    property Connections _figyelo: Connections {
        target: gyoker.celpont
        function onSourceChanged() { gyoker._jegyez("keres") }
        function onSourceSizeChanged() { gyoker._jegyez("keres") }
        function onStatusChanged() {
            if (gyoker.celpont.status === Image.Ready) gyoker._jegyez("kesz")
        }
    }
}
"""


class Naplo:
    """Egy `Image` betöltési kéréseinek és kész méreteinek naplója."""

    def __init__(self, kep) -> None:
        engine = qmlEngine(kep)
        komponens = QQmlComponent(engine)
        komponens.setData(QByteArray(_NAPLO_QML), QUrl())
        self._obj = komponens.create()
        assert self._obj is not None, komponens.errorString()
        self._obj.setProperty("celpont", kep)
        self._komponens = komponens

    def sorok(self) -> list[tuple[str, str, int, int]]:
        eredmeny = []
        for sor in str(self._obj.property("naplo")).splitlines():
            ok, url, szel, mag = sor.split("|")
            eredmeny.append((ok, url, int(float(szel)), int(float(mag))))
        return eredmeny

    def keresek(self) -> list[tuple[str, int, int]]:
        return [(url, s, m) for ok, url, s, m in self.sorok() if ok == "keres"]

    def meretek(self) -> list[tuple[int, int]]:
        return [(s, m) for ok, _u, s, m in self.sorok() if ok == "kesz"]

    def urit(self) -> None:
        self._obj.setProperty("naplo", "")


def _naplok(window) -> dict[str, Naplo]:
    return {nev: Naplo(_gyerek(window, nev)) for nev in ELEMEK}


def _vart_meret(url: str, forrasmeret: dict[str, tuple[int, int]]) -> tuple[int, int]:
    if url.startswith(SZOLGALTATO):
        return DOBOZ
    nev = url.rsplit("/", 1)[-1]
    return forrasmeret[nev]


def _ellenoriz(naplok, forrasmeret, lepes: str) -> None:
    """Elemenként legfeljebb EGY kérés, mindegyik a HELYES párral, és
    semmilyen betöltött kép nem nőtt a doboz fölé."""
    hibak = []
    for nev, naplo in naplok.items():
        keresek = naplo.keresek()
        if len(keresek) > 1:
            hibak.append(f"{nev}: {len(keresek)} kérés: {keresek}")
        for url, szel, mag in keresek:
            if (szel, mag) != _vart_meret(url, forrasmeret):
                hibak.append(f"{nev}: rossz pár: {url} @ {szel}x{mag}")
        for szel, mag in naplo.meretek():
            if max(szel, mag) > EL:
                hibak.append(f"{nev}: a doboz fölé nőtt: {szel}x{mag}")
        naplo.urit()
    assert not hibak, f"{lepes}:\n" + "\n".join(hibak)


@pytest.fixture
def lepes_kepek(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=lambda lib: _kepeket_ir(lib, _LEPES_KEPEK)
    )


class TestEgyKepEgyBetoltes:
    """#3877, 2. pont. Rontás-kontroll: a PR első változatával (két külön
    kötés: `source: kepUrl`, `sourceSize: forrasMeret(…)`) a lépésnél a
    nyers fájlos elemek (elő-betöltők, a rejtett `photoElotte`) képenként
    két kérést indítottak, köztük rossz párt; a kettős nézetre váltáskor a
    `photoElotte` a nyers fájl méretével kérte a szolgáltatót és fordítva."""

    def test_lepeskor_elemenkent_legfeljebb_egy_betoltes(self, lepes_kepek, qt_app):
        window, _c, _e = lepes_kepek
        nezo = _nezot_nyit(window, qt_app)
        _esemenyek(qt_app)
        naplok = _naplok(window)
        for lepes in range(3):
            QMetaObject.invokeMethod(nezo, "next", Qt.ConnectionType.DirectConnection)
            _esemenyek(qt_app)
            _ellenoriz(naplok, _LEPES_FORRASMERET, f"next() #{lepes + 1}")
        assert nezo.property("currentIndex") == 3
        for lepes in range(2):
            QTest.keyClick(window, Qt.Key.Key_Left)
            _esemenyek(qt_app)
            _ellenoriz(naplok, _LEPES_FORRASMERET, f"Bal nyíl #{lepes + 1}")
        assert nezo.property("currentIndex") == 1, "a Bal nyíl nem lapozott"

    @pytest.mark.parametrize("gomb", ["viewerLayoutAb", "viewerLayoutAa"])
    def test_kettos_nezetre_valtaskor_legfeljebb_egy_betoltes(
        self, lepes_kepek, qt_app, gomb
    ):
        window, _c, _e = lepes_kepek
        nezo = _nezot_nyit(window, qt_app)
        _esemenyek(qt_app)
        naplok = _naplok(window)
        _klikk(qt_app, window, _gyerek(window, gomb))
        _esemenyek(qt_app, var_ms=300)
        assert nezo.property("layoutMode") != "1up"
        _ellenoriz(naplok, _LEPES_FORRASMERET, f"{gomb} (a.jpg: 1440×2560)")


# -- a két út mérete a `ket_kep` fixtúrán és egy plafon fölötti képen -----


def _betoltott(qt_app, kep) -> tuple[int, int]:
    """A ténylegesen BETÖLTÖTT kép mérete — a `sourceSize` visszaolvasva a
    BEÁLLÍTOTT értéket adná akkor is, ha a Qt felnagyítana (#2492)."""
    for _ in range(60):
        if kep.property("implicitWidth") > 0:
            break
        QTest.qWait(50)
        qt_app.processEvents()
    return (int(kep.property("implicitWidth")), int(kep.property("implicitHeight")))


class TestAFoFotoForrasmerete:
    """A `ket_kep` fixtúra (a.jpg 640×400, b.jpg 300×500) képei a plafon
    ALATT: a nyers fájlos elemek a natív méretet kérik és kapják, a
    szolgáltatós `photo` (egyképes nézetben az `editpreview`) a dobozt kéri,
    és a szolgáltató jelölés nélkül NEM nagyít. Rontás-kontroll: a main
    csak-szélességes kérésével a nyers fájlos esetek 2560 szélesre nőnek."""

    @pytest.mark.parametrize("index,nev,var_keres,var_kep", [
        (0, "viewerImageElotte", (640, 400), (640, 400)),
        (1, "viewerImageElotte", (300, 500), (300, 500)),
        (0, "viewerImage", DOBOZ, (640, 400)),
        (1, "viewerImage", DOBOZ, (300, 500)),
        # a mappahatáron a lépés helyben marad (`folderNeighbor`, #84):
        # `currentIndex=0`-nál az előző A_JPG-n marad, a következő B_JPG-re lép
        (0, "viewerPreloadNext", (300, 500), (300, 500)),
        (0, "viewerPreloadPrev", (640, 400), (640, 400)),
    ])
    def test_a_keres_es_a_betoltott_kep(
        self, ket_kep, qt_app, index, nev, var_keres, var_kep  # noqa: F811
    ):
        window, _c, _e = ket_kep
        nezo = _nezot_nyit(window, qt_app)
        if index != 0:
            nezo.setProperty("currentIndex", index)
            _esemenyek(qt_app)
        kep = _gyerek(window, nev)
        szolgaltatos = kep.property("source").toString().startswith(SZOLGALTATO)
        assert szolgaltatos is (var_keres == DOBOZ), kep.property("source")
        meret = kep.property("sourceSize")
        assert (meret.width(), meret.height()) == var_keres
        assert _betoltott(qt_app, kep) == var_kep


#: 3000×5333: a 2560-as dobozba illő, legfeljebb natív méret 1440×2560 —
#: nem a Qt fájlbetöltőjének régen MÉRT, felnagyított 2560×4551-e
_TUL_NAGY = {"nagy.jpg": ((3000, 5333), None)}


@pytest.fixture
def tul_nagy_kep(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=lambda lib: _kepeket_ir(lib, _TUL_NAGY)
    )


class TestAFoFotoForrasmereteDobozNagysagnal:
    @pytest.mark.parametrize("nev,var_keres", [
        ("viewerImage", DOBOZ),
        ("viewerImageElotte", (1440, 2560)),
    ])
    def test_a_dobozba_illik_es_nem_nagyit_fel(self, tul_nagy_kep, qt_app, nev, var_keres):
        window, _c, _e = tul_nagy_kep
        _nezot_nyit(window, qt_app)
        _esemenyek(qt_app)
        kep = _gyerek(window, nev)
        meret = kep.property("sourceSize")
        assert (meret.width(), meret.height()) == var_keres
        assert _betoltott(qt_app, kep) == (1440, 2560)


# -- a szolgáltatós út: a jelölő megjelenítési mód (#1576) -----------------


@pytest.fixture
def kis_png(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path,
        kepeket_keszit=lambda lib: _kepeket_ir(lib, {"kicsi.png": ((640, 400), None)},
                                               formatum="PNG"),
    )


def _mod(window, qt_app, tetel: str) -> None:
    from tests.app.qml_functional.test_tulcsordulas_jeloles_1576 import _kattint

    _kattint(window, tetel)
    _esemenyek(qt_app, var_ms=300)


class TestSzolgaltatosUtDoboz:
    """#3877, 1. pont (BLOKKOLÓ). A szolgáltatós út az állandó dobozt kéri:
    jelölő módban a kis kép a dobozra nagyítva, a méretezés UTÁN jelölve
    jön; jelölés nélkül a szolgáltató nem nagyít fel. Rontás-kontroll: a PR
    első változatával (natív méret a szolgáltatónak is) a jelölő módú
    próba bukik — a kép 640×400-on marad, és a kirajzolás nyújtja szét."""

    def _kep(self, window, qt_app):
        _nezot_nyit(window, qt_app)
        _esemenyek(qt_app)
        kep = _gyerek(window, "viewerImage")
        assert kep.property("source").toString().startswith(SZOLGALTATO)
        return kep

    def test_jelolo_modban_a_kis_kep_a_dobozra_nagyitva_jon(self, kis_png, qt_app):
        window, _c, _e = kis_png
        kep = self._kep(window, qt_app)
        _mod(window, qt_app, "menuViewDisplayModeOverflow")
        meret = kep.property("sourceSize")
        assert (meret.width(), meret.height()) == DOBOZ
        assert (kep.property("implicitWidth"), kep.property("implicitHeight")) == (
            2560, 1600
        ), "a jelölő mód nem a dobozra nagyított képen jelöl"

    def test_jeloles_nelkul_nincs_felnagyitas(self, kis_png, qt_app):
        window, _c, _e = kis_png
        kep = self._kep(window, qt_app)
        meret = kep.property("sourceSize")
        assert (meret.width(), meret.height()) == DOBOZ
        assert (kep.property("implicitWidth"), kep.property("implicitHeight")) == (
            640, 400
        )


# -- a nyers fájlos út: a doboz és a felcserélt oldalú EXIF-kép -----------

#: 6-os állású képek: tárolva fekvő, megjelenítve álló
_CSERELT_KEPEK = {
    "a.jpg": ((5333, 3000), 6),  # megjelenítve 3000×5333 → 1440×2560
    "b.jpg": ((640, 400), 6),  # megjelenítve 400×640, a plafon alatt
}
#: a nyers fájlos úton várt `sourceSize` (TÁROLT tájolás) és a betöltött
#: kép (megjelenített tájolás)
_CSERELT_VART = {
    "a.jpg": ((2560, 1440), (1440, 2560)),
    "b.jpg": ((640, 400), (400, 640)),
}


@pytest.fixture
def cserelt_kepek(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=lambda lib: _kepeket_ir(lib, _CSERELT_KEPEK)
    )


def _meres(kep) -> tuple[str, tuple[int, int], tuple[int, int]]:
    meret = kep.property("sourceSize")
    return (
        kep.property("source").toString().rsplit("/", 1)[-1],
        (meret.width(), meret.height()),
        (int(kep.property("implicitWidth")), int(kep.property("implicitHeight"))),
    )


class TestFelcsereltOldaluExifKep:
    """#3877, 4. pont: `pixelSidesSwappedAt`. A nyers fájlos elemek a
    TÁROLT tájolásban kérnek, és a megjelenített tájolásban kapják meg a
    képet. Rontás-kontroll: az oldalcsere nélkül (`forrasMeret` a
    megjelenített párt adja) mind bukik — ld. a jelentés méréseit."""

    def _nyers(self, window, qt_app, index):
        nezo = _nezot_nyit(window, qt_app)
        if index != 0:
            nezo.setProperty("currentIndex", index)
        _esemenyek(qt_app)
        return nezo

    @pytest.mark.parametrize("index", [0, 1])
    def test_az_elo_betoltok(self, cserelt_kepek, qt_app, index):
        window, _c, _e = cserelt_kepek
        self._nyers(window, qt_app, index)
        masik = "b.jpg" if index == 0 else "a.jpg"
        # a mappahatáron a lépés helyben marad (#84)
        nev = "viewerPreloadNext" if index == 0 else "viewerPreloadPrev"
        assert _meres(_gyerek(window, nev)) == (masik, *_CSERELT_VART[masik])

    @pytest.mark.parametrize("index", [0, 1])
    def test_a_photo_nyers_fajlos_tartaleka(self, cserelt_kepek, qt_app, index):
        """Ha nincs szerkesztési előnézet, a `photo` a nyers fájlt tölti."""
        window, _c, _e = cserelt_kepek
        nezo = self._nyers(window, qt_app, index)
        nezo.property("editCtl").endEdit()
        _esemenyek(qt_app)
        nev = ("a.jpg", "b.jpg")[index]
        kep = _gyerek(window, "viewerImage")
        assert _meres(kep) == (nev, *_CSERELT_VART[nev])

    @pytest.mark.parametrize("index", [0, 1])
    def test_a_rejtett_photoElotte(self, cserelt_kepek, qt_app, index):
        window, _c, _e = cserelt_kepek
        self._nyers(window, qt_app, index)
        nev = ("a.jpg", "b.jpg")[index]
        assert _meres(_gyerek(window, "viewerImageElotte")) == (
            nev, *_CSERELT_VART[nev]
        )


# -- valódi GPU (a `test_gpu_finetune_fokusz_3755.py` alfolyamatában) -----

#: 9:16-os képek és egy 6-os állású — a nyers fájlos úton a régi
#: csak-szélességes kérés mind a hármat 2560×4551-re nagyította
_GPU_KEPEK = {
    "a.jpg": ((1440, 2560), None),
    "b.jpg": ((3000, 5333), None),
    "c.jpg": ((5333, 3000), 6),
}
_GPU_TEXTURA = {"a.jpg": (1440, 2560), "b.jpg": (1440, 2560), "c.jpg": (1440, 2560)}


@pytest.fixture
def gpu_nezo_kepek(qt_app, tmp_path):
    from tests.app.qml_functional.test_gpu_finetune_fokusz_3755 import _BELSO_JELZO

    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_egerhuzassal` alfolyamatában fut")
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=lambda lib: _kepeket_ir(lib, _GPU_KEPEK)
    )


def _varj(qt_app, kep, nev: str, *, hatarido_ms=15000) -> tuple[int, int]:
    for _ in range(hatarido_ms // 50):
        if (kep.property("source").toString().endswith("/" + nev)
                and kep.property("progress") == 1.0
                and kep.property("implicitWidth") > 0):
            break
        QTest.qWait(50)
    else:
        raise AssertionError(f"{kep.objectName()}: {nev} nem töltődött be")
    QTest.qWait(200)
    return (int(kep.property("implicitWidth")), int(kep.property("implicitHeight")))


class TestValodiGpuNezoTextura:
    """A néző nyers fájlos elemeinek textúrája valódi OpenGL-en (V3D,
    `GL_MAX_TEXTURE_SIZE` 4096). Rontás-kontroll: az origin/main
    `PhotoViewer.qml`-jével mindhárom kép 2560×4551 — ld. a jelentést."""

    def test_a_nyers_fajlos_elemek_texturaja(self, gpu_nezo_kepek, qt_app, tmp_path):
        from PySide6.QtQuick import QSGRendererInterface

        window, _c, _e = gpu_nezo_kepek
        api = window.rendererInterface().graphicsApi()
        if api != QSGRendererInterface.GraphicsApi.OpenGL:
            pytest.skip(f"a GraphicsInfo.api nem OpenGL: {api}")
        nezo = _nezot_nyit(window, qt_app)
        nezo.property("editCtl").endEdit()
        _esemenyek(qt_app)
        mert = {}
        for index, nev in enumerate(_GPU_KEPEK):
            nezo.setProperty("currentIndex", index)
            _esemenyek(qt_app)
            nezo.property("editCtl").endEdit()
            _esemenyek(qt_app)
            mert[("viewerImage", nev)] = _varj(qt_app, _gyerek(window, "viewerImage"), nev)
            mert[("viewerImageElotte", nev)] = _varj(
                qt_app, _gyerek(window, "viewerImageElotte"), nev)
            kovetkezo = list(_GPU_KEPEK)[min(index + 1, 2)]
            if kovetkezo != nev:
                mert[("viewerPreloadNext", kovetkezo)] = _varj(
                    qt_app, _gyerek(window, "viewerPreloadNext"), kovetkezo)
            elozo = list(_GPU_KEPEK)[max(index - 1, 0)]
            if elozo != nev:
                mert[("viewerPreloadPrev", elozo)] = _varj(
                    qt_app, _gyerek(window, "viewerPreloadPrev"), elozo)
            kepnev = os.environ.get("PICASAPY_GPU_3877_KEP")
            _kirajzolodik(window, qt_app, _gyerek(window, "viewerImage"),
                          Path(kepnev) if kepnev and index == 2 else None)
        print(f"\n#3877 GPU-textúrák: {mert}")
        vart = {kulcs: _GPU_TEXTURA[kulcs[1]] for kulcs in mert}
        assert mert == vart, mert


def _kirajzolodik(window, qt_app, kep, kepnev: Path | None) -> None:
    """Az egyszínű próbakép KIRAJZOLÓDIK: a kép közepén a saját színe (a
    Qt a plafon fölötti textúrát csendben lekicsinyítené — a méret-állítás
    a döntő, ez a pozitív kontroll)."""
    from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
        _kep,
        _kozel,
        _szin,
    )

    r = _kep_teglalap(kep)
    ablak = _kep(window, qt_app)
    if kepnev is not None:
        ablak.save(str(kepnev))
    pont = ((r["bal"] + r["jobb"]) / 2, (r["fent"] + r["lent"]) / 2)
    assert _kozel(_szin(ablak, *pont), (90, 150, 200)), (
        f"{kep.objectName()}: a kép nem rajzolódott ki: {_szin(ablak, *pont)}"
    )
