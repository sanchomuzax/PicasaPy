"""Az észlelt arcok indexműveleteinek kompatibilitási homlokzata.

A nyilvános nevek és az eredeti importútvonal itt maradnak; a megvalósítás
rekord-, lekérdezési és szkennelési modulokra oszlik.
"""

from ._faces_detected_store import (
    PendingEmbeddingFace,
    clear_faces,
    detected_face_count,
    face_embedding,
    faces_missing_embedding,
    replace_faces,
    replace_imported_unnamed_faces,
    reset_all_faces,
    store_embedding,
)
from ._faces_detected_queries import (
    UnnamedFace,
    _faces_in_state as _faces_in_state,
    _faces_where as _faces_where,
    faces_for_photo,
    ignored_faces,
    mark_faces_ignored,
    mark_faces_named,
    named_centroids,
    set_suggested_name,
    suggested_album_photos,
    suggested_faces,
    suggested_faces_for,
    unignore_faces,
    unnamed_album_photos,
    unnamed_face_count,
    unnamed_faces,
    unnamed_faces_for_photos,
    unnamed_photo_count,
)
from ._faces_detected_scan import (
    OK_DETEKTALVA as OK_DETEKTALVA,
    OK_KIZARVA as OK_KIZARVA,
    _MAPPAFA_FELTETEL as _MAPPAFA_FELTETEL,
    _like_vedett as _like_vedett,
    _mappafa_parameterek as _mappafa_parameterek,
    delete_faces_in_folder,
    face_scan_done,
    forget_face_scan,
    mark_face_scan,
    mark_folder_excluded,
)

# A nyilvános objektumok korábban ebből a modulból származtak. A beállítás
# megőrzi az introspekciós és pickle-importútvonalat a kompatibilitási rétegen.
_PUBLIC_OBJECTS = (
    PendingEmbeddingFace,
    clear_faces,
    detected_face_count,
    face_embedding,
    faces_missing_embedding,
    replace_faces,
    replace_imported_unnamed_faces,
    reset_all_faces,
    store_embedding,
    UnnamedFace,
    faces_for_photo,
    ignored_faces,
    mark_faces_ignored,
    mark_faces_named,
    named_centroids,
    set_suggested_name,
    suggested_album_photos,
    suggested_faces,
    suggested_faces_for,
    unignore_faces,
    unnamed_album_photos,
    unnamed_face_count,
    unnamed_faces,
    unnamed_faces_for_photos,
    unnamed_photo_count,
    delete_faces_in_folder,
    face_scan_done,
    forget_face_scan,
    mark_face_scan,
    mark_folder_excluded,
)
for _public_object in _PUBLIC_OBJECTS:
    _public_object.__module__ = __name__

del _PUBLIC_OBJECTS, _public_object
