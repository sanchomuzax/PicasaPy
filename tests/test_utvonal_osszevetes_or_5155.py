"""Őr: a tests/app assert-jei nem vethetnek össze egyenlőségre nyers `str(Path)`-ot (#5155).

## A hibafajta

Windowson a `str(Path(...))` visszaperjeles utat ad. Ha a várt érték ebből készül,
a felületről vagy a vágólapról érkező út viszont előreperjeles, és az egyenlőség a
windowsos CI-n bukik, Linuxon zöld marad. Ma kétszer fordult elő:

- #5138, javítva #5141: a fanézet sornevében `f"hierRow:{str(lib / 'kozep')}"`;
- #5152, javítva #5154: a vágólapon `fajlok == [str(controller.photos.filePathAt(0))]`.

## A szabály

Az őr a `tests/app` alatti `assert`-ek `==` és `!=` összevetéseit nézi. Hiba, ha az
összevetés egyik oldalán (akár listában, halmazban, tuple-ben, list comprehension-ben,
f-sztringben vagy `+` összefűzésben) közvetlenül `str(...)` áll, amelynek argumentuma
útvonal-szerű:

- `/` művelet (`tmp_path / "a.jpg"`, `lib / "kozep"`);
- `Path(...)` konstruktor;
- `.filePathAt(...)` hívás;
- a `tmp_path` név, vagy olyan név, amelyet a fájlban útvonalnak adtunk értékül.

A normalizált alak nem hiba. Ha az összevetés oldalán nincs közvetlen `str(...)`
(`Path(a) == Path(b)`, `p.as_posix() == ...`, `str(p).replace(...) == ...`,
`os.path.normpath(str(p)) == ...`), az őr nem jelez. A tartalmazás (`in`) és a
rendezés (`<`) nem tartozik ide.

Ismert korlát: a függvényből visszakapott útvonalat (`_lib(tmp_path)`) nem követi,
és a tartalmazást (`in`) sem vizsgálja.

## A nyilvántartás

A szabály a mai tests/app-ra 178 találatot ad 78 fájlban. A találatokat soronként
átnéztük, és a `KIVETEL`-ben fájlonként, darabszámmal rögzítettük, miért
biztonságosak. A darabszám pontos: ha új találat jön, vagy egy régi eltűnik,
az őr hibát ad, és a nyilvántartást át kell nézni. Új fájl csak indoklással
kerülhet a listára.
"""

from __future__ import annotations

import ast
import warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

TESZT_GYOKER = Path(__file__).resolve().parent
TESZT_APP = TESZT_GYOKER / "app"

UTVONAL_KONSTRUKTOR = frozenset(
    {"Path", "PurePath", "PosixPath", "WindowsPath", "PurePosixPath", "PureWindowsPath"}
)
UTVONAL_METODUS = frozenset(
    {"filePathAt", "joinpath", "resolve", "absolute", "with_name", "with_suffix"}
)


@dataclass(frozen=True)
class Talalat:
    fajl: str
    sor: int
    kulcs: str


def _hivas_neve(hivas: ast.Call) -> str | None:
    if isinstance(hivas.func, ast.Name):
        return hivas.func.id
    if isinstance(hivas.func, ast.Attribute):
        return hivas.func.attr
    return None


def _utvonal_szeru(kifejezes: ast.expr, nevek: frozenset[str]) -> bool:
    if isinstance(kifejezes, ast.Name):
        return kifejezes.id == "tmp_path" or kifejezes.id in nevek
    if isinstance(kifejezes, ast.BinOp):
        return isinstance(kifejezes.op, ast.Div)
    if isinstance(kifejezes, ast.Call):
        nev = _hivas_neve(kifejezes)
        return nev in UTVONAL_KONSTRUKTOR or nev in UTVONAL_METODUS
    return False


def _utvonal_nevek(fa: ast.AST) -> frozenset[str]:
    """A fájlban útvonalnak értékadott nevek (ismétlés a függőségek lezárásáig)."""
    nevek: set[str] = set()
    bovult = True
    while bovult:
        bovult = False
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.Assign):
                continue
            if not _utvonal_szeru(csomopont.value, frozenset(nevek)):
                continue
            for cel in csomopont.targets:
                if isinstance(cel, ast.Name) and cel.id not in nevek:
                    nevek.add(cel.id)
                    bovult = True
    return frozenset(nevek)


def _nyers_utvonal_str(kifejezes: ast.expr, nevek: frozenset[str]) -> bool:
    """Igaz, ha az összevetés oldalán közvetlen, útvonal-szerű `str(...)` áll.

    Más hívás belsejébe nem megyünk: `Path(...)`, `.as_posix()`, `.replace(...)` és
    `os.path.normpath(...)` burkolása így automatikusan normalizált marad.
    """
    if isinstance(kifejezes, ast.Call):
        return (
            _hivas_neve(kifejezes) == "str"
            and len(kifejezes.args) == 1
            and _utvonal_szeru(kifejezes.args[0], nevek)
        )
    if isinstance(kifejezes, (ast.List, ast.Tuple, ast.Set)):
        return any(_nyers_utvonal_str(elem, nevek) for elem in kifejezes.elts)
    if isinstance(kifejezes, ast.Dict):
        elemek = [*kifejezes.keys, *kifejezes.values]
        return any(_nyers_utvonal_str(elem, nevek) for elem in elemek if elem is not None)
    if isinstance(kifejezes, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return _nyers_utvonal_str(kifejezes.elt, nevek)
    if isinstance(kifejezes, ast.JoinedStr):
        return any(_nyers_utvonal_str(resz, nevek) for resz in kifejezes.values)
    if isinstance(kifejezes, ast.FormattedValue):
        return _utvonal_szeru(kifejezes.value, nevek) or _nyers_utvonal_str(
            kifejezes.value, nevek
        )
    if isinstance(kifejezes, ast.BinOp) and isinstance(kifejezes.op, ast.Add):
        return _nyers_utvonal_str(kifejezes.left, nevek) or _nyers_utvonal_str(
            kifejezes.right, nevek
        )
    return False


def _assert_nyers(assert_csomopont: ast.Assert, nevek: frozenset[str]) -> bool:
    for csomopont in ast.walk(assert_csomopont.test):
        if not isinstance(csomopont, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in csomopont.ops):
            continue
        oldalak = [csomopont.left, *csomopont.comparators]
        if any(_nyers_utvonal_str(oldal, nevek) for oldal in oldalak):
            return True
    return False


def keres_forrasban(forras: str, fajl: str = "<minta>") -> list[Talalat]:
    # A régi, nem nyers sztringekben lévő érvénytelen escape-ek (SyntaxWarning) nem ennek
    # az őrnek a dolga: a fájlok a saját tesztjeik részei, itt csak a fa kell.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        fa = ast.parse(forras, filename=fajl)
    nevek = _utvonal_nevek(fa)
    asserts = sorted(
        (csomopont for csomopont in ast.walk(fa) if isinstance(csomopont, ast.Assert)),
        key=lambda csomopont: csomopont.lineno,
    )
    return [
        Talalat(fajl=fajl, sor=csomopont.lineno, kulcs=ast.unparse(csomopont.test))
        for csomopont in asserts
        if _assert_nyers(csomopont, nevek)
    ]


RONTAS_VAGOLAP = """
def test_vagolap(controller):
    assert fajlok == [str(controller.photos.filePathAt(0))]
"""

RONTAS_FANEZET = """
def test_fanezet(lib):
    assert sor.objectName == f"hierRow:{str(lib / 'kozep')}"
"""

NORMALIZALT_ALAKOK = [
    "assert Path(a) == Path(b)",
    "assert [Path(f) for f in fajlok] == [Path(str(controller.photos.filePathAt(0)))]",
    r'assert str(p).replace("\\", "/") == "a/b.jpg"',
    'assert p.as_posix() == "a/b.jpg"',
    'assert os.path.normpath(str(p)) == os.path.normpath("a/b.jpg")',
    "assert str(p) in lista",
    'assert str(szoveg) == "abc"',
]


def test_rontas_vagolapi_alak_piros():
    talalatok = keres_forrasban(RONTAS_VAGOLAP)
    assert len(talalatok) == 1, "a #5152 nyers str(Path)-összevetését jeleznie kell"


def test_rontas_fanezet_alak_piros():
    talalatok = keres_forrasban(RONTAS_FANEZET)
    assert len(talalatok) == 1, "a #5138 nyers str(Path)-összevetését jeleznie kell"


@pytest.mark.parametrize("sor", NORMALIZALT_ALAKOK)
def test_normalizalt_alak_nem_lelet(sor):
    assert keres_forrasban(sor) == []


def _tests_app_talalatai() -> list[Talalat]:
    talalatok: list[Talalat] = []
    for path in sorted(TESZT_APP.rglob("*.py")):
        rel = path.relative_to(TESZT_GYOKER.parent).as_posix()
        talalatok += keres_forrasban(path.read_text(encoding="utf-8"), fajl=rel)
    return talalatok


KATEGORIAK = {
    "natív": (
        "mindkét oldal natív `str(Path)`-alak: Python-oldali érték natív előállítóval "
        "(`full_path`, `normalize_path`, `to_local_path`, az app `str(Path)`-visszaadása), "
        "vagy QML-tulajdonságon át változatlanul visszaolvasva. A `/`-t adó előállítók "
        "(hierarchia-`_join`, `flat_key`, `path_key`, `QUrl.toLocalFile`) ezeken az "
        "assert-eken nem szerepelnek."
    ),
    "különbség": "`!=` állítás, amely azt rögzíti, hogy az érték NEM egyezik",
    "normalizált": "a másik oldal már `str(Path(...))`-szel normalizált a teszt-segédben",
    "indexelt": "QML-fa-kulcs indexelt mappánál: a tárolt, natív út (#5141)",
}

KIVETEL: dict[str, tuple[int, str]] = {
    "tests/app/qml_diavetites_beallitasok_probe_4320.py": (2, "natív"),
    "tests/app/qml_functional/test_ajandek_cd_bekotes_3503.py": (1, "natív"),
    "tests/app/qml_functional/test_collage_output_ui_949.py": (1, "natív"),
    "tests/app/qml_functional/test_earth_megtekintes_1589.py": (1, "natív"),
    "tests/app/qml_functional/test_exportalt_kepek_csomopont_1565.py": (1, "natív"),
    "tests/app/qml_functional/test_film_panel_4125.py": (2, "natív"),
    "tests/app/qml_functional/test_film_ujraexport_4612.py": (1, "natív"),
    "tests/app/qml_functional/test_folder_file_transfer_5007.py": (2, "natív"),
    "tests/app/qml_functional/test_folder_pane_projects_1029.py": (2, "natív"),
    "tests/app/qml_functional/test_folder_rename_qml_4482.py": (3, "natív"),
    "tests/app/qml_functional/test_folder_sort_click_4890.py": (2, "natív"),
    "tests/app/qml_functional/test_folder_split_4534.py": (1, "natív"),
    "tests/app/qml_functional/test_mentes_szuro_main_3681.py": (1, "indexelt"),
    "tests/app/qml_functional/test_mentes_visszajelzes_1566.py": (2, "natív"),
    "tests/app/qml_functional/test_movie_transition_preview_4820.py": (1, "natív"),
    "tests/app/qml_functional/test_tiszta_profil_fomenuk_4420_kereses.py": (1, "natív"),
    "tests/app/test_ajandek_cd_vezerlo_3503.py": (2, "natív"),
    "tests/app/test_application.py": (6, "natív"),
    "tests/app/test_collage_controller_949.py": (2, "natív"),
    "tests/app/test_controller.py": (9, "natív"),
    "tests/app/test_create_controller.py": (1, "natív"),
    "tests/app/test_custom_collections_ini_4589.py": (3, "natív"),
    "tests/app/test_dedup_controller.py": (8, "natív"),
    "tests/app/test_dedup_scope.py": (2, "natív"),
    "tests/app/test_dirty_futasjelzo_1440.py": (4, "natív"),
    "tests/app/test_drop_import_controller.py": (7, "natív"),
    "tests/app/test_elo_frissules_1435.py": (2, "natív"),
    "tests/app/test_eltunt_gyoker_vedelme_1560.py": (4, "natív"),
    "tests/app/test_email_controller.py": (1, "különbség"),
    "tests/app/test_exportcel_indexelese_1565.py": (1, "natív"),
    "tests/app/test_exported_folders.py": (2, "natív"),
    "tests/app/test_face_exclusion_controller.py": (2, "natív"),
    "tests/app/test_face_scan_controller.py": (1, "különbség"),
    "tests/app/test_fajl_vagolap_1526.py": (3, "normalizált"),
    "tests/app/test_fileops_conflict_dialog.py": (2, "natív"),
    "tests/app/test_fileops_controller.py": (8, "natív"),
    "tests/app/test_fileops_controller_split_folder_4534.py": (2, "natív"),
    "tests/app/test_fileops_controller_uj_mappa_1614.py": (1, "natív"),
    "tests/app/test_folder_rename_4482.py": (8, "natív"),
    "tests/app/test_folder_tree_controller.py": (3, "natív"),
    "tests/app/test_gyoker_athelyezes_kovetes_1542.py": (10, "natív"),
    "tests/app/test_hasab_gyokerek_1407.py": (1, "natív"),
    "tests/app/test_hatterkep_linux_asztalok_4605.py": (2, "natív"),
    "tests/app/test_hatterkep_windows_2985.py": (1, "natív"),
    "tests/app/test_import_celmappak_1785.py": (5, "natív"),
    "tests/app/test_import_source_controller.py": (3, "natív"),
    "tests/app/test_indulasi_fusteszt_699.py": (1, "natív"),
    "tests/app/test_initial_scan.py": (4, "natív"),
    "tests/app/test_kepernyovedo_tetlenseg_4613.py": (1, "natív"),
    "tests/app/test_kimenet_resync_1539.py": (1, "natív"),
    "tests/app/test_mappa_athelyezes_resync_1538.py": (5, "natív"),
    "tests/app/test_mappa_frissesseg_1435.py": (2, "natív"),
    "tests/app/test_mappa_zene_4448.py": (1, "natív"),
    "tests/app/test_mappa_zene_ui_4448.py": (1, "natív"),
    "tests/app/test_mentes_gyoker_feloldas_3776.py": (1, "natív"),
    "tests/app/test_mentes_mappak_vezerlo_3594.py": (1, "natív"),
    "tests/app/test_mentes_racs_szuro_vezerlo_3751.py": (1, "natív"),
    "tests/app/test_mentes_vezerlo_440.py": (2, "natív"),
    "tests/app/test_models.py": (1, "natív"),
    "tests/app/test_movie_clip_export_4564.py": (1, "natív"),
    "tests/app/test_nativ_utvonal_kiiras_1629.py": (2, "natív"),
    "tests/app/test_offline_folder_notice_459.py": (2, "natív"),
    "tests/app/test_photo_ops_controller.py": (1, "natív"),
    "tests/app/test_picasa_manual_import_4592.py": (1, "natív"),
    "tests/app/test_platform_storage_1076.py": (1, "natív"),
    "tests/app/test_print_controller.py": (1, "natív"),
    "tests/app/test_project_folders_controller_1029.py": (1, "natív"),
    "tests/app/test_projekt_mappa_kivetel_2031.py": (1, "natív"),
    "tests/app/test_qml_dedup.py": (2, "natív"),
    "tests/app/test_qml_folder_manager_kattintas_1200.py": (1, "natív"),
    "tests/app/test_qml_perf_panel.py": (1, "natív"),
    "tests/app/test_rejtett_mappa_vezerlo_4597.py": (2, "natív"),
    "tests/app/test_relocate_controller.py": (3, "natív"),
    "tests/app/test_talca_album_token_szabaly_2741.py": (1, "natív"),
    "tests/app/test_tesztuzem_controller_1654.py": (1, "natív"),
    "tests/app/test_tray_controller.py": (1, "natív"),
    "tests/app/test_video_thumbnail_timeout_4273.py": (1, "natív"),
    "tests/app/test_webexport_controller.py": (2, "natív"),
}


def _elteres(talalatok: list[Talalat]) -> list[str]:
    """A tényleges és a nyilvántartott találatok eltérései, emberi olvasatban."""
    tenyleges = Counter(talalat.fajl for talalat in talalatok)
    hibak: list[str] = []
    for fajl, db in sorted(tenyleges.items()):
        nyilvantartott = KIVETEL.get(fajl, (0, ""))[0]
        if db == nyilvantartott:
            continue
        hibak.append(f"{fajl}: {db} találat, nyilvántartott: {nyilvantartott}")
        hibak += [
            f"    {talalat.sor}: {talalat.kulcs}"
            for talalat in talalatok
            if talalat.fajl == fajl
        ]
    for fajl in sorted(KIVETEL):
        if fajl not in tenyleges:
            hibak.append(f"{fajl}: a nyilvántartásban van, de nincs találat (elavult)")
    return hibak


def test_kivetel_kategoriai_ismertek():
    ismeretlen = {kat for _db, kat in KIVETEL.values()} - set(KATEGORIAK)
    assert not ismeretlen, f"ismeretlen kategória a nyilvántartásban: {ismeretlen}"


def test_tests_app_nyers_utvonal_osszevetes_csak_nyilvantartott():
    hibak = _elteres(_tests_app_talalatai())
    assert not hibak, "a nyers str(Path)-összevetések nyilvántartása eltér:\n" + "\n".join(
        hibak
    )
