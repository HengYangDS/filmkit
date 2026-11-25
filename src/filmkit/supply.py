"""Install the browser build, the dictionary and the speech models the engine pins, below the
tool cache.

The supply is the only build step that reaches the network. The locked @puppeteer/browsers installs
the browser build that the picture's and the players' checks run; the pinned CMUdict, which a
judgment of an English edition reads (`filmkit.narration.cmudict`), is downloaded from its
repository at its commit, checked for its size and SHA-256 and only then moved into its place; and
huggingface_hub downloads each pinned model snapshot, from the mirror that HF_ENDPOINT names when it
is set. Each is checked against its pinned digests, so the build that follows reads only checked
inputs and runs offline. Installing again keeps what is already in place: a dictionary whose bytes
hold the pin is not downloaded again, wherever it came from. A download that fails is refused in
one line, which names the file and its place.

Run by `filmkit supply` (`supply`).
"""

from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

from huggingface_hub import snapshot_download

import filmkit.narration.cmudict as cmudict
import filmkit.picture.browser as picture_browser
import filmkit.repository as repository
from filmkit.narration.snapshots import ALIGNER, RECOGNIZER, VOICE, SnapshotError

# The locked browser installer, below the film's npm packages.
BROWSER_INSTALLER = Path(".bin/browsers")
# The model snapshots the narration loads, in the order they are supplied.
SNAPSHOTS = (VOICE, RECOGNIZER, ALIGNER)
# Seconds one installer or download may take.
DEADLINE = 3600


class SupplyError(ValueError):
    """A supplied tool or model differs from its pin."""


def supply_browser() -> dict:
    """Install the pinned browser build and check its executable's SHA-256."""
    product, version = picture_browser.BROWSER
    folder = repository.ROOT / picture_browser.TOOL_CACHE / "browsers"
    installer = [
        str(repository.node_modules() / BROWSER_INSTALLER),
        "install",
        f"{product}@{version}",
    ]
    repository.run([*installer, "--path", str(folder)], timeout=DEADLINE)
    executable = picture_browser.supplied_browser()
    if not executable.is_file() or repository.sha(executable) != picture_browser.BROWSER_SHA256:
        msg = f"The {product}@{version} browser build differs from the pinned SHA-256"
        raise SupplyError(msg)
    return {"build": f"{product}@{version}", "executable": repository.relative(executable)}


def fetch(url: str, place: Path, *, deadline: int) -> None:
    """Download a URL's bytes into a file."""
    with urllib.request.urlopen(url, timeout=deadline) as response, place.open("wb") as stream:
        shutil.copyfileobj(response, stream)


def supply_dictionary() -> dict:
    """Place the pinned CMUdict, downloaded and checked beside its place and moved there only
    once its size and SHA-256 are the pin's; a file in place that holds the pin is kept."""
    place = repository.ROOT / cmudict.PLACE
    said = {"url": cmudict.URL, "file": cmudict.PLACE, "bytes": cmudict.BYTES}
    said["sha256"] = cmudict.SHA256
    if place.is_file() and repository.sha(place) == cmudict.SHA256:
        return {**said, "kept": True}
    place.parent.mkdir(parents=True, exist_ok=True)
    partial = place.with_name(f".{place.name}.{os.getpid()}.partial")
    try:
        try:
            fetch(cmudict.URL, partial, deadline=DEADLINE)
        except OSError as error:
            msg = (
                f"The CMUdict could not be downloaded from {cmudict.URL} to {cmudict.PLACE}: "
                + " ".join(str(error).split())
            )
            raise SupplyError(msg) from None
        if partial.stat().st_size != cmudict.BYTES or repository.sha(partial) != cmudict.SHA256:
            msg = f"The CMUdict downloaded from {cmudict.URL} differs from the pinned SHA-256"
            raise SupplyError(msg)
        partial.replace(place)
    finally:
        partial.unlink(missing_ok=True)
    return {**said, "kept": False}


def supply_models() -> list[dict]:
    """Download each pinned model snapshot into its folder and check its weights."""
    models = []
    for snapshot in SNAPSHOTS:
        snapshot_download(
            snapshot.repo,
            revision=snapshot.revision,
            allow_patterns=list(snapshot.files),
            local_dir=repository.ROOT / snapshot.folder,
        )
        try:
            snapshot.verify()
        except SnapshotError as error:
            raise SupplyError(str(error)) from None
        models.append(
            {"repo": snapshot.repo, "revision": snapshot.revision, "folder": snapshot.folder}
        )
    return models


def supply() -> dict:
    """Supply the browser build, the dictionary and the models, each checked: the report of
    what each is and where it stands (`filmkit supply`)."""
    report = {"browser": supply_browser(), "dictionary": supply_dictionary()}
    report["models"] = supply_models()
    return report


if __name__ == "__main__":
    from filmkit.retired import refuse

    refuse(__spec__.name)
