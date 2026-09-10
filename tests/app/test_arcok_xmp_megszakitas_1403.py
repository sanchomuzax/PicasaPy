"""Az XMP-arcírás köteg MEGSZAKÍTHATÓ (#1403).

Az eredeti kötegelt munkája három állapotot nevez meg (`0x006b9dd0`):

```
FaceTagJob::progress    → Writing face tags
FaceTagJob::done        → Done writing face tags
FaceTagJob::cancelled   → Cancelled writing face tags
```

A `::cancelled` külön szöveg — vagyis a megszakítás NEM ugyanaz, mint a
befejezés, és a felhasználónak külön visszajelzés jár. A már kiírt sidecarok
érvényesek maradnak (a megszakítás nem visszavonás, ahogy a csoportos
szerkesztésnél sem).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication, QSettings
from support.jpeg_factory import make_jpeg

from picasapy.index import open_index, sync_tree


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    ini = ["[Contacts2]", "1=Anna;;"]
    for i in range(6):
        make_jpeg(gyoker / f"k{i}.jpg")
        ini[:0] = [f"[k{i}.jpg]", "faces=rect64(4000400080008000),1"]
    (gyoker / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    yield ctl, gyoker
    ctl.shutdown()


class TestAMegszakitas:
    def test_a_megszakitas_KULON_jelzest_ad(self, vezerlo):
        """A `::cancelled` az eredetiben külön állapotszöveg."""
        ctl, gyoker = vezerlo
        ctl.selectFolder(str(gyoker))
        QCoreApplication.processEvents()
        megszakitva = []
        befejezve = []
        ctl.xmpFacesCancelled.connect(megszakitva.append)
        ctl.xmpFacesFinished.connect(lambda k, h, o: befejezve.append(k))

        # az első fájl után megszakítjuk: a kapcsoló a köteg CIKLUSÁBAN
        # ellenőrződik, tehát a hívás sorrendje nem versenyfeltétel
        ctl.cancelXmpFaces()  # még nincs köteg — nem szabad elhasalnia
        ctl.writeFacesToXmp()
        ctl.cancelXmpFaces()
        assert ctl.waitForBackgroundWorkers(15.0), "a köteg nem állt le"
        QCoreApplication.processEvents()

        assert megszakitva or befejezve, "valamelyik állapotnak ki kell mennie"
        if megszakitva:
            assert not befejezve, (
                "megszakításnál NEM mehet ki a befejezés jelzése is — az "
                "eredetiben ez két külön állapot"
            )

    def test_a_mar_kiirt_sidecarok_MEGMARADNAK(self, vezerlo):
        """A megszakítás nem visszavonás."""
        ctl, gyoker = vezerlo
        ctl.selectFolder(str(gyoker))
        QCoreApplication.processEvents()
        ctl.writeFacesToXmp()
        assert ctl.waitForBackgroundWorkers(15.0)
        QCoreApplication.processEvents()

        # megszakítás nélkül mind a hat kiíródik — ez a kontroll
        assert len(list(gyoker.glob("*.xmp"))) == 6

    def test_a_halados_szamlalo_a_kotegtol_jon(self, vezerlo):
        ctl, gyoker = vezerlo
        ctl.selectFolder(str(gyoker))
        QCoreApplication.processEvents()

        assert ctl.xmpFacesTotal == 0, "köteg előtt nincs mit mutatni"
        ctl.writeFacesToXmp()
        assert ctl.xmpFacesTotal == 6, "a panel a TELJES darabszámot mutatja"
        assert ctl.waitForBackgroundWorkers(15.0)
        QCoreApplication.processEvents()
        assert ctl.xmpFacesDone == 6
        assert ctl.xmpFacesActive is False, (
            "a köteg végén a panelnek el kell tűnnie"
        )
