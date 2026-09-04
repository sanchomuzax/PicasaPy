"""#1617 — az export hibaágai a KIVÁLTÓ helyzetből, ágankénti őrrel.

## Amit a jegy állított, és amit MÉRTÜNK

A jegy szerint „a tíz hibaágból nálunk egy sincs bekötve". Ez **ma nem
igaz**: a #1166 utómunkája bekötötte őket, végig a láncon —
`exporter.py` (fajta) → `ExportMixin._export_error_text` (szöveg) →
`exportFailedDetails` → `ExportDialogs.qml` (a felhasználó látja).

Ami VALÓBAN hiányzott, az a jegy második pontja: **ágankénti teszt,
amely a kiváltó helyzetet állítja elő** — nem a kivételt injektálja. Ez a
fájl az.

## Miért a kiváltó helyzet, és nem a kivétel

Injektált kivétellel a teszt akkor is zöld marad, ha a valódi
hibahelyzetben a kód más ágra fut (vagy oda sem jut el). A projekt
visszatérő kára épp ez volt: a zöld teszt elfedte, hogy a felület némán
hatástalan. A `chmod`-alapú próbák valódi `OSError`-t váltanak ki, a
valódi útvonalon.

⚠️ **Rendszergazdaként ezek a próbák értelmetlenek**: a root a
jogosultsági biteket figyelmen kívül hagyja, a `chmod 0` alatti mappa is
olvasható marad. Ilyenkor a teszt **kihagyja magát**, nem hamisan zöldül.

## Hány hibaág van valójában? HÉT, nem tíz

A spec 8.7 táblája tíz sort tartalmaz, de három közülük **nem hibaág**:

| kulcs | mi ez |
|---|---|
| `CExportPrefsPage::destexists` | **kérdés** („Felülírja az új albummal?") |
| `CExportPrefsPage::overwritetitle` | a kérdés **ablakcíme** |
| `CExportPrefsPage::errortitle` | a hibaablak **címe** |

Marad hét valódi ág, és mind a hetet ismerjük. A `scanfile` ág a mi
felépítésünkben nem előállítható (az ürítésünk nem külön
fájl-letapogatással dolgozik) — ezt a spec 12.3 ki is mondja.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

# #2176: az `uzenetek` fixture valódi `QGuiApplication`-t példányosít. Ha
# nincs használható megjelenítő, a Qt nem kivételt dob, hanem ABORTÁL —
# a részfutás `Fatal Python error: Aborted`-tal, 134-es kilépőkóddal áll
# meg, és a már lefutott próbák eredménye is elvész. Mérve: alapértelmezés
# nélkül 3/3 abort, offscreennel 3/3 zöld. `setdefault`, tehát aki valódi
# megjelenítőn akar futni, a környezetből felülírhatja.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from picasapy.export import ExportItem, export_photos

_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0

#: Windowson a `chmod` a POSIX-biteket NEM érvényesíti: a „csak olvasható"
#: mappába a Python továbbra is ír, a `chmod(0)` alatti mappa listázható.
#: A próba tehát nem váltja ki a hibaágat — az `error_kind` üresen marad,
#: és a teszt NEM azt méri, amit állít.
#:
#: ⚠️ Ez a windows-lábon 2026-09-01-ig MINDEN PR-t elbuktatott (`exit 1`,
#: négy állítás), csak nem tűnt fel: a windows-láb `continue-on-error`,
#: tehát nem blokkol. A darab 1/4 így hetekig NEM tesztelt a windowson —
#: a zöld összkép mögött néma lefedettség-vesztés.
_WINDOWS = os.name == "nt"

_jogosultsag_kihagy = pytest.mark.skipif(
    _ROOT or _WINDOWS,
    reason=(
        "rendszergazdaként a jogosultsági bitek nem korlátoznak; "
        "Windowson a chmod nem érvényesíti a POSIX-biteket"
    ),
)

#: Régi név, hogy a fájlon belüli hivatkozások egy helyen dőljenek el.
_root_kihagy = _jogosultsag_kihagy


def _kep(ut: Path) -> Path:
    """Valódi, beolvasható JPEG — a hibaágnak a MÁSIK okból kell jönnie."""
    import cv2
    import numpy as np

    ut.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(ut), np.full((8, 8, 3), 128, dtype=np.uint8))
    return ut


class TestDestdir:
    """`IDS_DESTDIRCANNOCREATE` — a célkönyvtár nem hozható létre."""

    def test_fajlra_mutato_cel(self, tmp_path: Path):
        cel = tmp_path / "ki"
        cel.write_bytes(b"ez egy fajl")
        jelentes = export_photos(
            [ExportItem(source=_kep(tmp_path / "src/a.jpg"))], cel
        )
        assert jelentes.error_kind == "destdir"
        assert jelentes.exported == ()

    @_root_kihagy
    def test_irasvedett_szulomappa(self, tmp_path: Path):
        szulo = tmp_path / "zart"
        szulo.mkdir()
        szulo.chmod(stat.S_IRUSR | stat.S_IXUSR)  # nincs írásjog
        try:
            jelentes = export_photos(
                [ExportItem(source=_kep(tmp_path / "src/a.jpg"))],
                szulo / "uj",
            )
            assert jelentes.error_kind == "destdir"
        finally:
            szulo.chmod(stat.S_IRWXU)


class TestUritesiAgak:
    """A `purge_existing=True` három ága: `scan` · `delete` · `remove`."""

    @_root_kihagy
    def test_scan_ha_a_celmappa_nem_olvashato(self, tmp_path: Path):
        """`CExportPrefsPage::scanerror` — a cél LETAPOGATÁSA bukik."""
        cel = tmp_path / "ki"
        cel.mkdir()
        (cel / "regi.jpg").write_bytes(b"x")
        cel.chmod(0)
        try:
            jelentes = export_photos(
                [ExportItem(source=_kep(tmp_path / "src/a.jpg"))],
                cel,
                purge_existing=True,
            )
            assert jelentes.error_kind == "scan", (
                "az olvashatatlan célmappa nem a letapogatás-hibaágra "
                f"futott, hanem: {jelentes.error_kind!r}"
            )
        finally:
            cel.chmod(stat.S_IRWXU)

    @_root_kihagy
    def test_delete_ha_a_benne_levo_FAJL_nem_torolheto(self, tmp_path: Path):
        """`CExportPrefsPage::deleteerror` — az előző album törlése bukik.

        A törölhetőséget a SZÜLŐ írásjoga dönti el, nem a fájlé."""
        cel = tmp_path / "ki"
        cel.mkdir()
        (cel / "regi.jpg").write_bytes(b"x")
        cel.chmod(stat.S_IRUSR | stat.S_IXUSR)  # olvasható, de nem írható
        try:
            jelentes = export_photos(
                [ExportItem(source=_kep(tmp_path / "src/a.jpg"))],
                cel,
                purge_existing=True,
            )
            assert jelentes.error_kind == "delete", (
                "a törölhetetlen FÁJL nem a törlés-hibaágra futott, "
                f"hanem: {jelentes.error_kind!r}"
            )
        finally:
            cel.chmod(stat.S_IRWXU)

    @_root_kihagy
    def test_remove_ha_a_benne_levo_MAPPA_nem_torolheto(self, tmp_path: Path):
        """`CExportPrefsPage::removeerror` — könyvtár eltávolítása bukik.

        A `delete`-től CSAK az különbözteti meg, hogy a bent lévő elem
        mappa-e — ezért van rá külön próba: egyetlen elágazás dönti el,
        melyik üzenetet kapja a felhasználó."""
        cel = tmp_path / "ki"
        (cel / "alkonyvtar").mkdir(parents=True)
        cel.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            jelentes = export_photos(
                [ExportItem(source=_kep(tmp_path / "src/a.jpg"))],
                cel,
                purge_existing=True,
            )
            assert jelentes.error_kind == "remove", (
                "a törölhetetlen MAPPA nem az eltávolítás-hibaágra futott, "
                f"hanem: {jelentes.error_kind!r}"
            )
        finally:
            cel.chmod(stat.S_IRWXU)


class TestWrite:
    """`CImageOutput::filewriteerr` — nem minden fájl írható."""

    def test_olvashatatlan_forras(self, tmp_path: Path):
        """A forrás nem JPEG — az elem bukik, a köteg viszont folytat."""
        jo = _kep(tmp_path / "src/jo.jpg")
        rossz = tmp_path / "src/rossz.jpg"
        rossz.write_bytes(b"ez nem kep")

        jelentes = export_photos(
            [ExportItem(source=jo), ExportItem(source=rossz)],
            tmp_path / "ki",
        )

        assert jelentes.error_kind == "write"
        assert len(jelentes.exported) == 1, "a köteg megállt egy rossz elemen"
        assert jelentes.failed == (rossz,)
        assert jelentes.reasons, "a bukott elemhez indoklás is jár (#136)"

    def test_hibatlan_kotegnek_NINCS_hibafajtaja(self, tmp_path: Path):
        """Az őr foga: ha ez elromlik, minden export hibát jelentene."""
        jelentes = export_photos(
            [ExportItem(source=_kep(tmp_path / "src/a.jpg"))], tmp_path / "ki"
        )
        assert jelentes.error_kind == ""
        assert jelentes.failed == ()


#: A hét VALÓDI hibaág — a spec 8.7 tíz sorából a kérdés és a két
#: ablakcím nélkül.
HIBAAGAK = ("destdir", "delete", "remove", "scan", "scanfile", "write", "noimages")


@pytest.fixture(scope="module")
def uzenetek():
    """Az `ExportMixin` a `tr()`-t a QObject-től kapja, ezért valódi
    QObject-be keverve példányosítjuk — nem `object.__new__`-val."""
    from PySide6.QtCore import QObject
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    from picasapy.app.export_controller import ExportMixin

    class _Probaverzio(ExportMixin, QObject):
        pass

    return _Probaverzio()


class TestAzUzenetLancVegig:
    """A fajta ÉS a hozzá tartozó eredeti szöveg — a lánc két vége."""

    @pytest.mark.parametrize("fajta", HIBAAGAK)
    def test_mind_a_het_fajtahoz_van_szoveg(self, uzenetek, fajta: str):
        assert uzenetek._export_error_text(fajta), (
            f"a(z) {fajta!r} fajtához nincs üzenet — a felhasználó "
            "üres hibaablakot kapna"
        )

    def test_a_szovegek_KULONBOZNEK(self, uzenetek):
        """Az eredeti hét ága hét KÜLÖN szöveget ad; ha kettő egybeesne,
        a felhasználó nem tudná, mi történt."""
        szovegek = [uzenetek._export_error_text(f) for f in HIBAAGAK]
        assert len(set(szovegek)) == len(HIBAAGAK)

    def test_ismeretlen_fajtara_ures(self, uzenetek):
        assert uzenetek._export_error_text("nincs-ilyen") == ""
