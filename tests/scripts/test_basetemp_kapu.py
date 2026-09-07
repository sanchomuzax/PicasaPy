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


_PLAFON_ELOTAG = (
    "systemd-run --user --scope -q -p MemoryMax=1800M -p MemorySwapMax=0 -- "
)

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
    _PLAFON_ELOTAG + "python3 -m pytest tests/app/test_tray_controller.py --basetemp=/tmp/bt",
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
# ⚠️ #2646 (2026-09-07): a `tests/app` alatti FÁJL-alak azóta CSAK
# memóriaplafon alatt megy át. A régi, plafon nélküli alakok szándékosan
# kerültek át a blokkolandók közé — nem a teszt romlott el, a szabály
# szigorodott: egyetlen ilyen fájl 30 mp alatt 898 → 1401 MiB-ra nőtt, és
# három párhuzamos munkamenet elvitte a gépet (az earlyoom a Claude
# Desktopot lőtte ki helyette).
APP_FAJL_ATENGEDENDO = [
    _PLAFON_ELOTAG + "python3 -m pytest tests/app/test_tray_controller.py -q --basetemp=/tmp/bt",
    _PLAFON_ELOTAG + "python3 -m pytest tests/app/qml_functional/test_icon_assets.py -q --basetemp=/tmp/bt",
    _PLAFON_ELOTAG + "python3 -m pytest tests/app/qml_functional/test_x.py::TestA::test_b -q --basetemp=/tmp/bt",
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


# --- #2646: memóriaplafon a `tests/app` alatti pytesthez ------------------
#
# 2026-09-07 08:48: az earlyoom a Claude Desktop rendererét lőtte ki
# (VmRSS 3579 MiB) egy 1031 MiB-os QML-teszt HELYETT — az earlyoom a
# legnagyobb RSS-t öli, tehát az áldozat strukturálisan sosem a tettes. A
# kiváltó EGYETLEN, önmagában legitim fájl volt, ami 30 másodperc alatt
# 898 → 1401 MiB-ra nőtt. Sem ez a kapu (mappa-alakot néz), sem a foglalási
# korlát (#2532, csak teljes futásokra) nem foghatta meg.

_PLAFON = ("systemd-run --user --scope -q "
           "-p MemoryMax=1800M -p MemorySwapMax=0 -- ")


def test_egyetlen_app_fajl_plafon_nelkul_blokkol():
    """Ez az az alak, ami 09-07-én elvitte a gépet."""
    cmd = "python3 -m pytest tests/app/qml_functional/test_keptalca_455.py -q --basetemp=/tmp/bt"
    assert "MEMÓRIAPLAFON" in (kapu.blokkolando(cmd) or "")


def test_plafonnal_atmegy():
    cmd = _PLAFON + "python3 -m pytest tests/app/qml_functional/test_x.py -q --basetemp=/tmp/bt"
    assert kapu.blokkolando(cmd) is None


def test_a_plafon_NEM_nyeli_el_a_basetemp_ellenorzest():
    """A burkoló mögött is látni kell a pytestet.

    Ellenpróba: ha a `_fej` nem lépné át a `systemd-run` kapcsolóit, a kapu
    a burkolót látná fejnek, nem ismerné fel a pytestet, és a `--basetemp`
    hiánya NÉMÁN átmenne — épp a jó szándékú, plafont használó hívásokon.
    """
    cmd = _PLAFON + "python3 -m pytest tests/app/qml_functional/test_x.py -q"
    assert "basetemp" in (kapu.blokkolando(cmd) or "")


def test_a_plafon_nem_kell_az_app_on_KIVUL():
    """A memóriaéhség a QML-motoré — ne büntessük a többi tesztet."""
    cmd = "python3 -m pytest tests/ini/test_roundtrip.py -q --basetemp=/tmp/bt"
    assert kapu.blokkolando(cmd) is None


def test_a_felemas_plafon_nem_szamit_plafonnak():
    """`systemd-run` MemoryMax nélkül nem korlátoz semmit."""
    cmd = ("systemd-run --user --scope -q -- python3 -m pytest "
           "tests/app/qml_functional/test_x.py -q --basetemp=/tmp/bt")
    assert "MEMÓRIAPLAFON" in (kapu.blokkolando(cmd) or "")


def test_az_uzenet_megnevezi_a_mert_karot(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {
        "command": "pytest tests/app/qml_functional/test_x.py --basetemp=/tmp/bt"}})))
    assert kapu.main() == 2
    hiba = capsys.readouterr().err
    assert "earlyoom" in hiba
    assert "MemoryMax" in hiba, "a kapu nem mondja meg, HOGYAN indítsa helyesen"
