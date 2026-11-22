"""The pre-render check with the register check: a film's words refused before a render, the
refused receipt it writes, and the entry page that both editions' receipts bind."""

import shutil
import sys

import pytest
import test_preflight as base

import filmkit.concepts as concepts
import filmkit.preflight as preflight
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.production import Edition

# The edition of the pre-render tests, every input of its render current, and their helpers.
edition = base.edition
painted, put, ready = base.painted, base.put, base.ready
SAMPLE = repository.ROOT
# The register and concept checks themselves, kept before the fixture stands in for them.
REGISTER_CHECK = preflight.register.check
CONCEPT_CHECK = preflight.concepts.check


def test_a_form_the_register_refuses_is_named_and_refuses(edition, monkeypatch):
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    monkeypatch.setattr(preflight.register, "check", REGISTER_CHECK)
    held = [concepts.Place("zh 01.1", "你们先看。"), concepts.Place("en 01.1", "Stop!")]
    monkeypatch.setattr(concepts, "places", lambda: {"zh": held})
    with pytest.raises(preflight.PreflightError) as refusal:
        preflight.preflight(edition)
    said = (
        "zh 01.1: '你们' addresses the audience (R1); en 01.1: '!' is an exclamation, a dash or an "
        "ellipsis (R5)"
    )
    assert str(refusal.value).endswith(f"register: {said}")
    receipt = repository.read(edition.readiness)
    assert (receipt["verdict"], receipt["inputs"]["register"]) == ("refuse", said)
    # A Vale that is not the pinned one refuses before any word is read, with a receipt too.
    other = repository.ROOT / "bin/vale"
    put(other, f"#!{sys.executable}\nprint('vale version 9.9.9')\n").chmod(0o755)
    monkeypatch.setenv("PATH", str(other.parent))
    with pytest.raises(preflight.PreflightError, match="register: .* reports Vale 9.9.9"):
        preflight.preflight(edition)
    assert repository.read(edition.readiness)["verdict"] == "refuse"


def test_an_entry_page_that_is_no_text_ends_both_word_checks_in_a_refused_receipt(
    edition, monkeypatch
):
    shutil.copytree(SAMPLE / "content", repository.ROOT / "content", dirs_exist_ok=True)
    (repository.ROOT / FILM.entry).write_bytes(b"<p>\xff</p>")
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    monkeypatch.setattr(preflight.register, "check", REGISTER_CHECK)
    monkeypatch.setattr(preflight.concepts, "check", CONCEPT_CHECK)
    with pytest.raises(preflight.PreflightError):
        preflight.preflight(edition)
    receipt, said = repository.read(edition.readiness), "The entry page content/index.html is no "
    said += "UTF-8 text: byte 3 cannot be read"
    assert (receipt["verdict"], receipt["inputs"]["concepts"]) == ("refuse", said)
    assert receipt["inputs"]["register"] == said


def test_a_change_of_the_entry_page_admits_neither_edition(edition, monkeypatch):
    for path in (Edition("en").script, Edition("en").cast):
        put(repository.ROOT / path, "{}")
    for path in (Edition("en").timeline, Edition("en").audio_assembly, Edition("en").soundtrack):
        put(path, "{}")
    ready("zh", monkeypatch)
    ready("en", monkeypatch)
    put(repository.ROOT / FILM.entry, "<title>Another</title>\n")
    with pytest.raises(preflight.PreflightError) as refusal:
        preflight.admitted(edition)
    assert str(refusal.value) == (
        "The zh edition is not admitted: build/evidence/editions/zh/readiness.json binds another"
        " entry; run preflight --language zh | build/evidence/editions/en/readiness.json binds"
        " another entry; run preflight --language en"
    )
