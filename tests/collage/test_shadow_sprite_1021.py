"""Az élő vászon árnyék-csempéje — #1021.

A #977 az árnyékot a **magba** építette be, így a MENTETT kép témánként
helyes árnyékot kap. Az élő vászon (QML jelenetgráf) viszont változatlan
maradt: a felhasználó kapcsolgatta a jelölőnégyzetet, és nem történt semmi.

## Miért CSEMPE, és nem shader

A kézenfekvő út a `QtQuick.Effects.MultiEffect` volna. Mérve **nem
járható**: a felhasználó gépén (Debian, disztribúciós PySide6 6.8.2) a
modul nincs telepítve —

    module "QtQuick.Effects" is not installed

—, a CI pedig `pip install PySide6`-ot használ, ahol MEGVAN. Egy
`MultiEffect`-es megoldás tehát **zöld CI mellett hagyná feketén** a
felhasználó vásznát. Ez pontosan az a néma eltérés, amit a projekt kerül.

## Amit ez a lap bizonyít

A vetett árnyék **szeparábilis** elmosás egy téglalapon (spec 9/b.1: „külön
X és Y irányú lecsengés szorzata"). Egy ilyen kép **kilenc szeletre bontva
pontosan újraépíthető**: a sarkok változatlanul, az élek egy tengelyen
nyújtva (ott a profil állandó), a közép telített. Ezt csinálja a QML
`BorderImage`.

Ez a lap azt méri, hogy a kilenc szeletből visszaépített kép **megegyezik a
mag `draw_shadow`-jával** — tehát a vászon és a mentett kép nem mondhat
ellent egymásnak. Beégetett kivonat sehol (#942): minden állítás tűréssel
mér.
"""

from __future__ import annotations

import base64
import math

import cv2
import numpy as np
import pytest

from picasapy.collage.shadow import ShadowParams, draw_shadow
from picasapy.collage.shadow_sprite import (
    BLUR_QUANTUM,
    SPRITE_MIDDLE,
    sprite_alpha_map,
    sprite_border,
    sprite_data_url,
    sprite_side,
    sprite_support,
)

#: A vásznon előforduló nagyságrendek: a lapegységben mért 8–10 elmosás a
#: tipikus panelméreten 4–6 képpontra jön ki.
PROBA_ELMOSASOK = (2.0, 3.0, 5.0, 12.0)


def _kilenc_szelet(sprite: np.ndarray, tamasz: int, cel_w: int, cel_h: int):
    """A `BorderImage` `Stretch` viselkedésének numpyos mása.

    Nem a Qt-t utánozzuk kedvtelésből: ez az a leképezés, amit a vásznon a
    jelenetgráf végez, és amit itt a maggal össze kell vetni."""
    b = 2 * tamasz
    ki = np.zeros((cel_h, cel_w), dtype=np.uint8)
    sh, sw = sprite.shape
    ki[:b, :b] = sprite[:b, :b]
    ki[:b, cel_w - b :] = sprite[:b, -b:]
    ki[cel_h - b :, :b] = sprite[-b:, :b]
    ki[cel_h - b :, cel_w - b :] = sprite[-b:, -b:]
    kozep_w, kozep_h = cel_w - 2 * b, cel_h - 2 * b
    nyujt = cv2.INTER_LINEAR
    ki[:b, b : cel_w - b] = cv2.resize(sprite[:b, b : sw - b], (kozep_w, b), interpolation=nyujt)
    ki[cel_h - b :, b : cel_w - b] = cv2.resize(
        sprite[-b:, b : sw - b], (kozep_w, b), interpolation=nyujt
    )
    ki[b : cel_h - b, :b] = cv2.resize(
        sprite[b : sh - b, :b], (b, kozep_h), interpolation=nyujt
    )
    ki[b : cel_h - b, cel_w - b :] = cv2.resize(
        sprite[b : sh - b, -b:], (b, kozep_h), interpolation=nyujt
    )
    ki[b : cel_h - b, b : cel_w - b] = cv2.resize(
        sprite[b : sh - b, b : sw - b], (kozep_w, kozep_h), interpolation=nyujt
    )
    return ki


def _mag_alfaja(blur: float, alfa: int, szeles: int, magas: int) -> np.ndarray:
    """A mag `draw_shadow`-ja FEHÉR vászonra, alfa-térképpé visszafejtve."""
    params = ShadowParams(offset_x=0.0, offset_y=0.0, blur=blur, opacity=alfa / 256.0)
    vaszon = np.full((magas + 200, szeles + 200, 3), 255, np.uint8)
    draw_shadow(
        vaszon, x=100, y=100, width=szeles, height=magas, theta=0.0, params=params
    )
    return 255.0 - vaszon[..., 0].astype(np.float32)


class TestAHalo:
    @pytest.mark.parametrize("blur", PROBA_ELMOSASOK)
    def test_a_halo_a_mag_novekmenyevel_egyezik(self, blur):
        """A csempe halója UGYANAZ a szám, amivel a mag bővíti a befoglalót.

        A mag `bounds_growth`-a `elmosás · 1,5`, és `draw_shadow` ennyivel
        keretezi ki a sziluettet. Ha a vászon halója ettől eltérne, az
        árnyék más messzire érne el, mint a mentett képen."""
        params = ShadowParams(offset_x=0, offset_y=0, blur=blur, opacity=0.4)
        assert sprite_support(blur) == max(1, math.ceil(params.bounds_growth))

    @pytest.mark.parametrize("blur", PROBA_ELMOSASOK)
    def test_a_szegely_a_TELJES_atmenetet_lefedi(self, blur):
        """A `BorderImage` szegélye kétszer a haló — és ez nem ráhagyás.

        Az átmenet a csempe éle KÖRÜL zajlik: a haló befelé és kifelé is
        ennyi. Ha a szegély csak egyszeres volna, a nyújtott középső sáv
        nem telített képpontokat nyújtana, és az árnyék a nagy csempéken
        elmosódott csíkot kapna."""
        assert sprite_border(blur) == 2 * sprite_support(blur)

    @pytest.mark.parametrize("blur", PROBA_ELMOSASOK)
    def test_a_csempe_merete_a_szegelybol_es_a_kozepbol_all(self, blur):
        kep = sprite_alpha_map(blur, 153)
        oldal = 2 * sprite_border(blur) + SPRITE_MIDDLE
        assert kep.shape == (oldal, oldal)


class TestARaszter:
    """Az elmosás huszad-képpontos rasztere — és hogy MINDENRE érvényes.

    Az ablak átméretezésekor az elmosás folytonosan változik; raszter
    nélkül minden képkocka új PNG-t és új textúra-betöltést szülne. A
    veszély viszont az, hogy a raszter CSAK az URL-re érvényesül: akkor a
    haló a nyers, a kép a kerekített elmosásból születne, a szegély nem
    illeszkedne a saját csempéjéhez, és az árnyék eltorzulna."""

    @pytest.mark.parametrize("blur", (5.0, 5.01, 5.02, 5.024))
    def test_a_raszteren_beluli_ertekek_UGYANAZT_adjak(self, blur):
        assert sprite_data_url(blur, 153) == sprite_data_url(5.0, 153)
        assert sprite_support(blur) == sprite_support(5.0)

    @pytest.mark.parametrize("blur", (0.0, 0.7, 3.33, 6.049, 9.999, 20.0))
    def test_a_csempe_merete_a_sajat_szegelyehez_illeszkedik(self, blur):
        """A csempe éle PONTOSAN két szegély és a közép — tetszőleges,
        nem raszterre eső elmosásnál is."""
        kep = sprite_alpha_map(blur, 153)
        assert kep.shape == (sprite_side(blur), sprite_side(blur))
        assert sprite_side(blur) == 2 * sprite_border(blur) + SPRITE_MIDDLE
        assert BLUR_QUANTUM > 0


class TestAzEgyezesAMaggal:
    @pytest.mark.parametrize("blur", PROBA_ELMOSASOK)
    @pytest.mark.parametrize("alfa", (102, 153))
    def test_a_kilenc_szelet_visszaadja_a_mag_arnyekat(self, blur, alfa):
        """A jegy szíve: a vászon és a mentett kép nem mondhat ellent.

        A tűrés 2/255 — nem beégetett kivonat, hanem a 3·szórásos támasz
        csonkolásának a hibája (a telített közép 0,9987-en áll, nem 1,0-n)."""
        szeles, magas = 120, 90
        tamasz = sprite_support(blur)
        mag = _mag_alfaja(blur, alfa, szeles, magas)
        rek = np.zeros_like(mag)
        cel_w, cel_h = szeles + 2 * tamasz, magas + 2 * tamasz
        rek[
            100 - tamasz : 100 - tamasz + cel_h, 100 - tamasz : 100 - tamasz + cel_w
        ] = _kilenc_szelet(sprite_alpha_map(blur, alfa), tamasz, cel_w, cel_h)
        elteres = np.abs(mag - rek)
        assert elteres.max() <= 2.0, (
            f"a vászon árnyéka {elteres.max():.1f}/255-tel tér el a mentettétől "
            f"(elmosás={blur}, alfa={alfa})"
        )

    def test_az_erosebb_alfa_sotetebb_csempet_ad(self):
        """A Rács/Indexkép 153-as alfája ténylegesen sötétebb a 102-esnél.

        Ez az az állítás, ami egyetlen KÖZÖS paraméterkészlettel megbukna
        — a #977 legkönnyebben elrontható száma."""
        gyenge = sprite_alpha_map(5.0, 102).max()
        eros = sprite_alpha_map(5.0, 153).max()
        assert eros > gyenge + 30, f"{eros} nem elég sötétebb {gyenge}-nál"

    def test_a_nulla_alfa_ures_csempet_ad(self):
        assert sprite_alpha_map(5.0, 0).max() == 0


class TestAzAdatURL:
    def test_a_data_url_visszafejtheto_PNG(self):
        """A csempe `data:` URL-ként megy a QML-nek — külön képszolgáltató
        nélkül, tehát bármelyik motorban működik (a teszt-QQuickView-ban
        is, ahol nincs regisztrált szolgáltató)."""
        url = sprite_data_url(5.0, 153)
        elotag = "data:image/png;base64,"
        assert url.startswith(elotag)
        nyers = base64.b64decode(url[len(elotag) :])
        kep = cv2.imdecode(np.frombuffer(nyers, np.uint8), cv2.IMREAD_UNCHANGED)
        assert kep is not None and kep.shape[2] == 4, "a csempének alfája van"
        oldal = 2 * sprite_border(5.0) + SPRITE_MIDDLE
        assert kep.shape[:2] == (oldal, oldal)
        # a szín FEKETE, az információ az alfában van
        assert kep[..., :3].max() == 0

    def test_a_PNG_alfaja_a_szamolt_terkep(self):
        url = sprite_data_url(4.0, 102)
        nyers = base64.b64decode(url.split(",", 1)[1])
        kep = cv2.imdecode(np.frombuffer(nyers, np.uint8), cv2.IMREAD_UNCHANGED)
        assert np.array_equal(kep[..., 3], sprite_alpha_map(4.0, 102))

    def test_ugyanaz_a_keres_ugyanazt_az_URL_t_adja(self):
        """A csempét 350 csomópont OSZTJA — ha a szöveg nem azonos, a Qt
        350 külön textúrát töltene be ugyanabból a képből."""
        assert sprite_data_url(5.0, 153) == sprite_data_url(5.0, 153)

    def test_az_URL_kicsi_marad(self):
        """A vászonra jellemző elmosásnál a csempe pár száz bájt.

        Nem esztétika: a `data:` URL a QML property-n megy át, és minden
        átméretezéskor újraszületik."""
        assert len(sprite_data_url(6.0, 153)) < 4096
