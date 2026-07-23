"""Fotó-szintű XMP sidecar-export a `.picasa.ini`-ből (issue #27).

Ez a réteg köti össze a tiszta XMP-építőt (`xmp.py`) a valós fotókkal: a
kép mellett lévő `.picasa.ini`-ből kiolvassa a hatásos kulcsszavakat,
feliratot és arcrégiókat (a nevet a `[Contacts2]`-ből feloldva, a
`FacesHelper` mintájára), a kép fejlécéből a pixelméretet, majd
digiKam/Lightroom-kompatibilis `.xmp` sidecart ír.

Csak-olvasás a `.picasa.ini` felől (nem módosítjuk), és robusztus: hiányzó
ini/szekció/adat vagy olvashatatlan kép nem dob kivételt — az adott fotó
egyszerűen kimarad vagy dimenzió nélkül exportálódik.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PIL import Image

from picasapy.ini import contacts_of, load_document, parse_faces
from picasapy.scanner import PICASA_INI_NAME

from .xmp import build_sidecar_from_picasa, write_sidecar


def _split_keywords(raw: str | None) -> tuple[str, ...]:
    """A `keywords=` CSV felbontása tiszta címkelistára (vessző az elválasztó)."""
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _dimensions(image_path: Path) -> tuple[int, int] | None:
    """A kép (szélesség, magasság) pixelben — csak a fejléc olvasásával.

    A PIL az ékezetes útvonalakat is helyesen kezeli (a `cv2.imread`-del
    ellentétben). Bármilyen hibánál None — a dimenzió az XMP-ben opcionális.
    """
    try:
        with Image.open(image_path) as image:
            return (int(image.width), int(image.height))
    except Exception:  # noqa: BLE001 — olvashatatlan kép: dimenzió nélkül exportálunk
        return None


def _faces_with_names(document, section_name: str) -> tuple:
    """A `faces=` régiók névvel feloldva (contact_id → [Contacts2] név).

    Névtelen/azonosítatlan arc üres névvel jön vissza — a sidecar-építő
    ezeket kihagyja. Hibás `faces=` érték esetén üres tuple.
    """
    section = document.section(section_name)
    raw_faces = section.get("faces") if section is not None else None
    if not raw_faces:
        return ()
    try:
        faces = parse_faces(raw_faces)
    except ValueError:
        return ()
    names = {
        contact.person_id.casefold(): contact.name
        for contact in contacts_of(document)
    }
    resolved = []
    for face in faces:
        name = names.get(face.contact_id.casefold(), "") if face.is_identified else ""
        resolved.append((face.rect, name))
    return tuple(resolved)


def build_sidecar_for_photo(image_path: Path) -> str | None:
    """Egy fotó XMP-csomagja a melletti `.picasa.ini` alapján (nem ír lemezre).

    None, ha nincs a fotóhoz exportálható adat (nincs ini/szekció, se
    kulcsszó, se felirat, se nevesített arc) — ilyenkor felesleges a sidecar.
    """
    image_path = Path(image_path)
    ini_path = image_path.parent / PICASA_INI_NAME
    if not ini_path.exists():
        return None
    document = load_document(ini_path)
    section = document.section(image_path.name)
    if section is None:
        return None

    keywords = _split_keywords(section.get("keywords"))
    caption = section.get("caption")
    faces = _faces_with_names(document, image_path.name)

    named_faces = tuple((rect, name) for rect, name in faces if name.strip())
    if not keywords and not caption and not named_faces:
        return None

    dimensions = _dimensions(image_path) if named_faces else None
    return build_sidecar_from_picasa(
        keywords=keywords,
        caption=caption,
        faces=faces,
        dimensions=dimensions,
    )


def export_sidecar_for_photo(image_path: Path) -> Path | None:
    """Egy fotó sidecarjának felépítése ÉS kiírása (`<fájlnév>.xmp`).

    Visszatérés: a kiírt sidecar útvonala, vagy None, ha nem volt mit
    exportálni.
    """
    image_path = Path(image_path)
    xmp = build_sidecar_for_photo(image_path)
    if xmp is None:
        return None
    return write_sidecar(image_path, xmp)


def export_sidecars(image_paths: Iterable[Path]) -> tuple[Path, ...]:
    """Több fotó XMP-exportja; az adat nélküli képek kimaradnak.

    Egy fotó hibája nem állítja le a köteget — a hívó (pl. worker-szál) a
    ténylegesen kiírt sidecarok listáját kapja vissza.
    """
    written: list[Path] = []
    for path in image_paths:
        try:
            out = export_sidecar_for_photo(Path(path))
        except Exception:  # noqa: BLE001 — egy rossz fotó nem állíthatja le a köteget
            continue
        if out is not None:
            written.append(out)
    return tuple(written)
