"""A korai, külön indulóablak regressziós tesztjei (#6367)."""

# rontás-kontroll: picasapy.app.startup_splash._SZOJEL = "" → 1 failed

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication

from picasapy.app.startup_splash import (
    _center_splash_position,
    _close_after_first_frame,
    _create_splash_pixmap,
    _logo_pixmap,
    _splash_is_enabled,
    _splash_preference_enabled,
    IndulasAblak,
    _splash_window_flags,
    _strip_nosplash,
    _version_label,
)

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QGuiApplication.instance() or QGuiApplication(["splash-test"])
    return _APP


def _feher_a_terulet(image, rect: QRect) -> bool:
    feher = QColor("#ffffff")
    return all(
        image.pixelColor(x, y) == feher
        for y in range(rect.top(), rect.bottom() + 1)
        for x in range(rect.left(), rect.right() + 1)
    )


class _Beallitasok:
    def __init__(self, values: dict[str, object] | None = None) -> None:
        self.values = values or {}

    def value(self, key: str, default=None):
        return self.values.get(key, default)


@pytest.mark.parametrize(
    ("argv", "platform", "values", "vart"),
    (
        (["picasapy"], "windows", {}, True),
        (["picasapy", "/nosplash"], "windows", {}, False),
        (["picasapy", "--onellenorzes"], "windows", {}, False),
        (["picasapy", "--screensaver"], "windows", {}, False),
        (["picasapy"], "offscreen", {}, False),
        (["picasapy"], "windows", {"usesplashscreen": False}, False),
        (["picasapy"], "windows", {"Preferences/usesplashscreen": "false"}, False),
    ),
)
def test_a_kapcsolok_es_a_beallitas_elnyomjak_az_induloablakot(
    argv: list[str], platform: str, values: dict[str, object], vart: bool
) -> None:
    assert _splash_is_enabled(argv, platform=platform, settings=_Beallitasok(values)) is vart


def test_az_indulas_nem_hoz_letre_widgetes_alkalmazast() -> None:
    """A program QGuiApplication-nel fut (print_controller.py); az indulóablak
    nem válthatja QApplication-re, és QtWidgets-et sem tölthet be."""
    from pathlib import Path

    forras = (
        Path(__file__).resolve().parents[2] / "src/picasapy/app/startup_splash.py"
    ).read_text(encoding="utf-8")
    assert "PySide6.QtWidgets" not in forras
    assert "QApplication(" not in forras.replace("QGuiApplication(", "")


def test_a_nosplash_kapcsolo_nem_kerul_a_qt_argumentumai_koze() -> None:
    assert _strip_nosplash(["picasapy", "/nosplash", "/tmp/fotok"]) == [
        "picasapy",
        "/tmp/fotok",
    ]


def test_a_nosplash_es_a_usesplashscreen_a_qml_splash_t_is_kikapcsolja() -> None:
    assert not _splash_preference_enabled(["picasapy", "/nosplash"], _Beallitasok())
    assert not _splash_preference_enabled(
        ["picasapy"], _Beallitasok({"usesplashscreen": False})
    )
    assert _splash_preference_enabled(["picasapy"], _Beallitasok())


def test_kikapcsolaskor_a_qml_allapot_hidja_keszre_all():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/application_startup_prepare.py"
    )
    source = path.read_text(encoding="utf-8")
    assert 'if not getattr(state, "qml_splash_enabled", True):' in source
    assert "startup_status.finish()" in source


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_a_munkaterulet_kozepet_hasznalja(height_delta: int) -> None:
    munkaterulet = QRect(23, 37, 1360, 760 + height_delta)
    ablakmeret = QSize(668, 263)
    vart = QPoint(
        munkaterulet.x() + (munkaterulet.width() - ablakmeret.width()) // 2,
        munkaterulet.y() + (munkaterulet.height() - ablakmeret.height()) // 2,
    )
    assert _center_splash_position(munkaterulet, ablakmeret) == vart


def test_a_raszteres_indulokep_a_meret_es_a_feher_kepteruletet_tartja() -> None:
    _app()
    pixmap = _create_splash_pixmap("0.9-test")
    assert not pixmap.isNull()
    assert pixmap.size() == QSize(668, 263)

    image = pixmap.toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(1, image.height() // 2).alpha() > 0
    assert image.pixelColor(13, image.height() // 2).alpha() > 0
    assert image.pixelColor(14, image.height() // 2) == QColor("#ffffff")
    assert image.pixelColor(14, 14) == QColor("#ffffff")
    assert _feher_a_terulet(image, QRect(14, 14, 640, 10))
    assert _feher_a_terulet(image, QRect(14, 248, 640, 1))
    assert _feher_a_terulet(image, QRect(14 + 523, 14 + 189, 100, 35))


def test_a_sajat_emblema_a_meresi_dobozban_van_es_a_felirat_nincs_raszterhez_kotve():
    _app()
    image = _create_splash_pixmap("v9.9.9").toImage()

    # A színes saját embléma képpontjai a Picasa-embléma mért befoglaló dobozán belül maradnak.
    logo_box = QRect(14 + 41, 14 + 57, 123, 123)
    colored = [
        (x, y)
        for y in range(logo_box.top(), logo_box.bottom() + 1)
        for x in range(logo_box.left(), logo_box.right() + 1)
        if image.pixelColor(x, y).rgb() != QColor("#ffffff").rgb()
    ]
    assert len(colored) > 500
    assert min(x for x, _ in colored) >= logo_box.left()
    assert max(x for x, _ in colored) <= logo_box.right()
    assert min(y for _, y in colored) >= logo_box.top()
    assert max(y for _, y in colored) <= logo_box.bottom()

    text_box = QRect(14 + 182, 14 + 93, 458, 52)
    assert any(
        image.pixelColor(x, y).rgb() != QColor("#ffffff").rgb()
        for y in range(text_box.top(), text_box.bottom() + 1)
        for x in range(text_box.left(), text_box.right() + 1)
    )

    # A betű rasterizált mérete platformfüggő; a forrás őrzi a mért rectet,
    # családot, méretet és színt.
    source = (
        Path(__file__).resolve().parents[2] / "src/picasapy/app/startup_splash.py"
    ).read_text(encoding="utf-8")
    assert "_EMBLEMA_HELYE = QRect(41, 57, 123, 123)" in source
    assert "_SZOJEL_HELYE = QRect(182, 93, 458, 52)" in source
    assert '_SZOJEL_SZIN = QColor("#4C5B5E")' in source
    assert '_SZOJEL_BETUCSALAD = "Open Sans"' in source
    assert "_SZOJEL_BETUMERET = 53" in source


def test_a_felso_es_jobb_also_resz_cim_es_google_jel_nelkul_marad() -> None:
    _app()
    image = _create_splash_pixmap("v9.9.9").toImage()
    assert _feher_a_terulet(image, QRect(14, 14, 640, 10))
    assert _feher_a_terulet(image, QRect(14 + 523, 14 + 189, 100, 35))
    assert _feher_a_terulet(image, QRect(14 + 182, 14 + 160, 330, 28))
    assert not _logo_pixmap().isNull()
    assert _version_label("v0.9-test") == "v0.9-test"


def test_a_kulon_ablak_keret_nelkuli_es_nem_kattinthato() -> None:
    flags = _splash_window_flags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.SplashScreen
    assert flags & Qt.WindowType.WindowTransparentForInput
    assert flags & Qt.WindowType.WindowDoesNotAcceptFocus
    assert not flags & Qt.WindowType.WindowStaysOnTopHint


def test_az_induloablak_a_kep_meretevel_es_a_jelzokkel_jon_letre() -> None:
    _app()
    pixmap = _create_splash_pixmap("v0.9-test")
    ablak = IndulasAblak(pixmap)
    try:
        assert ablak.size() == QSize(668, 263)
        assert ablak.flags() & Qt.WindowType.FramelessWindowHint
        assert ablak.flags() & Qt.WindowType.WindowTransparentForInput
    finally:
        ablak.destroy()


def test_a_nativ_ablak_paint_esemenye_alpha_nelkul_is_vegrehajthato() -> None:
    _app()
    ablak = IndulasAblak(_create_splash_pixmap("ignored-version"))
    try:
        ablak._alpha_supported = False
        ablak.paintEvent(None)
    finally:
        ablak.destroy()


def test_az_ablak_megjelenes_elott_frissitest_ker(monkeypatch) -> None:
    _app()
    frissitesek = []
    monkeypatch.setattr(IndulasAblak, "requestUpdate", lambda self: frissitesek.append(self))
    ablak = IndulasAblak(_create_splash_pixmap("ignored-version"))
    try:
        assert frissitesek == [ablak]
    finally:
        ablak.destroy()


def test_a_repot_es_a_csomag_forrasat_nem_szennyezi_splashbk_fajl() -> None:
    gyoker = Path(__file__).resolve().parents[2]
    atirt_hash = "a25cf9995bc198418d5b513db1a5ea272dd871fd109313f7f04e5bb5db8276f0"
    kihagyott = {".git", ".tmp", ".bt", ".venv", "__pycache__", ".pytest_cache"}
    talalatok = []

    for path in gyoker.rglob("*"):
        if any(resz in kihagyott for resz in path.relative_to(gyoker).parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if path.stem.casefold() == "splashbk":
            talalatok.append(f"splashbk nevű fájl: {path.relative_to(gyoker)}")
        if path.stat().st_size == 44195:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == atirt_hash:
                talalatok.append(f"az eredeti fájllal bájtra egyező: {path.relative_to(gyoker)}")

    assert not talalatok, "\n".join(talalatok)


def test_az_elso_fokocka_utan_egyszer_bezarja_a_kulon_ablakot() -> None:
    callbacks = []

    class _Signal:
        def connect(self, callback):
            callbacks.append(callback)

        def disconnect(self, callback):
            callbacks.remove(callback)

    class _Splash:
        close_count = 0

        def close(self):
            self.close_count += 1

    splash = _Splash()
    window = SimpleNamespace(frameSwapped=_Signal())
    _close_after_first_frame(window, splash)
    assert splash.close_count == 0
    callbacks[0]()
    assert splash.close_count == 1
    assert callbacks == []


def test_a_run_az_elso_fokocka_esemenyehez_koti_a_kulon_ablakot() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "src/picasapy/app/application.py"
    source = path.read_text(encoding="utf-8")
    assert "_close_after_first_frame(window, early_splash)" in source
    assert source.index("_close_after_first_frame(window, early_splash)") < source.index(
        "window.frameSwapped.connect(_on_first_frame)"
    )


def test_a_belepesi_pont_elobb_inditja_az_induloablakot_mint_a_run_fuggvenyt(
    monkeypatch,
) -> None:
    import inspect

    from picasapy.app import __main__ as entrypoint

    wrapper_source = inspect.getsource(entrypoint.run)
    sorrend: list[str] = []
    early = SimpleNamespace(argv=["picasapy", "/tmp/fotok"])
    monkeypatch.setattr(
        entrypoint, "start_early_startup", lambda argv: (sorrend.append("splash"), early)[1]
    )
    monkeypatch.setattr(
        entrypoint,
        "run",
        lambda argv, *, entry_at=None: (sorrend.append("run"), 0)[1],
    )
    monkeypatch.setattr(entrypoint.sys, "argv", ["picasapy", "/tmp/fotok"])

    assert entrypoint.main() == 0
    assert sorrend == ["splash", "run"]
    assert "from .application import run as application_run" in wrapper_source
