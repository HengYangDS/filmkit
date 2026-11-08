## Context

`rules/balance.mjs` `reviewedRuns` joins each frame's full-size lit box into the reviewers' runs: build-ups more than 90 px off for 1.5 s or more, which `check-picture` refuses, and settled runs more than 50 px off for 2 s or more with both edges still within 4 px, which it only records. A settled run is left out when the next frame holds a wider box of the same scene that contains it. `measure-like-the-reviewers` (0.8.0) kept settled runs recorded because the measure cannot tell a finished composition from a build-up that waits for a part arriving another way, such as a name docking to a bar.

The essentials film's sixth review (ZH6-1) found 07.3's delegation stage at about 63 px left for 11 s. The engine left the run out: at 504.0 s the next stage, 07.4, cut in with a wider box of the same scene that contained the old one. The stage had not grown; a stage cut had replaced it. The reviewer's tool counts no frame within 0.5 s after a detected stage cut as growth, and finds this one run in the film.

## Goals / Non-Goals

**Goals:**

- Stop reading a stage cut as growth, so the audit reports what the reviewers report.
- Refuse a finished composition that stands off centre, since the reviews treat it as the rejected "off balance".

**Non-Goals:**

- Refusing the remaining settled runs. A state that ends in the same stage without a cut may still wait for a docking part, so those stay recorded.
- Changing the limits (90 px for 1.5 s, 50 px for 2 s, edges within 4 px) or the lit-box measure.

## Decisions

### 1. A stage cut ends growth

The composition declares its stage cuts per scene (`stageCuts`, read by `declaredCuts()`, which the motion audit already uses). The frame audit passes `reviewedRuns.frame` whether a declared cut of the frame's scene falls after the previous sample and at or before this one. After such a cut the frame never counts as grown from the run before it. The reviewer's tool detects cuts from the pictures, within 0.5 s; the declared cuts are exact, so no window is needed.

### 2. Finished runs are reported apart and refused

A settled run whose next frame shows another scene, or follows a stage cut of its scene, cannot be waiting for a part: its stage is gone. The audit reports it as `off_centre_finished`, with the same span and offset as `off_centre_settled`, and `check-picture` refuses it. A run is listed under one key only. The other settled runs, those ending at an edge that moves within the stage, at nothing lit or at the end of the film, stay recorded under `off_centre_settled`.

Alternative considered: keep one list and refuse every settled run. That would refuse the docking states 0.8.0 kept for review, and the ETHOS film's index waits so (English 52.3–54.4 s).

### 3. A scene change counts as replacement

The frame audit's scene is the timeline segment the frame falls in. When the next frame belongs to another segment and shows its picture, the previous segment's state has been replaced, as at a stage cut. A next frame with nothing lit ends the run as before, under `off_centre_settled`.

## Risks / Trade-offs

- [The stricter gate refuses stages the films now pass] → Each refusal is a stage the reviews would find off balance. The three films gate again under this release before their next render, and each refusal is repaired in its film.
- [`declaredCuts()` runs in the composition's context every frame] → It reads one map; the motion audit already does this per frame.

## Migration Plan

Release 0.16.0. Each film adopts it, stages and gates both editions, and repairs any finished run before it renders.
