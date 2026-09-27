"""A második előnézet ÖNÁLLÓ szerkesztési állapota (#3187, 1. lépés).

A kettős nézet második fele ma a NYERS fájlt mutatja: nálunk egyetlen
szerkesztési állapot van. A #3014 mérése szerint az eredetiben teljes
értékű második előnézet áll (`editpanel/preview2`, `previewclip2`), saját
láncal — a #3014 ütközés-párbeszéde (`Confirm2up*`) épp attól kap
értelmet, hogy a két oldal KÜLÖN állapotot vehet fel.

Ez a lépés a HÁTTERET adja hozzá: az `EditController` egy „rekeszt"
(`slot`) kap, és minden előnézet-szolgáltatós művelete a rekeszes kulcson
megy. Két vezérlő így UGYANARRA a fotóra is tud két független
szerkesztési állapotot tartani — enélkül a második oldal lánca felülírná
az elsőét a szolgáltató gyorsítótárában (a kulcs a fotó azonosítója).

A felület bekötése (melyik oldal melyik rekeszt mutatja, a parancsok
irányítása) a jegy KÖVETKEZŐ lépése; itt még semmi nem változik a
képernyőn.
"""

from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg

FORRAS = Path(__file__).resolve().parents[2] / "src/picasapy/app/edit_controller.py"


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _van_kep(provider, kulcs):
    """A szolgáltató tárában áll-e kép ezen a kulcson.

    Nincs rá nyilvános lekérdező, és nem is kell: a tesztnek pont a
    KULCSOZÁS a tárgya, ezért a tárat nézzük közvetlenül."""
    return kulcs in provider._images


def _controller(provider, slot=""):
    from picasapy.app.edit_controller import EditController

    return EditController(provider, slot=slot) if slot else EditController(provider)


class TestARekeszKulcs:
    """A rekesz nélküli vezérlő viselkedése VÁLTOZATLAN."""

    def test_rekesz_nelkul_a_kulcs_a_fotoazonosito(self, provider, photo):
        ctl = _controller(provider)
        ctl.beginEdit("42", str(photo))
        assert ctl.previewSource.startswith("image://editpreview/42?rev=")

    def test_rekesszel_a_kulcs_megjelolt(self, provider, photo):
        ctl = _controller(provider, slot="masodik")
        ctl.beginEdit("42", str(photo))
        assert ctl.previewSource.startswith("image://editpreview/42@masodik?rev=")

    def test_a_gpu_urlek_is_a_rekeszes_kulcsot_viszik(self, provider, photo):
        """A `gpuprefix=1`/`gpulut=1` ág ugyanabból a kulcsból épül.

        Üres láncon a finetune2 a lánc végére kerülne, tehát a
        GPU-előnézet alkalmas — ez a #22 tesztjének bejáratott alapja."""
        ctl = _controller(provider, slot="masodik")
        ctl.beginEdit("42", str(photo))
        assert ctl.gpuPrefixSource.startswith("image://editpreview/42@masodik?gpuprefix=1")
        assert ctl.gpuLutSource.startswith("image://editpreview/42@masodik?gpulut=1")

    def test_a_fotoazonosito_maga_NEM_valtozik(self, provider, photo):
        """A rekesz csak a szolgáltató kulcsát jelöli meg.

        Az ini-be írt szakasznév a fájlnévből jön, a jegyzett fotó-
        azonosító pedig a LOGIKAI azonosító marad — különben a mentés más
        képhez kötné a láncot."""
        ctl = _controller(provider, slot="masodik")
        ctl.beginEdit("42", str(photo))
        assert ctl._photo_id == "42"
        ctl.applyEffect("bw")
        from picasapy.ini import load_document

        szakasz = load_document(photo.parent / ".picasa.ini").section("IMG_0001.jpg")
        assert szakasz is not None and "bw" in (szakasz.get("filters") or "")


class TestKetFuggetlenAllapot:
    """UGYANARRA a fotóra két vezérlő, két külön lánc."""

    def test_a_ket_lanc_nem_irja_felul_egymast(self, provider, photo):
        fo = _controller(provider)
        masodik = _controller(provider, slot="masodik")
        fo.beginEdit("42", str(photo))
        masodik.beginEdit("42", str(photo))

        fo.applyEffect("sepia")
        masodik.applyEffect("bw")

        assert [op.name for op in fo._session.ops] == ["sepia"]
        assert [op.name for op in masodik._session.ops] == ["bw"]
        # a szolgáltatóban MINDKÉT kulcs alatt áll kép
        assert _van_kep(provider, "42")
        assert _van_kep(provider, "42@masodik")

    def test_az_egyik_lezarasa_a_masikat_nem_bantja(self, provider, photo):
        fo = _controller(provider)
        masodik = _controller(provider, slot="masodik")
        fo.beginEdit("42", str(photo))
        masodik.beginEdit("42", str(photo))

        masodik.endEdit()

        assert _van_kep(provider, "42")
        assert not _van_kep(provider, "42@masodik")

    def test_a_hisztogram_a_sajat_rekeszebol_jon(self, provider, photo):
        """Két külön lánc → két külön hisztogram, egyidejűleg.

        A hisztogram a MEGJELENÍTETT képből számol, tehát ha a két rekesz
        összecsúszna, a két vezérlő ugyanazt adná vissza."""
        fo = _controller(provider)
        masodik = _controller(provider, slot="masodik")
        fo.beginEdit("42", str(photo))
        masodik.beginEdit("42", str(photo))
        masodik.applyEffect("bw")
        # az effekt-hozzáadás HÁTTÉRSZÁLON renderel (#514) — determinista
        # bevárás, nem `sleep` (#999)
        assert masodik.waitForBackgroundWorkers(10)

        assert fo.histogram != masodik.histogram


class TestNincsKikerulesiUt:
    """Forrás-szintű őr: a szolgáltató felé CSAK a rekeszes kulcs mehet.

    A rekesz akkor ér valamit, ha nem lehet elfelejteni: egy új
    `self._provider.…(self._photo_id, …)` hívás némán visszahozná az
    ütközést (a második oldal lánca felülírná az elsőét)."""

    def test_egyetlen_provider_hivas_sem_kapja_a_nyers_fotoazonositot(self):
        forras = FORRAS.read_text(encoding="utf-8")
        gyanus = [
            sor.strip()
            for sor in forras.splitlines()
            if "self._provider." in sor and "self._photo_id" in sor
        ]
        assert gyanus == [], gyanus

    def test_az_url_epitok_sem(self):
        forras = FORRAS.read_text(encoding="utf-8")
        gyanus = [
            sor.strip()
            for sor in forras.splitlines()
            if "image://editpreview/" in sor and "self._photo_id" in sor
        ]
        assert gyanus == [], gyanus


# -- #3773: a két rekesz a közös képtárban -----------------------------------


@pytest.fixture
def ket_vezerlo(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    szolgaltato = EditPreviewProvider()
    fo = EditController(szolgaltato)
    masodik = EditController(szolgaltato, slot="masodik")
    yield szolgaltato, fo, masodik
    fo.endEdit()
    masodik.endEdit()


@pytest.fixture
def lru_kepek(tmp_path):
    return [
        make_jpeg(tmp_path / f"IMG_{i:04d}.jpg", size=(8, 6)) for i in range(1, 4)
    ]


def _kulcsok(szolgaltato):
    return set(szolgaltato._images)


class TestKetRekeszNemSzoritjaKiEgymast:
    """A két előnézet-rekesz nem szorítja ki egymás képét (#3773).

    A szolgáltató gyorsítótára két helyes (`_LRU_CAPACITY = 2`), és a kettős
    nézetben két vezérlő tölti: a fő (`7`) és a második (`8@masodik`). Mérve a
    #3773-on: „ab" módba lépéskor a második vezérlő előbb a jelenlegi képre
    nyitott (`7@masodik`), majd a következőre (`8@masodik`) — a régi kulcsa
    bent maradt, és kiszorította a FŐ vezérlő képét. A bal fél ezután a
    helykitöltőt kapta.

    A szabály: egy vezérlő egyszerre legfeljebb EGY kulcsot tart a
    szolgáltató képtárában — másik fotóra nyitva a régi képét elengedi.
    """

    def test_a_masodik_rekesz_lapozasa_nem_szoritja_ki_a_fo_kepet(
        self, ket_vezerlo, lru_kepek
    ):
        szolgaltato, fo, masodik = ket_vezerlo
        fo.beginEdit("7", str(lru_kepek[0]))
        masodik.beginEdit("7", str(lru_kepek[0]))
        masodik.beginEdit("8", str(lru_kepek[1]))
        assert _kulcsok(szolgaltato) == {"7", "8@masodik"}

    def test_a_fo_rekesz_lapozasa_nem_szoritja_ki_a_masodik_kepet(
        self, ket_vezerlo, lru_kepek
    ):
        szolgaltato, fo, masodik = ket_vezerlo
        masodik.beginEdit("8", str(lru_kepek[1]))
        fo.beginEdit("7", str(lru_kepek[0]))
        fo.beginEdit("9", str(lru_kepek[2]))
        assert _kulcsok(szolgaltato) == {"9", "8@masodik"}

    def test_ugyanarra_a_fotora_nyitva_a_kep_bent_marad(
        self, ket_vezerlo, lru_kepek
    ):
        szolgaltato, fo, _masodik = ket_vezerlo
        fo.beginEdit("7", str(lru_kepek[0]))
        fo.beginEdit("7", str(lru_kepek[0]))
        assert _kulcsok(szolgaltato) == {"7"}
