"""A hangos vészfék őre (#1467).

A készletben 70 `QTimer.singleShot` hívás él a tesztekben, túlnyomó részük
egy jelzésre záruló eseményhurok **vészféke**. A régi alak néma volt: ha az
idő járt le, a hurok ugyanúgy lépett ki, mint sikeres jelzésnél, és a teszt
csak KÉSŐBB, egy látszólag független állításon bukott — vagy véletlenül zöld
maradt (a #1463 ezt élesben mérte ki a `test_tray_export.py`-n).

Ez a fájl a közös segéd (`support.qt_wait.HangosHurok`) három állítását őrzi:

1. a jelzés zárja a hurkot → nincs bukás, és nem ülünk ki időt;
2. a jelzés NEM jön meg → a hurok **ott helyben**, beszédesen bukik;
3. a jelzés az `exec()` ELŐTT jön meg (#2423) → a hurokba be sem lépünk.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Qt, QTimer, Signal

from support.qt_wait import HangosHurok, hangos_hurok, jelzes_neve


class _Jelzo(QObject):
    kesz = Signal()


class _Gyujto(QObject):
    """Szlot-gazda QObject — a jelzés hozzá SORBA ÁLLÍTVA érkezik."""

    def __init__(self) -> None:
        super().__init__()
        self.kapott: list[bool] = []

    def fogad(self) -> None:
        self.kapott.append(True)


class TestHangosVeszfek:
    def test_a_jelzes_zarja_a_hurkot(self, qt_app):
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, leiras="a teszt-művelet")
        QTimer.singleShot(10, jelzo.kesz.emit)
        kezdet = time.monotonic()
        hurok.exec()
        assert hurok.jelzes_megjott is True
        # a jelzésre AZONNAL továbblép, nem üli ki az időkorlátot
        assert time.monotonic() - kezdet < 2.0

    def test_a_veszfek_lejarta_ITT_bukik(self, qt_app):
        """Ez a jegy lényege: a néma vészfék helyett a VÁRAKOZÁS bukik."""
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, leiras="a soha meg nem jövő művelet", timeout_ms=120)
        with pytest.raises(AssertionError) as hiba:
            hurok.exec()
        uzenet = str(hiba.value)
        assert "#1467" in uzenet
        # a szöveg megnevezi, MI nem jött meg — enélkül a bukás ugyanolyan
        # tanácstalanná tesz, mint a néma vészfék
        assert "a soha meg nem jövő művelet" in uzenet
        assert "0,12" in uzenet or "0.12" in uzenet

    def test_az_exec_elott_erkezo_jelzes_nem_ul_ki_idot(self, qt_app):
        """#2423: a `quit()` az `exec()` előtt kiadva ELVESZIK — a hurok
        utána is kiülné a teljes időzítőt. A `HangosHurok` ilyenkor be sem
        lép a hurokba, tehát sem időt nem pazarol, sem hamis időtúllépést
        nem jelent."""
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, leiras="a szinkron művelet", timeout_ms=30_000)
        jelzo.kesz.emit()  # a jelzés az exec() ELŐTT jön
        kezdet = time.monotonic()
        hurok.exec()
        assert time.monotonic() - kezdet < 1.0

    def test_a_hurok_gyermeke_a_veszfek_timer(self, qt_app):
        """#430: árva, később elsülő timer nem maradhat a processzben."""
        jelzo = _Jelzo()
        hurok = HangosHurok(jelzo.kesz, leiras="x", timeout_ms=60)
        with pytest.raises(AssertionError):
            hurok.exec()
        timerek = [gy for gy in hurok.children() if isinstance(gy, QTimer)]
        assert timerek and all(not t.isActive() for t in timerek)

    def test_leiras_nelkul_a_JELZES_NEVE_kerul_az_uzenetbe(self, qt_app):
        """A mechanikus átírás sok helyen nem ad külön leírást — a bukás
        akkor sem lehet néma vagy tanácstalan: a jelzés neve azonosítja,
        mire vártunk."""
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, timeout_ms=60)
        with pytest.raises(AssertionError) as hiba:
            hurok.exec()
        assert "kesz" in str(hiba.value)

    def test_a_nevkiolvaso_ismeretlen_alakra_sem_dob(self):
        """Ha a PySide reprje egyszer megváltozik, a hangosítás értéke nem
        veszhet el egy kivétel miatt — csak a név lesz általánosabb."""
        assert jelzes_neve(object()) == "a háttérművelet"
        assert jelzes_neve(None) == "a háttérművelet"


class TestKesobbBekotottSzlot:
    """A hurok zárása nem vághatja le a nála KÉSŐBB bekötött szlotokat.

    ⚠️ Ez élesben megharapott (#1467). A `test_broken_photo_and_diskspace_459.py`
    importos őre a hangosítás után a futások harmadában bukott — `finished == []`,
    holott a jelzés megérkezett. MÉRVE, nyomkövetéssel: a hurok saját, ELSŐNEK
    bekötött záró szlotja lefutott, az `exec()` visszatért, és a teszt saját
    eredménygyűjtő szlotja csak EZUTÁN futott le. A záró `quit()` tehát levágta
    ugyanannak a kibocsátásnak a később bekötött, sorba állított kézbesítéseit.

    A javítás: halasztott (0 ms-os) zárás — a hurok megvárja a már posztolt
    kézbesítéseket. Az alábbi őr ezt a szerződést méri, sorba állított
    kapcsolattal kikényszerítve; a verseny természete miatt a valódi
    (terhelésfüggő) bukás nem reprodukálható determinisztikusan, ezért a
    fogat a KIKÉNYSZERÍTETT sorrend adja, nem a terhelés.
    """

    def test_a_kesobb_bekotott_sorba_allitott_szlot_is_lefut(self, qt_app):
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, timeout_ms=5000)
        gyujto = _Gyujto()
        # KÉSŐBB kötjük be, mint a hurok saját záró szlotját, és
        # KIFEJEZETTEN sorba állítva: a kézbesítése így biztosan a hurok
        # egy következő körfordulására marad
        jelzo.kesz.connect(gyujto.fogad, Qt.ConnectionType.QueuedConnection)

        QTimer.singleShot(0, jelzo.kesz.emit)
        hurok.exec()

        assert hurok.jelzes_megjott is True
        assert gyujto.kapott == [True], (
            "a hurok kilépett, mielőtt a nála később bekötött, sorba "
            "állított szlot lefutott volna — a záró quit() nem lehet azonnali"
        )


class TestRovidzarKesobbiSzlot:
    """A RÖVIDZÁR-ág (#2423) sem nyelheti el a hívó szlotját (#2743).

    ⚠️ Ez a testvére a fenti #1467-es esetnek, más ágon. Ha a jelzés már az
    `exec()` ELŐTT megérkezik, a hurok a #2423 óta azonnal visszatér (a
    `quit()` ilyenkor elveszne, és a teljes időzítőt kiülnénk). Csakhogy
    szálak közti (sorba állított) kapcsolatnál a Qt **kapcsolatonként külön
    eseményt posztol**: a hurok saját, közvetlen szlotja már lefutott, a
    hívóé viszont még a sorban áll — és az azonnali visszatérés miatt SOSEM
    kézbesítődik.

    Élesben: a `tests/app/test_face_scan_controller.py` esetei
    véletlenszerűen, GYORSAN (0,88 mp alatt) buktak `assert arrived is True`
    -val — nem időtúllépéssel (CI-futás `34248206013`, 2026-09-08). A
    `_jelzesre` docstringje kimondja a szerződést: „a hívó bármikor köthet rá
    további szlotot" — ennek a rövidzár-ágra is állnia kell.
    """

    def test_a_rovidzar_elott_erkezo_jelzes_utan_is_lefut_a_kesobbi_szlot(self, qt_app):
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, timeout_ms=5000)
        gyujto = _Gyujto()
        # a hurok saját szlotja UTÁN, sorba állítva — mint a valódi hívóknál
        jelzo.kesz.connect(gyujto.fogad, Qt.ConnectionType.QueuedConnection)

        # a jelzés az `exec()` ELŐTT jön meg: a hurok szlotja (közvetlen)
        # lefut, a gyűjtőé (sorba állított) a sorban marad
        jelzo.kesz.emit()
        assert hurok.jelzes_megjott is True, "a próba előfeltétele nem áll fenn"
        assert gyujto.kapott == [], (
            "a próba előfeltétele nem áll fenn: a sorba állított szlot már "
            "lefutott, tehát nem a rövidzár-ágat mérnénk"
        )

        hurok.exec()

        assert gyujto.kapott == [True], (
            "a rövidzár-ág elnyelte a hívó szlotját: az `exec()` visszatért, "
            "mielőtt az ugyanahhoz a kibocsátáshoz tartozó, sorba állított "
            "kézbesítés lefutott volna"
        )


#: A néma vészfék-alak ISMERT, indokolt kivételei: ezek a segédek maguk
#: mondják ki az időtúllépést (saját `assert`-tel, a jelzés megérkezését
#: külön nyilvántartva), ezért nem kell rájuk a közös hurok. A lista
#: SZÁNDÉKOSAN zárt: aki újat vesz fel, indokolja meg.
_ISMERT_SAJAT_HANGOS_VESZFEKEK = {
    # a jelzés SZÁNDÉKOSAN nem jön meg — a némaságot a teszt maga állítja
    ("tests/app/test_kollazs_gc_verseny_988.py", "test_a_mentes_tulel_agressziv_szemetgyujtest"),
    # kétjelzéses várakozás (photoOpFinished + photoOpFailed), #519
    ("tests/app/test_qml_slideshow.py", "_invoke_photo_op"),
    ("tests/app/test_regi_originals_a_feluleten_1425.py", "_wait"),  # #2408
    ("tests/app/test_save_controller.py", "_wait"),  # #2408
    ("tests/app/test_tray_export.py", "_wait_for_export"),  # #1038
    # GC-szünetes kollázs-várakozás (#988) — saját `assert`-je van
    ("tests/support/qt_wait.py", "varj_kollazs_jelzesre"),
}


class TestNemaVeszfekKapu:
    """Forrás-szintű kapu: ne szülessen ÚJ néma vészfék (#1467).

    A tiltott alak: egy eseményhurok, amit EGYSZERRE zár egy jelzés és egy
    `QTimer.singleShot(..., loop.quit)` — mert ilyenkor a kilépésből nem
    derül ki, melyik történt. A helyes megoldás a `support.qt_wait`
    `hangos_hurok`-ja; a fenti listán csak azok a segédek állnak, amelyek
    az időtúllépést SAJÁT `assert`-tel mondják ki.

    ⚠️ A kapu FORRÁST néz, nem viselkedést: azt méri, hogy nem másolják
    vissza a mintát. Azt NEM méri, hogy egy meglévő várakozás tényleg
    beváltja-e az ígéretét.
    """

    def test_nincs_uj_nema_veszfek_a_keszletben(self):
        import ast
        import re
        import warnings
        from pathlib import Path

        gyoker = Path(__file__).resolve().parents[2]
        talalatok = []
        for ut in sorted((gyoker / "tests").rglob("*.py")):
            forras = ut.read_text(encoding="utf-8")
            if "singleShot" not in forras:
                continue
            sorok = forras.splitlines()
            with warnings.catch_warnings():
                # más tesztfájlok régi, escape-hibás docstringjei nem a mi
                # dolgunk — a kapu nem szórhat idegen figyelmeztetéseket
                warnings.simplefilter("ignore", SyntaxWarning)
                fa = ast.parse(forras)
            for csomopont in ast.walk(fa):
                if not isinstance(csomopont, ast.FunctionDef):
                    continue
                torzs = "\n".join(sorok[csomopont.lineno - 1 : csomopont.end_lineno])
                for m in re.finditer(
                    r"QTimer\.singleShot\(\s*[^,]+,\s*(\w+)\.quit\s*\)", torzs
                ):
                    hurok = m.group(1)
                    zarja_jelzes = re.search(
                        rf"\.connect\({hurok}\.quit\)", torzs
                    ) or re.search(rf"{hurok}\.quit\(\)", torzs)
                    if not zarja_jelzes:
                        continue  # tiszta szünet/pumpa, nem vészfék
                    kulcs = (ut.relative_to(gyoker).as_posix(), csomopont.name)
                    if kulcs not in _ISMERT_SAJAT_HANGOS_VESZFEKEK:
                        talalatok.append(f"{kulcs[0]}:{csomopont.lineno} {kulcs[1]}")

        assert not talalatok, (
            "#1467: ÚJ néma vészfék került a készletbe — a hurkot egyszerre "
            "zárja egy jelzés és egy időzítő, tehát a kilépésből nem derül "
            "ki, melyik történt. Használd a `support.qt_wait.hangos_hurok`-ot:\n  "
            + "\n  ".join(talalatok)
        )

    def test_a_kivetel_lista_nem_avul_el(self):
        """Ha egy kivétel megszűnik (átírták a közös hurokra), a listáról is
        le kell venni — különben a kapu csendben tágul."""
        from pathlib import Path

        gyoker = Path(__file__).resolve().parents[2]
        hianyzo = [
            f"{f}::{fn}"
            for f, fn in _ISMERT_SAJAT_HANGOS_VESZFEKEK
            if f"def {fn}(" not in (gyoker / f).read_text(encoding="utf-8")
        ]
        assert not hianyzo, (
            "a kivétel-listán olyan segéd szerepel, ami már nem létezik: "
            + ", ".join(hianyzo)
        )


class TestHivoiQuitNemAdHamisIdotullepest:
    """A hívó saját szlotja lezárhatja a hurkot — ez nem időtúllépés.

    ⚠️ A fog HATÁRA, kimondva: ez az őr a SZERZŐDÉST rögzíti, de a valódi
    versenyt nem reprodukálja — a `QCoreApplication.processEvents()`
    mentőöv kivételével is zöld marad. A mentőöv szükségességét MÉRÉS
    igazolja, nem ez az őr: a `test_create_controller.py` a hívói
    `loop.quit()`-tel öt futásból ötben bukott mentőöv nélkül, és ötből
    egyben mentőövvel (a teljes javítás a hívói `quit()` elhagyása volt).

    ⚠️ MÉRVE (#1467): a `test_create_controller.py` és a
    `test_face_scan_controller.py` `_run` segédjében a hívó kezelője maga
    hívott `loop.quit()`-et. A hangos hurok saját szlotja a bekötési lista
    VÉGÉN áll, tehát sorba állított kézbesítésnél a hívó `quit()`-je
    kiléptette a hurkot, MIELŐTT a segéd nyilvántartásba vette volna a
    jelzést — és a segéd hamis időtúllépést jelentett. Négy őr bukott el
    így, futásonként váltakozva.
    """

    def test_a_hivo_quitje_utan_sem_bukik_ha_a_jelzes_megvolt(self, qt_app):
        jelzo = _Jelzo()
        hurok = hangos_hurok(jelzo.kesz, timeout_ms=5000)
        # a hívó saját, SORBA ÁLLÍTOTT kezelője zárja le a hurkot — a segéd
        # szlotja így a hurok kilépése után kerülne sorra
        jelzo.kesz.connect(hurok.quit, Qt.ConnectionType.QueuedConnection)

        QTimer.singleShot(0, jelzo.kesz.emit)
        hurok.exec()  # nem dobhat: a jelzés MEGVOLT

        assert hurok.jelzes_megjott is True
