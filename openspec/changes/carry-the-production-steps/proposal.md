## Why

Four production steps that every film needs still live in each film lane's own scripts, and each has cost a chain. The three lanes carry one byte-identical `build/runtime/work/picture/draft.py` to render the 10 fps draft and scan its stills, and on 2026-11-11 a chain failed its pre-render check at 14:01 because a copy wrote the draft record where `preflight` does not read it. A narration that overruns the film's runtime is first seen when `assemble` refuses it ("exceeds the runtime by 0.10 s" on 2026-11-06), so the lanes mirror the assembly in `dryfit.py` to try pause policies first. The renderer's capture is fixed in the engine at `--experimental-fast-capture`, although HyperFrames 0.9.9 itself turns its default-on drawElement capture off for parallel capture because it has no runtime self-verification, and all nine one-frame faults found since 2026-11-09 came from such renders; no film can choose another capture to test it. And since 0.19.0 `compare-pictures` names the picture that holds a one-frame fault, but the lanes render it again with hand-written loops (`chain20.sh`); on 2026-11-09, before the attribution existed, a refusal was answered by a guess and the essentials film's uncaptioned picture was rendered twice and refused twice.

## What Changes

- `produce render-draft --language zh|en` stages the edition's captioned picture afresh at 1920x1080, renders it at 10 fps in draft quality under `nice`, records a draft render receipt, and runs the still scan, whose record lands at the edition's draft record (`build/evidence/editions/<code>/draft-stills.json`), the record `preflight` reads. It refuses a render that does not complete and a draft with a still picture over the limit.
- `produce fit --language zh|en [--variants <file>]` runs the edition's assembly up to and including the designed-gap allocation without writing anything but the assembly's decode work files, and prints, for the script's pause policy and for each declared variant, the speech, the designed gaps, the closing quiet and the runtime left free or missing. It refuses when the script's own policy does not fit, with the refusal `assemble` would give. The assembly and the dry run share one code path.
- `content/film.toml` may declare `[picture] capture = "fast"` or `"screenshot"`. `"fast"`, the default, keeps today's renderer command; `"screenshot"` passes `--experimental-fast-capture=false` in its place, so HyperFrames captures each frame with `Page.captureScreenshot`. `render-picture` and `render-draft` honour it, every render receipt records the mode, and validation refuses a picture rendered in another mode than the film declares. The declaration offers the choice; whether screenshot capture avoids the faults is not shown by this change.
- `produce repair-pictures --language zh|en [--attempts <n>]` starts from a current refused `compare-pictures` record whose only findings are one-frame faults that each name their picture. For each attempt, at most `--attempts` (2), it keeps every named picture, its receipt and the refused record as evidence, renders only the named pictures again and compares again. It refuses any other finding, a difference that no one picture holds and a fault that remains after the last attempt, and records every attempt. A refusal of `compare-pictures` that `repair-pictures` can answer names it as the next step.

No existing film's output bytes change: a film that declares no capture renders with the same command as under 0.19.0, the assembly writes the same soundtrack, timeline and receipt, and the new commands write only new files.

## Capabilities

### New Capabilities

- `runtime-fit`: the dry run of an edition's assembly up to the gap allocation, under its pause policy and declared variants.

### Modified Capabilities

- `render-preflight`: a native command renders and scans the draft whose record the pre-render check reads.
- `film-engine`: a film declares how its picture is captured, and each render receipt records it.
- `caption-equivalence`: a native step renders again only the pictures that hold attributed one-frame faults, within an attempt limit, keeping the faulty pictures as evidence.
- `sample-film`: the sample film's picture task renders each edition's draft and passes the pre-render check before it renders.

## Impact

- `src/filmkit/produce.py` (three actions and their options), `src/filmkit/film.py` (`picture.capture`), `src/filmkit/production.py` (the draft's and the repairs' places), `src/filmkit/picture/rendering.py` (one renderer command and receipt for every render), a new `src/filmkit/picture/draft.py`, `src/filmkit/picture/still_scan.py` (the scan callable without a subprocess), a new `src/filmkit/picture/repair.py` with the attribution read in `src/filmkit/picture/faults.py` and the refusal's next step in `src/filmkit/picture/equivalence.py`, `src/filmkit/soundtrack/assembly.py` (the shared design and allocation) and a new `src/filmkit/soundtrack/fit.py`, and their tests.
- The sample film's picture task in `.config/mise/config.toml`; `README.md`, `CHANGELOG.md` and `VERSION` 0.20.0.
- The lanes retire `draft.py`, `dryfit.py` and the repair loop of their render chains when they adopt 0.20.0; a render receipt written by 0.19.0 stays valid for a film that declares no capture.
- Out of scope: the cause of the one-frame faults, the capture A/B and the move to HyperFrames 0.9.33 (0.21.0), keeping the renderer's captured frames, rendering a span of a picture again, and the recorded craft measures that the roadmap also places in 0.20.0, which a change of their own carries.
