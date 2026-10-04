"""Paritás-teszt (#22): a `GpuPointFilterPreview.qml` (RHI/`ShaderEffect`)
kimenete a CPU-referenciához (`picasapy.render`) képest tolerancián belül.

**GPU-RHI feltétel:** ez a teszt VALÓDI grafikai kontextust igényel — a
Qt Quick jelenetgráf csak RHI-hátterrel futtat tetszőleges
`ShaderEffect`-fragmentshadert; a `QT_QPA_PLATFORM=offscreen` ÖNMAGÁBAN a
`software` adaptert tölti be (nincs GPU, a shader nem fut le). A `tests/app/
conftest.py` offscreent állít, és a Qt a platformot csak induláskor olvassa,
ezért (a #3755 mintájára) a `test_valodi_gpun_a_headless_waylanden` ugyanezt
a fájlt ALFOLYAMATBAN indítja a headless Wayland-kompozitoron
(`/run/user/1000/wayland-headless`, valódi V3D/OpenGL). Ha az nincs, vagy nincs
RHI, a teszt kihagyja magát (a CI-n mindig skip) — nem hamis zöld.

**Mért ok (#3801):** a korábbi „3-ból 2 próba bukik" NEM shader-hiba volt.
A `QQuickView` alapértelmezett Wayland-felülete ~16 bites (RGB565-szerű),
és amint az ablak a kompozitoron megjelent (`isExposed()`), a `grabWindow()`
ezt a felületet olvassa vissza: a csatornák 5-6 bitre kvantálódnak (±4-5
eltérés, rendezett rácsmintával). A kitett állapot terheléstől függ (~40%
terhelt gépen, üresjáratban alig), ezért a bukás szórt. 8 bites felületet
(`QSurfaceFormat` R/G/B/A = 8) kérve a kitett és a nem kitett grab is
egyezik, legfeljebb ±1-gyel (a 240+ értékeknél a LUT-mintavétel +1).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QSG_RHI_BACKEND", "opengl")

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QSurfaceFormat  # noqa: E402
from PySide6.QtQuick import QQuickView, QSGRendererInterface  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from picasapy.render import (  # noqa: E402
    apply_bw,
    apply_saturation,
    build_finetune2_lut,
)

_GPU_QML_DIR = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
)

_TEST_QML = """
import QtQuick
import PicasaPy.Gpu

Item {{
    width: {width}
    height: {height}

    Image {{
        id: sourceImage
        source: "{source_url}"
        smooth: false
        visible: false
        sourceSize: Qt.size({width}, {height})
    }}
    Image {{
        id: lutImage
        source: "{lut_url}"
        smooth: false
        visible: false
    }}

    GpuPointFilterPreview {{
        anchors.fill: parent
        sourceItem: sourceImage
        lutItem: lutImage
        satGain: {sat_gain}
        bwMix: {bw_mix}
    }}
}}
"""


#: a NEM használt, különálló headless kompozitor — a felhasználó fizikai
#: képernyőjére (`/run/user/1000/wayland-0`) ez a próba SOHA nem nyit ablakot
_HEADLESS = Path("/run/user/1000/wayland-headless")
_BELSO_JELZO = "PICASAPY_GPU_3801_BELSO"
_GPU_KORNYEZET = {
    "QT_QPA_PLATFORM": "wayland",
    "QSG_RHI_BACKEND": "opengl",
    "QSG_RENDER_LOOP": "basic",
    "XDG_RUNTIME_DIR": str(_HEADLESS),
    "WAYLAND_DISPLAY": "wayland-0",
    _BELSO_JELZO: "1",
}
_ESETEK = 3


def test_valodi_gpun_a_headless_waylanden(tmp_path):
    """Az alfolyamat a `TestGpuPointFilterParity` mindhárom esetét valódi
    GPU-n futtatja; részleges kihagyás nem zöld."""
    if not (_HEADLESS / "wayland-0").exists():
        pytest.skip(f"nincs headless Wayland-kompozitor ({_HEADLESS}/wayland-0)")
    gyoker = Path(__file__).resolve().parents[2]
    kornyezet = {**os.environ, **_GPU_KORNYEZET}
    kornyezet.pop("DISPLAY", None)
    eredmeny = subprocess.run(
        [sys.executable, "-m", "pytest",
         f"{__file__}::TestGpuPointFilterParity",
         "-q", "-rs", "-p", "no:cacheprovider", f"--basetemp={tmp_path / 'bt'}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=240, cwd=str(gyoker), env=kornyezet,
    )
    kimenet = eredmeny.stdout[-4000:] + eredmeny.stderr[-2000:]
    if eredmeny.returncode == 0 and f"{_ESETEK} passed" not in eredmeny.stdout:
        pytest.skip(f"a GPU-s alfolyamat kihagyta magát:\n{kimenet}")
    assert eredmeny.returncode == 0, kimenet
    assert " skipped" not in eredmeny.stdout, kimenet


@pytest.fixture(scope="module")
def qt_app():
    if os.environ.get(_BELSO_JELZO) != "1":
        pytest.skip("csak a `test_valodi_gpun_a_headless_waylanden` alfolyamatában fut")
    app = QGuiApplication.instance() or QGuiApplication(["gpu-shader-test"])
    yield app


def _rgb_array_to_qimage(array: np.ndarray) -> QImage:
    contiguous = np.ascontiguousarray(array)
    height, width = contiguous.shape[:2]
    image = QImage(
        contiguous.data, width, height, width * 3, QImage.Format.Format_RGB888
    )
    return image.copy()


def _lut_to_qimage(lut: np.ndarray) -> QImage:
    """`(256, 3)` uint8 LUT → 256×1 RGB8 QImage — a shader ezt textúraként
    mintavételezi (`GpuPointFilterPreview.lutItem`)."""
    return _rgb_array_to_qimage(lut[np.newaxis, :, :])


def _grab_rhi_or_skip(width: int, height: int, qml_source: str) -> QImage | None:
    """A megadott QML-t egy offscreen `QQuickView`-ban rendereli és
    visszaadja a pixeleket — vagy `pytest.skip()`-el, ha ez a
    futtatókörnyezet nem tud RHI-grafikai kontextust nyitni."""
    view = QQuickView()
    # 8 bites felület kötelező: az alapértelmezett Wayland-felület ~16 bites,
    # és a kitett ablak grabja ±4-5-re kvantál (#3801)
    felulet = QSurfaceFormat()
    for beallit in (felulet.setRedBufferSize, felulet.setGreenBufferSize,
                    felulet.setBlueBufferSize, felulet.setAlphaBufferSize):
        beallit(8)
    view.setFormat(felulet)
    view.engine().addImportPath(str(_GPU_QML_DIR))
    view.setResizeMode(QQuickView.ResizeMode.SizeViewToRootObject)
    with tempfile.TemporaryDirectory() as tmp_dir:
        qml_path = Path(tmp_dir) / "probe.qml"
        qml_path.write_text(qml_source, encoding="utf-8")
        view.setSource(QUrl.fromLocalFile(str(qml_path)))
        errors = view.errors()
        if errors:
            pytest.fail(
                "QML-hiba a GPU-shader betöltésekor: "
                + "; ".join(error.toString() for error in errors)
            )
        view.show()
        # a KITETT ablak grabja a mérce (a kitettség terheléstől függött, ezért
        # szórt a bukás) — megvárjuk, hogy a mérés determinisztikus legyen
        QTest.qWaitForWindowExposed(view, 5000)
        QGuiApplication.processEvents()
        # A software jelenetgráf-adapter NEM futtat tetszőleges
        # ShaderEffect-fragmentshadert (a grab ekkor is sikeres, de az
        # eredmény a shader NÉLKÜLI, forrás-alapú alapértelmezés — ez
        # NÉMÁN téves paritást adna, ezért a tényleges backendet is
        # ellenőrizni kell, nem elég a grab nem-nulla méretét nézni).
        api = view.rendererInterface().graphicsApi()
        is_rhi = QSGRendererInterface.isApiRhiBased(api)
        grabbed = view.grabWindow()
        csatorna_bit = view.format().redBufferSize()
        view.close()
    assert csatorna_bit >= 8 or not is_rhi, (
        f"a grab felülete csak {csatorna_bit} bites — a kvantálás hamis eltérést ad"
    )
    if not is_rhi or grabbed.isNull() or grabbed.width() == 0 or grabbed.height() == 0:
        pytest.skip(
            "Ebben a futtatókörnyezetben nincs elérhető RHI-grafikai "
            f"kontextus (jelenetgráf-backend: {api!r}, RHI-alapú: {is_rhi}) "
            "— nincs /dev/dri, sem szoftver-EGL-felület, a Qt Quick a "
            "`software` adapterre esik vissza, ami NEM futtat tetszőleges "
            "ShaderEffect-et (ld. a #22 jegy jelentése: több RHI-backendet "
            "— opengl, vulkan, minimalegl+surfaceless — kipróbálva, "
            "mindegyik a GPU-eszköz hiányán bukik). RPi5-ön (valódi GPU) "
            "ennek a tesztnek futnia és pixel-hűnek kell lennie — ha ott "
            "is SKIP, az integrációs hiba."
        )
    return grabbed


class TestGpuPointFilterParity:
    def test_identity_lut_matches_source(self, qt_app, tmp_path):
        """Azonosság-LUT + satGain=1 + bwMix=0 mellett a kimenet == a bemenet."""
        rng = np.random.default_rng(7)
        source = rng.integers(0, 256, size=(8, 8, 3), dtype=np.uint8)
        lut = build_finetune2_lut()

        source_path = tmp_path / "source.png"
        lut_path = tmp_path / "lut.png"
        _rgb_array_to_qimage(source).save(str(source_path))
        _lut_to_qimage(lut).save(str(lut_path))

        qml = _TEST_QML.format(
            width=8,
            height=8,
            source_url=QUrl.fromLocalFile(str(source_path)).toString(),
            lut_url=QUrl.fromLocalFile(str(lut_path)).toString(),
            sat_gain=1.0,
            bw_mix=0.0,
        )
        grabbed = _grab_rhi_or_skip(8, 8, qml)
        result = grabbed.convertToFormat(QImage.Format.Format_RGB888)
        for y in range(8):
            for x in range(8):
                pixel = result.pixelColor(x, y)
                expected = source[y, x]
                assert abs(pixel.red() - int(expected[0])) <= 2
                assert abs(pixel.green() - int(expected[1])) <= 2
                assert abs(pixel.blue() - int(expected[2])) <= 2

    def test_black_and_white_matches_cpu_reference(self, qt_app, tmp_path):
        rng = np.random.default_rng(11)
        source = rng.integers(0, 256, size=(8, 8, 3), dtype=np.uint8)
        lut = build_finetune2_lut()
        expected = apply_bw(source)

        source_path = tmp_path / "source_bw.png"
        lut_path = tmp_path / "lut_bw.png"
        _rgb_array_to_qimage(source).save(str(source_path))
        _lut_to_qimage(lut).save(str(lut_path))

        qml = _TEST_QML.format(
            width=8,
            height=8,
            source_url=QUrl.fromLocalFile(str(source_path)).toString(),
            lut_url=QUrl.fromLocalFile(str(lut_path)).toString(),
            sat_gain=1.0,
            bw_mix=1.0,
        )
        grabbed = _grab_rhi_or_skip(8, 8, qml)
        result = grabbed.convertToFormat(QImage.Format.Format_RGB888)
        for y in range(8):
            for x in range(8):
                pixel = result.pixelColor(x, y)
                target = expected[y, x]
                assert abs(pixel.red() - int(target[0])) <= 2
                assert abs(pixel.green() - int(target[1])) <= 2
                assert abs(pixel.blue() - int(target[2])) <= 2

    def test_saturation_matches_cpu_reference(self, qt_app, tmp_path):
        rng = np.random.default_rng(19)
        source = rng.integers(0, 256, size=(8, 8, 3), dtype=np.uint8)
        lut = build_finetune2_lut()
        from picasapy.render import saturation_gain

        gain = saturation_gain(-0.5)
        expected = apply_saturation(source, -0.5)

        source_path = tmp_path / "source_sat.png"
        lut_path = tmp_path / "lut_sat.png"
        _rgb_array_to_qimage(source).save(str(source_path))
        _lut_to_qimage(lut).save(str(lut_path))

        qml = _TEST_QML.format(
            width=8,
            height=8,
            source_url=QUrl.fromLocalFile(str(source_path)).toString(),
            lut_url=QUrl.fromLocalFile(str(lut_path)).toString(),
            sat_gain=gain,
            bw_mix=0.0,
        )
        grabbed = _grab_rhi_or_skip(8, 8, qml)
        result = grabbed.convertToFormat(QImage.Format.Format_RGB888)
        for y in range(8):
            for x in range(8):
                pixel = result.pixelColor(x, y)
                target = expected[y, x]
                assert abs(pixel.red() - int(target[0])) <= 3
                assert abs(pixel.green() - int(target[1])) <= 3
                assert abs(pixel.blue() - int(target[2])) <= 3
