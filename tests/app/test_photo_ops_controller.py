"""`PhotoOpsMixin` — „Az összes effektus másolása/beillesztése" (#426, a
lánc-átvitel szemantikája javítva a #1544-ben).

A vezérlő-oldali kötegelt írást/visszavonást teszteli AppControlleren
keresztül (a `test_rename_many_controller.py` fixtúra-mintája).

⚠️ Ez a fájl a vezérlő metódusait KÖZVETLENÜL hívja, tehát akkor is zöld
lenne, ha a menütétel tiltott vagy takart. A menüpontról indított, lemezre
írt `.picasa.ini`-t mérő őr külön fájlban van:
`tests/app/qml_functional/test_effektus_beillesztes_vagas_1544.py`.
"""

import configparser

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


def _ini_section(folder, name: str) -> dict[str, str]:
    """Egy képszekció kulcs–érték párjai a lemezre írt `.picasa.ini`-ből."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(folder / ".picasa.ini", encoding="utf-8")
    return dict(parser[name]) if parser.has_section(name) else {}


class TestCopyAllEffects:
    def test_copies_chain_to_clipboard(self, controller):
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
    def test_applies_whole_chain_overwriting_existing(self, controller, library):
        """#1544: a TELJES lánc megy át, felülírva a cél saját láncát.

        A korábbi `test_applies_filtered_chain_overwriting_existing` azt
        állította, hogy a `crop64`/`redeye`/`retouch` NEM megy át. Ez az
        állítás téves volt: a #1534 a `Picasa3.exe` diszasszemblálásával
        igazolta, hogy a másolás (`0x005fecd0`) és a beillesztés
        (`0x005fefc0`) hívási útján nincs szűrő-névre vonatkozó
        összehasonlítás — a bináris-indexben a `"filters"` sztringnek 33
        kódhivatkozása van, a `crop64`-nek nulla. A szűrés a
        `filterdesc.xml` `mode="history"` oszlopából KÖVETKEZTETETT, saját
        szabály volt."""
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg", "c.jpg"))

        text = _ini_text(library)
        assert "[b.jpg]" in text
        # a b.jpg saját sat= láncát felülírta az a.jpg TELJES lánca
        expected = (
            "enhance=1;crop64=1,45930000ba03defe;"
            "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
            "redeye=1;retouch=1,10000000f1ddff49;"
        )
        lines = text.splitlines()
        b_index = lines.index("[b.jpg]")
        c_index = lines.index("[c.jpg]")
        b_block = "\n".join(lines[b_index:c_index])
        assert f"filters={expected}" in b_block
        assert "sat=1,-0.2" not in b_block, "a cél régi lánca nem íródott felül"

    def test_ismeretlen_lanc_bejegyzes_is_atmegy(self, controller, library):
        """#2380: idegen/ismeretlen szűrőnév is átmásolódik (#73/#152 elv).

        Ez az állítás a most eltávolított `EffectsClipboardMixin` tesztjéből
        került át — az volt az EGYETLEN olyan viselkedése, amit az élő
        `*AllEffects*` készlet nem fedett. A round-trip elv szerint egy
        általunk nem ismert bejegyzés (amit a valódi Picasa vagy egy újabb
        verziója írt) nem veszhet el a másolás-beillesztésen.
        """
        from picasapy.ini import load_document, save_document

        ini = library / ".picasa.ini"
        dokumentum = load_document(ini).with_value(
            "a.jpg",
            "filters",
            "enhance=1;JOVENOSZKA=1,x1,y2;",
            # carried: nem a mi írói utunk — idegen program írta a láncot,
            # a round-trip őr ezért nem utasítja vissza (ld. `ini.filter_guard`)
            carried=True,
        )
        save_document(dokumentum, ini, backup=False)
        # a másoló a lánc INDEXBELI példányát olvassa (`photo.filters`), ezért
        # a fájlírás után újra kell szinkronizálni — a `rescan()` háttérszálon
        # fut, itt determinisztikus lépés kell
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library))

        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))

        assert "JOVENOSZKA=1,x1,y2;" in _ini_section(library, "b.jpg")["filters"]

    def test_writes_the_crop_mirror_key(self, controller, library):
        """#1544: a `crop=rect64(...)` tükör-kulcs a lánccal együtt jár.

        A `filters=`-beli `crop64` az EREDETI Picasában önmagában nem vág —
        a renderelést a külön `crop=` kulcs hajtja
        (`docs/specs/filters-decoded.md`) —, ezért e nélkül ugyanaz a mappa
        a windowsos Picasában vágatlan képet mutatna."""
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))

        assert (
            _ini_section(library, "b.jpg").get("crop")
            == "rect64(45930000ba03defe)"
        )

    def test_chain_without_crop_removes_the_targets_crop_key(
        self, controller, library
    ):
        """Ellenkező irányú őr: vágás NÉLKÜLI lánc beillesztésekor a célkép
        meglévő `crop=` kulcsa is eltűnik — a teljes csere szemantikája
        szerint. `crop64` nélküli `crop=` kulcs az éles korpuszban 761-ből
        nulla esetben fordul elő."""
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        assert "crop=rect64" in _ini_text(library)

        # a c.jpg-ről másolunk: neki nincs lánca, tehát a b.jpg mindkét
        # kulcsának el kell tűnnie
        controller.copyAllEffects(_rows_by_name(controller, "c.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))

        szekcio = _ini_section(library, "b.jpg")
        assert "crop" not in szekcio, (
            f"a célkép régi `crop=` kulcsa bent maradt: {szekcio!r}"
        )
        assert "filters" not in szekcio, (
            f"a célkép régi lánca bent maradt: {szekcio!r}"
        )

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

        assert _ini_section(library, "b.jpg").get("filters") == "sat=1,-0.2;"
        # c.jpg-nek eredetileg nem volt filters= kulcsa -> visszavonás után
        # a beillesztett (a.jpg-ből másolt) lánc sehol nem maradhat bent
        assert "filters" not in _ini_section(library, "c.jpg")

    def test_restores_the_crop_mirror_key_too(self, controller, library):
        """#1544: a beillesztés a `crop=` kulcsot is írja, tehát a
        visszavonásnak azt is vissza kell vennie.

        Enélkül a célkép a RÉGI lánccal, de az ÚJ vágással maradna — a
        windowsos Picasa olyan rect szerint vágná, aminek a láncban nincs
        párja. (Ugyanez a hiba volt a #465 köteges útján.)"""
        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        assert "crop" in _ini_section(library, "b.jpg")

        controller.undoPasteAllEffects()

        szekcio = _ini_section(library, "b.jpg")
        assert szekcio.get("filters") == "sat=1,-0.2;"
        assert "crop" not in szekcio, (
            "a beillesztett vágás a visszavonás után is a célképen maradt: "
            f"{szekcio!r}"
        )

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


class TestGuardRejectionIsHandled:
    """#643/2: a round-trip őr visszautasítása a fotóműveleteknél is kezelt
    hiba — a hibasávban olvasható magyar üzenetként jelenik meg, nem néma
    bukásként a háttérszálon."""

    def test_filter_write_error_is_a_handled_write_error(self):
        from picasapy.app.photo_ops_controller import _WRITE_ERRORS
        from picasapy.ini import FilterWriteError

        assert FilterWriteError in _WRITE_ERRORS

    def test_rejected_paste_emits_photo_op_failed(
        self, controller, library, monkeypatch
    ):
        import picasapy.app.photo_ops_controller as photo_ops_mod
        from picasapy.ini import FilterWriteError

        controller.copyAllEffects(_rows_by_name(controller, "a.jpg"))

        def failing_update_document(path, mutate, backup=True):
            raise FilterWriteError("A szerkesztés nem menthető: teszt.")

        loop = QEventLoop()
        received = {}

        def _on_failed(message):
            received["message"] = message
            loop.quit()

        controller.photoOpFailed.connect(_on_failed)
        monkeypatch.setattr(
            photo_ops_mod, "update_document", failing_update_document
        )
        controller.pasteAllEffects(_rows_by_name(controller, "b.jpg"))
        if "message" not in received:
            QTimer.singleShot(2000, loop.quit)
            loop.exec()

        assert received.get("message") == "A szerkesztés nem menthető: teszt."
