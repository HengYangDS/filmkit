"""A stand-in chain for the tests of the plan and of `verify`: nodes that read and write small
files below a scratch root, declared as the engine's table declares its own, and run through the
seam as the film's chain runs its commands."""

import os
import time

import filmkit.repository as repository
from filmkit.graph import nodes, opens, runs
from filmkit.production import Edition

CODES = ("zh", "en")


def stand_in(name, reads, writes, expected="light"):
    """A node that reads and writes files below the root, each by its name; `{code}` in a file
    names the edition's own."""

    def places(files):
        return lambda e: {n: repository.ROOT / f.format(code=e.code) for n, f in files.items()}

    return nodes.Node(name, {"default": places(reads)}, places(writes), expected)


TABLE = (
    stand_in("assemble", {"script": "{code}/script.txt"}, {"timeline": "{code}/timeline.json"}),
    stand_in(
        "refresh-captions",
        {"script": "{code}/script.txt", "timeline": "{code}/timeline.json"},
        {"timeline": "{code}/timeline.json", "srt": "{code}/captions.srt"},
    ),
    stand_in("check-sound", {"timeline": "{code}/timeline.json"}, {"gate": "{code}/gate.json"}),
    stand_in("package-metadata", {"gate": "{code}/gate.json"}, {"page": "page.html"}),
    stand_in("stage", {"script": "{code}/script.txt"}, {"stage": "{code}/stage.txt"}),
    stand_in("render", {"stage": "{code}/stage.txt"}, {"picture": "{code}/picture"}, "heavy"),
    stand_in("compare", {"picture": "{code}/picture"}, {"compared": "{code}/compared.json"}),
    stand_in("narrate", {"script": "{code}/script.txt"}, {"takes": "{code}/takes.txt"}, "gpu"),
)
SHARED = {
    "timeline": (
        nodes.Writer("assemble", nodes.REPLACES),
        nodes.Writer("refresh-captions", nodes.REWRITES, ("assemble",)),
    ),
    "page": (nodes.Writer("package-metadata", nodes.REPLACES),),
}
# A chain whose assemble reads the selection that refresh-captions rewrites after select and
# assemble, as the engine's table has it: a reader that a rewriter follows (design decision 5).
SELECTING = (
    stand_in("select", {"script": "{code}/script.txt"}, {"selected": "{code}/selected.txt"}),
    stand_in("assemble", {"selected": "{code}/selected.txt"}, {"timeline": "{code}/timeline.json"}),
    stand_in(
        "refresh-captions",
        {"selected": "{code}/selected.txt", "timeline": "{code}/timeline.json"},
        {"timeline": "{code}/timeline.json", "selected": "{code}/selected.txt"},
    ),
)
SELECTING_SHARED = {
    "timeline": SHARED["timeline"],
    "selected": (
        nodes.Writer("select", nodes.REPLACES),
        nodes.Writer("refresh-captions", nodes.REWRITES, ("select", "assemble")),
    ),
}
# What each stand-in command writes: refresh-captions rewrites the timeline as it read it.
WRITES = {
    "assemble": lambda root, code: {
        "timeline": "timeline of "
        + (maybe(root, f"{code}/selected.txt") or read(root, f"{code}/script.txt"))
    },
    "refresh-captions": lambda root, code: {
        "timeline": read(root, f"{code}/timeline.json"),
        "srt": "captions",
        "selected": maybe(root, f"{code}/selected.txt"),
    },
    "check-sound": lambda root, code: {"gate": "gate of " + read(root, f"{code}/timeline.json")},
    "package-metadata": lambda root, code: {"page": f"page of {code}"},
    "stage": lambda root, code: {"stage": "stage of " + read(root, f"{code}/script.txt")},
    "render": lambda root, code: {"picture": "picture of " + read(root, f"{code}/stage.txt")},
    "compare": lambda root, code: {"compared": "pass for " + read(root, f"{code}/picture")},
    "narrate": lambda root, code: {"takes": "takes of " + read(root, f"{code}/script.txt")},
    "select": lambda root, code: {"selected": "selected of " + read(root, f"{code}/script.txt")},
}


def read(root, name):
    return (root / name).read_text()


def maybe(root, name):
    """A file's text where it stands, else nothing: the selection, which not every table has."""
    return read(root, name) if (root / name).is_file() else ""


def scratch(root):
    """A film root of both editions' scripts, whose node table is the stand-in one; the table."""
    for code in CODES:
        (root / code).mkdir()
        (root / code / "script.txt").write_text(f"the {code} script")
    return nodes.load(TABLE, SHARED, CODES)


def ran(name, code="zh", *, refuse=None, whole=True):
    """Run a stand-in command as the chain runs it, after the last one has ended."""
    time.sleep(0.005)
    with runs.run(code, name, whole=whole):
        if refuse:
            raise SystemExit(refuse)
        wrote(name, code)


def run_stand(root, block=lambda run: None, **options):
    """Run the one stand-in node of `conftest.one_node` through the seam: it sets a setting,
    writes out.txt in a phase `work`, then runs `block` with the run."""
    with runs.run("zh", "stand", **options) as run:
        run.settings["count"] = 2
        with run.phase("work"):
            (root / "out.txt").write_text("out")
            # A run that records nothing opens no node's run.
            expected = "stand:zh" if options.get("record", True) else None
            assert os.environ.get(opens.NODE) == expected
        block(run)


def wrote(name, code):
    """What a stand-in command writes, each output from what it read."""
    node = runs.table()[name]
    written = WRITES[name](repository.ROOT, code)
    for output, path in node.outputs(Edition(code)).items():
        path.write_text(written[output])


def chain(*codes):
    for code in codes or ("zh",):
        for name in ("assemble", "refresh-captions", "check-sound"):
            ran(name, code)


def selecting(monkeypatch):
    """Load the chain that selects (`SELECTING`) in place of the stand-in one; the table."""
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in SELECTING})
    return nodes.load(SELECTING, SELECTING_SHARED, CODES)
