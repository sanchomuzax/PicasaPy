""".picasa.ini olvasás/írás — kétirányú Picasa 3.x kompatibilitás."""

from .albums import Album, albums_of, parse_album_refs, serialize_album_refs
from .contacts import Contact, contacts_of, ensure_contact, find_contact_id
from .contacts_xml import (
    ContactXmlEntry,
    apply_contacts_xml,
    load_contacts_xml,
    parse_contacts_xml,
)
from .document import (
    NO_SOURCE_FILE,
    IniDocument,
    KeyValueLine,
    Line,
    Section,
    SourceFingerprint,
    parse_document,
)
from .faces import (
    UNIDENTIFIED_CONTACT,
    Face,
    parse_faces,
    serialize_faces,
    with_face,
    with_reassigned_face,
    without_face,
    without_face_at_rect,
)
from .filter_registry import (
    CANONICAL_FILTER_NAMES,
    MAX_PARAM_COUNTS,
    FilterWriteError,
    canonical_filter_name,
    canonicalize_filter_name,
    max_param_count,
)
from .filters import (
    FilterOp,
    canonicalize_op,
    parse_filters,
    serialize_filters,
    serialize_filters_for_write,
    validate_op_for_write,
)
from .folder_category import (
    PROJECTS_CATEGORY,
    is_projects_category,
    read_folder_category,
)
from .folder_date import (
    is_valid_folder_date,
    read_folder_date_override,
    with_folder_date_override,
    without_folder_date_override,
)
from .io import (
    IniConflictError,
    IniSaveError,
    load_document,
    load_or_empty,
    save_document,
    update_document,
)
from .rect64 import Rect64, decode_rect64, encode_rect64

__all__ = [
    "CANONICAL_FILTER_NAMES",
    "MAX_PARAM_COUNTS",
    "Album",
    "Contact",
    "ContactXmlEntry",
    "Face",
    "FilterOp",
    "FilterWriteError",
    "IniConflictError",
    "IniDocument",
    "IniSaveError",
    "KeyValueLine",
    "Line",
    "NO_SOURCE_FILE",
    "PROJECTS_CATEGORY",
    "Rect64",
    "Section",
    "SourceFingerprint",
    "UNIDENTIFIED_CONTACT",
    "albums_of",
    "apply_contacts_xml",
    "canonical_filter_name",
    "canonicalize_filter_name",
    "canonicalize_op",
    "contacts_of",
    "decode_rect64",
    "encode_rect64",
    "ensure_contact",
    "find_contact_id",
    "is_projects_category",
    "is_valid_folder_date",
    "load_contacts_xml",
    "load_document",
    "load_or_empty",
    "max_param_count",
    "parse_album_refs",
    "parse_contacts_xml",
    "parse_document",
    "parse_faces",
    "parse_filters",
    "read_folder_category",
    "read_folder_date_override",
    "save_document",
    "serialize_album_refs",
    "serialize_faces",
    "serialize_filters",
    "serialize_filters_for_write",
    "update_document",
    "validate_op_for_write",
    "with_face",
    "with_folder_date_override",
    "with_reassigned_face",
    "without_face",
    "without_face_at_rect",
    "without_folder_date_override",
]
