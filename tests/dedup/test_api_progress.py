"""#294: haladás-jelzés, megszakítás és külső dHash-forrás a
`find_duplicates`-en — a `sync_tree` (#209/#216) progress/should_stop
mintája szerint."""

import pytest

from picasapy.dedup import find_duplicates
from picasapy.dedup.api import PHASE_EXACT, PHASE_HASH

from support.jpeg_factory import make_jpeg
from support_images import gradient_jpeg, resave_as_jpeg


@pytest.fixture
def library(tmp_path):
    """Négy kép: egy bitre azonos pár és egy hasonló (átméretezett) pár."""
    original = make_jpeg(tmp_path / "a.jpg", size=(40, 20))
    copy = tmp_path / "b.jpg"
    copy.write_bytes(original.read_bytes())
    big = gradient_jpeg(tmp_path / "c.jpg", size=(256, 256))
    small = resave_as_jpeg(big, tmp_path / "d.jpg", size=(64, 64), quality=70)
    return [original, copy, big, small]


class TestProgress:
    def test_reports_both_phases_up_to_the_total(self, library):
        events = []
        find_duplicates(library, progress=lambda *args: events.append(args))

        assert events, "haladás-jelzés egyáltalán nem érkezett"
        phases = {phase for phase, _done, _total in events}
        assert phases == {PHASE_EXACT, PHASE_HASH}
        for phase in phases:
            steps = [event for event in events if event[0] == phase]
            assert steps[-1][1] == steps[-1][2], phase  # kész == összes
            assert [step[1] for step in steps] == sorted(
                step[1] for step in steps
            ), phase  # monoton növekvő

    def test_total_is_the_number_of_input_paths(self, library):
        events = []
        find_duplicates(library, progress=lambda *args: events.append(args))
        assert {event[2] for event in events} == {len(library)}

    def test_without_callback_nothing_breaks(self, library):
        assert find_duplicates(library).exact_groups


class TestCancellation:
    def test_should_stop_returns_cancelled_report(self, library):
        report = find_duplicates(library, should_stop=lambda: True)

        assert report.cancelled is True
        assert report.exact_groups == ()
        assert report.similar_groups == ()

    def test_truthy_progress_return_cancels(self, library):
        seen = []

        def progress(phase, done, total):
            seen.append((phase, done, total))
            return True  # megszakítás-kérés, a sync_tree mintája szerint

        report = find_duplicates(library, progress=progress)

        assert report.cancelled is True
        assert len(seen) == 1  # az első jelzés után azonnal leáll

    def test_uncancelled_report_says_so(self, library):
        assert find_duplicates(library).cancelled is False


class TestExternalHashSource:
    def test_cached_hashes_skip_recomputation(self, library):
        """A hívó (index-gyorsítótár) által ismert hash-eket nem szabad
        újraszámolni — ez teszi a második keresést azonnalivá."""
        computed = []

        def source(path):
            computed.append(path)
            return 0  # minden kép azonos lenyomatot kap

        report = find_duplicates(library, dhash_source=source)

        assert computed == list(library)
        # minden hash azonos → egyetlen hasonló csoport a nem-pontos képekre
        assert len(report.similar_groups) == 1

    def test_none_from_source_skips_the_image(self, library):
        report = find_duplicates(library, dhash_source=lambda path: None)
        assert report.similar_groups == ()
        assert report.exact_groups  # a pontos réteg ettől független
