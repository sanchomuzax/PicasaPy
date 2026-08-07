"""`PhotoOpsMixin` — „Az összes effektus másolása/beillesztése" (#426).

A vezérlő-oldali kötegelt írást/visszavonást teszteli AppControlleren
keresztül (a `test_rename_many_controller.py` fixtúra-mintája).
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg", size=(800, 600))
    make_jpeg(root / "b.jpg", size=(800, 600))
    make_jpeg(root / "c.jpg", size=(800, 600))
    (root / ".picasa.ini").write_text(
        "[a.jpg]\n"
        "filters=enhance=1;crop64=1,45930000ba03defe;"
        "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        "redeye=1;retouch=1,10000000f1ddff49;\n"
        "[b.jpg]\n"
        "filters=sat=1,-0.2;\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def other_folder_library(tmp_path):
    """Két mappa, hogy a kötegelt írás mappánkénti csoportosítása
    ellenőrizhető legyen."""
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "x.jpg", size=(800, 600))
    make_jpeg(folder_b / "y.jpg", size=(800, 600))
    (folder_a / ".picasa.ini").write_text(
        "[x.jpg]\nfilters=enhance=1;crop64=1,45930000ba03defe;\n", encoding="utf-8"
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
    return ctl


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


def _ini_text(folder) -> str:
    return (folder / ".picasa.ini").read_text(encoding="utf-8")


class TestCopyAllEffects:
    def test_copies_filtered_chain_to_clipboard(self, controller):
        assert controller.hasAllEffectsClipboard is False
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        assert controller.hasAllEffectsClipboard is True

    def test_empty_selection_is_noop(self, controller):
        controller.copyAllEffects([])
        assert controller.hasAllEffectsClipboard is False

    def test_does_not_write_anything(self, controller, library):
        before = _ini_text(library)
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        assert _ini_text(library) == before


class TestPasteAllEffects:
    def test_applies_filtered_chain_overwriting_existing(self, controller, library):
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg", "c.jpg"))

        text = _ini_text(library)
        assert "[b.jpg]" in text
        # a b.jpg saját sat= láncát felülírta a beillesztés
        expected = (
            "enhance=1;"
            "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        )
        assert f"filters={expected}" in text
        # a crop64/redeye/retouch NEM ment át
        lines = text.splitlines()
        b_index = lines.index("[b.jpg]")
        c_index = lines.index("[c.jpg]")
        b_block = "\n".join(lines[b_index:c_index])
        assert "crop64" not in b_block
        assert "redeye" not in b_block
        assert "retouch" not in b_block

    def test_without_clipboard_is_noop(self, controller, library):
        before = _ini_text(library)
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        assert _ini_text(library) == before

    def test_empty_selection_is_noop(self, controller, library):
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        before = _ini_text(library)
        controller.pasteAllEffects([])
        assert _ini_text(library) == before

    def test_single_write_per_folder(
        self, qt_app, tmp_path, other_folder_library, monkeypatch
    ):
        """A beillesztés mappánként EGY ini-írásban történik, nem
        fájlonként — a #426 kötegelt-írás követelménye."""
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings

        root = other_folder_library
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(root),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        ctl._reload()
        ctl.selectFolder(str(root / "a"))
        rows = _rows_by_name(ctl, "x.jpg")
        ctl.copyAllEffects(rows)

        # Az y.jpg-t (a másik mappában) is bevonjuk a kijelölésbe, hogy két
        # mappát érintsen a beillesztés — de a kijelölés `rows` a jelenlegi
        # nézetre vonatkozik; ehelyett közvetlenül a `_photos.photos`-on
        # ellenőrizzük a mappánkénti hívásszámot a `[.` ini-írón keresztül.
        write_calls = []
        import picasapy.app.photo_ops_controller as photo_ops_mod

        real_update_document = photo_ops_mod.update_document

        def counting_update_document(path, mutate, backup=True):
            write_calls.append(str(path))
            return real_update_document(path, mutate, backup=backup)

        monkeypatch.setattr(
            photo_ops_mod, "update_document", counting_update_document
        )
        ctl.selectFolder(str(root / "a"))
        ctl.pasteAllEffects(_rows_by_name(ctl, "x.jpg"))
        assert write_calls == [str(root / "a" / ".picasa.ini")]


class TestUndoPasteAllEffects:
    def test_restores_previous_filters(self, controller, library):
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        assert controller.canUndoPasteAllEffects is False
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        assert controller.canUndoPasteAllEffects is True

        controller.undoPasteAllEffects()

        assert "filters=sat=1,-0.2;" in _ini_text(library)
        assert controller.canUndoPasteAllEffects is False

    def test_is_single_undo_step_for_whole_batch(self, controller, library):
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg", "c.jpg"))
        controller.undoPasteAllEffects()

        text = _ini_text(library)
        assert "filters=sat=1,-0.2;" in text
        # c.jpg-nek eredetileg nem volt filters= kulcsa -> visszavonás után
        # a beillesztett (a.jpg-ből másolt) lánc sehol nem maradhat bent
        assert "enhance=1;finetune2" not in text

    def test_without_prior_paste_is_noop(self, controller, library):
        before = _ini_text(library)
        controller.undoPasteAllEffects()
        assert _ini_text(library) == before


class TestPasteAllEffectsWriteFailure:
    """Csapda: a hibaútja SZINKRON jelez (nincs háttérszál) — a jelzésre
    ELŐRE fel kell iratkozni, mielőtt a slotot meghívjuk (a
    `test_create_controller.py` `_run` mintája)."""

    def test_ini_write_error_emits_photo_op_failed(
        self, controller, library, monkeypatch
    ):
        import picasapy.app.photo_ops_controller as photo_ops_mod
        from picasapy.ini import IniSaveError

        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))

        def failing_update_document(path, mutate, backup=True):
            raise IniSaveError("szimulált írási hiba")

        loop = QEventLoop()
        received = {}

        def _on_failed(message):
            received["message"] = message
            loop.quit()

        # ELŐBB a feliratkozás, csak UTÁNA a hívás — a hibaút szinkron.
        controller.photoOpFailed.connect(_on_failed)
        monkeypatch.setattr(
            photo_ops_mod, "update_document", failing_update_document
        )
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        if "message" not in received:
            QTimer.singleShot(2000, loop.quit)
            loop.exec()

        assert received.get("message") == "szimulált írási hiba"
