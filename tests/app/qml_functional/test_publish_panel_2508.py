"""A `publish` panel MÉRT vezérlői (#2508).

## A mérés

`docs/specs/ajandek-cd-kimenet.md` **13. szakasz**: a `publish.tre` 106
elemneve közül 28 a valódi vezérlő, ebből **21 építendő** (7 online, a
`web_group` a `.tre`-ben `m_hidden`). A koordináták a `respack.yt`
rétegfejléceiből valók, a **1024 × 212**-es vászonhoz.

## Amit ez az őr mér

1. mind a 21 elem MEGVAN, a saját objektumnevén;
2. a helyük és a méretük **képpontra** a mért érték;
3. a feliratok az angol forrásszövegek (a magyar a `.ts`-ben);
4. a `cdname` mező **16 karakterre** korlátoz (a `namelimitext` mondja ki);
5. a `web_group` hét eleme **NINCS** megépítve.

## Amit NEM mér

A LÁTVÁNYT (színek, keretstílus) és a MŰKÖDÉST. Az Ajándék-CD üzemmód
működő vezérlőit (#3503) a `test_ajandek_cd_panel_3503.py`, a bekötését a
`test_ajandek_cd_bekotes_3503.py` méri; a mentés és a feltöltés üzemmódja
nincs bekötve.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

_KEEP_ALIVE: list = []

#: objektumnév → (x, y, szélesség, magasság) — a spec 13.3 táblájából
MERT_GEOMETRIA: dict[str, tuple[int, int, int, int]] = {
    # Ajándék-CD — `presentation_group`
    "publishStep1": (15, 37, 311, 166),
    "publishStep2": (337, 37, 311, 166),
    "publishSelectionText": (55, 43, 251, 18),
    "publishPicSizeText": (35, 169, 137, 18),
    "publishCdNameText": (377, 43, 251, 18),
    "publishLabelCdName": (357, 81, 93, 14),
    "publishCdName": (458, 83, 167, 14),
    "publishNameLimitText": (455, 101, 173, 14),
    "publishLabelOptionBox3": (390, 140, 227, 16),
    "publishLabelOptionBox2": (390, 172, 227, 16),
    "publishOriginInfo": (307, 2, 197, 25),
    # biztonsági mentés — `backup_group`
    "publishBackupRect2": (448, 37, 324, 166),
    "publishLabelBackupName": (148, 134, 108, 16),
    "publishBackupInfo": (420, 2, 197, 25),
    # feltöltés — `replication_group`
    "publishRpOptions": (36, 93, 199, 99),
    "publishUploadAllSize": (431, 106, 139, 21),
    "publishUploadAllAccess": (431, 138, 139, 21),
    "publishUploadSize3": (330, 107, 94, 16),
    "publishUploadAccess3": (330, 139, 94, 16),
    "publishUploadSync3": (330, 170, 94, 16),
    "publishStorageFill": (636, 122, 253, 11),
}

#: objektumnév → a MÉRT angol felirat (`publish_text.tre`)
MERT_FELIRAT = {
    "publishSelectionText": "Selection and Settings",
    "publishPicSizeText": "Photo Size",
    "publishCdNameText": "Name the Gift CD",
    "publishLabelCdName": "CD Name",
    "publishNameLimitText": "Limit 16 Characters",
    "publishLabelOptionBox2": "Erase Media",
    "publishLabelOptionBox3": "Include Picasa",
    "publishLabelBackupName": "Backup Set",
    "publishUploadSize3": "Size:",
    "publishUploadAccess3": "Visibility:",
    "publishUploadSync3": "Sync:",
}

#: a `web_group` elemei — SZÁNDÉKOSAN nem épülnek meg (online, `m_hidden`)
WEB_GROUP = (
    "publishAccountSpaceUsage", "publishAddMoreWeb", "publishManageWeb",
    "publishUploadAccount", "publishLabelUploadAccount",
    "publishSelectionInfo", "publishWebPublishGo",
)


@pytest.fixture(scope="module")
def engine(qt_app):
    """SAJÁT, könnyű motor: a panelhez nem kell a teljes főablak.

    A `qml_app` fixture függvény-hatókörű (minden próbához új ablakot
    állítana), és 44 paraméterezett állításnál ez percekbe telne — mérve:
    500 másodperc alatt sem futott végig.
    """
    from PySide6.QtQml import QQmlEngine

    motor = QQmlEngine()
    motor.addImportPath(str(app_module._APP_DIR / "qml"))
    yield motor
    motor.deleteLater()


@pytest.fixture(scope="module")
def panel(engine):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "PublishPanel.qml")),
    )
    _KEEP_ALIVE.append(comp)
    elem = comp.create()
    assert comp.errors() == [], comp.errorString()
    assert elem is not None
    _KEEP_ALIVE.append(elem)
    return elem


def test_a_MERT_vaszon() -> None:
    """A koordináták ehhez a vászonhoz szólnak — ha ez elmozdul, minden más is."""
    forras = (Path(app_module.__file__).parent / "qml" / "PicasaPy"
              / "PublishPanel.qml").read_text(encoding="utf-8")
    assert "vaszonSzelesseg: 1024" in forras
    assert "vaszonMagassag: 212" in forras


def test_mind_a_21_elem_megvan() -> None:
    assert len(MERT_GEOMETRIA) == 21


@pytest.mark.parametrize("nev", sorted(MERT_GEOMETRIA))
def test_az_elem_a_MERT_helyen_all(panel, nev: str) -> None:
    elem = panel.findChild(QObject, nev)
    assert elem is not None, f"{nev} nincs megépítve"
    x, y, sz, m = MERT_GEOMETRIA[nev]
    assert (elem.property("x"), elem.property("y")) == (x, y), nev
    assert (elem.property("width"), elem.property("height")) == (sz, m), nev


@pytest.mark.parametrize("nev", sorted(MERT_FELIRAT))
def test_a_felirat_a_MERT_szoveg(panel, nev: str) -> None:
    elem = panel.findChild(QObject, nev)
    assert elem.property("text") == MERT_FELIRAT[nev]


def test_a_cdname_16_karakterre_korlatoz(panel) -> None:
    """A `namelimitext` felirata ezt mondja ki — a mező tartsa is be."""
    mezo = panel.findChild(QObject, "publishCdName")
    assert mezo.property("maximumLength") == 16


@pytest.mark.parametrize("nev", WEB_GROUP)
def test_a_web_group_NEM_epult_meg(panel, nev: str) -> None:
    """Online funkció, a `.tre`-ben `m_hidden` — hatókörön kívül."""
    assert panel.findChild(QObject, nev) is None


def test_az_uzemmod_valtja_a_csoportokat(panel) -> None:
    for uzemmod, lathato in (
        ("cd", "publishPresentationGroup"),
        ("backup", "publishBackupGroup"),
        ("upload", "publishReplicationGroup"),
    ):
        panel.setProperty("uzemmod", uzemmod)
        for nev in ("publishPresentationGroup", "publishBackupGroup",
                    "publishReplicationGroup"):
            csoport = panel.findChild(QObject, nev)
            assert csoport.property("visible") is (nev == lathato), (
                f"{uzemmod}: a(z) {nev} láthatósága rossz")
    panel.setProperty("uzemmod", "cd")


def test_csak_a_KESZ_uzemmodok_vannak_bekotve() -> None:
    """Egy tétlen felület rosszabb a hiánynál — ezért a panelt CSAK olyan
    üzemmódban szabad bekötni, amelynek a művelete kész.

    #3503 óta az Ajándék-CD kész: `GiftCdHost.qml` köti be, `cd`
    üzemmódban, és a „Lemezre írás" a vezérlő műveletét hívja. #3504 óta a
    mentés is kész: `BackupHost.qml` köti be, `backup` üzemmódban, és a
    „Lemezre írás" a `backupController` műveleteit hívja. A feltöltés
    üzemmódja NINCS bekötve — ha valaki bekötné a panelt más gazdában vagy
    más üzemmódban, ez a próba szól.
    """
    qml = Path(app_module.__file__).parent / "qml"
    hivok = sorted(
        ut.name for ut in qml.rglob("*.qml")
        if ut.name != "PublishPanel.qml"
        and "PublishPanel" in ut.read_text(encoding="utf-8")
    )
    assert hivok == ["BackupHost.qml", "GiftCdHost.qml"], (
        f"váratlan gazda: {hivok}"
    )
    ajandek_cd = (qml / "PicasaPy" / "GiftCdHost.qml").read_text(encoding="utf-8")
    assert 'uzemmod: "cd"' in ajandek_cd
    assert "ajandekCdIrasa" in ajandek_cd

    mentes = (qml / "PicasaPy" / "BackupHost.qml").read_text(encoding="utf-8")
    assert 'uzemmod: "backup"' in mentes
    assert "backupController.futtasdMost(" in mentes
    assert "backupController.futtasdLemezkepbe(" in mentes
