"""#4229: a videó vezérlősávja a `movievolume` beállítást használja."""


def test_movievolume_alapertek_es_tarolt_ertek(qml_app):
    _ablak, vezerlo, _konyvtar, _engine = qml_app

    assert vezerlo.movieVolume == 500
    vezerlo.setMovieVolume(275)

    assert vezerlo.movieVolume == 275
    assert int(vezerlo._get_settings().value("movievolume")) == 275


def test_movievolume_a_0_es_1000_kozotti_tartomanyra_szorit(qml_app):
    _ablak, vezerlo, _konyvtar, _engine = qml_app

    vezerlo.setMovieVolume(-10)
    assert vezerlo.movieVolume == 0

    vezerlo.setMovieVolume(1200)
    assert vezerlo.movieVolume == 1000
