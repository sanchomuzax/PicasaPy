"""#2983: a mappa-borító azonosítója VISSZAPERES útvonalnál is működik.

A tulajdonos windowsos gépén egyetlen mappa-borító sem jelent meg, és a konzol
minden sorra hibát írt. Az ok MÉRVE: a Qt az `image://` URL útvonalát
dekódolja, a **kódolt elválasztót** viszont meghagyja.

| a QML-nek átadva | amit a szolgáltató KAP |
|---|---|
| `C:\\Users\\…\\Képek\\AI` | **`C:%5CUsers%5C…%5CKépek%5CAI`** |
| `C:/Users/…/Képek/AI` | változatlanul |
| `/home/…/nyaralás 2024` | változatlanul (ékezet, szóköz rendben) |
| `/home/…/a#b` | változatlanul |

Windowson az index natív, visszaperes útvonalat tárol, tehát a kódolt alakkal
a keresés nem talál fájlt → nincs borító → minden sor a mappaikonra esik
vissza, és a null kép miatt a Qt hibát naplóz.

⚠️ **A hiba LINUXON is reprodukálható** — a QML→szolgáltató lánc kódolása
platformfüggetlen —, ezért ez az őr itt is elbukik a javítás nélkül. Windows
nem kell hozzá.
"""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickImageProvider, QQuickView
from picasapy.app.folder_cover_provider import (
    FolderCoverProvider,
    normalizald_az_azonositot,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_KEEPALIVE: list[object] = []

#: A tulajdonos naplójából vett, valódi alakok.
WINDOWSOS = "C:\\Users\\attila.virag\\OneDrive - centralmediacsoport\\Képek\\AI"
HALOZATI = "\\\\ds215j\\lemez\\My Pictures\\PicasaPy meroszett"


class TestANormalizalas:
    def test_a_KODOLT_visszaper_feloldva(self):
        assert (
            normalizald_az_azonositot("C:%5CUsers%5Cattila.virag%5CKépek%5CAI")
            == "C:\\Users\\attila.virag\\Képek\\AI"
        )

    def test_a_kisbetus_alak_is(self):
        """A százalék-kódolás kis- és nagybetűs jegyekkel is érvényes."""
        assert normalizald_az_azonositot("a%5cb") == "a\\b"

    def test_a_HALOZATI_utvonal_ket_vezeto_visszapere(self):
        assert normalizald_az_azonositot(
            "%5C%5Cds215j%5Clemez%5CMy Pictures"
        ) == "\\\\ds215j\\lemez\\My Pictures"

    def test_a_kodolt_ELORE_per_is(self):
        assert normalizald_az_azonositot("a%2Fb") == "a/b"

    def test_a_TENYLEGES_szazalek_nem_romlik_el(self):
        """A jegy kimondott feltétele: egy `a%41b` nevű mappa ne `aAb` legyen.

        A Qt a `%`-ot már feloldotta (`%25` → `%`), tehát a teljes
        `fromPercentEncoding` itt MÁSODSZOR dekódolna."""
        assert normalizald_az_azonositot("/home/sancho/a%41b") == "/home/sancho/a%41b"

    def test_a_szokozos_ekezetes_utvonal_valtozatlan(self):
        ut = "/home/sancho/Képek/nyaralás 2024"
        assert normalizald_az_azonositot(ut) == ut

    def test_URES_azonosito(self):
        assert normalizald_az_azonositot("") == ""


class TestAQmlLanc:
    """A LÁNC: a QML URL-t épít, a Qt átadja, a szolgáltató megkapja.

    Ez az a lépés, ami a #2983-at okozta — és amit egy tisztán pythonos teszt
    nem lát, mert a kódolás a Qt URL-elemzőjében történik."""

    @pytest.fixture
    def kapott(self, qt_app):
        naplo: list[str] = []

        class Probe(QQuickImageProvider):
            def __init__(self) -> None:
                super().__init__(QQuickImageProvider.ImageType.Image)

            def requestImage(self, id, size, requestedSize):  # noqa: A002
                naplo.append(id)
                kep = QImage(2, 2, QImage.Format.Format_ARGB32)
                kep.fill(0xFF00FF00)
                if size is not None:
                    size.setWidth(2)
                    size.setHeight(2)
                return kep

        view = QQuickView()
        view.engine().addImageProvider("probe2983", Probe())
        qml = (
            "import QtQuick\nItem {\n"
            f'  Image {{ source: "image://probe2983/" + "{WINDOWSOS}" }}\n'
            "}\n"
        ).replace("\\", "\\\\")
        komponens = QQmlComponent(view.engine())
        komponens.setData(qml.encode("utf-8"), QUrl())
        assert komponens.errors() == [], [
            hiba.toString() for hiba in komponens.errors()
        ]
        elem = komponens.create()
        view.setContent(QUrl(), komponens, elem)
        view.resize(64, 64)
        view.show()
        for _ in range(20):
            qt_app.processEvents()
        _KEEPALIVE.extend([view, komponens, elem])
        return naplo

    def test_a_Qt_KODOLVA_adja_at_es_a_normalizalas_visszaadja(self, kapott):
        """A hiba GYÖKERE, számmal — és a javítás ugyanazon a mért azonosítón.

        A két állítás SZÁNDÉKOSAN egy esetben van: a Qt kép-gyorstára
        folyamat-szintű és URL-kulcsú, tehát ugyanarra az URL-re a MÁSODIK
        teszt már nem hívná meg a szolgáltatót (mérve: üres napló), és az
        eset hamisan zöldülne vagy elhasalna.

        Ha egy későbbi Qt-verzió feloldaná a `%5C`-t, az első állítás elbukik
        — és akkor a normalizálás feleslegessé válik. Addig ez a bizonyíték."""
        assert kapott, "a szolgáltatót meg sem hívták"
        assert "%5C" in kapott[0], (
            f"a Qt már feloldja a visszapert: {kapott[0]!r}"
        )
        assert normalizald_az_azonositot(kapott[0]) == WINDOWSOS


class TestASzolgaltato:
    """A szolgáltató a NORMALIZÁLT útvonallal keresi a fájlokat."""

    def test_a_kodolt_azonositoval_is_a_valodi_mappat_kerdezi(self, qt_app):
        kerdezett: list[str] = []

        def lekerdezo(mappa: str):
            kerdezett.append(mappa)
            return ()

        szolgaltato = FolderCoverProvider(lekerdezo)
        szolgaltato.requestImage("C:%5CUsers%5Cteszt%5CKépek", None, None)
        assert kerdezett == ["C:\\Users\\teszt\\Képek"]

    def test_a_gyorstar_a_NORMALIZALT_kulcsra_megy(self, qt_app):
        """Különben a kódolt és a dekódolt alak két bejegyzést kapna, és a
        mappánkénti négy JPEG kétszer dekódolódna."""
        hivasok: list[str] = []

        def lekerdezo(mappa: str):
            hivasok.append(mappa)
            return ()

        szolgaltato = FolderCoverProvider(lekerdezo)
        szolgaltato.requestImage("a%5Cb", None, None)
        szolgaltato.requestImage("a\\b", None, None)
        assert hivasok == ["a\\b"]
