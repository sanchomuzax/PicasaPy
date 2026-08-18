"""A kollázs KIMENETI törvénye — #949, spec 9.1.

A `docs/specs/kollazs-panel-ui-spec.md` 9.1-es táblája hét sorban mondja
meg, mit tesz az eredeti mentés, és mit kell pótolnunk. Ez a fájl mind a
hetet állítja, Qt nélkül: a `collage_output` tiszta réteg, tehát
eseményhurok nélkül mérhető.

⚠️ **Ez a fájl felülír három korábbi állítást.** A #943-as
`test_collage_layout_943.py` az időbélyeges `kollázs-<stamp>.jpg` nevet
és a `~/Pictures/Kollázsok` mappát rögzítette. A spec 9.1 táblája
ugyanezt a két sort **teendőként** sorolja fel („a `Picasa` közbülső szint
pótlása", „cím-alapú név + `%s%lu` számozás") — a régi teszt tehát a mi
korábbi tévedésünket őrizte, nem az eredeti viselkedést. A #943-as fájl
érintett esetei ezért átíródtak, nem törlődtek.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from picasapy.app import collage_output as output
from picasapy.collage.cxf import loads
from picasapy.collage.nodes import CollageNode
from picasapy.collage.themes import MULTIEXP, NOBORDER, PICTUREPILE

from support.jpeg_factory import make_jpeg


def _settings(width: int = 512, page_ratio: float = 0.75):
    return output.render_settings(
        theme=PICTUREPILE,
        border=NOBORDER,
        spacing=0.0,
        shadows=False,
        page_ratio=page_ratio,
        background_rgb=(10, 20, 30),
        frame_center=-1,
        seed=1,
        width=width,
    )


def _nodes(paths):
    """Két-három csomópont a lap közepe táján, lapegységben."""
    return tuple(
        CollageNode(
            path=str(path),
            center_x=200.0 + 200.0 * index,
            center_y=300.0,
            width=180.0,
            height=140.0,
            border=NOBORDER,
        )
        for index, path in enumerate(paths)
    )


@pytest.fixture
def kepek(tmp_path):
    mappa = tmp_path / "Nyaralás 2026"
    mappa.mkdir()
    utak = [mappa / "a.jpg", mappa / "b.jpg"]
    for ut in utak:
        make_jpeg(ut, size=(80, 60))
    return utak


class TestCelmappa:
    """„hova": `<Képek>/Picasa/Kollázsok` — a `Picasa` közbülső szinttel."""

    def test_az_alapertelmezett_mappa_a_picasa_szintet_is_tartalmazza(self):
        cel = output.output_dir(None)
        assert cel.parts[-3:] == ("Pictures", "Picasa", "Kollázsok")
        assert cel == Path.home() / output.DEFAULT_OUTPUT_DIR

    def test_a_beallitott_mappa_erosebb(self, tmp_path):
        assert output.output_dir(str(tmp_path)) == tmp_path


class TestFajlnev:
    """„milyen néven" + „ütközéskor" — cím-alapú név, `%s%lu` számozás."""

    def test_a_cim_adja_a_nevet(self, tmp_path):
        cel = output.output_path(tmp_path, "Nyaralás 2026")
        assert cel.name == "Nyaralás 2026.jpg"

    def test_ures_cimnel_a_tartalek_a_kollazs(self, tmp_path):
        assert output.output_path(tmp_path, "").name == "kollázs.jpg"
        assert output.output_path(tmp_path, "   ").name == "kollázs.jpg"

    def test_utkozeskor_szokoz_NELKULI_szamozas(self, tmp_path):
        (tmp_path / "Nyár.jpg").write_bytes(b"")
        assert output.output_path(tmp_path, "Nyár").name == "Nyár1.jpg"
        (tmp_path / "Nyár1.jpg").write_bytes(b"")
        assert output.output_path(tmp_path, "Nyár").name == "Nyár2.jpg"

    def test_a_par_masik_fele_is_utkozesnek_szamit(self, tmp_path):
        """Csak a `.cxf` van meg: a `.jpg` neve akkor SEM foglalható el.

        A kettőnek együtt kell mozognia — ha a `.jpg` szabad, de a `.cxf`
        nem, a mentés némán elhasítaná egy korábbi kollázs párját."""
        (tmp_path / "Tél.cxf").write_bytes(b"")
        assert output.output_path(tmp_path, "Tél").name == "Tél1.jpg"

    def test_az_utvonal_elvalasztoi_nem_szokhetnek_ki(self, tmp_path):
        cel = output.output_path(tmp_path, "../../etc/passwd")
        assert cel.parent == Path(tmp_path)
        assert "/" not in cel.name and "\\" not in cel.name


class TestFelsoMeret:
    """„felső méret": 5120 a HOSSZABBIK oldalon, tájolástól függetlenül."""

    def test_fekvo_lapon_a_szelesseg_a_korlat(self):
        beallitas = output.render_settings(
            theme=PICTUREPILE,
            border=NOBORDER,
            spacing=0.0,
            shadows=False,
            page_ratio=0.75,
            background_rgb=(0, 0, 0),
            frame_center=-1,
            seed=1,
        )
        assert beallitas.width == output.MAX_OUTPUT_EDGE
        assert max(beallitas.width, beallitas.height) == output.MAX_OUTPUT_EDGE

    def test_allo_lapon_a_MAGASSAG_a_korlat(self):
        beallitas = output.render_settings(
            theme=PICTUREPILE,
            border=NOBORDER,
            spacing=0.0,
            shadows=False,
            page_ratio=1.5,
            background_rgb=(0, 0, 0),
            frame_center=-1,
            seed=1,
        )
        assert max(beallitas.width, beallitas.height) == output.MAX_OUTPUT_EDGE
        assert beallitas.height == output.MAX_OUTPUT_EDGE

    def test_a_kifejezett_szelesseg_erosebb(self):
        assert _settings(width=1000, page_ratio=0.5).width == 1000
        assert _settings(width=1000, page_ratio=0.5).height == 500


class TestAtomiIras:
    """„hogyan": tmp-fájl, majd átnevezés — ELŐBB a `.cxf`, aztán a `.jpg`."""

    def test_a_par_mindket_tagja_megszuletik(self, tmp_path, kepek):
        cel = tmp_path / "kesz" / "Nyaralás.jpg"
        eredmeny = output.render_collage(_nodes(kepek), _settings(), cel)
        assert eredmeny.path == cel
        assert cel.exists()
        assert cel.with_suffix(".cxf").exists()
        assert eredmeny.used == 2

    def test_a_cxf_a_vaszon_csomopontjait_orzi(self, tmp_path, kepek):
        cel = tmp_path / "Nyaralás.jpg"
        output.render_collage(_nodes(kepek), _settings(), cel)
        projekt = loads(cel.with_suffix(".cxf").read_bytes())
        assert len(projekt.nodes) == 2
        assert [Path(csomo.src).name for csomo in projekt.nodes] == ["a.jpg", "b.jpg"]

    def test_nem_marad_tmp_fajl(self, tmp_path, kepek):
        cel = tmp_path / "Nyaralás.jpg"
        output.render_collage(_nodes(kepek), _settings(), cel)
        assert list(tmp_path.glob("*.tmp")) == []

    def test_a_JPEG_minoseg_90(self, tmp_path, kepek, monkeypatch):
        latott = {}

        eredeti = output.write_collage

        def _figyelo(target, image, quality=92):
            latott["quality"] = quality
            return eredeti(target, image, quality)

        monkeypatch.setattr(output, "write_collage", _figyelo)
        output.render_collage(_nodes(kepek), _settings(), tmp_path / "x.jpg")
        assert latott["quality"] == output.JPEG_QUALITY

    def test_a_bukott_iras_nem_hagy_csonkot(self, tmp_path, kepek, monkeypatch):
        """A JPEG kódolása elszáll: a `.cxf` sem maradhat félkész.

        Az atomi írás lényege, hogy a felhasználó vagy a TELJES párt látja,
        vagy semmit — egy magányos `.cxf` a könyvtárban hazudna."""

        def _robban(target, image, quality=92):
            raise ValueError("teszt: a kódolás elszállt")

        monkeypatch.setattr(output, "write_collage", _robban)
        cel = tmp_path / "Nyaralás.jpg"
        with pytest.raises(ValueError):
            output.render_collage(_nodes(kepek), _settings(), cel)
        assert not cel.exists()
        assert list(tmp_path.glob("*.tmp")) == []


class TestHianyzoKepek:
    """9.4: a hiányzó kép nem tünteti el a kollázst, de jelentve lesz."""

    def test_a_hianyzo_kep_jelentve_van(self, tmp_path, kepek):
        csomok = (*_nodes(kepek), *_nodes([tmp_path / "nincs.jpg"]))
        eredmeny = output.render_collage(csomok, _settings(), tmp_path / "x.jpg")
        assert eredmeny.used == 2
        assert [Path(p).name for p in eredmeny.missing] == ["nincs.jpg"]

    def test_ha_EGYETLEN_kep_sincs_nincs_fajl(self, tmp_path):
        csomok = _nodes([tmp_path / "nincs.jpg"])
        eredmeny = output.render_collage(csomok, _settings(), tmp_path / "x.jpg")
        assert eredmeny.path is None
        assert not (tmp_path / "x.jpg").exists()
        assert not (tmp_path / "x.cxf").exists()


class TestTobbszorosExponalas:
    """A Többszörös exponálásnak nincs csomópont-geometriája — külön út."""

    def test_a_multiexp_a_kepeket_egymasra_teszi(self, tmp_path, kepek):
        beallitas = output.render_settings(
            theme=MULTIEXP,
            border=NOBORDER,
            spacing=0.0,
            shadows=False,
            page_ratio=0.75,
            background_rgb=(0, 0, 0),
            frame_center=-1,
            seed=1,
            width=256,
        )
        eredmeny = output.render_collage(_nodes(kepek), beallitas, tmp_path / "m.jpg")
        assert eredmeny.path == tmp_path / "m.jpg"
        assert eredmeny.used == 2
        assert isinstance(eredmeny.image_shape, tuple)


class TestKepAdat:
    def test_a_kirajzolt_kep_merete_a_beallitasbol_jon(self, tmp_path, kepek):
        beallitas = _settings(width=320, page_ratio=0.5)
        eredmeny = output.render_collage(
            _nodes(kepek), beallitas, tmp_path / "k.jpg"
        )
        assert eredmeny.image_shape[:2] == (160, 320)

    def test_a_hatterszin_RGB_bol_BGR_be_fordul(self, tmp_path, kepek):
        beallitas = _settings(width=64, page_ratio=1.0)
        eredmeny = output.render_collage(
            _nodes(kepek), beallitas, tmp_path / "h.jpg"
        )
        assert eredmeny.path is not None
        # a `render_settings` a (10, 20, 30) RGB-t (30, 20, 10) BGR-re fordítja
        assert tuple(np.asarray(beallitas.background)) == (30, 20, 10)
