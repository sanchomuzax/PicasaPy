"""#1572 — a védtelen QML-kötések őrének tesztjei.

A hibaosztály: egy `bool`/`int`/`real` típusú property-be **közvetlenül**
beadott vezérlő-tulajdonság. Ha a tulajdonság nincs meg a vezérlőn — és a
QML-próbák nagy része STUB-vezérlővel fut, amin a frissen bevezetett
property még nincs rajta —, a kifejezés `undefined`, a QML pedig
`Unable to assign [undefined] to bool` szkripthibát dob. A #1260 őre ezt a
fixture-életciklusban bukásnak veszi, méghozzá olyan tesztfájlokon is,
amelyeknek a változtatáshoz semmi közük.

Az őr értéke KÉT dolgon áll vagy bukik, és mindkettőt a kimenetre kell
állítani, nem arra, hogy „lefut hiba nélkül":

1. **Van foga**: a védtelen kötést megtalálja — a `? :` és a `&&` alakban is.
2. **Nem kiabál hiába**: ahol a `!== undefined` őr ott van, vagy ahol a
   kifejezés úgyis logikai/szám eredményt ad (`=== true`, `> 0`, `!x`,
   szorzás), ott HALLGAT. A hamis riasztás itt drágább, mint a kihagyás:
   egy zajos őrt a következő kör kikapcsol.

Külön eset az ALSÓ KORLÁT (`also_korlat_hibai`): egy számoló őr üres
halmazon is zöld, tehát semmit nem őriz. Ha nincs QML-fájl, nincs
regisztrált vezérlő, vagy egyetlen őrzött vezérlő-hivatkozást sem talál, a
szkript 2-es kóddal áll el.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import qml_undefined_or as guard  # noqa: E402

APPLICATION_PY = """\
def main():
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("compactController", compact)
"""


def _fa(tmp_path: Path, qml: str, *, nev: str = "Proba.qml") -> Path:
    """Minta-forrásfa: egy `application.py` és egy QML-fájl."""
    gyoker = tmp_path / "app"
    (gyoker / "qml").mkdir(parents=True)
    (gyoker / "application.py").write_text(APPLICATION_PY, encoding="utf-8")
    (gyoker / "qml" / nev).write_text(qml, encoding="utf-8")
    return gyoker


def _kulcsok(gyoker: Path) -> set[str]:
    return {talalat.kulcs for talalat in guard.elemez(gyoker).vedtelenek}


def _item(torzs: str) -> str:
    return "import QtQuick\n\nItem {\n" + torzs + "\n}\n"


# -- 1. van foga -----------------------------------------------------------


def test_a_ternaris_vedtelen_kotest_megtalalja(tmp_path: Path) -> None:
    """`ctl ? ctl.x : 0` — a hiányzó `x` `undefined`-ot ad."""
    gyoker = _fa(
        tmp_path,
        _item("    readonly property int n: controller ? controller.clipCount : 0"),
    )
    assert _kulcsok(gyoker) == {"qml/Proba.qml::n::controller.clipCount"}


def test_az_es_alaku_vedtelen_kotest_megtalalja(tmp_path: Path) -> None:
    """`ctl && ctl.x` — ha `x` hiányzik, az `&&` eredménye `undefined`."""
    gyoker = _fa(
        tmp_path,
        _item("    readonly property bool b: controller && controller.filterActive"),
    )
    assert _kulcsok(gyoker) == {"qml/Proba.qml::b::controller.filterActive"}


def test_a_beepitett_bool_tulajdonsagot_is_nezi(tmp_path: Path) -> None:
    """A `visible:` típusa `bool`, akkor is, ha nincs `property` kulcsszó."""
    gyoker = _fa(
        tmp_path,
        _item("    visible: controller ? controller.searchActive : false"),
    )
    assert _kulcsok(gyoker) == {"qml/Proba.qml::visible::controller.searchActive"}


def test_az_alias_vezerlot_is_koveti(tmp_path: Path) -> None:
    """`readonly property var ctl: controller` — a `ctl.x` is vezérlő-tag."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    readonly property var ctl: controller\n"
            "    readonly property int n: root.ctl ? root.ctl.heldCount : 0"
        ),
    )
    assert _kulcsok(gyoker) == {"qml/Proba.qml::n::root.ctl.heldCount"}


def test_a_tobbsoros_kotest_is_osszefuzi(tmp_path: Path) -> None:
    """A tördelt ternáris ugyanaz a hiba — a sortörés nem védelem."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    readonly property bool b:\n"
            "        typeof compactController !== \"undefined\" && compactController\n"
            "            ? compactController.running : false"
        ),
    )
    assert _kulcsok(gyoker) == {"qml/Proba.qml::b::compactController.running"}


def test_a_sort_is_megnevezi(tmp_path: Path) -> None:
    """A hibaüzenethez fájl ÉS sor kell, különben nem cselekvésre utasít."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    // egy sor tölteléknek\n"
            "    readonly property int n: controller ? controller.clipCount : 0"
        ),
    )
    (talalat,) = guard.elemez(gyoker).vedtelenek
    assert talalat.sor == 5
    assert talalat.fajl == "qml/Proba.qml"


# -- 2. nem kiabál hiába ---------------------------------------------------


def test_a_vedett_alak_nem_ad_riasztast(tmp_path: Path) -> None:
    """A `!== undefined` őrrel ellátott kötés a KÍVÁNT alak."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    readonly property bool b: (controller"
            " && controller.filterActive !== undefined)\n"
            "        ? controller.filterActive === true : false"
        ),
    )
    assert _kulcsok(gyoker) == set()


def test_az_osszehasonlitas_nem_adhat_undefined_ot(tmp_path: Path) -> None:
    """`ctl.x > 0` — hiányzó `x` mellett is LOGIKAI érték, nem `undefined`."""
    gyoker = _fa(
        tmp_path,
        _item("    readonly property bool b: controller ? controller.heldCount > 0 : false"),
    )
    assert _kulcsok(gyoker) == set()


def test_a_tagadas_nem_adhat_undefined_ot(tmp_path: Path) -> None:
    """`!ctl.x` — a `!undefined` `true`, tehát logikai érték."""
    gyoker = _fa(
        tmp_path,
        _item("    visible: controller ? !controller.searchActive : true"),
    )
    assert _kulcsok(gyoker) == set()


def test_a_szamtani_muvelet_nem_adhat_undefined_ot(tmp_path: Path) -> None:
    """`ctl.x * 2` — a `undefined * 2` `NaN`, azt a `real` elnyeli."""
    gyoker = _fa(
        tmp_path,
        _item("    width: controller ? controller.unit * 2 : 0"),
    )
    assert _kulcsok(gyoker) == set()


def test_a_fuggvenyhivas_nem_ez_a_hibaosztaly(tmp_path: Path) -> None:
    """A hiányzó METÓDUS `TypeError`-t ad, nem `undefined` értékadást."""
    gyoker = _fa(
        tmp_path,
        _item('    visible: controller ? controller.isSuppressed("x") : false'),
    )
    assert _kulcsok(gyoker) == set()


def test_a_felteteli_reszben_allo_tag_nem_ertekadas(tmp_path: Path) -> None:
    """A ternáris FELTÉTELE nem kerül a property-be, tehát nem hibázhat."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    readonly property bool b: (controller && controller.caps)\n"
            "        ? controller.caps.overlay === true : false"
        ),
    )
    assert _kulcsok(gyoker) == set()


def test_a_nem_vezerlo_objektumra_nem_riaszt(tmp_path: Path) -> None:
    """`parent ? parent.width : 0` — a `parent` QML-elem, nem stubolható vezérlő."""
    gyoker = _fa(tmp_path, _item("    width: parent ? parent.width : 0"))
    assert _kulcsok(gyoker) == set()


def test_a_var_tipusu_property_elviseli_az_undefined_ot(tmp_path: Path) -> None:
    """`var`/`string` célra az `undefined` nem szkripthiba — ne riasszunk."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    readonly property var m: controller ? controller.nodes : null\n"
            "    readonly property string s: controller ? controller.name : \"\""
        ),
    )
    assert _kulcsok(gyoker) == set()


def test_a_kikommentelt_kotes_nem_kotes(tmp_path: Path) -> None:
    """A komment nem futó kód — se sorkomment, se blokk."""
    gyoker = _fa(
        tmp_path,
        _item(
            "    // visible: controller ? controller.searchActive : false\n"
            "    /* width: controller ? controller.unit : 0 */"
        ),
    )
    assert _kulcsok(gyoker) == set()


# -- 3. alsó korlát: az üres halmazon zöld őr semmit nem őriz --------------


def test_ures_qml_fa_eseten_alsokorlat_hiba(tmp_path: Path) -> None:
    """Ha nincs QML-fájl, a szkript nem mondhatja azt, hogy „rendben"."""
    gyoker = tmp_path / "app"
    (gyoker / "qml").mkdir(parents=True)
    (gyoker / "application.py").write_text(APPLICATION_PY, encoding="utf-8")
    hibak = guard.also_korlat_hibai(guard.elemez(gyoker))
    assert any("QML-fájl" in hiba for hiba in hibak)


def test_regisztracio_nelkul_alsokorlat_hiba(tmp_path: Path) -> None:
    """Vezérlő-nevek nélkül a vizsgálat üres — ez hiba, nem siker."""
    gyoker = tmp_path / "app"
    (gyoker / "qml").mkdir(parents=True)
    (gyoker / "application.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (gyoker / "qml" / "Proba.qml").write_text(
        _item("    visible: true"), encoding="utf-8"
    )
    hibak = guard.also_korlat_hibai(guard.elemez(gyoker))
    assert any("vezérlő" in hiba for hiba in hibak)


def test_egyetlen_orzott_hivatkozas_nelkul_alsokorlat_hiba(tmp_path: Path) -> None:
    """Ha a MINTA nem illeszkedik sehol, az őrnek nincs foga — 2-es kód."""
    gyoker = _fa(tmp_path, _item("    visible: true"))
    hibak = guard.also_korlat_hibai(guard.elemez(gyoker))
    assert any("őrzött" in hiba for hiba in hibak)


def test_a_teljes_fan_nincs_alsokorlat_hiba() -> None:
    """A VALÓDI fán mindhárom számnak pozitívnak kell lennie."""
    elemzes = guard.elemez(_REPO_ROOT / "src" / "picasapy" / "app")
    assert guard.also_korlat_hibai(elemzes) == []
    assert elemzes.qml_fajlok > 100
    assert elemzes.orzott_hivatkozasok > 0


# -- 4. az alapállapot csak rövidülhet -------------------------------------


def test_a_baseline_tetelhez_indoklas_kell(tmp_path: Path) -> None:
    """Indoklás nélküli sor HIBA — a néma engedély pontosan az, ami nem kell."""
    ut = tmp_path / "baseline.txt"
    ut.write_text("qml/Proba.qml::n::controller.clipCount\n", encoding="utf-8")
    with pytest.raises(ValueError, match="INDOKLÁS"):
        guard.baseline_olvas(ut)


def test_a_baseline_nem_hizhat_a_plafon_folé(tmp_path: Path, monkeypatch) -> None:
    """A plafon nélkül az őrt egy sor beírásával meg lehetne kerülni."""
    monkeypatch.setattr(guard, "MAX_BASELINE_ENTRIES", 0)
    ut = tmp_path / "baseline.txt"
    ut.write_text("qml/Proba.qml::n::controller.clipCount  #1", encoding="utf-8")
    with pytest.raises(ValueError, match="felső korlát"):
        guard.baseline_olvas(ut)


def test_a_valodi_fa_atmegy_az_ellenorzesen() -> None:
    """A main-nek zöldnek kell lennie — ez a CI-lépés maga."""
    assert guard.main([]) == 0
