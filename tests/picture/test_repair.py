"""Repair attributed one-frame faults: render again only the pictures that a refused comparison
names, within an attempt limit, keeping each faulty picture, its receipt and the refused record."""

import hashlib
import sys

import pytest
from test_faults import (
    BAND,
    CAPTION,
    CUES,
    FRAGMENT,
    NEXT,
    SECONDS,
    SIZE,
    encode,
    reporting,
    square,
)

import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.repair as picture_repair
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

RENDER = "python -m filmkit.produce render-picture --language zh"
COMPARE = "python -m filmkit.produce compare-pictures --language zh"
# The fault that compare-pictures attributes to the uncaptioned picture holding FRAGMENT.
FAULT = {
    "frame": 77,
    "time": 1.283,
    "box": [40, 10, 44, 14],
    "peak": 150,
    "picture": "uncaptioned",
    "caption_band": False,
    "residue": False,
}
REPAIRS = "build/evidence/editions/zh/picture-repairs"
# The fragment of FRAGMENT at frame 90, which the sampled measures compare too.
SAMPLED = square(40, 10, 170, "eq(n,90)")


@pytest.fixture
def pair(film_root, monkeypatch):
    """The Chinese edition with one caption and both pictures staged and checked, compared as
    pictures of 96x54 and two seconds."""
    monkeypatch.setattr(equivalence, "PICTURE_SIZE", SIZE)
    monkeypatch.setattr(equivalence, "DURATION", SECONDS)
    monkeypatch.setattr(equivalence, "validate_picture", lambda _edition, captions: {})
    monkeypatch.setattr(equivalence.tools, "run", reporting(BAND))
    edition = Edition("zh")
    film_root.timeline(edition, captions=CUES)
    film_root.staged(edition)
    return edition


@pytest.fixture
def takes(film_root, tmp_path):
    """Queue a picture's next render: the ground with the given boxes, under the caption in the
    captioned picture."""
    made = []

    def queue(captions: bool, *boxes):
        path = tmp_path / "takes" / f"{len(made)}.mp4"
        encode(path, *((CAPTION,) if captions else ()), *boxes)
        made.append(path)
        film_root.queue(Edition("zh").rendered(captions).file, path)

    return queue


def rendered(edition, takes, captioned=(), uncaptioned=()):
    """Render both pictures, each from its next take, and compare them; the comparison record."""
    takes(True, *captioned)
    takes(False, *uncaptioned)
    for captions in (True, False):
        picture_rendering.render_picture(edition, 60, captions=captions)
    try:
        equivalence.compare_pictures(edition)
    except PictureError:
        pass
    return repository.read(edition.caption_equivalence)


def outputs(film_root) -> list[str]:
    """The picture each render wrote, in order."""
    places = [Edition("zh").rendered(captions) for captions in (True, False)]
    named = {str(rendered.file): rendered.name for rendered in places}
    return [named[run["argv"][run["argv"].index("--output") + 1]] for run in film_root.runs()]


def held(edition) -> dict[str, str]:
    """The SHA-256 of both pictures and their receipts."""
    places = [edition.rendered(captions) for captions in (True, False)]
    return {path.name: repository.sha(path) for p in places for path in (p.file, p.receipt)}


def moving_bar(edge):
    """The boxes of both pictures with test_faults' moving bar, the captioned one drawing one sample
    of its trailing edge in grey `edge` at frame 70."""
    bar = [
        f"drawbox=x={10 + 2 * (n - 60)}:y=8:w=4:h=8:color=0xC8C8C8:t=fill:enable='eq(n,{n})'"
        for n in range(60, 81)
    ]
    sample = f"0x{edge:02X}{edge:02X}{edge:02X}"
    return [*bar, f"drawbox=x=30:y=10:w=1:h=1:color={sample}:t=fill:enable='eq(n,70)'"], bar


@pytest.mark.ffmpeg
def test_an_injected_fault_is_repaired_in_one_attempt_of_its_picture(pair, film_root, takes):
    assert rendered(pair, takes, uncaptioned=[FRAGMENT])["verdict"] == "refuse"
    faulty = pair.rendered(False)
    kept = {
        path.name: path.read_bytes()
        for path in (faulty.file, faulty.receipt, pair.caption_equivalence)
    }
    takes(False)
    passed = picture_repair.repair_pictures(pair, 2, 60)
    assert passed == repository.read(pair.caption_equivalence)
    assert passed["verdict"] == "pass"
    assert outputs(film_root) == ["captioned", "uncaptioned", "uncaptioned"]
    folder = repository.ROOT / REPAIRS / "1"
    assert sorted(path.name for path in folder.iterdir()) == sorted([*kept, "attempt.json"])
    for name, data in kept.items():
        assert (folder / name).read_bytes() == data
    attempt = repository.read(folder / "attempt.json")
    assert attempt["faults"] == {"uncaptioned": [FAULT]}
    assert attempt["kept"] == {
        f"{REPAIRS}/1/{name}": hashlib.sha256(data).hexdigest() for name, data in kept.items()
    }
    assert attempt["rendered"] == {"uncaptioned": repository.read(faulty.receipt)}
    assert (attempt["verdict"], attempt["findings"]) == ("pass", [])
    assert not (repository.ROOT / REPAIRS / "2").exists()


@pytest.mark.ffmpeg
def test_a_fault_that_remains_is_refused_after_the_last_attempt(pair, film_root, takes):
    rendered(pair, takes, uncaptioned=[FRAGMENT])
    takes(False, FRAGMENT)
    takes(False, FRAGMENT)
    with pytest.raises(PictureError) as refused:
        picture_repair.repair_pictures(pair, 2, 60)
    assert str(refused.value) == (
        f"The zh pictures still hold one-frame faults after 2 attempts, kept in {REPAIRS} as "
        "attempts 1, 2: encoded frame 77 at 1.283 s: the uncaptioned picture holds a one-frame "
        f"fault of 150 levels in box [40, 10, 44, 14] outside the caption band; render it again "
        f"with {RENDER} --uncaptioned"
    )
    assert outputs(film_root) == ["captioned", *["uncaptioned"] * 3]
    for number in (1, 2):
        attempt = repository.read(repository.ROOT / REPAIRS / f"{number}/attempt.json")
        assert (attempt["faults"], attempt["verdict"]) == ({"uncaptioned": [FAULT]}, "refuse")
    assert not (repository.ROOT / REPAIRS / "3").exists()


@pytest.mark.ffmpeg
@pytest.mark.parametrize(
    ("pictures", "reason"),
    [
        (
            moving_bar(50),
            "frame 70 differs by 150 levels in box [30, 10, 31, 11] and no one picture holds it; "
            f"render both pictures again with {RENDER} and with --uncaptioned",
        ),
        # A difference over frames 10 to 12, which no sampled frame sees.
        (
            ((), [square(40, 10, 170, "between(n,10,12)")]),
            "the pictures differ over frames 10-12 in box [40, 8, 48, 16]",
        ),
    ],
)
def test_a_difference_one_render_cannot_repair_is_refused_with_nothing_moved(
    pair, film_root, takes, pictures, reason
):
    assert rendered(pair, takes, *pictures)["verdict"] == "refuse"
    before = held(pair)
    with pytest.raises(PictureError) as refused:
        picture_repair.repair_pictures(pair, 2, 60)
    assert str(refused.value) == (
        f"The comparison record holds what rendering one picture again cannot repair: {reason}"
    )
    assert held(pair) == before
    assert outputs(film_root) == ["captioned", "uncaptioned"]
    assert not (repository.ROOT / REPAIRS).exists()


@pytest.mark.ffmpeg
def test_a_missing_or_stale_record_is_refused(pair, film_root, takes):
    takes(True)
    takes(False, FRAGMENT)
    for captions in (True, False):
        picture_rendering.render_picture(pair, 60, captions=captions)
    with pytest.raises(PictureError, match="^The zh pictures have no comparison record; run"):
        picture_repair.repair_pictures(pair, 2, 60)
    with pytest.raises(PictureError):
        equivalence.compare_pictures(pair)
    # A picture rendered again after the comparison is not the one its record binds.
    takes(False)
    picture_rendering.render_picture(pair, 60, captions=False)
    stale = "^The zh comparison record does not bind the current pictures; run compare-pictures$"
    with pytest.raises(PictureError, match=stale):
        picture_repair.repair_pictures(pair, 2, 60)
    pair.rendered(False).file.unlink()
    missing = "^The zh comparison record cannot be checked: missing build/artifacts/film/zh/"
    with pytest.raises(PictureError, match=missing):
        picture_repair.repair_pictures(pair, 2, 60)
    assert outputs(film_root) == ["captioned", "uncaptioned", "uncaptioned"]
    assert not (repository.ROOT / REPAIRS).exists()


@pytest.mark.ffmpeg
def test_a_passing_record_renders_nothing(pair, film_root, takes):
    record = rendered(pair, takes)
    assert record["verdict"] == "pass"
    assert picture_repair.repair_pictures(pair, 2, 60) == record
    assert outputs(film_root) == ["captioned", "uncaptioned"]
    assert not (repository.ROOT / REPAIRS).exists()


@pytest.mark.ffmpeg
def test_a_later_run_continues_the_attempt_numbers(pair, takes):
    rendered(pair, takes, uncaptioned=[FRAGMENT])
    takes(False, FRAGMENT)
    with pytest.raises(PictureError, match="after 1 attempt, kept in .* as attempt 1: "):
        picture_repair.repair_pictures(pair, 1, 60)
    first = repository.ROOT / REPAIRS / "1"
    kept = {path.name: repository.sha(path) for path in first.iterdir()}
    takes(False)
    picture_repair.repair_pictures(pair, 1, 60)
    assert {path.name: repository.sha(path) for path in first.iterdir()} == kept
    later = repository.read(repository.ROOT / REPAIRS / "2/attempt.json")
    assert (later["faults"], later["verdict"]) == ({"uncaptioned": [FAULT]}, "pass")


@pytest.mark.ffmpeg
@pytest.mark.parametrize("stale", ["gate", "template"])
def test_a_picture_whose_stage_or_check_is_not_current_is_refused_before_moving(
    pair, film_root, takes, stale
):
    rendered(pair, takes, uncaptioned=[FRAGMENT])
    before = held(pair)
    if stale == "gate":
        repository.write(
            pair.picture_gates, {**repository.read(pair.picture_gates), "verdict": "x"}
        )
        reason = "did not pass; run check-picture"
    else:
        template = repository.ROOT / picture_rendering.TEMPLATE
        template.write_text(template.read_text().replace("<title>", "<title>Changed "))
        reason = "template_sha256 differ"
    with pytest.raises(PictureError, match=reason):
        picture_repair.repair_pictures(pair, 2, 60)
    assert held(pair) == before
    assert outputs(film_root) == ["captioned", "uncaptioned"]
    assert not (repository.ROOT / REPAIRS).exists()


def refused(composition=0, sampled=(), unlisted=0, **every):
    """A refused comparison record: its composition instants that differ, the sampled frames that
    differ beyond the encoders' noise, listed and not, and its every-frame report, by default
    FAULT alone."""
    report = {"lasting": [], "lasting_runs": 0, "faults": [FAULT], "fault_frames": 1, **every}
    failing = [{"frame": frame, "largest_tile": 37.5, "psnr_db": 27.4} for frame in sampled]
    encoded = {"failing": failing, "failing_frames": len(failing) + unlisted, "every_frame": report}
    if composition:
        encoded = {"not_compared": "the compositions differ beyond their captions"}
    return {
        "composition": {"differing_instants": composition},
        "encoded": encoded,
        "verdict": "refuse",
    }


def test_a_record_s_faults_are_read_by_the_picture_that_holds_each():
    in_band = {**FAULT, "frame": 50, "picture": "captioned", "caption_band": True}
    residue = {**FAULT, "frame": 9, "peak": 93, "picture": None, "residue": True}
    found = faults.repairable(refused(faults=[in_band, FAULT, residue], fault_frames=2), "zh")
    assert found == {"captioned": [in_band], "uncaptioned": [FAULT]}
    assert faults.repairable({"verdict": "pass"}, "zh") == {}
    # A fault outside the caption band that lands on a sampled frame fails that frame too.
    assert faults.repairable(refused(sampled=[77]), "zh") == {"uncaptioned": [FAULT]}


# A sampled frame beyond the noise that no fault of one picture outside the caption band explains.
UNHELD = "differs beyond the encoders' noise without a one-frame fault of one picture there"


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (refused(composition=3), "the compositions differ beyond their captions at 3 instants"),
        (refused(sampled=[30]), f"sampled frame 30 {UNHELD}"),
        (
            refused(sampled=[77], unlisted=2),
            "2 more sampled frames differ beyond the encoders' noise",
        ),
        # A fault in the caption band, which the sampled measures leave out, or a residue does
        # not account for its sampled frame.
        (
            refused(sampled=[77], faults=[{**FAULT, "caption_band": True}]),
            f"sampled frame 77 {UNHELD}",
        ),
        (
            refused(
                sampled=[77], faults=[{**FAULT, "picture": None, "residue": True}], fault_frames=0
            ),
            f"sampled frame 77 {UNHELD}",
        ),
        (
            refused(lasting=[{"first": 10, "last": 12, "box": [0, 0, 8, 8]}], lasting_runs=2),
            "the pictures differ over frames 10-12 in box [0, 0, 8, 8]; 1 more runs of frames "
            "differ",
        ),
        (refused(fault_frames=3), "2 more one-frame differences are not listed with a picture"),
    ],
)
def test_a_record_of_anything_but_attributed_faults_is_refused(record, reason):
    with pytest.raises(PictureError) as refusal:
        faults.repairable(record, "zh")
    assert str(refusal.value) == (
        f"The comparison record holds what rendering one picture again cannot repair: {reason}"
    )


@pytest.mark.ffmpeg
@pytest.mark.parametrize(("pictures", "named"), [(((), [FRAGMENT]), True), (moving_bar(50), False)])
def test_a_refusal_names_the_repair_only_where_the_repair_can_answer_it(
    pair, takes, pictures, named
):
    rendered(pair, takes, *pictures)
    with pytest.raises(PictureError) as refusal:
        equivalence.compare_pictures(pair)
    assert str(refusal.value).endswith(NEXT) is named
    assert ("repair-pictures" in str(refusal.value)) is named


@pytest.mark.ffmpeg
def test_a_fault_on_a_sampled_frame_is_repaired_as_any_other(pair, film_root, takes):
    record = rendered(pair, takes, uncaptioned=[SAMPLED])
    # Frame 90 fails the sampled measures, and the scan of every frame names its picture.
    assert [row["frame"] for row in record["encoded"]["failing"]] == [90]
    held = record["encoded"]["every_frame"]["faults"]
    assert [(row["frame"], row["picture"]) for row in held] == [(90, "uncaptioned")]
    with pytest.raises(PictureError) as refusal:
        equivalence.compare_pictures(pair)
    assert str(refusal.value).endswith(NEXT)
    takes(False)
    assert picture_repair.repair_pictures(pair, 2, 60)["verdict"] == "pass"
    assert outputs(film_root) == ["captioned", "uncaptioned", "uncaptioned"]


@pytest.mark.ffmpeg
def test_one_attempt_renders_both_pictures_where_each_holds_a_fault(pair, film_root, takes):
    record = rendered(pair, takes, [FRAGMENT], [square(60, 20, 170, "eq(n,100)")])
    held = record["encoded"]["every_frame"]["faults"]
    assert [(row["frame"], row["picture"]) for row in held] == [
        (77, "captioned"),
        (100, "uncaptioned"),
    ]
    takes(True)
    takes(False)
    assert picture_repair.repair_pictures(pair, 2, 60)["verdict"] == "pass"
    assert outputs(film_root) == ["captioned", "uncaptioned", "captioned", "uncaptioned"]
    places = [pair.rendered(captions) for captions in (True, False)]
    kept = [path.name for p in places for path in (p.file, p.receipt)]
    folder = repository.ROOT / REPAIRS / "1"
    expected = [*kept, "caption-equivalence.json", "attempt.json"]
    assert sorted(path.name for path in folder.iterdir()) == sorted(expected)


@pytest.mark.ffmpeg
def test_a_render_that_fails_in_an_attempt_is_recorded_with_the_way_back(pair, film_root, takes):
    rendered(pair, takes, uncaptioned=[FRAGMENT])
    faulty = pair.rendered(False).file.read_bytes()
    film_root.renderer.write_text(f"#!{sys.executable}\nraise SystemExit(3)\n")
    with pytest.raises(PictureError) as refusal:
        picture_repair.repair_pictures(pair, 2, 60)
    folder = f"{REPAIRS}/1"
    assert str(refusal.value) == (
        f"Attempt 1 of the zh repair stopped, with the faulty pictures kept in {folder}: Native "
        f"picture render did not complete from the current stage; render again with {RENDER} "
        f"--uncaptioned, then run {COMPARE}"
    )
    attempt = repository.read(repository.ROOT / folder / "attempt.json")
    assert attempt["error"] == "Native picture render did not complete from the current stage"
    assert [(name, receipt["exit"]) for name, receipt in attempt["rendered"].items()] == [
        ("uncaptioned", 3)
    ]
    assert "verdict" not in attempt
    assert (repository.ROOT / folder / pair.rendered(False).file.name).read_bytes() == faulty
    assert not (repository.ROOT / REPAIRS / "2").exists()


@pytest.mark.ffmpeg
def test_a_later_comparison_that_one_render_cannot_repair_names_the_attempts(
    pair, film_root, takes
):
    rendered(pair, takes, uncaptioned=[FRAGMENT])
    takes(False, square(40, 10, 170, "between(n,10,12)"))
    with pytest.raises(PictureError) as refusal:
        picture_repair.repair_pictures(pair, 2, 60)
    assert str(refusal.value) == (
        "The comparison record holds what rendering one picture again cannot repair: the "
        "pictures differ over frames 10-12 in box [40, 8, 48, 16]; the repair stopped after 1 "
        f"attempt, kept in {REPAIRS} as attempt 1"
    )
    assert outputs(film_root) == ["captioned", "uncaptioned", "uncaptioned"]
    assert repository.read(repository.ROOT / REPAIRS / "1/attempt.json")["verdict"] == "refuse"


def test_attempt_folders_are_numbered_by_ascii_digits_only(pair):
    repairs = repository.ROOT / REPAIRS
    for name in ("2", "\u00b2", "\u0663", "notes"):
        (repairs / name).mkdir(parents=True)
    assert picture_repair.next_attempt(pair) == repairs / "3"


def test_a_repair_makes_at_least_one_attempt(pair):
    with pytest.raises(PictureError, match="^A repair makes at least one attempt, not 0$"):
        picture_repair.repair_pictures(pair, 0, 60)
