"""#4511: render face crops, enter a name, and refresh the panel."""

import pytest

from test_people_panel_26 import (
    _run_named_and_unnamed_faces_render_and_name_through_the_panel,
)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_face_rows_and_enter_naming_at_nearby_heights(
    qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
):
    _run_named_and_unnamed_faces_render_and_name_through_the_panel(
        qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
    )
