## Context

The [proposal](proposal.md) names the four steps and the [specs](specs) their behaviour. Each step exists today as a lane script that drives filmkit 0.19.0's internals:

- `build/runtime/work/picture/draft.py`, byte-identical in the three film lanes: `rendering.stage_picture(Edition(code), stage, DURATION, 1920, 1080)` into `build/runtime/work/picture-draft/<code>/`, the renderer under `nice -n 10` with `--fps 10 --quality draft --workers 8 --gpu --browser-gpu --no-low-memory-mode --experimental-fast-capture --strict` and a 3600 s deadline through `rendering.run_renderer`, then `python -m filmkit.picture.still_scan <draft> --language <code>` in a subprocess.
- `dryfit.py` in the ETHOS lane: `assembly.assemble` copied up to `allocate_designed_gaps`, through the module's private functions, with each variant's fields merged into the script's `voice_performance`.
- `render/chain20.sh`: compare, parse the refusal's text with a regular expression, keep the named picture, render it again, compare again, at most twice per picture, and render both pictures once for a difference no one picture holds.

`render_picture` builds its renderer command inline with `--experimental-fast-capture`. HyperFrames 0.9.9 reads that flag into `PRODUCER_EXPERIMENTAL_FAST_CAPTURE` (`render-7HIEI7QP.js`, about line 532), and with the variable set to `true` it keeps drawElement capture on for parallel capture, which it otherwise turns off because that path "has no runtime self-verification" (`chunk-2NGBIAUF.js`, about line 13515). Leaving the flag out lets the caller's environment and the renderer's own defaults decide.

## Goals / Non-Goals

**Goals:** carry the four steps natively with the lanes' settings; keep every existing film's output bytes; give each behaviour one owner, so that the dry run and the assembly, and the draft and the picture renders, cannot drift apart.

**Non-Goals:** changing the default capture; HyperFrames 0.9.33; keeping the renderer's captured frames (54 to 108 GB per picture, inferred); rendering part of a picture; the recorded craft measures; orchestrating whole production runs.

## Decisions

### 1. One renderer command and one receipt for every render

`rendering.renderer_command(stage, output, fps, quality)` returns the command that `render_picture` runs today, with the capture flag of the declared mode in the place where `--experimental-fast-capture` stands now, and `rendering.record_render(...)` runs it through `run_renderer` and writes the receipt. Each quality brings its encoding: `looks` with `--crf 14`, as the pictures render, and `draft` alone, as the lanes' `draft.py` renders. `render_picture` keeps its checks and calls both; `render_draft` calls both with 10 fps and `--quality draft`. A film that declares no capture therefore runs the same command, element for element, which a test pins against the 0.19.0 list.

### 2. The capture mode is declared, explicit and recorded

`film.Picture.capture` is `Literal["fast", "screenshot", "software"]`, default `fast`; `extra="forbid"` already refuses an unknown key, and pydantic names `picture.capture` for another value. Each mode is a browser flag and a capture flag (`rendering.CAPTURE_FLAGS`): `fast` passes `--browser-gpu` and `--experimental-fast-capture`, `screenshot` `--browser-gpu` and `--experimental-fast-capture=false`, and `software` `--no-browser-gpu` and `--experimental-fast-capture=false`, so the browser draws in its software rasterizer (SwiftShader) and the frames are captured by screenshot. Every flag is explicit, so the mode depends neither on the caller's environment, which `renderer_environment` passes on, nor on HyperFrames' defaults for the host and worker count. The receipt gains `capture`. Validation reads a receipt's mode from its capture flag and its browser flag, a command without a browser flag drawing in the host's GPU, requires a recorded `capture` to agree with it, and refuses a mode other than the declared one; a 0.19.0 receipt carries both flags and records no key, so it validates for a film that declares nothing. Both pictures of an edition are validated before `compare-pictures`, so they share one mode.

`software` comes from a capture A/B on 2026-11-12 (task 6.7). The DDWG film's Chinese captioned composition of its n6f build, 90,000 UHD frames, rendered with the host's GPU held 5 one-frame glyph faults with fast capture and 9 with screenshot capture, each a box 2 to 16 px wide whose samples sat 92 to 213 levels off their neighbouring frames, so the capture API is not their cause. Rendered twice in the software rasterizer with screenshot capture, the two pictures differed at no frame, with no fault, in 894 and 1,027 s against 767 s for the GPU's screenshot capture on the same host. The faults have been found only in Chinese pictures (5 of 7 Chinese comparisons since 0.19.0 refused, none of the 2 English ones), which hold many more distinct glyphs; the GPU's glyph rasterization is the inferred cause.

Alternatives: a per-run option or environment variable leaves no trace in the film's sources, so a rebuild could not reproduce the picture; switching the default to `software` now would change every film's bytes, so each film declares it in its next edition, and a later release may move the default once the films render with it.

### 3. `render-draft`: the draft beside the pictures, the scan in process

`filmkit.picture.draft.render_draft(edition, deadline)` removes its own stage `build/runtime/work/picture-draft/<code>/` and draft `build/runtime/work/picture-draft/<code>.mp4`, the lanes' places, and the edition's earlier draft record and receipt, so that a refused draft leaves no record for `preflight`, stages the captioned picture there at 1920x1080 over the whole duration, renders under `nice` (the command's first three elements) at niceness 10, or the caller's if higher, with a default deadline of 3600 s, and writes its receipt to `build/evidence/editions/<code>/render/receipt-draft.json`, beside the pictures' receipts, with `picture` set to `draft`. The still scan's judging and record writing move from `still_scan.main` into `still_scan.record_draft(edition, movie, limit)`, which `main --language` and `render_draft` both call, so the record lands at `Edition.draft_stills` by one writer. A `StillScanError` and a scan over the limit refuse as `PictureError`.

`render-draft` does not require a passing gate record, as the lanes' script does not: a draft is how a film looks at its picture before the gates pass, and `preflight` refuses a missing gate record before the final render anyway.

Alternatives: a `--draft` option of `render-picture` would mix a 10 fps 1080p draft into the places, receipts and validation of the delivered pictures; keeping the scan as a second command is the arrangement that failed on 2026-11-11.

### 4. `fit`: the assembly's own steps, stopped at the allocation

`assemble` is split, in its present order, into shared functions of `soundtrack.assembly`: `bound_recordings` (today's `_bound_inputs`), `decode_recordings` (the decode loop and its work files), `designed_clips` (shaping, boundary measures, thought-pause targets and clips) and `allocate` (kinds, designed bases, runtime and `allocate_designed_gaps`). `assemble` keeps its abrupt-take refusal before decoding, its chapter gains before the allocation and everything after it; its soundtrack, timeline and receipt stay byte-identical, which the two-chapter fixture's hashes prove.

`filmkit.soundtrack.fit.fit(edition, variants)` validates the script's policy and every variant with `designed_pause_policy` before decoding, decodes once, and runs `designed_clips` and `allocate` for each policy on copies of the decoded samples. It prints one JSON line per policy, the script's first as `declared`: `speech_seconds`, `gap_seconds` (the designed gaps before the allocation), `closing_seconds`, `free_seconds` (negative when missing), `gaps` (the allocated gaps as the assembly receipt records them, or `null` where the allocation refuses) and `verdict`, `fits` or the allocation's own message; the first four are the values `dryfit.py` reports. A policy whose clips or gaps cannot be designed, as `assemble` would refuse them for a pause, a level or a recording, is reported with that refusal as its verdict and no measures, so a variant that fails so never ends the run. It refuses with that message when the declared policy does not fit. A variant replaces whole top-level fields of `voice_performance`, as the lanes' files do, so the policy's rule that `designed_pauses` names every kind keeps holding, and a field that `designed_pause_policy` does not read is refused, naming the variant and the field, as a mistyped field would change nothing. `--variants` names a file below the film's root or an absolute one, as the engine names every other file and as the README's commands, run at the film's root, imply. `fit` judges no take: abrupt endings, pauses and terms stay with `assemble`. It writes no record; the printed lines are its result.

Alternatives: a mirror of the assembly, as in `dryfit.py`, reaches into its private functions and drifts as soon as the assembly changes how it shapes, trims or releases a clip; assembling into a scratch copy writes the timeline, soundtrack and receipt and runs the level and speech gates; predicting from receipts without decoding misses the shaping of each recording's inner pauses.

### 5. `repair-pictures`: the record decides, the owners act

`faults.repairable(record, code)` reads the record's fields, never its text, and returns the named pictures with their faults, or refuses naming why: composition instants that differ, sampled frames beyond noise, lasting runs, a fault without a picture above the residue ceiling, or more one-frame differences (`fault_frames`) than the record lists with a picture. A fault outside the caption band that lands on a sampled frame fails that frame's measures too, so a sampled frame beyond noise counts as part of such a fault when it is that fault's frame and every other sampled frame passes; any other sampled failure, and one the record does not list, stays refused. `filmkit.picture.repair.repair_pictures(edition, attempts, deadline)` then:

1. requires the record to bind the current pictures and inputs (`equivalence.current_bindings`), and returns without rendering when it passed;
2. checks each named picture's current stage and passing gate record, the checks `render_picture` makes, before it moves anything;
3. for each attempt, creates `build/evidence/editions/<code>/picture-repairs/<n>/` with `n` one above the highest ASCII number present, copies the refused `caption-equivalence.json` there, moves each named picture and its receipt there, renders each named picture with `render_picture`, runs `compare_pictures`, and writes `attempt.json` with the faults, each kept file's SHA-256, the new receipts and the comparison's verdict and findings; a render or comparison that fails is recorded there instead, with its error and the receipts so far, and refused naming the folder and the commands that bring the edition back, `render-picture` for each picture not rendered again and then `compare-pictures`;
4. stops at the first passing comparison, refuses a later comparison that `repairable` does not accept and one whose faults remain after the last attempt, each refusal naming the attempts made and where they are kept.

A picture is moved rather than copied: on one volume a move costs no space or time, and the render writes a new file. The kept pictures stay below the edition's evidence rather than in `build/artifacts/film/superseded/`: a faulty render is evidence of a fault, not a reproducible artifact, and `set-aside`'s superseded folder belongs to whole reviewed builds. `--attempts` (2 by default, the lanes' limit, at least 1) bounds one run; a later run continues the numbering. A difference that no one picture holds is refused rather than rendered in both pictures, as the lanes' chain did once: no render fault measured so far was of that kind, and a guessed render is what the 2026-11-09 incident cost. Its refusal names the next step, rendering both pictures again with `render-picture`. When `faults.repairable` accepts a refused comparison, `compare-pictures` names `repair-pictures` as the next step in its refusal, so the refusal and the repair cannot disagree.

Alternatives: a loop inside `compare-pictures` would make a judgement schedule renders; reading the refusal's text, as the lanes do, breaks when a message changes; keeping the renderer's captured frames to tell capture from encoding is left for when disk allows it.

### 6. The command line

`produce` gains `fit` after `select`, `render-draft` after `check-picture` and `repair-pictures` after `compare-pictures`. `--variants` applies only to `fit` and `--attempts` only to `repair-pictures`, refused elsewhere as `--uncaptioned` is; `--deadline` defaults to each owner's own (10800 s for a picture, 3600 s for a draft).

## Risks / Trade-offs

- [Screenshot capture is slower] → HyperFrames' help calls fast capture about twice as fast; a film chooses, and the A/B measures it before any default moves.
- [The receipt records the requested mode] → HyperFrames may still fall back from drawElement to screenshot capture by itself for a composition it cannot capture; the receipt states what the engine asked for, not what each frame used.
- [Kept pictures fill the disk] → each attempt keeps a few hundred MB per picture; the attempt folders are evidence with a named consumer, the capture A/B and an upstream report, and are removed with the lane's build when that consumer releases them.
- [A refused render leaves the edition without a picture] → the preconditions are checked before the move, and the kept picture stays in its attempt folder; `repair-pictures` cannot start again without a comparison of current pictures, so the attempt's record keeps the error and the receipts so far, and the refusal names the folder and the commands that bring the edition back: `render-picture` for each picture not rendered again, then `compare-pictures`.
- [`fit` and `assemble` share the decode work files] → both decode the selected recordings into `build/runtime/work/audio-assembly/<edition>/<segment>-source.wav`, so they must not run at once on one edition; a film runs them in turn, as its tasks do.

## Migration Plan

Release as 0.20.0. A film adopts it at its next build and retires its `draft.py`, `dryfit.py` and the repair loop of its chain; nothing it has rendered, assembled or packaged changes. Rollback pins 0.19.0, after removing a declared `capture`, which 0.19.0 refuses as an unknown field.

## Open Questions

None. The lead's answers of 2026-11-11 are folded in above: the kept pictures stay below the edition's evidence; the acceptance compares `fit` with `dryfit.py` on a copy of the ETHOS lane's Chinese assembly inputs, and the unit tests cover a 0.10 s overrun, whose 2026-11-06 inputs were not kept; and `compare-pictures` names `repair-pictures` where it can answer the refusal.
