"""#3755: kettős nézetben a finomhangoló GPU élő-előnézete a FÓKUSZBAN lévő
félre illeszkedjen, ne fixen a jobb (`photo`) képre.

A hiba (mérve a #3741 (PR #3750) átnézésekor): a `GpuPointFilterPreview`
geometriája (`PhotoViewer.qml` ~2346) fixen a `photoKeret`/`photo`-hoz volt
kötve — bal fókusznál (`photoArea.fokuszKep === photoElotte`) a húzás alatt
ezért a NEM kijelölt jobb képre rajzolt volna, mihelyt a futtatókörnyezet
GPU-képes.

GPU-képtelen (offscreen/software) futtatókörnyezetben a réteg SOSEM válik
láthatóvá (ld. `test_gpu_finetune_preview.py`), tehát pixelszínnel nem
mérhető — a próbák ezért a KIRAJZOLT geometria-kötéseket nézik: a réteg
`x`/`y`/`width`/`height`/`rotation`/`scale` tulajdonságait a fókuszban lévő
fél SAJÁT elemeiből (`viewerImageElotte`/`viewerImageElotteKeret`, illetve
`viewerImage`/`viewerImageKeret`) számítjuk ki — FÜGGETLENÜL a vizsgált
implementáció `fokuszKep`/`fokuszKeret` aliasától.

A KIRAJZOLT képet a fájl végén álló `TestValodiGpu` méri, valódi OpenGL-en
és valódi egérhúzással — ez csak a fejlesztői gépen fut, a CI-n kihagyja
magát (ld. ott).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QSGRendererInterface
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
    KEK,
    NARANCS,
    ZOLD,
    _bal_fokusz,
    _jobb_fokusz,
    _kep,
    _kozel,
    _szin,
    ket_kep,  # noqa: F401 — pytest-fixture
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _gyerek,
    _kep_teglalap,
    _klikk,
    _nezot_nyit,
)


def _sajat_geometria(kep, keret) -> dict[str, float]:
    """A `photo`/`photoElotte` + a keretük abszolút geometriája a
    `photoArea` koordinátarendszerében — ugyanaz a képlet, mint a
    `GpuPointFilterPreview` implementációja, de a `fokuszKep`/`fokuszKeret`
    alias NÉLKÜL, közvetlenül a névvel elért elemekből."""
    szel = kep.property("width")
    mag = kep.property("height")
    pszel = kep.property("paintedWidth")
    pmag = kep.property("paintedHeight")
    return {
        "x": keret.property("x") + kep.property("x") + (szel - pszel) / 2,
        "y": keret.property("y") + kep.property("y") + (mag - pmag) / 2,
        "width": pszel,
        "height": pmag,
        "rotation": kep.property("rotation"),
        "scale": kep.property("scale"),
    }


def _gpu_geometria(window) -> dict[str, float]:
    """A réteg geometriája a `photoArea` koordinátarendszerében. A réteg
    a fókuszkeretet követő vágó-`Item` gyereke (#3755, 2. pont), tehát
    az `x`/`y`-ja ahhoz relatív."""
    reteg = _gyerek(window, "gpuFinetunePreview")
    vago = _gyerek(window, "gpuFinetuneVago")
    geometria = {kulcs: reteg.property(kulcs)
                 for kulcs in ("x", "y", "width", "height", "rotation", "scale")}
    geometria["x"] += vago.property("x")
    geometria["y"] += vago.property("y")
    return geometria


class TestAGpuElonezetAFokuszbanLevoFelen:
    def test_bal_fokusznal_a_bal_kepre_illeszkedik(self, ket_kep, qt_app):  # noqa: F811
        window, _c, _e = ket_kep
        _bal_fokusz(window, qt_app)
        vart = _sajat_geometria(
            _gyerek(window, "viewerImageElotte"),
            _gyerek(window, "viewerImageElotteKeret"),
        )
        mert = _gpu_geometria(window)
        for kulcs in vart:
            assert mert[kulcs] == pytest.approx(vart[kulcs], abs=0.5), (
                f"{kulcs}: mért={mert[kulcs]} várt={vart[kulcs]} (bal fókusz)"
            )

    def test_jobb_fokusznal_a_jobb_kepre_illeszkedik(self, ket_kep, qt_app):  # noqa: F811
        window, _c, _e = ket_kep
        _jobb_fokusz(window, qt_app)
        vart = _sajat_geometria(
            _gyerek(window, "viewerImage"),
            _gyerek(window, "viewerImageKeret"),
        )
        mert = _gpu_geometria(window)
        for kulcs in vart:
            assert mert[kulcs] == pytest.approx(vart[kulcs], abs=0.5), (
                f"{kulcs}: mért={mert[kulcs]} várt={vart[kulcs]} (jobb fókusz)"
            )

    def test_bal_fokusznal_nagyitva_a_reteg_a_nagyitast_koveti(
        self, ket_kep, qt_app  # noqa: F811
    ):
        """A hiba tiszta jele: a réteg `scale`-je a fixen kötött `photo`
        (bal fókusznál mindig 1,0) helyett a TÉNYLEGESEN nagyított bal
        képet (`photoElotte`) kövesse."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.8)
        qt_app.processEvents()
        elotte = _gyerek(window, "viewerImageElotte")
        assert elotte.property("scale") > 1.05
        reteg = _gyerek(window, "gpuFinetunePreview")
        assert reteg.property("scale") == pytest.approx(
            elotte.property("scale"), abs=0.01
        )

    def test_nagyitva_a_vago_a_fokuszkeret_geometriajat_es_vagasat_koveti(
        self, ket_kep, qt_app  # noqa: F811
    ):
        """#3755, 2. pont: nagyításnál a réteg a `photoArea` gyerekeként
        átlógott a másik félre — a `fokuszKeret` vágása nem érte el. A
        vágó-`Item` a keret geometriáját és `clip`-jét követi."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.8)
        qt_app.processEvents()
        keret = _gyerek(window, "viewerImageElotteKeret")
        vago = _gyerek(window, "gpuFinetuneVago")
        assert keret.property("clip") is True
        for kulcs in ("x", "y", "width", "height", "clip"):
            assert vago.property(kulcs) == keret.property(kulcs), kulcs


class TestAzElotagTexturaMerete:
    """#3800: a `gpuPrefixImage` forrásmérete BEFOGLALÓ doboz — csak
    szélességgel egy magas (1,6-nál nagyobb arányú) kép a textúraplafon
    (V3D: 4096) fölé nőtt. A szolgáltató ma a hosszabb élt 2560-ra
    korlátozza, és nem nagyít; ez az őr akkor is fog, ha az a korlát
    egyszer elmozdul."""

    #: a legkisebb általánosan elérhető GL-textúraplafon ezen a vonalon
    TEXTURA_PLAFON = 4096

    def test_a_forrasmeret_mindket_iranyban_korlatos(self, ket_kep, qt_app):  # noqa: F811
        window, _c, _e = ket_kep
        meret = _gyerek(window, "gpuPrefixImage").property("sourceSize")
        assert 0 < meret.width() <= self.TEXTURA_PLAFON, meret
        assert 0 < meret.height() <= self.TEXTURA_PLAFON, meret


# -- valódi GPU, valódi egérhúzás (#3755, 3. pont) ----------------------------
#
# A fenti próbák offscreen alatt futnak, ahol a GPU-réteg sosem látszik. Az
# alábbiak a KIRAJZOLT képet mérik egy valódi OpenGL-es Wayland-kompozitoron,
# a Kiemelések csúszkát `QTest.mousePress`/`mouseMove`-val húzva, és a gomb
# felengedése ELŐTT készítenek képet.
#
# A környezetet (QPA, RHI, render-loop) a Qt csak induláskor olvassa, a
# `tests/app/conftest.py` pedig offscreent állít be — ezért a mérés egy
# ALFOLYAMATBAN fut (`test_valodi_gpun_egerhuzassal`), amely ugyanezt a
# fájlt a `TestValodiGpu` osztályra szűkítve, a GPU-s környezettel indítja.
# A `TestValodiGpu` önmagában, a belső jelző nélkül, mindig kihagyja magát.
#
# ⚠️ Kihagyás (skip), ha nincs `/run/user/1000/wayland-headless/wayland-0`
# socket, vagy a `GraphicsInfo.api` nem OpenGL. A CI-n (ubuntu, windows)
# tehát MINDIG skip: ezt a próbát csak a fejlesztői gép futtatja.
#
# rontás-kontroll: a réteg geometriáját visszakötve a fix `photoKeret`/
# `photo` párra (a PR előtti main) a `test_ab_bal_fokusz`, a
# `test_aa_bal_fokusz` és a `test_ab_bal_fokusz_nagyitva` BUKIK (a bal kép
# nem változik, a jobb igen); a vágó-`Item` nélkül (a réteg a `photoArea`
# gyereke) egyedül a `test_ab_bal_fokusz_nagyitva` BUKIK (a jobb kép bal
# széle is kivilágosodik). Lefuttatva 2026-09-27-én, valódi OpenGL-en.
#
# rontás-kontroll (#3800): a PR előtti állapotban (`sourceSize.width: 2560`
# a `gpuPrefixImage`-en, és a szolgáltató a `gpuprefix=1` képet is
# felnagyítja) a `TestValodiGpuAlloKep` mindkét esete BUKIK — a 9:16-os kép
# húzás közben változatlan (57,162,57), a textúra 2560×4551. Csak a
# QML-sort visszaállítva a `TestAzElotagTexturaMerete` BUKIK (magasság 0);
# csak a szolgáltatót visszaállítva a `test_kis_kepet_nem_nagyit_fel` (és a
# `test_edit_preview.py` kis képes esete: 1440×2560). Lefuttatva
# 2026-09-28-án, valódi OpenGL-en.
#
# rontás-kontroll (#3819): a javítás előtti main-en (csak szélességes
# `sourceSize.width: 2560` a fő fotón, a szolgáltató a fő képet is
# felnagyítja) a `test_a_fo_foto_nem_nagyit_es_kirajzolodik` mindkét esete
# és a `test_kettos_nezetben_mindket_fel_kirajzolodik` BUKIK — a textúra
# 360×640-es és 1440×2560-as képnél is 2560×4551 —, a `TestAFoFotoForrasmerete`
# (#3877 óta a `test_nezo_forrasmeret_3877.py`-ban)
# mind a négy esete is (magasság 0). ⚠️ A kép a 4096-os plafon fölött IS
# látszott: a Qt feltöltéskor maga zsugorítja a textúrát, tehát a
# színpróba magában nem bukik, a méret-állítás fog. Csak a szolgáltatót
# visszaállítva a kis képes eset és a kettős nézet BUKIK (1440×2560 ≠
# 360×640); csak a QML-t visszaállítva egyedül a `TestAFoFotoForrasmerete`
# BUKIK (a szolgáltató a 2560-as élkorlát miatt ekkor már nem nagyít, a
# dobozt a nyers fájlos út és az előtöltők igénylik). Lefuttatva
# 2026-09-28-án, valódi OpenGL-en.

#: a NEM használt, különálló headless kompozitor — a felhasználó fizikai
#: képernyőjére (`/run/user/1000/wayland-0`) ez a próba SOHA nem nyit ablakot
_HEADLESS = Path("/run/user/1000/wayland-headless")
_BELSO_JELZO = "PICASAPY_GPU_3755_BELSO"
_GPU_KORNYEZET = {
    "QT_QPA_PLATFORM": "wayland",
    "QSG_RHI_BACKEND": "opengl",
    #: kötelező: többszálas renderelésnél a `QTest.mousePress` GIL-holtpontra fut
    "QSG_RENDER_LOOP": "basic",
    "XDG_RUNTIME_DIR": str(_HEADLESS),
    "WAYLAND_DISPLAY": "wayland-0",
    _BELSO_JELZO: "1",
}
#: összegzett RGB-eltérés, ami fölött egy mintapont „megváltozott"
_VALTOZAS_KUSZOB = 25


def test_valodi_gpun_egerhuzassal(tmp_path):
    if not (_HEADLESS / "wayland-0").exists():
        pytest.skip(f"nincs headless Wayland-kompozitor ({_HEADLESS}/wayland-0)")
    kliens = None
    try:
        kliens = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        kliens.settimeout(0.5)
        kliens.connect(str(_HEADLESS / "wayland-0"))
    except OSError as exc:
        pytest.skip(f"a headless Wayland-kompozitor nem érhető el: {exc}")
    finally:
        if kliens is not None:
            kliens.close()
    gyoker = Path(__file__).resolve().parents[3]
    kornyezet = {**os.environ, **_GPU_KORNYEZET}
    kornyezet.pop("DISPLAY", None)
    # #4422: az offscreen tesztfuttató QT_QUICK_BACKEND=software értéke nem
    # öröklődhet a valódi OpenGL-es Wayland alfolyamatba.
    kornyezet.pop("QT_QUICK_BACKEND", None)
    eredmeny = subprocess.run(
        [sys.executable, "-m", "pytest", f"{__file__}::TestValodiGpu",
         f"{__file__}::TestValodiGpuAlloKep",
         f"{__file__}::TestValodiGpuDiavetites",
         #: #3877: a néző nyers fájlos elemeinek textúrája
         f"{Path(__file__).with_name('test_nezo_forrasmeret_3877.py')}"
         "::TestValodiGpuNezoTextura",
         "-q", "-rs", "-p", "no:cacheprovider", f"--basetemp={tmp_path / 'bt'}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=240, cwd=str(gyoker), env=kornyezet,
    )
    kimenet = eredmeny.stdout[-4000:] + eredmeny.stderr[-2000:]
    if eredmeny.returncode == 0 and " passed" not in eredmeny.stdout:
        pytest.skip(f"a GPU-s alfolyamat kihagyta magát:\n{kimenet}")
    assert eredmeny.returncode == 0, kimenet
    # részleges kihagyás nem zöld: minden esetnek ténylegesen mérnie kell
    assert " skipped" not in eredmeny.stdout, kimenet


def _kepek_gpu(lib) -> None:
    """A B próbakép aránya legfeljebb 1,6 — a magasabb (9:16-os) képet a
    `TestValodiGpuAlloKep` méri (#3800)."""
    a = np.full((400, 640, 3), ZOLD[::-1], np.uint8)
    b = np.full((480, 320, 3), NARANCS[::-1], np.uint8)
    b[0:100, 0:100] = KEK[::-1]
    cv2.imwrite(str(lib / "a.jpg"), a, [cv2.IMWRITE_JPEG_QUALITY, 98])
    cv2.imwrite(str(lib / "b.jpg"), b, [cv2.IMWRITE_JPEG_QUALITY, 98])


@pytest.fixture
def ket_kep_gpu(qt_app, tmp_path):
    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_egerhuzassal` alfolyamatában fut")
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_gpu)


#: #3800: 9:16-os telefonos álló kép — a régi `sourceSize.width: 2560`
#: ezt 2560×4551-es textúrára nagyította (a V3D plafonja 4096)
_ALLO_MERET = (360, 640)


def _allo_kep_gpu(lib) -> None:
    szel, mag = _ALLO_MERET
    cv2.imwrite(str(lib / "allo.jpg"), np.full((mag, szel, 3), ZOLD[::-1], np.uint8),
                [cv2.IMWRITE_JPEG_QUALITY, 98])


@pytest.fixture
def allo_kep_gpu(qt_app, tmp_path):
    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_egerhuzassal` alfolyamatában fut")
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_allo_kep_gpu)


def _esemenyek(qt_app, n=10):
    for _ in range(n):
        qt_app.processEvents()


def _also_kozep(r) -> tuple[float, float]:
    """A kirajzolt kép vízszintes közepe, a magasság 80%-ánál — a B kép
    kék sarka (bal felső 100×100) így nem esik bele."""
    return ((r["bal"] + r["jobb"]) / 2, r["fent"] + 0.8 * (r["lent"] - r["fent"]))


def _valtozott(elotte, utana) -> bool:
    return sum(abs(a - b) for a, b in zip(elotte, utana, strict=True)) > _VALTOZAS_KUSZOB


def _varj_a_gpu_forrasokra(window, qt_app, *, hatarido_ms=5000) -> None:
    """A réteg két forrás-`Image`-e (a finetune2 előtti kép és a LUT)
    valódi platformon ASZINKRON töltődik: amíg nincs kész, a réteg nem
    rajzol, és a kép a húzás ellenére változatlannak látszana (mérve:
    egyszer az egyképes esetben így bukott). Kész: teljes a `progress`, és
    van valódi (implicit) képmérete — a `status` enumot a `property()` nem
    tudja Pythonba fordítani (ld. `test_collage_background_1009.py`)."""
    forrasok = [_gyerek(window, nev) for nev in ("gpuPrefixImage", "gpuLutImage")]

    def _kesz(kep) -> bool:
        return (kep.property("progress") == 1.0
                and kep.property("implicitWidth") > 0
                and kep.property("implicitHeight") > 0)

    for _ in range(hatarido_ms // 50):
        if all(_kesz(f) for f in forrasok):
            break
        QTest.qWait(50)
    else:
        allapot = {f.objectName(): (f.property("progress"), f.property("implicitWidth"))
                   for f in forrasok}
        raise AssertionError(f"a GPU-réteg forrásai nem töltődtek be: {allapot}")
    QTest.qWait(300)


def _huzas_kozben(window, qt_app, nezo, pontok, kepnev: Path):
    """A Finomhangolás fülön megfogja és jobbra húzza a Kiemelések
    csúszkát, és a gomb felengedése ELŐTT képet készít.

    A `pontok(window)` adja a mért jelenet-pontokat nevesítve, mindegyikhez
    a húzás ELŐTT várt színnel (pozitív kontroll: a pont tényleg a mért
    képre esik). A pontokat a fül megnyitása UTÁN kérjük: a szerkesztőpanel
    megjelenése átrendezi a képterületet. Az eredmény pontonként
    (előtte, húzás közben)."""
    api = window.rendererInterface().graphicsApi()
    if api != QSGRendererInterface.GraphicsApi.OpenGL:
        pytest.skip(f"a GraphicsInfo.api nem OpenGL: {api}")
    _klikk(qt_app, window, _gyerek(window, "editTabFinetune"))
    QTest.qWait(200)
    assert nezo.property("gpuFinetuneEligible") is True, "OpenGL, de nem GPU-alkalmas"
    elotte = _kep(window, qt_app)
    mert = pontok(window)
    for nev, (pont, vart) in mert.items():
        assert _kozel(_szin(elotte, *pont), vart), (
            f"a(z) {nev} pont nem a várt színre esik húzás előtt: "
            f"{_szin(elotte, *pont)} ≠ {vart} @ {pont}"
        )
    csuszka = _gyerek(window, "finetuneHighlightsSlider")
    bal = csuszka.mapToScene(QPointF(0, csuszka.property("height") / 2))
    szel = csuszka.property("width")
    p0 = QPoint(int(bal.x() + 0.05 * szel), int(bal.y()))
    p1 = QPoint(int(bal.x() + 0.9 * szel), int(bal.y()))
    gomb, mod = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    QTest.mousePress(window, gomb, mod, p0)
    _esemenyek(qt_app)
    for i in range(1, 11):
        QTest.mouseMove(window, QPoint(p0.x() + (p1.x() - p0.x()) * i // 10, p0.y()))
        _esemenyek(qt_app, 3)
    _varj_a_gpu_forrasokra(window, qt_app)
    try:
        assert nezo.property("gpuFinetuneActive") is True
        assert _gyerek(window, "gpuFinetunePreview").property("visible") is True
        huzas = _kep(window, qt_app)
    finally:
        QTest.mouseRelease(window, gomb, mod, p1)
        _esemenyek(qt_app)
    elotte.save(str(kepnev.with_name(kepnev.stem + "_elotte.png")))
    huzas.save(str(kepnev.with_name(kepnev.stem + "_huzas.png")))
    return {nev: (_szin(elotte, *pont), _szin(huzas, *pont))
            for nev, (pont, _vart) in mert.items()}


#: a letterbox-sáv (a `photoArea` háttere) színe — RGB, tűréssel
_SAV = (132, 130, 132)


def _felek_pontjai(bal_szin, jobb_szin):
    def pontok(window):
        return {
            "bal": (_also_kozep(_kep_teglalap(_gyerek(window, "viewerImageElotte"))),
                    bal_szin),
            "jobb": (_also_kozep(_kep_teglalap(_gyerek(window, "viewerImage"))),
                     jobb_szin),
        }
    return pontok


class TestValodiGpu:
    def test_ab_bal_fokusz(self, ket_kep_gpu, qt_app, tmp_path):
        window, _c, _e = ket_kep_gpu
        nezo = _bal_fokusz(window, qt_app)
        m = _huzas_kozben(window, qt_app, nezo, _felek_pontjai(NARANCS, ZOLD),
                          tmp_path / "ab_bal.png")
        assert _valtozott(*m["bal"]), f"a kijelölt bal fél nem változott: {m}"
        assert not _valtozott(*m["jobb"]), f"a NEM kijelölt jobb fél változott: {m}"

    def test_ab_jobb_fokusz(self, ket_kep_gpu, qt_app, tmp_path):
        window, _c, _e = ket_kep_gpu
        nezo = _jobb_fokusz(window, qt_app)
        m = _huzas_kozben(window, qt_app, nezo, _felek_pontjai(NARANCS, ZOLD),
                          tmp_path / "ab_jobb.png")
        assert _valtozott(*m["jobb"]), f"a kijelölt jobb fél nem változott: {m}"
        assert not _valtozott(*m["bal"]), f"a NEM kijelölt bal fél változott: {m}"

    def test_aa_bal_fokusz(self, ket_kep_gpu, qt_app, tmp_path):
        window, _c, _e = ket_kep_gpu
        nezo = _nezot_nyit(window, qt_app)
        nezo.setProperty("currentIndex", 1)
        _klikk(qt_app, window, _gyerek(window, "viewerLayoutAa"))
        QTest.qWait(300)
        assert nezo.property("layoutMode") == "aa"
        if nezo.property("aktivOldal") != "bal":
            _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"
        m = _huzas_kozben(window, qt_app, nezo, _felek_pontjai(NARANCS, NARANCS),
                          tmp_path / "aa_bal.png")
        assert _valtozott(*m["bal"]), f"a kijelölt bal fél nem változott: {m}"
        assert not _valtozott(*m["jobb"]), f"a NEM kijelölt jobb fél változott: {m}"

    def test_egykepes_nezet(self, ket_kep_gpu, qt_app, tmp_path):
        """Egyképes nézetben a réteg a kirajzolt képre kerül, és nem lóg
        ki belőle (a letterbox-sáv a kép mellett változatlan, #415)."""
        window, _c, _e = ket_kep_gpu
        nezo = _nezot_nyit(window, qt_app)
        assert nezo.property("layoutMode") == "1up"

        def pontok(window):
            r = _kep_teglalap(_gyerek(window, "viewerImage"))
            kozep_y = (r["fent"] + r["lent"]) / 2
            return {"kep": (_also_kozep(r), ZOLD),
                    "savban": ((r["bal"] - 6, kozep_y), _SAV)}

        m = _huzas_kozben(window, qt_app, nezo, pontok, tmp_path / "egy.png")
        assert _valtozott(*m["kep"]), f"a kép nem változott: {m}"
        assert not _valtozott(*m["savban"]), f"a réteg kilógott a képből: {m}"

    def test_ab_bal_fokusz_nagyitva(self, ket_kep_gpu, qt_app, tmp_path):
        """#3755, 2. pont: nagyított bal képnél a réteg ne lógjon át a jobb
        kép bal szélére (a `fokuszKeret` vágása őt is érje)."""
        window, _c, _e = ket_kep_gpu
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.8)
        _esemenyek(qt_app)
        QTest.qWait(200)
        assert nezo.property("zoomFactor") > 2

        def pontok(window):
            keret = _gyerek(window, "viewerImageElotteKeret")
            kozep = keret.mapToScene(QPointF(keret.property("width") / 2,
                                             keret.property("height") / 2))
            rj = _kep_teglalap(_gyerek(window, "viewerImage"))
            eredmeny = {"bal": ((kozep.x(), kozep.y()), NARANCS)}
            for i, arany in enumerate((0.2, 0.5, 0.8)):
                pont = (rj["bal"] + 4, rj["fent"] + arany * (rj["lent"] - rj["fent"]))
                eredmeny[f"jobb_szel_{i}"] = (pont, ZOLD)
            return eredmeny

        m = _huzas_kozben(window, qt_app, nezo, pontok, tmp_path / "ab_nagyitva.png")
        assert _valtozott(*m["bal"]), f"a nagyított bal fél nem változott: {m}"
        for nev in m:
            if nev.startswith("jobb"):
                assert not _valtozott(*m[nev]), f"a réteg átlógott a jobb képre: {m}"


class TestValodiGpuAlloKep:
    """#3800: 1,6-nál magasabb arányú (9:16-os) álló képnél a húzás alatt
    SEMMI nem látszott — az előtag-textúra 4096 px fölé nőtt, és a V3D-n
    átlátszó maradt, a CPU-előnézet pedig a GPU-út miatt nem indult."""

    def test_egykepes_nezetben_huzas_kozben_vilagosodik(
        self, allo_kep_gpu, qt_app, tmp_path
    ):
        window, _c, _e = allo_kep_gpu
        nezo = _nezot_nyit(window, qt_app)
        assert nezo.property("layoutMode") == "1up"

        def pontok(window):
            return {"kep": (_also_kozep(_kep_teglalap(_gyerek(window, "viewerImage"))),
                            ZOLD)}

        kepnev = Path(os.environ.get("PICASAPY_GPU_3800_KEP", tmp_path / "allo.png"))
        m = _huzas_kozben(window, qt_app, nezo, pontok, kepnev)
        elotte, huzas = m["kep"]
        assert _valtozott(elotte, huzas), f"az álló kép nem változott: {m}"
        assert sum(huzas) > sum(elotte), f"az álló kép nem világosodott: {m}"

    def test_kis_kepet_nem_nagyit_fel(self, allo_kep_gpu, qt_app, tmp_path):
        """A textúra a kép saját méretét kapja: a kis képet nem nagyítja a
        befoglaló dobozra (a régi kötés 2560 szélesre nagyította)."""
        window, _c, _e = allo_kep_gpu
        nezo = _nezot_nyit(window, qt_app)
        _huzas_kozben(window, qt_app, nezo, lambda _w: {}, tmp_path / "kicsi.png")
        elotag = _gyerek(window, "gpuPrefixImage")
        assert (elotag.property("implicitWidth"),
                elotag.property("implicitHeight")) == _ALLO_MERET

    @pytest.mark.parametrize("sor", [0, 1])
    def test_a_fo_foto_nem_nagyit_es_kirajzolodik(
        self, ket_allo_kep_gpu, qt_app, tmp_path, sor
    ):
        """#3819: a fő fotó textúrája a kép SAJÁT mérete (nem 2560×4551),
        és a kép a kirajzolt ablakon megjelenik — a kék felső sáv a
        helyén, alatta az alapszín."""
        window, _c, _e = ket_allo_kep_gpu
        nezo = _nezot_nyit(window, qt_app)
        nezo.setProperty("currentIndex", sor)
        meret, alap = _FO_KEPEK[sor]
        kep = _gyerek(window, "viewerImage")
        _varj_betoltesre(qt_app, kep, meret, foto_id=sor + 1)
        assert _implicit(kep) == meret
        kepnev = os.environ.get("PICASAPY_GPU_3819_KEP")
        _savos_kep_latszik(window, qt_app, kep, alap,
                           Path(kepnev) if kepnev and sor == 1 else None)

    def test_kettos_nezetben_mindket_fel_kirajzolodik(
        self, ket_allo_kep_gpu, qt_app, tmp_path
    ):
        """#3819: ab módban a bal fél az `editpreview`-ból, a jobb a nyers
        fájlból tölt — mindkettő a saját méretén, és mindkettő látszik."""
        window, _c, _e = ket_allo_kep_gpu
        _bal_fokusz(window, qt_app)
        latott = set()
        for nev in ("viewerImageElotte", "viewerImage"):
            kep = _gyerek(window, nev)
            _varj_betoltesre(qt_app, kep, _FO_KEPEK[0][0])
            # melyik kép van ezen a felén: az alapszínéből
            r = _kep_teglalap(kep)
            szin = _szin(_kep(window, qt_app), (r["bal"] + r["jobb"]) / 2,
                         r["fent"] + 0.6 * (r["lent"] - r["fent"]))
            sor = next((s for s, (_m, alap) in _FO_KEPEK.items() if _kozel(szin, alap)),
                       None)
            assert sor is not None, f"{nev}: ismeretlen alapszín {szin}"
            latott.add(sor)
            meret, alap = _FO_KEPEK[sor]
            assert _implicit(kep) == meret, nev
            _savos_kep_latszik(window, qt_app, kep, alap, None)
        assert latott == set(_FO_KEPEK), f"a két fél nem a két képet mutatja: {latott}"


#: #3819: egy kis és egy nagy 9:16-os kép — a nagyé a szolgáltató
#: 2560-as élkorlátjának pontos határa
_FO_KEPEK = {0: ((360, 640), ZOLD), 1: ((1440, 2560), NARANCS)}


def _fo_kepek_gpu(lib) -> None:
    for sor, nev in ((0, "a.jpg"), (1, "b.jpg")):
        (szel, mag), alap = _FO_KEPEK[sor]
        kep = np.full((mag, szel, 3), alap[::-1], np.uint8)
        kep[: mag // 4] = KEK[::-1]
        cv2.imwrite(str(lib / nev), kep, [cv2.IMWRITE_JPEG_QUALITY, 98])


@pytest.fixture
def ket_allo_kep_gpu(qt_app, tmp_path):
    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_egerhuzassal` alfolyamatában fut")
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_fo_kepek_gpu)


def _implicit(kep) -> tuple[int, int]:
    return (int(kep.property("implicitWidth")), int(kep.property("implicitHeight")))


def _forras_foto_id(kep) -> str:
    """Az `image://editpreview/<id>?rev=…` forrás fotó-azonosítója."""
    return kep.property("source").path().strip("/")


def _varj_betoltesre(qt_app, kep, meret, *, foto_id=None, hatarido_ms=5000) -> None:
    """Az aszinkron betöltés vége: teljes `progress` és a várt képarány
    (a mérete maga az állítás tárgya, arra itt nem várunk).

    #4079: a két próbakép aránya azonos (9:16), ezért a képarány magában
    az ELŐZŐ fotó még betöltött textúráját is elfogadta, amíg a `source`
    át nem váltott az újra (mérve: a `currentIndex` átállítása után a
    forrás egy ideig még az előző fotó azonosítóján áll). A `foto_id`
    megadva a várakozás a forrás átváltására is vár."""
    arany = meret[0] / meret[1]
    for _ in range(hatarido_ms // 50):
        szel, mag = _implicit(kep)
        if ((foto_id is None or _forras_foto_id(kep) == str(foto_id))
                and kep.property("progress") == 1.0 and mag > 0
                and abs(szel / mag - arany) < 0.01):
            break
        QTest.qWait(50)
    else:
        raise AssertionError(
            f"{kep.objectName()}: a kép nem töltődött be: "
            f"{kep.property('source').toString()} {_implicit(kep)}")
    QTest.qWait(300)


def _savos_kep_latszik(window, qt_app, kep, alap, kepnev: Path | None) -> None:
    r = _kep_teglalap(kep)
    kozep_x = (r["bal"] + r["jobb"]) / 2
    ablak = _kep(window, qt_app)
    if kepnev is not None:
        ablak.save(str(kepnev))
    for arany, vart in ((0.1, KEK), (0.6, alap)):
        pont = (kozep_x, r["fent"] + arany * (r["lent"] - r["fent"]))
        assert _kozel(_szin(ablak, *pont), vart), (
            f"{kep.objectName()} {arany:.0%}-nál: {_szin(ablak, *pont)} ≠ {vart}")


# -- #3832: a diavetítés textúrája, valódi GPU-n ------------------------------
#
# A Qt fájlbetöltője `PreserveAspectFit` mellett a kért `sourceSize`-ra
# FELNAGYÍT: a régi csak-szélességes 2560-as kérés 1440×2560-ból és
# 3000×5333-ból is 2560×4551-es textúrát csinált (V3D-plafon: 4096), egy
# 400×300-as képből 2560×1920-at. A diavetítés ezért a kép valódi méretéből
# számolt PONTOS, natívnál nem nagyobb méretet kér (`forrasMeret`).
#
# rontás-kontroll (#3832): a main `SlideshowView.qml`-jével és
# szolgáltatójával (csak-szélességes 2560) mód nélkül és Projektor módban is
# BUKIK: 400×300 → 2560×1920, 1440×2560 és 3000×5333 → 2560×4551. A PR első
# változatával (2560-as doboz csak a szolgáltatónak) mód nélkül ugyanez a
# három érték, Projektor módban a 400×300-as kép bukik (2560×1920, a
# jelölő mód a dobozra nagyít). A színpróba egyikben sem bukik: a Qt a
# plafon fölötti textúrát feltöltéskor csendben lekicsinyíti — a méret-
# állítás fog. Lefuttatva 2026-09-28-án, valódi OpenGL-en (V3D).

PIROS = (200, 40, 40)
#: név → (méret, alapszín); a felső negyed mindegyiken kék sáv
_DIA_KEPEK = {
    "a.jpg": ((400, 300), ZOLD),
    "b.jpg": ((1440, 2560), NARANCS),
    "c.jpg": ((3000, 5333), PIROS),
}
#: a várt textúra: 2560-as dobozba illő, legfeljebb natív méret
_DIA_TEXTURA = {"a.jpg": (400, 300), "b.jpg": (1440, 2560), "c.jpg": (1440, 2560)}


def _dia_kepek_gpu(lib) -> None:
    for nev, ((szel, mag), alap) in _DIA_KEPEK.items():
        kep = np.full((mag, szel, 3), alap[::-1], np.uint8)
        kep[: mag // 4] = KEK[::-1]
        cv2.imwrite(str(lib / nev), kep, [cv2.IMWRITE_JPEG_QUALITY, 95])


@pytest.fixture
def dia_kepek_gpu(qt_app, tmp_path):
    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_egerhuzassal` alfolyamatában fut")
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_dia_kepek_gpu)


def _diavetites(window, qt_app, mod: str):
    """Elindított, megállított, vágásos átmenetű diavetítés — a `mod`
    menütételével (üres = mód nélkül)."""
    from PySide6.QtCore import QMetaObject, QObject, Q_ARG

    from tests.app.qml_functional.test_diavetites_mod_a_kepernyon_1640 import _kattint

    api = window.rendererInterface().graphicsApi()
    if api != QSGRendererInterface.GraphicsApi.OpenGL:
        pytest.skip(f"a GraphicsInfo.api nem OpenGL: {api}")
    if mod:
        _kattint(window, mod)
        _esemenyek(qt_app)
    QMetaObject.invokeMethod(window, "startSlideshow",
                             Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0))
    _esemenyek(qt_app)
    show = window.findChild(QObject, "slideshowView")
    assert show.property("visible") is True, "a diavetítés nem indult el"
    show.setProperty("playing", False)
    show.setProperty("transitionKind", "cut")
    return show


def _diara_lep(qt_app, show, nev: str, *, hatarido_ms=15000):
    """A `nev` képre lép, és megvárja, hogy a dia BETÖLTSE (aszinkron)."""
    from PySide6.QtCore import QObject

    modell = show.property("photosModel")
    sor = next(i for i in range(modell.rowCount())
               if modell.filePathAt(i).endswith("/" + nev))
    show.setProperty("currentIndex", sor)
    dia = show.findChild(QObject, "slideshowImage")
    for _ in range(hatarido_ms // 50):
        if (nev in dia.property("source").toString()
                and dia.property("progress") == 1.0
                and dia.property("implicitWidth") > 0):
            break
        QTest.qWait(50)
    else:
        raise AssertionError(f"{nev}: a dia nem töltődött be")
    QTest.qWait(300)
    return dia


class TestValodiGpuDiavetites:
    TEXTURA_PLAFON = 4096

    @pytest.mark.parametrize("mod", ["", "menuViewDisplayModeProjector"])
    def test_a_textura_a_dobozban_nativnal_nem_nagyobb_es_kirajzolodik(
        self, dia_kepek_gpu, qt_app, mod
    ):
        window, _c, _e = dia_kepek_gpu
        show = _diavetites(window, qt_app, mod)
        kepnev = os.environ.get("PICASAPY_GPU_3832_KEP")
        mert = {}
        for nev in ("b.jpg", "c.jpg", "a.jpg"):
            dia = _diara_lep(qt_app, show, nev)
            mert[nev] = _implicit(dia)
            ment = Path(kepnev) if kepnev and not mod and nev == "c.jpg" else None
            _savos_kep_latszik(window, qt_app, dia, _DIA_KEPEK[nev][1], ment)
        # az összes mért méret egyszerre — a bukás a teljes táblát mutassa
        assert mert == _DIA_TEXTURA, f"{mod or 'mód nélkül'}: {mert}"
        for nev, (szel, mag) in mert.items():
            natv_szel, natv_mag = _DIA_KEPEK[nev][0]
            assert max(szel, mag) <= self.TEXTURA_PLAFON, nev
            assert szel <= natv_szel and mag <= natv_mag, f"{nev} felnagyítva"
