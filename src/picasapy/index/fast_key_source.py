"""Index-háttérrel dolgozó gyorskulcs-forrás (#1494).

A `dedup/exact.py` és az `importsource.duplicate_paths` egy egyszerű
`Callable[[Path], int | None]` kulcsforrást vár — alapértelmezésben a
lemezről számoló `picasa_fast_key`-t. Ez az osztály ugyanaz a hívható,
csak közé teszi az index `photo_hashes.originfast` oszlopát:

    olvasás  →  memória-gyorstár → index (FÁJLONKÉNT egy lekérdezés,
                nem kötegelt) → (ha egyik sem) számolás
    írás     →  köteg, `flush()`-nál az indexbe

**Miért lusta**: a migráció egyetlen kulcsot sem számol ki előre (a jegy
1. pontja). A sor akkor töltődik fel, amikor a hívó úgyis beolvasná a fájl
két végét — így a bevezetés SEMMILYEN egyszeri költséget nem ró a
felhasználóra, csak a második körtől nyer.

⚠️ **Az érvényesség a fájl AZONOSSÁGA**, nem az útvonala: a lekérdezés
`(útvonal, mtime_ns, méret)` hármassal megy, és a tárolt sor csak akkor
számít, ha mindhárom egyezik. Enélkül egy megváltozott fájlra a régi kulcs
jönne vissza — a duplikátum-kezelő pedig törlést ajánlana rá (#287), az
importálás meg kihagyná a fényképet (#441).

⚠️ **Az azonosságot a hívó is megadhatja** (`azonossagok`), és ha a
`photo_hashes` MÁSIK oszlopát (`dhash`) is írja ugyanabban a körben, akkor
KÖTELEZŐ is: a két oszlop egy soron osztozik, és minden írás NULL-ozza a
párját, ha a sorban tárolt azonosság nem egyezik a most beírttal. Két
külön azonosság-forrásból ezért a két gyorstár körönként váltakozva
ürítené egymást — a megtakarítás épp azokra a fájlokra veszne el, amelyek
a legdrágábbak (#1494 átnézés, 3. lelet). Megadás nélkül friss `stat()`
fut minden lekérdezés előtt.

⚠️ **A `None` kulcs (üres vagy olvashatatlan fájl) NEM kerül az indexbe**:
az oszlop NULL-ja azt jelenti, „még nincs kiszámolva", és a kettőt nem
tudnánk megkülönböztetni. Ezek a fájlok körönként újra próbálkoznak — ez
helyes: az „olvashatatlan" állapot átmeneti is lehet (levált NAS-mount).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Mapping
from pathlib import Path

from picasapy.dedup.fastkey import picasa_fast_key

from .hashes import HashKey, load_fast_keys, save_fast_keys

_log = logging.getLogger(__name__)

#: Ennyi új kulcs után megy ki egy köteg az indexbe. A `dedup_controller`
#: dHash-kötegével azonos nagyságrend: egy megszakított keresés munkája se
#: vesszen el, de ne is írjunk soronként. Ez az ígéret CSAK azért teljesül,
#: mert a `flush()` commitol is — commit nélkül a köteg a kör végéig egy
#: nyitott tranzakcióban ülne, és egy megszakadás mindet elvinné.
_FLUSH_MERET = 200


class IndexFastKeySource:
    """A gyorskulcs forrása az indexből, lusta feltöltéssel.

    Egy KÖRÖN belül él (a hívó nyitva tartja hozzá a kapcsolatot), és a
    körön belül memóriában is gyorstáraz — ugyanaz a fájl több
    méret-csoport összevetésében is előjöhet.

    A `flush()` KI is írja ÉS commitolja is a köteget (ld. ott), és soha
    nem dob: a gyorstár feltöltése kényelmi szolgáltatás, a hívó KÉSZ
    eredményét egy index-hiba nem ronthatja el.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        azonossagok: Mapping[str, HashKey] | None = None,
    ) -> None:
        self._conn = conn
        #: útvonal → a hívó által MÁR MEGMÉRT fájl-azonosság (ld. a modul
        #: docstringjét); ami nincs benne, arra friss `stat()` fut
        self._azonossagok = azonossagok or {}
        self._gyorstar: dict[HashKey, int | None] = {}
        self._varakozo: list[tuple[str, int, int, int]] = []
        #: mérőszámok (#1494): hány kulcs jött az indexből, és hány
        #: számolódott ki (azaz hány fájl két végét kellett beolvasni)
        self.talalat = 0
        self.szamolt = 0

    def __call__(self, path: Path) -> int | None:
        """A fájl gyorskulcsa — az indexből, ha van érvényes bejegyzés."""
        kulcs = self._azonossag(path)
        if kulcs is None:
            return None
        if kulcs in self._gyorstar:
            return self._gyorstar[kulcs]
        tarolt = load_fast_keys(self._conn, [kulcs])
        if kulcs in tarolt:
            self.talalat += 1
            self._gyorstar[kulcs] = tarolt[kulcs]
            return tarolt[kulcs]
        return self._szamol(path, kulcs)

    def flush(self) -> None:
        """A várakozó kulcsok kiírása ÉS commitolása.

        A commit SZÁNDÉKOSAN itt van, nem a hívónál — a `dedup_controller`
        dHash-kötegének már meglévő mintája szerint. `executemany` után az
        SQLite tranzakcióban marad, és a nyitott ÍRÁSI zár a teljes
        összevetés idejére (kártyányi képnél percek) kizárna minden más
        írót az indexből: a mappaszinkron, a mentés, a kulcsszó- és az
        arckeresés a `busy_timeout` letelte után `database is locked`-kal
        bukna. Ezért commitol a köteg, amint kiment.

        A művelet SOHA nem dob: a gyorstár feltöltése kényelmi
        szolgáltatás, a hívó KÉSZ eredményét (duplikátum-lista,
        dedup-jelentés) egy zárolt vagy tele index nem semmisítheti meg.
        Hiba esetén a köteget eldobjuk, visszagörgetünk — hogy a
        félbemaradt tranzakció ne tartsa tovább a zárat —, és a következő
        kör újrapróbálja."""
        if not self._varakozo:
            return
        koteg = tuple(self._varakozo)
        self._varakozo.clear()
        try:
            save_fast_keys(self._conn, koteg)
            self._conn.commit()
        except sqlite3.Error:
            _log.warning("#1494: a gyorskulcsok mentése nem sikerült", exc_info=True)
            self._visszagorget()

    def _visszagorget(self) -> None:
        """A félbemaradt tranzakció elengedése (a zár feloldásáért)."""
        try:
            self._conn.rollback()
        except sqlite3.Error:
            _log.warning("#1494: a visszagörgetés sem sikerült", exc_info=True)

    def _azonossag(self, path: Path) -> HashKey | None:
        """A fájl azonossága (útvonal, mtime_ns, méret), vagy `None`.

        Elsőbbsége a hívótól kapott, MÁR MEGMÉRT azonosságnak van — így
        osztozik a `dhash` oszlop írójával ugyanazon a soron anélkül, hogy
        a kettő kioltaná egymást."""
        kapott = self._azonossagok.get(str(path))
        if kapott is not None:
            return kapott
        try:
            adat = path.stat()
        except OSError:
            return None
        return (str(path), adat.st_mtime_ns, adat.st_size)

    def _szamol(self, path: Path, kulcs: HashKey) -> int | None:
        """A kulcs kiszámítása a fájlból + betevés a mentendők közé."""
        self.szamolt += 1
        ertek = picasa_fast_key(path)
        self._gyorstar[kulcs] = ertek
        if ertek is not None:
            self._varakozo.append((*kulcs, ertek))
            if len(self._varakozo) >= _FLUSH_MERET:
                self.flush()
        return ertek
