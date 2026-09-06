"""A basetemp-kapu hook próbasora — #1649.

A kapu azt a hibaosztályt fogja meg, ami 2026-08-15-én **5,8 GB**-ot hagyott a
tmpfs-en: csupasz `pytest` közös `--basetemp` nélkül, öt párhuzamos körben.
A kár nem a vétkes körnél jelentkezik, hanem a párhuzamos munkameneteknél.

A vaklárma-osztályokat a `test_release_kapu.py` tanulságai alapján előre
őrizzük: a parancs SZÖVEGÉBEN előforduló említés (grep, fájlírás) nem
blokkolhat, és a projekt saját futtatója sem.
"""

import importlib.util
import io
import json
import pathlib

import pytest

_UT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "basetemp_kapu.py"
_spec = importlib.util.spec_from_file_location("basetemp_kapu", _UT)
kapu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapu)


BLOKKOLANDO = [
    "pytest tests/app",
    "python -m pytest tests/ini",
    "python3 -m pytest tests/app/test_x.py -q",
    "cd /x && python3 -m pytest tests -q",
    "timeout 60 python3 -m pytest tests/app/test_y.py",
    "python3 -m pytest -q tests/app && echo kesz",
]

ATENGEDENDO = [
    # a projekt saját futtatója — maga adja a futásonként egyedi basetempet
    "python scripts/run_tests.py",
    "python3 scripts/run_tests.py --gyors",
    # explicit közös basetemp
    #
    # ⚠️ #2558: a `tests/app` MAPPA itt SZÁNDÉKOSAN nem szerepel többé. A
    # #1649-es kapu csak a basetempet nézte, ezért az az alak átment — és
    # 2026-09-06-án épp az döntötte el a gépet (3,18 GiB egyetlen
    # processzben, betelt swap, kényszerű újraindítás). A helyére a
    # FÁJLONKÉNTI alak került, ami a `run_tests.py` szabálya is.
    "python3 -m pytest tests/app/test_tray_controller.py --basetemp=/tmp/bt",
    "python3 -m pytest tests --basetemp /tmp/bt -q",
    "pytest tests/ini --basetemp=$SCRATCH/bt",
    # tmpdir-t nem hozó alakok
    "python3 -m pytest --help",
    "pytest -h",
    "pytest --version",
    "python3 -m pytest tests --collect-only",
    # puszta említés a parancs SZÖVEGÉBEN — a release_kapu élesben tanult osztálya
    "grep -rn 'python3 -m pytest' docs/",
    "echo 'ne hasznalj csupasz pytest-et' >> jegyzet.txt",
    "rg --files-with-matches 'pytest tests' .",
    # nem is pytest
    "git status",
    "python3 scripts/menu_lefedettseg.py",
]


@pytest.mark.parametrize("cmd", BLOKKOLANDO)
def test_csupasz_pytest_blokkolodik(cmd):
    assert kapu.blokkolando(cmd) is not None, cmd


@pytest.mark.parametrize("cmd", ATENGEDENDO)
def test_szabalyos_parancs_atmegy(cmd):
    assert kapu.blokkolando(cmd) is None, cmd


@pytest.mark.parametrize("bemenet", ["", "{", '{"tool_input": null}', "[]"])
def test_fail_open_rossz_bemenetre(bemenet, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(bemenet))
    assert kapu.main() == 0


def test_blokkolaskor_2_es_kilepokod_es_uzenet(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "pytest tests"}}))
    )
    assert kapu.main() == 2
    hiba = capsys.readouterr().err
    assert "basetemp" in hiba.lower()
    assert "run_tests.py" in hiba          # mondja meg, mit tegyen helyette


def test_szabalyos_parancsra_0(monkeypatch):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"tool_input": {"command": "python scripts/run_tests.py"}})),
    )
    assert kapu.main() == 0


# ==========================================================================
# #2558: a `tests/app` alatti MAPPÁRA indított pytest — a gépet döntötte el
# ==========================================================================
#: MÉRVE (2026-09-06): a `pytest tests/app/qml_functional -q` egyetlen
#: processze négy perc alatt 446 MiB-ról 3,18 GiB-ra hízott, a 2 GiB swap
#: betelt, a terhelés 5-ről 105-re ment, és a tulajdonosnak újra kellett
#: indítania a gépet. A közös `--basetemp` MEGVOLT — a #1649-es kapu ezt az
#: alakot nem fogta meg, mert csak a basetempet nézte.
APP_MAPPA_BLOKKOLANDO = [
    "python3 -m pytest tests/app/qml_functional -q --basetemp=/tmp/bt",
    "python3 -m pytest tests/app -q --basetemp=/tmp/bt",
    "python3 -m pytest tests/app/qml_functional/ -q --basetemp=/tmp/bt",
    "pytest tests/app/qml_functional --basetemp=/tmp/bt",
    "timeout 900 python3 -m pytest tests/app/qml_functional -q --basetemp=/tmp/bt",
    # több cél között ELREJTVE is meg kell fogni
    "python3 -m pytest tests/perf tests/app/qml_functional --basetemp=/tmp/bt",
]

#: A FÁJLONKÉNTI futtatás továbbra is szabályos — épp azt írja elő a
#: `run_tests.py` is. Ha ezeket is blokkolnánk, a kapu ellehetetlenítené a
#: helyes munkát, és megkerülnék.
APP_FAJL_ATENGEDENDO = [
    "python3 -m pytest tests/app/test_tray_controller.py -q --basetemp=/tmp/bt",
    "python3 -m pytest tests/app/qml_functional/test_icon_assets.py -q --basetemp=/tmp/bt",
    "python3 -m pytest tests/app/qml_functional/test_x.py::TestA::test_b -q --basetemp=/tmp/bt",
    # más csomagok mappái NEM esnek a tilalom alá: ott nincs QML-motor
    "python3 -m pytest tests/perf tests/index -q --basetemp=/tmp/bt",
    "python3 -m pytest tests/scanner -q --basetemp=/tmp/bt",
    # a listázó alak nem indít motort
    "python3 -m pytest tests/app --collect-only",
    # a parancs SZÖVEGÉBEN előforduló említés nem hívás
    'grep -rn "pytest tests/app/qml_functional" docs/',
]


@pytest.mark.parametrize("cmd", APP_MAPPA_BLOKKOLANDO)
def test_az_app_mappa_blokkolt(cmd):
    indok = kapu.blokkolando(cmd)
    assert indok is not None, cmd
    assert "MAPPA" in indok, f"a basetemp-ágra esett, nem a mappa-ágra: {indok}"


@pytest.mark.parametrize("cmd", APP_FAJL_ATENGEDENDO)
def test_a_fajlonkenti_futtatas_atmegy(cmd):
    assert kapu.blokkolando(cmd) is None, cmd


def test_a_mappa_uzenete_megnevezi_a_MERT_karot(monkeypatch, capsys):
    """A kapu mondja meg, MIÉRT tilos — különben a következő kör
    megkerüli, ahogy a #1649-es szöveges szabályt is megkerültük."""
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_input": {
                        "command": "pytest tests/app/qml_functional --basetemp=/tmp/bt"
                    }
                }
            )
        ),
    )
    assert kapu.main() == 2
    hiba = capsys.readouterr().err
    assert "3,18 GiB" in hiba or "3.18 GiB" in hiba
    assert "ÚJRA KELL" in hiba.upper()
    assert "fájlonként" in hiba.lower()
