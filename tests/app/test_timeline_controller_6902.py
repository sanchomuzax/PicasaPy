"""A Recently Updated virtuális kártya az Időrend teljes fotóhalmazát kapja (#6902)."""

import os
import time
from pathlib import Path

from picasapy.app.timeline_controller import TimelineController
from picasapy.index import open_index, sync_tree
from picasapy.ini import RECENT_ALBUM_TOKEN
from support.jpeg_factory import make_jpeg


class _Provider:
    def register_photos(self, photos):
        self.photos = tuple(photos)


def test_reload_adds_recently_updated_virtual_album_with_its_exact_photo_set(
    tmp_path
):
    library = tmp_path / "library"
    folder = library / "2019_marcius"
    folder.mkdir(parents=True)
    recent = folder / "recent.jpg"
    old = folder / "old.jpg"
    make_jpeg(recent, size=(96, 72))
    make_jpeg(old, size=(96, 72))
    stale_time = time.time() - 30 * 24 * 60 * 60
    os.utime(old, (stale_time, stale_time))

    database = tmp_path / "index.db"
    with open_index(database) as conn:
        sync_tree(conn, library)

    controller = TimelineController(database, _Provider())
    controller.setTimelineOpen(True)

    recent_cards = [
        card
        for card in controller.collections
        if card["albumToken"] == RECENT_ALBUM_TOKEN
    ]
    assert len(recent_cards) == 1
    card = recent_cards[0]
    assert card["kind"] == "album"
    assert card["name"] == "Recently Updated"
    assert card["count"] == 1
    assert [photo["name"] for photo in card["photos"]] == ["recent.jpg"]

    slideshow = controller.slideshowModel(card["collectionId"])
    assert slideshow.rowCount() == 1
    assert Path(slideshow.filePathAt(0)) == recent
