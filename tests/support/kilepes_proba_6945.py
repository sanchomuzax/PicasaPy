"""A valódi alkalmazás kilépési próbája KÜLÖN FOLYAMATBAN (#6945).

A #671-es őrök a QML FORRÁSÁT mérik, élő kilépést sosem hajtanak végre
(„a `Qt.quit()` a próba processzét vinné magával”). Ezért maradt észrevétlen,
hogy a „Kilépés most” gomb háttérmunka mellett nem léptet ki: a `Qt.quit()`
a Qt-tól bezárási kérést kap a főablak, az `onClosing` pedig a futó munka
miatt újra visszavonja, vagyis a megerősített kilépés végtelen kérdésciklus.

Két rész egy fájlban:

* **szülő** (`futtasd`): elindítja a gyereket elszigetelt profillal, méri,
  mennyi idő telik el a „Kilépés most” kattintás és a folyamat vége között,
  és határidő után megöli;
* **gyerek** (`python kilepes_proba_6945.py <profil> <könyvtár> <belépés>
  <munka>`): a valódi `picasapy.app.__main__.main()`-t futtatja, egy háttérszál
  pedig a valódi gombot kattintja.

`belepes`: `kilepes` (a Fájl ▸ Kilépés közös útja) vagy `close` (az ablak „X”-e).
`munka`: `semmi` (kérdés sincs, a mérés a kilépési kéréstől számít), `hatter`
(nyilvántartott háttérszál, amely sosem fejeződik be) vagy `atnevezes` (a
`hatter` mellé a vezérlő átnevező-szálai közé tett szál is, amelyre a
`controller.shutdown()` KORLÁTLANUL vár) vagy `arckereses` (nem injektál
semmit: megvárja, míg a valódi `picasapy-face-scan` háttérszál fut).
"""

from __future__ import annotations

import os
import site
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_KLIKK_JELZO = "proba-klikk.txt"
_VEREMKEP = "proba-veremkep.txt"
_KIMENET = "proba-kimenet.txt"


@dataclass(frozen=True)
class ProbaEredmeny:
    """A próba kimenetele; `kilepesi_ido_s` a kattintástól a folyamat végéig."""

    eljutott_a_kattintasig: bool
    kilepett: bool
    kilepesi_ido_s: float | None
    visszateresi_kod: int | None
    kimenet: str
    veremkep: str


def _kornyezet(profil: Path) -> dict[str, str]:
    env = os.environ.copy()
    repo = Path(__file__).resolve().parents[2]
    env.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "PICASAPY_LANG": "en",
            # az elszigetelt HOME mellett a felhasználói csomagok is látszódjanak
            "PYTHONUSERBASE": site.getuserbase(),
            "PYTHONPATH": os.pathsep.join(
                [str(repo / "src"), str(repo / "tests")]
                + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
            ),
        }
    )
    if os.name == "nt":
        env.update(
            {
                "USERPROFILE": str(profil),
                "APPDATA": str(profil / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(profil / "AppData" / "Local"),
                "TEMP": str(profil / "Temp"),
                "TMP": str(profil / "Temp"),
            }
        )
    else:
        env.update(
            {
                "HOME": str(profil),
                "XDG_CONFIG_HOME": str(profil / ".config"),
                "XDG_DATA_HOME": str(profil / ".local" / "share"),
                "XDG_CACHE_HOME": str(profil / ".cache"),
                "XDG_RUNTIME_DIR": str(profil / "run"),
            }
        )
        (profil / "run").mkdir(mode=0o700, parents=True, exist_ok=True)
    return env


def futtasd(
    profil: Path,
    konyvtar: Path,
    *,
    belepes: str,
    munka: str,
    hatarido_s: float,
    indulasi_hatarido_s: float = 120.0,
) -> ProbaEredmeny:
    """A gyerek elindítása, a kilépés mérése, határidő után kényszerített leállítás."""
    profil.mkdir(parents=True, exist_ok=True)
    kimenet_fajl = profil / _KIMENET
    env = _kornyezet(profil)
    # a veremkép a szülő határideje ELŐTT készüljön el, hogy elakadáskor látsszon
    env["PICASAPY_PROBA_VEREMKEP_S"] = str(max(hatarido_s - 3.0, 3.0))
    with kimenet_fajl.open("wb") as kimenet:
        folyamat = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), str(profil),
             str(konyvtar), belepes, munka],
            env=env,
            stdout=kimenet,
            stderr=subprocess.STDOUT,
        )
        kezdet = time.monotonic()
        klikk_ideje: float | None = None
        try:
            while folyamat.poll() is None:
                time.sleep(0.1)
                if klikk_ideje is None and (profil / _KLIKK_JELZO).exists():
                    klikk_ideje = time.monotonic()
                if klikk_ideje is None:
                    if time.monotonic() - kezdet > indulasi_hatarido_s:
                        break
                elif time.monotonic() - klikk_ideje > hatarido_s:
                    break
        finally:
            kilepett = folyamat.poll() is not None
            vege = time.monotonic()
            if not kilepett:
                folyamat.kill()
            folyamat.wait()
    # ha a folyamat még a jelzőfájl észlelése előtt kilépett, a mérés 0 s-nak számít
    if klikk_ideje is None and (profil / _KLIKK_JELZO).exists():
        klikk_ideje = vege
    return ProbaEredmeny(
        eljutott_a_kattintasig=klikk_ideje is not None,
        kilepett=kilepett,
        kilepesi_ido_s=(vege - klikk_ideje) if (kilepett and klikk_ideje) else None,
        visszateresi_kod=folyamat.returncode if kilepett else None,
        kimenet=kimenet_fajl.read_text(encoding="utf-8", errors="replace"),
        veremkep=_olvas(profil / _VEREMKEP),
    )


def _olvas(utvonal: Path) -> str:
    try:
        return utvonal.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# gyerek
# ---------------------------------------------------------------------------


def _gyerek(profil: Path, konyvtar: Path, belepes: str, munka: str) -> int:
    import faulthandler
    import threading

    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo / "tests"))

    from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, Slot
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import qmlEngine
    from PySide6.QtTest import QTest

    from picasapy.app.worker_thread import BackgroundWorkerMixin

    class Tarto(BackgroundWorkerMixin):
        pass

    def eredmennyel(fuggveny):
        """A slot eredményét a hívó szál várja; sorba állított hívásnál nincs visszatérési érték."""

        def beburkolt(self) -> None:
            self.eredmeny = False
            try:
                self.eredmeny = bool(fuggveny(self))
            finally:
                self.kesz.set()

        beburkolt.__name__ = fuggveny.__name__
        return Slot()(beburkolt)

    class Vezerlo(QObject):
        def __init__(self) -> None:
            super().__init__()
            self.ablak = None
            self.felenged = threading.Event()
            self.tarto = Tarto()
            self.kesz = threading.Event()
            self.eredmeny = False

        def _gyokerobjektum(self, nev: str):
            kontextus = qmlEngine(self.ablak).rootContext()
            return kontextus.contextProperty(nev)

        @eredmennyel
        def kesz_az_indulas(self) -> bool:
            if self.ablak is None:
                for ablak in QGuiApplication.topLevelWindows():
                    if ablak.title() == "PicasaPy" and ablak.isVisible():
                        self.ablak = ablak
            if self.ablak is None:
                return False
            allapot = self._gyokerobjektum("startupStatus")
            return bool(allapot is not None and allapot.property("ready"))

        @eredmennyel
        def arckereses_fut(self) -> bool:
            from picasapy.app.worker_thread import running_background_workers

            return any("face-scan" in nev for nev in running_background_workers())

        @eredmennyel
        def munka_inditasa(self) -> bool:
            if munka in ("hatter", "atnevezes"):
                self.tarto._start_background(
                    self.felenged.wait, name="picasapy-proba-export"
                )
            if munka == "atnevezes":
                szal = threading.Thread(
                    target=self.felenged.wait, name="picasapy-proba-atnevezes",
                    daemon=True,
                )
                szal.start()
                self._gyokerobjektum("controller")._rename_worker_set().add(szal)
            return True

        @eredmennyel
        def kilepes_kerese(self) -> bool:
            if munka == "semmi":
                # kérdés nincs: a mérés a kilépési kéréstől számít
                (profil / _KLIKK_JELZO).write_text(str(time.time()), encoding="utf-8")
            if belepes == "close":
                self.ablak.close()
            else:
                QMetaObject.invokeMethod(
                    self.ablak, "kilepes", Qt.ConnectionType.DirectConnection
                )
            return True

        @eredmennyel
        def kerdes_latszik(self) -> bool:
            elem = self.ablak.findChild(QObject, "exitYesButton")
            return elem is not None and bool(elem.property("visible"))

        @eredmennyel
        def kilepes_most(self) -> bool:
            elem = self.ablak.findChild(QObject, "exitYesButton")
            kozep = elem.mapToScene(
                QPointF(elem.property("width") / 2, elem.property("height") / 2)
            )
            (profil / _KLIKK_JELZO).write_text(str(time.time()), encoding="utf-8")
            QTest.mouseClick(
                self.ablak,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(kozep.x()), round(kozep.y())),
            )
            return True

    vezerlo = Vezerlo()

    def fo_szalon(slot: str) -> bool:
        vezerlo.kesz.clear()
        QMetaObject.invokeMethod(vezerlo, slot, Qt.ConnectionType.QueuedConnection)
        vezerlo.kesz.wait(30)
        return vezerlo.eredmeny

    def varj(slot: str, hatarido_s: float) -> bool:
        vege = time.monotonic() + hatarido_s
        while time.monotonic() < vege:
            if fo_szalon(slot):
                return True
            time.sleep(0.3)
        return False

    def forgatokonyv() -> None:
        if not varj("kesz_az_indulas", 90):
            return
        if munka == "arckereses" and not varj("arckereses_fut", 120):
            return
        fo_szalon("munka_inditasa")
        time.sleep(0.5)
        fo_szalon("kilepes_kerese")
        if munka == "semmi":
            return
        if not varj("kerdes_latszik", 15):
            return
        szamlalo_hatar = float(os.environ.get("PICASAPY_PROBA_VEREMKEP_S", "40"))
        faulthandler.dump_traceback_later(
            szamlalo_hatar, file=open(profil / _VEREMKEP, "w", encoding="utf-8")
        )
        fo_szalon("kilepes_most")

    threading.Thread(target=forgatokonyv, daemon=True, name="proba-forgatokonyv").start()

    from picasapy.app.__main__ import main

    sys.argv = ["picasapy", str(konyvtar)]
    kod = main()
    faulthandler.cancel_dump_traceback_later()
    return kod


if __name__ == "__main__":
    sys.exit(_gyerek(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]))
