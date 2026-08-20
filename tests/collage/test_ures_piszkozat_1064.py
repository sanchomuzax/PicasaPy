"""A piszkozat-felajánlás csak akkor jár, ha van mit visszatölteni (#1064).

## A lelet

A #1051 óta a program induláskor felajánlja a piszkozat visszaállítását. A
feltétel eddig annyi volt, hogy a `.cxf` **beolvasható** legyen — azt nem
néztük meg, hogy a benne hivatkozott képek **léteznek-e**.

Egy olyan piszkozatra is felajánlotta tehát a visszaállítást, aminek
egyetlen képe sem található; a felhasználó rábólint, és csupa helykitöltő
csempéből álló lapot kap.

## Az eredeti szabálya

`CollageUI::AllImagesMissing` (spec 9.3):

> „A kollázs nem szerkeszthető, mert a benne hivatkozott képek egyike sem
> található."

Ha nem szerkeszthető, felajánlani sincs értelme.

## A határ: LEGALÁBB EGY kép

A részleges visszaállítás **értékes** — a hiányzók helykitöltőként
jelennek meg (spec 9.4), a többi munka viszont megmarad. Ezért a szabály
nem „minden kép meglegyen", hanem „**legalább egy**".

## Amit szándékosan NEM teszünk

A nem visszaállítható piszkozatot **nem töröljük**. A felhasználó fájlját
némán eldobni rosszabb, mint egy elmaradt felajánlás — és ha a képek
visszakerülnek a helyükre (visszacsatolt meghajtó, visszaállított mappa),
a piszkozat magától újra érvényes lesz.
"""

from __future__ import annotations

from picasapy.collage.autosave import (
    AUTOSAVE_NAME,
    has_recoverable_draft,
    write_autosave,
)
from picasapy.collage.cxf import CxfBackground, CxfNode, CxfProject


def _projekt(*forrasok: str) -> CxfProject:
    return CxfProject(
        aspect_ratio="4:3",
        orientation="landscape",
        theme="picturepile",
        shadows=True,
        captions=False,
        album_uid="a4ef8e0fd2dbb152d25d79eb2bd2a28b",
        album_title="",
        album_date="",
        background=CxfBackground(type="solid", color="FFFFFFFF"),
        spacing=0.0,
        nodes=tuple(
            CxfNode(
                x=0.1 + 0.2 * i, y=0.5, w=0.2, h=0.2, theta=0.0, scale=200.0,
                theme="noborder", src=forras,
            )
            for i, forras in enumerate(forrasok)
        ),
    )


def _kep(mappa, nev: str) -> str:
    ut = mappa / nev
    ut.write_bytes(b"nem valodi JPEG, de LETEZIK")
    return str(ut)


class TestAFelajanlasFeltetele:
    def test_minden_kep_hianyzik_NINCS_felajanlas(self, tmp_path):
        """⚠️ Ez a jegy: eddig felajánlotta, és a felhasználó üres lapot kapott."""
        write_autosave(
            tmp_path,
            _projekt(str(tmp_path / "nincs1.jpg"), str(tmp_path / "nincs2.jpg")),
        )

        assert has_recoverable_draft(tmp_path) is False

    def test_EGY_kep_is_eleg_a_felajanlashoz(self, tmp_path):
        """A részleges visszaállítás értékes: a hiányzók helykitöltők lesznek."""
        write_autosave(
            tmp_path,
            _projekt(_kep(tmp_path, "van.jpg"), str(tmp_path / "nincs.jpg")),
        )

        assert has_recoverable_draft(tmp_path) is True

    def test_minden_kep_megvan_van_felajanlas(self, tmp_path):
        write_autosave(
            tmp_path, _projekt(_kep(tmp_path, "a.jpg"), _kep(tmp_path, "b.jpg"))
        )

        assert has_recoverable_draft(tmp_path) is True

    def test_csomopont_nelkuli_piszkozatra_NINCS_felajanlas(self, tmp_path):
        """Nincs mit visszatölteni — a `.cxf` beolvasható, de üres."""
        write_autosave(tmp_path, _projekt())

        assert has_recoverable_draft(tmp_path) is False

    def test_serult_piszkozatra_tovabbra_sincs(self, tmp_path):
        (tmp_path / AUTOSAVE_NAME).write_bytes(b"<collage")

        assert has_recoverable_draft(tmp_path) is False


class TestAPiszkozatMEGMARAD:
    """A nem visszaállítható piszkozatot NEM dobjuk el magától."""

    def test_a_fajl_a_helyen_marad(self, tmp_path):
        write_autosave(tmp_path, _projekt(str(tmp_path / "nincs.jpg")))

        has_recoverable_draft(tmp_path)

        assert (tmp_path / AUTOSAVE_NAME).exists()

    def test_a_kep_visszaterese_ujra_ervenyesse_teszi(self, tmp_path):
        """Visszacsatolt meghajtó, visszaállított mappa: a piszkozat éled."""
        forras = tmp_path / "kesobb.jpg"
        write_autosave(tmp_path, _projekt(str(forras)))
        assert has_recoverable_draft(tmp_path) is False

        forras.write_bytes(b"most mar itt van")

        assert has_recoverable_draft(tmp_path) is True
