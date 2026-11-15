"""#6972: a Revert párbeszéd paritása az eredeti Picasával.

Az eredeti (`0x0053b2e0`, `0x0053b615`, `0x0053b87e`):

* egy képnél ott az „Undo Save" gomb és a magyarázó sor (`message1undo`);
* több képnél a kérdés „Revert to original version of these files?"
  (`messageX`), a gomb és a magyarázat rejtve;
* ha a fájl a mentés óta kívülről módosult, külön figyelmeztetés jön
  (`changed1` / `changedX`) „Revert Anyway" gombbal; a Mégse nem állít vissza.

A gombokra valódi egérkattintás megy; a nyelvi ágban minden fordítás sorra
kerül. A Visszaállítás után az ini-kulcsok tesztje: `tests/edit`.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QTranslator, Qt
from PySide6.QtTest import QSignalSpy, QTest

from support.halasztott_parbeszed import nyisd_meg
from support.jpeg_factory import make_minta_jpeg
from support.qt_wait import wait_for_signal
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    vizualis_bejaras,
)
from tests.support.varakozas import var_feltetelre

_I18N = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "i18n"
_FORRAS_TOBBES = "Revert to original version of these files?"
_FORRAS_EGY = "Revert to original version of file?"
_FORRAS_CHANGED1 = (
    "This file has been changed outside of PicasaPy. Reverting will lose those changes."
)
_FORRAS_CHANGEDX = (
    "These files have changed outside of PicasaPy. Reverting will lose those changes."
)
_FORRAS_FOLYTATAS = "Do you want to revert?"
_FORRAS_GOMB = "Revert Anyway"
_NYELVEK = sorted(p.stem.removeprefix("picasapy_") for p in _I18N.glob("picasapy_*.ts"))


@pytest.fixture
def revert_app(qt_app, tmp_path):
    """Három fotó, a=0 és b=1 szerkesztéssel (mentés után visszaállítható)."""

    def kepeket(lib: Path) -> None:
        for index, nev in enumerate(("a.jpg", "b.jpg", "c.jpg")):
            make_minta_jpeg(lib / nev, size=(320, 240), seed=6972 + index)
        (lib / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=bw=1;\n[b.jpg]\nfilters=bw=1;\n", encoding="utf-8"
        )

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=kepeket)


def _kepernyokep(window, nev: str) -> None:
    """Opcionális képernyőkép a szemrevételezéshez: `PICASAPY_6972_KEPEK=<mappa>`."""
    mappa = os.environ.get("PICASAPY_6972_KEPEK", "")
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    kep = window.grabWindow()
    assert not kep.isNull(), "üres lett a képernyőkép"
    assert kep.save(str(cel / f"{nev}.png")), f"nem menthető: {nev}"


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _var(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _lathato(window, nev: str) -> bool:
    elem = window.findChild(QObject, nev)
    return elem is not None and bool(elem.property("visible"))


def _nyisd_a_visszaallitast(window, qt_app, sorok: list[int]) -> None:
    nyisd_meg(window, "saveDialogs")
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        _gyerek(window, "saveDialogs"), "openRevert",
        Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", sorok),
    )
    _var(
        qt_app,
        lambda: _gyerek(window, "revertConfirmDialog").property("opened") is True,
        "a Revert megerősítő nem nyílt meg",
    )


def _zard_be(window, qt_app, nev: str) -> None:
    QMetaObject.invokeMethod(
        _gyerek(window, nev), "close", Qt.ConnectionType.DirectConnection
    )
    _var(
        qt_app,
        lambda: _gyerek(window, nev).property("visible") is False,
        f"{nev} nem záródott be",
    )


def _lathato_gombok(dialog) -> list[tuple[float, str]]:
    from PySide6.QtCore import QPointF

    footer = dialog.property("footer")
    nevek = {"revertOkButton", "revertUndoSaveButton", "revertCancelButton"}
    return sorted(
        (item.mapToScene(QPointF(0, 0)).x(), item.objectName())
        for item in vizualis_bejaras(footer)
        if item.objectName() in nevek and item.isVisible()
    )


def _fordito_szoveg(kod: str, forras: str) -> str:
    """A `.ts`-ben a SaveDialogs-kontextus fordítása (angolnál a forrás)."""
    gyoker = ET.parse(_I18N / f"picasapy_{kod}.ts").getroot()
    for ctx in gyoker.iter("context"):
        if ctx.findtext("name") != "SaveDialogs":
            continue
        for msg in ctx.findall("message"):
            if msg.findtext("source") == forras:
                tr = msg.find("translation")
                assert tr is not None and tr.get("type") != "unfinished", (kod, forras)
                return tr.text or ""
    raise AssertionError(f"{kod}: {forras!r} hiányzik a SaveDialogs kontextusból")


def _jpeg(szin: tuple[int, int, int]) -> bytes:
    ok, kodolt = cv2.imencode(".jpg", np.full((24, 24, 3), szin, dtype=np.uint8))
    assert ok
    return kodolt.tobytes()


def _fotok_mentese(qt_app, controller, sorok: list[int]) -> dict[int, tuple[Path, bytes]]:
    """A sorok mentése; visszaadja az útvonalat és a MEGŐRZÖTT EREDETI bájtjait."""
    wait_for_signal(
        controller.saveFinished,
        lambda: controller.saveRowsToDisk(sorok),
        description="a kép mentése a visszaállítás előtt",
        process_events_with=qt_app,
    )
    ki = {}
    for sor in sorok:
        kep = Path(str(controller.photos.filePathAt(sor)))
        eredeti = kep.parent / ".picasaoriginals" / kep.name
        assert eredeti.is_file(), f"nincs megőrzött eredeti: {kep.name}"
        ki[sor] = (kep, eredeti.read_bytes())
    return ki


class TestEgyKepEsTobbKep:
    def test_egy_kepnel_ott_az_undo_save_gomb_es_a_magyarazat(self, revert_app, qt_app):
        window, _controller, _engine = revert_app
        _nyisd_a_visszaallitast(window, qt_app, [0])

        _kepernyokep(window, "egy-kep")
        assert _gyerek(window, "revertConfirmMessage").property("text") == _FORRAS_EGY
        assert _lathato(window, "revertUndoSaveButton")
        assert _lathato(window, "revertUndoSaveHint")
        assert [nev for _x, nev in _lathato_gombok(
            _gyerek(window, "revertConfirmDialog"))] == [
            "revertOkButton", "revertUndoSaveButton", "revertCancelButton"]

    def test_tobb_kepnel_a_kerdes_pontosan_a_hivatalos_es_nincs_undo_save(
        self, revert_app, qt_app
    ):
        window, _controller, _engine = revert_app
        _nyisd_a_visszaallitast(window, qt_app, [0, 1])
        _kepernyokep(window, "tobb-kep")

        assert (
            _gyerek(window, "revertConfirmMessage").property("text") == _FORRAS_TOBBES
        )
        assert not _lathato(window, "revertUndoSaveButton")
        assert not _lathato(window, "revertUndoSaveHint")
        gombok = _lathato_gombok(_gyerek(window, "revertConfirmDialog"))
        assert [nev for _x, nev in gombok] == ["revertOkButton", "revertCancelButton"]

    def test_a_gombsor_oda_vissza_valtasnal_is_jo_marad(self, revert_app, qt_app):
        """Egy kép, több kép, megint egy kép: a gombok sorrendje és köze
        mindig az eredeti, a rejtett gomb helye nem marad üresen."""
        window, _controller, _engine = revert_app
        dialog_neve = "revertConfirmDialog"
        egy = ["revertOkButton", "revertUndoSaveButton", "revertCancelButton"]
        tobb = ["revertOkButton", "revertCancelButton"]

        def merj(sorok: list[int], vart: list[str]) -> tuple[list[str], float]:
            _nyisd_a_visszaallitast(window, qt_app, sorok)
            dialog = _gyerek(window, dialog_neve)
            # a gombsor elrendezése a megnyitás után egy-két képkockával áll be
            # (lassabb gépen később): addig várunk, de legfeljebb a korlátig
            ok = _gyerek(window, "revertOkButton")

            def _beallt() -> bool:
                gombok = _lathato_gombok(dialog)
                if [nev for _x, nev in gombok] != vart or len(gombok) < 2:
                    return False
                # a kivett gomb helye is bezárult (a rés a gombtávolság nagyságrendje)
                return gombok[1][0] - (gombok[0][0] + ok.width()) < 40

            var_feltetelre(qt_app, _beallt)
            gombok = _lathato_gombok(dialog)
            koz = gombok[1][0] - (gombok[0][0] + ok.width())
            nevek = [nev for _x, nev in gombok]
            _zard_be(window, qt_app, dialog_neve)
            return nevek, koz

        nevek1, koz1 = merj([0], egy)
        nevek2, koz2 = merj([0, 1], tobb)
        nevek3, koz3 = merj([0], egy)

        assert (nevek1, nevek2, nevek3) == (egy, tobb, egy)
        assert abs(koz2 - koz1) <= 1, f"üres rés a gombok között: {koz1} és {koz2}"
        assert abs(koz3 - koz1) <= 1, f"a visszaváltás után más a köz: {koz1} és {koz3}"

    def test_az_undo_save_a_gombbal_egy_kepnel_valoban_kattinthato(
        self, revert_app, qt_app
    ):
        window, controller, _engine = revert_app
        _nyisd_a_visszaallitast(window, qt_app, [0])
        hivasok = []
        eredeti = controller.undoLastSave
        controller.undoLastSave = lambda sorok: hivasok.append(list(sorok))
        try:
            kattints(window, qt_app, _gyerek(window, "revertUndoSaveButton"))
        finally:
            controller.undoLastSave = eredeti
        assert hivasok == [[0]]


class TestEgyesNyelvek:
    """Minden nyelvi fordítással: a kérdés a fordítás, a gomb és a hint rejtve."""

    def test_minden_nyelven_a_tobbes_kerdes_a_forditas_es_a_gomb_rejtve(
        self, revert_app, qt_app
    ):
        window, _controller, engine = revert_app
        hibak: list[str] = []
        for kod in _NYELVEK:
            fordito = QTranslator(qt_app)
            if not fordito.load(f"picasapy_{kod}", str(_I18N)):
                hibak.append(f"{kod}: a .qm nem tölthető be")
                continue
            qt_app.installTranslator(fordito)
            try:
                engine.retranslate()
                qt_app.processEvents()
                _nyisd_a_visszaallitast(window, qt_app, [0, 1])
                kapott = _gyerek(window, "revertConfirmMessage").property("text")
                vart = _fordito_szoveg(kod, _FORRAS_TOBBES)
                if kapott != vart:
                    hibak.append(f"{kod}: kérdés {kapott!r} != {vart!r}")
                if _lathato(window, "revertUndoSaveButton"):
                    hibak.append(f"{kod}: az Undo Save gomb látszik több képnél")
                if _lathato(window, "revertUndoSaveHint"):
                    hibak.append(f"{kod}: a magyarázó sor látszik több képnél")
                _zard_be(window, qt_app, "revertConfirmDialog")
                _nyisd_a_visszaallitast(window, qt_app, [0])
                if not _lathato(window, "revertUndoSaveButton"):
                    hibak.append(f"{kod}: az Undo Save gomb hiányzik egy képnél")
                if not _lathato(window, "revertUndoSaveHint"):
                    hibak.append(f"{kod}: a magyarázó sor hiányzik egy képnél")
                _zard_be(window, qt_app, "revertConfirmDialog")
            finally:
                qt_app.removeTranslator(fordito)
        engine.retranslate()
        assert not hibak, "\n".join(hibak)
        assert len(_NYELVEK) >= 41

    def test_a_kulso_modositas_szovegei_minden_nyelven_fordituak(self):
        """A `.ts` mind az öt új szöveget befejezett fordítással tartalmazza."""
        hibak = []
        for kod in _NYELVEK:
            for forras in (_FORRAS_TOBBES, _FORRAS_CHANGED1, _FORRAS_CHANGEDX,
                           _FORRAS_FOLYTATAS, _FORRAS_GOMB):
                szoveg = _fordito_szoveg(kod, forras)
                if not szoveg.strip() or "\\n" in szoveg:
                    hibak.append(f"{kod}: {forras!r} -> {szoveg!r}")
        assert not hibak, "\n".join(hibak)


class TestKulsoModositas:
    def test_valtozatlan_mentett_kep_nem_kap_figyelmeztetest(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        fotok = _fotok_mentese(qt_app, controller, [0])
        kep, eredeti = fotok[0]
        _nyisd_a_visszaallitast(window, qt_app, [0])

        wait_for_signal(
            controller.revertFinished,
            lambda: kattints(window, qt_app, _gyerek(window, "revertOkButton")),
            description="a változatlan kép visszaállítása",
            process_events_with=qt_app,
        )

        assert _gyerek(window, "revertChangedDialog").property("visible") is False
        assert kep.read_bytes() == eredeti

    def test_kivulrol_modositott_kepnel_megjelenik_a_figyelmeztetes(
        self, revert_app, qt_app
    ):
        window, controller, _engine = revert_app
        fotok = _fotok_mentese(qt_app, controller, [0])
        kep, _eredeti = fotok[0]
        kep.write_bytes(_jpeg((250, 10, 10)))
        spy = QSignalSpy(controller.revertFinished)
        _nyisd_a_visszaallitast(window, qt_app, [0])

        kattints(window, qt_app, _gyerek(window, "revertOkButton"))

        figyelmeztetes = _gyerek(window, "revertChangedDialog")
        _var(qt_app, lambda: figyelmeztetes.property("opened") is True,
             "a külső módosítás figyelmeztetése nem jelent meg")
        _kepernyokep(window, "kulso-modositas")
        assert _gyerek(window, "revertChangedMessage").property("text") == _FORRAS_CHANGED1
        assert _gyerek(window, "revertChangedContinue").property("text") == _FORRAS_FOLYTATAS
        assert _gyerek(window, "revertAnywayButton").property("text") == _FORRAS_GOMB
        assert _gyerek(window, "revertChangedCancelButton").property("activeFocus") is True
        assert spy.count() == 0, "a figyelmeztetés előtt már visszaállt a kép"

    def test_revert_anyway_visszaallit(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        kep, eredeti = _fotok_mentese(qt_app, controller, [0])[0]
        kep.write_bytes(_jpeg((250, 10, 10)))
        _nyisd_a_visszaallitast(window, qt_app, [0])
        kattints(window, qt_app, _gyerek(window, "revertOkButton"))
        figyelmeztetes = _gyerek(window, "revertChangedDialog")
        _var(qt_app, lambda: figyelmeztetes.property("opened") is True,
             "a külső módosítás figyelmeztetése nem jelent meg")

        wait_for_signal(
            controller.revertFinished,
            lambda: kattints(window, qt_app, _gyerek(window, "revertAnywayButton")),
            description="a Revert Anyway utáni visszaállítás",
            process_events_with=qt_app,
        )

        assert kep.read_bytes() == eredeti, "a Revert Anyway nem állította vissza a képet"
        assert figyelmeztetes.property("visible") is False

    def test_megse_nem_allit_vissza(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        kep, _eredeti = _fotok_mentese(qt_app, controller, [0])[0]
        kulso = _jpeg((250, 10, 10))
        kep.write_bytes(kulso)
        spy = QSignalSpy(controller.revertFinished)
        _nyisd_a_visszaallitast(window, qt_app, [0])
        kattints(window, qt_app, _gyerek(window, "revertOkButton"))
        figyelmeztetes = _gyerek(window, "revertChangedDialog")
        _var(qt_app, lambda: figyelmeztetes.property("opened") is True,
             "a külső módosítás figyelmeztetése nem jelent meg")

        kattints(window, qt_app, _gyerek(window, "revertChangedCancelButton"))
        _var(qt_app, lambda: figyelmeztetes.property("visible") is False,
             "a Mégse nem zárta be a figyelmeztetést")
        QTest.qWait(300)

        assert spy.count() == 0, "a Mégse után lefutott a visszaállítás"
        assert kep.read_bytes() == kulso, "a Mégse megváltoztatta a képet"

    def test_enter_a_figyelmeztetesben_nem_allit_vissza(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        kep, _eredeti = _fotok_mentese(qt_app, controller, [0])[0]
        kulso = _jpeg((250, 10, 10))
        kep.write_bytes(kulso)
        spy = QSignalSpy(controller.revertFinished)
        _nyisd_a_visszaallitast(window, qt_app, [0])
        kattints(window, qt_app, _gyerek(window, "revertOkButton"))
        figyelmeztetes = _gyerek(window, "revertChangedDialog")
        _var(qt_app, lambda: figyelmeztetes.property("opened") is True,
             "a külső módosítás figyelmeztetése nem jelent meg")
        window.requestActivate()
        _var(qt_app, lambda: window.isActive(), "a főablak nem aktiválódott")

        QTest.keyClick(window, Qt.Key.Key_Return)
        _var(qt_app, lambda: figyelmeztetes.property("visible") is False,
             "az Enter nem zárta be a figyelmeztetést")
        QTest.qWait(300)

        assert spy.count() == 0
        assert kep.read_bytes() == kulso

    def test_tobb_kepnel_a_tobbes_alak_jelenik_meg(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        fotok = _fotok_mentese(qt_app, controller, [0, 1])
        for kep, _eredeti in fotok.values():
            kep.write_bytes(_jpeg((250, 10, 10)))
        _nyisd_a_visszaallitast(window, qt_app, [0, 1])

        kattints(window, qt_app, _gyerek(window, "revertOkButton"))

        figyelmeztetes = _gyerek(window, "revertChangedDialog")
        _var(qt_app, lambda: figyelmeztetes.property("opened") is True,
             "a külső módosítás figyelmeztetése nem jelent meg")
        assert _gyerek(window, "revertChangedMessage").property("text") == _FORRAS_CHANGEDX

    def test_csak_a_modositott_kep_szamit_a_darabszamba(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        fotok = _fotok_mentese(qt_app, controller, [0, 1])
        fotok[1][0].write_bytes(_jpeg((250, 10, 10)))

        assert controller.externallyChangedCount([0, 1]) == 1
        assert controller.externallyChangedCount([0]) == 0
        assert controller.externallyChangedCount([2]) == 0
        _nyisd_a_visszaallitast(window, qt_app, [0, 1])
        _zard_be(window, qt_app, "revertConfirmDialog")

    def test_a_sajat_felirat_iras_nem_kulso_modositas(self, revert_app, qt_app):
        """A PicasaPy saját IPTC-írása a mentés után nem riaszt."""
        from picasapy.metadata import write_iptc_caption

        _window, controller, _engine = revert_app
        kep, _eredeti = _fotok_mentese(qt_app, controller, [0])[0]
        assert write_iptc_caption(kep, "Nyaralás")

        assert controller.externallyChangedCount([0]) == 0

    def test_visszaallitas_utan_nincs_tobbe_riasztas(self, revert_app, qt_app):
        window, controller, _engine = revert_app
        kep, _eredeti = _fotok_mentese(qt_app, controller, [0])[0]
        wait_for_signal(
            controller.revertFinished,
            lambda: controller.revertRowsToOriginal([0]),
            description="a visszaállítás",
            process_events_with=qt_app,
        )
        kep.write_bytes(_jpeg((250, 10, 10)))

        assert controller.externallyChangedCount([0]) == 0
        del window
