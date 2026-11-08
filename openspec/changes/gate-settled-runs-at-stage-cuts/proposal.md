## Why

The essentials film's sixth production review found its delegation stage standing about 63 px left of centre for 11 s (ZH6-1, material: the owner's rejected "off balance"). `check-picture` had passed it. The reviewers' rule allows a settled composition more than 50 px off for less than 2 s, and the frame audit measures that rule, but it excuses a still state when the next frame holds a wider box of the same scene that contains it, reading the picture as grown from it. Here the next frame was the next stage, which replaced the state at a stage cut. The reviewer's own tool, which does not count a frame after a stage cut as growth, finds this one run. The audit also only records settled runs, because a still state may be a build-up that waits for a part docking to it; a state that a stage cut or another scene replaces waits for nothing.

## What Changes

- A frame that follows a stage cut the composition declares for its scene no longer counts as growth from the state before it.
- A settled run whose next frame shows another scene, or follows a stage cut of its scene, is a finished composition. The frame audit reports it as `off_centre_finished` instead of `off_centre_settled`, with its span and largest offset.
- `check-picture` refuses `off_centre_finished`, as it refuses `off_centre_builds`, and still records the other `off_centre_settled` runs.
- This breaks a composition with a finished stage that stands more than 50 px off for 2 s or more. The essentials film's 07.3 is one, and it is repaired in that film.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `picture-gates`: settled runs stop at stage cuts, and finished compositions off centre refuse.

## Impact

`src/filmkit/picture/rules/balance.mjs` (`reviewedRuns`), `frame-audit/composition.mjs`, `frame-audit.mjs` and `frame-audit/report.mjs` (the new report key), `picture/gates.py` (the gated key), their tests, the README's balance paragraph and the release notes. The films gate again under the release before their next render.
