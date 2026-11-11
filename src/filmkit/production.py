"""Each language edition's sources and the places of its media and evidence.

Every action takes the edition it produces as an argument; nothing holds a current edition.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.film import FILM

if TYPE_CHECKING:
    from pathlib import Path


# The language editions, Chinese first.
CODES = ("zh", "en")


@dataclass(frozen=True)
class Rendition:
    """A delivered film: its frame size, whether and how it re-encodes its picture, and which
    picture it carries.

    `decoding` holds the FFmpeg options before the picture input and `video` those of the video
    stream. A rendition that re-encodes may declare `keyframe_seconds`: its film then holds a
    keyframe at every that many seconds of frames from the first and at no other frame; one
    that declares none keeps the keyframes of the stream it copies. Packaging allows the encode
    `deadline_ratio` seconds per second of film, and never less than its own floor. `captions`
    names the picture: the one that draws the captions, or the uncaptioned one.
    """

    width: int
    height: int
    reencoded: bool
    decoding: tuple[str, ...] = ()
    video: tuple[str, ...] = ("-c:v:0", "copy")
    deadline_ratio: int = 0
    captions: bool = True
    keyframe_seconds: int | None = None


# The two sizes a film is delivered at: the UHD master and the 1080p viewing film.
UHD = Rendition(3840, 2160, reencoded=False)
VIEWING = Rendition(
    1920,
    1080,
    reencoded=True,
    decoding=("-hwaccel", "videotoolbox"),
    video=(
        "-filter:v:0",
        "scale=w=1920:h=1080:flags=area",
        "-c:v:0",
        "h264_videotoolbox",
        "-b:v:0",
        "10M",
    ),
    deadline_ratio=2,
    keyframe_seconds=2,
)
# Each edition's delivered films by kind: at each size, one with the captions the picture draws
# and one without them. The UHD films copy their rendered picture's stream. The 1080p viewing
# films re-encode it: decoded through VideoToolbox, averaged over each 2x2 block of pixels, which
# neither rings nor lifts a white as VideoToolbox's own scaler does, and encoded through
# VideoToolbox with a keyframe every 2 s. The two films of a size are made alike from their own
# pictures.
RENDITIONS = {
    "uhd": UHD,
    "1080p-captioned": VIEWING,
    "uhd-uncaptioned": replace(UHD, captions=False),
    "1080p-uncaptioned": replace(VIEWING, captions=False),
}


@dataclass(frozen=True)
class Rendered:
    """One of an edition's two pictures and its places: its stage, its file and its receipt.

    The captioned picture draws the timeline's captions; the uncaptioned one is staged from the
    same composition and timeline with no captions, and is otherwise the same picture.
    """

    captions: bool
    stage: Path
    file: Path
    receipt: Path

    @property
    def name(self) -> str:
        """The picture as its stage record, receipt and package name it."""
        return "captioned" if self.captions else "uncaptioned"


@dataclass(frozen=True)
class Edition:
    """Keep language-specific source, timing, media and evidence together."""

    code: str

    def __post_init__(self) -> None:
        if self.code not in CODES:
            message = "An edition must be zh or en"
            raise ValueError(message)

    @property
    def language(self) -> str:
        return "Chinese" if self.code == "zh" else "English"

    @property
    def sources(self) -> str:
        """The folder of the edition's script, cast and narration mirror."""
        return FILM.editions[self.code].sources

    @property
    def script(self) -> str:
        return f"{self.sources}/film-script.json"

    @property
    def cast(self) -> str:
        return f"{self.sources}/voice-reference.json"

    @property
    def shot_plan(self) -> Path:
        """The shot plan that packaging writes from the script, composition and timeline."""
        return self.evidence / "shot-plan.json"

    @property
    def mirror(self) -> str:
        """The narration text, which equals the script's segment texts joined by blank lines."""
        return f"{self.sources}/narration.md"

    @property
    def cover(self) -> str:
        return FILM.editions[self.code].cover

    @property
    def artifacts(self) -> Path:
        return repository.ROOT / "build/artifacts/film" / self.code

    @property
    def evidence(self) -> Path:
        return repository.ROOT / "build/evidence/editions" / self.code

    def rendered(self, captions: bool = True) -> Rendered:
        """The captioned picture's places, or with `captions` False the uncaptioned one's."""
        suffix = "" if captions else "-uncaptioned"
        return Rendered(
            captions,
            repository.ROOT / "build/runtime/work" / f"final-delivery-{self.code}-uhd{suffix}",
            self.artifacts / f"{FILM.slug}-final-picture{suffix}.mp4",
            self.evidence / f"render/receipt{suffix}.json",
        )

    @property
    def picture_stage(self) -> Path:
        """The captioned picture's stage."""
        return self.rendered().stage

    @property
    def prefix(self) -> str:
        return f"{FILM.slug}-{self.code}"

    @property
    def timeline(self) -> Path:
        """The assembled timeline: segment times, thought pauses, words and captions."""
        return self.artifacts / "timeline.json"

    @property
    def soundtrack(self) -> Path:
        """The assembled narration at program level, the films' only audio."""
        return self.artifacts / f"{self.prefix}-narration.wav"

    @property
    def picture(self) -> Path:
        """The rendered captioned picture, before the soundtrack, cover and metadata join it."""
        return self.rendered().file

    def film(self, kind: str) -> Path:
        """A delivered film by its kind in `RENDITIONS`."""
        return self.artifacts / f"{self.prefix}-{kind}.mp4"

    @property
    def films(self) -> list[Path]:
        """The delivered films in `RENDITIONS` order: the UHD master and the viewing film, each
        with its captions drawn, then the same two without captions."""
        return [self.film(kind) for kind in RENDITIONS]

    @property
    def ear_first(self) -> Path:
        """The narration's recordings and their receipt, alignment and transcript."""
        return self.evidence / "ear-first"

    @property
    def narration_selected(self) -> Path:
        return self.evidence / "narration-selected.json"

    @property
    def alignment_selected(self) -> Path:
        return self.evidence / "alignment-selected.json"

    @property
    def audio_assembly(self) -> Path:
        return self.evidence / "audio-assembly.json"

    @property
    def render_receipt(self) -> Path:
        """The captioned picture's render receipt."""
        return self.rendered().receipt

    @property
    def caption_equivalence(self) -> Path:
        """The record that the uncaptioned picture differs from the captioned one only by its
        captions (`filmkit.picture.equivalence`)."""
        return self.evidence / "caption-equivalence.json"

    @property
    def picture_geometry(self) -> Path:
        return self.evidence / "picture-geometry.json"

    @property
    def picture_sync(self) -> Path:
        return self.evidence / "picture-sync.json"

    @property
    def picture_gates(self) -> Path:
        """The record of the audits that check-picture ran on the current picture."""
        return self.evidence / "picture-gates.json"

    @property
    def draft_stills(self) -> Path:
        """The still scan of the edition's 10 fps draft, bound to its timeline and composition."""
        return self.evidence / "draft-stills.json"

    @property
    def draft_stage(self) -> Path:
        """The stage of the edition's 10 fps draft (`filmkit.picture.draft`)."""
        return repository.ROOT / "build/runtime/work/picture-draft" / self.code

    @property
    def draft_picture(self) -> Path:
        """The edition's 10 fps draft, beside its stage."""
        return self.draft_stage.with_name(f"{self.code}.mp4")

    @property
    def draft_receipt(self) -> Path:
        """The render receipt of the edition's draft, beside its pictures' receipts."""
        return self.evidence / "render/receipt-draft.json"

    @property
    def picture_repairs(self) -> Path:
        """The numbered attempts of `filmkit.picture.repair`, each holding the pictures it found
        faulty and rendered again."""
        return self.evidence / "picture-repairs"

    @property
    def film_package(self) -> Path:
        return self.evidence / "film-package.json"

    @property
    def viewing_package(self) -> Path:
        return self.evidence / "viewing-package.json"

    @property
    def production_review(self) -> Path:
        """The production review record, beside its report, that the film verifier reads."""
        return self.evidence / "production-review.json"

    @property
    def release(self) -> dict:
        """The release metadata the edition's script declares for its films."""
        return repository.read(self.script)["release"]

    @property
    def comment(self) -> str:
        return self.release["comment"]

    @property
    def description(self) -> str:
        return self.release["description"]
