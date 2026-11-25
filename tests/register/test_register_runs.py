"""The register check's Vale: the pinned one, run as documented, on the engine's own rule files;
a run it cannot read is a refusal in one line."""

import configparser
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from placing import placed, refused, refused_lines

import filmkit.child_processes as child_processes
import filmkit.concepts as concepts
import filmkit.languages as languages
import filmkit.register as register
import filmkit.released as released

ADDRESS = "addresses the audience (R1)"


def stand_in(tmp_path, monkeypatch, lint: str, version: str = "pass") -> Path:
    """A vale first on the path that reports the pinned version after `version`'s statement
    and answers a lint run, after reading its text, with `lint`'s statements."""
    vale = tmp_path / "bin/vale"
    vale.parent.mkdir()
    program = f"""\
        #!{sys.executable}
        import json, sys, time
        if "--version" in sys.argv:
            {version}
            print("vale version {released.vale()}")
        else:
            text = sys.stdin.buffer.read()
            {lint}
        """
    vale.write_text(textwrap.dedent(program))
    vale.chmod(0o755)
    monkeypatch.setenv("PATH", str(vale.parent))
    return vale


def alert(line: int, severity: str = "error", match: object = "你们", span=(1, 2)) -> str:
    """A Vale alert of a form on a line, as a Python literal for the stand-in to print."""
    fields = {"Check": "register.address", "Message": f"'你们' {ADDRESS}", "Span": list(span)}
    return repr({**fields, "Severity": severity, "Match": match, "Line": line})


@pytest.mark.parametrize(
    ("lint", "version", "said"),
    [
        ("print('no json')", "pass", "Vale printed no JSON object of alerts: no json"),
        ("print('[]')", "pass", "Vale printed no JSON object of alerts: []"),
        ("print(json.dumps({'x': 1}))", "pass", "Vale printed no JSON object of alerts"),
        ("pass", "pass", "Vale ended with status 0 and printed nothing"),
        ("sys.exit(1)", "pass", "Vale ended with status 1 and printed nothing"),
        ("print('{}'); sys.exit(2)", "pass", "Vale ended with status 2"),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(1, 'warning')}]}})); sys.exit(1)",
            "pass",
            "Vale ended with status 1 and reported no error-level alert",
        ),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(1)}]}}))",
            "pass",
            "Vale ended with status 0 though it reported an error-level alert",
        ),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(999)}]}})); sys.exit(1)",
            "pass",
            "Vale reported an alert that names no place: ",
        ),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(1, span=(2, 3))}]}})); sys.exit(1)",
            "pass",
            "Vale reported '你们' at a span its place does not hold it: [2, 3]",
        ),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(1, 'ERROR')}]}}))",
            "pass",
            "Vale reported an alert this check cannot read: ",
        ),
        (
            f"print(json.dumps({{'stdin.txt': [{alert(1, match=7)}]}})); sys.exit(1)",
            "pass",
            "Vale reported an alert this check cannot read: ",
        ),
        ("sys.stdout.buffer.write(b'{\\xff}'); sys.exit(1)", "pass", "printed no JSON object"),
        (
            "pass",
            f"print('vale version {released.vale()}'); sys.exit(3)",
            "--version ended with status 3",
        ),
        ("time.sleep(5)", "pass", "did not end within 1 s"),
        ("pass", "time.sleep(5)", "did not end within 1 s"),
    ],
)
def test_an_abnormal_vale_run_is_a_refusal_in_one_line(tmp_path, monkeypatch, lint, version, said):
    if "sleep" in lint + version:
        monkeypatch.setattr(register, "_DEADLINE", 1)
    placed(monkeypatch, "你们先看。")
    stand_in(tmp_path, monkeypatch, lint, version)
    message = str(refused())
    assert said in message
    assert "\n" not in message


def test_alerts_are_read_under_any_key_and_a_file_that_is_no_program_refuses(tmp_path, monkeypatch):
    placed(monkeypatch, "你们先看。")
    vale = stand_in(tmp_path, monkeypatch, f"print(json.dumps({{'x': [{alert(1)}]}})); sys.exit(1)")
    assert refused_lines() == [f"zh 01.1: '你们' {ADDRESS}"]
    vale.write_text("not a program\n")
    assert str(refused()) == f"{vale} cannot run: Exec format error"


def test_the_checker_runs_alone_on_the_engines_configuration(tmp_path, monkeypatch):
    placed(monkeypatch, "先看。")
    vale = stand_in(
        tmp_path,
        monkeypatch,
        "open(sys.argv[0] + '.args', 'w').write(json.dumps(sys.argv[1:])); print('{}')",
    )
    register.check()
    # The configuration is the check's own file beside the module, named for the check.
    config = Path(register.__file__).with_name("register.ini")
    assert config.is_file()
    # It is INI to any reader, its settings under a section, and names the style folder the
    # check holds its rule files to.
    stated = configparser.ConfigParser(interpolation=None, strict=True)
    stated.read_string(config.read_text(encoding="utf-8"))
    style = config.parent / stated.defaults()["stylespath"] / stated["*.txt"]["basedonstyles"]
    assert (stated.sections(), style) == (["*.txt"], register._STYLE)
    # Each run applies one language's rules alone, by Vale's filter.
    arguments = json.loads(Path(f"{vale}.args").read_text())
    assert arguments[:4] == ["--no-global", f"--config={config}", "--ext=.txt", "--output=JSON"]
    filters = [
        "--filter=.Name in [" + ", ".join(f'"register.{rule}"' for rule in language.rules) + "]"
        for language in (languages.language("zh"), languages.language("en"))
    ]
    assert arguments[4:] in ([filters[0]], [filters[1]])


def test_the_text_reaches_the_checker_as_utf8_under_any_locale(tmp_path, monkeypatch):
    vale = stand_in(
        tmp_path,
        monkeypatch,
        "open(sys.argv[0] + '.text', 'wb').write(text); "
        f"print(json.dumps({{'stdin.txt': [{alert(1)}]}})); sys.exit(1)",
    )
    child = (
        "import sys, filmkit.concepts as c, filmkit.register as r\n"
        "c.places = lambda: {'zh': [c.Place('zh 01.1', '你们先看。')]}\n"
        "try:\n    r.check()\nexcept r.RegisterError as error:\n"
        "    sys.stdout.buffer.write(str(error).splitlines()[0].encode())\n"
    )
    environment = {
        "PATH": str(vale.parent),
        "HOME": os.environ["HOME"],
        "FILMKIT_ROOT": os.environ["FILMKIT_ROOT"],
        # The child imports the engine under test, not another installed copy.
        "PYTHONPATH": str(Path(register.__file__).parents[2]),
        "LC_ALL": "en_US.ISO8859-1",
        "LANG": "en_US.ISO8859-1",
    }
    ran = subprocess.run(
        [sys.executable, "-B", "-c", child],
        capture_output=True,
        env=environment,
        check=False,
        timeout=60,
    )
    assert ran.returncode == 0, ran.stderr.decode("utf-8", "replace")
    assert Path(f"{vale}.text").read_bytes() == "你们先看。\n".encode()
    assert ran.stdout.decode() == f"zh 01.1: '你们' {ADDRESS}"


def test_an_installed_engine_that_lost_a_rule_file_refuses_before_any_word_is_read(
    tmp_path, monkeypatch
):
    def unread():
        pytest.fail("the words were read")

    monkeypatch.setattr(concepts, "places", unread)
    # An installed layout, as a wheel lays it out: the package and its record side by side.
    shipped = Path(register.__file__).with_name("styles") / "register"
    site = tmp_path / "site"
    style = site / "filmkit/register/styles/register"
    shutil.copytree(shipped, style)
    record = site / "filmkit-0.0.0.dist-info"
    record.mkdir()
    (record / "METADATA").write_text("Metadata-Version: 2.4\nName: filmkit\nVersion: 0.0.0\n")
    rows = [
        f"filmkit/register/styles/register/{rule.name},sha256=x,1" for rule in shipped.glob("*.yml")
    ]
    (record / "RECORD").write_text("\n".join([*rows, "filmkit-0.0.0.dist-info/RECORD,,"]) + "\n")
    monkeypatch.syspath_prepend(str(site))
    monkeypatch.setattr(register, "_STYLE", style)
    (style / "marks.yml").unlink()
    (style / "colloquial.yml").unlink()
    assert str(refused()) == (
        f"The engine's register style at {style} lacks colloquial.yml, marks.yml, which the engine"
        " was installed with; install the engine again"
    )


def test_a_style_folder_without_rule_files_refuses_before_any_word_is_read(tmp_path, monkeypatch):
    def unread():
        pytest.fail("the words were read")

    monkeypatch.setattr(concepts, "places", unread)
    monkeypatch.setattr(register, "_STYLE", tmp_path)
    assert str(refused()) == (
        f"The engine's register style at {tmp_path} holds no rule file; install the engine again"
    )
    # An engine that lost its Vale configuration is refused by the file's name, before the style.
    lost = tmp_path / "register.ini"
    monkeypatch.setattr(register, "_CONFIG", lost)
    assert str(refused()) == (
        f"The engine's register configuration at {lost} is not there; install the engine again"
    )


def test_another_vale_on_the_path_refuses_before_any_word_is_read(tmp_path, monkeypatch):
    def unread():
        pytest.fail("the words were read")

    monkeypatch.setattr(concepts, "places", unread)
    other = tmp_path / "bin/vale"
    other.parent.mkdir()
    other.write_text(
        f"#!{sys.executable}\nimport pathlib, sys\n"
        "pathlib.Path(sys.argv[0]).with_name('calls').open('a').write(' '.join(sys.argv[1:]))\n"
        "print('vale version 9.9.9')\n"
    )
    other.chmod(0o755)
    monkeypatch.setenv("PATH", str(other.parent))
    runs = f"the register check runs Vale {released.vale()}, as this engine's release states"
    pin = f"mise use github:vale-cli/vale@{released.vale()}"
    assert str(refused()) == f"{other} reports Vale 9.9.9; {runs}: {pin}"
    assert (other.parent / "calls").read_text() == "--version"
    monkeypatch.setenv("PATH", str(tmp_path / "nothing"))
    # No Vale at all is a tool the host lacks: the check cannot finish, and refuses nothing.
    with pytest.raises(child_processes.MissingToolError) as missing:
        register.check()
    assert str(missing.value) == f"No vale on the path; {runs}"
