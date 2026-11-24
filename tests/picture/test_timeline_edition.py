"""A picture is drawn from a timeline that states its own edition, which the assembly writes
(`filmkit.soundtrack.assembly`); staging refuses one that states none or another edition's."""

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.errors import PictureError
from filmkit.production import Edition


@pytest.mark.parametrize(("stated", "named"), [(None, "states no edition"), ("en", "states en")])
def test_a_timeline_without_its_own_edition_is_refused(film_root, stated, named):
    edition = Edition("zh")
    timeline = repository.read(edition.timeline)
    timeline.pop("edition", None)
    if stated:
        timeline["edition"] = stated
    with pytest.raises(PictureError, match=f"timeline.json {named}; assemble the zh edition"):
        picture_rendering.film_data(edition, 0, timeline=timeline)
    assert '"edition": "zh"' in picture_rendering.film_data(edition, 0)
