"""#7020: az Áthelyezés új mappába ablak dátuma a kép ideje + 1 másodperc.

Az eredeti Picasa 3.9-ben (#7008) a `0x005e9a42` a `0x004ae0a0`-val lekéri a
kép idejét (OLE-nap), a `0x005e9a47` pedig hozzáad `0xcf50c8` = 1/86400 napot,
azaz pontosan egy másodpercet. A mappadátum ebből a napi rész.

A számítás a `ujmappa_datum.js`-ben él (a `FileOpsDialogs.qml` már a 800 soros
határ fölött van, és ez aritmetika, nem felület). Itt QJSEngine-nel próbáljuk.

Amit ez a fájl NEM állít: a menüből megnyitott ablak tényleges mezőjét; azt a
`tests/app/qml_functional/test_athelyezes_uj_mappaba_datum_7020.py` olvassa
vissza valódi menükattintás után.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtQml import QJSEngine

_JS = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "ujmappa_datum.js"
).read_text(encoding="utf-8")


@pytest.fixture
def motor(qt_app):
    """Az `ujmappa_datum.js` egy JS-motorban.

    ⚠️ A `qt_app` KELL: `QCoreApplication` nélkül a `QJSEngine` leáll
    (a projekt visszatérő csapdája).
    """
    engine = QJSEngine()
    # a `.pragma library` sor a modul-alakhoz kell, a sima kiértékeléshez nem
    forras = _JS.replace(".pragma library", "")
    kimenet = engine.evaluate(
        "(function () {\n" + forras
        + "\nreturn {kepNapja: kepNapja, kezdoDatum: kezdoDatum}\n})()"
    )
    assert not kimenet.isError(), kimenet.toString()
    yield kimenet
    del kimenet, engine


def _nap(motor, szoveg) -> str:
    eredmeny = motor.property("kepNapja").call([szoveg])
    assert not eredmeny.isError(), eredmeny.toString()
    return eredmeny.toString()


def test_kozepnapi_kep_a_sajat_napjat_adja(motor):
    assert _nap(motor, "2019-07-04T10:20:30") == "2019-07-04"


def test_egy_masodperccel_ejfel_elotti_kep_a_kovetkezo_napot_adja(motor):
    """A +1 másodperc éjfél előtt egy másodperccel készült képnél napot vált."""
    assert _nap(motor, "2021-12-31T23:59:59") == "2022-01-01"
    assert _nap(motor, "2024-03-05T23:59:59") == "2024-03-06"


def test_ejfel_elotti_ket_masodperc_meg_ugyanazon_a_napon_marad(motor):
    assert _nap(motor, "2024-03-05T23:59:58") == "2024-03-05"


def test_szokonap_es_honapvaltas(motor):
    assert _nap(motor, "2024-02-28T23:59:59") == "2024-02-29"
    assert _nap(motor, "2024-02-29T23:59:59") == "2024-03-01"
    assert _nap(motor, "2023-02-28T23:59:59") == "2023-03-01"
    assert _nap(motor, "2023-04-30T23:59:59") == "2023-05-01"


def test_nyari_idoszamitas_atmenete_nem_tolja_el_a_napot(motor):
    """Helyi idő helyett naiv számítás: a hiányzó óra sem ront."""
    assert _nap(motor, "2024-03-30T23:59:59") == "2024-03-31"
    assert _nap(motor, "2024-03-31T02:30:00") == "2024-03-31"
    assert _nap(motor, "2024-10-27T02:30:00") == "2024-10-27"


def test_szokozos_alak_es_toredekmasodperc_is_elfogadott(motor):
    assert _nap(motor, "2023-11-04 18:20:11") == "2023-11-04"
    assert _nap(motor, "2023-11-04T23:59:59.500") == "2023-11-05"


def test_csak_datumos_ertek_a_sajat_napja(motor):
    assert _nap(motor, "2024-03-05") == "2024-03-05"


@pytest.mark.parametrize(
    "szoveg",
    ["", "   ", "nem dátum", "2024-13-01T00:00:00", "2023-02-30T10:00:00",
     "2024-03-05T25:00:00", None],
)
def test_hianyzo_vagy_ervenytelen_ido_ures_valaszt_ad(motor, szoveg):
    """Üres válasz: a hívó ilyenkor a mai napra esik vissza (ahogy eddig)."""
    eredmeny = motor.property("kepNapja").call([szoveg])
    assert not eredmeny.isError()
    assert eredmeny.toString() == ""


def _kezdo(motor, szoveg) -> str:
    eredmeny = motor.property("kezdoDatum").call([szoveg])
    assert not eredmeny.isError(), eredmeny.toString()
    return eredmeny.toString()


def test_kezdo_datum_a_kep_napja_ha_van(motor):
    assert _kezdo(motor, "2019-07-04T10:20:30") == "2019-07-04"
    assert _kezdo(motor, "2021-12-31T23:59:59") == "2022-01-01"


@pytest.mark.parametrize("szoveg", ["", "hibás", None])
def test_kezdo_datum_kep_ideje_nelkul_a_mai_nap(motor, szoveg):
    """Dátum nélküli képnél marad a korábbi viselkedés: a mai nap."""
    assert _kezdo(motor, szoveg) == date.today().isoformat()
