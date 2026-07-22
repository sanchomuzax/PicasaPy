""".picasa.ini olvasás/írás — kétirányú Picasa 3.x kompatibilitás."""

from .albums import Album, albums_of, parse_album_refs, serialize_album_refs
from .contacts import Contact, contacts_of
from .document import IniDocument, KeyValueLine, Line, Section, parse_document
from .faces import UNIDENTIFIED_CONTACT, Face, parse_faces, serialize_faces
from .filters import FilterOp, parse_filters, serialize_filters
from .io import IniSaveError, load_document, load_or_empty, save_document
from .rect64 import Rect64, decode_rect64, encode_rect64

__all__ = [
    "Album",
    "Contact",
    "Face",
    "FilterOp",
    "IniDocument",
    "IniSaveError",
    "KeyValueLine",
    "Line",
    "Rect64",
    "Section",
    "UNIDENTIFIED_CONTACT",
    "albums_of",
    "contacts_of",
    "decode_rect64",
    "encode_rect64",
    "load_document",
    "load_or_empty",
    "parse_album_refs",
    "parse_document",
    "parse_faces",
    "parse_filters",
    "save_document",
    "serialize_album_refs",
    "serialize_faces",
    "serialize_filters",
]
