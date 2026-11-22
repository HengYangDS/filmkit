"""The register check's base style: each rule's own cases pass under the pinned Vale, every rule
fires in one of them, and so does every form an error-level rule refuses."""

import shutil
import subprocess
from pathlib import Path

import yaml

import filmkit.register as register
import filmkit.released as released

STYLE = Path(register.__file__).with_name("styles") / "register"


def pinned() -> str:
    """The Vale on the path, which must be the version the engine's release states."""
    vale = shutil.which("vale")
    assert vale, "no vale on the path; run the suite under Mise, which pins it"
    reported = subprocess.run([vale, "--version"], capture_output=True, text=True, check=True)
    assert reported.stdout.split() == ["vale", "version", released.vale()]
    return vale


def test_every_rule_passes_its_cases_and_fires_in_one(tmp_path):
    tested = subprocess.run(
        [pinned(), "test", "--coverage", str(STYLE)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        timeout=60,
    )
    assert tested.returncode == 0, tested.stdout + tested.stderr


def test_every_token_of_an_error_rule_fires_in_one_of_its_cases(tmp_path):
    # Vale's coverage judges a rule, so each token runs here as a rule of its own over the
    # cases of the rule that holds it.
    probes, inputs, owners = tmp_path / "styles/Probe", [], {}
    probes.mkdir(parents=True)
    for path in sorted(STYLE.glob("*.yml")):
        rule = yaml.safe_load(path.read_text(encoding="utf-8"))
        if rule["level"] != "error":
            continue
        inputs += [case["input"] for case in rule["tests"]]
        for index, token in enumerate(rule["tokens"]):
            name = f"{path.stem}{index}"
            owners[f"Probe.{name}"] = f"{path.stem}: {token}"
            probe = {**rule, "message": "%s", "tokens": [token], "tests": []}
            (probes / f"{name}.yml").write_text(yaml.safe_dump(probe, allow_unicode=True))
    config = tmp_path / "probe.ini"
    config.write_text("StylesPath = styles\n\n[*.txt]\nBasedOnStyles = Probe\n")
    linted = subprocess.run(
        [pinned(), "--no-global", f"--config={config}", "--ext=.txt", "--output=JSON"],
        input="\n\n".join(line for text in inputs for line in text.splitlines() if line) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    fired = {alert["Check"] for held in yaml.safe_load(linted.stdout).values() for alert in held}
    assert sorted(owners[name] for name in set(owners) - fired) == []
