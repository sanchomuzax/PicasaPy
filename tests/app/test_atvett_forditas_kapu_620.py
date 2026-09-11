"""#620: az eredeti magyar feliratok átvétele KAPUT kap, nem csak szabályt.

A `Picasa3i18n.dll` 75 panel-erőforrásából kinyert tábla
(`referencia/panel-feliratok-hu.tsv`, privát repó) **az eredeti, kiadott
magyar szöveget** adja — ez a fordítás alapja a felület-jegyeknél, nem a
saját fordításunk.

⚠️ **De nem másolható vakon.** A jegy KÉT bizonyított hibát nevez meg az
eredeti magyarban, és mindkettő pont olyan párbeszédben, amit mi is építünk:

| erőforrás | a hiba |
|---|---|
| `buttonmgr/instructions` | **fordított irány**: „a fentről lefelé … egyenértékű a **jobbról balra** mozgatással", az angol viszont *left-to-right* |
| `printoptions/apply`, `printoptions/ok` | **rossz alany**: „…alkalmazása a **Google Fotókra**", az angol *Photos*-a a nyomtatandó KÉPEKET jelenti |

A második a késői Picasa Web Albums → Google Photos átnevezés gépies
következménye: ahol tényleg az online szolgáltatásról van szó
(`thumbui/lightbox_bgtext`, `headerpanel/share`), ott a magyar HELYES — ezért
a kapu nem a „Google Fotók" szóra tilt, hanem az **angol–magyar értelem
eltérésére**.

## Amit ez a lap mér, és amit nem

**Mér:** hogy a két hibaosztály egyike sem került a kiadott magyar
fordításunkba. A minta általános, nem a két sztringre szabott — a
hibaosztályt fogja meg, tehát egy harmadik, hasonló átvételnél is szól.

⚠️ **Nem mér:** hogy egy fordítás valóban a táblából jött-e. Azt gép nem
tudja megállapítani; a jegy 1–2. pontja munkaszabály, aminek ez a lap a
foga, nem a helyettesítője.

A pásztázást **ismert pozitívval** hitelesítjük: a két eredeti, hibás
szövegre a vizsgálat elbukik. Enélkül egy elrontott minta nulla találata
„tisztának" látszana.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import picasapy.app
import pytest

_TS = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"

#: A két bizonyított hiba SZÓ SZERINT, az eredeti magyarból — a pozitív
#: kontroll bemenete. (A `buttonmgr/instructions` rövidítve arra a tagmondatra,
#: amelyik az irányt megfordítja.)
EREDETI_HIBAK = (
    (
        "Top-to-bottom here equals left-to-right in the application",
        "A fentről lefelé irány egyenértékű az alkalmazásban jobbról balra "
        "való mozgatással.",
    ),
    (
        "Apply selected options to Photos",
        "A kijelölt beállítások alkalmazása a Google Fotókra",
    ),
)


def _forditas_parok() -> list[tuple[str, str, str]]:
    """`(kontextus, angol, magyar)` hármasok a kiadott fordításból."""
    gyoker = ET.parse(_TS).getroot()
    parok: list[tuple[str, str, str]] = []
    for context in gyoker.findall("context"):
        nev = (context.findtext("name") or "").strip()
        for message in context.findall("message"):
            angol = message.findtext("source") or ""
            magyar = message.findtext("translation") or ""
            if angol and magyar:
                parok.append((nev, angol, magyar))
    return parok


#: „balról jobbra" jellegű irány-párok: (angol minta, a magyar ELLENTÉTE)
_IRANY_PAROK = (
    (r"left[- ]to[- ]right", "jobbról balra"),
    (r"right[- ]to[- ]left", "balról jobbra"),
    (r"top[- ]to[- ]bottom", "lentről felfelé"),
    (r"bottom[- ]to[- ]top", "fentről lefelé"),
)


def megforditott_irany(angol: str, magyar: str) -> bool:
    """Megfordítja-e a magyar az angolban megadott irányt? (#620/1)"""
    for minta, ellentet in _IRANY_PAROK:
        if re.search(minta, angol, re.IGNORECASE) and ellentet in magyar.lower():
            return True
    return False


def google_fotokra_cserelt_kepek(angol: str, magyar: str) -> bool:
    """A magyar a Google szolgáltatását nevezi meg ott, ahol az angol csak
    KÉPEKET mond? (#620/2)

    A feltétel szándékosan az angolra támaszkodik: ha az angol maga is
    „Google Photos"-t ír, a magyar „Google Fotók" HELYES."""
    if "google fot" not in magyar.lower():
        return False
    #: a gyorsító `&` a szó KÖZEPÉN is állhat („Google &Photos"), ezért a
    #: minta előtt kivesszük — enélkül a kapu a HELYES átvételre is szólt
    #: (mérve: `AlbumContextMenu`, `FolderContextMenu`)
    tiszta = angol.replace("&", "")
    return not re.search(r"google\s*(photos|drive|account)", tiszta, re.IGNORECASE)


class TestAKapu:
    def test_egyetlen_forditas_sem_forditja_meg_az_iranyt(self):
        vetkesek = [
            (ctx, angol)
            for ctx, angol, magyar in _forditas_parok()
            if megforditott_irany(angol, magyar)
        ]
        assert not vetkesek, (
            "#620/1: a magyar az angollal ELLENTÉTES irányt mond — az eredeti "
            f"`buttonmgr/instructions` hibája: {vetkesek}"
        )

    def test_a_KEPEK_nem_lettek_Google_Fotokka(self):
        vetkesek = [
            (ctx, angol)
            for ctx, angol, magyar in _forditas_parok()
            if google_fotokra_cserelt_kepek(angol, magyar)
        ]
        assert not vetkesek, (
            "#620/2: a magyar a Google szolgáltatását nevezi meg, az angol "
            f"viszont a KÉPEKET — az eredeti `printoptions/apply` hibája: "
            f"{vetkesek}"
        )


class TestAPaszazasHitelesitese:
    """Ismert pozitív: a két eredeti hibás szövegre a vizsgálatnak BUKNIA kell.

    Enélkül egy elrontott minta nulla találata „tisztának" látszana."""

    def test_az_irany_hibat_FELISMERI(self):
        angol, magyar = EREDETI_HIBAK[0]
        assert megforditott_irany(angol, magyar) is True

    def test_a_Google_Fotok_hibat_FELISMERI(self):
        angol, magyar = EREDETI_HIBAK[1]
        assert google_fotokra_cserelt_kepek(angol, magyar) is True

    def test_a_HELYES_atvetelt_nem_jelzi(self):
        """Ahol tényleg az online szolgáltatásról van szó, a „Google Fotók"
        jó — a kapu nem tilthatja meg (`thumbui/lightbox_bgtext`,
        `headerpanel/share`)."""
        assert (
            google_fotokra_cserelt_kepek(
                "Upload to Google Photos", "Feltöltés a Google Fotókba"
            )
            is False
        )
        #: a gyorsító `&` a szó közepén — ez a valódi alak a menüinkben
        assert (
            google_fotokra_cserelt_kepek(
                "Upload to Google &Photos...", "Feltöltés a Google Fotókba…"
            )
            is False
        )
        assert megforditott_irany("Sort left-to-right", "Rendezés balról jobbra") is False


class TestAForditasTabla:
    """A lap CSAK akkor ér valamit, ha tényleg végigmegy a fordításokon."""

    def test_a_paszazas_nem_ures(self):
        parok = _forditas_parok()
        assert len(parok) > 1000, (
            f"csak {len(parok)} fordítás-párt olvastunk ki — a `.ts` elemzése "
            "elromlott, és a kapu ilyenkor semmit nem állít"
        )

    def test_a_kontextus_is_megvan(self):
        """A lelet neve nélkül a hibát nem lehet megtalálni."""
        assert any(ctx for ctx, _, _ in _forditas_parok())

    @pytest.mark.parametrize("angol,magyar", EREDETI_HIBAK)
    def test_a_ket_hibas_szoveg_NINCS_a_forditasunkban(self, angol, magyar):
        szoveg = _TS.read_text(encoding="utf-8")
        assert magyar not in szoveg, (
            "#620: az eredeti magyar bizonyítottan hibás sora bekerült a "
            "fordításunkba — a jegy 3. pontja szerint JAVÍTVA kell átvenni"
        )
