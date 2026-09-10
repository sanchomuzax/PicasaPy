"""A fájl-vágólap MÁSIK fele: Beillesztés (#1526).

## A mérés, amire épül

A Picasa a Windows shell-fájlátvitel formátumait teszi a vágólapra, köztük a
**`Preferred DropEffect`**-et — ez bizonyítja, hogy a Kivágás és a Másolás
UGYANAZT az adatot teszi fel, és csak ez a formátum különbözteti meg őket
(a jegy mérése: `0x005378e0`, nyolc regisztrált formátum).

Linuxon ennek a párja az `x-special/gnome-copied-files`, aminek az ELSŐ sora
`copy` vagy `cut`. A másolás oldalát a #1526 korábbi köre már megírta; ez a
fájl a beillesztést méri.

⚠️ A vágólapot NEM a valódi Qt-vágólapon keresztül próbáljuk: fej nélküli
környezetben nincs vágólap-tulajdonos, és a `setMimeData` a CI-n
szegmenshibával állította meg a tesztfájlt. Ezért a vezérlő
`_vagolap_adata()` metódusát térítjük el — ugyanazt a `QMimeData`-t adjuk,
amit a saját írónk felépít.
"""

from __future__ import annotations


import pytest
from pathlib import Path

from PySide6.QtCore import QByteArray, QMimeData, QUrl

from picasapy.app.fileops_controller import FileOpsController, vagolap_fajlok

_GNOME = "x-special/gnome-copied-files"


def _mime(utak, muvelet: str | None) -> QMimeData:
    adat = QMimeData()
    urlek = [QUrl.fromLocalFile(str(u)) for u in utak]
    adat.setUrls(urlek)
    if muvelet is not None:
        sorok = [muvelet, *(u.toString() for u in urlek)]
        adat.setData(_GNOME, QByteArray("\n".join(sorok).encode("utf-8")))
    return adat


class TestAzElemzo:
    @staticmethod
    def _utak(eredmeny):
        """Az útvonalak `Path`-ként — windowson a `QUrl.toLocalFile()` „/"-t
        ad, a `str(Path)` „\\"-t; a kettő UGYANAZ a fájl, tehát a próba nem
        az elválasztót méri (a CI windows-lába pontosan ezen bukott el)."""
        utak, muvelet = eredmeny
        return ([Path(u) for u in utak], muvelet)

    def test_a_masolas_jelzese(self, tmp_path):
        fajl = tmp_path / "a.jpg"
        fajl.write_bytes(b"x")
        assert self._utak(vagolap_fajlok(_mime([fajl], "copy"))) == (
            [fajl], "copy"
        )

    def test_a_kivagas_jelzese(self, tmp_path):
        fajl = tmp_path / "a.jpg"
        fajl.write_bytes(b"x")
        assert self._utak(vagolap_fajlok(_mime([fajl], "cut"))) == ([fajl], "cut")

    def test_jelzes_NELKUL_masolas(self, tmp_path):
        """A biztonságos alapértelmezés: egy félreértett `cut` MOZGATNA.

        Más programok (böngésző, terminál) csak `text/uri-list`-et tesznek
        fel — ott nincs `copy`/`cut` jelzés."""
        fajl = tmp_path / "a.jpg"
        fajl.write_bytes(b"x")
        assert self._utak(vagolap_fajlok(_mime([fajl], None))) == (
            [fajl], "copy"
        )

    def test_ures_vagolap(self):
        assert vagolap_fajlok(None) == ([], "copy")
        assert vagolap_fajlok(QMimeData()) == ([], "copy")

    def test_a_tavoli_url_kimarad(self):
        adat = QMimeData()
        adat.setUrls([QUrl("https://example.com/kep.jpg")])
        assert vagolap_fajlok(adat) == ([], "copy")


class TestABeillesztes:
    @pytest.fixture
    def vezerlo(self, qt_app):
        return FileOpsController()

    def test_a_masolas_atmasolja_a_fajlt(self, vezerlo, tmp_path, monkeypatch):
        forras = tmp_path / "forras"
        forras.mkdir()
        kep = forras / "a.jpg"
        kep.write_bytes(b"kep")
        cel = tmp_path / "cel"
        cel.mkdir()
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([kep], "copy"))

        assert vezerlo.pasteFilesFromClipboard(str(cel)) is True
        assert (cel / "a.jpg").exists(), "a beillesztés nem másolta át a fájlt"
        assert kep.exists(), "másoláskor a forrásnak MEG KELL maradnia"

    def test_a_kivagas_athelyezi(self, vezerlo, tmp_path, monkeypatch):
        forras = tmp_path / "forras"
        forras.mkdir()
        kep = forras / "a.jpg"
        kep.write_bytes(b"kep")
        cel = tmp_path / "cel"
        cel.mkdir()
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([kep], "cut"))

        assert vezerlo.pasteFilesFromClipboard(str(cel)) is True
        assert (cel / "a.jpg").exists()
        assert not kep.exists(), "kivágáskor a forrásnak el kell tűnnie"

    def test_ures_vagolapra_NEM_indul_muvelet(self, vezerlo, tmp_path, monkeypatch):
        """A hívó ebből tud üzenetet adni — nem néma hatástalanság."""
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: None)
        assert vezerlo.pasteFilesFromClipboard(str(tmp_path)) is False

    def test_celmappa_nelkul_sem(self, vezerlo, tmp_path, monkeypatch):
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([kep], "copy"))
        assert vezerlo.pasteFilesFromClipboard("") is False

    def test_a_menu_allapota_a_vagolapot_tukrozi(self, vezerlo, tmp_path, monkeypatch):
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: None)
        assert vezerlo.clipboardHasFiles is False
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([kep], "copy"))
        assert vezerlo.clipboardHasFiles is True
