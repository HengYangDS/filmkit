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
# The name of an edition's captioned picture's stage below the work folder, which the uncaptioned
# picture's extends.
STAGE = "final-delivery-{code}-uhd"


@dataclass(frozen=True)
class Rendition:
    """A delivered film: its frame size, whether and how it re-encodes its picture, and which
    picture it carries.

    `decoding` holds the FFmpeg options before the picture input and `video` those of the video
    stream. A rendition that re-encodes may declare `keyframe_seconds`: its film then holds a
    keyframe at every that many seconds of frames from the first and at no other frame, which
    packaging asks of the encoder by its interval, the interval's minimum and no scene cuts; one
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


# The 1080p viewing film's encoder and its settings: x264, whose keyframes stand where its
# options put them. VideoToolbox, which encoded these films before, left the declared grid six
# times between 13 and 17 November 2026 under this host's load, for a cause never found, each
# time ending a build. Measured on 17 November 2026 on a film's span of 7,200 frames against its
# area-scaled source, as seconds, megabytes, and decibels on average and at the lowest frame:
# VideoToolbox at 10 Mbit/s 23.7 s, 23.9 MB, 63.4 and 51.8 dB; x264 veryfast at rate factor 16,
# 7.8 s, 4.8 MB, 56.4 and 48.7 dB; at 14, 7.4 s, 5.7 MB, 58.2 and 50.3 dB; at 12, 8.1 s, 6.7 MB,
# 59.8 and 51.8 dB; at 10, 9.5 s, 7.8 MB, 61.4 and 53.3 dB; faster and medium at 14, 11.4 and
# 11.9 s, 51.3 and 51.5 dB at the lowest frame. The rate factor is the highest whose lowest frame
# stands clear of VideoToolbox's: 12 meets it by 0.01 dB on that one span, which is no margin,
# and 10 stands 1.5 dB over it for 1.4 s more a span. Those encodes held x264's default B-frames.
# The films hold none, as every film delivered before held none and no player was tried on a
# stream that reorders its frames: on the span's first 1,800 frames at rate factor 10 and two
# threads, 5.1 s either way, 2.9 MB without them against 2.0 MB with them, 61.6 against 61.1 dB
# on average and 56.7 against 53.4 dB at the lowest frame.
VIEWING_ENCODER = "libx264"
VIEWING_PRESET = "veryfast"
VIEWING_RATE_FACTOR = 10
# The two sizes a film is delivered at: the UHD master and the 1080p viewing film, whose encode
# scales the picture to its frame.
UHD = Rendition(3840, 2160, reencoded=False)
VIEWING_SIZE = (1920, 1080)
VIEWING = Rendition(
    *VIEWING_SIZE,
    reencoded=True,
    video=(
        "-filter:v:0",
        "scale=w={}:h={}:flags=area".format(*VIEWING_SIZE),
        "-c:v:0",
        VIEWING_ENCODER,
        "-preset:v:0",
        VIEWING_PRESET,
        "-crf:v:0",
        str(VIEWING_RATE_FACTOR),
        "-bf:v:0",
        "0",
        "-pix_fmt:v:0",
        "yuv420p",
    ),
    deadline_ratio=2,
    keyframe_seconds=2,
)
# Each edition's delivered films by kind: at each size, one with the captions the picture draws
# and one without them. The UHD films copy their picture's stream. The 1080p viewing films
# re-encode it: decoded in software, averaged over each 2x2 block of pixels, which neither rings
# nor lifts a white, and encoded by x264 with a keyframe forced every 2 s. The two films of a
# size are made alike, each from its own picture, but for the 1080p uncaptioned film of a pair
# whose uncaptioned picture is derived: its encode reads the captioned picture and paints the
# caption band as the derivation did (`filmkit.picture.derivation.film_source`).
RENDITIONS = {
    "uhd": UHD,
    "1080p-captioned": VIEWING,
    "uhd-uncaptioned": replace(UHD, captions=False),
    "1080p-uncaptioned": replace(VIEWING, captions=False),
}


# What a picture's stage holds by name: the page that the renderer draws and the browser checks
# paint, and the record that binds the stage to its inputs (`filmkit.picture.rendering`). The
# engine's Node modules read the same names from `picture/stage-contract.mjs`.
STAGE_PAGE = "index.html"
STAGE_RECORD = "stage.json"


@dataclass(frozen=True)
class Rendered:
    """One of an edition's two pictures and its places: its stage, with the page it holds, its
    file and its receipt.

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

    @property
    def page(self) -> Path:
        """The page the stage holds, which the renderer draws."""
        return self.stage / STAGE_PAGE


def review_report(record: Path) -> Path:
    """The report of a review record: beside it and under its name, as Markdown. A round writes
    the copy there, the verifier reads it there and a release publishes it from there, wherever
    the record lies."""
    return record.with_suffix(".md")


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
        return repository.ROOT / repository.ARTIFACTS / self.code

    @property
    def evidence(self) -> Path:
        return repository.ROOT / repository.EVIDENCE / self.code

    def rendered(self, captions: bool = True) -> Rendered:
        """The captioned picture's places, or with `captions` False the uncaptioned one's."""
        suffix = "" if captions else "-uncaptioned"
        return Rendered(
            captions,
            repository.ROOT / "build/runtime/work" / (STAGE.format(code=self.code) + suffix),
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

    # The documents the edition delivers beside its films, which the captions' writer writes
    # from the timeline (`filmkit.captions.documents.subtitle_files`).
    @property
    def srt(self) -> Path:
        """The captions as SRT."""
        return self.artifacts / f"{self.prefix}.srt"

    @property
    def vtt(self) -> Path:
        """The captions as WebVTT, whose cues the player's track embeds."""
        return self.artifacts / f"{self.prefix}.vtt"

    @property
    def transcript(self) -> Path:
        """The transcript, as Markdown."""
        return self.artifacts / f"{self.prefix}-transcript.md"

    @property
    def chapters(self) -> Path:
        """The chapters, as JSON."""
        return self.artifacts / "chapters.json"

    @property
    def chapter_metadata(self) -> Path:
        """The chapters as FFmetadata, which packaging maps into every film."""
        return self.artifacts / "chapters.ffmeta"

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
    def renderer_qualification(self) -> Path:
        """The record that two renders of the captioned stage decode to the same frames
        (`filmkit.picture.qualification`)."""
        return self.evidence / "renderer-qualification.json"

    @property
    def picture_geometry(self) -> Path:
        return self.evidence / "picture-geometry.json"

    @property
    def sound_gates(self) -> Path:
        """The record of the measures that check-sound took on the assembled soundtrack."""
        return self.evidence / "sound-gates.json"

    @property
    def picture_gates(self) -> Path:
        """The record of the audits that check-picture ran on the current picture."""
        return self.evidence / "picture-gates.json"

    @property
    def readiness(self) -> Path:
        """The receipt of the pre-render check, bound to the inputs it judged
        (`filmkit.preflight`)."""
        return self.evidence / "readiness.json"

    @property
    def draft_stills(self) -> Path:
        """The still scan of the edition's 10 fps draft, bound to its timeline and composition."""
        return self.evidence / "draft-stills.json"

    @property
    def film_stills(self) -> Path:
        """The still scan of the edition's 1080p captioned film, bound to that film, the timeline
        and the composition (`filmkit.picture.still_scan.scan_film`)."""
        return self.evidence / "film-stills.json"

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
