"""Az EditSession régióinak és másolásának változatlan forrású mixinje."""

from __future__ import annotations

from typing import TYPE_CHECKING

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64
from picasapy.ini.redeye import (
    EyeCircle64,
    REDEYE_FILTER_NAME,
    build_redeye_op,
    parse_redeye_regions,
)
from picasapy.ini.retouch import (
    RETOUCH_FILTER_NAME,
    RetouchPatch,
    build_retouch_op,
    build_retouch_patches_op,
    parse_retouch_patches,
    parse_retouch_regions,
)

if TYPE_CHECKING:
    from .session import EditSession

class _SessionRegionsMixin:
    def set_retouch_regions(self, regions: tuple[Rect64, ...]) -> EditSession:
        """A retusálási régiók (#148, PicasaPy-saját `retouch=1,<rect64>...;`
        kiterjesztés, ld. `picasapy.ini.retouch`) beállítása/cseréje — a
        crop64/tilt mintájára legfeljebb egy `retouch` réteg lehet a láncban.

        Üres `regions`-nál egyenértékű a `clear_retouch()`-csal (a puszta
        `retouch=1;` flag régió nélkül nem ír be semmit — a lánc-elem
        megléte nélkül nem lenne mit renderelni).

        Args:
            regions: A retusálandó relatív [0..1] téglalapok.

        Returns:
            Új EditSession.
        """
        if not regions:
            return self.clear_retouch()
        new_op = build_retouch_op(regions)
        return self._with_single_layer(
            lambda op: op.matches(RETOUCH_FILTER_NAME), new_op
        )

    def clear_retouch(self) -> EditSession:
        """A retusálási réteg eltávolítása (v1 régió- és v2 folt-alak is)."""
        new_ops = [op for op in self.ops if not op.matches(RETOUCH_FILTER_NAME)]
        return EditSession(ops=tuple(new_ops))

    def retouch_regions(self) -> tuple[Rect64, ...]:
        """A jelenlegi, v1 (téglalap-régiós, #148) retusálási régiók.

        Csak visszamenőleges olvasáshoz (ld. `picasapy.ini.retouch`
        docsztring) — a szerkesztő UI a `retouch_patches()`-t használja.
        Hibás/érvénytelen rect64-nél is üres tuple-t ad (nem dob) — a
        `crop()`/`tilt_param()` #301-mintáját követve idegen/sérült lánc
        olvasása se szökjön ki kivétellel.

        Returns:
            A dekódolt régiók, vagy üres tuple ha nincs (érvényes) v1 retouch.
        """
        for op in self.ops:
            if op.matches(RETOUCH_FILTER_NAME):
                try:
                    return parse_retouch_regions(op)
                except ValueError:
                    return ()
        return ()

    def set_retouch_patches(self, patches: tuple[RetouchPatch, ...]) -> EditSession:
        """A retusálási FOLTOK (#445, PicasaPy-saját `retouch=2,<patch>...;`
        kiterjesztés, ld. `picasapy.ini.retouch`) beállítása/cseréje — a
        crop64/tilt mintájára legfeljebb egy `retouch` réteg lehet a láncban
        (a v1 régiós alakot is ez váltja le, ha lenne).

        Üres `patches`-nél egyenértékű a `clear_retouch()`-csal.

        Args:
            patches: A retusálandó relatív [0..1] foltok (cél+forrás+sugár).

        Returns:
            Új EditSession.
        """
        if not patches:
            return self.clear_retouch()
        new_op = build_retouch_patches_op(patches)
        return self._with_single_layer(
            lambda op: op.matches(RETOUCH_FILTER_NAME), new_op
        )

    def retouch_patches(self) -> tuple[RetouchPatch, ...]:
        """A jelenlegi, v2 (folt-alapú, #445) retusálási foltok.

        Egy v1 (téglalap-régiós) vagy valódi Picasa-eredetű, adat nélküli
        `retouch=1;` bejegyzésnél üres tuple-t ad — ezeket a szerkesztő UI
        nem tudja folt-alakban megjeleníteni (ld. `picasapy.ini.retouch`
        docsztring), de a render-lánc továbbra is alkalmazza őket (a
        `retouch_regions()`-on át). Hibás/érvénytelen kódolásnál is üres
        tuple-t ad (nem dob), a #301-elv szerint.

        Returns:
            A dekódolt foltok, vagy üres tuple ha nincs (érvényes) v2 retouch.
        """
        for op in self.ops:
            if op.matches(RETOUCH_FILTER_NAME):
                try:
                    return parse_retouch_patches(op)
                except ValueError:
                    return ()
        return ()

    def set_redeye_regions(
        self,
        regions: tuple[Rect64, ...],
        *,
        eye_circles: tuple[EyeCircle64, ...] = (),
        full_image_fallback: bool = False,
    ) -> EditSession:
        """A KÉZZEL megjelölt vörösszem-régiók beállítása/cseréje (#445).

        A `redeye` bejegyzésből — a crop64/tilt/retouch mintájára — legfeljebb
        egy réteg lehet a láncban, a helyén cserélve. Üres adatnál a
        bejegyzés bájtra a valódi Picasa alakja (`redeye=1`) marad, amit a
        renderer identitásként kezel. A PicasaPy saját automatikus találatai
        `eye64(...)`-ként, modell nélküli tartalékuk `autofull64()`-ként
        tárolódik. A réteg levételére a `clear_redeye()` (vagy a
        `toggle("redeye")`) való.

        Args:
            regions: A kézzel megjelölt szemek relatív [0..1] téglalapjai.
            eye_circles: Az automatikusan megtalált szemek normalizált körei.
            full_image_fallback: Modell hiányakor használt teljes képes út.

        Returns:
            Új EditSession.
        """
        return self._with_single_layer(
            lambda op: op.matches(REDEYE_FILTER_NAME),
            build_redeye_op(
                regions,
                eye_circles=eye_circles,
                full_image_fallback=full_image_fallback,
            ),
        )

    def clear_redeye(self) -> EditSession:
        """A vörösszem-réteg eltávolítása (minden előfordulása)."""
        return EditSession(
            ops=tuple(op for op in self.ops if not op.matches(REDEYE_FILTER_NAME))
        )

    def redeye_detection_ops(self) -> tuple[FilterOp, ...]:
        """A láncrész, amelynek képméretében a YuNet-köröket megmérjük.

        Meglévő `redeye` réteg cseréjekor az automatikus körök annak helyén
        futnak, ezért csak az előtte álló prefix képe a koordináta-alap.
        Új réteg a lánc végére kerül, így akkor a teljes láncot kell
        detektálni.
        """
        for index, op in enumerate(self.ops):
            if op.matches(REDEYE_FILTER_NAME):
                return self.ops[:index]
        return self.ops

    def redeye_post_detection_ops(self) -> tuple[FilterOp, ...]:
        """A mentett vörösszem-réteg után futó műveletek.

        Ezek nem változtatják meg a detektált kör renderkoordinátáit, de az
        overlay kereteit át kell vetíteni rajtuk a végső előnézethez.
        Új vörösszem-rétegnél nincs utótag, mert az a lánc végére kerül.
        """
        for index, op in enumerate(self.ops):
            if op.matches(REDEYE_FILTER_NAME):
                return self.ops[index + 1 :]
        return ()

    def redeye_regions(self) -> tuple[Rect64, ...]:
        """A jelenlegi, kézzel megjelölt vörösszem-régiók (#445).

        Adat nélküli (`redeye=1;`, valódi Picasa-eredetű) bejegyzésnél üres
        tuple-t ad. Hibás kódolásnál is üres tuple (nem dob), a #301-elv
        szerint.
        """
        for op in self.ops:
            if op.matches(REDEYE_FILTER_NAME):
                try:
                    return parse_redeye_regions(op)
                except ValueError:
                    return ()
        return ()

    def copy_effects(self) -> tuple[FilterOp, ...]:
        """Az effektlánc (filters=, benne a crop64-gyel) „vágólap"-pillanatképe (#152).

        Picasa „Copy All Effects" viselkedése: a teljes láncot (beleértve a
        crop64-et és minden ismeretlen/idegen bejegyzést) másolja, változtatás
        nélkül. A visszaadott `FilterOp` tuple immutábilis — a hívó egy másik
        `EditSession.paste_effects()`-nek adhatja tovább, string-kerülő úton
        (nincs parse/serialize kör), így bitre pontos a round-trip.

        Returns:
            Az `ops` lánc másolata (maguk a `FilterOp` elemek immutábilisak,
            a tuple is új példány, de tartalmilag azonos).
        """
        return tuple(self.ops)

    @classmethod
    def paste_effects(cls, ops: tuple[FilterOp, ...]) -> EditSession:
        """Egy másik kép effektláncának beillesztése (#152).

        Picasa „Paste All Effects" viselkedése: a CÉL kép teljes szerkesztési
        láncát lecseréli a másolt láncra (nem rétegez rá) — a crop64 (és vele
        a `crop=` tükör-kulcs, amit a hívó rétege ír) is átkerül, az ismeretlen
        bejegyzések pedig változatlanul, mert a `copy_effects()`-ből kapott
        `FilterOp`-okat nem parse-oljuk/serializáljuk újra (#73 round-trip elv).

        Undo-barát használat: a hívó a meglévő minta szerint tolja az
        undo-vermet a MEGLÉVŐ (beillesztés előtti) session `to_value()`-jával,
        mielőtt a session-t erre az eredményre cseréli — ugyanúgy, ahogy az
        `EditController` egyéb műveletei teszik (pl. `applyEffect`).

        Args:
            ops: Egy másik `EditSession.copy_effects()` hívás eredménye.

        Returns:
            Új EditSession, a másolt lánccal (a cél korábbi lánca eldobva).
        """
        return cls(ops=tuple(ops))
