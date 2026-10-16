"""#4533: a „Társítás…" háttere — a freedesktop-társítások és az indítás.

Valódi `.desktop` és `mimeapps.list` fájlokat írunk egy ideiglenes XDG-fába,
és a `XDG_*` változókkal oda irányítjuk a modult.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.fileops.open_with as open_with


@pytest.fixture
def xdg(tmp_path, monkeypatch):
    """Üres XDG-fa: a felhasználói és a rendszer-szintű útvonalak is a tmp alatt."""
    otthon = tmp_path / "otthon"
    rendszer = tmp_path / "rendszer"
    monkeypatch.setenv("XDG_DATA_HOME", str(otthon / "share"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(otthon / "config"))
    monkeypatch.setenv("XDG_DATA_DIRS", str(rendszer / "share"))
    monkeypatch.setenv("XDG_CONFIG_DIRS", str(rendszer / "config"))
    monkeypatch.setenv("LANG", "hu_HU.UTF-8")
    return tmp_path


def _desktop(konyvtar: Path, nev: str, tartalom: str) -> None:
    (konyvtar / "applications").mkdir(parents=True, exist_ok=True)
    (konyvtar / "applications" / nev).write_text(tartalom, encoding="utf-8")


def _entry(name: str, exec_line: str, extra: str = "") -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        f"Exec={exec_line}\n"
        f"{extra}"
    )


def _mimeapps(konyvtar: Path, tartalom: str) -> None:
    konyvtar.mkdir(parents=True, exist_ok=True)
    (konyvtar / "mimeapps.list").write_text(tartalom, encoding="utf-8")


def test_a_mime_tipushoz_tarsitott_alkalmazasok_a_sorrendben_adodnak(xdg):
    felhasznalo = xdg / "otthon" / "share"
    _desktop(felhasznalo, "gimp.desktop", _entry("GIMP", "gimp %U"))
    _desktop(felhasznalo, "eog.desktop", _entry("Képnézegető", "eog %U"))
    _mimeapps(
        xdg / "otthon" / "config",
        "[Default Applications]\nimage/jpeg=eog.desktop;\n"
        "[Added Associations]\nimage/jpeg=gimp.desktop;eog.desktop;\n",
    )

    alkalmazasok = open_with.apps_for_file(Path("kep.jpg"))

    assert [a.app_id for a in alkalmazasok] == ["eog.desktop", "gimp.desktop"]


def test_a_lokalizalt_nev_a_nyelvi_kulcsot_hasznalja(xdg):
    felhasznalo = xdg / "otthon" / "share"
    _desktop(
        felhasznalo,
        "gimp.desktop",
        _entry("GIMP", "gimp %U", "Name[hu]=GIMP (magyar)\n"),
    )
    _mimeapps(
        xdg / "otthon" / "config",
        "[Added Associations]\nimage/png=gimp.desktop;\n",
    )

    (alkalmazas,) = open_with.apps_for_file(Path("kep.png"))

    assert alkalmazas.name == "GIMP (magyar)"


def test_rejtett_es_nem_megjelenitheto_alkalmazas_kimarad(xdg):
    felhasznalo = xdg / "otthon" / "share"
    _desktop(
        felhasznalo,
        "rejtett.desktop",
        _entry("Rejtett", "rejtett %f", "Hidden=true\n"),
    )
    _desktop(
        felhasznalo,
        "nincs-megjelenitve.desktop",
        _entry("Belső", "belso %f", "NoDisplay=true\n"),
    )
    _desktop(felhasznalo, "latszik.desktop", _entry("Látszik", "latszik %f"))
    _mimeapps(
        xdg / "otthon" / "config",
        "[Added Associations]\nimage/gif="
        "rejtett.desktop;nincs-megjelenitve.desktop;latszik.desktop;\n",
    )

    alkalmazasok = open_with.apps_for_file(Path("kep.gif"))

    assert [a.app_id for a in alkalmazasok] == ["latszik.desktop"]


def test_ismeretlen_tipushoz_ures_a_lista(xdg):
    assert open_with.apps_for_file(Path("valami.ismeretlen-kiterjesztes")) == []


def test_hianyzo_desktop_fajl_nem_hiba(xdg):
    _mimeapps(
        xdg / "otthon" / "config",
        "[Added Associations]\nimage/jpeg=nincs-ilyen.desktop;\n",
    )

    assert open_with.apps_for_file(Path("kep.jpg")) == []


@pytest.mark.parametrize(
    ("exec_line", "elvart"),
    [
        ("gimp %U", ["gimp", "/k/kep.jpg"]),
        ("eog --new-instance %F", ["eog", "--new-instance", "/k/kep.jpg"]),
        ("feh --scale-down %f", ["feh", "--scale-down", "/k/kep.jpg"]),
        # nincs fájlmező: a kép a végére kerül
        ("ristretto", ["ristretto", "/k/kep.jpg"]),
        # ismeretlen kódok kimaradnak, a %% valódi százalékjel lesz
        ("app %c %i --title=100%% %u", ["app", "--title=100%", "/k/kep.jpg"]),
        # idézett argumentum egy tokenben marad
        ('viewer "Kép neve" %f', ["viewer", "Kép neve", "/k/kep.jpg"]),
    ],
)
def test_exec_argumentumok_a_fajl_helyere_kerulnek(exec_line, elvart):
    # A fájl a platform saját alakjában kerül az argumentumba (Windowson
    # `\\k\\kep.jpg`) — a várt listát ugyanígy képezzük (#4831).
    kep = Path("/k/kep.jpg")
    elvart = [str(kep) if elem == "/k/kep.jpg" else elem for elem in elvart]
    assert open_with.exec_argv(exec_line, kep) == elvart


def test_inditas_a_valasztott_alkalmazassal_a_kep_utvonalaval(monkeypatch):
    hivasok = []
    monkeypatch.setattr(
        open_with,
        "_popen",
        lambda argv, **kwargs: hivasok.append((argv, kwargs)),
    )
    app = open_with.OpenWithApp("eog.desktop", "Képnézegető", "eog %F")

    kep = Path("/k/kep.jpg")
    open_with.launch_app(app, kep)

    # A fájl a platform saját alakjában kerül az argumentumba (#4835).
    (argv, kwargs), = hivasok
    assert argv == ["eog", str(kep)]
    assert kwargs["start_new_session"] is True
