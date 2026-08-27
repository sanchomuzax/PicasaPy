"""#1526: a `FileOpsController` vágólap-szelete — a MODULSZINTŰ fogantyún át.

A felületi mérés (`qml_functional/test_vagolap_parancsok_1526.py`) a valódi
Qt-vágólapot használja, mert az `offscreen` platformon folyamaton belüli és
megbízható. Ez a fájl a másik oldalt fedi: azokat az ágakat, amelyeket a
valódi vágólappal nehéz vagy lehetetlen előállítani —

* **nincs vágólap** (fejetlen, `QGuiApplication` nélküli környezet),
* **eltűnt forrásfájl** (a vágólap túléli a fájl törlését),
* **idegen alkalmazás** hasznos terhe (`text/plain` a fájlok mellett).

A csere a `fileops_controller._clipboard()` függvényen történik — a
`reveal.py` `_run`-jának és a `trash.py` `_stat`-jának mintája. A globális
Qt-osztályt SZÁNDÉKOSAN nem írjuk át: arra külön őrünk van (#1375).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QObject, Signal

from picasapy.app import fileops_controller as modul
from picasapy.app.fileops_controller import FileOpsController
from picasapy.fileops.clipboard import (
    COPY,
    CUT,
    GNOME_COPIED_FILES,
    URI_LIST,
    gnome_payload,
    parse_gnome_payload,
    uri_list_payload,
)

# A vágólapot tesztenként el kell engedni, különben a folyamat SIGSEGV-vel
# áll le (#1526) — az indoklás a fixture docstringjében.
pytestmark = pytest.mark.usefixtures("vagolap_elengedese")


class HamisVagolap(QObject):
    """Folyamaton belüli vágólap-utánzat: annyit tud, amennyit használunk.

    `QObject`, mert a vezérlő a `dataChanged`-re köt — a menüpont
    szürkülése ettől él, tehát a hamisítványnak is jeleznie kell.
    """

    dataChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._data: QMimeData | None = None
        self._text = ""

    # -- a Qt felülete
    def mimeData(self):  # noqa: N802 — a Qt nevét követi
        return self._data

    def setMimeData(self, data) -> None:  # noqa: N802
        self._data = data
        self._text = ""
        self.dataChanged.emit()

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = text
        csomag = QMimeData()
        csomag.setText(text)
        self._data = csomag
        self.dataChanged.emit()

    def clear(self) -> None:
        self._data = None
        self._text = ""
        self.dataChanged.emit()


@pytest.fixture
def vagolap(monkeypatch):
    board = HamisVagolap()
    monkeypatch.setattr(modul, "_clipboard", lambda: board)
    return board


@pytest.fixture
def vezerlo(vagolap):
    return FileOpsController()


def _teher(vagolap, mime: str) -> bytes:
    return bytes(vagolap.mimeData().data(mime))


class TestMasolasEsKivagas:
    def test_a_masolas_mindket_formatumot_felteszi(self, vezerlo, vagolap, tmp_path):
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        vezerlo.copyToClipboard([str(kep)])
        formatumok = vagolap.mimeData().formats()
        assert URI_LIST in formatumok
        assert GNOME_COPIED_FILES in formatumok

    def test_a_kivagas_jelzese_cut(self, vezerlo, vagolap, tmp_path):
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        vezerlo.cutToClipboard([str(kep)])
        assert parse_gnome_payload(_teher(vagolap, GNOME_COPIED_FILES))[0] == CUT

    def test_a_ket_muvelet_uri_listaja_azonos(self, vezerlo, vagolap, tmp_path):
        kepek = []
        for nev in ("a.jpg", "b.jpg"):
            ut = tmp_path / nev
            ut.write_bytes(b"x")
            kepek.append(str(ut))
        vezerlo.copyToClipboard(kepek)
        masolas = _teher(vagolap, URI_LIST)
        vezerlo.cutToClipboard(kepek)
        assert _teher(vagolap, URI_LIST) == masolas

    def test_file_url_bemenetet_is_elfogad(self, vezerlo, vagolap, tmp_path):
        """A QML néhol `file://` URL-t ad — a `_to_local_path` oldja fel."""
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        vezerlo.copyToClipboard([kep.as_uri()])
        assert vezerlo.clipboardPaths() == [str(kep)]

    def test_ures_lista_nem_nyul_a_vagolaphoz(self, vezerlo, vagolap, tmp_path):
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        vezerlo.copyToClipboard([str(kep)])
        elotte = _teher(vagolap, URI_LIST)
        vezerlo.copyToClipboard([])
        assert _teher(vagolap, URI_LIST) == elotte


class TestVisszaolvasas:
    def test_eltunt_fajl_kimarad(self, vezerlo, vagolap, tmp_path):
        """A vágólap túléli a forrásfájl törlését — a hiányzó fájl a
        kötegben csak fölösleges hibasor lenne."""
        elo = tmp_path / "elo.jpg"
        elo.write_bytes(b"x")
        halott = tmp_path / "halott.jpg"
        csomag = QMimeData()
        csomag.setData(URI_LIST, uri_list_payload([elo, halott]))
        csomag.setData(GNOME_COPIED_FILES, gnome_payload([elo, halott], COPY))
        vagolap.setMimeData(csomag)
        assert vezerlo.clipboardPaths() == [str(elo)]

    def test_csak_szoveges_vagolapnal_nincs_fajl(self, vezerlo, vagolap):
        vagolap.setText("nem fájl")
        assert vezerlo.clipboardPaths() == []
        assert vezerlo.hasClipboardFiles is False

    def test_muvelet_jelzes_nelkuli_fajllista_MASOLAS(
        self, vezerlo, vagolap, tmp_path
    ):
        """Egy `text/uri-list`-et adó, de művelet-jelzés nélküli forrás
        (pl. böngésző) nem vihet el fájlt a forrásmappából."""
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        csomag = QMimeData()
        csomag.setData(URI_LIST, uri_list_payload([kep]))
        vagolap.setMimeData(csomag)
        assert vezerlo.clipboardEffect() == COPY


class TestSzoveg:
    def test_a_beallitott_szoveg_visszaolvashato(self, vezerlo, vagolap):
        vezerlo.setClipboardText("Nyári kép")
        assert vezerlo.clipboardText() == "Nyári kép"
        assert vezerlo.hasClipboardText is True

    def test_fajlos_vagolap_szovege_URES(self, vezerlo, vagolap, tmp_path):
        """A fájlkezelők a `text/uri-list` mellé `text/plain`-t is tesznek
        (a fájlnevekkel) — azt feliratként beírni néma adatrongálás volna."""
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        csomag = QMimeData()
        csomag.setData(URI_LIST, uri_list_payload([kep]))
        csomag.setText(str(kep))
        vagolap.setMimeData(csomag)
        assert vezerlo.clipboardText() == ""
        assert vezerlo.hasClipboardText is False

    def test_urites(self, vezerlo, vagolap):
        vezerlo.setClipboardText("valami")
        vezerlo.clearClipboard()
        assert vezerlo.hasClipboardText is False
        assert vezerlo.hasClipboardFiles is False


class TestVagolapNelkul:
    """Fejetlen környezet: a vágólap hiánya nem hibaág, csak nincs hova
    másolni (a `copyFullPath` már eddig is így viselkedett)."""

    @pytest.fixture
    def nincs_vagolap(self, monkeypatch):
        monkeypatch.setattr(modul, "_clipboard", lambda: None)
        return FileOpsController()

    def test_masolas_nem_dob(self, nincs_vagolap, tmp_path):
        nincs_vagolap.copyToClipboard([str(tmp_path / "a.jpg")])

    def test_lekerdezesek_ures_valaszt_adnak(self, nincs_vagolap):
        assert nincs_vagolap.clipboardPaths() == []
        assert nincs_vagolap.clipboardText() == ""
        assert nincs_vagolap.clipboardEffect() == COPY
        assert nincs_vagolap.hasClipboardFiles is False
        assert nincs_vagolap.hasClipboardText is False

    def test_urites_nem_dob(self, nincs_vagolap):
        nincs_vagolap.clearClipboard()

    def test_teljes_ut_masolasa_nem_dob(self, nincs_vagolap, tmp_path):
        nincs_vagolap.copyFullPath(str(tmp_path / "a.jpg"))


class TestFogantyu:
    def test_a_termek_a_modulszintu_fogantyun_at_er_a_vagolaphoz(self):
        """Ha valaki visszaírja a közvetlen `QGuiApplication.clipboard()`
        hívást, ez a teszt bukik — a fogantyú nélkül a fenti ágak
        mérhetetlenek."""
        forras = Path(modul.__file__).read_text(encoding="utf-8")
        # a `_clipboard()` definícióján KÍVÜL nincs közvetlen hívás
        assert forras.count("QGuiApplication.clipboard()") == 1
