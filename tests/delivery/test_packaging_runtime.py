"""Packaging a film of an odd number of seconds: its keyframe grid, its finished-film check and its
shot plan, all read from the runtime its edition's timeline states."""

import test_packaging

import filmkit.delivery.packaging as delivery_packaging
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification

packaging_root = test_packaging.packaging_root
keyed, RUNTIME = test_packaging.keyed, test_packaging.RUNTIME


def test_a_film_of_an_odd_number_of_seconds_holds_its_frames_and_a_last_half_group(
    packaging_root,
):
    _, edition, _ = packaging_root
    frames = RUNTIME * specification.FPS
    viewing = production.RENDITIONS["1080p-captioned"]
    grid = keyed(frames, 2 * specification.FPS)["keyframes"]
    # 88,620 frames, the last of the 739 groups of 120 frames half a group of 60.
    assert (frames, len(grid), frames - grid[-1]) == (88620, 739, 60)
    assert delivery_packaging.keyed_as_declared(viewing, grid, RUNTIME)
    assert not delivery_packaging.keyed_as_declared(viewing, [*grid, frames], RUNTIME)
    assert not delivery_packaging.keyed_as_declared(viewing, grid, 1476)
    delivery_packaging.check_delivered_film(edition.film("1080p-captioned"), edition, viewing)


def test_the_shot_plan_states_the_runtime_of_its_timeline(packaging_root):
    root, edition, _ = packaging_root
    scene = {"id": "01", "title": "Sources", "text": "先看数据。", "source_sections": []}
    script = {**repository.read(edition.script), "segments": [scene]}
    repository.write(root / edition.script, script)
    (root / delivery_packaging.COMPOSITION_SCRIPT).parent.mkdir(parents=True)
    (root / delivery_packaging.COMPOSITION_SCRIPT).write_text("/* film */")
    times = {"start": 0.0, "end": 1474.0, "voice_start": 2.0, "voice_end": 9.0}
    timeline = {
        "duration": RUNTIME,
        "fps": specification.FPS,
        "segments": [{**scene, **times, "gap_kind": "opening"}],
        "captions": [],
    }
    repository.write(edition.timeline, timeline)
    delivery_packaging.refresh_shot_plan(edition, timeline)
    plan = repository.read(edition.shot_plan)
    assert (plan["duration"], plan["fps"]) == (1477, 60)
