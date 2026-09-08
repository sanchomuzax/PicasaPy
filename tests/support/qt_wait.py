"""Közös várakozó-segédek háttérszálas Qt-műveletekhez (#475).

## Miért kell

A csillagozás/felirat/forgatás háttérszálon fut (NAS-írás + célzott
index-UPDATE), ezért a teszt a `photoOpFinished` jelzésre vár. A korábbi,
fájlonként lemásolt minta így nézett ki:

```python
loop = QEventLoop()
controller.photoOpFinished.connect(loop.quit)
action()
QTimer.singleShot(2000, loop.quit)   # vészfék
loop.exec()
```

A **vészfék csendben** engedte tovább a tesztet: ha a 2 másodperc alatt nem
jött meg a jelzés (lassú CI-runner!), a hurok kilépett, a művelet még nem
fejeződött be, és a teszt nem időtúllépést jelentett, hanem egy KÉSŐBBI
állítás bukott el rossz értékkel — ami teljesen elfedte a valódi okot.
Így bukott a `test_selection.py` a windows-lábon: „a csillag fehér, nem
arany", holott a csillagozás egyszerűen még nem futott le (#475).

## Mit csinál helyette

Ez a segéd a vészféket **hangossá** teszi: ha a jelzés nem érkezik meg,
beszédes `AssertionError`-t dob, és az időkorlát bőkezűbb (a lassú CI-hez
szabva). A hívónak így soha nem kell találgatnia, mi romlott el.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

# A régi 2 másodperc a fejlesztői gépre volt szabva. A CI-runner (különösen
# a windows-láb, coverage alatt) lényegesen lassabb — a bő időkorlát nem
# lassítja a zöld futást (a jelzés érkezésekor azonnal továbblép), csak a
# hamis bukást előzi meg.
DEFAULT_TIMEOUT_MS = 15000


def jelzes_neve(jelzes) -> str:
    """A Qt-jelzés neve emberi olvasásra — a bukás-üzenethez.

    A PySide a `SignalInstance` reprjében kiírja a jelzés nevét
    (`<PySide6.QtCore.SignalInstance scanFinished() at 0x...>`); ha ez a
    formátum egyszer megváltozna, a segéd nem dobhat — a hangosítás
    értéke akkor sem vész el, csak a név lesz általánosabb.
    """
    try:
        szoveg = repr(jelzes)
        nev = szoveg.split("SignalInstance ", 1)[1].split(" at ", 1)[0]
        return f"a(z) {nev} jelzésre váró művelet" if nev else "a háttérművelet"
    except (IndexError, TypeError):
        return "a háttérművelet"


class HangosHurok(QEventLoop):
    """Jelzésre záruló eseményhurok, amelynek a vészféke **HANGOS** (#1467).

    ## A baj, amit megszüntet

    A készletben tucatnyi helyen élt ez a minta:

    ```python
    loop = QEventLoop()
    signal.connect(loop.quit)
    action()
    QTimer.singleShot(5000, loop.quit)   # néma vészfék
    loop.exec()
    assert valami_az_eredmenyrol
    ```

    A vészfék **csendben** engedte tovább a tesztet: ha az 5 másodperc
    alatt nem jött meg a jelzés (terhelt CI-futó!), a hurok pontosan
    ugyanúgy lépett ki, mint sikeres jelzésnél. A teszt ezután egy
    látszólag független állításon bukott — vagy, rosszabb esetben,
    **véletlenül zöld maradt**. A #1463 mérte ki, hogy ez nem elméleti: a
    `test_tray_export.py` néma vészféke egy VALÓDI versenyt nyelt el, és a
    teszt zöld volt; amint a vészfék hangos lett, azonnal pirosra váltott.

    ## Mit csinál helyette

    A hurok maga tartja nyilván, hogy a jelzés megérkezett-e. Ha az
    `exec()` úgy tér vissza, hogy nem a jelzés zárta a hurkot, **ott
    helyben** dob beszédes `AssertionError`-t — nem hagyja, hogy a bukás
    egy későbbi, félrevezető állításon jelentkezzen.

    ## A szinkron ág fogása (#2423)

    A `QEventLoop.quit()` az `exec()` ELŐTT kiadva **elvész** — a hurok
    utána is kiüli a teljes időzítőt. Ha tehát a jelzés már a művelet
    indítása közben megjött, az `exec()` **be sem lép** a hurokba, hanem
    azonnal visszatér. Enélkül minden szinkron úton jelző teszt a teljes
    időkorlátot elpazarolná — és a hangosítás után hamis időtúllépést is
    jelentene.
    """

    def __init__(
        self, jelzes, *, leiras: str | None = None, timeout_ms: int = DEFAULT_TIMEOUT_MS
    ):
        super().__init__()
        self._leiras = leiras or jelzes_neve(jelzes)
        self._timeout_ms = timeout_ms
        #: publikus: a hívó is megnézheti, a jelzés zárta-e a hurkot
        self.jelzes_megjott = False
        jelzes.connect(self._jelzesre)

    def _jelzesre(self, *_args) -> None:
        """A jelzés megjött — a hurkot azonban NEM azonnal zárjuk.

        ⚠️ MÉRVE (#1467): az azonnali `quit()` **levágja ugyanannak a
        kibocsátásnak a nálunk KÉSŐBB bekötött szlotjait.** Szálak közti
        (sorba állított) kapcsolatnál a Qt kapcsolatonként külön eseményt
        posztol; az elsőként bekötött slotunk `quit()`-je után a hurok
        kilép, és a hívó saját, eredményt gyűjtő szlotja SOSEM fut le.
        A `test_broken_photo_and_diskspace_459.py` importos őre így bukott
        el a futások harmadában: `finished == []`, holott a jelzés
        megérkezett — a lambda a hurok kilépése UTÁN futott volna.

        A halasztott (0 ms-os) zárás megvárja a már posztolt kézbesítéseket,
        tehát a bekötési sorrend nem dönthet arról, lefut-e a hívó saját
        szlotja. Ez a segéd SZERZŐDÉSE: a hívó bármikor köthet rá további
        szlotot.

        (A záró szlot bekötési lista végére mozgatását is kipróbáltuk;
        MÉRVE nem hozott semmit a halasztott zárás mellett, ezért nincs
        benne — igazolatlan mechanizmus nem marad a kódban.)"""
        self.jelzes_megjott = True
        QTimer.singleShot(0, self.quit)

    def exec(self, *args, **kwargs) -> int:
        """Lefuttatja a hurkot, és ELBUKIK, ha nem a jelzés zárta le."""
        if self.jelzes_megjott:
            # #2423: a jelzés a hurok indítása ELŐTT megjött — a quit()
            # ilyenkor elveszne, és a teljes időzítőt kiülnénk
            return 0
        # a vészfék-timer a hurok GYERMEKE: a hurokkal együtt megsemmisül,
        # így nem marad árva, később elsülő timer a processzben (#430)
        veszfek = QTimer(self)
        veszfek.setSingleShot(True)
        veszfek.timeout.connect(self.quit)
        veszfek.start(self._timeout_ms)
        try:
            eredmeny = super().exec(*args, **kwargs)
        finally:
            veszfek.stop()
        if not self.jelzes_megjott:
            # A hurokból kiléphetett egy MÁSIK szlot `quit()`-je is,
            # mielőtt a miénk sorra került volna (a hívó saját kezelője a
            # bekötési listán ELŐTTÜNK áll). Ilyenkor a jelzés MEGVOLT, csak
            # mi nem tudunk róla — HAMIS időtúllépést jelentenénk. Egy
            # kézbesítési kör ezt eldönti. (Mérve #1467: a
            # `test_create_controller.py` őrei buktak így el.)
            QCoreApplication.processEvents()
        if not self.jelzes_megjott:
            raise AssertionError(
                f"#1467: {self._leiras} — a várt jelzés "
                f"{self._timeout_ms / 1000:g} másodperc alatt nem érkezett "
                f"meg. Ez NEM tartalmi hiba: a háttérmunka lassabb volt az "
                f"időkorlátnál, beragadt, vagy a jelzés nincs bekötve. A "
                f"bukás SZÁNDÉKOSAN itt jelentkezik, nem egy későbbi, "
                f"félrevezető állításon."
            )
        return eredmeny


def hangos_hurok(
    jelzes, *, leiras: str | None = None, timeout_ms: int = DEFAULT_TIMEOUT_MS
):
    """`HangosHurok` a `jelzes`-re — a néma `QEventLoop` + `singleShot`
    vészfék páros helyett (#1467).

    Használat a korábbi minta helyén::

        loop = hangos_hurok(controller.syncFinished, leiras="a mappa-szinkron")
        controller.rescan()
        loop.exec()          # itt bukik, ha a jelzés nem jött meg

    `leiras`: emberi nyelvű megnevezés, ez kerül a bukás üzenetébe. Ha
    elmarad, a jelzés SAJÁT neve kerül bele (`jelzes_neve`), tehát a bukás
    akkor is megnevezi, mire vártunk.
    """
    return HangosHurok(jelzes, leiras=leiras, timeout_ms=timeout_ms)


def wait_for_signal(
    signal,
    action: Callable[[], object] | None = None,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    description: str = "a háttérművelet",
    process_events_with=None,
) -> None:
    """Elindítja az `action`-t, és megvárja a `signal` megérkezését.

    A jelzésre azonnal továbblép. Ha az időkorlát alatt NEM jön meg,
    `AssertionError`-t dob — nem engedi tovább csendben a tesztet.

    `process_events_with`: opcionális `QGuiApplication`; ha meg van adva, a
    jelzés után lefuttat egy `processEvents()`-et, hogy a QML-kötések is
    frissüljenek (a QML-funkcionális tesztek igénye)."""
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    arrived: list[bool] = []

    def _on_signal(*_args):
        arrived.append(True)
        loop.quit()

    signal.connect(_on_signal)
    # a vészfék-timer a hurok GYERMEKE: a hurokkal együtt megsemmisül, így
    # nem marad árva, később elsülő timer a processzben
    timer = QTimer(loop)
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(timeout_ms)

    if action is not None:
        action()
    loop.exec()
    timer.stop()
    signal.disconnect(_on_signal)

    assert arrived, (
        f"{description} nem fejeződött be {timeout_ms / 1000:g} másodperc "
        f"alatt (a várt jelzés nem érkezett meg). Ez NEM tartalmi hiba: a "
        f"művelet lassabb volt az időkorlátnál — ld. #475."
    )
    if process_events_with is not None:
        process_events_with.processEvents()


def wait_for_photo_op(controller, action, *, qt_app=None) -> None:
    """A `photoOpFinished`-re várakozás rövidítése (csillag/felirat/
    forgatás). A korábbi, fájlonként másolt `_do_photo_op` utódja."""
    wait_for_signal(
        controller.photoOpFinished,
        action,
        description="a kép-művelet (photoOpFinished)",
        process_events_with=qt_app,
    )


def varj_kollazs_jelzesre(signal, action, timeout_ms: int = 20000):
    """Kollázs-háttérmunkát indító művelet bevárása — **GC-szünettel**.

    A kollázs-tesztek `_wait` segédjének közös alakja. Két dolgot tesz a
    beágyazott eseményhurkon felül, és mindkettő KÜLÖN állítás, külön
    bizonyítékkal (#988):

    1. **A várakozás idejére kikapcsolja a szemétgyűjtőt.** A CI-n
       visszatérő `exit -11` (SIGSEGV) veremkiíratása ezt mutatta:

       ```
       Thread (háttér):  picasa_render._canvas ← collage_save._render_worker
       Current thread:   Garbage-collecting ← _wait ← a teszt
       ```

       A főszál épp GC-t futtat a beágyazott hurokban, miközben a
       háttérszál — egy sima `threading.Thread` — Qt-jelzést marsall a
       PySide-burkolókon. A GC időzítése dönti el, hogy elszáll-e; ezért
       nem reprodukálható terhelés nélkül, és ezért látszik
       párhuzamosság-függőnek.

    2. **A végén bontja a kapcsolatot.** Enélkül hívásonként egy holt,
       lokális függvényre mutató kapcsolat és egy `QEventLoop` marad a
       jelzésen — pont az, amit később a szemétgyűjtő takarítana.

    Mindkettő a `finally`-ben: egy elszálló teszt sem hagyhatja
    kikapcsolva a gyűjtőt a többinek.

    **Hol van a hiba — MÉRVE (2026-08-23).** Sokáig az volt a magyarázat,
    hogy a versenyhelyzet a TERMÉKBEN van, és a valódi javítás a worker
    Qt-natívvá tétele (`QThread`) lenne. **Ezt a mérés megcáfolta:** a
    kollázs-mentés 96 egymást követő futásban hibátlanul lefutott úgy,
    hogy a főszál 0 ms-onként teljes szemétgyűjtést végzett közben
    (`tests/app/test_kollazs_gc_verseny_988.py` őrzi ezt). A #1112 óta a
    háttérszál nem ír állapotot és nem bocsát ki nyilvános jelzést, a
    rajzolás pedig tiszta numpy — Qt-objektumhoz nem nyúl.

    Ami tehát elszállt, az a TESZT oldalán keletkezett: a bontatlan
    kapcsolatok és az árván maradt `QEventLoop`-ok, amiket a szemétgyűjtő
    egy tetszőleges pillanatban takarított. Ezért elég — és ezért helyes —
    itt kezelni.

    **A vészfék HANGOS (#1467).** Ha a jelzés nem jön meg, a segéd maga
    dob beszédes `AssertionError`-t — a visszaadott `megjott` eldobása sem
    nyelheti el az időtúllépést.

    Returns:
        `(megjott, args)` — a jelzés megérkezett-e, és a paraméterei.
    """
    import gc

    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    received: dict[str, tuple] = {}

    def _on(*args):
        received.setdefault("args", args)
        loop.quit()

    signal.connect(_on)
    gc.disable()
    try:
        action()
        if "args" not in received:
            QTimer.singleShot(timeout_ms, loop.quit)
            loop.exec()
    finally:
        gc.enable()
        signal.disconnect(_on)
    # #1467: a vészfék itt sem lehet néma. A MAI hívók mind ellenőrzik a
    # visszaadott `megjott`-at (mérve), de a jelző eldobása némán elnyelné
    # az időtúllépést — ezért a segéd MAGA is megáll.
    assert "args" in received, (
        f"#1467: a kollázs-jelzés {timeout_ms / 1000:g} másodperc alatt nem "
        f"érkezett meg. Ez NEM tartalmi hiba: a háttérmunka lassabb volt az "
        f"időkorlátnál vagy beragadt."
    )
    return ("args" in received, received.get("args", ()))
