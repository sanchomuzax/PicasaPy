r"""A „Keresés a lemezen" platformonként MÁS parancsot hív (#1104).

## A panasz

A tulajdonos Windowson (v0.8.23) ezt kapta:

```
A fájlművelet nem sikerült
A fájlkezelő megnyitása sikertelen (xdg-open hiányzik?):
C:\Users\…\Képek\Picasa\Kollázsok
```

A modul platform-ág nélkül `xdg-open`-t hívott. A Linux-first **helyes
projektdöntés**, de a program fut Windowson is, és ott ez nem hiba-ág volt,
hanem működésképtelenség — és nem csak a kollázsban: ugyanez a két függvény
szolgálja ki a fájl- és a mappa-kontextusmenüt (#15, #112, #422).

## Mit állítanak a tesztek

A `sys.platform`-ot fecskendezzük be (a `application.py:143`
`_force_qml_dialogs` mintájára), és a TÉNYLEGES parancssort nézzük — nem
azt, hogy „lefutott-e".

⚠️ **A Windows-ág két külön állítást igényel**, mert két külön csapda van:
az `explorer` **sikeres** megnyitásnál is nemnulla kóddal tér vissza, a
`/select,<út>` pedig **egyetlen** argumentum, vessző után szóköz nélkül.
"""

from __future__ import annotations

import pytest

from picasapy.fileops import reveal_in_file_manager
from picasapy.fileops.reveal import open_folder_in_file_manager


class _Kimenet:
    """A `subprocess.run` visszatérése, állítható kilépési kóddal."""

    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode


@pytest.fixture
def hivasok(monkeypatch):
    """A `subprocess.run` elkapva — a PARANCSSOR a vizsgálat tárgya."""
    rogzitett: list[list[str]] = []
    kimenet = _Kimenet()

    def _run(args, **_kwargs):
        rogzitett.append(list(args))
        return kimenet

    monkeypatch.setattr("picasapy.fileops.reveal.subprocess.run", _run)
    return rogzitett, kimenet


def _platform(monkeypatch, nev: str) -> None:
    monkeypatch.setattr("picasapy.fileops.reveal.sys.platform", nev)


class TestWindows:
    """`explorer` — a fájlt KI IS JELÖLI."""

    def test_a_fajlt_kijeloli(self, tmp_path, monkeypatch, hivasok):
        rogzitett, _ = hivasok
        _platform(monkeypatch, "win32")
        kep = tmp_path / "album" / "a.jpg"

        reveal_in_file_manager(kep)

        assert rogzitett == [["explorer", f"/select,{kep}"]]

    def test_a_select_EGY_argumentum_vesszo_utan_szokoz_nelkul(
        self, tmp_path, monkeypatch, hivasok
    ):
        """Szóközös, ékezetes útvonalon is — ez a tulajdonos esete."""
        rogzitett, _ = hivasok
        _platform(monkeypatch, "win32")
        kep = tmp_path / "OneDrive - centralmediacsoport" / "Képek" / "a.jpg"

        reveal_in_file_manager(kep)

        (parancs,) = rogzitett
        assert len(parancs) == 2
        assert parancs[1].startswith("/select,")
        assert not parancs[1].startswith("/select, ")
        assert parancs[1][len("/select,") :] == str(kep)

    def test_a_mappat_kijeloles_nelkul_nyitja(self, tmp_path, monkeypatch, hivasok):
        rogzitett, _ = hivasok
        _platform(monkeypatch, "win32")

        open_folder_in_file_manager(tmp_path)

        assert rogzitett == [["explorer", str(tmp_path)]]

    def test_a_nemnulla_kilepesi_kod_NEM_hiba(self, tmp_path, monkeypatch, hivasok):
        """Az `explorer` sikeres megnyitásnál is nemnullát ad — a régi
        szabály itt HAMIS hibaüzenetet adott volna."""
        _, kimenet = hivasok
        kimenet.returncode = 1
        _platform(monkeypatch, "win32")

        open_folder_in_file_manager(tmp_path)  # nem emel kivételt

    def test_a_hianyzo_binaris_TOVABBRA_is_hiba(self, tmp_path, monkeypatch):
        _platform(monkeypatch, "win32")

        def _raise(*_a, **_k):
            raise FileNotFoundError("nincs explorer")

        monkeypatch.setattr("picasapy.fileops.reveal.subprocess.run", _raise)

        with pytest.raises(OSError):
            open_folder_in_file_manager(tmp_path)


class TestMacOS:
    def test_a_fajlt_kijeloli(self, tmp_path, monkeypatch, hivasok):
        rogzitett, _ = hivasok
        _platform(monkeypatch, "darwin")
        kep = tmp_path / "a.jpg"

        reveal_in_file_manager(kep)

        assert rogzitett == [["open", "-R", str(kep)]]

    def test_a_mappat_egyszeruen_nyitja(self, tmp_path, monkeypatch, hivasok):
        rogzitett, _ = hivasok
        _platform(monkeypatch, "darwin")

        open_folder_in_file_manager(tmp_path)

        assert rogzitett == [["open", str(tmp_path)]]


class TestLinuxValtozatlan:
    """A jegy kikötése: linuxon a viselkedés BITRE ugyanaz marad."""

    def test_a_SZULOMAPPAT_nyitja_xdg_opennel(self, tmp_path, monkeypatch, hivasok):
        rogzitett, _ = hivasok
        _platform(monkeypatch, "linux")
        kep = tmp_path / "album" / "a.jpg"
        kep.parent.mkdir()

        reveal_in_file_manager(kep)

        assert rogzitett == [["xdg-open", str(kep.parent)]]

    def test_a_nemnulla_kilepesi_kod_TOVABBRA_is_hiba(
        self, tmp_path, monkeypatch, hivasok
    ):
        _, kimenet = hivasok
        kimenet.returncode = 1
        _platform(monkeypatch, "linux")

        with pytest.raises(OSError):
            open_folder_in_file_manager(tmp_path)
