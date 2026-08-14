"""A megszűnt online szolgáltatások menüpontjai — #422.

**A tulajdonos döntése (2026-08-14):** a Picasa webes tételei (Feltöltés
Google Fotókba / Picasa Webalbumba, Gyorsfeltöltés, Feltöltés tiltása,
Online műveletek) **maradjanak a menüben, véglegesen szürkén**. Így a menük
szerkezete és a tételek helye egyezik az eredetivel — az izommemória
működik —, miközben látszik, hogy nem használhatók.

**Miért külön állapot ez.** A `placeholder: true` eddig azt jelentette:
„még nincs bekötve" — ígéret a jövőre, amit a sor jobb szélén egy pont is
jelöl. A megszűnt szolgáltatásoknál ez félrevezető: azok soha nem lesznek
bekötve, mert a szolgáltatás maga szűnt meg (a Picasa Webalbumok 2016-ban,
a Blogger-feltöltő API vele együtt). Ezért kapnak `retired: true`-t:
ugyanúgy szürkék és kattinthatatlanok, de **nincs pont** a soruk végén, és
nem számítanak bele a hátralévő munkába.

A jegy elfogadási feltétele is így fogalmaz: „a nálunk értelmezhetetlen
webes tételek kivételével, külön indokolva".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_QML_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"

#: A megszűnt szolgáltatásokhoz tartozó tételek, menünként. A lista
#: SZÁNDÉKOSAN szűk: csak az kerül bele, aminek a szolgáltatása bizonyíthatóan
#: megszűnt. A helyi funkciók (pl. a gyűjtemény jelszava) NEM tartoznak ide,
#: azok továbbra is `placeholder`-ök, mert egyszer megvalósíthatók.
NYUGDIJAZOTT = {
    "PhotoContextMenu.qml": (
        "contextMenuUploadToWebAlbums",
        "contextMenuBlockUpload",
    ),
    "ViewerContextMenu.qml": (
        "viewerMenuQuickUpload",
        "viewerMenuBlockUpload",
    ),
    "AlbumContextMenu.qml": (
        "albumMenuOnlineActions",
        "albumMenuUploadToGooglePhotos",
    ),
    "FolderContextMenu.qml": ("folderMenuUploadToGooglePhotos",),
}

MIND = tuple(
    (fajl, nev) for fajl, nevek in NYUGDIJAZOTT.items() for nev in nevek
)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _menu_item(engine, komponens: str, object_name: str):
    """Egy menütétel a saját menüjéből, önállóan betöltve."""
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'{komponens} {{ objectName: "menu" }}\n'
        ).encode("utf-8"),
        QUrl(),
    )
    root = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert root is not None
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, root))
    item = root.findChild(QObject, object_name)
    assert item is not None, f"{object_name} nem található a(z) {komponens}-ben"
    return item


def _forras(fajl: str) -> str:
    return (_QML_DIR / "PicasaPy" / fajl).read_text(encoding="utf-8")


class TestANyugdijazottTetelekLatszanakDeTiltottak:
    @pytest.mark.parametrize(("fajl", "nev"), MIND, ids=[n for _, n in MIND])
    def test_a_menuben_marad_de_nem_kattinthato(
        self, qml_engine, fajl: str, nev: str
    ) -> None:
        """A tulajdonos döntése: maradjon a menüben, de ne legyen aktív.

        A jelenlétet a `_menu_item` megtalálása bizonyítja (ha kikerült volna
        a menüből, nem lenne a fában). A `visible`-t szándékosan NEM
        vizsgáljuk: az öröklődik a szülőtől, és egy zárt menü minden gyereke
        láthatatlan — viselkedést kell tesztelni, nem láthatóságot.
        """
        item = _menu_item(qml_engine, fajl.removesuffix(".qml"), nev)

        assert item.property("text"), "a tételnek van felirata (a helye megvan)"
        assert item.property("enabled") is False, "a tétel nem lehet aktív"

    @pytest.mark.parametrize(("fajl", "nev"), MIND, ids=[n for _, n in MIND])
    def test_nyugdijazottkent_van_jelolve(
        self, qml_engine, fajl: str, nev: str
    ) -> None:
        """`retired`, nem `placeholder`: nem hátralévő munka, hanem lezárt ügy."""
        item = _menu_item(qml_engine, fajl.removesuffix(".qml"), nev)

        assert item.property("retired") is True, (
            "a megszűnt szolgáltatás tételét `retired: true`-val kell jelölni"
        )

    @pytest.mark.parametrize(("fajl", "nev"), MIND, ids=[n for _, n in MIND])
    def test_nincs_rajta_a_folytatas_pontja(
        self, qml_engine, fajl: str, nev: str
    ) -> None:
        """A jobb szélső pont azt ígéri, hogy ez még jönni fog — itt nem jön."""
        item = _menu_item(qml_engine, fajl.removesuffix(".qml"), nev)
        dot = item.findChild(QObject, "placeholderDot")

        assert dot is None or dot.property("visible") is False, (
            "a megszűnt szolgáltatás tételén nem lehet folytatást ígérő pont"
        )


class TestASzamontartasHelyes:
    @pytest.mark.parametrize("fajl", sorted(NYUGDIJAZOTT))
    def test_a_forrasban_nem_placeholderkent_szerepelnek(self, fajl: str) -> None:
        """Forrás-őr: a nyugdíjazott tétel ne csússzon vissza helyfoglalónak —
        onnan ugyanis egy későbbi kör „hátralévő munkának" olvasná."""
        forras = _forras(fajl)
        for nev in NYUGDIJAZOTT[fajl]:
            blokk = re.search(
                rf'objectName: "{nev}".*?\n    \}}', forras, re.DOTALL
            )
            assert blokk is not None, f"nem található a(z) {nev} blokkja"
            assert "placeholder: true" not in blokk.group(0), (
                f"{nev}: megszűnt szolgáltatás, nem helyfoglaló"
            )
            assert "retired: true" in blokk.group(0)

    def test_a_helyi_funkciok_helyfoglalok_maradnak(self) -> None:
        """Ellenpróba: ami MEGVALÓSÍTHATÓ, az nem kerülhet a nyugdíjazottak
        közé. A gyűjtemény jelszava helyi funkció, nem webes szolgáltatás."""
        forras = _forras("CollectionContextMenu.qml")
        blokk = re.search(
            r'objectName: "collectionMenuPassword".*?\n    \}', forras, re.DOTALL
        )
        assert blokk is not None
        assert "placeholder: true" in blokk.group(0)
        assert "retired: true" not in blokk.group(0)
