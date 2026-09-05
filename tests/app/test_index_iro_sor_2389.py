"""#2389 — az index-írók SOROSÍTÁSA, néma kihagyás nélkül.

A #1456 a `rescan()`-t úgy javította, hogy futó író mellett **kihagy**. Ott
ez helyes: az ötperces időzítő úgyis újrapróbál, és a felhasználó nem kérte
kimondottan.

A „Mappa hozzáadása" és a „Keresés egyszer" viszont **közvetlen felhasználói
művelet**. Ott a néma kihagyás ROSSZABB a mai hibánál: ma legalább
`syncFailed` jelzés van, a kihagyás után viszont a mappa egyszerűen nem
kerül be, és a felhasználó ezt csak jóval később venné észre.

Ezért itt sorosítás van, nem kihagyás: egyszerre egy író fut, a többi VÁR,
de mindegyik le is fut.
"""

from __future__ import annotations

import threading

from picasapy.app.index_writer_queue import IndexWriterQueue


class _Szal:
    """A `_start_background` helyettese: a szál indítását MI vezéreljük."""

    def __init__(self) -> None:
        self.inditott: list[threading.Thread] = []

    def __call__(self, munka, *, name=""):
        szal = threading.Thread(target=munka, name=name, daemon=True)
        self.inditott.append(szal)
        szal.start()
        return szal


class TestEgyszerreEgyIro:
    def test_a_masodik_munka_megvarja_az_elsot(self):
        naplo: list[str] = []
        elso_mehet = threading.Event()
        kesz = threading.Event()

        def elso() -> None:
            naplo.append("elso-be")
            elso_mehet.wait(5)
            naplo.append("elso-ki")

        def masodik() -> None:
            naplo.append("masodik-be")
            kesz.set()

        sor = IndexWriterQueue(_Szal())
        sor.submit(elso, name="elso")
        sor.submit(masodik, name="masodik")

        # amig az elso fut, a masodik MEG NEM kezdodhetett el
        assert "masodik-be" not in naplo
        elso_mehet.set()
        assert kesz.wait(5), "a masodik munka soha nem futott le"
        assert naplo == ["elso-be", "elso-ki", "masodik-be"]

    def test_soha_nem_fut_ket_iro_egyszerre(self):
        """A LENYEG: az atfedes tilos.

        Nem azt allitjuk, hogy ugyanaz a szal viszi mindet — ha a sor
        kiurul, a kovetkezo munka nyugodtan kaphat uj szalat. Ami tilos,
        az az ATFEDES: ket parhuzamos iro adja a #1440/#1456
        `sqlite3.OperationalError`-jat.
        """
        egyideju = 0
        csucs = 0
        zar = threading.Lock()

        def munka() -> None:
            nonlocal egyideju, csucs
            with zar:
                egyideju += 1
                csucs = max(csucs, egyideju)
            threading.Event().wait(0.02)
            with zar:
                egyideju -= 1

        sor = IndexWriterQueue(_Szal())
        for _ in range(5):
            sor.submit(munka, name="m")
        assert sor.wait_idle(5), "a sor nem urult ki"

        assert csucs == 1, f"{csucs} iro futott egyszerre — atfedes"


class TestNincsNemaKihagyas:
    def test_a_varolistara_kerult_munka_is_lefut(self):
        lefutott: list[str] = []
        elso_mehet = threading.Event()

        sor = IndexWriterQueue(_Szal())
        sor.submit(lambda: (lefutott.append("a"), elso_mehet.wait(5)), name="a")
        sor.submit(lambda: lefutott.append("b"), name="b")
        elso_mehet.set()
        sor.wait_idle(5)

        assert lefutott == ["a", "b"]

    def test_a_hivo_megtudja_hogy_varolistara_kerult(self):
        elso_mehet = threading.Event()
        sor = IndexWriterQueue(_Szal())

        azonnal = sor.submit(lambda: elso_mehet.wait(5), name="a")
        varolistan = sor.submit(lambda: None, name="b")
        elso_mehet.set()
        sor.wait_idle(5)

        assert azonnal is True, "az elso munkanak azonnal indulnia kell"
        assert varolistan is False, (
            "a masodik varolistara kerult — a hivonak ezt tudnia kell, "
            "kulonben nem tud visszajelezni a felhasznalonak"
        )


class TestAHibaNemAllitjaMegASort:
    def test_a_bukott_munka_utan_a_kovetkezo_lefut(self):
        lefutott: list[str] = []

        def bukik() -> None:
            lefutott.append("bukik")
            raise RuntimeError("szandekos")

        sor = IndexWriterQueue(_Szal())
        sor.submit(bukik, name="bukik")
        sor.submit(lambda: lefutott.append("utana"), name="utana")
        sor.wait_idle(5)

        assert lefutott == ["bukik", "utana"], (
            "egy bukott iro nem allithatja meg a sort — a felhasznalo "
            "kerese kulonben nyomtalanul elveszne"
        )

    def test_a_hibat_a_hivo_megkapja(self):
        hibak: list[BaseException] = []
        sor = IndexWriterQueue(_Szal(), on_error=hibak.append)

        sor.submit(lambda: (_ for _ in ()).throw(RuntimeError("x")), name="b")
        sor.wait_idle(5)

        assert len(hibak) == 1
        assert isinstance(hibak[0], RuntimeError)


class TestVarakozasFutoIdegenIroraIs:
    def test_megvarja_a_masik_uton_indult_irot(self):
        idegen_fut = threading.Event()
        idegen_fut.set()
        naplo: list[str] = []

        sor = IndexWriterQueue(_Szal(), is_busy=idegen_fut.is_set, poll_s=0.01)
        sor.submit(lambda: naplo.append("mienk"), name="m")

        assert not sor.wait_idle(0.2), "a sor nem varhatott volna meg"
        assert naplo == [], "az idegen iro mellett NEM indulhat masodik iro"

        idegen_fut.clear()
        assert sor.wait_idle(5)
        assert naplo == ["mienk"], "az idegen iro utan le KELL futnia"


def test_a_sor_nem_hasznal_polling_ot_ha_nincs_idegen_iro():
    """Alapertelmezesben nincs `is_busy` — ilyenkor semmi varakozas."""
    sor = IndexWriterQueue(_Szal())
    kesz = threading.Event()
    sor.submit(kesz.set, name="m")
    assert kesz.wait(2), "idegen iro nelkul azonnal futnia kell"
