"""#1476 — a felületről elérhetetlen vezérlő-képességek őrének tesztjei.

Az őr értéke három dolgon áll vagy bukik, és MINDHÁRMAT a kimenetre kell
állítani, nem arra, hogy „lefut hiba nélkül":

1. **Van foga**: a bekötetlen tagot megtalálja — akkor is, ha ugyanaz a
   tagnév EGY MÁSIK vezérlőn be van kötve. Ez a #1476 lényege: a naiv
   ``.tagnév`` keresés ilyenkor élőnek látja a halottat.
2. **Nem kiabál hiába**: ahol VAN bekötés — közvetlenül vagy aliason át —,
   ott hallgat. A hamis riasztástól a csapat kikapcsolja az őrt.
3. **Nem üresen zöld**: ha a vizsgálat maga romlik el (rossz útvonal,
   megváltozott mappaszerkezet), akkor NEM „hibátlant" jelent, hanem megáll.
   Ez a hibafajta 2026-08-25-én háromszor harapott meg minket.

A valódi fára tett állítások szándékosan **alsó korlátok** (…nál több
fájl, …nál több tag), nem pontos számok: a pontos szám holnap avul, a
„semmit nem néztem meg" viszont mindig hiba.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import kepesseg_or as or_  # noqa: E402

VALODI_APP = _REPO_ROOT / "src" / "picasapy" / "app"
VALODI_BASELINE = _REPO_ROOT / "scripts" / "kepesseg_or_baseline.txt"
VALODI_LELTAR = _REPO_ROOT / "docs" / "specs" / "lanc-szakadasok-leltar.md"

VEZERLO = """\
from PySide6.QtCore import Property, QObject, Slot


class Vezerlo(QObject):
    @Slot()
    def bekotott(self):
        pass

    @Slot()
    def bekotetlen(self):
        pass
"""

ALKALMAZAS = """\
def main(engine):
    controller = Vezerlo()
    engine.rootContext().setContextProperty("controller", controller)
"""


def _fa(
    tmp_path: Path,
    *,
    vezerlok: dict[str, str] | None = None,
    alkalmazas: str = ALKALMAZAS,
    qml: dict[str, str] | None = None,
) -> Path:
    """Minta-forrásfa: `application.py`, vezérlő-fájlok és QML-fájlok."""
    gyoker = tmp_path / "app"
    (gyoker / "qml").mkdir(parents=True)
    (gyoker / "application.py").write_text(alkalmazas, encoding="utf-8")
    for nev, tartalom in (vezerlok or {"vezerlo.py": VEZERLO}).items():
        (gyoker / nev).write_text(tartalom, encoding="utf-8")
    for nev, tartalom in (qml or {"Main.qml": "Item {}"}).items():
        (gyoker / "qml" / nev).write_text(tartalom, encoding="utf-8")
    return gyoker


def _szakadas_kulcsok(gyoker: Path) -> set[str]:
    return {tag.kulcs for tag in or_.elemez(gyoker).szakadasok}


@pytest.fixture(scope="module")
def valodi() -> or_.Elemzes:
    """A VALÓDI fa egyszeri mérése — a modul összes valós állítása erre épül."""
    return or_.elemez(VALODI_APP)


# -- 1. van foga -----------------------------------------------------------


def test_a_bekotetlen_tagot_megtalalja(tmp_path: Path) -> None:
    """Se QML, se alias — az őrnek jeleznie KELL."""
    gyoker = _fa(tmp_path, qml={"Main.qml": "Item { Text { text: controller.bekotott } }"})
    assert _szakadas_kulcsok(gyoker) == {"controller.bekotetlen"}


def test_az_orokolt_mixin_tagot_is_vegignezi(tmp_path: Path) -> None:
    """A `controller` tagjainak fele mixinekből jön — azok is a felületé."""
    vezerlo = """\
from PySide6.QtCore import QObject, Slot


class Mixin:
    @Slot()
    def mixinTag(self):
        pass


class Vezerlo(Mixin, QObject):
    @Slot()
    def sajatTag(self):
        pass
"""
    gyoker = _fa(tmp_path, vezerlok={"vezerlo.py": vezerlo})
    assert _szakadas_kulcsok(gyoker) == {"controller.mixinTag", "controller.sajatTag"}


def test_a_kikommentelt_hivatkozas_nem_bekotes(tmp_path: Path) -> None:
    """A `// controller.bekotetlen()` sor nem kapcsol össze semmit."""
    gyoker = _fa(
        tmp_path,
        qml={"Main.qml": "Item {\n // controller.bekotetlen()\n /* controller.bekotott */\n}"},
    )
    assert _szakadas_kulcsok(gyoker) == {"controller.bekotott", "controller.bekotetlen"}


def test_a_soha_nem_regisztralt_vezerlot_kulon_jelenti(tmp_path: Path) -> None:
    """A #1472 alakja: kész vezérlő, ami soha nem példányosul."""
    masik = VEZERLO.replace("class Vezerlo", "class Nyomtato")
    gyoker = _fa(tmp_path, vezerlok={"vezerlo.py": VEZERLO, "nyomtato.py": masik})
    arvak = {arva.nev for arva in or_.elemez(gyoker).arva_osztalyok}
    assert arvak == {"Nyomtato"}


# -- 2. a MINŐSÍTETT keresés: a #1476 magja --------------------------------


KET_VEZERLO = """\
from PySide6.QtCore import QObject, Slot


class Elso(QObject):
    @Slot()
    def cancelScan(self):
        pass


class Masodik(QObject):
    @Slot()
    def cancelScan(self):
        pass
"""

KET_REGISZTRACIO = """\
def main(engine):
    elso = Elso()
    masodik = Masodik()
    engine.rootContext().setContextProperty("elsoController", elso)
    engine.rootContext().setContextProperty("masodikController", masodik)
"""


def test_az_azonos_nevu_tagot_nem_keveri_ossze(tmp_path: Path) -> None:
    """Ez a jegy magja: a naiv `.cancelScan` keresés MINDKETTŐT élőnek látná.

    A valóságban ez a `dedupController.cancelScan` és a
    `faceScanController.cancelScan` — a #1476 szerzője maga is beleesett.
    """
    gyoker = _fa(
        tmp_path,
        vezerlok={"vezerlok.py": KET_VEZERLO},
        alkalmazas=KET_REGISZTRACIO,
        qml={"Main.qml": "Item { onClicked: elsoController.cancelScan() }"},
    )
    assert _szakadas_kulcsok(gyoker) == {"masodikController.cancelScan"}


def test_a_mas_objektumon_levo_alias_sem_kevered(tmp_path: Path) -> None:
    """Az alias sem hordozhatja át az egyik vezérlő életét a másikra."""
    gyoker = _fa(
        tmp_path,
        vezerlok={"vezerlok.py": KET_VEZERLO},
        alkalmazas=KET_REGISZTRACIO,
        qml={
            "Main.qml": (
                "Item {\n readonly property var ctl: elsoController\n"
                " onClicked: ctl.cancelScan()\n}"
            )
        },
    )
    assert _szakadas_kulcsok(gyoker) == {"masodikController.cancelScan"}


# -- 3. nem kiabál hiába ---------------------------------------------------


@pytest.mark.parametrize(
    ("cimke", "qml"),
    [
        ("közvetlen", "Item { onClicked: controller.bekotetlen() }"),
        (
            "alias",
            "Item {\n readonly property var ctl: controller\n"
            " onClicked: ctl.bekotetlen()\n}",
        ),
        (
            "null-őrös alias",
            'Item {\n readonly property var ctl:\n'
            '  typeof controller !== "undefined" ? controller : null\n'
            " onClicked: ctl.bekotetlen()\n}",
        ),
        (
            "null-őrös alias &&-tel",
            'Item {\n readonly property var ctl:\n'
            '  (typeof controller !== "undefined" && controller)\n'
            "   ? controller : null\n"
            " onClicked: ctl.bekotetlen()\n}",
        ),
        (
            "JS-fájlból",
            None,  # külön kezelve: .js kiterjesztés
        ),
    ],
)
def test_a_bekotott_tagra_hallgat(tmp_path: Path, cimke: str, qml: str | None) -> None:
    """Minden bekötési alakra külön eset — a hamis riasztás itt a rosszabb hiba."""
    if qml is None:
        fajlok = {
            "Main.qml": "Item {}",
            "seged.js": "function f() { controller.bekotetlen() }",
        }
    else:
        fajlok = {"Main.qml": qml}
    gyoker = _fa(tmp_path, qml=fajlok)
    assert "controller.bekotetlen" not in _szakadas_kulcsok(gyoker), cimke


def test_a_tranzitiv_alias_is_bekotes(tmp_path: Path) -> None:
    """A szülő továbbadja a vezérlőt, a gyerek azt hívja — ez ÉLŐ lánc.

    A valóságban: `Main.qml` → `FolderPane.hierarchyController` →
    `FolderHierarchyView.hierarchy` → `root.hierarchy.expandAll()`.
    """
    gyoker = _fa(
        tmp_path,
        qml={
            "Main.qml": "Item { Panel { id: p; hidCtl: controller } }",
            "Panel.qml": "Item {\n property var hidCtl: null\n"
            " Nezet { atadott: p.hidCtl }\n}",
            "Nezet.qml": "Item {\n property var atadott: null\n"
            " onClicked: atadott.bekotetlen()\n}",
        },
    )
    assert "controller.bekotetlen" not in _szakadas_kulcsok(gyoker)


def test_az_ertekkotes_nem_alias(tmp_path: Path) -> None:
    """`enabled: root.ctl !== null` LOGIKAI érték — nem viheti tovább a nevet."""
    gyoker = _fa(
        tmp_path,
        qml={
            "Main.qml": "Item {\n property bool enabled: controller !== null\n}",
            "Masik.qml": "Item { onClicked: enabled.bekotetlen() }",
        },
    )
    assert "controller.bekotetlen" in _szakadas_kulcsok(gyoker)


def test_a_connections_targetje_nem_alias(tmp_path: Path) -> None:
    """A `target` a valódi fában 12 objektumra mutat; aliasként hamis életet adna."""
    gyoker = _fa(
        tmp_path,
        qml={
            "Main.qml": "Item { Connections { target: controller } }",
            "Mezo.qml": "Item {\n property var target: null\n"
            " onClicked: target.bekotetlen()\n}",
        },
    )
    assert "controller.bekotetlen" in _szakadas_kulcsok(gyoker)


def test_az_url_ketto_perjele_nem_komment(tmp_path: Path) -> None:
    """Az `image://` a sor közepén nem kezdhet kommentet.

    A naiv `//` vágás a sor MARADÉKÁT — benne a hivatkozással — elnyelné,
    és az őr hamis szakadást jelentene.
    """
    gyoker = _fa(
        tmp_path,
        qml={"Main.qml": 'Item { Image { source: "image://x/" + controller.bekotetlen } }'},
    )
    assert "controller.bekotetlen" not in _szakadas_kulcsok(gyoker)


def test_a_belso_slotot_nem_keri_szamon(tmp_path: Path) -> None:
    """A `_`-sal kezdődő slot jelzésfogadó, nem felületi tag."""
    vezerlo = VEZERLO.replace("def bekotetlen", "def _on_valami_tortent")
    gyoker = _fa(tmp_path, vezerlok={"vezerlo.py": vezerlo})
    assert _szakadas_kulcsok(gyoker) == {"controller.bekotott"}


# -- 4. alsó korlát: az őr nem lehet üresen zöld ---------------------------


def test_ures_qml_mappa_eseten_megall(tmp_path: Path) -> None:
    """Nulla QML-fájl mellett a „0 szakadás" HAZUGSÁG, nem siker."""
    gyoker = _fa(tmp_path)
    (gyoker / "qml" / "Main.qml").unlink()
    hibak = or_.also_korlat_hibai(or_.elemez(gyoker))
    assert any("QML" in hiba for hiba in hibak)


def test_regisztracio_nelkul_megall(tmp_path: Path) -> None:
    """Ha a `setContextProperty` mintája elavul, az őr NEM hallgathat."""
    gyoker = _fa(tmp_path, alkalmazas="def main(engine):\n    pass\n")
    hibak = or_.also_korlat_hibai(or_.elemez(gyoker))
    assert any("setContextProperty" in hiba for hiba in hibak)


def test_elo_hivatkozas_nelkul_megall(tmp_path: Path) -> None:
    """Ha a KERESÉS romlik el, minden tag halottnak látszik — ez is hiba."""
    gyoker = _fa(tmp_path, qml={"Main.qml": "Item {}"})
    hibak = or_.also_korlat_hibai(or_.elemez(gyoker))
    assert any("ÉLŐ" in hiba for hiba in hibak)


def test_feloldatlan_regisztracio_hiba(tmp_path: Path) -> None:
    """Amit nem tudok osztályra visszavezetni, azt NÉMÁN nem hagyhatom ki."""
    gyoker = _fa(
        tmp_path,
        alkalmazas=(
            "def main(engine):\n"
            "    controller = Vezerlo()\n"
            '    engine.rootContext().setContextProperty("controller", controller)\n'
            '    engine.rootContext().setContextProperty("ismeretlen", gyar()[0])\n'
        ),
        qml={"Main.qml": "Item { onClicked: controller.bekotott() }"},
    )
    hibak = or_.also_korlat_hibai(or_.elemez(gyoker))
    assert any("ismeretlen" in hiba for hiba in hibak)


def test_a_valodi_fan_nincs_also_korlat_hiba(valodi: or_.Elemzes) -> None:
    assert or_.also_korlat_hibai(valodi) == []


def test_a_valodi_fan_erdemi_mennyiseget_nez_at(valodi: or_.Elemzes) -> None:
    """Alsó korlátok — pontos szám helyett, mert az holnapra avul."""
    assert valodi.py_fajlok >= 50
    assert valodi.qml_fajlok >= 100
    assert len(valodi.kontextusok) >= 15
    assert len(valodi.tagok) >= 300
    assert len(valodi.hivatkozott) >= 200
    assert len(valodi.aliasok) >= 5


# -- 5. pozitív kontroll a VALÓDI fán --------------------------------------


@pytest.mark.parametrize(
    ("kontextus", "tag", "miert"),
    [
        ("controller", "toggleShowHidden", "menüpont hívja közvetlenül"),
        ("controller", "toggleDarkTheme", "menüpont hívja közvetlenül"),
        ("controller", "photos", "a rács modellje"),
        ("controller", "statusText", "aliason át: tray.ctl.statusText"),
        ("startupStatus", "statusText", "aliason át: statusBridge.statusText"),
        ("editController", "applyEffect", "a szerkesztő gombjai hívják"),
        ("dedupController", "cancelScan", "a másolatkereső párbeszéd Mégse gombja"),
        ("fileOpsController", "movePhotos", "a fájlműveleti párbeszéd"),
        ("folderHierarchyController", "expandAll", "kétlépcsős aliason át"),
        ("importSourceController", "toggleStar", "az importáló nézet csillaga"),
    ],
)
def test_pozitiv_kontroll_a_helyes_mintat_is_megtalalja(
    valodi: or_.Elemzes, kontextus: str, tag: str, miert: str
) -> None:
    """Az őr a HELYES mintából is találjon — különben üresen jelentene hibátlant."""
    assert valodi.elo(kontextus, tag), f"{kontextus}.{tag} élő kell legyen ({miert})"


@pytest.mark.parametrize(
    ("kontextus", "tag"),
    [("dedupController", "cancelScan"), ("importSourceController", "toggleStar")],
)
def test_az_ikertag_elo_parja_valoban_elo(valodi: or_.Elemzes, kontextus: str, tag: str) -> None:
    assert valodi.elo(kontextus, tag)


@pytest.mark.parametrize(
    ("kontextus", "tag", "mit_lat_a_naiv_kereses"),
    [
        ("faceScanController", "cancelScan", "a dedupController.cancelScan hívásait"),
        ("editController", "revision", "a controller.photos.revision kötéseket"),
    ],
)
def test_a_naiv_kereses_csapdaja_a_valodi_fan(
    valodi: or_.Elemzes, kontextus: str, tag: str, mit_lat_a_naiv_kereses: str
) -> None:
    """Ezek a tagok HALOTTAK, miközben a puszta `.tagnév` bőven talál rájuk."""
    assert not valodi.elo(kontextus, tag), (
        f"{kontextus}.{tag} ma bekötött — ha ez szándékos, a baseline sorát törölni kell"
    )


# -- 6. diszkriminációs próba: elrontva BUKNIA kell ------------------------


def _valodi_masolat(tmp_path: Path) -> Path:
    """A valódi app-fa másolata, hogy mutálni lehessen (a fát nem bántjuk)."""
    cel = tmp_path / "app"
    shutil.copytree(VALODI_APP, cel)
    return cel


def test_rossz_kontextusnevvel_a_tagok_halottnak_latszanak(tmp_path: Path) -> None:
    """Ha az objektum MÁS néven kerül a kontextusba, a QML nem éri el.

    Ez a próba mutatja meg, hogy az őr tényleg a MINŐSÍTETT alakot nézi: a
    tagnevek változatlanok, csak a kontextus-név más — a naiv `.tagnév`
    kereső ettől meg se rezzenne.
    """
    gyoker = _valodi_masolat(tmp_path)
    alkalmazas = gyoker / "application.py"
    alkalmazas.write_text(
        alkalmazas.read_text(encoding="utf-8").replace(
            'setContextProperty("editController"', 'setContextProperty("szerkesztoVezerlo"'
        ),
        encoding="utf-8",
    )
    eredeti = or_.elemez(VALODI_APP)
    romlott = or_.elemez(gyoker)
    eredeti_edit = {tag.kulcs for tag in eredeti.szakadasok if tag.kontextus == "editController"}
    romlott_edit = {
        tag.kulcs for tag in romlott.szakadasok if tag.kontextus == "szerkesztoVezerlo"
    }
    assert len(romlott_edit) > len(eredeti_edit) + 10, (
        "a kontextus-név elrontásától a szerkesztő MINDEN tagjának el kell szakadnia"
    )


def test_a_bekotes_kivetelekor_uj_szakadas_keletkezik(tmp_path: Path) -> None:
    """Egy meglévő bekötés ideiglenes kivétele — az őr foga a valódi fán."""
    gyoker = _valodi_masolat(tmp_path)
    menu = gyoker / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
    menu.write_text(
        menu.read_text(encoding="utf-8").replace("toggleShowHidden", "toggleShowHiddenXX"),
        encoding="utf-8",
    )
    assert "controller.toggleShowHidden" in _szakadas_kulcsok(gyoker)


# -- 7. az alapállapot-lista fegyelme --------------------------------------


def test_az_indoklas_nelkuli_sor_hiba(tmp_path: Path) -> None:
    """A néma engedély pontosan az, ami a listára nem kerülhet."""
    lista = tmp_path / "alap.txt"
    lista.write_text("controller.valami\n", encoding="utf-8")
    with pytest.raises(ValueError):
        or_.baseline_olvas(lista)


def test_a_lista_minden_sora_indokolt() -> None:
    baseline = or_.baseline_olvas(VALODI_BASELINE)
    assert all(indoklas.strip() for indoklas in baseline.values())
    assert baseline, "üres alapállapot: az őr ilyenkor mindent újnak látna"


def test_a_valodi_lista_naprakesz(valodi: or_.Elemzes) -> None:
    """Se ÚJ szakadás, se ELAVULT listatétel — ez a CI-lépés lényege."""
    baseline = or_.baseline_olvas(VALODI_BASELINE)
    ujak, elavultak = or_.elteresek(valodi, baseline)
    assert ujak == [], "új, felületről elérhetetlen vezérlő-tag"
    assert elavultak == [], "a lista elavult tételt konzervál — a sorát törölni kell"


def test_az_osztaly_lista_naprakesz(valodi: or_.Elemzes) -> None:
    baseline = or_.baseline_osztalyok_olvas(VALODI_BASELINE)
    maiak = {arva.nev for arva in valodi.arva_osztalyok}
    assert maiak - set(baseline) == set()
    assert set(baseline) - maiak == set()


def test_a_lista_nem_hizhat_eszrevetlenul() -> None:
    """A plafon teszi tudatos lépéssé az új kivételt (ld. #1003 ugyanezt)."""
    assert len(or_.baseline_olvas(VALODI_BASELINE)) <= or_.MAX_BASELINE_ENTRIES
    assert len(or_.baseline_osztalyok_olvas(VALODI_BASELINE)) <= or_.MAX_OSZTALY_ENTRIES


def test_az_elteres_mindket_iranyt_jelzi() -> None:
    elemzes = or_.Elemzes(
        szakadasok=[or_.Tag("controller", "uj", "Slot", "v.py", 1)],
    )
    ujak, elavultak = or_.elteresek(elemzes, {"controller.regi": "indok"})
    assert ujak == ["controller.uj"]
    assert elavultak == ["controller.regi"]


# -- 8. a leltár generált, nem kézi pillanatkép ----------------------------


def test_a_leltar_generalt_blokkja_naprakesz(valodi: or_.Elemzes) -> None:
    """A #1476 kikötése: a leltár az őrből álljon elő, ne kézzel.

    Ha ez elhasal: `python scripts/kepesseg_or.py --leltar --ir`.
    """
    baseline = or_.baseline_olvas(VALODI_BASELINE)
    osztalyok = or_.baseline_osztalyok_olvas(VALODI_BASELINE)
    varhato = or_.leltar_tabla(valodi, baseline, osztalyok)
    szoveg = VALODI_LELTAR.read_text(encoding="utf-8")
    assert or_.LELTAR_KEZDET in szoveg and or_.LELTAR_VEGE in szoveg
    jelenlegi = (
        or_.LELTAR_KEZDET + szoveg.split(or_.LELTAR_KEZDET)[1].split(or_.LELTAR_VEGE)[0]
        + or_.LELTAR_VEGE
    )
    assert jelenlegi == varhato


def test_a_leltar_irasa_csak_a_blokkot_csereli(tmp_path: Path) -> None:
    ut = tmp_path / "leltar.md"
    ut.write_text(
        f"eleje\n\n{or_.LELTAR_KEZDET}\nrégi\n{or_.LELTAR_VEGE}\n\nvége\n", encoding="utf-8"
    )
    or_.leltar_ir(ut, f"{or_.LELTAR_KEZDET}\nÚJ\n{or_.LELTAR_VEGE}")
    szoveg = ut.read_text(encoding="utf-8")
    assert "eleje" in szoveg and "vége" in szoveg and "ÚJ" in szoveg
    assert "régi" not in szoveg


# -- 9. a parancssor -------------------------------------------------------


def test_a_parancssor_zold_a_mai_fan() -> None:
    assert or_.main([]) == 0


def test_a_parancssor_hibas_utra_ketes_koddal_all_meg(tmp_path: Path) -> None:
    """Rossz útvonalra NEM „hibátlant" kell jelenteni."""
    assert or_.main(["--app", str(tmp_path / "nincs-ilyen")]) == 2


def test_a_parancssor_uj_szakadasra_bukik(tmp_path: Path) -> None:
    lista = tmp_path / "alap.txt"
    lista.write_text("# üres lista\n", encoding="utf-8")
    assert or_.main(["--baseline", str(lista)]) == 1
