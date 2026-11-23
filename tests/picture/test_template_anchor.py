"""The picture template's language anchor, `<html lang="und">`, which staging replaces with the
edition's language tag, as it replaced the former anchor `<html lang="zh-CN">`."""

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.picture.template as picture_template
import filmkit.repository as repository
from filmkit.production import Edition

RUNTIME = 1477


@pytest.mark.parametrize("code", ["zh", "en"])
def test_the_template_anchored_on_und_stages_the_page_the_former_anchor_staged(
    code, film_root, monkeypatch
):
    edition = Edition(code)
    page = repository.ROOT / picture_rendering.COMPOSITION / "index.html"
    staged = picture_rendering.picture_html(edition, RUNTIME, 3840, 2160, 0)
    assert '<html lang="und">' in page.read_text()
    page.write_text(page.read_text().replace('<html lang="und">', '<html lang="zh-CN">'))
    former = (('<html lang="zh-CN">', 1), *picture_template.ANCHORS[1:])
    monkeypatch.setattr(picture_template, "ANCHORS", former)
    assert picture_rendering.picture_html(edition, RUNTIME, 3840, 2160, 0) == staged
    assert f'<html lang="{edition.declaration.tag}">' in staged
