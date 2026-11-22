"""A take's verdict on every line the film holds for it, and the choice among judged takes."""

import dataclasses
import json
import wave

import numpy as np
import pytest

import filmkit.film as film
import filmkit.narration.group_generation as narration_group_generation
import filmkit.narration.judge as narration_judge
import filmkit.narration.judgment as narration_judgment
import filmkit.narration.readings as narration_readings
import filmkit.narration.terms as narration_terms
import filmkit.preflight as preflight
import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly
from filmkit.narration.recognition import Names
from filmkit.production import Edition


def take(seed, *, failed=(), clarity=None, pause=None, end_ratio=0.1, line=18.0) -> dict:
    verdict = {"passes": None} if clarity is None else {"passes": True, **line_of(line)}
    return {
        "seed": seed,
        "failed": list(failed),
        "end_ratio": end_ratio,
        "clarity": None if clarity is None else {"cpp_db": clarity},
        "nearest_unmarked_pause": pause and {"pause_s": pause[0], "limit_s": pause[1]},
        "lines": {"clarity": verdict},
    }


def line_of(line) -> dict:
    return {"floor_db": 18.0} if line is None else {"line_db": line, "floor_db": 18.0}


def test_a_choice_takes_the_widest_margin_among_the_takes_no_line_refuses():
    takes = [
        take(1, failed=["ending"], clarity=25.0),
        take(2, failed=["units"], clarity=21.0),
        take(3, clarity=18.9),
        take(4, clarity=19.8),
        take(5, clarity=19.8, pause=(0.38, 0.4)),
    ]
    # A line refuses takes 1 and 2, however clear they are; take 4 stands widest above its
    # line, and take 5's pause brings it nearer to a line than its clarity does.
    assert narration_judgment.choose(takes)["seed"] == 4
    assert narration_judgment.margin(takes[4]) == pytest.approx(0.05)
    assert narration_judgment.margin(takes[3]) == pytest.approx(0.1)
    # The margin is taken from the pause nearest its limit: 0.19 s under a script switch's
    # 0.2 s stands nearer than 0.25 s under 0.4 s, though the second pause is the longer.
    assert narration_judgment.margin(take(6, pause=(0.19, 0.2))) == pytest.approx(0.05)
    # Where a single thought has no line, the margin is taken above the edition's floor.
    assert narration_judgment.margin(take(7, clarity=19.8, line=None)) == pytest.approx(0.1)
    # Without a line that has a margin the quietest ending is taken, then the lowest seed.
    plain = [take(8, end_ratio=0.2), take(7, end_ratio=0.05), take(6, end_ratio=0.05)]
    assert narration_judgment.margin(plain[0]) == float("inf")
    assert narration_judgment.choose(plain)["seed"] == 6
    assert narration_judgment.choose(takes[:1]) is None


def measured(
    *, natural=True, clip_quiet=True, stops=(), fluent=True, terms=True, units=(0, 0), short=False
) -> dict:
    return {
        "path": "take.wav",
        "natural": natural,
        "clip_opens_quiet": clip_quiet,
        "phrase_stops": None if stops is None else list(stops),
        "fluent": fluent,
        "terms_pass": terms,
        "differing_units": units[0],
        "differing_units_by_reading": units[1],
        "short": short,
    }


def test_every_failing_line_of_a_take_is_named_at_once():
    held = narration_judgment.Held({"26": {2: 0.12}})
    sound = narration_judgment.judge(measured(), "26", 1, held)
    assert sound["failed"] == []
    assert sound["lines"]["units"] == {"passes": True, "limit": 0}
    assert sound["lines"]["clarity"] == {"passes": None, "why": narration_judgment.NO_FLOOR}
    broken = measured(
        natural=False, clip_quiet=False, stops=None, fluent=False, terms=False, units=(2, 2)
    )
    judged = narration_judgment.judge({**broken, "short": True}, "26", 1, held)
    assert judged["failed"] == ["length", "ending", "phrase", "opening", "pause", "terms", "units"]
    # A thought that does not open its recording has no opening line, and a declared release
    # of its join keeps an ending that is cut, as the assembly reads it.
    later = narration_judgment.judge(measured(natural=False, clip_quiet=False), "26", 2, held)
    assert later["failed"] == []
    assert later["lines"]["opening"] == {"passes": None, "why": narration_judgment.NOT_OPENING}
    assert later["lines"]["ending"] == {"passes": True, "release_declared": True}
    # A run-on take that found no quiet to be cut in holds the next words: no release keeps it.
    uncut = {**measured(natural=False), "run_on": None}
    assert narration_judgment.judge(uncut, "26", 2, held)["failed"] == ["ending"]


def test_a_take_is_held_to_its_words_by_reading_and_not_to_the_recognizers_spelling():
    held = narration_judgment.Held({})
    # Three units differ as written and none as heard: a homophone, a spelling, a spacing.
    spelled = narration_judgment.judge(measured(units=(3, 0)), "26", 2, held)
    assert (spelled["failed"], spelled["lines"]["units"]["passes"]) == ([], True)
    # One unit that differs by reading is a word heard as another: the take is refused.
    other = narration_judgment.judge(measured(units=(1, 1)), "26", 2, held)
    assert other["failed"] == ["units"]
    assert narration_judgment.refusal([{"thought": "26.2", **other}]) == [
        "  26.2: units: it is heard to say other words than its text"
    ]


def test_a_take_of_one_second_or_less_is_refused_as_the_engine_refuses_such_a_recording(
    narrated, voiced
):
    narrated([voiced(), voiced()])
    record = repository.read(Edition("en").ear_first / "narration-receipt.json")["records"][0]
    bench, held = narration_judgment.studio("en", [record])
    path = repository.ROOT / "02-take.wav"
    for seconds, short in ((0.8, True), (1.2, False)):
        pcm = voiced(seconds=seconds)
        with wave.open(str(path), "wb") as take_file:
            take_file.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            take_file.writeframes(pcm.tobytes())
        take_row = narration_judgment.measured(path, "26.2", " Second thought.", bench)
        assert take_row["short"] is short
        assert ("length" in narration_judgment.judge(take_row, "26", 2, held)["failed"]) is short
        assert narration_group_generation.too_short(len(pcm), 24000) is short


def test_clarity_is_judged_only_where_the_film_declares_a_line_for_a_single_thought(
    monkeypatch, declared
):
    script = {"segments": [{"id": "26", "utterance_groups": ["First.", " Second."]}]}
    declared(clarity_minimum_db=None)
    film_declared = narration_judgment.FILM
    assert narration_judgment.held("en", script, film_declared) == narration_judgment.Held({})
    # The film declares a floor and no line for a single thought: recorded, as preflight words it.
    floors = {"zh": 18.0, "en": 17.0}
    declared(clarity_minimum_db=floors)
    held = narration_judgment.held("en", script, narration_judgment.FILM)
    assert (held.floor, held.line, held.kept) == (17.0, None, frozenset())
    assert narration_judgment.NO_THOUGHT_LINE is preflight.NO_THOUGHT_LINE
    line = narration_judgment.clarity_line({"cpp_db": 15.0}, "26.2", held)
    assert line == {"passes": None, "why": preflight.NO_THOUGHT_LINE, "floor_db": 17.0}
    # With a margin a thought is held to the floor, and a thought the film keeps to the floor
    # less the margin.
    kept = film.ClarityException(edition="en", thought="26.2", reason="a short thought")
    declared(
        clarity_minimum_db=floors,
        clarity_thought_margin_db=1.0,
        clarity_exceptions=(kept,),
    )
    held = narration_judgment.held("en", script, narration_judgment.FILM)
    assert (held.floor, held.line, held.kept) == (17.0, 16.0, frozenset({"26.2"}))
    verdicts = [
        narration_judgment.clarity_line({"cpp_db": value}, thought, held)["passes"]
        for thought, value in (("26.1", 17.0), ("26.1", 16.5), ("26.2", 16.5), ("26.2", 15.9))
    ]
    assert verdicts == [True, False, True, False]
    # A take that keeps no frame has no value: it is not judged, as the sound gate reads it.
    silent = narration_judgment.clarity_line({"cpp_db": None}, "26.1", held)
    assert (silent["passes"], silent["why"]) == (None, narration_judgment.NO_FRAMES)
    # `judge` fails the line for a take under it and names the line a kept thought is held to.
    monkeypatch.setattr(narration_judgment, "take_clarity", lambda _path, _floor: {"cpp_db": 16.5})
    under = narration_judgment.judge(measured(), "26", 1, held)
    assert (under["failed"], under["lines"]["clarity"]["line_db"]) == (["clarity"], 17.0)
    kept_take = narration_judgment.judge(measured(), "26", 2, held)
    assert (kept_take["failed"], kept_take["lines"]["clarity"]["line_db"]) == ([], 16.0)


def test_preflight_and_the_judgment_refuse_the_same_thoughts_for_their_clarity(
    monkeypatch, declared, tmp_path
):
    # One sound gate record: four thoughts under the floor of 17, one of them kept by the film.
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    values = {"26.1": 17.2, "26.2": 16.5, "26.3": 16.5, "26.4": 15.9, "26.5": None}
    kept = film.ClarityException(edition="en", thought="26.3", reason="a short thought")
    declared(
        clarity_minimum_db={"zh": 18.0, "en": 17.0},
        clarity_thought_margin_db=1.0,
        clarity_exceptions=(kept,),
    )
    monkeypatch.setattr(preflight, "FILM", narration_judgment.FILM)
    rows = [
        {"id": name, "cpp_db": value, "below_floor": value is not None and value < 17.0}
        for name, value in values.items()
    ]
    edition = Edition("en")
    repository.write(edition.sound_gates, {"clarity": {"floor_db": 17.0, "thoughts": rows}})
    said = preflight.clarity(edition)
    held = narration_judgment.held("en", {"segments": []}, narration_judgment.FILM)
    for name, value in values.items():
        line = narration_judgment.clarity_line({"cpp_db": value}, name, held)
        assert (line["passes"] is False) is (f"thought {name} reads" in said), name
    assert [name for name in values if f"thought {name} reads" in said] == ["26.2", "26.4"]


def test_the_assembly_and_the_judgment_keep_the_same_endings(narrated, voiced):
    # One record: the first thought ends naturally, the second and the third are cut.
    thoughts = ["First thought.", " Second thought.", " Third thought."]
    plans = [{"text": text, "spoken_text": text} for text in thoughts]
    record = narrated([voiced(), voiced(natural=False), voiced(natural=False)], plans)
    releases = {"26": {3: 0.12}}
    segment = {"id": "26"}
    abrupt = soundtrack_assembly._abrupt_thoughts([segment], {"26": record}, releases)  # noqa: SLF001
    held = narration_judgment.Held(releases)
    refused = [
        f"26.{child['index']}"
        for child in record["utterance_groups"]["records"]
        if "ending"
        in narration_judgment.judge({**measured(), **ending_of(child)}, "26", child["index"], held)[
            "failed"
        ]
    ]
    assert abrupt == refused == ["26.2"]


def ending_of(child: dict) -> dict:
    with wave.open(str(repository.ROOT / child["path"])) as source:
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    return {"natural": narration_judgment.ending(pcm, 24000)["natural"]}


def test_a_chinese_take_is_compared_by_the_readings_the_film_declares(monkeypatch, tmp_path):
    # The bench of a Chinese edition holds the words whose readings the film's contract declares,
    # and each word a homophone rule respells, read as its spoken form reads.
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    contract = {
        "schema_version": 2,
        "pronunciation": {
            "languages": {
                "Chinese": {
                    "normalization": [{"display": "去重", "spoken": "去虫", "kind": "homophone"}],
                    "targets": [
                        {
                            "kind": "contextual-mandarin-word",
                            "term": "重来",
                            "target_reading": "chóng lái",
                        }
                    ],
                }
            }
        },
    }
    repository.write("contract.json", contract)
    repository.write(
        Edition("zh").script,
        {"pronunciation_contract": "contract.json", "segments": []},
    )
    monkeypatch.setattr(narration_judgment, "standards", lambda *_: [])
    bench = narration_judgment.bench("zh", [], asr=None, aligner={})
    assert [word.term for word in bench.words] == ["重来", "去重"]
    assert bench.words == narration_readings.compared_words(
        contract["pronunciation"]["languages"]["Chinese"]
    )


NAME = film.NarrationTerm(
    term="NAME", spoken="Naim", ipa="ˈneɪm", reference={"en": {"thought": "26.1", "index": 0}}
)
SAYS_NAME = ("Naim is built.", " Second thought.")
CLOSE = narration_terms.Vowel(250.0, 2750.0, 6)


def says_name(narrated, voiced, monkeypatch, *, term: bool = True) -> dict:
    """An English edition whose first thought says NAME as its contract respells it, Naim.

    With `term`, the film declares NAME with its reference in that thought. The receipt's
    texts are its spoken texts, as the retained records hold them.
    """
    record = narrated([voiced(), voiced()], [{"text": t, "spoken_text": t} for t in SAYS_NAME])
    rule = {"display": "NAME", "spoken": "Naim", "kind": "english-name"}
    languages = {"English": {"normalization": [rule]}}
    repository.write("content/voice-performance.json", {"pronunciation": {"languages": languages}})
    narrated.recognizer.thoughts[:2] = SAYS_NAME
    if term:
        update = {"narration": film.Narration(terms=(NAME,))}
        monkeypatch.setattr(
            narration_judgment, "FILM", narration_judgment.FILM.model_copy(update=update)
        )
    return record


def test_a_take_that_says_a_declared_term_is_held_to_the_term_and_not_to_its_respelling(
    narrated, voiced, monkeypatch
):
    says_name(narrated, voiced, monkeypatch)
    # The recognizer writes the name as it is displayed; the stand-in voice is a tone, so the
    # term's first vowel is stood in for.
    narrated.recognizer.thoughts[0] = "Name is built."
    monkeypatch.setattr(narration_terms, "first_vowel", lambda *_: CLOSE)
    narration_judge.main(["--language", "en"])
    first = repository.read(Edition("en").ear_first / narration_judge.RECORD)["thoughts"][0]
    assert (first["differing_units"], first["differing_units_by_reading"]) == (1, 0)
    assert first["failed"] == []


def test_a_chinese_bench_reads_the_editions_other_latin_units_from_its_script(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    rule = {"display": "NAME", "spoken": "Naim", "kind": "english-name"}
    languages = {language: {"normalization": [rule]} for language in ("Chinese", "English")}
    repository.write("contract.json", {"pronunciation": {"languages": languages}})
    groups = ["NAME 和 Agent 一起。", "再用 Node.js 跑。"]
    text = "".join(groups)
    spoken = text.replace("NAME", "Naim")
    segment = {"id": "01", "text": text, "spoken_text": spoken, "utterance_groups": groups}
    for code in ("zh", "en"):
        script = {"pronunciation_contract": "contract.json", "segments": [segment]}
        repository.write(Edition(code).script, script)
    monkeypatch.setattr(narration_judgment, "standards", lambda *_: [])
    declared = narration_judgment.FILM.model_copy(
        update={"narration": film.Narration(terms=(NAME,))}
    )
    # The script's Latin units by their letters, less the term's: `Node.js` is two units.
    zh = narration_judgment.bench("zh", [], asr=None, aligner={}, film=declared)
    assert zh.names == Names((NAME,), chinese=True, others=frozenset({"agent", "node", "js"}))
    # The English bench has no rule of other letters, under which any word would pass.
    en = narration_judgment.bench("en", [], asr=None, aligner={}, film=declared)
    assert en.names == Names((NAME,))
    # Nor has a Chinese bench whose script names no contract: no script units are known.
    repository.write(Edition("zh").script, {"segments": [segment]})
    bare = narration_judgment.bench("zh", [], asr=None, aligner={}, film=declared)
    assert (bare.words, bare.names) == ((), Names((NAME,)))


def test_a_take_records_the_unit_that_stood_for_a_term_in_other_letters(narrated, voiced):
    record = narrated([voiced(), voiced()])
    bench, _held = narration_judgment.studio("en", [record])
    chinese = dataclasses.replace(
        bench, code="zh", language="Chinese", names=Names((NAME,), chinese=True)
    )
    path = repository.ROOT / record["utterance_groups"]["records"][0]["path"]
    said = "Naim 走的是另一条路。"
    narrated.recognizer.heard[path.name] = "Nime 走的是另一条路。"
    take = narration_judgment.measured(path, "26.1", said, chinese)
    assert take["differing_units_by_reading"] == 0
    assert take["terms_in_other_letters"] == [{"term": "NAME", "unit": "nime"}]
    # A take that writes the term in one of its forms records none.
    narrated.recognizer.heard[path.name] = "Name 走的是另一条路。"
    take = narration_judgment.measured(path, "26.1", said, chinese)
    assert take["differing_units_by_reading"] == 0
    assert "terms_in_other_letters" not in take


def test_a_complete_receipt_with_an_undeclared_respelled_name_is_refused_before_any_model_loads(
    narrated, voiced, monkeypatch
):
    # A complete receipt narrates nothing, so no readings check runs before the models load.
    says_name(narrated, voiced, monkeypatch, term=False)
    monkeypatch.setattr(narration_judgment, "load_asr", pytest.fail)
    monkeypatch.setattr(narration_judgment, "load_aligner", pytest.fail)
    with pytest.raises(SystemExit) as refused:
        narration_judge.main(["--language", "en"])
    assert str(refused.value) == (
        "en: the normalization respells NAME as Naim, said in 26.1; declare NAME in "
        "[[narration.terms]]"
    )


def test_a_reference_take_without_two_formants_is_refused_in_one_line(
    narrated, voiced, monkeypatch
):
    import converging

    record = says_name(narrated, voiced, monkeypatch)
    another = "declare another occurrence of NAME as its en reference in [[narration.terms]]"
    # On its take alone the reference shows no two formants: no take can be held to it.
    monkeypatch.setattr(narration_terms, "first_vowel", lambda *_: None)
    with pytest.raises(SystemExit) as refused:
        narration_judge.main(["--language", "en"])
    assert str(refused.value) == (
        f"en: the NAME reference 26.1 #0 shows no two formants on its take; {another}"
    )
    # The take alone shows two, the segment as the selection aligns it none: the gate stops
    # before any thought is judged, where it would otherwise settle every thought.
    converging.write_checks("en", [record], converging.placed)

    def vowel(recording, *_):
        return CLOSE if len(recording.mono) < 3 * 24000 else None

    monkeypatch.setattr(narration_terms, "first_vowel", vowel)
    with pytest.raises(SystemExit) as refused:
        narration_judge.main(["--language", "en"])
    assert str(refused.value) == (
        "en: the NAME reference 26.1 #0 shows no two formants as the selection aligns its "
        f"segment; {another}"
    )
    assert not (Edition("en").ear_first / narration_judge.RECORD).exists()


def test_a_reference_the_segments_alignment_does_not_place_is_refused_in_one_line(
    narrated, voiced, monkeypatch
):
    import converging

    record = says_name(narrated, voiced, monkeypatch)
    monkeypatch.setattr(narration_terms, "first_vowel", lambda *_: CLOSE)

    def misplaced(segment):
        """The segment's words as an aligner placed them that parts the name in two items."""
        found = []
        for word, start, end in converging.placed(segment):
            middle = (start + end) / 2
            found += [("Na", start, middle), ("im", middle, end)] if word == "Naim" else []
            found += [] if word == "Naim" else [(word, start, end)]
        return found

    # The take alone holds its reference; the segment's alignment holds none: no thought is
    # named, so the gate stops before any thought is judged rather than let every one settle.
    converging.write_checks("en", [record], misplaced)
    with pytest.raises(SystemExit) as refused:
        narration_judge.main(["--language", "en"])
    assert str(refused.value) == (
        "en: the NAME reference 26.1 #0 is not in the narration as the selection aligns its "
        "segment; declare another occurrence of NAME as its en reference in [[narration.terms]]"
    )
    assert not (Edition("en").ear_first / narration_judge.RECORD).exists()


def test_judge_refuses_every_thought_with_every_failing_line_and_writes_one_record(
    narrated, voiced, capsys
):
    narrated([voiced(quiet_first=False), voiced(natural=False)])
    with pytest.raises(SystemExit) as refused:
        narration_judge.main(["--language", "en"])
    assert str(refused.value).splitlines() == [
        "en: 2 of 2 thoughts are refused",
        "  26.1: opening: it opens its recording in sound",
        "  26.2: ending: it ends abruptly where its join declares no release",
    ]
    record = repository.read(Edition("en").ear_first / narration_judge.RECORD)
    assert record["refused"] == {"26.1": ["opening"], "26.2": ["ending"]}
    assert record["clarity"] == {"floor_db": None, "thought_line_db": None, "kept": []}
    assert [row["thought"] for row in record["thoughts"]] == ["26.1", "26.2"]
    first = record["thoughts"][0]
    assert (first["differing_units"], first["differing_units_by_reading"]) == (0, 0)
    assert record["unit_limit"] == 0
    assert set(record["bound"]) == {"receipt_sha256", "script_sha256", "cast_sha256"}
    assert json.loads(capsys.readouterr().out)["refused"] == 2


def test_judging_accepted_takes_again_writes_the_same_record(narrated, voiced, capsys):
    narrated([voiced(), voiced()])
    narration_judge.main(["--language", "en"])
    path = Edition("en").ear_first / narration_judge.RECORD
    first = path.read_bytes()
    narration_judge.main(["--language", "en"])
    assert path.read_bytes() == first
    assert repository.read(path)["refused"] == {}
    assert [json.loads(line)["refused"] for line in capsys.readouterr().out.splitlines()] == [0, 0]


def test_a_receipt_that_does_not_hold_the_current_thought_is_refused_before_any_model(
    narrated, voiced, monkeypatch
):
    narrated([voiced(), voiced()])
    script = repository.read(Edition("en").script)
    script["segments"][0]["utterance_groups"][1] = " Another thought."
    repository.write(Edition("en").script, script)
    monkeypatch.setattr(narration_judgment, "load_asr", pytest.fail)
    with pytest.raises(ValueError, match="26.2: the receipt does not hold the current thought"):
        narration_judge.main(["--language", "en"])


def test_a_receipt_that_lacks_a_segment_of_the_script_is_refused(narrated, voiced, monkeypatch):
    narrated([voiced(), voiced()])
    script = repository.read(Edition("en").script)
    script["segments"].append(
        {
            "id": "27",
            "text": "Third thought. Fourth thought.",
            "spoken_text": "Third thought. Fourth thought.",
            "utterance_groups": ["Third thought.", " Fourth thought."],
        }
    )
    repository.write(Edition("en").script, script)
    monkeypatch.setattr(narration_judgment, "load_asr", pytest.fail)
    with pytest.raises(ValueError, match="it lacks 27.1, 27.2"):
        narration_judge.main(["--language", "en"])


def test_the_judgment_reads_the_receipt_the_cast_declares(narrated, voiced):
    narrated([voiced(), voiced()])
    assert narration_judge.receipt_of("en").endswith("ear-first/narration-receipt.json")
    cast = repository.read(Edition("en").cast)
    cast["performance_recording"] = {"receipt": "build/other-receipt.json"}
    repository.write(Edition("en").cast, cast)
    assert narration_judge.receipt_of("en") == "build/other-receipt.json"
