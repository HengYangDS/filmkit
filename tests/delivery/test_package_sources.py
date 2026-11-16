"""Each packaged film names the picture it shows and the picture file its encode read."""

import json

import pytest
import test_packaging

import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.verification as delivery_verification
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError

# The packaging tests' root, with FFmpeg and ExifTool simulated, under its own name.
packaging_root = test_packaging.packaging_root
CAPTIONED = "sample-reel-final-picture.mp4"
UNCAPTIONED = "sample-reel-final-picture-uncaptioned.mp4"


def sources(edition) -> list[tuple[str, str, str]]:
    package = json.loads(edition.film_package.read_text())
    return [(m["path"], m["picture"], m["source"]) for m in package["editions"]]


def test_a_rendered_pairs_films_each_read_the_picture_they_show(packaging_root):
    _, edition, _ = packaging_root
    delivery_packaging.package_film(edition)
    assert sources(edition) == [
        ("sample-reel-zh-uhd.mp4", "captioned", CAPTIONED),
        ("sample-reel-zh-1080p-captioned.mp4", "captioned", CAPTIONED),
        ("sample-reel-zh-uhd-uncaptioned.mp4", "uncaptioned", UNCAPTIONED),
        ("sample-reel-zh-1080p-uncaptioned.mp4", "uncaptioned", UNCAPTIONED),
    ]


def test_a_derived_pairs_1080p_uncaptioned_film_names_the_captioned_file_it_read(packaging_root):
    _, edition, calls = packaging_root
    derived = {"rows": [1872, 2048], "ground": {"y": 21, "u": 129, "v": 125}}
    receipt = {"picture": "uncaptioned", "derived": derived}
    repository.write(edition.rendered(captions=False).receipt, receipt)
    delivery_packaging.package_film(edition)
    assert sources(edition) == [
        ("sample-reel-zh-uhd.mp4", "captioned", CAPTIONED),
        ("sample-reel-zh-1080p-captioned.mp4", "captioned", CAPTIONED),
        ("sample-reel-zh-uhd-uncaptioned.mp4", "uncaptioned", UNCAPTIONED),
        ("sample-reel-zh-1080p-uncaptioned.mp4", "uncaptioned", CAPTIONED),
    ]
    # The record agrees with the command: that film's encode reads the captioned picture.
    encodes = [command for command, _ in calls if command[0] == "ffmpeg" and "-f" in command]
    read = [command[command.index("-i") + 1].rsplit("/", 1)[-1] for command in encodes]
    assert read == [CAPTIONED, CAPTIONED, UNCAPTIONED, CAPTIONED]


@pytest.mark.parametrize("source", [UNCAPTIONED, None])
def test_the_verifier_refuses_a_member_that_names_another_source(inputs, source):
    edition = inputs.edition
    package = repository.read(edition.film_package)
    assert all("source" in member for member in package["editions"])
    delivery_verification.verify_package(edition)
    package["editions"][0] = {**package["editions"][0], "source": source}
    repository.write(edition.film_package, package)
    with pytest.raises(VerificationError, match="Film package differs from its current inputs"):
        delivery_verification.verify_package(edition)
