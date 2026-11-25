"""The sample film's tasks, read from the repository's task configuration: the sample builds by
the engine's verbs and by no module command (design decision 17 of build-a-film-by-its-verbs)."""

import re
import tomllib
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1] / ".config/mise/config.toml"
# Each task of the sample's build and the verb it runs.
VERBS = {
    "sample:supply": "filmkit supply",
    "sample:check": "filmkit check",
    "sample:narrate": "filmkit narrate --edition all",
    "sample:build": "filmkit build all",
    "sample:verify": "filmkit verify --technical-only",
}


def test_each_sample_task_runs_its_verb_in_the_sample_and_no_module_command():
    tasks = tomllib.loads(TASKS.read_text(encoding="utf-8"))["tasks"]
    sample = {name: task for name, task in tasks.items() if name.startswith("sample:")}
    assert set(sample) == set(VERBS)
    for name, task in sample.items():
        assert task["dir"] == "{{config_root}}/examples/sample-film"
        assert task["run"].endswith(f" {VERBS[name]}")
        assert not re.search(r"python -m filmkit", task["run"])
