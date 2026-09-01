"""A tesztüzem naplója megmondja, MILYEN tárolón fut a program — #1660.

A #1653 mérése szerint az indulás **fájlbeolvasás-korlátos**: minden
induláskor ~290 MB modul olvasódik be (a `cv2` egymaga 138 MB), és
ugyanazon a gépen, ugyanazzal a commit-tal az importlánc **490 ms** meleg
lapgyorstárral, **3679 ms** hideggel — 7,5×, kizárólag a fájlrendszer
állapotától.

⇒ Ha a telepítés hálózati meghajtón van, az önmagában megmagyarázza a
tulajdonos 33 másodpercét. Ez a napló-sor adja a #1653 zárásához hiányzó
bizonyítékot — a felhasználó terhelése nélkül.

## ⚠️ A jegy adatvédelmi kikötése

CSAK a típus kerül a naplóba, a HELY soha: se meghajtóbetű, se UNC-név, se
útvonal, se felhasználónév. A `TestNincsBenneHely` ezt méri.

## Nincs `skipif`

A windowsos ág a `platform`/`win_drive_type` fogantyúkon át **Linuxon is
végigmérhető** (a #1217 mintája). A #1560 hibája épp az volt, hogy egy
windowsra kötött ág a CI ubuntu-lábán üresen zölden maradt.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.perf.tesztuzem import (
    TAROLO_CSERELHETO,
    TAROLO_HALOZATI,
    TAROLO_HELYI,
    TAROLO_ISMERETLEN,
    TAROLO_MEMORIA,
    KonyvtarMeret,
    naplo_szovege,
    tarolo_tipusa,
)


class TestAWindowsAg:
    """`GetDriveType` — a fogantyún át Linuxon is mérve."""

    @pytest.mark.parametrize(
        "kod,vart",
        [
            (2, TAROLO_CSERELHETO),
            (3, TAROLO_HELYI),
            (4, TAROLO_HALOZATI),
            (6, TAROLO_MEMORIA),
            (0, TAROLO_ISMERETLEN),
            (1, TAROLO_ISMERETLEN),
        ],
    )
    def test_a_meghajto_tipuskodja(self, kod, vart):
        assert (
            tarolo_tipusa(
                "C:/Program Files/PicasaPy",
                platform="win32",
                win_drive_type=lambda _gyoker: kod,
            )
            == vart
        )

    def test_az_UNC_ut_halozati_kerdezes_NELKUL(self):
        """A `GetDriveType`-nak az UNC nem meghajtó — magunk ismerjük fel."""
        def sosem_hivhato(_gyoker):  # pragma: no cover
            raise AssertionError("UNC-útra nem szabad meghajtót kérdezni")

        assert (
            tarolo_tipusa(
                r"\\\\szerver\\megosztas\\PicasaPy",
                platform="win32",
                win_drive_type=sosem_hivhato,
            )
            == TAROLO_HALOZATI
        )


class TestAPosixAg:
    @pytest.mark.parametrize(
        "fs,vart",
        [
            ("ext4", TAROLO_HELYI),
            ("btrfs", TAROLO_HELYI),
            ("nfs4", TAROLO_HALOZATI),
            ("cifs", TAROLO_HALOZATI),
            ("fuse.sshfs", TAROLO_HALOZATI),
            ("tmpfs", TAROLO_MEMORIA),
        ],
    )
    def test_a_mount_tipusa_dont(self, fs, vart):
        assert (
            tarolo_tipusa(
                "/home/valaki/PicasaPy",
                platform="linux",
                mount_tipus=lambda _ut: fs,
            )
            == vart
        )

    def test_ismeretlen_mount_NEM_talalgat(self):
        """Rosszabb egy magabiztos téves besorolás, mint a nemtudás."""
        assert (
            tarolo_tipusa(
                "/x", platform="linux", mount_tipus=lambda _ut: None
            )
            == TAROLO_ISMERETLEN
        )

    def test_a_valodi_gepen_sem_dol_el(self):
        """Fogantyú nélkül, éles `/proc/mounts`-szal sem dobhat kivételt."""
        assert tarolo_tipusa(Path.cwd()) in {
            TAROLO_HELYI,
            TAROLO_HALOZATI,
            TAROLO_MEMORIA,
            TAROLO_CSERELHETO,
            TAROLO_ISMERETLEN,
        }


class TestAHibaNemAllitjaMegAzIndulast:
    def test_kivetelre_ismeretlen(self):
        def robban(_ut):
            raise RuntimeError("a mount-olvasó elhasalt")

        assert (
            tarolo_tipusa("/x", platform="linux", mount_tipus=robban)
            == TAROLO_ISMERETLEN
        )


class TestANaploban:
    def _naplo(self, tarolo=None):
        return naplo_szovege(
            idovonal_jelentes="(idővonal)",
            fejlec={},
            meret=KonyvtarMeret(2, 3),
            tarolo=tarolo,
        )

    def test_megjelenik_mindket_hely_tipusa(self):
        szoveg = self._naplo(
            {"a program helye": TAROLO_HALOZATI,
             "a könyvtár helye": TAROLO_HELYI}
        )
        assert "A tároló típusa" in szoveg
        assert f"a program helye: {TAROLO_HALOZATI}" in szoveg
        assert f"a könyvtár helye: {TAROLO_HELYI}" in szoveg

    def test_tarolo_nelkul_nincs_szakasz(self):
        """A régi hívók (és a kikapcsolt diagnosztika) ne kapjanak üres
        fejlécet."""
        assert "A tároló típusa" not in self._naplo(None)


class TestNincsBenneHely:
    """A jegy adatvédelmi kikötése: CSAK a típus, sosem a hely."""

    def test_a_tipusnevek_nem_tartalmaznak_utvonalat(self):
        for tipus in (
            TAROLO_HELYI, TAROLO_HALOZATI, TAROLO_CSERELHETO,
            TAROLO_MEMORIA, TAROLO_ISMERETLEN,
        ):
            assert "/" not in tipus and "\\\\" not in tipus
            assert ":" not in tipus

    def test_a_naploba_nem_szivarog_be_az_ut(self):
        """Még akkor sem, ha valaki később útvonalat adna típusnak — a
        napló `utvonalmentes()` szűrője az utolsó védvonal."""
        szoveg = naplo_szovege(
            idovonal_jelentes="(idővonal)",
            fejlec={},
            meret=KonyvtarMeret(1, 1),
            tarolo={"a program helye": "/home/sancho/PicasaPy"},
        )
        assert "/home/sancho" not in szoveg

    def test_a_windowsos_ag_sem_irja_ki_a_meghajtot(self):
        """A visszaadott érték a TÍPUS neve, nem a betűjel."""
        eredmeny = tarolo_tipusa(
            "D:/Fotok", platform="win32", win_drive_type=lambda _g: 3
        )
        assert "D:" not in eredmeny
