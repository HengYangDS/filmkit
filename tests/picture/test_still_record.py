"""The reader of a still scan's record, for a film and for a draft, and what the scan refuses of
inputs it cannot read: no body of a record and no answer of a tool ends a reader with an error
of its own."""

import json
import subprocess
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import filmkit.picture.renderer as renderer
import filmkit.picture.still_scan as still_scan
import filmkit.preflight as preflight
import filmkit.repository as repository
from filmkit.picture.errors import PictureError
from filmkit.production import Edition

UNREADABLE = "The zh film's still scan record cannot be read; run filmkit build scan-film:zh"
DRAFT = "build/evidence/editions/zh/draft-stills.json"


def timeline(*spans, **stated):
    words = [{"text": f"w{k}", "start": a, "end": b} for k, (a, b) in enumerate(spans)]
    return {"segments": [{"id": "01", "words": words}], **stated}


def frames(moving, still):
    """A bright square that moves for `moving` frames and then stands for `still` more."""
    out = []
    for k in range(moving + still):
        frame = np.full((still_scan.HEIGHT, still_scan.WIDTH), 15, dtype=np.uint8)
        x = 100 + 5 * min(k, moving - 1)
        frame[100:120, x : x + 20] = 200
        out.append(frame)
    return out


@pytest.fixture
def packaged(tmp_path, monkeypatch):
    """The Chinese edition's packaged film, its draft's receipt, its timeline of six seconds,
    four of them speech, and the composition, below a test root. Each phase of a scan reads
    `frames`, sixty that keep moving unless a test sets others; `scans` counts the decodes and
    `meanwhile` runs during each."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = Edition("zh")
    film = edition.film("1080p-captioned")
    film.parent.mkdir(parents=True)
    film.write_bytes(b"a packaged film")
    (tmp_path / "draft.mp4").write_bytes(b"a draft")
    (tmp_path / "picture").mkdir()
    (tmp_path / "picture/film.js").write_text("scenes = {};\n")
    repository.write(edition.timeline, timeline((1.0, 5.0), duration=6))
    drew = {
        "package": renderer.RENDERER_NAME,
        "version": renderer.RENDERER_VERSION,
        "text_renderer": renderer.TEXT_RENDERER,
    }
    repository.write(edition.draft_receipt, {"renderer": drew})
    state = SimpleNamespace(edition=edition, film=film, frames=frames(60, 0), scans=0)
    state.meanwhile = lambda: None

    def phase_reports(_film, words):
        state.scans += 1
        state.meanwhile()
        return [still_scan.scan(iter(state.frames), words) for _ in still_scan.PHASES]

    monkeypatch.setattr(still_scan, "phase_reports", phase_reports)
    return state


def refusal(edition):
    with pytest.raises(PictureError) as refused:
        still_scan.require_film_scan(edition)
    return str(refused.value)


def rescanned(packaged):
    """Whether `scan-film` decodes the film again, after which the requirement passes."""
    before = packaged.scans
    still_scan.scan_film(packaged.edition)
    still_scan.require_film_scan(packaged.edition)
    return packaged.scans == before + 1


def rewrite(path, **fields):
    repository.write(path, {**repository.read(path), **fields})


def held(packaged):
    """Scan a film that stands still under four seconds of speech: its record lists the run."""
    packaged.frames = frames(10, 50)
    with pytest.raises(PictureError):
        still_scan.scan_film(packaged.edition)
    return repository.read(packaged.edition.film_stills)


@pytest.mark.parametrize(
    "body",
    [
        "[" * 100_000 + "]" * 100_000,
        '{"a": ' * 100_000 + "1" + "}" * 100_000,
    ],
)
def test_a_body_nested_deeper_than_the_reader_follows_cannot_be_read(packaged, body):
    still_scan.scan_film(packaged.edition)
    packaged.edition.film_stills.write_text(body)
    assert repository.read_entry(packaged.edition.film_stills, ("movie",)) is None
    assert refusal(packaged.edition) == UNREADABLE
    assert rescanned(packaged)


@pytest.mark.parametrize(
    "run",
    [
        {"start": 0.9, "end": 5.9, "speech": 10**400},
        {"start": 10**400, "end": 10**400, "speech": 4.0},
        {"start": 0.9, "end": 5.9, "speech": float("nan")},
        {"start": 0.9, "end": 5.9, "speech": -1},
        {"start": 0.9, "end": 5.9, "speech": 5.5},
        {"start": 5.0, "end": 4.0, "speech": 0.0},
        {"start": 0.9, "end": 6.5, "speech": 4.0},
        {"start": -0.1, "end": 5.9, "speech": 4.0},
    ],
)
def test_a_run_that_no_scan_of_this_film_could_list_makes_the_record_unreadable(packaged, run):
    # A number past a float's range, no number, a negative speech, more speech than the run is
    # long, a run that ends before it starts or after the film: the record is rewritten to agree
    # with itself in every other statement, and still answers for nothing.
    record = held(packaged)
    path = packaged.edition.film_stills
    fine = {**record["fine"], "runs": [run]}
    text = json.dumps({**record, "fine": fine, "over_limit": [run], "longest_fine_speech": 4.0})
    path.write_text(text)
    assert refusal(packaged.edition) == UNREADABLE
    with pytest.raises(PictureError, match="holds a still picture with 3.5 s of speech or more"):
        still_scan.scan_film(packaged.edition)
    assert packaged.scans == 2


@pytest.mark.parametrize(
    "damage",
    [
        {"fps": "10"},
        {"fps": True},
        {"frames": 60.5},
        {"phases": None},
        {"coarse": None},
        {"coarse": {"rule": "a rule"}},
        {"coarse": {"rule": 3, "runs": []}},
        {"fine": {"runs": []}},
        {"phase_frames": [60, "60"]},
        {"limit_seconds": "3.5"},
        {"over_limit": [{"start": 1}]},
        {"movie": {"sha256": 7, "path": "film.mp4"}},
        {"timeline": {"sha256": "x"}},
    ],
)
def test_a_record_that_lacks_the_scan_s_shape_cannot_be_read(packaged, damage):
    # Every field the scan writes, of the scan's type: a reader takes no record on less.
    still_scan.scan_film(packaged.edition)
    rewrite(packaged.edition.film_stills, **damage)
    assert refusal(packaged.edition) == UNREADABLE
    assert rescanned(packaged)


@pytest.mark.parametrize(
    ("edit", "named"),
    [
        ({"fps": 20}, "its rate"),
        ({"phases": 3}, "its phases"),
        ({"frames": 59}, "the frames it read"),
        ({"fine": {"rule": "at most 8 band pixels change", "runs": []}}, "its rules' wording"),
        ({"limit_seconds": 2.5, "fps": 30}, "its limit and its rate"),
    ],
)
def test_a_record_that_states_a_rule_twice_must_agree_with_itself(packaged, edit, named):
    # A record states its rate, its limit, both rules' wording and its phases beside its
    # `rules`, for the readers that take one field: the two statements are one fact.
    still_scan.scan_film(packaged.edition)
    rewrite(packaged.edition.film_stills, **edit)
    assert refusal(packaged.edition) == (
        f"The zh film's still scan record cannot be trusted, as it contradicts itself in {named}; "
        "run filmkit build scan-film:zh"
    )
    assert rescanned(packaged)


def test_the_rules_state_the_decode_and_the_cut_of_speech(packaged, monkeypatch):
    # A reading depends on the scaler and the grey conversion of the decode and on how speech is
    # recorded: a record written under others answers for nothing, under one engine version.
    assert still_scan.rules()["decode"] == "scale=480:270:flags=area,format=gray"
    assert still_scan.rules()["speech"] == "cut to whole hundredths of a second"
    assert still_scan.rules()["coarse_share"] == 0.0005
    for name, other in (("DECODE", "scale=480:270:flags=bilinear,format=gray"), ("SPEECH", "x")):
        still_scan.scan_film(packaged.edition)
        with monkeypatch.context() as patch:
            patch.setattr(still_scan, name, other)
            assert refusal(packaged.edition) == (
                "The zh film's still scan record states other rules than the engine's; "
                "run filmkit build scan-film:zh"
            )


def test_words_that_overlap_give_a_run_no_more_speech_than_it_lasts(packaged):
    # The reader refuses a run that carries more speech than its length; the scan writes none,
    # or the command a refusal names could not repair its own record.
    edition = packaged.edition
    repository.write(edition.timeline, timeline((1.0, 5.0), (1.5, 5.5), (2.0, 5.8), duration=6))
    packaged.frames = frames(10, 50)
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(edition)
    assert "0.90-5.90 s with 5.00 s of speech" in str(refused.value)
    assert "0.90-5.90 s with 5.00 s of speech" in refusal(edition)


@pytest.mark.parametrize("limit", [None, "3.5", True])
def test_a_refusal_names_a_record_s_limit_only_where_it_is_another_number(packaged, limit):
    still_scan.scan_film(packaged.edition)
    stated = {**still_scan.rules(), "limit_seconds": limit}
    if limit is None:
        del stated["limit_seconds"]
    rewrite(packaged.edition.film_stills, rules=stated)
    assert refusal(packaged.edition) == (
        "The zh film's still scan record states other rules than the engine's; run filmkit "
        "build scan-film:zh"
    )


def test_a_timeline_replaced_while_the_film_is_scanned_is_refused_and_leaves_no_record(packaged):
    still_scan.scan_film(packaged.edition)
    packaged.film.write_bytes(b"the film packaged again")
    edition = packaged.edition
    packaged.meanwhile = lambda: repository.write(
        edition.timeline, timeline((1.0, 4.0), duration=6)
    )
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(edition)
    assert str(refused.value) == (
        f"build/artifacts/film/zh/{packaged.film.name} or build/artifacts/film/zh/timeline.json "
        "changed while the film was scanned"
    )
    assert not edition.film_stills.exists()


@pytest.mark.parametrize(
    ("stated", "said"),
    [
        ("[]", "states no runtime in whole seconds"),
        ('{"segments": [], "duration": NaN}', "states no runtime in whole seconds"),
        ('{"segments": [], "duration": Infinity}', "states no runtime in whole seconds"),
        ('{"segments": [], "duration": 0}', "states no runtime in whole seconds"),
        ('{"segments": [], "duration": "6"}', "states no runtime in whole seconds"),
        ('{"duration": 6}', "The timeline's aligned words stand in no form the scan reads"),
        (
            '{"duration": 6, "segments": [{"words": [{"start": 1}]}]}',
            "The timeline's aligned words stand in no form the scan reads",
        ),
        (
            '{"duration": 6, "segments": [{"words": [{"start": 1, "end": "2"}]}]}',
            "The timeline states a word whose start or end is no time",
        ),
        ('{"duration": 6, "segments": 3', "states no runtime in whole seconds"),
    ],
)
def test_a_timeline_the_scan_cannot_read_is_refused_by_its_name(packaged, stated, said):
    packaged.edition.timeline.write_text(stated)
    with pytest.raises(PictureError) as refused:
        still_scan.scan_film(packaged.edition)
    assert said in str(refused.value)
    assert "build/artifacts/film/zh/timeline.json" in str(refused.value)
    assert (packaged.scans, packaged.edition.film_stills.exists()) == (0, False)


@pytest.mark.parametrize(
    ("answer", "said"),
    [
        ("0/0\n", "film.mp4 runs at 0 fps, not a whole multiple of 10 above none"),
        ("0/1\n", "film.mp4 runs at 0 fps, not a whole multiple of 10 above none"),
        ("25/1\n", "film.mp4 runs at 25 fps, not a whole multiple of 10 above none"),
        ("60/1\n60/1\n", "FFmpeg read no frames from film.mp4 (ffprobe exit 0)"),
        ("N/A\n", "FFmpeg read no frames from film.mp4 (ffprobe exit 0)"),
        ("60/x\n", "FFmpeg read no frames from film.mp4 (ffprobe exit 0)"),
        ("", "FFmpeg read no frames from film.mp4 (ffprobe exit 0)"),
    ],
)
def test_an_answer_of_ffprobe_that_is_no_frame_rate_is_refused_by_the_film_s_name(
    tmp_path, monkeypatch, answer, said
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    probe = subprocess.CompletedProcess([], 0, stdout=answer, stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *_, **__: probe)
    with pytest.raises(still_scan.StillScanError) as refused:
        still_scan.frame_rate(Path("film.mp4"))
    assert str(refused.value) == said


class Decoder:
    """Stand in for the FFmpeg process of a decode: it gives `frames` frames and ends with
    `status`, and keeps the command it was started with."""

    started: list[list[str]] = []

    def __init__(self, frames, status):
        self.left, self.status, self.returncode, self.stdout = frames, status, None, self

    def __call__(self, command, **_):
        Decoder.started.append(command)
        return self

    def read(self, size):
        self.left -= 1
        return bytes(size) if self.left >= 0 else b""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.returncode = self.status


@pytest.mark.parametrize(
    ("given", "status", "said"),
    [
        (60, 1, "FFmpeg ended with exit 1 after 60 frames of film.mp4"),
        (0, 1, "FFmpeg read no frames from film.mp4"),
        (0, 0, "FFmpeg read no frames from film.mp4"),
    ],
)
def test_a_decode_that_fails_says_how_far_it_read_and_names_the_film(
    tmp_path, monkeypatch, given, status, said
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: 60)
    monkeypatch.setattr(subprocess, "Popen", Decoder(given, status))
    with pytest.raises(still_scan.StillScanError) as refused:
        list(still_scan.decode(tmp_path / "film.mp4"))
    assert str(refused.value) == said
    chain = Decoder.started[-1][Decoder.started[-1].index("-vf") + 1]
    assert chain == f"select='eq(mod(n\\,6)\\,0)',{still_scan.rules()['decode']}"


@pytest.mark.parametrize("limit", ["3.456", "3.5001", "0.001"])
def test_a_limit_finer_than_hundredths_is_refused(packaged, limit, capsys):
    # A run's speech is recorded cut to hundredths, so a finer limit would be judged wrongly.
    with pytest.raises(SystemExit) as refused:
        still_scan.main(["draft.mp4", "--language", "zh", "--limit", limit])
    assert refused.value.code == 2
    assert "--limit is stated in whole hundredths of a second" in capsys.readouterr().err
    assert (packaged.scans, packaged.edition.draft_stills.exists()) == (0, False)
    still_scan.main(["draft.mp4", "--language", "zh", "--limit", "3.45"])
    assert repository.read(packaged.edition.draft_stills)["limit_seconds"] == 3.45


def drafted(packaged):
    """Scan the edition's draft into its record, which then admits a render."""
    still_scan.main(["draft.mp4", "--language", "zh"])
    assert preflight.draft(packaged.edition) is None
    return packaged.edition.draft_stills


@pytest.mark.parametrize(
    ("damage", "said"),
    [
        (lambda path: path.write_text(path.read_text()[:200]), "cannot be read"),
        (lambda path: path.write_text(""), "cannot be read"),
        (lambda path: path.write_text("[]"), "cannot be read"),
        (lambda path: path.write_text("null"), "cannot be read"),
        (lambda path: rewrite(path, timeline=None), "cannot be read"),
        (lambda path: rewrite(path, coarse=None), "cannot be read"),
        (
            lambda path: rewrite(path, over_limit=[{"start": 0.9, "end": 5.9, "speech": 3.9}]),
            "cannot be trusted, as it contradicts itself in its runs at the limit",
        ),
        (
            lambda path: rewrite(path, limit_seconds=99),
            "cannot be trusted, as it contradicts itself in its limit",
        ),
        (
            lambda path: rewrite(path, rules={**still_scan.rules(), "limit_seconds": 99}),
            "states other rules than the engine's: a limit of 99 s where the engine's is 3.5 s",
        ),
        (
            lambda path: rewrite(path, phase_frames=[35, 35], frames=35),
            "cannot be trusted, as it contradicts itself in the frames it read",
        ),
    ],
)
def test_a_draft_record_is_read_as_a_film_s_is(packaged, damage, said):
    # The draft's record goes through the reader of the film's: no body of it ends the
    # pre-render check with an error, and one statement of its verdict is not taken alone.
    path = drafted(packaged)
    damage(path)
    assert preflight.draft(packaged.edition) == f"{DRAFT} {said}; scan a new draft"


def test_a_draft_scanned_under_another_limit_or_by_another_engine_s_rules_admits_no_render(
    packaged, monkeypatch
):
    still_scan.main(["draft.mp4", "--language", "zh", "--limit", "9.5"])
    assert preflight.draft(packaged.edition) == (
        f"{DRAFT} states other rules than the engine's: a limit of 9.5 s where the engine's is "
        "3.5 s; scan a new draft"
    )
    drafted(packaged)
    monkeypatch.setattr(still_scan, "FINE_RULE", "at most 8 band pixels change")
    assert preflight.draft(packaged.edition) == (
        f"{DRAFT} states other rules than the engine's; scan a new draft"
    )


def test_a_draft_binds_no_engine_and_another_composition_is_named(packaged):
    path = drafted(packaged)
    assert "engine_version" not in repository.read(path)
    (repository.ROOT / "picture/film.js").write_text("scenes = {1: 2};\n")
    assert preflight.draft(packaged.edition) == (
        f"{DRAFT} binds another composition; scan a new draft"
    )


def test_a_draft_whose_decode_ends_early_is_refused_and_leaves_no_record(packaged):
    # A decode that ends with exit 0 after part of the draft would be reported as a shorter
    # film: the draft's timeline is the edition's, so its frames are known.
    path = drafted(packaged)
    packaged.frames = frames(35, 0)
    with pytest.raises(SystemExit) as refused:
        still_scan.main(["draft.mp4", "--language", "zh"])
    # The scan's own command refuses in one line, as `scan-film` does, with no error of its own.
    assert str(refused.value) == (
        "still_scan: draft.mp4 decodes to 35 and 35 frames at 10 fps in its phases, not the 60 of "
        "its timeline's seconds"
    )
    assert not path.exists()
    packaged.edition.timeline.write_text('{"duration": 6}')
    for arguments in (
        ["--language", "zh"],
        ["build/artifacts/film/zh/timeline.json", "--out", "x"],
    ):
        with pytest.raises(SystemExit) as refused:
            still_scan.main(["draft.mp4", *arguments])
        assert str(refused.value) == (
            "still_scan: The timeline's aligned words stand in no form the scan reads "
            "(build/artifacts/film/zh/timeline.json)"
        )


def test_the_film_s_record_names_the_engine_and_the_reader_asks_it(packaged):
    still_scan.scan_film(packaged.edition)
    rewrite(packaged.edition.film_stills, engine_version="0.0.1")
    assert version("filmkit") != "0.0.1"
    assert refusal(packaged.edition) == (
        "The zh film's still scan record binds another engine; run filmkit build scan-film:zh"
    )
