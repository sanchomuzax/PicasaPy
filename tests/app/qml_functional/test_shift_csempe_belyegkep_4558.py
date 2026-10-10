"""#4558: Shiftre a kilenc kétmódú csempe BÉLYEGKÉPE is a másodlagosra vált.

Eredeti (`ui-audit-editor.md`, „A második tokent a SHIFT billentyű
kapcsolja”): a csempe felirata ÉS bélyegképe az erőforrás-név `_mod%s`
utótagjával váltja a másodlagosat. Nálunk eddig csak a felirat és a hívás
váltott, a `thumbSource` az elsődleges effektnél maradt.

Egyetlen alkalmazás, EGY Shift-lenyomás, mind a TÍZ csempe (a 4. fül
`effectPicnikGrain`-je is). A teszt LÁT: Shift után megvárja, hogy a
`<objektum>Thumb` Image `Ready` legyen és a forrás-kulcs a másodlagos, majd
az ablakból (`grabWindow`) kivágja a csempe dobozát Shift előtt és alatt.
A hét nem azonos párnál a kivágás eltér; a két, spec szerint azonos kezelőjű
párnál (`unsharp`/`unsharp2`: filters-decoded.md 463., `glow`/`glow2`:
filters-decoded.md 2229.) egyezik. Shift fel → minden az elsődlegesre áll.

⚠️ Az eredeti Picasa Shiftes referencia-képével való egyezést ez a teszt
NEM méri (nincs ilyen képernyőkép); a renderelt pár-eltérést a
`tests/app/test_shift_belyegkep_katalogus_4558.py` is méri.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import (
    _build_qml_app,
    _module_qml_warnings,  # noqa: F401 — modul-fixture
    _module_user_folder_guard,  # noqa: F401 — modul-fixture
)

#: (fül, objektumnév, elsődleges, másodlagos)
CSEMPEK = [
    (2, "effectUnsharp", "unsharp2", "unsharp"),
    (2, "effectGrain2", "picnikgrain", "grain"),
    (2, "effectTint", "picniktint", "tint"),
    (2, "effectGlow2", "glow2", "glow"),
    (2, "effectDirTint", "dir_tint", "radtint"),
    (3, "effectHeatMap", "heatmap", "nightvision"),
    (4, "effectVignette", "vignette", "matte"),
    (4, "effectPixelate", "pixelate", "picnikfocalpixelate"),
    (4, "effectBorder", "border", "roundededges"),
    (5, "effectPicnikGrain", "picnikgrain", "grain"),
]
#: a spec szerint azonos kezelőjű párok (a kép Shift alatt is ugyanaz)
AZONOS = {"effectUnsharp", "effectGlow2"}


def _kepeket_keszit(konyvtar):
    y, x = np.indices((200, 320), dtype=np.uint16)
    rgb = np.empty((200, 320, 3), dtype=np.uint8)
    rgb[..., 0] = (x * 3 + y) % 256
    rgb[..., 1] = (y * 2 + x // 2) % 256
    rgb[..., 2] = ((x // 16 + y // 16) % 2) * 220 + 20
    Image.fromarray(rgb, "RGB").save(
        konyvtar / "a.jpg", format="JPEG", quality=95, subsampling=0
    )


@pytest.fixture(scope="module")
def app(qt_app, tmp_path_factory, _module_qml_warnings, _module_user_folder_guard):  # noqa: F811
    """Egy alkalmazás a modulhoz — a VALÓDI effekt-bélyegkép render-maggal.

    ⚠️ A harness `effectthumb` szolgáltatója egyszínű szürke stub, azon a
    kirajzolt kép nem mérhető. Itt a termék `EffectThumbnailProvider`-ének
    szinkron render-magját (`requestImage`) kötjük be a helyére — a
    pool-ugrás nélkül, mint a `thumbs` szolgáltatónál.
    """
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.index import open_index, photos_in_folder
    from support.szinkron_kepszolgaltato import SzinkronValodiBelyegkep

    gyoker = tmp_path_factory.mktemp("shift4558")
    generator = _build_qml_app(
        qt_app,
        gyoker,
        kepeket_keszit=_kepeket_keszit,
        valodi_belyegkep=True,
    )
    ablak, vezerlo, engine = next(generator)
    with open_index(gyoker / "index.db") as conn:
        rekordok = {
            str(r.id): r for r in photos_in_folder(conn, gyoker / "kepek")
        }
    engine.addImageProvider(
        "effectthumb", SzinkronValodiBelyegkep(EffectThumbnailProvider(rekordok.get))
    )
    yield ablak, vezerlo, engine
    generator.close()


def _varj(qt_app, feltetel, uzenet, masodperc=8.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.02)
    raise AssertionError(uzenet)


def _kulcs(kep) -> str:
    forras = kep.property("source")
    forras = forras.toString() if hasattr(forras, "toString") else str(forras)
    return forras.split("?", 1)[0].rsplit("/", 1)[-1]


def _kesz(kep) -> bool:
    """Image.Ready. A `status` enumot PySide nem tudja kiolvasni, de a
    PanelButton a `<név>Thumb` Image `visible` értékét épp erre köti
    (`visible: status === Image.Ready`), és forrásváltáskor a státusz
    azonnal Loading-ra áll — tehát a `visible` itt a Ready jele.
    ⚠️ A `progress`/`paintedWidth` NEM elég: aszinkron forrásváltásnál a
    régi kép marad kirajzolva, és a `progress` is 1 marad."""
    return bool(kep.property("visible")) and kep.property("paintedWidth") > 0


def _kivagas(ablak, csempe) -> bytes:
    """A csempe BÉLYEGKÉP-doboza az ablak képéből (a felirat nélkül)."""
    bal_felso = csempe.mapToScene(QPointF(0, 0))
    QTest.qWait(120)  # a kirajzolt képkocka megérkezéséig
    kep = ablak.grabWindow()
    resz = kep.copy(
        int(bal_felso.x()), int(bal_felso.y()),
        int(csempe.width()), int(csempe.height()),
    ).convertToFormat(QImage.Format.Format_RGB888)
    return resz.constBits().tobytes()


def _csempek(ablak, qt_app, panel, ful, objektumok):
    panel.setProperty("activeTab", ful)
    _varj(qt_app, lambda: all(
        ablak.findChild(QObject, o) is not None
        and ablak.findChild(QObject, o + "Thumb") is not None
        for o in objektumok), f"a(z) {ful}. fül csempéi nem jelentek meg")
    return {o: (ablak.findChild(QObject, o), ablak.findChild(QObject, o + "Thumb"))
            for o in objektumok}


def _fulenkent():
    ful_objektum: dict[int, list] = {}
    for ful, obj, elso, masodik in CSEMPEK:
        ful_objektum.setdefault(ful, []).append((obj, elso, masodik))
    return ful_objektum


def _allapot_ellenorzes(ablak, qt_app, panel, index):
    """Minden fülön: Ready és a kért kulcs (index 1 = elsődleges, 2 = másodlagos)."""
    for ful, tetelek in _fulenkent().items():
        csempek = _csempek(ablak, qt_app, panel, ful, [t[0] for t in tetelek])
        for tetel in tetelek:
            obj, kulcs = tetel[0], tetel[index]
            kep = csempek[obj][1]
            _varj(qt_app, lambda k=kep, c=kulcs: _kesz(k) and _kulcs(k) == c,
                  f"{obj}: nem Ready/{kulcs}: {_kulcs(kep)!r}, "
                  f"visible={kep.property('visible')}")


def test_egy_shiftre_mind_a_tiz_csempe_belyegkepe_a_masodlagosra_valt(app, qt_app):
    ablak, _vezerlo, _engine = app
    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert panel is not None

    # Shift nélkül: elsődleges, Ready; kivágás az ablakból
    _allapot_ellenorzes(ablak, qt_app, panel, 1)
    elotte: dict[str, bytes] = {}
    for ful, tetelek in _fulenkent().items():
        csempek = _csempek(ablak, qt_app, panel, ful, [t[0] for t in tetelek])
        qt_app.processEvents()
        for obj, _e, _m in tetelek:
            elotte[obj] = _kivagas(ablak, csempek[obj][1])
            assert len(set(elotte[obj])) > 8, (
                f"{obj}: a kivágás egyszínű — nincs kirajzolt bélyegkép"
            )

    QTest.keyPress(ablak, Qt.Key.Key_Shift)
    try:
        _allapot_ellenorzes(ablak, qt_app, panel, 2)
        for ful, tetelek in _fulenkent().items():
            csempek = _csempek(ablak, qt_app, panel, ful, [t[0] for t in tetelek])
            qt_app.processEvents()
            for obj, _e, _m in tetelek:
                alatt = _kivagas(ablak, csempek[obj][1])
                if obj in AZONOS:
                    assert alatt == elotte[obj], f"{obj}: a spec szerint azonos pár képe eltér"
                else:
                    assert alatt != elotte[obj], f"{obj}: Shift alatt a látható kép nem változott"
    finally:
        QTest.keyRelease(ablak, Qt.Key.Key_Shift)

    _allapot_ellenorzes(ablak, qt_app, panel, 1)
