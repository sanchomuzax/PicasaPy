"""#1526: a fájl-vágólap HASZNOS TERHE — mit teszünk fel, és mit olvasunk le.

Az eredeti Picasa a Másolás/Kivágás alatt **fájlokat** tesz a vágólapra
(nyolc windowsos shell-formátumot regisztrál indításkor, `0x005378e0`), és
a kettő különbségét egyetlen formátum hordozza: a **`Preferred DropEffect`**
(mozgatás vs. másolás). A windowsos formátumoknak nincs Linux-megfelelője
— a jegy ezt HATÓKÖRÖN KÍVÜLRE tette —, a lényeg viszont a linuxos
szabvánnyal pontosan visszaadható:

* `text/uri-list` — a fájlok listája (ezt minden fájlkezelő és
  fogadóalkalmazás érti, ez a beillesztés „adata");
* `x-special/gnome-copied-files` — a `Preferred DropEffect` megfelelője: az
  ELSŐ sora `copy` vagy `cut`, utána ugyanazok az URI-k.

Ez a modul a két hasznos teher összeállítása és visszaolvasása — tiszta
logika, Qt nélkül, hogy a formátum önmagában is mérhető legyen.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops.clipboard import (
    CUT,
    COPY,
    GNOME_COPIED_FILES,
    URI_LIST,
    gnome_payload,
    parse_gnome_payload,
    paths_from_uri_list,
    uri_list_payload,
)


class TestUriLista:
    """`text/uri-list` — a szabvány CRLF-fel választ el (RFC 2483)."""

    def test_ket_fajl_crlf_el_valasztva(self):
        adat = uri_list_payload([Path("/kepek/a.jpg"), Path("/kepek/b.jpg")])
        assert adat == b"file:///kepek/a.jpg\r\nfile:///kepek/b.jpg"

    def test_szokozos_nev_szazalekkodolva(self):
        adat = uri_list_payload([Path("/kepek/nyari kep.jpg")])
        assert adat == b"file:///kepek/nyari%20kep.jpg"

    def test_ekezetes_nev_visszaolvasva_ugyanaz(self):
        eredeti = [Path("/kepek/nyári kép.jpg")]
        assert paths_from_uri_list(uri_list_payload(eredeti)) == eredeti

    def test_lf_el_valasztott_lista_is_olvashato(self):
        """Fájlkezelőtől érkező lista LF-fel is jöhet — fogadjuk el."""
        adat = b"file:///kepek/a.jpg\nfile:///kepek/b.jpg\n"
        assert paths_from_uri_list(adat) == [
            Path("/kepek/a.jpg"),
            Path("/kepek/b.jpg"),
        ]

    def test_megjegyzes_sor_kimarad(self):
        """Az RFC szerint a `#`-kezdetű sor megjegyzés."""
        adat = b"# ez megjegyzes\r\nfile:///kepek/a.jpg"
        assert paths_from_uri_list(adat) == [Path("/kepek/a.jpg")]

    def test_nem_fajl_uri_kimarad(self):
        """Egy `http://` URI nem fájl — nem tudunk vele mit kezdeni."""
        adat = b"http://example.invalid/a.jpg\r\nfile:///kepek/a.jpg"
        assert paths_from_uri_list(adat) == [Path("/kepek/a.jpg")]

    def test_ures_bemenet_ures_lista(self):
        assert paths_from_uri_list(b"") == []


class TestGnomeHasznosTeher:
    """`x-special/gnome-copied-files` — az ELSŐ sor a művelet."""

    def test_masolas_elso_sora_copy(self):
        adat = gnome_payload([Path("/kepek/a.jpg")], COPY)
        assert adat.split(b"\n")[0] == b"copy"

    def test_kivagas_elso_sora_cut(self):
        adat = gnome_payload([Path("/kepek/a.jpg")], CUT)
        assert adat.split(b"\n")[0] == b"cut"

    def test_a_ket_muvelet_csak_az_elso_sorban_ter_el(self):
        """A jegy lelete: a Kivágás és a Másolás UGYANAZT az adatot teszi
        fel, és csak a művelet-jelzés különbözteti meg őket."""
        utak = [Path("/kepek/a.jpg"), Path("/kepek/b.jpg")]
        masolas = gnome_payload(utak, COPY).split(b"\n")
        kivagas = gnome_payload(utak, CUT).split(b"\n")
        assert masolas[1:] == kivagas[1:]
        assert masolas[0] != kivagas[0]

    def test_visszaolvasas(self):
        utak = [Path("/kepek/a.jpg"), Path("/kepek/b.jpg")]
        muvelet, vissza = parse_gnome_payload(gnome_payload(utak, CUT))
        assert muvelet == CUT
        assert vissza == utak

    def test_ismeretlen_muvelet_masolasnak_szamit(self):
        """Idegen alkalmazás bármit írhat az első sorba — a BIZTONSÁGOS
        alapértelmezés a másolás: az nem visz el fájlt a forrásból."""
        muvelet, utak = parse_gnome_payload(b"barmi\nfile:///kepek/a.jpg")
        assert muvelet == COPY
        assert utak == [Path("/kepek/a.jpg")]

    def test_ures_teher_nem_ad_utat(self):
        muvelet, utak = parse_gnome_payload(b"")
        assert muvelet == COPY
        assert utak == []

    def test_ismeretlen_muvelet_kiirasa_hiba(self):
        with pytest.raises(ValueError):
            gnome_payload([Path("/kepek/a.jpg")], "move")


class TestMimeNevek:
    def test_a_ket_mime_nev_a_linuxos_szabvany(self):
        assert URI_LIST == "text/uri-list"
        assert GNOME_COPIED_FILES == "x-special/gnome-copied-files"
