"""A #190-es effekt-referencia-generátor (`tools/golden/make_golden_kit_effects.py`)
füstpróbája.

A valódi golden-kitek (`research/golden-kit*/`) a fejlesztői gépen élnek, a
repóban nincsenek — itt csak a szkript LOGIKÁJÁT ellenőrizzük szintetikus
bemenettel: minden effekthez létrejön-e a beszédes nevű referencia-kép, a
csúszkás effektek 2-3 változatot kapnak-e, és az UTMUTATO.md hiánytalanul
felsorolja-e mindet.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "golden"
    / "make_golden_kit_effects.py"
)


def _load_module():
    """A tools/golden/make_golden_kit_effects.py betöltése fájlútvonalról
    (nincs a pythonpath-on — szándékosan eszköz, nem csomag)."""
    spec = importlib.util.spec_from_file_location(
        "make_golden_kit_effects", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("make_golden_kit_effects", module)
    spec.loader.exec_module(module)
    return module


mgke = _load_module()


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


def test_slugify_ekezet_nelkuli_fajlnev_biztos_szeletke() -> None:
    assert mgke.slugify("Lomo-szerű") == "lomoszeru"
    assert mgke.slugify("HDR-szerű") == "hdrszeru"
    assert mgke.slugify("60-as évek") == "60as_evek"
    assert mgke.slugify("Múzeumi matt") == "muzeumi_matt"


def test_effect_listak_a_jegyben_felsorolt_effekteket_tartalmazzak() -> None:
    nevek4 = [e.nev for e in mgke.EFFECTS_4]
    nevek5 = [e.nev for e in mgke.EFFECTS_5]
    assert nevek4 == [
        "Infravörös film", "Lomo-szerű", "Holga-szerű", "HDR-szerű",
        "Kinemaszkóp", "Orton-szerű", "60-as évek", "Színinvertálás",
        "Hőtérkép", "Áttűnés", "Poszterizálás", "Kéttónusú",
    ]
    assert nevek5 == [
        "Felpörgetés", "Lágyítás", "Képpontnagyítás", "Fókusznagyítás",
        "Ceruzarajz", "Neon", "Képregény", "Szegély", "Árnyékvetés",
        "Múzeumi matt", "Polaroid",
    ]


def test_csuszkas_effektek_2_vagy_3_beallitast_kapnak() -> None:
    for eff in [*mgke.EFFECTS_4, *mgke.EFFECTS_5]:
        assert 1 <= len(eff.beallitasok) <= 3
        assert len(set(eff.beallitasok)) == len(eff.beallitasok)


def test_kit_generalas_letrehozza_a_vart_mappaszerkezetet(
    tmp_path: Path, fotok_dir: Path
) -> None:
    out = tmp_path / "golden-kit-effects"
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(fotok_dir), str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert (out / "UTMUTATO.md").exists()
    assert (out / "export").is_dir()
    assert (out / "00-base" / "chart_ramp.jpg").exists()
    assert (out / "00-base" / "photo00.jpg").exists()

    vart4 = sum(len(e.beallitasok) for e in mgke.EFFECTS_4)
    vart5 = sum(len(e.beallitasok) for e in mgke.EFFECTS_5)
    kepek4 = sorted((out / "effekt4").glob("*.jpg"))
    kepek5 = sorted((out / "effekt5").glob("*.jpg"))
    assert len(kepek4) == vart4
    assert len(kepek5) == vart5

    # minden fájl valódi, beolvasható kép
    for p in [*kepek4, *kepek5]:
        assert cv2.imread(str(p)) is not None

    # az UTMUTATO.md minden fájlnevet felsorol
    utmutato = (out / "UTMUTATO.md").read_text(encoding="utf-8")
    for p in [*kepek4, *kepek5]:
        assert p.name in utmutato


def test_imwrite_imread_unicode_ekezetes_utvonalon(tmp_path: Path) -> None:
    """#190: a cv2.imwrite/imread Windowson nem kezeli a nem-ASCII
    útvonalat (pl. „Képek") — a helperek memóriában kódolnak/dekódolnak,
    így az útvonalat mindig a Unicode-biztos Python-IO kezeli."""
    mgk = mgke._mgk
    d = tmp_path / "Képek árvíztűrő tükörfúrógép"
    d.mkdir()
    p = d / "próba_kép.jpg"
    img = np.full((20, 30, 3), 128, np.uint8)
    mgk.imwrite_unicode(p, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    assert p.exists() and p.stat().st_size > 0
    vissza = mgk.imread_unicode(p)
    assert vissza is not None and vissza.shape == (20, 30, 3)
    # olvashatatlan/hiányzó fájlnál None, mint a cv2.imread
    assert mgk.imread_unicode(d / "nincs.jpg") is None


def test_kit_generalas_ekezetes_kimeneti_mappaba(tmp_path: Path) -> None:
    """#190: a teljes kit-generálás ékezetes kimeneti útvonallal is
    hiánytalan — a felhasználó valódi esete („…\\Képek\\Picasa\\…")."""
    out = tmp_path / "Képek" / "PicasaPy-golden-kit"
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert (out / "UTMUTATO.md").exists()
    for chart in ("chart_ramp.jpg", "chart_color.jpg", "chart_detail.jpg",
                  "photo00.jpg"):
        p = out / "00-base" / chart
        assert p.exists() and p.stat().st_size > 0, f"hiányzó alapkép: {chart}"
        assert mgke._mgk.imread_unicode(p) is not None
    kepek = [*(out / "effekt4").glob("*.jpg"), *(out / "effekt5").glob("*.jpg")]
    assert len(kepek) == 49
    for p in kepek:
        assert p.stat().st_size > 0


def test_kit_generalas_zarolt_kimenetnel_felulirassal_folytat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#190: ha a meglévő kimeneti mappa nem törölhető (OneDrive/víruskereső
    zárolás → PermissionError, a felhasználó Windows-os esete), a generálás
    NEM áll le — a meglévő mappába, felülírással készül el a kit."""
    out = tmp_path / "golden-kit-zarolt"
    out.mkdir()
    (out / "00-base").mkdir()
    (out / "regi.txt").write_text("onedrive-maradvany")

    def _zarolt_rmtree(*_args, **_kwargs):
        raise PermissionError(5, "A hozzáférés megtagadva")

    monkeypatch.setattr(mgke.shutil, "rmtree", _zarolt_rmtree)
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert (out / "UTMUTATO.md").exists()
    assert (out / "00-base" / "photo00.jpg").exists()
    assert sorted((out / "effekt4").glob("*.jpg")), "a képek felülírással is elkészülnek"
    # a nem-törölhető régi tartalom megmarad — ez elfogadott, nem hiba
    assert (out / "regi.txt").exists()


def test_kit_generalas_fotomappa_nelkul_is_mukodik(tmp_path: Path) -> None:
    """#190: fotókönyvtár HIÁNYÁBAN (csak kimeneti mappa argumentum) a kit
    szintetikus fotóval elkészül — nem száll el, mint a korábbi verzió."""
    out = tmp_path / "golden-kit-nofoto"
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    photo = out / "00-base" / "photo00.jpg"
    assert photo.exists(), "szintetikus fotó-alapképnek létre kell jönnie"
    assert cv2.imread(str(photo)) is not None, "a fotó-alapkép valós kép"
    # a photo-alapú effektek képei is legyártódtak (pl. Szegély, Polaroid)
    kepek5 = sorted((out / "effekt5").glob("*.jpg"))
    assert kepek5, "a photo-alapú effektek képeinek is létre kell jönnie"
    assert (out / "UTMUTATO.md").exists()


def test_kit_generalas_ures_fotomappaval_szintetikus_fotot_general(
    tmp_path: Path,
) -> None:
    """#190: ha a megadott fotómappa létezik, de ÜRES (pontosan a
    felhasználó esete), a pick_photos IndexError-ját elnyeljük, és
    szintetikus fotóra esünk vissza — a generálás nem bukik el."""
    ures = tmp_path / "ures-fotok"
    ures.mkdir()
    out = tmp_path / "golden-kit-ures"
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(ures), str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert (out / "00-base" / "photo00.jpg").exists()
    assert (out / "UTMUTATO.md").exists()


def test_kit_generalas_letezo_kimeneti_mappat_felulir(
    tmp_path: Path, fotok_dir: Path
) -> None:
    out = tmp_path / "golden-kit-effects"
    out.mkdir()
    (out / "regi-maradvany.txt").write_text("torlendo")

    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(fotok_dir), str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert not (out / "regi-maradvany.txt").exists()
    assert (out / "UTMUTATO.md").exists()
