"""Három párbeszéd NYERS URL-alakban írta ki a mappa útvonalát — #1629.

Windowson `/C:/Users/…` jelent meg `C:\\Users\\…` helyett, mert mindhárom
hely szöveges cserével vágta le a `file://` előtagot. Az érintett helyek:
`ExportDialogs.qml`, `ImportSourceDialog.qml` (kétszer),
`MoveDatabaseDialog.qml`.

## Miért nem oldható meg QML-ből

A `QUrl.toLocalFile()` a meghajtóbetű elé tett perjelet **csak Windowson**
szedi le (a `QUrlPrivate::toLocalFile` megfelelő ága `#ifdef Q_OS_WIN`
alatt áll) — ezt a #1626 lemérte. A helyes átalakítás ezért Python-oldali,
és a #1626 `formatting.to_local_path`-ját használja, EGYETLEN helyen.

## Miért nincs `skipif` ebben a fájlban

A #1560 hibája: egy `skipif`-fel windowsra kötött ág Linuxon SOSEM fut, és
a CI ubuntu-lába üresen zölden hagyja. A `to_local_path` a `_platform()`
fogantyún át dolgozik, tehát a windowsos ág **Linuxon is végigmérhető** —
ez a fájl ezt teszi.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest

from picasapy.app import formatting

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_EXPORT = (_QML / "ExportDialogs.qml").read_text(encoding="utf-8")
_IMPORT = (_QML / "ImportSourceDialog.qml").read_text(encoding="utf-8")
_MOVEDB = (_QML / "MoveDatabaseDialog.qml").read_text(encoding="utf-8")
#: ⚠️ A három forrás NEVEZVE, nem paraméterként átadva. A `parametrize` a
#: paraméter ÉRTÉKÉBŐL képez teszt-azonosítót, és a pytest azt a
#: `PYTEST_CURRENT_TEST` KÖRNYEZETI VÁLTOZÓBA is kiírja — egy egész
#: QML-fájllal az azonosító átlépi a Windows 32767 karakteres korlátját,
#: és a teszt `ValueError`-ral MÁR A SETUPBAN elhasal. Linuxon ez nem
#: látszik; a CI windows-lába fogta meg (#1629).
_FORRASOK = {
    "ExportDialogs": _EXPORT,
    "ImportSourceDialog": _IMPORT,
    "MoveDatabaseDialog": _MOVEDB,
}

_FILEOPS = (
    Path(picasapy.app.__file__).parent / "fileops_controller.py"
).read_text(encoding="utf-8")


class TestAzAtalakitas:
    def test_windowson_NEM_marad_vezeto_perjel(self, monkeypatch):
        """A lelet magja: `/C:/Users/…` helyett `C:\\Users\\…`."""
        monkeypatch.setattr(formatting, "_platform", lambda: "win32")
        eredmeny = formatting.to_local_path("file:///C:/Users/sancho/Képek")
        assert not eredmeny.startswith("/")
        assert eredmeny.startswith("C:")

    def test_linuxon_valtozatlan(self, monkeypatch):
        #: ⚠️ A várt értéket `str(Path(...))` állítja elő, nem beégetett
        #: per-jeles sztring: Windowson a `to_local_path` visszaperjelet
        #: ad, és a beégetett mérce ott elbukna (#1634 — a
        #: `test_windows_csapdak_1082` őre pontosan ezt fogja meg, és
        #: ezt a fájlt is elkapta az első körben).
        monkeypatch.setattr(formatting, "_platform", lambda: "linux")
        assert formatting.to_local_path("file:///home/s/kepek") == str(
            Path("/home/s/kepek")
        )

    def test_ures_bemenetre_ures(self):
        assert formatting.to_local_path("") == ""

    def test_a_sima_utvonal_is_atmegy(self, monkeypatch):
        monkeypatch.setattr(formatting, "_platform", lambda: "linux")
        assert formatting.to_local_path("/home/s/kepek") == str(
            Path("/home/s/kepek")
        )


class TestASlot:
    @pytest.fixture
    def ctl(self, qt_app, tmp_path):
        from picasapy.app.fileops_controller import FileOpsController
        import inspect

        parameterek = inspect.signature(FileOpsController.__init__).parameters
        kwargs = {}
        if "db_path" in parameterek:
            kwargs["db_path"] = tmp_path / "index.db"
        return FileOpsController(**kwargs)

    def test_a_slot_a_KOZOS_fuggvenyt_hivja(self):
        """A jegy kiköti: az átalakítás EGYETLEN helyen éljen, ne másolva."""
        kezd = _FILEOPS.index("def toLocalPath(")
        blokk = _FILEOPS[kezd : kezd + 1400]
        assert "return to_local_path(path_or_url)" in blokk
        # Saját, kézi levágás NEM lehet benne — az lenne a másolás.
        assert "replace(" not in blokk

    def test_a_slot_windowson_natívot_ad(self, ctl, monkeypatch):
        monkeypatch.setattr(formatting, "_platform", lambda: "win32")
        assert ctl.toLocalPath("file:///C:/Users/s/K").startswith("C:")


class TestAHaromParbeszed:
    @pytest.mark.parametrize("nev", sorted(_FORRASOK))
    def test_a_vezerlon_at_alakit(self, nev):
        assert "fileOpsController.toLocalPath(" in _FORRASOK[nev], nev

    def test_az_importban_MINDKET_utvonal_at_van_kotve(self):
        """A jegy két helyet nevez meg ebben a fájlban (:87 és :89)."""
        assert _IMPORT.count("fileOpsController.toLocalPath(") == 2

    @pytest.mark.parametrize("nev", sorted(_FORRASOK))
    def test_a_nyers_levagas_CSAK_tartalekagkent_marad(self, nev):
        """A szöveges csere megmarad annak az ágnak, ahol a vezérlő nincs
        regisztrálva (önálló próbák) — de MINDIG a `toLocalPath` UTÁN,
        tartalékként, nem helyette."""
        forras = _FORRASOK[nev]
        for i, sor in enumerate(forras.split("\n")):
            if "replace(/^file:" not in sor:
                continue
            korny = "\n".join(forras.split("\n")[max(0, i - 6) : i + 1])
            assert "toLocalPath(" in korny, (
                f"{nev}: a {i + 1}. sor nyers levágása nincs a vezérlős ág "
                "mögé kötve"
            )
