"""What tests of several folders share of the still scan. A draft's record as the scan writes
it, for the tests that need one standing without a scan, in the scan's whole shape. And the
scan's own requirement, for a test that asks it where a fixture stands in for it."""

import filmkit.picture.renderer as renderer
import filmkit.picture.rendering as rendering
import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository

# What the engine's renderer names itself as in a draft's receipt and record.
DREW = {
    "package": renderer.RENDERER_NAME,
    "version": renderer.RENDERER_VERSION,
    "text_renderer": renderer.TEXT_RENDERER,
}
# The scan's own requirement as the engine defines it. A folder's fixtures may replace it by one
# that passes; a test that asks the requirement itself puts this one back. It is read when a
# test module imports this one, which is before any fixture runs.
REQUIRE_FILM_SCAN = still_scan.require_film_scan


def draft_stills(edition, runs=()) -> dict:
    """The record of a draft that the engine's renderer drew and the scan read whole, against the
    edition's timeline and the composition as they stand, with `runs` as the fine measure's
    still runs."""
    frames = still_scan.film_frames(edition)
    paths = (edition.timeline, repository.ROOT / rendering.COMPOSITION_SCRIPT)
    bound = {
        name: {"path": repository.relative(path), "sha256": repository.sha(path)}
        for name, path in zip(still_scan.SUBJECTS[1:], paths, strict=True)
    }
    report = {
        "fps": still_scan.FPS,
        "frames": frames[0],
        "fine": {"rule": still_scan.FINE_RULE, "runs": list(runs)},
        "coarse": {"rule": still_scan.COARSE_RULE, "runs": []},
        "longest_fine_speech": max((run["speech"] for run in runs), default=0),
        "phases": len(frames),
        "phase_frames": frames,
    }
    stated = {
        "rules": still_scan.rules(),
        "limit_seconds": still_scan.LIMIT_SECONDS,
        "over_limit": still_scan.over_limit(report),
    }
    movie = {"path": "build/runtime/work/picture-draft/draft.mp4", "sha256": "0" * 64}
    return {"movie": movie, **bound, **report, **stated, "drawn_by": DREW}
