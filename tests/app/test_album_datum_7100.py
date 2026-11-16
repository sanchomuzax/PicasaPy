"""#7100: az Add to Album ▸ New Album... ablak dátuma a kijelölés első képének
ideje MÍNUSZ egy másodperc (az eredeti `0x0056c5a0` almenü New Album ága).

Az Áthelyezés új mappába ablak ennek a párja (#7020): ott +1 mp, itt -1 mp.
A számítás az `ujmappa_datum.js`-ben él; itt QJSEngine-nel próbáljuk.

Amit ez a fájl NEM állít: a menüből megnyitott ablak tényleges dátumát; azt a
`tests/app/qml_functional/test_hozzaadas_albumhoz_almenu_7100.py` olvassa
vissza valódi menükattintás után.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtQml import QJSEngine

_JS = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "ujmappa_datum.js"
).read_text(encoding="utf-8")


@pytest.fixture
def motor(qt_app):
    """Az `ujmappa_datum.js` egy JS-motorban (a `qt_app` kell: `QCoreApplication`
    nélkül a `QJSEngine` leáll)."""
    engine = QJSEngine()
    forras = _JS.replace(".pragma library", "")
    kimenet = engine.evaluate(
        "(function () {\n" + forras
        + "\nreturn {albumDatum: albumDatum, kepNapja: kepNapja}\n})()"
    )
    assert not kimenet.isError(), kimenet.toString()
    yield kimenet
    del kimenet, engine


def _datum(motor, szoveg) -> str:
    eredmeny = motor.property("albumDatum").call([szoveg])
    assert not eredmeny.isError(), eredmeny.toString()
    return eredmeny.toString()


def test_delutani_kep_a_sajat_napjat_adja(motor):
    assert _datum(motor, "2019-07-04T10:20:30") == "2019-07-04"


def test_ejfelkor_keszult_kep_az_elozo_napot_adja(motor):
    """A -1 másodperc éjfélkor készült képnél napot vált (az eredeti viselkedés)."""
    assert _datum(motor, "2025-05-01T00:00:00") == "2025-04-30"
    assert _datum(motor, "2025-01-01T00:00:00") == "2024-12-31"


def test_egy_masodperccel_ejfel_utani_kep_meg_ugyanazon_a_napon_marad(motor):
    assert _datum(motor, "2025-05-01T00:00:01") == "2025-05-01"


def test_szokonap_es_honapvaltas(motor):
    assert _datum(motor, "2024-03-01T00:00:00") == "2024-02-29"
    assert _datum(motor, "2023-03-01T00:00:00") == "2023-02-28"
    assert _datum(motor, "2023-05-01T00:00:00") == "2023-04-30"


def test_szokozos_idoalak_is_ertelmezett(motor):
    assert _datum(motor, "2025-05-01 00:00:00") == "2025-04-30"


def test_nincs_datum_ures_marad_a_mai_napra_sem_esik_vissza(motor):
    """Eltérés a mappaablaktól: a hiányzó dátum itt ÜRES, nem a mai nap."""
    assert _datum(motor, "") == ""
    assert _datum(motor, "ez nem dátum") == ""
    assert _datum(motor, "2025-02-30T10:00:00") == ""


def test_az_athelyezes_ablak_plusz_egy_masodperces_szabalya_valtozatlan(motor):
    """A #7020 `kepNapja` (+1 mp) nem változhat."""
    eredmeny = motor.property("kepNapja").call(["2021-12-31T23:59:59"])
    assert eredmeny.toString() == "2022-01-01"
