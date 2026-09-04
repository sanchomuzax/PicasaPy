"""#2273 — a csempe-bélyegkép a szerkesztési lánc TETEJÉN álljon.

Az eredeti Picasa a csempe-előnézetet a lánc **aktuális tetejére**
rendereli: ha a képre Fekete-fehér került, mind a tizenkét csempe alapja
is szürke, és a csempe csak a saját effektjét teszi rá. Nálunk eddig
minden csempe a **nyers** fotóból indult — mért eltérés, nem szabad
választás (a tulajdonos hat képernyőképe, három független előtte/utána
pár, három különböző fülön).

⚠️ A cache-kulcs is bővül: a `(útvonal, mtime, effekt)` hármas nem
különböztette meg a különböző láncokat, tehát a lánc változása után a
RÉGI bélyegkép jött vissza.
"""

from __future__ import annotations


from picasapy.index import open_index, photos_in_folder, sync_tree
from support.jpeg_factory import make_jpeg


def _library(tmp_path, *, filters: str = ""):
    lib = tmp_path / "kepek"
    lib.mkdir(parents=True)
    make_jpeg(lib / "kep.jpg", size=(320, 200))
    if filters:
        (lib / ".picasa.ini").write_text(
            f"[kep.jpg]\nfilters={filters}\n", encoding="utf-8"
        )
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return photos_in_folder(conn, lib)


def _provider(records, **kwargs):
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider

    registry = {str(r.id): r for r in records}
    return EffectThumbnailProvider(registry.get, **kwargs)


def _atlag(kep):
    """A QImage átlagos világossága — a „szürke lett-e" méréséhez."""
    kep = kep.convertToFormat(kep.format())
    w, h = kep.width(), kep.height()
    minta = [kep.pixelColor(x, y) for x in range(0, w, 4) for y in range(0, h, 4)]
    return sum(c.red() + c.green() + c.blue() for c in minta) / (3 * len(minta))


def _szaturacio(kep):
    """Átlagos színtelítettség — fekete-fehér láncnál ~0-ra esik."""
    w, h = kep.width(), kep.height()
    ertekek = []
    for x in range(0, w, 4):
        for y in range(0, h, 4):
            c = kep.pixelColor(x, y)
            ertekek.append(max(c.red(), c.green(), c.blue())
                           - min(c.red(), c.green(), c.blue()))
    return sum(ertekek) / len(ertekek)


class TestALancTetejerolIndul:
    def test_a_fekete_feher_lanc_a_csempere_is_hat(self, qt_app, tmp_path):
        """A jegy fő megfigyelése: `bw` a láncban ⇒ a csempe is szürke."""
        rekordok_a = _library(tmp_path / "c")
        rekordok_b = _library(tmp_path / "d", filters="bw=1;")
        p_a, p_b = _provider(rekordok_a), _provider(rekordok_b)

        a = p_a.requestImage(f"{rekordok_a[0].id}/sat", None, None)
        b = p_b.requestImage(f"{rekordok_b[0].id}/sat", None, None)
        assert not a.isNull() and not b.isNull()
        assert _szaturacio(b) < _szaturacio(a), (
            "a fekete-fehér lánc nem hatott a csempe előnézetére "
            f"(telítettség: lánccal {_szaturacio(b):.1f}, lánc nélkül "
            f"{_szaturacio(a):.1f})"
        )

    def test_lanc_nelkul_valtozatlan_a_viselkedes(self, qt_app, tmp_path):
        rekordok = _library(tmp_path)
        p = _provider(rekordok)
        kep = p.requestImage(f"{rekordok[0].id}/sepia", None, None)
        assert not kep.isNull()
        assert 64 <= max(kep.width(), kep.height()) <= 96


class TestACacheKulcsTartalmazzaALancot:
    """⚠️ A próbának UGYANAZON a provideren kell mérnie.

    Két külön provider két külön cache-t jelent — ott a régi kulcs is
    „működne", és a próba akkor is zöld lenne, ha a lánc kimarad belőle.
    A valós eset: a felhasználó effektet alkalmaz, tehát UGYANARRA a
    fotó-id-re jön friss rekord, új `filters` mezővel.
    """

    def test_a_lanc_valtozasa_utan_UJ_belyegkep_jon(self, qt_app, tmp_path):
        """⚠️ UGYANARRA a fájlra, változó lánccal.

        Két külön könyvtár nem mérne semmit: ott az útvonal is más, tehát
        a régi, lánc nélküli kulcs is megkülönböztetné őket. A valós eset
        az, hogy a felhasználó effektet alkalmaz — a KÉP fájlja ilyenkor
        NEM változik (csak a `.picasa.ini`), tehát az `mtime` sem: épp
        ezért nem volt elég a régi hármas.
        """
        from picasapy.app.effect_thumbnails import EffectThumbnailProvider
        from picasapy.index import open_index, photos_in_folder, sync_tree

        lib = tmp_path / "kepek"
        lib.mkdir(parents=True)
        make_jpeg(lib / "kep.jpg", size=(320, 200))
        db = tmp_path / "i.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)
            lanc_nelkul = photos_in_folder(conn, lib)[0]

        # a felhasználó effektet alkalmaz: CSAK a .picasa.ini változik
        (lib / ".picasa.ini").write_text(
            "[kep.jpg]\nfilters=bw=1;\n", encoding="utf-8"
        )
        with open_index(db) as conn:
            sync_tree(conn, lib)
            lanccal = photos_in_folder(conn, lib)[0]

        assert lanccal.mtime_ns == lanc_nelkul.mtime_ns, (
            "a kép fájlja megváltozott — akkor a próba nem azt méri, amit állít"
        )
        assert (lanccal.filters or "") != (lanc_nelkul.filters or "")

        allapot = {"rekord": lanc_nelkul}
        provider = EffectThumbnailProvider(lambda _id: allapot["rekord"])
        azonosito = f"{lanc_nelkul.id}/sat"

        elotte = provider.requestImage(azonosito, None, None)
        allapot["rekord"] = lanccal
        utana = provider.requestImage(azonosito, None, None)

        assert _szaturacio(utana) < _szaturacio(elotte), (
            "a lánc változása után a RÉGI (gyorsítótárazott) bélyegkép jött "
            f"vissza — telítettség előtte {_szaturacio(elotte):.1f}, "
            f"utána {_szaturacio(utana):.1f}"
        )

    def test_valtozatlan_lancnal_a_GYORSITOTARBOL_jon(self, qt_app, tmp_path):
        """A bővített kulcs nem ronthatja el a találatot."""
        from picasapy.app.effect_thumbnails import EffectThumbnailProvider

        rekord = _library(tmp_path)[0]
        hivasok = {"n": 0}

        def lookup(_id):
            hivasok["n"] += 1
            return rekord

        provider = EffectThumbnailProvider(lookup)
        azonosito = f"{rekord.id}/sepia"
        elso = provider.requestImage(azonosito, None, None)
        masodik = provider.requestImage(azonosito, None, None)
        assert not elso.isNull() and not masodik.isNull()
        assert _szaturacio(elso) == _szaturacio(masodik)
