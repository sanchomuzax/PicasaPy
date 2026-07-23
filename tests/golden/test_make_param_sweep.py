"""A #190 2. köri paraméter-sweep generátor
(`tools/golden/make_param_sweep.py`) füstpróbája.

A valódi golden-kitek (`research/golden-kit*/`) a fejlesztői gépen élnek —
itt szintetikus alapképpel csak a szkript LOGIKÁJÁT ellenőrizzük: (a) a
várt mappák/`.picasa.ini`-k létrejönnek-e, (b) a `filters=` kulcsok és
sweep-értékek helyesek-e, (c) a generált `filters=` sorok a projekt
ini-parszerével round-trip-biztosak-e, (d) az `UTMUTATO.md` létrejön-e.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.ini import load_document, parse_filters, serialize_filters

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "golden"
    / "make_param_sweep.py"
)


def _load_module():
    """A tools/golden/make_param_sweep.py betöltése fájlútvonalról (nincs a
    pythonpath-on — szándékosan eszköz, nem csomag)."""
    spec = importlib.util.spec_from_file_location(
        "make_param_sweep", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("make_param_sweep", module)
    spec.loader.exec_module(module)
    return module


mps = _load_module()


@pytest.fixture
def fotok_dir(tmp_path: Path) -> Path:
    """Néhány szintetikus "fénykép" a pick_photos-nak (fényerő-szórással)."""
    d = tmp_path / "fotok"
    d.mkdir()
    rng = np.random.default_rng(7)
    for i in range(6):
        img = rng.integers(30 + i * 30, 200 + i * 5, (40, 60, 3), dtype=np.uint8)
        cv2.imwrite(str(d / f"photo_{i:02d}.jpg"), img)
    return d


@pytest.fixture
def out_dir(tmp_path: Path, fotok_dir: Path) -> Path:
    out = tmp_path / "param-sweep"
    argv = sys.argv
    sys.argv = ["make_param_sweep.py", str(fotok_dir), str(out)]
    try:
        mps.main()
    finally:
        sys.argv = argv
    return out


def _folder_for(effect) -> str:
    return f"effekt{effect.tab}_{mps.slugify(effect.nev)}"


class TestEffektLista:
    def test_mind_a_23_effekt_szerepel(self) -> None:
        assert len(mps.EFFECTS) == 23
        assert len({e.key for e in mps.EFFECTS}) == 23

    def test_kulcsok_egyeznek_a_190es_1koros_valodi_mintakkal(self) -> None:
        varakozott = {
            "IR", "Lomo", "Holga", "HDR", "Cinemascope", "Orton", "Sixties",
            "Invert", "HeatMap", "CrossProcess", "QuantizePalette", "TwoTone",
            "Boost", "Soften", "Pixelate", "FocalZoom", "PencilSketch",
            "Neon", "Comicize", "Border", "DropShadow", "MuseumMatte",
            "Polaroid",
        }
        assert {e.key for e in mps.EFFECTS} == varakozott


class TestSablonokAValodiMintakkalIgazolva:
    """A #190 1. körben rögzített VALÓDI minták (tests/ini/test_filters.py
    `TestEffektFulKulcsok190`) pontosan visszaállnak, ha a sweepelt helyre a
    minta saját értékét helyettesítjük — ez igazolja, hogy a `template`
    mezők pozíciója/formátuma hibátlanul illeszkedik a valódi kulcsokhoz."""

    MINTA_ERTEKEK = {
        "IR": (0.0, "IR=1,0.000000;"),
        "Lomo": (50.0, "Lomo=1,50.000000,0.000000;"),
        "Holga": (70.0, "Holga=1,70.000000,30.000000,0.000000;"),
        "HDR": (20.0, "HDR=1,20.000000,3.000000,0.000000;"),
        "Cinemascope": (0.0, "Cinemascope=1,0;"),
        "Orton": (25.0, "Orton=1,25.000000,50.000000,0.000000;"),
        "Sixties": (20.0, "Sixties=1,20.000000,00ffffff,0;"),
        "Invert": (0.0, "Invert=1;"),
        "HeatMap": (0.0, "HeatMap=1,0.000000,0.000000;"),
        "CrossProcess": (0.0, "CrossProcess=1,0.000000;"),
        "QuantizePalette": (
            8.0, "QuantizePalette=1,8.000000,80.000000,0.000000;",
        ),
        "TwoTone": (
            0.0,
            "TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;",
        ),
        "Boost": (50.0, "Boost=1,50.000000;"),
        "Soften": (50.0, "Soften=1,50.000000,50.000000;"),
        "Pixelate": (20.0, "Pixelate=1,20.000000,9.000000,0.000000;"),
        "FocalZoom": (
            50.0,
            "FocalZoom=1,0.500000,0.500000,50.000000,50.000000,"
            "50.000000,0.000000;",
        ),
        "PencilSketch": (2.0, "PencilSketch=1,2.000000,100.000000,0.000000;"),
        "Neon": (0.0, "Neon=1,0.000000,00ff0000;"),
        "Comicize": (20.0, "Comicize=1,20.000000,50.000000,50.000000;"),
        "Border": (
            20.0,
            "Border=1,20.000000,5.000000,0.000000,00000000,"
            "00ffffff,0.000000;",
        ),
        "DropShadow": (
            4.0,
            "DropShadow=1,4.000000,90.000000,10.000000,00000000,"
            "00ffffff,30.000000;",
        ),
        "MuseumMatte": (
            25.0, "MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;",
        ),
        "Polaroid": (5.0, "Polaroid=1,5.000000,00e2e2e2;"),
    }

    def test_lefedi_mind_a_23_mintat(self) -> None:
        assert len(self.MINTA_ERTEKEK) == 23
        assert set(self.MINTA_ERTEKEK) == {e.key for e in mps.EFFECTS}

    @pytest.mark.parametrize("key", list(MINTA_ERTEKEK))
    def test_sablon_visszaallitja_a_valodi_mintat(self, key: str) -> None:
        value, expected = self.MINTA_ERTEKEK[key]
        effect = next(e for e in mps.EFFECTS if e.key == key)
        assert mps._filters_value(effect, value) == expected
        # a minta maga is bitre round-trip-biztos (a projekt parszerével)
        assert serialize_filters(parse_filters(expected)) == expected


class TestKitGeneralas:
    def test_letrehozza_a_vart_mappakat_es_inieket(self, out_dir: Path) -> None:
        assert (out_dir / "UTMUTATO.md").exists()
        assert (out_dir / "export").is_dir()
        for effect in mps.EFFECTS:
            folder = out_dir / _folder_for(effect)
            assert folder.is_dir(), f"hiányzó mappa: {folder}"
            assert (folder / ".picasa.ini").exists(), f"hiányzó ini: {folder}"

    def test_egyparameteres_invert_egyetlen_bejegyzest_kap(
        self, out_dir: Path
    ) -> None:
        invert = next(e for e in mps.EFFECTS if e.key == "Invert")
        folder = out_dir / _folder_for(invert)
        kepek = sorted(folder.glob("*.jpg"))
        assert len(kepek) == 1
        doc = load_document(folder / ".picasa.ini")
        section = doc.section(kepek[0].name)
        assert section is not None
        assert section.get("filters") == "Invert=1;"

    def test_cinemascope_negy_diszkret_egesz_erteket_kap(
        self, out_dir: Path
    ) -> None:
        cine = next(e for e in mps.EFFECTS if e.key == "Cinemascope")
        folder = out_dir / _folder_for(cine)
        kepek = sorted(folder.glob("*.jpg"))
        assert len(kepek) == 4
        doc = load_document(folder / ".picasa.ini")
        ertekek = set()
        for kep in kepek:
            section = doc.section(kep.name)
            assert section is not None
            filt = section.get("filters")
            assert filt.startswith("Cinemascope=1,")
            ertekek.add(filt)
        assert ertekek == {
            "Cinemascope=1,0;", "Cinemascope=1,1;",
            "Cinemascope=1,2;", "Cinemascope=1,3;",
        }

    def test_folytonos_sweep_5_pontot_general_min_max_hatarral(
        self, out_dir: Path
    ) -> None:
        boost = next(e for e in mps.EFFECTS if e.key == "Boost")
        folder = out_dir / _folder_for(boost)
        kepek = sorted(folder.glob("*.jpg"))
        assert len(kepek) == 5
        doc = load_document(folder / ".picasa.ini")
        ertekek = []
        for kep in kepek:
            section = doc.section(kep.name)
            filt = section.get("filters")
            op = parse_filters(filt)[0]
            ertekek.append(op.float_params()[0])
        assert sorted(ertekek) == pytest.approx([0.0, 25.0, 50.0, 75.0, 100.0])

    def test_twotone_negativ_tartomanyt_is_sweepel(self, out_dir: Path) -> None:
        """TwoTone feltételezett tartománya -100..100 (előjeles) — a
        legkisebb sweep-pont negatív kell legyen."""
        twotone = next(e for e in mps.EFFECTS if e.key == "TwoTone")
        folder = out_dir / _folder_for(twotone)
        doc = load_document(folder / ".picasa.ini")
        ertekek = []
        for kep in sorted(folder.glob("*.jpg")):
            section = doc.section(kep.name)
            op = parse_filters(section.get("filters"))[0]
            # a színparaméterek (hex) miatt csak az 1. numerikus paramétert
            # olvassuk, a float_params() a színt is konvertálni próbálná
            ertekek.append(float(op.params[1]))
        assert min(ertekek) == pytest.approx(-100.0)
        assert max(ertekek) == pytest.approx(100.0)

    def test_focalzoom_a_kozeppontot_fixen_tartja(self, out_dir: Path) -> None:
        """FocalZoom p1/p2 (0.5,0.5) fixen — csak a 3. paraméter (nagyítás)
        sweepelt, a fókuszpont minden variánsban a kép közepén marad."""
        fz = next(e for e in mps.EFFECTS if e.key == "FocalZoom")
        folder = out_dir / _folder_for(fz)
        doc = load_document(folder / ".picasa.ini")
        for kep in sorted(folder.glob("*.jpg")):
            section = doc.section(kep.name)
            op = parse_filters(section.get("filters"))[0]
            floats = op.float_params()
            assert floats[0] == pytest.approx(0.5)
            assert floats[1] == pytest.approx(0.5)

    def test_minden_generalt_filters_sor_roundtrip_biztos(
        self, out_dir: Path
    ) -> None:
        for effect in mps.EFFECTS:
            folder = out_dir / _folder_for(effect)
            doc = load_document(folder / ".picasa.ini")
            for section in doc.file_sections():
                value = section.get("filters")
                assert value is not None
                assert serialize_filters(parse_filters(value)) == value

    def test_kepek_valos_beolvashato_fajlok(self, out_dir: Path) -> None:
        for effect in mps.EFFECTS:
            folder = out_dir / _folder_for(effect)
            for kep in folder.glob("*.jpg"):
                assert cv2.imread(str(kep)) is not None

    def test_utmutato_minden_mappat_es_kulcsot_felsorol(
        self, out_dir: Path
    ) -> None:
        utmutato = (out_dir / "UTMUTATO.md").read_text(encoding="utf-8")
        for effect in mps.EFFECTS:
            assert _folder_for(effect) in utmutato
            assert f"`{effect.key}`" in utmutato

    def test_fotomappa_nelkul_is_lefut(self, tmp_path: Path) -> None:
        out = tmp_path / "param-sweep-nofoto"
        argv = sys.argv
        sys.argv = ["make_param_sweep.py", str(out)]
        try:
            mps.main()
        finally:
            sys.argv = argv
        assert (out / "UTMUTATO.md").exists()
        boost_folder = out / _folder_for(
            next(e for e in mps.EFFECTS if e.key == "Boost")
        )
        assert len(list(boost_folder.glob("*.jpg"))) == 5
