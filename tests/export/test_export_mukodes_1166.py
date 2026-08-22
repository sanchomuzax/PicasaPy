"""Az exportálás MŰKÖDÉSE: ini-átvitel és célmappa-ütközés (#1166).

## Az eredeti — bizonyíték

Teljes levezetés: `docs/specs/export-parbeszed.md` 8. és 13. szakasz. A
mappa-export, az e-mail-küldés és a képernyővédő **ugyanazt a magot**
használja (`CImageOutput`, `0x0073f320`). A mag két, eddig hiányzó
viselkedése:

1. **A `.picasa.ini` `caption` és `keywords` mezője átkerül** a
   célmappába (a sztringek a függvényben, `0x0073f320`);
2. **Ha a célmappa már létezik**, a program megkérdezi
   (`CExportPrefsPage::destexists` — „A cél már létezik. Felülírja az új
   albummal?"), és igen esetén az **előző albumot törli**.

⚠️ Az ini-írás az `ini/` csomag API-ján megy (`update_document`) — a
projekt sáv-invariánsa szerint közvetlen fájlírás sehol máshol nincs.
"""

from pathlib import Path

import pytest

from picasapy.export.exporter import ExportItem, ExportSettings, export_photos
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME


def _kep(utvonal: Path, meret=(64, 48)) -> Path:
    import numpy as np
    import cv2

    utvonal.parent.mkdir(parents=True, exist_ok=True)
    tomb = np.full((meret[1], meret[0], 3), 128, dtype=np.uint8)
    cv2.imwrite(str(utvonal), tomb)
    return utvonal


class TestIniAtvitel:
    def test_a_felirat_es_a_cimkek_atkerulnek(self, tmp_path):
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=forras, caption="Nyaralás", keywords="tenger,nyár")],
            cel,
        )

        assert jelentes.failed == ()
        ini = load_or_empty(cel / PICASA_INI_NAME)
        szekcio = ini.section(jelentes.exported[0].name)
        assert szekcio is not None, "a célmappában nem készült .picasa.ini szekció"
        assert szekcio.get("caption") == "Nyaralás"
        assert szekcio.get("keywords") == "tenger,nyár"

    def test_felirat_es_cimke_nelkul_nem_keszul_ini(self, tmp_path):
        """Megőrző: üres adatnál ne szemeteljünk a célmappában."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"

        export_photos([ExportItem(source=forras)], cel)

        assert not (cel / PICASA_INI_NAME).exists()

    def test_a_sorszamozott_nev_szekcioja_a_CELNEVET_kapja(self, tmp_path):
        """A `%0*d-%s` sorszám a célfájl nevében van — a szekció fejlécének
        is annak kell lennie, különben az adat nem talál gazdát."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=forras, caption="X")],
            cel,
            ExportSettings(add_numbers=True),
        )

        nev = jelentes.exported[0].name
        assert nev.startswith("001-"), nev
        assert load_or_empty(cel / PICASA_INI_NAME).section(nev) is not None


class TestCelmappaUtkozes:
    def test_uritessel_az_elozo_album_eltunik(self, tmp_path):
        """`purge_existing=True`: az eredeti „igen, felülírom" ága — az
        ELŐZŐ album tartalma törlődik, nem mellé kerül az új."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"
        cel.mkdir()
        regi = cel / "regi.jpg"
        regi.write_bytes(b"regi")

        export_photos([ExportItem(source=forras)], cel, purge_existing=True)

        assert not regi.exists(), "az előző album tartalma ottmaradt"
        assert (cel / "a.jpg").exists()

    def test_urites_nelkul_a_regi_marad(self, tmp_path):
        """Megőrző: alapértelmezésben (nem kérdeztünk) nem törlünk."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"
        cel.mkdir()
        regi = cel / "regi.jpg"
        regi.write_bytes(b"regi")

        export_photos([ExportItem(source=forras)], cel)

        assert regi.exists()

    def test_az_urites_csak_a_celmappat_erinti(self, tmp_path):
        """Az ürítés SOSEM léphet ki a célmappából — se a szülőbe, se
        egy másik ágba."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        szomszed = tmp_path / "szomszed.jpg"
        szomszed.write_bytes(b"nem-en")
        cel = tmp_path / "ki"
        cel.mkdir()
        (cel / "alkonyvtar").mkdir()
        (cel / "alkonyvtar" / "b.jpg").write_bytes(b"regi")

        export_photos([ExportItem(source=forras)], cel, purge_existing=True)

        assert szomszed.exists(), "az ürítés kilépett a célmappából"
        assert not (cel / "alkonyvtar").exists()

    def test_nem_letezo_celmappanal_az_urites_artalmatlan(self, tmp_path):
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"

        jelentes = export_photos([ExportItem(source=forras)], cel, purge_existing=True)

        assert jelentes.failed == ()
        assert (cel / "a.jpg").exists()

    def test_fajlra_mutato_cel_hibat_ad_nem_torol(self, tmp_path):
        """Ha a cél egy FÁJL, ne töröljük — az `IDS_DESTDIRCANNOCREATE`
        hibaága való ide."""
        forras = _kep(tmp_path / "src" / "a.jpg")
        cel = tmp_path / "ki"
        cel.write_bytes(b"ez egy fajl")

        jelentes = export_photos([ExportItem(source=forras)], cel, purge_existing=True)

        assert jelentes.exported == ()
        assert jelentes.failed
        assert cel.read_bytes() == b"ez egy fajl"


@pytest.mark.parametrize("darab,szelesseg", [(1, 3), (999, 3), (1000, 4)])
def test_a_sorszam_szelessege(tmp_path, darab, szelesseg):
    """Megőrző (#369): a `%0*d-%s` szélessége a kötegmérethez igazodik."""
    forras = _kep(tmp_path / "src" / "a.jpg")
    jelentes = export_photos(
        [ExportItem(source=forras)] * 1,
        tmp_path / f"ki{darab}",
        ExportSettings(add_numbers=True),
    )
    assert jelentes.exported[0].name.startswith("0" * (szelesseg - 1) + "1-") or darab > 1


class TestFilmMod:
    """`export.fen` `radiogroup name="movies"`: „Első képkocka" /
    „Teljes film (nincs átméretezés)". Az alapértelmezés a tárolt
    `FileExportMovie`-ból jön (#1166)."""

    @staticmethod
    def _video(utvonal: Path) -> Path:
        import cv2
        import numpy as np

        utvonal.parent.mkdir(parents=True, exist_ok=True)
        iro = cv2.VideoWriter(
            str(utvonal), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (32, 24)
        )
        for ertek in (40, 120, 200):
            iro.write(np.full((24, 32, 3), ertek, dtype=np.uint8))
        iro.release()
        return utvonal

    def test_teljes_film_eseten_a_felvetel_masolodik(self, tmp_path):
        video = self._video(tmp_path / "src" / "v.mp4")
        if not video.exists() or video.stat().st_size == 0:
            pytest.skip("a gépen nincs mp4-kódoló — a mérés nem érvényes")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=video)], cel, ExportSettings(movie_full=True)
        )

        assert jelentes.exported[0].suffix == ".mp4"
        assert jelentes.exported[0].read_bytes() == video.read_bytes()

    def test_elso_kepkocka_eseten_JPEG_keszul(self, tmp_path):
        video = self._video(tmp_path / "src" / "v.mp4")
        if not video.exists() or video.stat().st_size == 0:
            pytest.skip("a gépen nincs mp4-kódoló — a mérés nem érvényes")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=video)], cel, ExportSettings(movie_full=False)
        )

        assert jelentes.failed == ()
        assert jelentes.exported[0].suffix == ".jpg"
        assert jelentes.exported[0].stat().st_size > 0

    def test_olvashatatlan_felvetelnel_a_teljes_filmre_esik_vissza(self, tmp_path):
        """Nem veszíthetjük el a felvételt: az eredeti is fájlt ad."""
        alvideo = tmp_path / "src" / "rossz.mp4"
        alvideo.parent.mkdir(parents=True, exist_ok=True)
        alvideo.write_bytes(b"ez nem video")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=alvideo)], cel, ExportSettings(movie_full=False)
        )

        assert jelentes.failed == ()
        assert jelentes.exported[0].suffix == ".mp4"
