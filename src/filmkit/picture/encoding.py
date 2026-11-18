"""How an edition's two pictures are encoded: one definition for the renderer and the derivation.

A rendered picture (`filmkit.picture.renderer`) and a derived one (`filmkit.picture.derivation`)
are both x264 with a keyframe forced every KEYFRAME_SECONDS, none at a scene cut, and no
B-frames, so that a derived picture is the stream its rendered twin would be and the UHD films
copy either.

On a span of 7,200 UHD frames, with the band painted by colour and x264's default B-frames, the
encode took 20.7 s at rate factor 14, 21.0 s at 12 and 22.8 s at 10, where a browser's render
took 126 to 141 s, and stood above the band 59.5, 60.7 and 61.7 dB on average from that picture,
52.1, 53.5 and 52.6 dB at the lowest frame (17 November 2026). Rate factor 12 is a decibel
closer than 14 in the same time. No film delivered before held a B-frame, the rendered pictures
hold none, and no player was tried on a stream that reorders its frames, so no picture holds
one: on that span's first 1,800 frames at rate factor 12 and two threads, 12.2 s and 5.1 MB
without them against 14.2 s and 3.7 MB with them, 60.0 against 59.9 dB on average and 55.4
against 53.1 dB at the lowest frame.
"""

from __future__ import annotations

KEYFRAME_SECONDS = 2
RATE_FACTOR = 12


def encoder(fps: int) -> tuple[str, ...]:
    """FFmpeg's options for a picture's video stream at a frame rate."""
    group = str(KEYFRAME_SECONDS * fps)
    return (
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        str(RATE_FACTOR),
        "-g",
        group,
        "-keyint_min",
        group,
        "-sc_threshold",
        "0",
        "-bf",
        "0",
        "-pix_fmt",
        "yuv420p",
    )
