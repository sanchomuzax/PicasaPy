"""A bélyegkép renderelése, megjelenítési módja és arc-kivágása."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QImage, QTransform

from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL
from picasapy.scanner import PICASA_INI_NAME
from .display_mode_paint import apply_display_mode_to_qimage, display_mode_from_thumb_id
from .arc_nagyitas_url import arc_from_thumb_id, arcra_vag, szukseges_hosszabb_el
from .thumb_level_url import szint_from_thumb_id
from .thumbnail_provider_jobs import _placeholder

_log = logging.getLogger("picasapy.app.thumbnail_provider")


def _request_image(provider, photo_id, size, requested_size):
    """Szinkron render-mag (a pool-feladat és a tesztek hívják) —
    a korábbi szinkron provider változatlan szerződésével."""
    # a jelzés a lock ALATT megy ki: így az értékek kibocsátási sorrendje
    # a számláló sorrendjét követi (queued kézbesítésnél is), és a busy
    # nem ragadhat be egy megcserélődött 1→0 pár miatt
    with provider._active_lock:
        provider._active += 1
        provider.activeCountChanged.emit(provider._active)
    try:
        try:
            image = provider._render(photo_id)
        except Exception:
            _log.exception("thumbnail-render hiba: %s", photo_id)
            image = QImage()
        if image.isNull():
            image = _placeholder()
        else:
            #: #2187: az arc-nagyítás (`&fz=`) a gyorstárak UTÁN vág — a
            #: `_render` gyorstárai (lemez, `_FilteredThumbMemo`) a
            #: teljes képet tartják. Cimke nélkül ez egyetlen
            #: sztring-próba: a rendes út nem változik.
            arc = arc_from_thumb_id(photo_id)
            if arc is not None:
                image = arcra_vag(provider._arc_forras(photo_id, image, arc), arc)
        # Megjelenítési mód (#1596) — a render-mag UTÁN, a gyorstárakat
        # ÉRINTETLENÜL hagyva.
        #
        # A sorrend a jegy lényege: a `_render` írja a lemezes
        # bélyegképet és a `_FilteredThumbMemo` rekeszét. Ha a festés
        # ELŐBB futna, a mód BELEÉGNE a tárolt bélyegképbe — kikapcsolva
        # is festve maradna a kép, és a webexport/kollázs is a képernyő
        # figyelmeztető színét vinné tovább. A mód megjelenítési
        # átalakító, nem a bélyegkép tartalma.
        #
        # A mód magából az URL-ből jön (`&d=<mód>`), nem a szolgáltató
        # állapotából: így az URL egyértelműen meghatározza a
        # képpontokat, és egy gyors módváltás nem tud rossz módú képet
        # beragasztani a Qt URL-kulcsú gyorstárába. Ld.
        # `display_mode_paint` modul-docstring.
        image = apply_display_mode_to_qimage(
            image, display_mode_from_thumb_id(photo_id)
        )
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
    finally:
        with provider._active_lock:
            provider._active -= 1
            provider.activeCountChanged.emit(provider._active)


def _arc_forras(
    provider,
    photo_id: str,
    image: QImage,
    arc: tuple,
    original_reader,
) -> QImage:
    """Az arc-vágás forrásképe (#2187): akkora, hogy a kivágott négyzet
    oldala elérje a kért cellát (`&sz=`, cimke nélkül a felső szint).

    Sorrend, a legolcsóbbtól: a már kész `image`, ha elég; a tár egy
    nagyobb szintje; az eredeti fájl (`arc_eredetibol`). Szerkesztett
    képnél az eredeti fájl a `filters=` láncot nem hordozza, ezért ott a
    felső szint a határ."""
    cella = szint_from_thumb_id(photo_id) or provider.top_level
    hosszabb = szukseges_hosszabb_el(image.width(), image.height(), arc, cella)
    if hosszabb is None:
        return image
    jelenlegi = max(image.width(), image.height())
    for szint in provider._cache.levels:
        if jelenlegi < szint and szint >= hosszabb:
            return provider._render_szinten(photo_id, szint) or image
    photo = provider._photo_for_render(photo_id)
    if photo is not None and not provider._resolved_ops(photo)[0]:
        eredeti = original_reader(
            Path(photo.folder_path) / photo.name,
            hosszabb,
            photo.rotate_steps,
            int(getattr(photo, "flip_flags", 0) or 0),
        )
        if eredeti is not None and not eredeti.isNull():
            return eredeti
    if jelenlegi < provider.top_level:
        return provider._render_szinten(photo_id, provider.top_level) or image
    return image


def _render_szinten(provider, photo_id: str, szint: int) -> QImage | None:
    """A `_render` a megadott szinten (az URL `&sz=` cimkéjét cseréljük);
    `None`, ha nem készült el."""
    alap, _, query = photo_id.partition("?")
    parameterek = [
        p for p in query.split("&") if p and not p.startswith("sz=")
    ]
    kep = provider._render(f"{alap}?{'&'.join([*parameterek, f'sz={szint}'])}")
    return None if kep.isNull() else kep


def _render(provider, photo_id: str, cache_reader) -> QImage:
    """A kész (szerkesztett, forgatott) thumbnail; null-QImage, ha a
    forrás nem dekódolható — a hívó ebből csinál placeholdert."""
    # az URL-ben ?r=<lépés> cache-buster jöhet — az id az első rész
    photo = provider._photo_for_render(photo_id)
    if photo is None:
        return QImage()
    path = Path(photo.folder_path) / photo.name
    mtime_ns, size_bytes = photo.mtime_ns, photo.size
    rotate = photo.rotate_steps
    #: #2902: a tükrözés a forgatás párja — ugyanúgy nem-destruktív, és
    #: ugyanúgy a KÉSZ kis bélyegképen történik.
    flip = int(getattr(photo, "flip_flags", 0) or 0)
    ops, chain_crc = provider._resolved_ops(photo)
    crop, crop_ini_readable = (
        provider._crop_reader.read(path.parent / PICASA_INI_NAME, photo.name)
        if ops
        else (None, True)
    )
    # #144: szűrt képnél előbb a memóriacache — találatnál a filters-
    # lánc, a lemez-dekód és a forgatás is kimarad. A crop kulcs is a
    # kulcs része, mert az nem szerepel a PhotoRecord indexrekordjában.
    memo_key = (
        str(path),
        mtime_ns,
        size_bytes,
        chain_crc,
        crop,
        crop_ini_readable,
        rotate,
        flip,
    )
    if ops:
        cached = provider._memo.get(memo_key)
        if cached is not None:
            return cached
    # szerkesztő-lánc (filters=) a bélyegképen is (#59): a szűrt bélyegkép
    # a #163 óta NAGY bázison készül és külön cache-fájlba kerül — a
    # vágott kép így éles marad, nem a kész kis thumbnailt vágjuk tovább
    # (ami felnagyítva homályos lenne). A forgatás lentebb, a kész kis
    # bélyegképen történik (veszteségmentes 90°-os lépés).
    #: #598: a SZINT az URL-ből jön (`&sz=`), nem a szolgáltató
    #: állapotából — ugyanaz az elv, mint a megjelenítési módnál: az URL
    #: egyértelműen meghatározza a képpontokat, így a Qt URL-kulcsú
    #: gyorstárába nem ragadhat be más szintű kép.
    szint = szint_from_thumb_id(photo_id)
    def kesz_thumb():
        if ops:
            return provider._cache.get_or_create_edited(
                path,
                mtime_ns,
                size_bytes,
                ops,
                szint,
                crop=crop,
                crop_ini_readable=crop_ini_readable,
            )
        return provider._cache.get_or_create(path, mtime_ns, size_bytes, szint)

    thumb = kesz_thumb()
    if thumb is None:
        _log.warning("thumbnail nem készült el: %s", path)
        provider.brokenImageDetected.emit(str(photo.id))
        return QImage()
    image = cache_reader(thumb)
    if image.isNull():
        # A cache-fájl olvashatatlansága nem a fotó sérülése (#5553): a
        # bélyegkép a forrásból újraírható. Sérültfotó-jelzés csak akkor
        # megy, ha a forrásból sem készül bélyegkép.
        thumb.unlink(missing_ok=True)
        thumb = kesz_thumb()
        if thumb is None:
            _log.warning("thumbnail nem készült el: %s", path)
            provider.brokenImageDetected.emit(str(photo.id))
            return QImage()
        image = cache_reader(thumb)
    if image.isNull():
        _log.warning("cache-elt thumbnail nem olvasható: %s", thumb)
        return image
    if rotate:
        # nem-destruktív ini-forgatás (a cache-elt thumb forgatatlan)
        image = image.transformed(QTransform().rotate(90 * rotate))
    if flip:
        # #2902: a `QImage.mirrored` maga is új képet ad — a gyorstárban
        # tükrözetlen bélyegkép marad, ahogy a forgatásnál is
        image = image.mirrored(bool(flip & FLIP_HORIZONTAL),
                               bool(flip & FLIP_VERTICAL))
    if ops:
        provider._memo.put(memo_key, image)
    return image
