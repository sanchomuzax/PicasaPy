"""#2497 — a „Minden effekt beillesztése" (#152) ini-írásának hibája NE
legyen néma.

A `pasteEffects`/`undoPasteEffects` `update_document` hívása korábban
védtelen volt: írásvédett mappán vagy tele lemezen a kivétel a QML-slotból
szökött ki, a felhasználó pedig SEMMIT nem látott — a rács közben már az
új láncot mutatta. A projekt meglévő hibacsatornája ezekre a
`photoOpFailed` (→ `syncFailed` → `Main.qml` `errorBanner`, #459), ezért a
két út is oda jelent.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "x.jpg", size=(120, 90))
    make_jpeg(root / "y.jpg", size=(120, 90))
    (root / ".picasa.ini").write_text(
        "[x.jpg]\nfilters=sat=1,-0.2;\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


def _row(controller, name: str) -> int:
    return {p.name: i for i, p in enumerate(controller.photos.photos)}[name]


def _torj_el_irast(monkeypatch, uzenet: str = "teszt: a lemez megtelt") -> None:
    """Az ini-írás bukása — a valóságban írásvédett mappa vagy tele lemez."""

    def bukik(*_args, **_kwargs):
        raise OSError(uzenet)

    monkeypatch.setattr("picasapy.app.effects_controller.update_document", bukik)


class TestPasteEffectsIrasiHiba:
    def test_a_beillesztes_bukasa_lathato_hibat_ad(self, controller, monkeypatch):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        controller.copyEffects([_row(controller, "x.jpg")])
        _torj_el_irast(monkeypatch)

        controller.pasteEffects([_row(controller, "y.jpg")])

        assert hibak, "az írási hiba NÉMÁN futott le (#2497)"
        assert "teszt: a lemez megtelt" in hibak[0]

    def test_bukott_beillesztes_utan_nincs_visszavonhato_lepes(
        self, controller, monkeypatch
    ):
        """A verem csak akkor kap elemet, ha az írás tényleg megtörtént —
        különben a „Beillesztés visszavonása" nem létező írást vonna vissza."""
        controller.copyEffects([_row(controller, "x.jpg")])
        _torj_el_irast(monkeypatch)

        controller.pasteEffects([_row(controller, "y.jpg")])

        assert controller.canUndoPasteEffects is False


class TestUndoPasteEffectsIrasiHiba:
    def test_a_visszavonas_bukasa_lathato_hibat_ad(self, controller, monkeypatch):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        controller.copyEffects([_row(controller, "x.jpg")])
        controller.pasteEffects([_row(controller, "y.jpg")])
        assert controller.canUndoPasteEffects is True
        _torj_el_irast(monkeypatch, "teszt: írásvédett mappa")

        controller.undoPasteEffects()

        assert hibak, "a visszavonás írási hibája NÉMÁN futott le (#2497)"
        assert "teszt: írásvédett mappa" in hibak[0]
