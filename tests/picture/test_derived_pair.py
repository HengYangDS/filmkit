"""An edition's derived uncaptioned picture: its receipt, what refuses a derivation, how either kind
of receipt validates, and the comparison of a derived pair by its record."""

import json

import pytest

import filmkit.media as media
import filmkit.picture.derivation as derivation
import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.repair as repair
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

BAND = {"left": 600, "top": 960, "right": 1320, "bottom": 1000}
GROUND = {"y": 21, "u": 129, "v": 125}
FREE = [[0.0, 0.9], [2.0, 3.0]]


class Tools:
    """The Node tools as a derivation and a comparison run them, each writing the report it is
    set to give."""

    def __init__(self):
        self.runs = []
        self.composition = {
            "format": "caption-equivalence",
            "instants": 7,
            "band": BAND,
            "differing_instants": 0,
            "findings": [],
            "verdict": "equivalent",
        }
        self.audit = {
            "format": "band-audit",
            "instants": 90,
            "caption_instants": 30,
            "caption_rows": [960, 1000],
            "free": FREE,
            "escaping_instants": 0,
            "intruding_instants": 0,
            "escapes": [],
            "intrusions": [],
            "verdict": "pass",
        }

    def __call__(self, tool, arguments, *, stdout, environment=None):
        self.runs.append((tool, arguments))
        report = self.composition if tool == "caption-equivalence" else self.audit
        stdout.write_text(json.dumps(report))
        return 0 if report["verdict"] in ("pass", "equivalent") else 1


@pytest.fixture
def pair(film_root, monkeypatch):
    """The Chinese edition with its captioned picture rendered by the stand-in, the Node tools
    and the derivation's encode replaced, and media checks that pass."""
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    monkeypatch.setattr(media, "probe", lambda path: {})
    monkeypatch.setattr(media, "require_video", lambda *arguments, **options: {})
    monkeypatch.setattr(media, "video_cadence", lambda *arguments: {"keyframes": []})
    monkeypatch.setattr(derivation, "require_derived_media", lambda path: None)
    tools = Tools()
    monkeypatch.setattr(derivation.tools, "run", tools)
    encodes = []

    def derive(source, target, size, rows, frames, work, deadline, *, edges):
        encodes.append({"rows": rows, "frames": frames, "deadline": deadline, "edges": edges})
        target.write_text(f"derived from {repository.sha(source)}")
        check = {"frames": 99, "largest_departure": 1, "verdict": "pass"}
        whole = derivation.DURATION * derivation.FPS
        edge = {"rows": list(edges), "frames": whole, "largest_departure": 0, "verdict": "pass"}
        made = {"ground": GROUND, "command": ["ffmpeg"], "elapsed_seconds": 1.5, "check": check}
        return {**made, "edge_check": edge}

    monkeypatch.setattr(derivation, "derive", derive)
    return edition, tools, encodes


def test_a_derivation_writes_the_picture_and_a_receipt_that_binds_its_source(pair):
    edition, tools, encodes = pair
    captioned, uncaptioned = edition.rendered(True), edition.rendered(False)
    uncaptioned.file.write_text("an earlier uncaptioned picture")
    receipt = derivation.derive_uncaptioned(edition, 600)
    assert repository.read(uncaptioned.receipt) == receipt
    assert (receipt["picture"], receipt["exit"], receipt["timed_out"]) == ("uncaptioned", 0, False)
    assert receipt["uncaptioned"] == {
        "way": "derived",
        "reason": "the film declares software capture, which the engine's release qualifies",
    }
    derived = receipt["derived"]
    assert derived["from"] == "captioned"
    assert derived["source_sha256"] == repository.sha(captioned.file)
    assert derived["source_receipt_sha256"] == repository.sha(captioned.receipt)
    # The band widened by 24 rows on each side and out to 16-pixel blocks of the UHD frame.
    assert (derived["band"], derived["rows"]) == (BAND, [1872, 2048])
    assert (derived["ground"], derived["tolerance"]) == (GROUND, 3)
    assert derived["band_audit"]["verdict"] == derived["ground_check"]["verdict"] == "pass"
    assert receipt["output_sha256"] == repository.sha(uncaptioned.file)
    # The edge rows: 16 at each side, of the 48 between the painted rows and the caption's.
    encode = {"rows": (1872, 2048), "frames": [(4, 50), (124, 176)], "deadline": 600}
    assert encodes == [{**encode, "edges": (16, 16)}]
    assert derived["edge_check"]["rows"] == [16, 16]
    # The band audit is given the rows in the composition's frame, at 30 frames a second.
    assert tools.runs[1] == ("band-audit", [str(edition.timeline), "936", "1024", "30"])
    # Either receipt validates through the same call.
    assert picture_rendering.validate_picture(edition, captions=False) == receipt
    picture_rendering.validate_picture_binding(edition, receipt, captions=False)
    assert derivation.is_derived(receipt)
    assert not derivation.is_derived(repository.read(captioned.receipt))


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            lambda tools: tools.audit.update(
                verdict="refuse",
                intruding_instants=4,
                intrusions=[{"time": 1.5, "kind": "stroke", "scene": "03"}],
            ),
            "a stroke of scene 03 reaches the rows at 1.500 s .* --uncaptioned --native",
        ),
        (
            lambda tools: tools.audit.update(
                verdict="refuse", escaping_instants=2, escapes=[{"time": 0.5, "kind": "text"}]
            ),
            "a caption leaves the rows at 0.500 s",
        ),
        (
            lambda tools: tools.composition.update(differing_instants=3),
            "differs beyond its captions at 3 instants; .* --native",
        ),
        (lambda tools: tools.composition.update(band=None), "paints no caption"),
        (lambda tools: tools.audit.update(free=[[1.0, 1.1]]), "a caption at every instant"),
        (
            lambda tools: tools.audit.update(caption_rows=[936, 1024]),
            "leaves no row free of captions at either edge of the painted rows; .* --native",
        ),
    ],
)
def test_a_refused_derivation_encodes_nothing_and_leaves_no_picture(pair, change, reason):
    edition, tools, encodes = pair
    uncaptioned = edition.rendered(False)
    uncaptioned.file.write_text("an earlier uncaptioned picture")
    repository.write(uncaptioned.receipt, {"picture": "uncaptioned"})
    change(tools)
    with pytest.raises(PictureError, match=reason):
        derivation.derive_uncaptioned(edition)
    assert encodes == []
    assert not uncaptioned.file.exists() and not uncaptioned.receipt.exists()


def test_a_captioned_picture_that_is_not_valid_refuses_before_anything_else(pair):
    edition, tools, encodes = pair
    edition.rendered(True).file.write_text("another picture")
    with pytest.raises(PictureError, match="rendered picture differs from its receipt"):
        derivation.derive_uncaptioned(edition)
    assert (tools.runs, encodes) == ([], [])


def test_a_derived_picture_whose_media_differ_is_removed(pair, monkeypatch):
    edition, _, _ = pair

    def refuse(path):
        message = "keyframes leave the 2 s grid"
        raise PictureError(message)

    monkeypatch.setattr(derivation, "require_derived_media", refuse)
    with pytest.raises(PictureError, match="keyframes"):
        derivation.derive_uncaptioned(edition)
    uncaptioned = edition.rendered(False)
    assert not uncaptioned.file.exists() and not uncaptioned.receipt.exists()


@pytest.fixture
def compared(pair, monkeypatch):
    """A derived pair, compared with the comparison's own tool runs replaced and no decode."""
    edition, tools, _ = pair
    derivation.derive_uncaptioned(edition)
    monkeypatch.setattr(equivalence.tools, "run", tools)

    def decoded(*arguments, **options):
        message = "a derived pair is compared without decoding"
        raise AssertionError(message)

    monkeypatch.setattr(equivalence, "compare_decoded", decoded)
    monkeypatch.setattr(faults, "scan", decoded)
    return edition, tools


def test_a_derived_pair_is_compared_by_its_record_without_decoding(compared):
    edition, _ = compared
    record = equivalence.compare_pictures(edition)
    assert record["verdict"] == "pass"
    assert record["findings"] == []
    assert record["uncaptioned"]["way"] == "derived"
    uncaptioned = record["pictures"]["uncaptioned"]
    assert uncaptioned["derived"] is True and "stage_sha256" not in uncaptioned
    assert "stage_sha256" in record["pictures"]["captioned"]
    derived = record["encoded"]["derived"]
    assert (derived["rows"], derived["ground"]) == ([1872, 2048], GROUND)
    assert derived["ground_check"]["frames"] == 99
    assert derived["edge_check"]["verdict"] == "pass"
    assert repository.read(edition.caption_equivalence) == record
    assert equivalence.require_equivalence(edition) == record


def test_a_captioned_picture_rendered_again_asks_for_the_derivation_again(compared):
    edition, _ = compared
    equivalence.compare_pictures(edition)
    picture_rendering.render_picture(edition, 60)
    edition.rendered(True).file.write_text("rendered again")
    receipt = repository.read(edition.render_receipt)
    receipt["output_sha256"] = repository.sha(edition.rendered(True).file)
    repository.write(edition.render_receipt, receipt)
    with pytest.raises(PictureError, match="binds another source_sha256.* --uncaptioned$"):
        equivalence.compare_pictures(edition)
    with pytest.raises(PictureError, match="binds another pictures"):
        equivalence.require_equivalence(edition)


def test_a_band_other_than_the_painted_one_is_a_finding_that_no_render_repairs(compared):
    edition, tools = compared
    tools.composition["band"] = {**BAND, "top": 900}
    with pytest.raises(PictureError, match="derived pair is not current: the derivation painted"):
        equivalence.compare_pictures(edition)
    record = repository.read(edition.caption_equivalence)
    assert record["verdict"] == "refuse"
    with pytest.raises(PictureError, match="is derived, which rendering a picture again does not"):
        repair.repair_pictures(edition)


def test_a_receipt_without_both_proofs_or_of_another_picture_is_refused(pair):
    edition, _, _ = pair
    receipt = derivation.derive_uncaptioned(edition)
    for proof in ("band_audit", "ground_check", "edge_check"):
        unproven = {**receipt, "derived": {**receipt["derived"], proof: {"verdict": "refuse"}}}
        with pytest.raises(PictureError, match="records no completed derivation"):
            derivation.validate_binding(edition, unproven)
    with pytest.raises(PictureError, match="holds the captioned picture"):
        derivation.validate_binding(edition, {**receipt, "picture": "captioned"})
    edition.rendered(False).file.write_text("another derived picture")
    with pytest.raises(PictureError, match="differs from its receipt"):
        derivation.validate_binding(edition, receipt)


def test_a_ground_refusal_of_the_encode_names_the_native_render(pair, monkeypatch):
    edition, _, _ = pair

    def refuse(*arguments, **options):
        message = "The captioned picture's band is not the ground at frame 40"
        raise PictureError(message)

    monkeypatch.setattr(derivation, "derive", refuse)
    named = "not the ground at frame 40; render the uncaptioned picture with render-picture "
    with pytest.raises(PictureError, match=named + "--language zh --uncaptioned --native"):
        derivation.derive_uncaptioned(edition)


def test_edge_rows_measured_at_fewer_frames_than_the_film_holds_are_refused(pair, monkeypatch):
    edition, _, _ = pair
    whole = derivation.derive

    def short(*arguments, **options):
        made = whole(*arguments, **options)
        return {**made, "edge_check": {**made["edge_check"], "frames": 100}}

    monkeypatch.setattr(derivation, "derive", short)
    with pytest.raises(PictureError, match="edge rows were measured at 100 frames"):
        derivation.derive_uncaptioned(edition)
    assert not edition.rendered(False).file.exists()
