"""The stage the engine writes gives the real-browser check its frame contract.

The geometry check takes a picture's size, seconds and rate from the stage's record and holds the
stage's page to it; the page states no rate. On 19 November 2026 the sample film's page had lost
its rate together with the browser renderer's attributes, and the check, which still read the
page, refused every stage: no test ran it on a stage the engine had made, so a rehearsal of a
build was the first to meet it.
"""

import json
import shutil
import subprocess
from pathlib import Path

import filmkit.picture.rendering as picture_rendering
from filmkit.production import Edition
from filmkit.specification import DURATION, FPS

# The contract's reader imports no browser, so it runs wherever the engine's Node tools run.
CONTRACT = Path(picture_rendering.__file__).with_name("stage-contract.mjs")
PROGRAM = (
    f"import {{ frameContract }} from {json.dumps(CONTRACT.as_uri())};"
    "try { console.log(JSON.stringify(await frameContract(process.argv[1]))); }"
    "catch (error) { console.error(error.message); process.exit(1); }"
)


def contract(stage: Path) -> subprocess.CompletedProcess:
    node = shutil.which("node")
    assert node, "the engine's Node tools need node on PATH"
    command = [node, "--input-type=module", "-e", PROGRAM, str(stage)]
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)


def test_the_geometry_check_reads_its_frame_contract_from_the_engines_own_stage(film_root):
    edition = Edition("zh")
    film_root.staged(edition)
    stage = edition.picture_stage
    read = contract(stage)
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout) == [3840, 2160, DURATION, FPS]
    assert "data-fps" not in (stage / "index.html").read_text(encoding="utf-8")
    # A stage restaged at another size and cut short before its record: the page and the record
    # disagree, and the refusal names what to run.
    record = json.loads((stage / "stage.json").read_text(encoding="utf-8"))
    (stage / "stage.json").write_text(json.dumps({**record, "width": 1920}), encoding="utf-8")
    apart = contract(stage)
    assert apart.returncode == 1
    page = stage / "index.html"
    assert f"page {page} states a width of 3840 where its record states 1920" in apart.stderr
    assert apart.stderr.rstrip().endswith("run stage-picture again")
