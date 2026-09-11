"""#598: rétegzett bélyegkép-gyorsítótár — a szintek és a levezetés.

Az eredeti Picasa négy bélyegkép-tárat tartott, és a méretek a tulajdonos
saját Picasa-mentéséből **mérve** vannak (`docs/specs/pmp-database.md`):
72 · 144 · 288 · 640 képpont a hosszabb oldalon.

Nálunk a két kicsi szint jön át, a felső helyére a saját rács-maximum kerül
— a `szintek` modul docstringje kimondja, miért (a 288-as szint a felső
fokozatokon LASSABB nálunk, a 640-es előnézet pedig homályosabb, mint a
nézőnk, ami a fájlból tölt).

⚠️ Ez az őr a SZERKEZETET és a levezetést méri: hogy melyik szint mekkora,
hogy nagyítás sosem történik, és hogy a kis szint a nagyobb KÉSZ szintből
áll elő. A gördülés gyorsulását nem méri — azt a modul docstringjének
táblázata adja, mérésből.
"""

from __future__ import annotations

import numpy as np
import pytest
from picasapy.thumbs import szintek as sz
from picasapy.thumbs.cache import ThumbnailCache


class TestASzintek:
    def test_a_negy_MERT_picasa_szint(self):
        assert sz.PICASA_SZINTEK == (72, 144, 288, 640)

    def test_a_harom_belyegkep_szint_duplazodik(self):
        """A 72 → 144 → 288 pontos felezés — ez teszi olcsóvá a levezetést."""
        assert sz.NORMAL == 2 * sz.PINKY
        assert sz.NAGY == 2 * sz.NORMAL

    def test_a_mi_letranknak_a_teto_a_legnagyobb(self):
        assert sz.szintek(256) == (72, 144, 256)

    def test_a_tetonel_nem_kisebb_kis_szint_KIMARAD(self):
        """Két szint ne tárolja ugyanazt a képet."""
        assert sz.szintek(144) == (72, 144)
        assert sz.szintek(100) == (72, 100)
        assert sz.szintek(64) == (64,)

    @pytest.mark.parametrize(
        "cella,vart",
        [(16, 72), (72, 72), (73, 144), (144, 144), (145, 256), (256, 256)],
    )
    def test_a_cellahoz_a_legkisebb_ELEG_szint_jar(self, cella, vart):
        assert sz.szint_cellahoz(cella, 256) == vart

    def test_a_tetonel_nagyobb_cella_is_a_tetot_kapja(self):
        """Nagyítás helyett a legnagyobb, ami van — homályos kép sosem."""
        assert sz.szint_cellahoz(4000, 256) == 256

    @pytest.mark.parametrize("rossz", [0, -1])
    def test_ervenytelen_meretet_elutasit(self, rossz):
        with pytest.raises(ValueError):
            sz.szintek(rossz)
        with pytest.raises(ValueError):
            sz.szint_cellahoz(rossz, 256)


def _kep(utvonal, szeles=800, magas=600):
    import cv2

    kep = np.zeros((magas, szeles, 3), np.uint8)
    kep[:, :, 1] = np.linspace(0, 255, szeles, dtype=np.uint8)[None, :]
    cv2.imwrite(str(utvonal), kep)
    return utvonal


class TestATar:
    @pytest.fixture
    def tar(self, tmp_path):
        return ThumbnailCache(tmp_path / "thumbs", size=256)

    def test_a_tar_szintjei(self, tar):
        assert tar.levels == (72, 144, 256)

    def test_a_FELSO_szint_utvonala_VALTOZATLAN(self, tar, tmp_path):
        """A meglévő gyorsítótár érvényes marad — százezres könyvtárnál az
        újraépítés órákba kerülne."""
        ut = tar.thumbnail_path(tmp_path / "a.jpg", 1, 2)
        assert ut.parent.parent == tmp_path / "thumbs"

    def test_a_kis_szintek_KULON_mappaba_mennek(self, tar, tmp_path):
        """Így a takarító szintenként is tud dolgozni."""
        ut = tar.thumbnail_path(tmp_path / "a.jpg", 1, 2, 72)
        assert ut.parent.parent == tmp_path / "thumbs" / "sz72"

    def test_ket_szint_KULON_fajlba_ir(self, tar, tmp_path):
        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        kicsi = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, 72)
        nagy = tar.get_or_create(forras, st.st_mtime_ns, st.st_size)
        assert kicsi is not None and nagy is not None
        assert kicsi != nagy

    def test_a_szint_MERETE_a_hosszabb_oldalon_all(self, tar, tmp_path):
        import cv2

        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        for szint, vart in ((72, 72), (144, 144), (None, 256)):
            ut = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, szint)
            kep = cv2.imread(str(ut))
            assert max(kep.shape[:2]) == vart

    def test_a_kepARANY_megmarad(self, tar, tmp_path):
        import cv2

        forras = _kep(tmp_path / "k.jpg", 800, 600)
        st = forras.stat()
        ut = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, 72)
        kep = cv2.imread(str(ut))
        assert kep.shape[1] / kep.shape[0] == pytest.approx(800 / 600, rel=0.02)

    def test_a_kis_szint_a_KESZ_nagyobbikbol_all_elo(self, tar, tmp_path):
        """A nyereség forrása: a forrásfotót nem dekódoljuk újra.

        A mérés úgy megy, hogy a forrásfájlt a nagy szint elkészítése UTÁN
        kicseréljük olvashatatlanra — ha a kis szint mégis elkészül, csakis
        a kész nagy szintből dolgozhatott."""
        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        assert tar.get_or_create(forras, st.st_mtime_ns, st.st_size) is not None
        forras.write_bytes(b"ez nem JPEG")
        kicsi = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, 72)
        assert kicsi is not None and kicsi.exists()

    def test_ismeretlen_szintet_a_LETRARA_kerekit(self, tar, tmp_path):
        """Elgépelt szám különben néma, sosem találatot adó negyedik tárat
        nyitna."""
        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        ut = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, 100)
        assert ut == tar.thumbnail_path(forras, st.st_mtime_ns, st.st_size, 144)

    def test_a_szint_nelkuli_hivas_a_REGI_viselkedes(self, tar, tmp_path):
        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        a = tar.get_or_create(forras, st.st_mtime_ns, st.st_size)
        b = tar.get_or_create(forras, st.st_mtime_ns, st.st_size, 256)
        assert a == b


class TestAzUrites:
    def test_a_torles_MINDEN_szintet_erint_es_meri_a_helyet(self, tmp_path):
        forras = _kep(tmp_path / "k.jpg")
        st = forras.stat()
        tar = ThumbnailCache(tmp_path / "thumbs", size=256)
        utak = [
            tar.get_or_create(forras, st.st_mtime_ns, st.st_size, szint)
            for szint in (72, 144, None)
        ]
        assert all(ut is not None and ut.exists() for ut in utak)
        vart = sum(ut.stat().st_size for ut in utak)
        assert tar.clear() == vart
        assert not any(ut.exists() for ut in utak)

    def test_ures_taron_nulla(self, tmp_path):
        assert ThumbnailCache(tmp_path / "nincs", size=256).clear() == 0
