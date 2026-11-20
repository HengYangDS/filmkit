"""The verifier's and the reproduction's runs are recorded unless they are asked to be read-only."""

import pytest

import filmkit.delivery.reproduction as reproduction
import filmkit.delivery.verification as delivery_verification
import filmkit.picture.still_scan as picture_still_scan
import filmkit.production as production
import filmkit.repository as repository


@pytest.fixture
def verifying(tmp_path, monkeypatch):
    """Every check of an edition replaced by a marker, below a root of its own."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    for name in ("sources", "narration", "picture", "package", "spotlight", "review"):
        monkeypatch.setattr(delivery_verification, f"verify_{name}", lambda *_, n=name: n)
    monkeypatch.setattr(picture_still_scan, "require_film_scan", lambda _edition: "still_scan")
    monkeypatch.setattr(
        delivery_verification, "verify_media", lambda _edition, path, _rendition: path.name
    )
    return tmp_path.resolve()


def films(code="all") -> list[str]:
    codes = production.CODES if code == "all" else (code,)
    return [str(film) for c in codes for film in production.Edition(c).films]


def test_a_verification_writes_each_editions_duration_record_and_nothing_else(verifying, capsys):
    delivery_verification.main(["--technical-only", "--language", "all", *films()])
    capsys.readouterr()
    written = sorted(str(path.relative_to(verifying)) for path in verifying.rglob("*.json"))
    assert written == [
        "build/evidence/editions/en/durations/verify.json",
        "build/evidence/editions/zh/durations/verify.json",
    ]
    record = repository.read(written[1])
    assert (record["command"], record["edition"], record["completed"]) == ("verify", "zh", True)
    assert [*record["phases"]] == ["bindings", "media", "spotlight"]


def test_a_read_only_verification_writes_nothing(verifying, capsys):
    arguments = ["--read-only", "--technical-only", "--language", "zh", *films("zh")]
    delivery_verification.main(arguments)
    assert list(verifying.rglob("*")) == []


def test_a_refused_verification_is_recorded_as_not_completed(verifying, monkeypatch, capsys):
    def refuse(*arguments):
        message = "Film package differs from its current inputs"
        raise delivery_verification.VerificationError(message)

    monkeypatch.setattr(delivery_verification, "verify_package", refuse)
    with pytest.raises(SystemExit, match="zh: Film package differs"):
        delivery_verification.main(["--technical-only", "--language", "zh", *films("zh")])
    record = repository.read("build/evidence/editions/zh/durations/verify.json")
    assert record["completed"] is False


def test_a_reproduction_records_each_editions_comparison_unless_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    compared = []

    def compare_edition(edition, record, assets, listed):
        compared.append(edition.code)
        return {"films": [], "documents": []}

    monkeypatch.setattr(reproduction, "compare_edition", compare_edition)
    reproduction.compare_editions({"zh": None, "en": None}, {}, {}, record=True)
    assert compared == ["zh", "en"]
    for code in ("zh", "en"):
        record = repository.read(f"build/evidence/editions/{code}/durations/reproduce.json")
        assert (record["command"], record["completed"]) == ("reproduce", True)
    for path in list(tmp_path.rglob("*.json")):
        path.unlink()
    reproduction.compare_editions({"zh": None, "en": None}, {}, {}, record=False)
    assert list(tmp_path.rglob("*.json")) == []


def comparing(monkeypatch, films_of):
    """Have each edition's comparison return the given films' results and nothing else."""

    def compare_edition(edition, record, assets, listed):
        return {"films": films_of(edition.code), "documents": []}

    monkeypatch.setattr(reproduction, "compare_edition", compare_edition)


@pytest.mark.parametrize(
    ("film", "completed"),
    [
        ({"asset": "film.mp4", "verdict": "pass", "failing": []}, True),
        ({"asset": "film.mp4", "verdict": "fail", "failing": ["picture"]}, False),
        # A film without a recorded floor is not yet reproduced.
        ({"asset": "film.mp4", "verdict": "calibrating", "failing": []}, False),
    ],
    ids=["pass", "fail", "calibrating"],
)
def test_an_edition_whose_comparison_does_not_pass_is_recorded_as_not_completed(
    tmp_path, monkeypatch, film, completed
):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    # The Chinese edition passes; the English one holds the film in question.
    passing = {"asset": "film.mp4", "verdict": "pass", "failing": []}
    comparing(monkeypatch, lambda code: [passing if code == "zh" else film])
    compared = reproduction.compare_editions({"zh": None, "en": None}, {}, {}, record=True)
    assert [*compared] == ["zh", "en"]
    assert compared["en"]["films"] == [film]
    records = {
        code: repository.read(f"build/evidence/editions/{code}/durations/reproduce.json")
        for code in ("zh", "en")
    }
    assert records["zh"]["completed"] is True
    assert records["en"]["completed"] is completed


def test_a_failing_layer_of_an_edition_is_recorded_as_not_completed(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())

    def compare_edition(edition, record, assets, listed):
        soundtrack = {"verdict": "fail" if edition.code == "zh" else "pass"}
        return {"soundtrack": soundtrack, "films": [], "documents": []}

    monkeypatch.setattr(reproduction, "compare_edition", compare_edition)
    reproduction.compare_editions({"zh": None, "en": None}, {}, {}, record=True)
    zh = repository.read("build/evidence/editions/zh/durations/reproduce.json")
    en = repository.read("build/evidence/editions/en/durations/reproduce.json")
    assert (zh["completed"], en["completed"]) == (False, True)
