"""Az XMP-arcadatok képműveleti témamixinje."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.export import export_sidecar_for_photo
from picasapy.index import open_index, photos_with_faces


class PhotoOpsXmpMixin:
    xmpFacesFinished = Signal(int, int, str)
    xmpFacesStateChanged = Signal()
    xmpFacesCancelled = Signal(int)

    @Property(bool, notify=xmpFacesStateChanged)
    def xmpFacesActive(self) -> bool:
        """Fut-e épp az XMP-arcírás — a folyamat-panel ettől látszik."""
        return bool(getattr(self, "_xmp_faces_total", 0)) and not getattr(
            self, "_xmp_faces_done_all", True
        )

    @Property(int, notify=xmpFacesStateChanged)
    def xmpFacesDone(self) -> int:
        return int(getattr(self, "_xmp_faces_done", 0))

    @Property(int, notify=xmpFacesStateChanged)
    def xmpFacesTotal(self) -> int:
        return int(getattr(self, "_xmp_faces_total", 0))

    @Slot()
    def cancelXmpFaces(self) -> None:
        """A köteg megszakítása (#1403).

        Az eredeti kötegelt munkája megszakítható, és külön állapotszöveget ad
        rá (`FaceTagJob::cancelled`). A MÁR kiírt sidecarok érvényesek
        maradnak — a megszakítás nem visszavonás, ahogy a csoportos
        szerkesztésnél sem (`cancelBatchEdit`)."""
        esemeny = getattr(self, "_xmp_faces_cancel", None)
        if esemeny is not None:
            esemeny.set()

    @Slot(str, "QVariantList")
    def writeFacesToXmp(self, scope: str, rows) -> None:
        """A kiválasztott hatókör XMP-sidecarjai arcrégiókkal (#1403, #4634).

        Az eredeti parancsa (`eMenuTools::ID_WRITE_XMP_FACES`, `.fen`
        `write_all_facetags`) kötegelt munkaként fut, és a HÁROM állapotát
        külön szöveg nevezi meg (`0x006b9dd0`): `FaceTagJob::progress` /
        `::done` / `::cancelled`. A köteg tehát **megszakítható**, a csak
        olvasható fájl pedig külön, megnevezett hibaeset:

            Face tag write failed for read only file: %s

        Ezért a köteg nem áll le az első hibán: végigmegy, és a végén EGY
        összegzést ad (kiírt · kihagyott · az első hiba oka). Megszakításnál a
        `xmpFacesCancelled` megy ki a MÁR kiírt darabszámmal — azok a
        sidecarok érvényesek maradnak.

        Az adat forrása a `.picasa.ini` (`export.export_sidecar_for_photo`),
        nem az index — így a frissen elnevezett arc is bekerül, mielőtt a
        szinkron végigfut.
        """
        photos = self._photos.photos
        if scope == "selected":
            kijelolt_sorok: set[int] = set()
            for nyers in rows or ():
                try:
                    sor = int(nyers)
                except (TypeError, ValueError):
                    continue
                if 0 <= sor < len(photos):
                    kijelolt_sorok.add(sor)
            photos = [photo for i, photo in enumerate(photos) if i in kijelolt_sorok]
        elif scope == "faces":
            with open_index(self._db_path) as conn:
                arcot_tartalmazo_azonositok = {
                    photo.id for photo in photos_with_faces(conn)
                }
            photos = [
                photo
                for photo in photos
                if photo.id in arcot_tartalmazo_azonositok
            ]
        elif scope != "all":
            # Ismeretlen hatókörrel ne lehessen véletlenül a teljes nézetet írni.
            self.xmpFacesFinished.emit(0, 0, "")
            return

        utak = [Path(photo.folder_path) / photo.name for photo in photos]
        if not utak:
            self.xmpFacesFinished.emit(0, 0, "")
            return

        megszakitas = threading.Event()
        self._xmp_faces_cancel = megszakitas
        self._xmp_faces_total = len(utak)
        self._xmp_faces_done = 0
        self._xmp_faces_done_all = False
        self.xmpFacesStateChanged.emit()

        def worker() -> None:
            kiirt = 0
            kihagyott = 0
            elso_hiba = ""
            megszakitva = False
            for index, ut in enumerate(utak, start=1):
                if megszakitas.is_set():
                    megszakitva = True
                    break
                try:
                    eredmeny = export_sidecar_for_photo(ut)
                except OSError as hiba:
                    kihagyott += 1
                    if not elso_hiba:
                        elso_hiba = f"{ut.name}: {hiba}"
                else:
                    if eredmeny is None:
                        kihagyott += 1
                    else:
                        kiirt += 1
                self._xmp_faces_done = index
                self.xmpFacesStateChanged.emit()
            self._xmp_faces_done_all = True
            self.xmpFacesStateChanged.emit()
            if megszakitva:
                self.xmpFacesCancelled.emit(kiirt)
            else:
                self.xmpFacesFinished.emit(kiirt, kihagyott, elso_hiba)

        self._start_background(worker, name="picasapy-xmp-arcok")
