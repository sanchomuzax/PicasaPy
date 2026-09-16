"""#3184 — az arcátvételnek HÍVÓJA lett: a #2336 futtatója viszi ki.

## Mit rögzít ez a lap

A #3002 megírta az arcátvétel tiszta átalakítóját (`arcatvetel.arcokat_atvesz`),
de **hívó nélkül** maradt: a db3-ban álló arcok sehogy nem jutottak el a
`.picasa.ini`-be. A #2336 közben megírta a futtatót (mappánként EGY írás az
`update_document` ütközésbiztos útján) — ez a lap azt méri, hogy az arcok
ugyanabba a ciklusba kerültek be.

## Amit a jegy „Kész, ha" listája kér, és amit itt mérünk

* egy mappa **EGY** írás — nem három (kulcsszó, hely, arc külön);
* a jelentés **külön** számolja az arcokat;
* a `[Contacts2]` szakasz csak az arcírással EGYÜTT keletkezik (nincs árva
  kontakt);
* `frversion = "1.5"` a `[Picasa]` szakaszba, ha írtunk arcot;
* a meglévő `faces=` **érintetlen** marad — és a száraz futás sem hozza
  létre az ini-t, ha semmi nem írható.
"""

from __future__ import annotations

from picasapy.ini.document import parse_document
from picasapy.pmpimport.deferredregion import DeferredFace
from picasapy.pmpimport.importer import PhotoRecord
from picasapy.pmpimport.db3_atvetel import (
    AtvetelJelentes,
    rekordokat_atvesz,
)
from picasapy.ini.rect64 import Rect64


def _rect(x: float = 0.1) -> Rect64:
    return Rect64(left=x, top=x, right=x + 0.2, bottom=x + 0.2)


def _rekord(ut: str, *, tags=(), lat=None, lon=None, faces=()) -> PhotoRecord:
    return PhotoRecord(
        local_path=ut,
        windows_path="C:\\\\nincs",
        row=0,
        caption=None,
        rotate=None,
        star=False,
        filters=None,
        crop64=None,
        tags=tags,
        latitude=lat,
        longitude=lon,
        faces=faces,
    )


def _ini(mappa) -> str:
    ut = mappa / ".picasa.ini"
    return ut.read_text(encoding="utf-8") if ut.exists() else ""


class TestAFuttatoKiviszi:
    def test_az_arc_es_a_kontakt_kikerul_az_iniben(self, tmp_path):
        (tmp_path / "kep.jpg").write_bytes(b"")
        jelentes = rekordokat_atvesz(
            [
                _rekord(
                    str(tmp_path / "kep.jpg"),
                    faces=(DeferredFace(rect=_rect(), name="Kiss Anna"),),
                )
            ]
        )
        szoveg = _ini(tmp_path)
        assert "faces=" in szoveg
        assert "Kiss Anna" in szoveg
        assert "[Contacts2]" in szoveg
        assert 'frversion=1.5' in szoveg.replace('"', "")
        assert jelentes.arc == 1
        assert jelentes.mappak == 1

    def test_arc_NELKUL_nincs_kontakt_szakasz(self, tmp_path):
        """Nincs árva kontakt: kulcsszó-csak adatnál a `[Contacts2]` sem jön."""
        (tmp_path / "kep.jpg").write_bytes(b"")
        rekordokat_atvesz([_rekord(str(tmp_path / "kep.jpg"), tags=("nyar",))])
        szoveg = _ini(tmp_path)
        assert "keywords=nyar" in szoveg
        assert "[Contacts2]" not in szoveg
        assert "frversion" not in szoveg

    def test_a_meglevo_faces_erintetlen_es_kihagyottnak_szamit(self, tmp_path):
        (tmp_path / "kep.jpg").write_bytes(b"")
        (tmp_path / ".picasa.ini").write_text(
            "[kep.jpg]\nfaces=rect64(1234567812345678),abcdef0123456789\n",
            encoding="utf-8",
        )
        jelentes = rekordokat_atvesz(
            [
                _rekord(
                    str(tmp_path / "kep.jpg"),
                    faces=(DeferredFace(rect=_rect(), name="Kiss Anna"),),
                )
            ]
        )
        szoveg = _ini(tmp_path)
        assert "Kiss Anna" not in szoveg
        assert "abcdef0123456789" in szoveg
        assert jelentes.arc == 0
        assert jelentes.kihagyott == 1

    def test_csak_arc_eseten_is_IR(self, tmp_path):
        """⛔ A száraz futás korábban csak a kulcsszót és a helyet nézte: a
        csak-arc adatú mappa így NÉMÁN kimaradt volna."""
        (tmp_path / "kep.jpg").write_bytes(b"")
        rekordokat_atvesz(
            [
                _rekord(
                    str(tmp_path / "kep.jpg"),
                    faces=(DeferredFace(rect=_rect(), name="Nagy Béla"),),
                )
            ]
        )
        assert (tmp_path / ".picasa.ini").exists()
        assert "Nagy Béla" in _ini(tmp_path)

    def test_semmi_adat_semmi_fajl(self, tmp_path):
        (tmp_path / "kep.jpg").write_bytes(b"")
        jelentes = rekordokat_atvesz([_rekord(str(tmp_path / "kep.jpg"))])
        assert not (tmp_path / ".picasa.ini").exists()
        assert jelentes == AtvetelJelentes()


class TestEgyMappaEgyIras:
    def test_a_harom_adatfajta_EGY_irasban_megy_ki(self, tmp_path, monkeypatch):
        """A jegy kikötése: „egy mappa egy írás, ne három."""
        from picasapy.pmpimport import db3_atvetel as modul

        hivasok = []
        igazi = modul.update_document

        def szamolo(ut, mutate, **kw):
            hivasok.append(ut)
            return igazi(ut, mutate, **kw)

        monkeypatch.setattr(modul, "update_document", szamolo)

        (tmp_path / "kep.jpg").write_bytes(b"")
        jelentes = rekordokat_atvesz(
            [
                _rekord(
                    str(tmp_path / "kep.jpg"),
                    tags=("nyar",),
                    lat=47.5,
                    lon=19.05,
                    faces=(DeferredFace(rect=_rect(), name="Kiss Anna"),),
                )
            ]
        )
        assert len(hivasok) == 1, f"{len(hivasok)} írás egy mappára"
        assert jelentes == AtvetelJelentes(
            mappak=1, kulcsszo=1, hely=1, arc=1, kihagyott=0
        )
        szoveg = _ini(tmp_path)
        dok = parse_document(szoveg)
        szakasz = dok.section("kep.jpg")
        assert szakasz.get("keywords") == "nyar"
        assert szakasz.get("geotag")
        assert szakasz.get("faces")
