"""A kollázs automatikus mentése és helyreállítása — #431.

## Mit őriz ez a fájl

A Picasa a kollázs szerkesztése közben folyamatosan írt egy `autosave.cxf`-et
(`CAutosaveCollageThread`), és összeomlás után felajánlotta a visszaállítást
(`collage::recoveredautosave` / `lastautosave`) — a felhasználó munkája sosem
veszett el (`docs/specs/picasa-create-features.md` 1.5 és 4/3).

A helyreállítás értéke azon áll vagy bukik, hogy **a mentés maga ne tudja
tönkretenni a korábbi piszkozatot**. Ezért a lényeg nem a „le van írva a
fájl", hanem három sarokeset:

1. **Atomi írás** — félbeszakadt mentés után a RÉGI piszkozat maradjon meg
   épen. Enélkül pont az összeomlás vinné el azt, amit meg akarunk menteni.
2. **Sérült fájl nem dönti be az indulást** — a helyreállítás egy összeomlás
   UTÁN fut, amikor a fájl fél kézzel írt csonk is lehet. Kivétel helyett
   „nincs visszaállítható piszkozat" a helyes válasz.
3. **A körbejárás megőrzi a képenkénti `theta`/`scale`-t** — a kupac
   elrendezése nem determinisztikus, ezért csak ez adja vissza pontosan.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from picasapy.collage.autosave import (
    AUTOSAVE_NAME,
    autosave_path,
    discard_autosave,
    has_recoverable_draft,
    read_autosave,
    write_autosave,
)
from picasapy.collage.cxf import CxfBackground, CxfNode, CxfProject


def _project(theta: float = 0.4, scale: float = 512.0) -> CxfProject:
    """Kétképes kupac — a képenkénti szög és méret a lényeg."""
    return CxfProject(
        aspect_ratio="15:10",
        orientation="portrait",
        theme="picturepile",
        shadows=True,
        captions=True,
        album_uid="a4ef8e0fd2dbb152d25d79eb2bd2a28b",
        album_title="Nyaralás",
        album_date="2023. november",
        background=CxfBackground(type="solid", color="FF203040"),
        spacing=0.25,
        nodes=(
            CxfNode(
                x=0.25, y=0.5, w=0.3, h=0.2, theta=theta, scale=scale,
                theme="polaroid", src=r"$My Pictures\Nyaralás\elso.jpg",
            ),
            CxfNode(
                x=0.75, y=0.5, w=0.3, h=0.2, theta=-theta, scale=scale * 2,
                theme="whiteborder", src=r"$My Pictures\Nyaralás\masodik.jpg",
            ),
        ),
    )


class TestAKorbejaras:
    """Írás → olvasás: a piszkozat maradéktalanul visszajön."""

    def test_a_kiirt_piszkozat_visszaolvasva_azonos(self, tmp_path):
        eredeti = _project()
        write_autosave(tmp_path, eredeti)

        visszaolvasott = read_autosave(tmp_path)

        assert visszaolvasott == eredeti

    def test_a_kepenkenti_szog_es_meret_megmarad(self, tmp_path):
        # a kupac elrendezése nem determinisztikus: ha ez elveszik, a
        # helyreállított kollázs MÁSHOGY néz ki, mint amit a felhasználó hagyott
        write_autosave(tmp_path, _project(theta=1.2345, scale=777.0))

        visszaolvasott = read_autosave(tmp_path)

        assert visszaolvasott is not None
        assert visszaolvasott.nodes[0].theta == pytest.approx(1.2345, abs=1e-5)
        assert visszaolvasott.nodes[0].scale == pytest.approx(777.0, abs=1e-5)
        assert visszaolvasott.nodes[1].theta == pytest.approx(-1.2345, abs=1e-5)

    def test_a_fajl_neve_a_Picasaval_egyezik(self, tmp_path):
        utvonal = write_autosave(tmp_path, _project())

        assert utvonal.name == AUTOSAVE_NAME == "autosave.cxf"
        assert autosave_path(tmp_path) == utvonal


class TestAzAtomiIras:
    """A mentés nem teheti tönkre a korábbi piszkozatot."""

    def test_iras_utan_nem_marad_ideiglenes_fajl(self, tmp_path):
        write_autosave(tmp_path, _project())

        maradek = [p.name for p in tmp_path.iterdir() if p.name != AUTOSAVE_NAME]

        assert maradek == [], f"ideiglenes fájl maradt hátra: {maradek}"

    def test_felbeszakadt_iras_utan_a_REGI_piszkozat_ep_marad(
        self, tmp_path, monkeypatch
    ):
        # az első, sikeres mentés — ezt kell megvédeni
        write_autosave(tmp_path, _project(theta=0.4))

        # a második mentés a végleges helyre mozgatás előtt elszáll
        def _elszall(*args, **kwargs):
            raise OSError("szimulált összeomlás mentés közben")

        monkeypatch.setattr("picasapy.collage.autosave.os.replace", _elszall)
        with pytest.raises(OSError):
            write_autosave(tmp_path, _project(theta=9.9))

        # a RÉGI piszkozat változatlanul olvasható
        visszaolvasott = read_autosave(tmp_path)
        assert visszaolvasott is not None
        assert visszaolvasott.nodes[0].theta == pytest.approx(0.4, abs=1e-5)

    def test_a_felbeszakadt_iras_nem_hagy_szemetet(self, tmp_path, monkeypatch):
        write_autosave(tmp_path, _project())

        def _elszall(*args, **kwargs):
            raise OSError("szimulált összeomlás mentés közben")

        monkeypatch.setattr("picasapy.collage.autosave.os.replace", _elszall)
        with pytest.raises(OSError):
            write_autosave(tmp_path, _project(theta=9.9))

        maradek = [p.name for p in tmp_path.iterdir() if p.name != AUTOSAVE_NAME]
        assert maradek == [], f"ideiglenes fájl maradt hátra: {maradek}"


class TestAHelyreallitasSosemDobKivetelt:
    """A helyreállítás összeomlás UTÁN fut — ott nem szabad elszállni."""

    def test_nincs_piszkozat(self, tmp_path):
        assert read_autosave(tmp_path) is None
        assert has_recoverable_draft(tmp_path) is False

    def test_serult_fajl_eseten_nincs_piszkozat_a_valasz(self, tmp_path):
        # csonk: pont az, ami egy összeomlás után marad
        autosave_path(tmp_path).write_bytes(
            b'<?xml version="1.0" encoding="utf-8" ?>\r\n<collage version="2"'
        )

        assert read_autosave(tmp_path) is None
        assert has_recoverable_draft(tmp_path) is False

    def test_nem_letezo_mappa_eseten_sem_szall_el(self, tmp_path):
        hianyzo = tmp_path / "nincs" / "ilyen"

        assert read_autosave(hianyzo) is None
        assert has_recoverable_draft(hianyzo) is False

    def test_ep_piszkozatra_igent_mond(self, tmp_path):
        """⚠️ #1064: az „ép" azóta TÖBBET jelent — legalább egy képnek
        léteznie is kell, különben a visszaállítás csupa helykitöltőt adna
        (`CollageUI::AllImagesMissing`, spec 9.3). A `_project()` mintája
        Picasa-relatív útvonalakat tárol (`$My Pictures\…`), amik itt nem
        léteznek; ezért kap a piszkozat egy VALÓDI képet."""
        valodi = tmp_path / "elso.jpg"
        valodi.write_bytes(b"nem valodi JPEG, de LETEZIK")
        projekt = _project()
        projekt = replace(
            projekt,
            nodes=(replace(projekt.nodes[0], src=str(valodi)),) + projekt.nodes[1:],
        )
        write_autosave(tmp_path, projekt)

        assert has_recoverable_draft(tmp_path) is True

    def test_kepek_nelkuli_piszkozatra_NEMET_mond(self, tmp_path):
        """A #1064 másik fele: a beolvashatóság önmagában nem elég."""
        write_autosave(tmp_path, _project())

        assert has_recoverable_draft(tmp_path) is False


class TestAPiszkozatEldobasa:
    """Sikeres mentés (vagy a felhasználó nemet mond) után eltűnik."""

    def test_eldobas_utan_nincs_piszkozat(self, tmp_path):
        write_autosave(tmp_path, _project())

        assert discard_autosave(tmp_path) is True
        assert has_recoverable_draft(tmp_path) is False
        assert not autosave_path(tmp_path).exists()

    def test_az_eldobas_ismetelheto(self, tmp_path):
        # a felhasználó kétszer is nemet mondhat, és a mentés is eldobja —
        # a másodiknak nem szabad elszállnia
        write_autosave(tmp_path, _project())
        discard_autosave(tmp_path)

        assert discard_autosave(tmp_path) is False

    def test_a_serult_piszkozat_is_eldobhato(self, tmp_path):
        autosave_path(tmp_path).write_bytes(b"csonk")

        assert discard_autosave(tmp_path) is True
        assert not autosave_path(tmp_path).exists()
