"""#1838: a három vágás-vezérlő a videó-sávon (`setin`/`setout`/`reset_trim`).

Forrás-szintű őr: a `VideoPlayerView.qml` a vágást **nem maga menti**, hanem
jelez, és a `PhotoViewer.qml` hívja a vezérlőt a sor indexével. A lap ezt a
láncot köti ki — a `QtMultimedia` miatt a komponenst gépi teszt itt nem tudja
betölteni (a CI-n nincs videó-dekódolás), ezért a kötések SZÖVEGÉT mérjük, és
ezt a korlátot kimondjuk.

A viselkedés mért oldala (mit írunk a `filters=` láncba) a
`test_videovagas_mentes_1838.py`-ban áll, valódi ini-írással.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_LEJATSZO = (_QML / "VideoPlayerView.qml").read_text(encoding="utf-8")
_NEZO = (_QML / "PhotoViewer.qml").read_text(encoding="utf-8")


class TestAHaromVezerlo:
    def test_mindharom_gomb_megvan(self):
        for nev in ("videoSetInButton", "videoSetOutButton", "videoResetTrimButton"):
            assert f'objectName: "{nev}"' in _LEJATSZO, nev

    def test_a_setin_a_JELENLEGI_poziciot_adja_kezdetnek(self):
        kezd = _LEJATSZO.index('objectName: "videoSetInButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert "player.trimRequested(media.position, player.trimEndMs)" in blokk

    def test_a_setout_a_masik_oldalt_valtozatlanul_viszi(self):
        kezd = _LEJATSZO.index('objectName: "videoSetOutButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert "player.trimRequested(player.trimStartMs, media.position)" in blokk

    def test_a_visszaallitas_vagas_nelkul_SZURKE(self):
        kezd = _LEJATSZO.index('objectName: "videoResetTrimButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert "enabled: player.trimmed" in blokk
        assert "player.trimResetRequested()" in blokk

    def test_a_ket_felirat_az_EREDETI_buboreksugoja(self):
        """A buboréksúgók az eredeti Picasa szövegei (`0x005952d0` környéke)."""
        assert 'ToolTip.text: qsTr("Create a new starting point")' in _LEJATSZO
        assert 'ToolTip.text: qsTr("Create a new ending point")' in _LEJATSZO

    def test_a_lejatszo_NEM_ir_inifajlt(self):
        """A komponens jelez; az írás a vezérlőé (rétegzés)."""
        assert "signal trimRequested(" in _LEJATSZO
        assert "signal trimResetRequested(" in _LEJATSZO
        # ⚠️ A puszta névre keresés VAK szabály volna: a komponens
        # docstringje nevesíti a két slotot, hogy olvasható legyen. A HÍVÁS
        # az, ami tilos — az minősített alakban állna.
        assert "controller.setMovieTrim" not in _LEJATSZO, (
            "a lejátszó közvetlenül hívja a vezérlőt — a gazda dolga"
        )
        assert "controller.resetMovieTrim" not in _LEJATSZO


class TestANezoKotiBe:
    def test_mindket_slot_hivasa_megvan(self):
        assert "controller.setMovieTrim(" in _NEZO
        assert "controller.resetMovieTrim(" in _NEZO

    def test_a_SOR_indexet_adja_at(self):
        kezd = _NEZO.index("controller.setMovieTrim(")
        assert "viewer.currentIndex" in _NEZO[kezd : kezd + 200]

    def test_a_kotes_a_REVISION_tol_is_fugg(self):
        """A `movieTrimAt` sima slot-hívás: enélkül a mentés után a lejátszó a
        régi szakaszt tartaná, és a vágás csak átnavigálás után élne."""
        kezd = _NEZO.index('property: "trimStartMs"')
        veg = _NEZO.index('property: "trimEndMs"', kezd)
        assert "photosModel.revision" in _NEZO[kezd:veg]

    def test_a_jelzes_csak_VIDEONAL_el(self):
        kezd = _NEZO.index("function onTrimRequested(")
        blokk = _NEZO[max(0, kezd - 500) : kezd]
        assert "viewer.isCurrentVideo" in blokk


class TestKepkockaGomb:
    """#1838: a `movieeditpanel/capture_frame` — „Take Snapshot".

    Ugyanaz a lánc, mint a vágásnál: a lejátszó JELEZ, a néző hívja a
    vezérlőt a sor indexével. A komponenst a `QtMultimedia` miatt itt sem
    tudjuk betölteni — a kötések SZÖVEGÉT mérjük (ld. a lap fejlécét).
    """

    def test_a_gomb_megvan(self):
        assert 'objectName: "videoCaptureFrameButton"' in _LEJATSZO

    def test_az_EPP_LATOTT_poziciot_adja_at(self):
        kezd = _LEJATSZO.index('objectName: "videoCaptureFrameButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert "player.captureFrameRequested(media.position)" in blokk

    def test_a_buboreksugo_az_EREDETIE(self):
        """`Tooltip(movieeditpanel/capture_frame)` — „Capture current frame"."""
        kezd = _LEJATSZO.index('objectName: "videoCaptureFrameButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert 'qsTr("Capture current frame")' in blokk

    def test_a_visszaallitas_buboreksugoja_is_az_EREDETIE(self):
        """A `reset_trim` súgója korábban saját fogalmazású volt („Reset
        trim"); az eredeti szövege a `.tre`-ből olvasva más."""
        assert (
            'qsTr("Restore movie to its original length '
            '(remove start and end points)")' in _LEJATSZO
        )

    def test_a_lejatszo_NEM_ir_fajlt(self):
        """A komponens jelez; a dekódolás és az írás a vezérlőé."""
        kezd = _LEJATSZO.index('objectName: "videoCaptureFrameButton"')
        blokk = _LEJATSZO[kezd : kezd + 600]
        assert "captureMovieFrame" not in blokk

    def test_a_nezo_a_SOR_indexevel_hivja_a_vezerlot(self):
        assert "function onCaptureFrameRequested(positionMs)" in _NEZO
        kezd = _NEZO.index("function onCaptureFrameRequested(positionMs)")
        blokk = _NEZO[kezd : kezd + 400]
        assert "controller.captureMovieFrame(" in blokk
        assert "viewer.currentIndex" in blokk

    def test_a_vegeredmeny_MINDKET_agon_latszik(self):
        """Siker és bukás is kap visszajelzést — a bukás nem lehet néma."""
        assert "function onMovieFrameCaptured(path)" in _NEZO
        assert "function onMovieFrameCaptureFailed()" in _NEZO
        assert 'qsTr("Failed to capture frame")' in _NEZO
        assert 'qsTr("Saved %1 to Captured Videos")' in _NEZO
