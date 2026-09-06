"""A főablak pozíciójának/méretének mentése és visszaállítása (#192).

Az ablak zárásakor a geometria QSettings-be íródik; a következő induláskor
visszaáll — de csak akkor, ha a mentett adat értelmes méretű és látható
részben a mostani virtuális asztalon van. Így egy lecsatolt monitor nem
hagyhatja az ablakot a képernyőn kívül, hibás/kézzel átírt beállítás pedig
egyszerűen az alapértelmezett geometriát adja.

Maximalizált/teljes képernyős zárásnál csak a maximalizált-jelző íródik —
a normál geometria a korábbi mentésből őrződik meg, hogy a maximalizálás
visszavonása később is értelmes méretre ugorjon.
"""

from __future__ import annotations

from PySide6.QtGui import QWindow

# a mentett méret alsó határa — ez alatt hibás/értelmetlen adat
_MIN_SIZE = 200
# ennyi képpontnyi ablaknak kell az asztalon belül maradnia, hogy a
# címsor egérrel megfogható legyen
_VISIBLE_MARGIN = 48

_KEY_X = "window/x"
_KEY_Y = "window/y"
_KEY_WIDTH = "window/width"
_KEY_HEIGHT = "window/height"
_KEY_MAXIMIZED = "window/maximized"


def sanitize_geometry(
    x: int,
    y: int,
    width: int,
    height: int,
    virtual_rect: tuple,
    min_size: tuple[int, int] | None = None,
) -> tuple[int, int, int, int] | None:
    """A mentett geometria észszerűsítése a virtuális asztalhoz.

    `virtual_rect`: (x, y, szélesség, magasság). None az eredmény, ha az
    adat értelmezhetetlen (törpe méret, üres asztal); egyébként úgy
    igazított geometria, hogy az ablak fogható része látsszon.

    `min_size`: az ablak BEJELENTETT minimuma (#2586). Enélkül a mentett
    méret a platform minimuma alá eshet, és az ablakkezelő felülbírálja —
    Windowson ez látható figyelmeztetéssel jár:

        QWindowsWindow::setGeometry: Unable to set geometry 958x1120…
        Resulting geometry: 993x1120… minimum size: 993x419

    Az eset nem egyszeri: a minimum a QML-ből jön, és MÉRT, VÁLTOZÓ érték
    (`Main.qml` `minimumWidth: trayBar.requiredWidth`, #1367;
    `minimumHeight: photoViewer.requiredHeight`, #641) — valahányszor a sáv
    igénye változik, a korábban mentett geometria elavul.

    ⚠️ A SORREND: **minimumra emelés → asztalra vágás → pozíció-korrekció**.
    Ha az asztal keskenyebb, mint a minimum, a **minimum nyer**: a platform
    úgyis azt adja, a `min(width, vw)` pedig épp a figyelmeztetést hozná
    vissza. A pozíció-korrekció ezért a MÁR FELEMELT mérettel számol,
    különben a jobb szélre mentett ablak lecsúszna.
    """
    vx, vy, vw, vh = virtual_rect
    if vw <= 0 or vh <= 0:
        return None
    # a `_MIN_SIZE` szentinel MARAD, ami: az „értelmetlen mentés" szűrője,
    # nem méret-politika (#2586) — a minimumra emelés nem írhatja felül
    if width < _MIN_SIZE or height < _MIN_SIZE:
        return None
    if min_size is not None:
        min_w, min_h = min_size
        # EGY kifejezés, három szabállyal: vágj az asztalra, de a minimum
        # alá SOHA. (A külön „emeld a minimumra" lépés fölösleges volt — a
        # mutációs próba mutatta meg, hogy egyetlen teszt sem különbözteti
        # meg: ez a `max(min(...), min_w)` már tartalmazza.)
        width = max(min(width, vw), min_w)
        height = max(min(height, vh), min_h)
    else:
        width = min(width, vw)
        height = min(height, vh)
    # vízszintesen legalább _VISIBLE_MARGIN-nyi ablak maradjon az asztalon
    x = max(vx + _VISIBLE_MARGIN - width, min(x, vx + vw - _VISIBLE_MARGIN))
    # a címsor nem kerülhet az asztal fölé, és alul is maradjon fogható sáv
    y = max(vy, min(y, vy + vh - _VISIBLE_MARGIN))
    return (x, y, width, height)


def virtual_desktop_rect(app) -> tuple[int, int, int, int]:
    """Az összes képernyőt befoglaló elérhető terület; képernyő nélkül
    (0, 0, 0, 0) — ilyenkor a visszaállítás kimarad."""
    screen = app.primaryScreen()
    if screen is None:
        return (0, 0, 0, 0)
    rect = screen.availableVirtualGeometry()
    return (rect.x(), rect.y(), rect.width(), rect.height())


def _read_int(settings, key: str) -> int | None:
    value = settings.value(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def save_window_geometry(window, settings, visibility=None) -> None:
    """Az ablak geometriájának mentése. Maximalizált/teljes képernyős
    állapotban csak a jelző íródik — a normál geometria marad a korábbi.

    `visibility`: felülbírálat záráskor — a már elrejtett ablak
    visibility()-je Hidden, ezért a bekötés a rejtés ELŐTTI állapotot
    adja át."""
    if visibility is None:
        visibility = window.visibility()
    maximized = visibility in (
        QWindow.Visibility.Maximized,
        QWindow.Visibility.FullScreen,
    )
    settings.setValue(_KEY_MAXIMIZED, "true" if maximized else "false")
    if maximized:
        return
    settings.setValue(_KEY_X, int(window.x()))
    settings.setValue(_KEY_Y, int(window.y()))
    settings.setValue(_KEY_WIDTH, int(window.width()))
    settings.setValue(_KEY_HEIGHT, int(window.height()))


def restore_window_geometry(window, settings, virtual_rect: tuple) -> bool:
    """A mentett geometria visszaállítása; True, ha bármi visszaállt.

    Hiányzó/hibás mentésnél az ablak alapértelmezett geometriája marad.
    """
    x = _read_int(settings, _KEY_X)
    y = _read_int(settings, _KEY_Y)
    width = _read_int(settings, _KEY_WIDTH)
    height = _read_int(settings, _KEY_HEIGHT)
    restored = False
    if None not in (x, y, width, height):
        # #2586: az ablak BEJELENTETT minimuma is számít. A `wire_window_
        # geometry` a QML-fa felépülése UTÁN fut (`application.py`), tehát
        # a `minimumWidth`/`minimumHeight` ekkor már a mért értéket adja.
        # Csonk-ablakon (a próbákéin) a `getattr` 0-t ad, és a viselkedés a
        # #2586 ELŐTTI marad.
        min_size = (
            int(getattr(window, "minimumWidth", lambda: 0)() or 0),
            int(getattr(window, "minimumHeight", lambda: 0)() or 0),
        )
        geometry = sanitize_geometry(
            x, y, width, height, virtual_rect,
            min_size=min_size if any(min_size) else None,
        )
        if geometry is not None:
            window.setGeometry(*geometry)
            restored = True
    if settings.value(_KEY_MAXIMIZED) in (True, "true"):
        window.showMaximized()
        restored = True
    return restored


def wire_window_geometry(window, settings, virtual_rect: tuple) -> None:
    """Bekötés (application.py): visszaállítás most, mentés záráskor.

    A mentést a visibilityChanged(Hidden) váltja ki (a closing jel
    QQuickCloseEvent-paraméterét a PySide6 nem tudja Python-oldalra
    konvertálni); a rejtés előtti utolsó láthatóságot követjük, hogy a
    maximalizáltan zárt ablak jelzője is helyesen íródjon."""
    restore_window_geometry(window, settings, virtual_rect)
    state = {"visibility": window.visibility()}

    def _on_visibility_changed(visibility) -> None:
        if visibility == QWindow.Visibility.Hidden:
            save_window_geometry(window, settings, state["visibility"])
        else:
            state["visibility"] = visibility

    window.visibilityChanged.connect(_on_visibility_changed)
