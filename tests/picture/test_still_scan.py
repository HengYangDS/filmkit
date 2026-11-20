"""Exercise the still-picture scan on small grey frames and a timeline, and the scan of an
edition's packaged film with the record its consumers require."""

import hashlib
import json
import subprocess
from importlib.metadata import version
from types import SimpleNamespace

import numpy as np
import pytest

import filmkit.durations as durations
import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository
from filmkit.picture.errors import PictureError
from filmkit.production import Edition

# What the scan and its requirement say of the film that stands still under four seconds of speech.
HELD = (
    "The zh film holds a still picture with 3.5 s of speech or more: 0.90-5.90 s with 4.00 s of "
    "speech; see build/evidence/editions/zh/film-stills.json"
)


def timeline(*spans):
    words = [{"text": f"w{k}", "start": a, "end": b} for k, (a, b) in enumerate(spans)]
    return {"segments": [{"id": "01", "words": words}]}


def frames(moving, still, *, toggle=0):
    """A bright square that moves for `moving` frames and then stands for `still` more."""
    out = []
    for k in range(moving + still):
        frame = np.full((still_scan.HEIGHT, still_scan.WIDTH), 15, dtype=np.uint8)
        x = 100 + 5 * min(k, moving - 1)
        frame[100:120, x : x + 20] = 200
        if toggle and k % 2:
            frame[60 : 60 + toggle, 60:61] = 200
        out.append(frame)
    return out


def decoding(monkeypatch, rate, read, decoded):
    """Stand in for the decode of a film at `rate` fps: `read()` gives the frames each phase
    reads, which one decode yields in the film's order, one of each distinct phase in turn.
    `decoded` lists the phases each decode was asked for."""

    def decode(_movie, phases=still_scan.PHASES[:1]):
        decoded.append(tuple(phases))
        distinct = len({phase % (rate // still_scan.FPS) for phase in phases})
        for frame in read():
            yield from [frame] * distinct

    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: rate)
    monkeypatch.setattr(still_scan, "decode", decode)


def test_a_still_run_carries_the_speech_inside_it():
    report = still_scan.scan(frames(10, 30), timeline((1.5, 2.5), (2.6, 3.5)))
    assert report["fine"]["runs"] == [{"start": 0.9, "end": 3.9, "speech": 1.9}]
    assert report["longest_fine_speech"] == 1.9


def test_a_change_of_a_few_pixels_leaves_the_picture_still():
    report = still_scan.scan(frames(10, 30, toggle=4), timeline((1.0, 3.8)))
    assert report["fine"]["runs"] == [{"start": 0.9, "end": 3.9, "speech": 2.8}]


def test_moving_marks_carry_no_still_run():
    report = still_scan.scan(frames(40, 0), timeline((0.5, 3.5)))
    assert report["fine"]["runs"] == []
    assert report["coarse"]["runs"] == []
    assert report["longest_fine_speech"] == 0


def test_the_coarse_measure_compares_frames_two_steps_apart():
    # A change of 30 pixels in every other frame is motion to the fine measure only.
    report = still_scan.scan(frames(10, 30, toggle=30), timeline((1.0, 3.8)))
    assert report["fine"]["runs"] == []
    assert report["coarse"]["runs"] == [{"start": 1.0, "end": 3.8, "speech": 2.8}]


def test_the_limit_fails_a_run_that_carries_too_much_speech():
    report = still_scan.scan(frames(10, 30), timeline((0.9, 3.9)))
    assert still_scan.over_limit(report, 3.0) == [{"start": 0.9, "end": 3.9, "speech": 3.0}]
    assert still_scan.over_limit(report, 3.5) == []


@pytest.mark.parametrize(
    ("spoken", "recorded", "held"),
    [(3.496, 3.49, False), (3.4999999, 3.5, True), (3.5, 3.5, True), (3.504, 3.5, True)],
)
def test_speech_is_recorded_cut_so_that_it_stands_at_the_limit_when_the_measured_does(
    spoken, recorded, held
):
    # Rounded, 3.496 s would be recorded as 3.5 and refused. A figure within a microsecond of the
    # limit is the limit: word times carry a float's noise.
    report = still_scan.scan(frames(10, 50), timeline((1.0, 1.0 + spoken)))
    assert report["fine"]["runs"] == [{"start": 0.9, "end": 5.9, "speech": recorded}]
    assert bool(still_scan.over_limit(report)) is held


def test_the_worse_of_two_sampling_phases_decides():
    # A run that one phase sees moving at its edge is still on the other, offset 0.05 s.
    early = still_scan.scan(frames(10, 30), timeline((0.9, 3.9)))
    late = still_scan.scan(frames(12, 28), timeline((0.9, 3.9)))
    both = still_scan.worst([late, early])
    assert both["longest_fine_speech"] == early["longest_fine_speech"] == 3.0
    assert both["fine"]["runs"] == early["fine"]["runs"]
    assert (both["phases"], both["phase_frames"]) == (2, [40, 40])


def test_one_decode_s_frames_are_dealt_to_their_phases_in_turn(monkeypatch):
    # The decode of a 60 fps film yields the frames of phase 0 and of phase 3 in turn. Here the
    # first phase sees a square that stops and the second one that keeps moving.
    still, moving = frames(10, 30), frames(40, 0)
    turns = [frame for pair in zip(still, moving, strict=True) for frame in pair]
    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: 60)
    monkeypatch.setattr(still_scan, "decode", lambda _movie, _phases: iter(turns))
    words = timeline((0.9, 3.9))
    first, second = still_scan.phase_reports("film.mp4", words)
    assert first == still_scan.scan(still, words)
    assert second == still_scan.scan(moving, words)
    assert (first["longest_fine_speech"], second["longest_fine_speech"]) == (3.0, 0)
    # A film at 30 fps holds no frame 0.05 s after a sample: both phases select the same
    # frames, the decode yields each once, and both read one report.
    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: 30)
    monkeypatch.setattr(still_scan, "decode", lambda _movie, _phases: iter(still))
    assert still_scan.phase_reports("film.mp4", words) == [first, first]


def test_a_scan_of_no_frames_is_refused():
    # A scan that read no frames has not judged the film, so it never passes it.
    with pytest.raises(still_scan.StillScanError, match="no frames"):
        still_scan.scan([], timeline((0.5, 1.0)))


@pytest.mark.ffmpeg
def test_a_film_that_cannot_be_read_is_refused(tmp_path):
    with pytest.raises(still_scan.StillScanError, match="no frames"):
        list(still_scan.decode(tmp_path / "absent.mp4"))


@pytest.mark.ffmpeg
@pytest.mark.parametrize("rate", [10, 60])
def test_each_phase_reads_ten_frames_a_second_at_any_frame_rate(tmp_path, rate):
    # A draft is rendered at 10 fps and a final film at 60 fps; both read 10 frames per second.
    movie = tmp_path / f"grey-{rate}.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=gray:size=480x270:rate={rate}:duration=2",
            "-pix_fmt",
            "yuv420p",
            str(movie),
        ],
        check=True,
    )
    assert len(list(still_scan.decode(movie, (0,)))) == 20
    assert len(list(still_scan.decode(movie, (1,)))) == 20
    # One decode keeps the frames of both phases, where the film holds a frame between them.
    assert len(list(still_scan.decode(movie, still_scan.PHASES))) == (40 if rate == 60 else 20)


@pytest.mark.ffmpeg
def test_one_decode_reports_each_phase_as_a_decode_of_its_own_does(tmp_path):
    # A white square on black that jumps at frames 122 and 242 of a 60 fps film of six seconds:
    # phase 3 samples frame 123 and sees each jump one sample before phase 0, which samples
    # frame 126, so the two phases report different runs. Each phase's report from the one
    # decode equals the report of that phase decoded alone.
    movie = tmp_path / "jumping.mp4"
    inputs = [
        option
        for source in ("color=black:size=480x270", "color=white:size=40x40")
        for option in ("-f", "lavfi", "-i", f"{source}:rate=60:duration=6")
    ]
    jump = "[0][1]overlay=x='100+60*gte(t\\,2.03)+60*gte(t\\,4.03)':y=120"
    command = ["ffmpeg", "-v", "error", *inputs, "-filter_complex", jump, "-pix_fmt", "yuv420p"]
    subprocess.run([*command, str(movie)], check=True)
    words = timeline((0.5, 5.5))
    together = still_scan.phase_reports(movie, words)
    apart = [still_scan.scan(still_scan.decode(movie, (phase,)), words) for phase in (0, 3)]
    assert together == apart
    assert [report["frames"] for report in together] == [60, 60]
    assert together[0]["fine"]["runs"] != together[1]["fine"]["runs"]


def test_the_scan_record_names_the_film_timeline_and_composition_it_judged(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    (tmp_path / "film.mp4").write_bytes(b"a rendered film")
    (tmp_path / "picture").mkdir()
    (tmp_path / "picture/film.js").write_text("scenes = {};\n")
    repository.write("timeline.json", timeline((1.0, 1.5)))
    decoded = []
    decoding(monkeypatch, 60, lambda: frames(40, 0), decoded)
    still_scan.main(["film.mp4", "timeline.json", "--out", "scan.json"])
    # A 60 fps film has frames between its samples: one decode reads both phases' frames.
    assert decoded == [(0, 3)]
    record = json.loads((tmp_path / "scan.json").read_text())
    assert record["movie"] == {
        "path": "film.mp4",
        "sha256": hashlib.sha256(b"a rendered film").hexdigest(),
    }
    assert record["timeline"]["path"] == "timeline.json"
    assert record["timeline"]["sha256"] == repository.sha(tmp_path / "timeline.json")
    assert record["composition"] == {
        "path": "picture/film.js",
        "sha256": repository.sha(tmp_path / "picture/film.js"),
    }
    # A record states the rules it was written under and the frames each phase read.
    assert (record["rules"], record["phase_frames"]) == (still_scan.rules(), [40, 40])
    assert record["rules"] == {
        "fps": 10,
        "size": [480, 270],
        "band": [30, 226],
        "phases": [0, 3],
        "decode": "scale=480:270:flags=area,format=gray",
        "fine": "at most 12 band pixels change by more than 24 levels in 0.1 s",
        "coarse": "under 0.05% of the band changes by more than 24 levels in 0.2 s",
        "coarse_share": 0.0005,
        "reported_speech_seconds": 1.0,
        "speech": "cut to whole hundredths of a second",
        "limit_seconds": 3.5,
    }


def test_an_edition_draft_is_scanned_against_its_timeline_into_its_record(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    (tmp_path / "draft.mp4").write_bytes(b"a draft")
    (tmp_path / "picture").mkdir()
    (tmp_path / "picture/film.js").write_text("scenes = {};\n")
    edition = Edition("en")
    repository.write(edition.timeline, {**timeline((1.0, 1.5)), "duration": 4})
    decoded = []
    decoding(monkeypatch, 10, lambda: frames(40, 0), decoded)
    still_scan.main(["draft.mp4", "--language", "en"])
    record = json.loads(edition.draft_stills.read_text())
    # A draft at the scan's own rate holds one frame for both phases, which the record still
    # names with the frames each read.
    assert (decoded, record["phases"], record["phase_frames"]) == ([(0, 3)], 2, [40, 40])
    assert record["timeline"] == {
        "path": "build/artifacts/film/en/timeline.json",
        "sha256": repository.sha(edition.timeline),
    }
    assert record["over_limit"] == []
    for wrong in (["draft.mp4", "--language", "en", "--out", "x.json"], ["draft.mp4"]):
        with pytest.raises(SystemExit):
            still_scan.main(wrong)


@pytest.fixture
def packaged(tmp_path, monkeypatch):
    """The Chinese edition's packaged 1080p captioned film below a test root, with its timeline
    of six seconds, four of them speech, and the composition. The film decodes to
    `shown["frames"]` in each phase, sixty that keep moving unless a test sets others, and
    `decoded` lists the phases of each decode."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = Edition("zh")
    film = edition.film("1080p-captioned")
    film.parent.mkdir(parents=True)
    film.write_bytes(b"a packaged film")
    (tmp_path / "picture").mkdir()
    (tmp_path / "picture/film.js").write_text("scenes = {};\n")
    repository.write(edition.timeline, {**timeline((1.0, 5.0)), "duration": 6})
    shown, decoded = {"frames": frames(60, 0)}, []
    decoding(monkeypatch, 60, lambda: shown["frames"], decoded)
    return SimpleNamespace(edition=edition, film=film, shown=shown, decoded=decoded)


def refusal(edition):
    """What the requirement says of the edition's film record."""
    with pytest.raises(PictureError) as refused:
        still_scan.require_film_scan(edition)
    return str(refused.value)


def rescanned(packaged):
    """Whether `scan-film` decodes the film again, after which the requirement passes."""
    before = len(packaged.decoded)
    still_scan.scan_film(packaged.edition)
    still_scan.require_film_scan(packaged.edition)
    return packaged.decoded[before:] == [(0, 3)]


def test_a_film_that_keeps_moving_writes_its_record_and_meets_the_requirement(packaged, capsys):
    edition = packaged.edition
    record = still_scan.scan_film(edition)
    assert json.loads(capsys.readouterr().out) == {
        "longest_fine_speech": 0,
        "over_limit": 0,
        "scanned": True,
    }
    # The final film runs at 60 fps: one decode reads both phases.
    assert packaged.decoded == [(0, 3)]
    assert record == repository.read("build/evidence/editions/zh/film-stills.json")
    assert record["movie"] == {
        "path": f"build/artifacts/film/zh/{packaged.film.name}",
        "sha256": hashlib.sha256(b"a packaged film").hexdigest(),
    }
    assert record["timeline"]["sha256"] == repository.sha(edition.timeline)
    assert record["composition"]["sha256"] == repository.sha("picture/film.js")
    assert (record["engine_version"], record["limit_seconds"]) == (version("filmkit"), 3.5)
    assert (record["rules"], record["phase_frames"]) == (still_scan.rules(), [60, 60])
    assert record["over_limit"] == []
    assert still_scan.require_film_scan(edition) == {
        "film": packaged.film.name,
        "longest_fine_speech": 0,
        "limit_seconds": 3.5,
    }


def test_a_film_that_stands_still_is_refused_at_its_scan_and_by_the_requirement(packaged):
    packaged.shown["frames"] = frames(10, 50)
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert str(refused.value) == HELD
    # The record is written before the refusal, and the requirement reads the same run from it.
    held = [{"start": 0.9, "end": 5.9, "speech": 4.0}]
    assert repository.read(packaged.edition.film_stills)["over_limit"] == held
    assert refusal(packaged.edition) == HELD


def test_a_second_scan_of_an_unchanged_film_decodes_nothing(packaged, capsys):
    still_scan.scan_film(packaged.edition)
    still_scan.scan_film(packaged.edition)
    assert packaged.decoded == [(0, 3)]
    first, second = map(json.loads, capsys.readouterr().out.splitlines())
    assert (first["scanned"], second["scanned"]) == (True, False)
    assert {**second, "scanned": True} == first


def test_the_duration_record_says_whether_the_film_was_decoded(packaged):
    path = "build/evidence/editions/zh/durations/scan-film.json"
    with durations.run("zh", "scan-film"):
        still_scan.scan_film(packaged.edition)
    first = repository.read(path)
    assert ([*first["phases"]], first["settings"]) == (["scan"], {"scanned": True})
    with durations.run("zh", "scan-film"):
        still_scan.scan_film(packaged.edition)
    second = repository.read(path)
    assert (second["phases"], second["settings"]) == ({}, {"scanned": False})


def test_a_second_scan_of_a_refused_film_refuses_again_from_its_record(packaged):
    packaged.shown["frames"] = frames(10, 50)
    for _ in range(2):
        with pytest.raises(PictureError) as refused:
            still_scan.scan_film(packaged.edition)
        assert str(refused.value) == HELD
    assert packaged.decoded == [(0, 3)]


def change_film(packaged):
    packaged.film.write_bytes(b"another packaged film")


def change_timeline(packaged):
    repository.write(packaged.edition.timeline, {**timeline((1.0, 5.2)), "duration": 6})


def change_composition(packaged):
    (repository.ROOT / "picture/film.js").write_text("scenes = {changed: 1};\n")


def change_engine(packaged):
    rewrite(packaged, engine_version="0.0.1")


def rewrite(packaged, **fields):
    """Set fields of the edition's film record, as a hand does."""
    path = packaged.edition.film_stills
    repository.write(path, {**repository.read(path), **fields})


@pytest.mark.parametrize(
    ("change", "named"),
    [
        (change_film, "movie"),
        (change_timeline, "timeline"),
        (change_composition, "composition"),
        (change_engine, "engine"),
    ],
)
def test_a_record_of_another_film_timeline_composition_or_engine_is_refused(
    packaged, change, named
):
    still_scan.scan_film(packaged.edition)
    change(packaged)
    assert refusal(packaged.edition) == (
        f"The zh film's still scan record binds another {named}; run scan-film"
    )
    # The scan does not answer from such a record: it decodes the film again and rebinds it.
    assert rescanned(packaged)


def test_an_edition_without_a_record_is_refused_with_the_action_that_writes_it(packaged):
    assert refusal(packaged.edition) == "The zh film has no still scan record; run scan-film"


def cut_to(share):
    def cut(packaged):
        path = packaged.edition.film_stills
        text = path.read_text()
        path.write_text(text[: int(len(text) * share)])

    return cut


def body(text):
    return lambda packaged: packaged.edition.film_stills.write_text(text)


def without(key):
    def drop(packaged):
        path = packaged.edition.film_stills
        record = repository.read(path)
        del record[key]
        repository.write(path, record)

    return drop


@pytest.mark.parametrize(
    "damage",
    [
        cut_to(0.5),
        cut_to(0),
        body("[]"),
        body('"a record"'),
        body("null"),
        body("{}"),
        lambda packaged: rewrite(packaged, movie=None),
        lambda packaged: rewrite(packaged, fine={"runs": [{"start": 1, "end": 5, "speech": "4"}]}),
        lambda packaged: rewrite(packaged, rules="the engine's"),
        lambda packaged: rewrite(packaged, longest_fine_speech=True),
        without("fine"),
        without("longest_fine_speech"),
        without("over_limit"),
        without("phase_frames"),
        without("rules"),
        without("engine_version"),
    ],
)
def test_a_record_that_cannot_be_read_is_refused_and_repaired_by_the_action_it_names(
    packaged, damage
):
    # A record cut short, of another type or without a field of the scan's ends no reader with
    # an error of its own, and the command the refusal names writes a whole record again.
    still_scan.scan_film(packaged.edition)
    damage(packaged)
    assert refusal(packaged.edition) == (
        "The zh film's still scan record cannot be read; run scan-film"
    )
    assert rescanned(packaged)


@pytest.mark.parametrize(
    ("edit", "named"),
    [
        (
            {"fine": {"rule": still_scan.FINE_RULE, "runs": []}},
            "its runs at the limit and its longest speech",
        ),
        ({"over_limit": []}, "its runs at the limit"),
        ({"longest_fine_speech": 0}, "its longest speech"),
        ({"limit_seconds": 99}, "its limit"),
        ({"phase_frames": [1, 60]}, "the frames it read"),
    ],
)
def test_a_record_that_contradicts_itself_is_not_trusted_and_the_film_is_scanned_again(
    packaged, edit, named
):
    # A film that stands still, and a record of it in which a hand emptied one statement of the
    # verdict: the others still state it, so no reader takes the record's word.
    packaged.shown["frames"] = frames(10, 50)
    with pytest.raises(PictureError):
        still_scan.scan_film(packaged.edition)
    rewrite(packaged, **edit)
    assert refusal(packaged.edition) == (
        f"The zh film's still scan record cannot be trusted, as it contradicts itself in {named}; "
        "run scan-film"
    )
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert (str(refused.value), packaged.decoded) == (HELD, [(0, 3), (0, 3)])


def test_a_record_written_under_another_limit_is_refused_with_both_limits(packaged):
    # The general form scans any film with any limit; at the film record's place such a record,
    # the engine's version added, states rules that are not the engine's.
    packaged.shown["frames"] = frames(10, 50)
    edition = packaged.edition
    record = still_scan.record_scan(packaged.film, edition.timeline, edition.film_stills, 99)
    assert (record["over_limit"], record["limit_seconds"]) == ([], 99)
    assert refusal(edition) == "The zh film's still scan record cannot be read; run scan-film"
    rewrite(packaged, engine_version=version("filmkit"))
    assert refusal(edition) == (
        "The zh film's still scan record states other rules than the engine's: a limit of 99 s "
        "where the engine's is 3.5 s; run scan-film"
    )
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(edition)
    assert (str(refused.value), packaged.decoded) == (HELD, [(0, 3), (0, 3)])


def test_a_record_of_earlier_rules_is_refused_though_the_engine_s_version_stands(
    packaged, monkeypatch
):
    # Between two releases the scan's rules can change under one version: the record states the
    # rules it was written under, and the reader compares them with the engine's own.
    still_scan.scan_film(packaged.edition)
    monkeypatch.setattr(still_scan, "FINE_RULE", "at most 8 band pixels change")
    assert refusal(packaged.edition) == (
        "The zh film's still scan record states other rules than the engine's; run scan-film"
    )
    assert rescanned(packaged)


def test_a_film_replaced_while_it_is_scanned_is_refused_and_leaves_no_record(packaged, monkeypatch):
    def replaced(_movie, _phases):
        for k, frame in enumerate(frames(60, 0)):
            if k == 30:
                packaged.film.write_bytes(b"a film packaged meanwhile")
            yield from (frame, frame)

    # The record would bind bytes that no scan read. An earlier record of the film as it stood
    # does not outlive the scan either.
    still_scan.scan_film(packaged.edition)
    change_film(packaged)
    monkeypatch.setattr(still_scan, "decode", replaced)
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert str(refused.value) == (
        f"build/artifacts/film/zh/{packaged.film.name} or build/artifacts/film/zh/timeline.json "
        "changed while the film was scanned"
    )
    assert not packaged.edition.film_stills.exists()


def test_a_film_that_does_not_decode_to_its_timeline_s_seconds_is_refused(packaged):
    # A film that decodes short was not read whole, so a scan of it settles nothing.
    packaged.shown["frames"] = frames(59, 0)
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert str(refused.value) == (
        f"build/artifacts/film/zh/{packaged.film.name} decodes to 59 and 59 frames at 10 fps in "
        "its phases, not the 60 of its timeline's seconds"
    )
    assert not packaged.edition.film_stills.exists()


def test_a_timeline_that_states_no_duration_is_named(packaged):
    repository.write(packaged.edition.timeline, timeline((1.0, 5.0)))
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert str(refused.value) == (
        "build/artifacts/film/zh/timeline.json states no duration for the film's scan"
    )


def test_a_missing_film_is_named_by_the_scan_and_by_the_requirement(packaged):
    still_scan.scan_film(packaged.edition)
    packaged.film.unlink()
    needs = f"The zh film's still scan needs build/artifacts/film/zh/{packaged.film.name}"
    for ask in (still_scan.scan_film, still_scan.require_film_scan):
        with pytest.raises(PictureError) as refused:
            ask(packaged.edition)
        assert str(refused.value) == needs


def test_a_film_that_cannot_be_read_is_the_action_s_refusal_and_leaves_no_record(
    packaged, monkeypatch
):
    def unreadable(_movie, _phases):
        msg = "FFmpeg read no frames from the film (exit 1)"
        raise still_scan.StillScanError(msg)

    # An earlier record, here of the film before it was packaged again, does not outlive a scan
    # that could not read the film.
    still_scan.scan_film(packaged.edition)
    change_film(packaged)
    monkeypatch.setattr(still_scan, "decode", unreadable)
    with pytest.raises(PictureError, match="FFmpeg read no frames from the film"):
        still_scan.scan_film(packaged.edition)
    assert not packaged.edition.film_stills.exists()
