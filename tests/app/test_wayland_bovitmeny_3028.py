"""#3028: wayland-asztalon a hiányzó Qt-bővítményt MAGYARUL mondjuk meg.

## A jelentett eset

A tulajdonos Raspberry Pi 5-ösén a program nem indult el:

```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in ""
This application failed to start because no Qt platform plugin could be
initialized.
```

A mérés a gépén: a munkamenet wayland (`XDG_SESSION_TYPE=wayland`), a Qt 6
bővítmény-mappában viszont nincs `libqwayland*.so` — a `qt6-wayland`
csomag nincs telepítve (a fent lévő `qtwayland5` a Qt 5-é).

A Qt üzenete angol, és nem mondja meg, mit kell tenni. Ez a próba azt
tartja fenn, hogy a mi üzenetünk megmondja — és hogy TÉVESEN ne szóljon.
"""

from __future__ import annotations

from picasapy.app.platform_check import hianyzo_wayland_bovitmeny


def _kornyezet(**tobbi):
    alap = {"XDG_SESSION_TYPE": "wayland", "WAYLAND_DISPLAY": "wayland-0"}
    alap.update(tobbi)
    return alap


class TestAmikorSzolni_KELL:
    def test_wayland_munkamenet_bovitmeny_nelkul(self):
        uzenet = hianyzo_wayland_bovitmeny(
            _kornyezet(), bovitmenyek=("xcb", "offscreen", "eglfs")
        )
        assert uzenet, "wayland munkamenetben, bővítmény nélkül szólni kell"

    def test_az_uzenet_megnevezi_a_TELEPITENDO_csomagot(self):
        uzenet = hianyzo_wayland_bovitmeny(
            _kornyezet(), bovitmenyek=("xcb",)
        )
        assert "qt6-wayland" in uzenet, (
            "a felhasználónak a PARANCS kell, nem a jelenség leírása"
        )
        assert "apt install" in uzenet

    def test_az_uzenet_MAGYAR(self):
        uzenet = hianyzo_wayland_bovitmeny(_kornyezet(), bovitmenyek=("xcb",))
        assert any(szo in uzenet for szo in ("nem indul", "hiányzik", "telepít"))

    def test_WAYLAND_DISPLAY_onmagaban_is_eleg(self):
        """Van, ahol a munkamenet típusa nincs beállítva, a kijelző mégis él."""
        uzenet = hianyzo_wayland_bovitmeny(
            {"WAYLAND_DISPLAY": "wayland-0"}, bovitmenyek=("xcb",)
        )
        assert uzenet


class TestAmikor_HALLGATNI_kell:
    """A téves riasztás rosszabb, mint a hallgatás: elszoktat az olvasástól."""

    def test_ha_VAN_wayland_bovitmeny(self):
        assert hianyzo_wayland_bovitmeny(
            _kornyezet(), bovitmenyek=("wayland", "xcb")
        ) is None

    def test_ha_NEM_wayland_a_munkamenet(self):
        assert hianyzo_wayland_bovitmeny(
            {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"}, bovitmenyek=("xcb",)
        ) is None

    def test_ha_a_felhasznalo_MAS_platformot_ker(self):
        """`QT_QPA_PLATFORM=xcb` melletti figyelmeztetés puszta zaj."""
        assert hianyzo_wayland_bovitmeny(
            _kornyezet(QT_QPA_PLATFORM="xcb"), bovitmenyek=("xcb",)
        ) is None

    def test_a_tesztek_offscreen_platformjan_HALLGAT(self):
        assert hianyzo_wayland_bovitmeny(
            _kornyezet(QT_QPA_PLATFORM="offscreen"), bovitmenyek=("xcb",)
        ) is None

    def test_ures_kornyezetben_hallgat(self):
        assert hianyzo_wayland_bovitmeny({}, bovitmenyek=("xcb",)) is None


class TestABovitmenyLista:
    """A tényleges lista a Qt telepítéséből jön, nem beégetve."""

    def test_a_valos_listat_olvassa(self):
        from picasapy.app.platform_check import elerheto_platformok

        nevek = elerheto_platformok()
        assert isinstance(nevek, tuple)
        assert "offscreen" in nevek, (
            "a tesztek offscreen platformon futnak, tehát léteznie kell: "
            f"{nevek}"
        )
