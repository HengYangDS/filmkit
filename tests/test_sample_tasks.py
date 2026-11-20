"""The sample film's tasks, read from the repository's task configuration, which nothing but a
whole build runs."""

import tomllib
from pathlib import Path

from filmkit.production import CODES

TASKS = Path(__file__).resolve().parents[1] / ".config/mise/config.toml"


def test_the_sample_s_package_task_scans_each_edition_s_film_right_after_packaging_it():
    # The verifier requires each edition's film record, so a package task without `scan-film`
    # would stop the sample's build at its verification.
    run = tomllib.loads(TASKS.read_text(encoding="utf-8"))["tasks"]["sample:package"]["run"]
    actions = [tuple(command.split()[-3:]) for command in run]
    for code in CODES:
        packaged = actions.index(("package-film", "--language", code))
        assert actions[packaged + 1] == ("scan-film", "--language", code)
