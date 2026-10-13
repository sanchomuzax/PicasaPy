"""A PR-tesztek statikus választásának és darabolásának próbái (#4922)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import teszt_valasztas as tv  # noqa: E402


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "src/picasapy").mkdir(parents=True)
    (tmp_path / "tests/app/qml_functional").mkdir(parents=True)
    (tmp_path / "tests/support").mkdir(parents=True)
    for ut in (*tv.SMOKE_TESTS, *tv.HELP_TESTS, *tv.I18N_TESTS):
        cel = tmp_path / ut
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_text("def test_fust():\n    assert True\n", encoding="utf-8")
    (tmp_path / "tests/test_fogyaszto.py").write_text(
        "from picasapy.reteg import fut\n", encoding="utf-8"
    )
    (tmp_path / "tests/test_kozvetlen.py").write_text(
        "from picasapy import forras\n", encoding="utf-8"
    )
    (tmp_path / "tests/app/qml_functional/test_nev.py").write_text(
        "def test_nev():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "tests/app/test_nem_qml.py").write_text(
        "def test_nem_qml():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "src/picasapy/reteg.py").write_text(
        "def fut():\n    from picasapy import forras\n    return forras.x\n",
        encoding="utf-8",
    )
    (tmp_path / "src/picasapy/forras.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def test_fuggvenyen_beluli_lusta_importon_at_is_eljut_a_tesztig(repo: Path) -> None:
    dontes = tv.select_tests(repo, ["src/picasapy/forras.py"])

    assert not dontes.teljes
    assert "tests/test_fogyaszto.py" in dontes.fajlok
    assert "tests/test_kozvetlen.py" in dontes.fajlok
    assert set(tv.SMOKE_TESTS) <= set(dontes.fajlok)


def test_importlib_aliason_at_eler_a_csomag_lusta_api_mogotti_modulhoz(
    repo: Path,
) -> None:
    (repo / "src/picasapy/facade").mkdir()
    (repo / "src/picasapy/facade/__init__.py").write_text(
        "from importlib import import_module\n"
        "_NAME_TO_MODULE = {'value': 'impl'}\n"
        "def __getattr__(name):\n"
        "    return getattr(import_module(f'.{_NAME_TO_MODULE[name]}', __name__), name)\n",
        encoding="utf-8",
    )
    (repo / "src/picasapy/facade/impl.py").write_text("value = 1\n", encoding="utf-8")
    fogyaszto = repo / "tests/test_lusta_api.py"
    fogyaszto.write_text("from picasapy.facade import value\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["src/picasapy/facade/impl.py"])

    assert not dontes.teljes
    assert "tests/test_lusta_api.py" in dontes.fajlok


def test_valodi_qml_nevekhez_tartozo_regresszios_orok_kivalasztodnak() -> None:
    dontes = tv.select_tests(
        _ROOT,
        [
            "src/picasapy/app/qml/PicasaPy/FolderPane.qml",
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "src/picasapy/app/folder_cover_provider.py",
        ],
    )

    assert "tests/app/qml_functional/test_mappa_borito_lathato_ikon_4876.py" in dontes.fajlok
    assert "tests/app/qml_functional/test_nezet_indexkep_pipa_4623.py" in dontes.fajlok


def test_qml_valtozasnal_a_teljes_qml_funkcionalis_keszlet_fut(repo: Path) -> None:
    dontes = tv.select_tests(
        repo, ["src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"]
    )

    assert "tests/app/qml_functional/test_nev.py" in dontes.fajlok
    assert "tests/app/test_nem_qml.py" not in dontes.fajlok
    assert dontes.teljes is False


@pytest.mark.parametrize(
    "ut",
    [
        "tests/conftest.py",
        "tests/app/conftest.py",
        "tests/app/qml_functional/conftest.py",
        "tests/support/segitseg.py",
        "scripts/run_tests.py",
        ".github/workflows/ci.yml",
        ".github/workflows/teszt-darabok.yml",
        "packaging/qt-runtime-deps.txt",
    ],
)
def test_kozos_beallitasok_valtozasanal_teljes_keszletet_valaszt(repo, ut: str) -> None:
    dontes = tv.select_tests(repo, [ut])

    assert dontes.teljes, ut
    assert set(dontes.fajlok) == set(tv.discover_tests(repo))


def test_pyproject_csak_verziosora_es_a_changelogokra_fustkeszletet_valaszt(
    repo: Path,
) -> None:
    dontes = tv.select_tests(
        repo,
        ["pyproject.toml", "CHANGELOG.md", "changelog.d/4922.md"],
        pyproject_version_only=True,
    )

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_pyproject_egyeb_valtozasa_teljes_keszlet(repo: Path) -> None:
    assert tv.select_tests(
        repo, ["pyproject.toml"], pyproject_version_only=False
    ).teljes


def test_verziosor_valtozasa_tartalom_alapjan_ismerheto_fel() -> None:
    regi = '[project]\nname = "picasapy"\nversion = "0.9.1"\n'
    uj = '[project]\nname = "picasapy"\nversion = "0.9.2"\n'
    masik = uj + "\n[tool.ruff]\nline-length = 100\n"

    assert tv.pyproject_only_version_changed(regi, uj)
    assert not tv.pyproject_only_version_changed(regi, masik)
    assert not tv.pyproject_only_version_changed(uj, uj)


def test_ismeretlen_hatas_vagy_ures_diff_teljes_keszlet(repo: Path) -> None:
    assert tv.select_tests(repo, None).teljes
    assert tv.select_tests(repo, []).teljes
    assert tv.select_tests(repo, ["src/picasapy/unknown/data.bin"]).teljes


def test_sugo_tartalom_valtozasnal_a_minden_lapot_olvaso_tesztek_futnak(
    repo: Path,
) -> None:
    dontes = tv.select_tests(repo, ["src/picasapy/help/features/konyvtar.md"])

    assert not dontes.teljes
    assert set(tv.HELP_TESTS) <= set(dontes.fajlok)


def test_forditasi_katalogus_valtozasnal_az_i18n_orok_futnak(repo: Path) -> None:
    dontes = tv.select_tests(
        repo, ["src/picasapy/app/i18n/picasapy_hu.ts"]
    )

    assert not dontes.teljes
    assert set(tv.I18N_TESTS) <= set(dontes.fajlok)


def test_uj_tesztfajl_es_fustkeszlet_is_bekerul(repo: Path) -> None:
    uj = "tests/test_uj.py"
    (repo / uj).write_text("def test_uj():\n    assert True\n", encoding="utf-8")

    dontes = tv.select_tests(repo, [uj])

    assert uj in dontes.fajlok
    assert set(tv.SMOKE_TESTS) <= set(dontes.fajlok)


def test_mert_idokkel_harom_perces_celt_es_tizenhatos_plafont_hasznal(
    tmp_path: Path,
) -> None:
    fajlok = [f"tests/test_{i}.py" for i in range(40)]
    idok = {ut: 30.0 for ut in fajlok}

    terv = tv.tervezz_darabokat(fajlok, idok, teljes=False)

    assert terv.darabszam == 7
    assert terv.mert_masodperc == 1200.0
    assert terv.ismeretlen_fajlok == ()
    osszes = set().union(
        *(tv.darab_fajljai(fajlok, idok, i, terv.darabszam) for i in range(1, 8))
    )
    assert osszes == set(fajlok)


def test_meres_nelkul_fajlszambol_darabol_es_kimondja_a_hianyzo_adatot() -> None:
    fajlok = [f"tests/test_{i}.py" for i in range(75)]

    terv = tv.tervezz_darabokat(fajlok, {}, teljes=False)

    assert terv.darabszam == 3
    assert terv.mert_masodperc == 0
    assert len(terv.ismeretlen_fajlok) == 75


def test_reszben_mert_keszletnel_a_hianyzo_fajlok_a_meresi_p90_becslest_kapjak() -> None:
    ismert = "tests/test_mert.py"
    ismeretlenek = [f"tests/test_uj_{i}.py" for i in range(30)]
    idok = {ismert: 60.0, **{f"tests/test_regi_{i}.py": 60.0 for i in range(10)}}

    terv = tv.tervezz_darabokat([ismert, *ismeretlenek], idok, teljes=False)

    assert terv.darabszam == 11
    assert terv.mert_masodperc == 60.0
    assert set(terv.ismeretlen_fajlok) == set(ismeretlenek)


def test_teljes_keszlet_merese_a_nem_app_osszesitett_idot_is_beszamitja(
    tmp_path: Path,
) -> None:
    fajlok = ["tests/test_a.py", "tests/app/test_b.py"]
    idok = {tv.NON_APP_UNIT: 488.53, "tests/app/test_b.py": 7206.0}

    terv = tv.tervezz_darabokat(fajlok, idok, teljes=True)

    assert terv.darabszam == 16
    assert terv.mert_masodperc == pytest.approx(7694.53)
    assert terv.ismeretlen_fajlok == ("tests/test_a.py",)


def test_teljes_keszletben_a_nem_app_fajlok_kulon_darabokba_kerulnek() -> None:
    fajlok = ["tests/test_a.py", "tests/test_b.py", "tests/app/test_c.py"]
    idok = {
        tv.NON_APP_UNIT: 120.0,
        "tests/app/test_c.py": 30.0,
    }

    darabok = [
        tv.darab_fajljai(fajlok, idok, sorszam, 2, teljes=True)
        for sorszam in (1, 2)
    ]

    assert set().union(*map(set, darabok)) == set(fajlok)
    assert set(darabok[0]).isdisjoint(darabok[1])
    assert sum("tests/test_a.py" in darab for darab in darabok) == 1
    assert sum("tests/test_b.py" in darab for darab in darabok) == 1
    assert ("tests/test_a.py" in darabok[0]) != ("tests/test_b.py" in darabok[0])


def test_a_valodi_main_meres_tizenhat_darabot_ad() -> None:
    fajlok = tv.discover_tests(_ROOT)
    idok = json.loads((_ROOT / "scripts/teszt_idok.json").read_text(encoding="utf-8"))

    terv = tv.tervezz_darabokat(fajlok, idok, teljes=True)
    nem_app_meresek = sum(
        idok[ut]
        for ut in fajlok
        if not ut.startswith("tests/app/") and ut in idok
    )
    mert_osszeg = sum(idok[ut] for ut in fajlok if ut in idok) + max(
        0.0, idok[tv.NON_APP_UNIT] - nem_app_meresek
    )

    assert terv.darabszam == 16
    assert terv.mert_masodperc == pytest.approx(mert_osszeg)


def test_a_ci_a_valasztot_listat_futtatja_a_kotelezo_nev_megtartasaval() -> None:
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    chunks = (_ROOT / ".github/workflows/teszt-darabok.yml").read_text(
        encoding="utf-8"
    )

    assert "scripts/teszt_valasztas.py --darabszam" in ci
    assert "Test (ubuntu-latest)" in ci
    assert "scripts/teszt_valasztas.py --lista" in chunks
    assert "--fajllista" in chunks
    assert "inputs.darabszam" in chunks
