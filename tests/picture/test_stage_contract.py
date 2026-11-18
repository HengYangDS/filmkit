"""The stage the engine writes gives the real-browser check its frame contract.

The geometry check takes a picture's size, seconds and rate from the stage's record, and the page
states no rate. On 19 November 2026 the sample film's page had lost its rate together with the
browser renderer's attributes, and the check, which still read the page, refused every stage: no
test ran it on a stage the engine had made, so a build was the first to meet it.
"""

import json
import subprocess
from pathlib import Path

import filmkit.picture.rendering as picture_rendering
from filmkit.production import Edition
from filmkit.specification import DURATION, FPS

CHECK = Path(picture_rendering.__file__).with_name("geometry-check.mjs")
PROGRAM = (
    f"import {{ frameContract }} from {json.dumps(CHECK.as_uri())};"
    "console.log(JSON.stringify(await frameContract(process.argv[1])));"
)


def test_the_geometry_check_reads_its_frame_contract_from_the_engines_own_stage(
    film_root,
):
    edition = Edition("zh")
    film_root.staged(edition)
    stage = edition.picture_stage
    command = ["node", "--input-type=module", "-e", PROGRAM, str(stage)]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == [3840, 2160, DURATION, FPS]
    assert "data-fps" not in (stage / "index.html").read_text(encoding="utf-8")
