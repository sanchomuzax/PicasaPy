"""#7114: a vágólapról Beillesztés az első fájlhibánál megáll (vezérlő-szint).

Az eredeti `0x005350b0` az első végleges fájlhibánál kilép a további elemek
ciklusából; a korábbi sikeres másolatok megmaradnak. A vezérlőn ezt a
`pasteFilesFromClipboard` útja kapja meg.

**NEM SZABAD (a jegy szerint):** a fogd-és-vidd és a menüs másolás/áthelyezés
(`copyPhotos`/`movePhotos`, #301/#459) továbbra is folytatja a köteget a
hibás fájl után. Ezt itt UGYANAZON a hibás lemezű helyzeten mérjük, a vágólap
útjával egymás mellett: a kettő különbsége az, amit a jegy kér.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray, QMimeData, QUrl

from picasapy.app.fileops_controller import FileOpsController
from picasapy.fileops import batch as batch_module

_GNOME = "x-special/gnome-copied-files"


def _mime(utak, muvelet: str) -> QMimeData:
    adat = QMimeData()
    urlek = [QUrl.fromLocalFile(str(u)) for u in utak]
    adat.setUrls(urlek)
    sorok = [muvelet, *(u.toString() for u in urlek)]
    adat.setData(_GNOME, QByteArray("\n".join(sorok).encode("utf-8")))
    return adat


@pytest.fixture
def vezerlo(qt_app):
    return FileOpsController()


@pytest.fixture
def harom_kep(tmp_path):
    forras, cel = tmp_path / "forras", tmp_path / "cel"
    forras.mkdir()
    cel.mkdir()
    kepek = []
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        kep = forras / nev
        kep.write_bytes(nev.encode())
        kepek.append(kep)
    return kepek, cel


@pytest.fixture
def masodik_iras_hibas(monkeypatch):
    """A `b.jpg` másolása lemezhibára fut, a többié nem (modulfogantyún, #1375)."""
    eredeti = batch_module.copy_photo

    def copy_photo(path, dest_folder):
        if Path(path).name == "b.jpg":
            raise OSError(28, "No space left on device")
        return eredeti(path, dest_folder)

    monkeypatch.setattr(batch_module, "copy_photo", copy_photo)


def _osszegzesek(vezerlo) -> list[tuple]:
    kapott: list[tuple] = []
    vezerlo.batchFinished.connect(lambda *args: kapott.append(args))
    return kapott


def _jovahagyott_beillesztes(vezerlo, cel: Path) -> None:
    """A másik mappás kérdés után a választott köteg induljon el."""
    kerdesek = []
    vezerlo.clipboardPasteConfirmationRequested.connect(
        lambda *args: kerdesek.append(args)
    )

    assert vezerlo.pasteFilesFromClipboard(str(cel)) is True
    assert len(kerdesek) == 1, "az eltérő mappás Beillesztés nem kért jóváhagyást"
    paths, dest, operation = kerdesek[0]
    assert Path(dest) == cel
    vezerlo.runPasteBatch(operation, paths, dest, "rename")


class TestABeillesztesLeall:
    def test_masolasnal_a_masodik_hibajanal_megall(
        self, vezerlo, harom_kep, masodik_iras_hibas, monkeypatch
    ):
        (a, b, c), cel = harom_kep
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([a, b, c], "copy"))
        osszegzesek = _osszegzesek(vezerlo)

        _jovahagyott_beillesztes(vezerlo, cel)

        assert (cel / "a.jpg").read_bytes() == b"a.jpg", "az első másolat nem maradt meg"
        assert not (cel / "b.jpg").exists(), "a hibás képből félkész példány maradt"
        assert not (cel / "c.jpg").exists(), "a hiba után a harmadik kép is elindult"
        assert a.exists() and b.exists() and c.exists(), "másoláskor a forrás marad"

        assert len(osszegzesek) == 1, "EGY összegző jelzés kell, nem több"
        operation, done, skipped, failed, reason = osszegzesek[0]
        assert (operation, done, skipped, failed) == ("copy", 1, 0, 1)
        assert "b.jpg" in reason and "No space left" in reason, (
            "az összegzés nem nevezi meg a hibát"
        )

    def test_kivagasnal_is_megall_az_elso_hibanal(
        self, vezerlo, harom_kep, monkeypatch
    ):
        (a, b, c), cel = harom_kep

        eredeti = batch_module.move_photo

        def move_photo(path, dest_folder):
            if Path(path).name == "b.jpg":
                raise OSError(13, "Permission denied")
            return eredeti(path, dest_folder)

        monkeypatch.setattr(batch_module, "move_photo", move_photo)
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([a, b, c], "cut"))
        osszegzesek = _osszegzesek(vezerlo)

        _jovahagyott_beillesztes(vezerlo, cel)

        assert (cel / "a.jpg").exists() and not a.exists(), "az első áthelyezés elveszett"
        assert b.exists() and not (cel / "b.jpg").exists()
        assert c.exists() and not (cel / "c.jpg").exists(), "a harmadik kép elmozdult"
        assert len(osszegzesek) == 1
        assert osszegzesek[0][:4] == ("move", 1, 0, 1)
        assert "b.jpg" in osszegzesek[0][4] and "Permission denied" in osszegzesek[0][4]

    def test_hibatlan_beillesztes_valtozatlanul_atviszi_mindet(
        self, vezerlo, harom_kep, monkeypatch
    ):
        (a, b, c), cel = harom_kep
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([a, b, c], "copy"))

        _jovahagyott_beillesztes(vezerlo, cel)

        assert sorted(p.name for p in cel.iterdir()) == ["a.jpg", "b.jpg", "c.jpg"]

    def test_run_paste_batch_elso_hibanal_megall_es_a_valasztott_kihagyast_tartja(
        self, vezerlo, harom_kep, monkeypatch
    ):
        (a, b, c), cel = harom_kep
        meglevo_a = cel / "a.jpg"
        meglevo_a.write_bytes(b"cel-a")

        eredeti = batch_module.copy_photo

        def copy_photo(path, dest_folder):
            if Path(path).name == "b.jpg":
                raise OSError(28, "No space left on device")
            return eredeti(path, dest_folder)

        monkeypatch.setattr(batch_module, "copy_photo", copy_photo)
        osszegzesek = _osszegzesek(vezerlo)

        vezerlo.runPasteBatch(
            "copy", [str(a), str(b), str(c)], str(cel), "skip"
        )

        assert meglevo_a.read_bytes() == b"cel-a", "a skip választás felülírta a célt"
        assert not (cel / "a-1.jpg").exists(), "a skip választást átnevezésként kezelte"
        assert not (cel / "b.jpg").exists(), "a hibás másolat félkészen maradt"
        assert not (cel / "c.jpg").exists(), "az első hiba után a következő kép is elindult"
        assert len(osszegzesek) == 1
        assert osszegzesek[0][:4] == ("copy", 0, 1, 1)
        assert "b.jpg" in osszegzesek[0][4] and "No space left" in osszegzesek[0][4]

    def test_a_vagolap_nem_ragadhat_a_kovetkezo_kotegre(
        self, vezerlo, harom_kep, masodik_iras_hibas, monkeypatch
    ):
        """A megállás a BEILLESZTÉS sajátja: a következő, ugyanazon vezérlőn
        indított húzásos köteg ettől még folytatja a hibás kép után."""
        (a, b, c), cel = harom_kep
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([a, b, c], "copy"))
        _jovahagyott_beillesztes(vezerlo, cel)
        masik = cel.parent / "masik"
        masik.mkdir()

        vezerlo.copyPhotos([str(a), str(b), str(c)], str(masik), "rename")

        assert (masik / "a.jpg").exists() and (masik / "c.jpg").exists()


class TestANemSzabad:
    """A fogd-és-vidd és a menüs kötegek (#301/#459) FOLYTATJÁK a hibás fájl után."""

    def test_a_menus_masolas_folytatja(self, vezerlo, harom_kep, masodik_iras_hibas):
        (a, b, c), cel = harom_kep
        osszegzesek = _osszegzesek(vezerlo)

        vezerlo.copyPhotos([str(a), str(b), str(c)], str(cel), "rename")

        assert (cel / "a.jpg").exists() and (cel / "c.jpg").exists(), (
            "a menüs másolás megállt a hibás kép után: #301/#459 sérült"
        )
        assert not (cel / "b.jpg").exists()
        assert osszegzesek[0][:4] == ("copy", 2, 0, 1)

    def test_a_hibatlan_menus_athelyezes_folytatja(self, vezerlo, harom_kep, monkeypatch):
        (a, b, c), cel = harom_kep

        eredeti = batch_module.move_photo

        def move_photo(path, dest_folder):
            if Path(path).name == "b.jpg":
                raise OSError(13, "Permission denied")
            return eredeti(path, dest_folder)

        monkeypatch.setattr(batch_module, "move_photo", move_photo)
        osszegzesek = _osszegzesek(vezerlo)

        vezerlo.movePhotos([str(a), str(b), str(c)], str(cel), "rename")

        assert (cel / "a.jpg").exists() and (cel / "c.jpg").exists()
        assert osszegzesek[0][:4] == ("move", 2, 0, 1)
