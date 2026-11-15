"""#6987: az E-mail parancs az eredeti Picasa 3.9 szerint (vezérlő-szint).

Az eredeti (`docs/specs/paritas-ellenorzes.md`, #6984):

- 20-nál több képnél megerősítő kérdés előzi meg az előkészítést
  (`CThumbUI::OutputBottleneck`, `0x00531550`); Mégse esetén nincs előkészítés;
- a saját levelezős ág (`EmailPrepType = 3`, `0x00742a2c`) belső szerkesztő
  nélkül adja át a csatolmányokat a rendszer levelezőjének;
- a tárgy és a törzs a képszám szerint töltődik (`0x0073d970`), a reklámsor
  (`IDS_MAPITAGLINE`) nélkül;
- a MAPI hibakódok a hivatalos szövegekkel jelennek meg, a felhasználói
  megszakítás csendes (`0x0073d8c0`).

A `]history:email` jelölés NINCS itt: nem ini-token, hanem az
`albumdata_token.pmp` album-sorának tokenje (`docs/specs/export-parbeszed.md`
13.9), amit a PicasaPy nem ír.

Valódi levelező nem indul: a `_which`/`_popen`/`_platform`/`_mapi_send`
modulszintű fogantyúkat cseréljük.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QSettings, QTranslator
from PySide6.QtGui import QGuiApplication

from picasapy.app import email_controller as email_module
from picasapy.app.email_controller import EmailController

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _fotok(mappa: Path, darab: int):
    return [
        SimpleNamespace(
            folder_path=str(mappa),
            name=f"{i}.jpg",
            rotate_steps=0,
            flip_flags=0,
            filters="",
            taken_at_override=None,
        )
        for i in range(darab)
    ]


def _vezerlo(tmp_path, darab=3, *, sajat_levelezo=True, talca=None):
    vezerlo = EmailController(
        photo_source=lambda: _fotok(tmp_path, darab),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        tray_source=(lambda: talca) if talca is not None else None,
    )
    vezerlo.setUseDefaultClient(sajat_levelezo)
    return vezerlo


def _xdg_argv(vezerlo, rows_vagy_utak, *, kuldes):
    """A kiadott `xdg-email` argumentumlista; valódi folyamat nem indul."""
    with patch.object(
        email_module, "_which", return_value="/usr/bin/xdg-email"
    ), patch.object(email_module, "_popen") as popen:
        popen.return_value.wait.return_value = 0
        kuldes()
    popen.assert_called_once()
    return popen.call_args[0][0]


def _ertek(argv, kapcsolo):
    return argv[argv.index(kapcsolo) + 1]


class TestMegerositesHuszFelett:
    """`CThumbUI::OutputBottleneck`: 20-nál több képnél kérdés, Mégse = semmi."""

    def test_21_kepnel_kerdez_es_nem_keszit_elo(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, 21)
        kerdesek = []
        vezerlo.sendConfirmRequested.connect(
            lambda sorok, db: kerdesek.append((list(sorok), db))
        )
        rows = list(range(21))
        with patch.object(
            email_module,
            "_mkdtemp",
            side_effect=AssertionError("kérdés előtt készült előkészítés"),
        ), patch.object(email_module, "_popen") as popen:
            vezerlo.sendSelection(rows, False)

        assert kerdesek == [(rows, 21)]
        popen.assert_not_called()

    def test_20_kepnel_nincs_kerdes_es_megy_az_eloekeszites(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, 20)
        kerdesek = []
        vezerlo.sendConfirmRequested.connect(
            lambda sorok, db: kerdesek.append(db)
        )
        rows = list(range(20))
        with patch.object(
            EmailController, "prepareAttachments", return_value=[]
        ) as elokeszit:
            vezerlo.sendSelection(rows, False)

        assert kerdesek == []
        elokeszit.assert_called_once()
        assert list(elokeszit.call_args[0][0]) == rows

    def test_jovahagyas_utan_a_21_kep_is_elokeszitodik(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, 21)
        kerdesek = []
        vezerlo.sendConfirmRequested.connect(
            lambda sorok, db: kerdesek.append(db)
        )
        with patch.object(
            EmailController, "prepareAttachments", return_value=[]
        ) as elokeszit:
            vezerlo.sendSelection(list(range(21)), True)

        assert kerdesek == []
        elokeszit.assert_called_once()

    def test_a_kepszamot_a_tenyleges_kimenet_adja_a_talca_elonyben(
        self, qt_app, tmp_path
    ):
        """Egy kijelölt kép, de 25 képnyi tálca: a 25 megy el, tehát a kérdés
        is 25-ről szól (`_resolve_records`: a tálca nyer)."""
        vezerlo = _vezerlo(tmp_path, 3, talca=_fotok(tmp_path, 25))
        kerdesek = []
        vezerlo.sendConfirmRequested.connect(
            lambda sorok, db: kerdesek.append(db)
        )
        with patch.object(EmailController, "prepareAttachments") as elokeszit:
            vezerlo.sendSelection([0], False)
        assert kerdesek == [25]
        elokeszit.assert_not_called()

    def test_az_elokeszites_eredmenytelen_nem_kuld_es_nem_kerdez(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, 2)
        with patch.object(
            EmailController, "prepareAttachments", return_value=[]
        ), patch.object(EmailController, "sendRows") as kuldes:
            vezerlo.sendSelection([0, 1], False)
        kuldes.assert_not_called()


class TestSajatLevelezoNincsBelsoPanel:
    """`EmailPrepType = 3`: az előkészítés után KÖZVETLENÜL a levelező nyílik."""

    def test_a_sajat_levelezo_modban_nem_nyilik_valaszto_vagy_szerkeszto(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, sajat_levelezo=True)
        kerdesek = []
        vezerlo.mailChoiceRequested.connect(
            lambda *args: kerdesek.append(args)
        )
        argv = _xdg_argv(
            vezerlo,
            None,
            kuldes=lambda: vezerlo.sendRows(["/tmp/a.jpg"], "", ""),
        )
        assert kerdesek == [], "a saját levelezős ág belső panelt nyitott"
        assert Path(_ertek(argv, "--attach")) == Path("/tmp/a.jpg")

    def test_a_kerdezz_mod_a_valaszto_dialogust_kerik_alapszovegekkel(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, sajat_levelezo=False)
        kerdesek = []
        vezerlo.mailChoiceRequested.connect(
            lambda utak, targy, szoveg: kerdesek.append(
                (list(utak), targy, szoveg)
            )
        )
        with patch.object(email_module, "_popen") as popen:
            eredmeny = vezerlo.sendRows(["/tmp/a.jpg", "/tmp/b.jpg"], "", "")
        assert eredmeny is False
        popen.assert_not_called()
        assert kerdesek == [
            (
                ["/tmp/a.jpg", "/tmp/b.jpg"],
                "2 pictures for you",
                "You have been sent 2 pictures.\n\n",
            )
        ]

    def test_a_kifejezetten_megadott_targy_es_szoveg_marad(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path, sajat_levelezo=True)
        argv = _xdg_argv(
            vezerlo,
            None,
            kuldes=lambda: vezerlo.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg"),
        )
        assert _ertek(argv, "--subject") == "Tárgy"
        assert _ertek(argv, "--body") == "Szöveg"


class TestTargyEsTorzsAKepszamSzerint:
    """`IDS_MAPI_SUBJ_*` / `IDS_MAPI_BODY_*`, a reklámsor nélkül."""

    @pytest.mark.parametrize(
        ("darab", "targy", "torzs"),
        [
            (1, "a picture for you", "You have been sent 1 picture.\n\n"),
            (2, "2 pictures for you", "You have been sent 2 pictures.\n\n"),
            (21, "21 pictures for you", "You have been sent 21 pictures.\n\n"),
        ],
    )
    def test_a_levelezonek_atadott_szovegek(
        self, qt_app, tmp_path, darab, targy, torzs
    ):
        vezerlo = _vezerlo(tmp_path)
        utak = [f"/tmp/{i}.jpg" for i in range(darab)]
        argv = _xdg_argv(
            vezerlo, None, kuldes=lambda: vezerlo.sendRows(utak, "", "")
        )
        assert _ertek(argv, "--subject") == targy
        assert _ertek(argv, "--body") == torzs

    def test_nincs_reklamsor_az_eredeti_idsmapitagline_nem_kerul_a_levelbe(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path)
        argv = _xdg_argv(
            vezerlo,
            None,
            kuldes=lambda: vezerlo.sendRows(["/tmp/a.jpg"], "", ""),
        )
        szoveg = " ".join(argv).lower()
        assert "picasa" not in szoveg
        assert "google" not in szoveg
        assert "try it out" not in szoveg

    def test_windowson_a_mapi_levelnek_is_kitoltott_a_targya(
        self, qt_app, tmp_path
    ):
        vezerlo = _vezerlo(tmp_path)
        with patch.object(
            email_module, "_platform", return_value="win32"
        ), patch.object(
            email_module, "_mapi_send", return_value=0
        ) as mapi:
            vezerlo.sendRows(["C:/a.jpg", "C:/b.jpg", "C:/c.jpg"], "", "")
        uzenet = mapi.call_args[0][0].message
        assert uzenet.lpszSubject == "3 pictures for you"
        assert uzenet.lpszNoteText == "You have been sent 3 pictures.\n\n"


class TestMapiHibakodok:
    """`0x0073d8c0`: külön hivatalos üzenet, a megszakítás csendes."""

    @pytest.mark.parametrize(
        ("kod", "uzenet"),
        [
            (9, "Too many file attachments to send."),
            (11, "Attachment was not found"),
            (12, "Could not open an attachment."),
            (14, "Unknown recipient."),
            (2, "The email could not be sent."),
            (26, "The email could not be sent."),
        ],
    )
    def test_a_hibakod_a_hivatalos_szoveget_jelzi(
        self, qt_app, tmp_path, kod, uzenet
    ):
        vezerlo = _vezerlo(tmp_path)
        esemenyek = []
        vezerlo.emailFailed.connect(esemenyek.append)
        with patch.object(
            email_module, "_platform", return_value="win32"
        ), patch.object(email_module, "_mapi_send", return_value=kod):
            ok = vezerlo.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert ok is False
        assert esemenyek == [uzenet]

    def test_a_felhasznaloi_megszakitas_csendes(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path)
        esemenyek = []
        vezerlo.emailFailed.connect(esemenyek.append)
        with patch.object(
            email_module, "_platform", return_value="win32"
        ), patch.object(
            email_module,
            "_mapi_send",
            return_value=email_module.MAPI_USER_ABORT,
        ):
            ok = vezerlo.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert ok is False
        assert esemenyek == []

    def test_a_mapi_betoltesi_hiba_marad_nincs_levelezoprogram(
        self, qt_app, tmp_path
    ):
        """Nem MAPI-kód, hanem a hívás maga hiúsult meg: nincs levelező."""
        vezerlo = _vezerlo(tmp_path)
        esemenyek = []
        vezerlo.emailFailed.connect(esemenyek.append)
        with patch.object(
            email_module, "_platform", return_value="win32"
        ), patch.object(
            email_module, "_mapi_send", side_effect=OSError("mapi32")
        ):
            vezerlo.sendWithDefaultClient(["C:/a.jpg"], "T", "Sz", False)
        assert esemenyek == ["No email program was found."]


#: (angol forrás, magyar hivatalos szöveg) - a `stringres.xml` szerint, a
#: literális `\n` valódi sortöréssé alakítva (az erőforrás-betöltő is így tesz).
_HIVATALOS_MAGYAR = {
    "a picture for you": "Küldök egy képet",
    "%d pictures for you": "Küldök %d képet",
    "You have been sent 1 picture.\n\n": "Ön 1 képet kapott.\n\n",
    "You have been sent %d pictures.\n\n": "Ön %d képet kapott.\n\n",
    "Attachment was not found": None,
    "Could not open an attachment.": None,
    "Too many file attachments to send.": None,
    "Unknown recipient.": None,
    "The email could not be sent.": None,
}

_UJ_EMAIL_FORRASOK = tuple(_HIVATALOS_MAGYAR)


def _ts_uzenetek(nyelv: str, kontextus: str) -> dict[str, str]:
    gyoker = ET.parse(_I18N / f"picasapy_{nyelv}.ts").getroot()
    ki: dict[str, str] = {}
    for ctx in gyoker.iter("context"):
        if ctx.findtext("name") != kontextus:
            continue
        for msg in ctx.iter("message"):
            fordit = msg.find("translation")
            if fordit is not None and fordit.get("type") != "unfinished":
                ki[msg.findtext("source") or ""] = fordit.text or ""
    return ki


class TestHivatalosForditasok:
    def test_a_magyar_szovegek_a_hivatalos_szotarbol_vannak(self, qt_app):
        fordito = QTranslator(qt_app)
        assert fordito.load(str(_I18N / "picasapy_hu.qm"))
        for forras, magyar in _HIVATALOS_MAGYAR.items():
            lefordtva = fordito.translate("EmailController", forras)
            assert lefordtva, f"nincs magyar fordítás: {forras!r}"
            if magyar is not None:
                assert lefordtva == magyar

    @pytest.mark.parametrize(
        "nyelv",
        [
            p.stem.removeprefix("picasapy_")
            for p in sorted(_I18N.glob("picasapy_*.ts"))
        ],
    )
    def test_mind_a_41_nyelvben_van_befejezett_fordítás(self, nyelv):
        uzenetek = _ts_uzenetek(nyelv, "EmailController")
        hianyzik = [f for f in _UJ_EMAIL_FORRASOK if not uzenetek.get(f)]
        assert not hianyzik, f"{nyelv}: hiányzó fordítás: {hianyzik}"
        # a törzs sortörései valódiak, nem literális `\n` karakterpár
        for forras in _UJ_EMAIL_FORRASOK:
            assert "\\n" not in uzenetek[forras], (nyelv, forras)

    def test_a_torzs_sortorese_a_lefordtott_nyelvben_is_megvan(self, qt_app):
        fordito = QTranslator(qt_app)
        assert fordito.load(str(_I18N / "picasapy_de.qm"))
        torzs = fordito.translate(
            "EmailController", "You have been sent %d pictures.\n\n"
        )
        assert torzs.endswith("\n\n")

    def test_a_forditatlan_alapszoveg_visszaadja_az_angolt(self, qt_app):
        assert (
            QCoreApplication.translate("EmailController", "Unknown recipient.")
            == "Unknown recipient."
        )
