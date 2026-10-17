"""A PR-tesztek statikus választásának és darabolásának próbái (#4922)."""

from __future__ import annotations

import json
import subprocess
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
        'QML_FILE = "PhotoViewer.qml"\n'
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
        "conftest.py",
        "scripts/run_tests.py",
        "scripts/teszt_valasztas.py",
        "scripts/teszt_valasztas_importok.py",
        ".github/workflows/ci.yml",
        ".github/workflows/teszt-darabok.yml",
        "packaging/qt-runtime-deps.txt",
    ],
)
def test_kozos_beallitasok_valtozasanal_teljes_keszletet_valaszt(repo, ut: str) -> None:
    dontes = tv.select_tests(repo, [ut])

    assert dontes.teljes, ut
    assert set(dontes.fajlok) == set(tv.discover_tests(repo))


def test_mappa_conftestje_csak_a_mappaja_alatti_teszteket_valasztja(repo: Path) -> None:
    dontes = tv.select_tests(repo, ["tests/app/qml_functional/conftest.py"])

    assert not dontes.teljes
    assert "tests/app/qml_functional/test_nev.py" in dontes.fajlok
    assert "tests/app/test_nem_qml.py" not in dontes.fajlok


def test_tesztsegedet_a_nevevel_hivatkozo_teszt_valasztja_nem_a_teljes_keszletet(
    repo: Path,
) -> None:
    (repo / "tests/support").mkdir(exist_ok=True)
    (repo / "tests/support/segitseg.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests/test_hasznalja.py").write_text(
        "from tests.support.segitseg import x\n", encoding="utf-8"
    )

    dontes = tv.select_tests(repo, ["tests/support/segitseg.py"])

    assert not dontes.teljes
    assert "tests/test_hasznalja.py" in dontes.fajlok
    assert "tests/test_kozvetlen.py" not in dontes.fajlok


def test_hivatkozas_nelkuli_tesztsegedet_nem_tolt_be_pytest_ezert_nem_teljes(
    repo: Path,
) -> None:
    (repo / "tests/helper_nincs.py").write_text("x = 1\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["tests/helper_nincs.py"])

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_torolt_teszt_neve_a_meresi_tablaban_nem_teljes_keszlet(repo: Path) -> None:
    (repo / "scripts").mkdir(exist_ok=True)
    (repo / "scripts/teszt_idok.json").write_text(
        '{"tests/test_torolt.py": 4.0}\n', encoding="utf-8"
    )

    dontes = tv.select_tests(repo, ["tests/test_torolt.py"])

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_docs_emlites_nem_szamit_tesztsegednel(repo: Path) -> None:
    (repo / "tests/support").mkdir(exist_ok=True)
    (repo / "tests/support/magany.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs/leiras.md").write_text("A magany.py segédet említi.\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["tests/support/magany.py"])

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_docstringben_emlitett_eszkoz_nem_huzza_be_a_forrast(repo: Path) -> None:
    (repo / "tools").mkdir()
    (repo / "tools/eszkoz_4922.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src/picasapy/leiras.py").write_text(
        '"""A mércéje: `tools/eszkoz_4922.py` (# komment is)."""\n'
        "# tools/eszkoz_4922.py\n"
        "x = 1\n",
        encoding="utf-8",
    )

    dontes = tv.select_tests(repo, ["tools/eszkoz_4922.py"])

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_kodbeli_szovegreferencia_a_forrast_es_a_tesztjeit_is_behuzza(repo: Path) -> None:
    (repo / "tools").mkdir()
    (repo / "tools/eszkoz_4922.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src/picasapy/futtato.py").write_text(
        'SZKRIPT = "tools/eszkoz_4922.py"\n', encoding="utf-8"
    )
    (repo / "tests/test_futtato.py").write_text(
        "from picasapy import futtato\n", encoding="utf-8"
    )

    dontes = tv.select_tests(repo, ["tools/eszkoz_4922.py"])

    assert not dontes.teljes
    assert "tests/test_futtato.py" in dontes.fajlok


def test_tesztadat_a_nevet_hivatkozo_teszttel_fut(repo: Path) -> None:
    adat = "tests/app/qml_functional/data/minta_4922.json"
    (repo / adat).parent.mkdir(parents=True)
    (repo / adat).write_text("{}\n", encoding="utf-8")
    (repo / "tests/app/test_adat_nev.py").write_text(
        'ADAT = "minta_4922.json"\n', encoding="utf-8"
    )

    dontes = tv.select_tests(repo, [adat])

    assert not dontes.teljes
    assert "tests/app/test_adat_nev.py" in dontes.fajlok
    assert "tests/app/test_nem_qml.py" not in dontes.fajlok


def test_nevtelen_tesztadat_a_mappaja_tesztjeit_futtatja(repo: Path) -> None:
    adat = "tests/app/qml_functional/data/nevtelen_4922.json"
    (repo / adat).parent.mkdir(parents=True)
    (repo / adat).write_text("{}\n", encoding="utf-8")

    dontes = tv.select_tests(repo, [adat])

    assert not dontes.teljes
    assert "tests/app/qml_functional/test_nev.py" in dontes.fajlok
    assert "tests/app/test_nem_qml.py" not in dontes.fajlok


def test_eszkozkonfiguracio_hivatkozas_nelkul_nem_teljes(repo: Path) -> None:
    (repo / ".codex").mkdir()
    (repo / ".codex/hooks.json").write_text("{}\n", encoding="utf-8")

    dontes = tv.select_tests(repo, [".codex/hooks.json"])

    assert not dontes.teljes
    assert set(dontes.fajlok) == set(tv.SMOKE_TESTS)


def test_nev_nelkul_nem_importalt_forrasmodul_teljes_keszlet(repo: Path) -> None:
    # Dinamikus import (`import_module(f"...{nev}")`) nem látszik a gráfban,
    # ezért a név nélküli, senki által nem importált modul marad teljes.
    (repo / "src/picasapy/elszigetelt.py").write_text("x = 1\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["src/picasapy/elszigetelt.py"])

    assert dontes.teljes


def test_nev_szerint_inditott_forrasmodult_a_nevet_emlito_teszt_futtatja(repo: Path) -> None:
    (repo / "src/picasapy/elszigetelt.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests/test_inditja.py").write_text(
        'SZAMITOGEP = ["python", "-m", "picasapy.elszigetelt"]\n', encoding="utf-8"
    )

    dontes = tv.select_tests(repo, ["src/picasapy/elszigetelt.py"])

    assert not dontes.teljes
    assert "tests/test_inditja.py" in dontes.fajlok


def test_tobb_mint_hatvan_szazalekot_erinto_modul_a_pontos_fogyasztoit_adja(
    repo: Path,
) -> None:
    # 26 teszt közül 17 (= 2 + 15) importálja a modult: a 60%-os határ fölött.
    sokan = [f"tests/test_sok_{i}.py" for i in range(15)]
    for ut in sokan:
        (repo / ut).write_text("from picasapy import forras\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["src/picasapy/forras.py"])

    assert not dontes.teljes
    assert set(sokan) <= set(dontes.fajlok)
    assert "tests/app/test_nem_qml.py" not in dontes.fajlok


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


def test_docs_valtozasnal_a_teljes_utvonalat_vagy_alapnevet_emlito_teszt_is_fut(
    repo: Path,
) -> None:
    utvonalas = "tests/test_spec_utvonal.py"
    alapneves = "tests/test_spec_alapnev.py"
    masik = "tests/test_spec_masik.py"
    (repo / utvonalas).write_text(
        'SPEC = "docs/specs/picasa-format.md"\n', encoding="utf-8"
    )
    (repo / alapneves).write_text(
        'SPEC = "picasa-format.md"\n', encoding="utf-8"
    )
    (repo / masik).write_text('SPEC = "masik.md"\n', encoding="utf-8")

    dontes = tv.select_tests(repo, ["docs/specs/picasa-format.md"])

    assert not dontes.teljes
    assert utvonalas in dontes.fajlok
    assert alapneves in dontes.fajlok
    assert masik not in dontes.fajlok
    assert set(tv.SMOKE_TESTS) <= set(dontes.fajlok)


def test_a_gyorsbillentyu_spec_dokumentacios_valtozasnal_kivalasztja_a_regresszios_orot() -> None:
    dontes = tv.select_tests(
        _ROOT, ["docs/specs/picasa-gyorsbillentyuk.md"]
    )

    assert "tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py" in dontes.fajlok


def test_a_docs_only_kivalasztott_tesztjei_elinditjak_az_ubuntu_darabot() -> None:
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    ubuntu = ci.split("\n  darabok-ubuntu:", 1)[1].split("\n  darabok-windows:", 1)[0]
    kotelezo = ci.split("\n  test-ubuntu:", 1)[1].split("\n  test-windows:", 1)[0]

    assert "needs.valtozas.outputs.darabszam != '0'" in ubuntu
    assert "needs.valtozas.outputs.darabszam != '0'" in kotelezo


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


def test_a_windows_pr_lista_csak_a_kivalasztott_windows_erzekeny_tesztekbol_all(
    repo: Path,
) -> None:
    windows_teszt = "tests/app/test_windows_csapdak_1082.py"
    altalanos_teszt = "tests/test_fogyaszto.py"
    (repo / windows_teszt).parent.mkdir(parents=True, exist_ok=True)
    (repo / windows_teszt).write_text("def test_win(): pass\n", encoding="utf-8")
    kiv = tv.Selection(
        (windows_teszt, altalanos_teszt, *tv.SMOKE_TESTS), False, "próba"
    )

    windows = tv.windows_only_tests(repo, kiv, force_full=False)

    # A startup smoke próba a kötelező füstkészlet része, Windows alatt is fut.
    assert windows.fajlok == (
        windows_teszt,
        "tests/app/test_startup_smoke_4687.py",
    )
    assert windows.teljes is False


def test_a_main_windows_laba_a_teljes_keszletet_kapja(repo: Path) -> None:
    teljes = tv.windows_only_tests(
        repo, tv.Selection(tuple(tv.discover_tests(repo)), True, "main"),
        force_full=True,
    )

    assert teljes.fajlok == tuple(tv.discover_tests(repo))
    assert teljes.teljes is True


def test_a_windows_seged_tesztlista_ures_lehet() -> None:
    assert tv.windows_only_tests(
        _ROOT, tv.Selection(("tests/test_teszt_valasztas.py",), False, "pr"),
        force_full=False,
    ).fajlok == ()


def test_a_windows_erzekeny_lista_minden_utvonala_letezik() -> None:
    assert tv.WINDOWS_SENSITIVE_TESTS
    assert set(tv.WINDOWS_SENSITIVE_TESTS) <= set(tv.discover_tests(_ROOT))


def test_a_windows_agat_orzo_tesztek_rajta_vannak_a_pr_listan(
    repo: Path,
) -> None:
    windows_agak = {
        "tests/app/qml_functional/test_adjust_timestamp_4332.py",
        "tests/app/qml_functional/test_earth_megtekintes_1589.py",
        "tests/app/qml_functional/test_eredeti_geometria_racs_2494.py",
        "tests/app/qml_functional/test_maradek_arc_video_4229.py",
        "tests/app/qml_functional/test_tiszta_profil_4317.py",
        "tests/app/qml_functional/test_video_panel_4566.py",
        "tests/app/test_application.py",
        "tests/app/test_eltunt_gyoker_vedelme_1560.py",
        "tests/app/test_fileops_controller.py",
        "tests/app/test_folder_hierarchy.py",
        "tests/app/test_indulasi_fusteszt_699.py",
        "tests/app/test_kepernyovedo_tetlenseg_4613.py",
        "tests/app/test_mentes_gyoker_feloldas_3776.py",
        "tests/app/test_qml_video.py",
        "tests/app/test_startup_smoke_4687.py",
        "tests/app/test_timestamp_controller_4693.py",
        "tests/app/test_timestamp_video_4885.py",
        "tests/export/test_export_hibaagak_1617.py",
        "tests/fileops/test_move_folder.py",
        "tests/index/test_sync.py",
        "tests/metadata/test_iptc_writer.py",
        "tests/perf/test_exportcel_utvonalfeloldas_2483.py",
        "tests/perf/test_tarolo_tipus_1660.py",
        "tests/test_ioutil.py",
        "tests/test_paths.py",
        "tests/test_run_tests_maradek_eletjel_1358.py",
        "tests/test_run_tests_osszeomlas_diagnosztika_1457.py",
    }
    posix_only = "tests/app/test_folder_dedup_repro.py"
    selection = tv.Selection(tuple(sorted(windows_agak | {posix_only})), False, "PR")

    windows = tv.windows_only_tests(repo, selection, force_full=False)

    assert set(windows.fajlok) == windows_agak


def test_ci_es_futtato_valtozasnal_a_fogyaszto_tesztcsoport_fut(repo: Path) -> None:
    olvasok = {
        ".github/workflows/ci.yml": "tests/test_ci_fogyaszto.py",
        "scripts/run_tests.py": "tests/test_futtato_fogyaszto.py",
        "scripts/kepesseg_or_baseline.txt": "tests/tools/test_kepesseg_or_1476.py",
    }
    for ut, teszt in olvasok.items():
        (repo / ut).parent.mkdir(parents=True, exist_ok=True)
        (repo / ut).write_text("", encoding="utf-8")
        (repo / teszt).parent.mkdir(parents=True, exist_ok=True)
        needle = Path(ut).name if ut.endswith(".yml") or ut.endswith(".txt") else "run_tests"
        (repo / teszt).write_text(f"# {needle}\n", encoding="utf-8")

    for ut, teszt in olvasok.items():
        dontes = tv.select_tests(repo, [ut])

        assert dontes.teljes is False, ut
        assert teszt in dontes.fajlok, ut
        assert set(tv.SMOKE_TESTS) <= set(dontes.fajlok), ut


def test_ismeretlen_ci_fajl_tovabbra_is_teljes_keszletet_valaszt(repo: Path) -> None:
    assert tv.select_tests(repo, [".github/workflows/ismeretlen.yml"]).teljes


@pytest.mark.parametrize(
    ("ut", "fogyaszto"),
    [
        (".github/workflows/ci.yml", "tests/test_teszt_valasztas.py"),
        (".github/workflows/teszt-darabok.yml", "tests/test_ci_kor_ideje_1127.py"),
        ("scripts/run_tests.py", "tests/test_run_tests_fajllista_4922.py"),
        (
            "scripts/kepesseg_or_baseline.txt",
            "tests/tools/test_kepesseg_or_1476.py",
        ),
    ],
)
def test_a_teljes_keszletre_visszaeso_valodi_utvonalak_szukuleteset_orzik(
    ut: str, fogyaszto: str,
) -> None:
    dontes = tv.select_tests(_ROOT, [ut])

    assert dontes.teljes is False, ut
    assert fogyaszto in dontes.fajlok, ut


def test_qml_valtozas_csak_a_nev_szerint_hivatkozo_teszteket_valaszt(
    repo: Path,
) -> None:
    cel = "tests/app/qml_functional/test_photoviewer.py"
    masik = "tests/app/qml_functional/test_masik.py"
    (repo / cel).write_text('QML = "PhotoViewer.qml"\n', encoding="utf-8")
    (repo / masik).write_text("def test_masik(): assert True\n", encoding="utf-8")

    dontes = tv.select_tests(repo, ["src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"])

    assert cel in dontes.fajlok
    assert masik not in dontes.fajlok


def _git_commit(root: Path) -> str:
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git", "-c", "user.name=Teszt", "-c", "user.email=teszt@example.invalid",
            "commit", "-qm", "teszt",
        ],
        cwd=root,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout.strip()


def _main_qml_repo(repo: Path) -> tuple[str, Path]:
    qml = repo / "src/picasapy/app/qml/Main.qml"
    qml.parent.mkdir(parents=True, exist_ok=True)
    qml.write_text(
        "import QtQuick\n"
        "ApplicationWindow {\n"
        "    id: window\n"
        "    width: 1280\n"
        "    Item {\n"
        "        id: targetPane\n"
        "        objectName: \"targetPane\"\n"
        "        property int spacing: 4\n"
        "        SpecialPane { id: specialPane }\n"
        "    }\n"
        "    Item { id: siblingPane; objectName: \"siblingPane\" }\n"
        "}\n",
        encoding="utf-8",
    )
    functional = repo / "tests/app/qml_functional"
    (functional / "test_target_pane.py").write_text(
        'def test_target(): assert "targetPane" and "SpecialPane"\n',
        encoding="utf-8",
    )
    (functional / "test_sibling_pane.py").write_text(
        'def test_sibling(): assert "siblingPane"\n', encoding="utf-8"
    )
    (functional / "test_main_named.py").write_text(
        'def test_main(): assert "Main.qml"\n', encoding="utf-8"
    )
    (functional / "test_unrelated.py").write_text(
        "def test_unrelated(): assert True\n", encoding="utf-8"
    )
    base = _git_commit(repo)
    return base, qml


def _select_git_diff(repo: Path, base: str) -> tv.Selection:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout.strip()
    return tv._selection_for_cli(repo, base=base, head=head, force_full=False)


def test_main_qml_azonosithato_blokkvaltozasa_szukuletett_keszletet_valaszt(
    repo: Path,
) -> None:
    base, qml = _main_qml_repo(repo)
    qml.write_text(
        qml.read_text(encoding="utf-8").replace("spacing: 4", "spacing: 8"),
        encoding="utf-8",
    )
    _git_commit(repo)

    dontes = _select_git_diff(repo, base)

    assert not dontes.teljes
    assert "tests/app/qml_functional/test_target_pane.py" in dontes.fajlok
    assert "tests/app/qml_functional/test_main_named.py" in dontes.fajlok
    assert "tests/app/qml_functional/test_sibling_pane.py" not in dontes.fajlok
    assert "tests/app/qml_functional/test_unrelated.py" not in dontes.fajlok


def test_main_qml_importvaltozasa_teljes_keszletet_valaszt(repo: Path) -> None:
    base, qml = _main_qml_repo(repo)
    qml.write_text(
        qml.read_text(encoding="utf-8").replace(
            "import QtQuick", "import QtQuick.Controls"
        ),
        encoding="utf-8",
    )
    _git_commit(repo)

    dontes = _select_git_diff(repo, base)

    assert dontes.teljes
    assert set(dontes.fajlok) == set(tv.discover_tests(repo))


def test_main_qml_gyokerproperty_valtozasa_teljes_keszletet_valaszt(
    repo: Path,
) -> None:
    base, qml = _main_qml_repo(repo)
    qml.write_text(
        qml.read_text(encoding="utf-8").replace("width: 1280", "width: 1440"),
        encoding="utf-8",
    )
    _git_commit(repo)

    dontes = _select_git_diff(repo, base)

    assert dontes.teljes
    assert set(dontes.fajlok) == set(tv.discover_tests(repo))


def test_main_qml_dinamikus_objectname_teljes_keszletet_valaszt(
    repo: Path,
) -> None:
    base, qml = _main_qml_repo(repo)
    qml.write_text(
        qml.read_text(encoding="utf-8").replace(
            'objectName: "targetPane"', "objectName: paneObjectName"
        ).replace("spacing: 4", "spacing: 8"),
        encoding="utf-8",
    )
    _git_commit(repo)

    dontes = _select_git_diff(repo, base)

    assert dontes.teljes
    assert set(dontes.fajlok) == set(tv.discover_tests(repo))


def test_a_pr_darabok_szama_a_mereshez_igazodik_mainen_tizenhat_a_plafon() -> None:
    fajlok = [f"tests/test_{i}.py" for i in range(80)]
    idok = {ut: 57.225 for ut in fajlok}  # összesen 76,3 perc, a mért PR-minta

    pr = tv.ci_shard_plan(fajlok, idok, teljes=False, main_run=False)
    main = tv.ci_shard_plan(fajlok, idok, teljes=True, main_run=True)

    assert pr.darabszam == 20
    assert main.darabszam == 16
    kiosztas = [
        set(tv.darab_fajljai(fajlok, idok, sorszam, pr.darabszam))
        for sorszam in range(1, pr.darabszam + 1)
    ]
    assert set().union(*kiosztas) == set(fajlok)
    assert sum(map(len, kiosztas)) == len(fajlok)
    teljes_pr = tv.ci_shard_plan(fajlok, idok, teljes=True, main_run=False)
    teljes_kiosztas = [
        tv.darab_fajljai(
            fajlok, idok, sorszam, teljes_pr.darabszam, teljes=True
        )
        for sorszam in range(1, teljes_pr.darabszam + 1)
    ]
    assert teljes_pr.darabszam == 20
    assert set().union(*map(set, teljes_kiosztas)) == set(fajlok)
    assert sum(map(len, teljes_kiosztas)) == len(fajlok)
