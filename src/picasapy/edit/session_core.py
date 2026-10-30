"""Az EditSession alapláncának változatlan forrású mixinje."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from picasapy.ini.filters import (
    FilterOp,
    canonicalize_op,
    parse_filters,
    serialize_filters,
    validate_op_for_write,
)
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

if TYPE_CHECKING:
    from .session import EditSession

# A finomhangolás (#20) egyetlen finetune2 réteg, a tilt/crop mintájára a
# láncban a helyén cserélődik (nem rétegződik). A v1 "finetune"-t is ez
# kezeli (mindkét nevet ugyanaz a réteg jelenti).
_FINETUNE_NAMES = ("finetune2", "finetune")
_FINETUNE_CANONICAL = "finetune2"
# p4 (semleges-szín pipetta) alapértéke: nulla alfa = nincs kijelölt szín.
_NEUTRAL_DEFAULT = "00000000"

@dataclass(frozen=True)
class FinetuneValues:
    """A finetune2 négy csúszkája + a pipetta-szín (round-triphez megőrzött).

    fill/highlights/shadows ∈ [0..1], temperature ∈ [-1..1]; neutral az
    AARRGGBB hex (p4), változatlanul visszaírva."""

    fill: float
    highlights: float
    shadows: float
    temperature: float
    neutral: str = _NEUTRAL_DEFAULT

class _SessionCoreMixin:
    @classmethod
    def from_value(cls, value: str | None) -> EditSession:
        """Parse a `filters=` érték stringből.

        Args:
            value: A filters= érték; None vagy üres string üres láncot ad.

        Returns:
            Új EditSession.
        """
        if not value:
            return cls()
        ops = parse_filters(value)
        return cls(ops=ops)

    def to_value(self) -> str:
        """Stringgé konvertál (serialize) — a `.picasa.ini`-be írható alakban.

        **#695:** a regiszterbeli szűrők neve itt a KANONIKUS (Picasa által
        várt) alakra áll be. Az eredeti Picasa bájtra illeszti a nevet, és a
        nem egyező bejegyzést némán elejti — ha a saját írásmódunkkal írnánk
        vissza a láncot, a felhasználó szerkesztése a windowsos Picasában
        eltűnne. Ez nem sérti a round-trip elvet: a NEM módosított
        `filters=` érték soha nem jön erre (a document-réteg nyersen tárolja),
        ide csak az általunk módosított lánc jut el.

        Az ismeretlen (idegen/jövőbeli) szűrőnevek változatlanul mennek ki.
        A paraméterszám ellenőrzése SZÁNDÉKOSAN nincs itt: a láncban
        maradhatnak idegen eredetű, hibás elemek, azokat bájtra meg kell
        őriznünk (#301). Az író-oldali kapu ott zár, ahol az elem
        KELETKEZIK (`append_effect`, `apply`, `set_*`), illetve explicit
        igény esetén a `serialize_filters_for_write`-ban.

        Returns:
            A filters= érték stringje.
        """
        return serialize_filters(tuple(canonicalize_op(op) for op in self.ops))

    def append_crop(self, rect: Rect64) -> EditSession:
        """Új `crop64` réteg a lánc VÉGÉRE — a korábbiak érintetlenül maradnak.

        **#1553 — miért halmozás, és nem csere.** A metódus 2026-08-27-ig
        `set_crop` néven a `_with_single_layer` „legfeljebb egy réteg"
        szabályát követte. Ez a szabály a #19/#47 eredeti kódjából jött,
        bizonyíték nélkül (a #302 csak közös helperbe emelte). Egy
        Picasa-eredetű, több-vágásos láncnál az ELSŐ Alkalmaz eldobta a
        korábbi `crop64`-eket; mérve, a valódi gombra kattintva:
        `crop64=1,0000000080008000;bw=1;crop64=1,c0008000ffffffff;` +
        Alkalmaz → `crop64=1,40004000c000c000;bw=1;`.

        Az eredeti Picasa HALMOZ; három, egymástól független bizonyíték:

        1. **A `filters=` MAGA a visszavonás-verem.** A `CFilterStackUI`
           frissítője (`Picasa3.exe`, `0x006ad530`) a visszavonás-listát a
           `"filters"`, az újra-listát a `"redo"` tulajdonságból építi —
           ugyanaz a `0x0069f510` hívás, két kulccsal —, és a Visszavonás
           felirata a lánc UTOLSÓ elemének a neve (`0x00753c46`). Egy
           meglévő elem helyben cserélése az előzményt semmisítené meg.
        2. **Az eredeti saját felirat-párja:** `IDS_CROP_LABEL` = „Crop" és
           `IDS_RECROP_LABEL` = „Recrop" (magyarul **„Vágás megismétlése"**).
           A `0x007533b0` a `0x006b0140` („van-e már érvényes vágás")
           válasza szerint választ köztük: az újravágás önálló, névvel bíró
           művelet, nem a meglévő vágás átírása.
        3. **Az éles korpusz:** 38 lánc tartalmaz több `crop64`-et, 33-ban a
           két téglalap átfedése IoU > 0,5 (ugyanaz a kivágás újraigazítva),
           14-ben további szűrők állnak az utolsó `crop64` UTÁN. A
           `scan0016.png` szekcióban maga a Picasa írt egy
           `redo=crop64=1,14effffdca5;enhance=1;crop64=1,ffffdca5;` sort — a
           redo-verem csak Visszavonásra töltődik, tehát ez a lánc valóban a
           Picasa `filters=` visszavonás-verme volt.

        A HATÁLYOS vágás továbbra is az utolsó (`crop()`, #1550), tehát a
        render és a `crop=` tükörkulcs változatlan; csak az előzmény marad
        meg mellette.

        Args:
            rect: Az új Rect64 téglalap.

        Returns:
            Új EditSession.
        """
        new_op = _new_op("crop64", ("1", encode_rect64(rect)))
        return EditSession(ops=self.ops + (new_op,))

    def clear_crop(self) -> EditSession:
        """Crop64 eltávolítása."""
        new_ops = [op for op in self.ops if not op.matches("crop64")]
        return EditSession(ops=tuple(new_ops))

    def crop(self) -> Rect64 | None:
        """A HATÁLYOS crop64 téglalap — a lánc UTOLSÓ érvényes bejegyzése.

        **#1550 — miért az utolsó, és nem az első.** A láncban több `crop64`
        is állhat: a felhasználó gyűjteményét a windowsos Picasa írta, és a
        PicasaPy maga is halmoz újravágáskor (`append_crop`, #1553). Korábban
        ez a metódus az ELSŐT adta, ami két, egymástól független
        bizonyítéknak mondott ellent:

        1. **A render-lánc** (`render/chain.py`, #130) az UTOLSÓ `crop64`-et
           alkalmazza — a bejárás felülírja a `crop_op`-ot. Mérve: 800×600-as
           képre a `crop64=1,0000000080008000;bw=1;crop64=1,c0008000ffffffff;`
           lánc **200×300**-at ad; az első szerint 400×300 lenne.
        2. **Az éles korpusz** (859 `.picasa.ini`, 18 801 szekció): a 38
           több-`crop64`-es láncnál **38/38** esetben a `crop=rect64(...)`
           tükör-kulcs az UTOLSÓT tükrözi, az elsőt **nulla** esetben.

        Így a szerkesztő felülete (`hasCrop`, `cropSelection`) és a mentés
        (`_save`) ugyanazt a téglalapot használja, amit a kép ténylegesen
        hordoz. A `crop_mirror_value()` (#1544) is erre az útra épül.

        A lánc maga NEM módosul ettől: a korábbi `crop64`-ek bent maradnak,
        ők a visszavonás alapja (`_seed_undo_from_chain`).

        Hibás/érvénytelen hex paraméternél is `None`-t ad (nem dob) — idegen
        vagy sérült lánc olvasása se szökjön ki kivétellel (#301). A
        2. paraméter nélküli (`crop64=1;`) bejegyzés nem hatályos: azt
        átlépjük, és a lánc előbbi utolsó érvényes bejegyzése számít.

        Returns:
            Rect64 a dekódolt értékkel, vagy None ha nincs (érvényes) crop64.
        """
        for op in reversed(self.ops):
            if op.matches("crop64"):
                if len(op.params) >= 2:
                    try:
                        return decode_rect64(op.params[1])
                    except ValueError:
                        return None
        return None

def _new_op(name: str, params: tuple[str, ...]) -> FilterOp:
    """Új lánc-elem az ÍRÓ kapun át (#695).

    Minden itt keletkező bejegyzés a regiszterbeli (Picasa által várt)
    írásmóddal és megengedett paraméterszámmal jön létre — így soha nem
    írunk ki olyan elemet, amit az eredeti Picasa némán elejtene.

    Args:
        name: A szűrő neve (bármilyen írásmódban).
        params: A paraméterek; a `params[0]` az engedélyező flag.

    Returns:
        A kanonikus nevű, ellenőrzött `FilterOp`.

    Raises:
        FilterWriteError: Ha a paraméterszám kilóg a regiszterbeliből.
    """
    op = canonicalize_op(FilterOp(name, params))
    validate_op_for_write(op)
    return op
