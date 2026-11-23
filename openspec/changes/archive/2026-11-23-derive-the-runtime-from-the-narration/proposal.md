## Why

On 23 November 2026 the films session decided that each December edition lasts as long as its settled narration at its designed pauses, rounded up to the whole second and counted by the engine's own count: never pitch or time stretching, never an approved text changed for time, never a pause outside its declared range [S1]. The engine cannot hold that rule today. Each script declares `duration` (1500, 600 and 900 s in the three films), the engine refuses a film whose two editions declare different values, and the assembly fits the narration into that number: it shares whatever the narration leaves among the gaps, and refuses a narration that runs over [S2]. With one narrator for every film, the full film's Chinese edition runs about 136 s over its 1500 s while its English edition leaves about 25 s free [S1]. A runtime stated beside the narration is a second statement of a fact the narration already decides (the owner's C-2), and today a person would have to write it into both scripts at every build.

## What Changes

- **An edition's runtime is its narration's length, in whole seconds.** The assembly makes each edition's runtime the credits plus the speech with its designed thought pauses, the designed gaps and the closing quiet, counted in samples and rounded up to the next whole second; the runtime is always a whole number of seconds. The fraction the rounding leaves goes first to the gaps by their declared weights, each gap capped at the top of its declared range (an opening or chapter gap at its declared limit); what the gaps cannot take goes to the credits, which hold no pause [S5]. No thought pause or closing quiet changes, and no gap leaves its range.
- **The timeline states the runtime, and every step reads it there.** The assembly writes the runtime as the timeline's `duration`, the field every composition and Node tool already reads, and the credits as laid out as the timeline's `credits_duration`. Staging, rendering, the draft, the caption documents and chapters, packaging, verification, the player page, the entry page, the player check and the review prompts take each edition's runtime, and the credits' start, from that edition's timeline.
- **The two editions may differ in length.** Where a page or a check covers both, each edition keeps its own runtime: each language link on the entry page shows its edition's, the player check plays each edition's films against their own, and each review prompt states its own edition's.
- **BREAKING: a script declares neither `duration` nor `credits_duration`.** The credits' length is declared once, in the film's declaration (`content/film.toml`), since both editions draw one composition. The engine refuses at load a script that still declares either key, with one line that names the script and the key and says to remove it, or to move the credits to the declaration, and a declaration that omits `credits_duration`, with one line that says to declare it there; it never defaults the credits. The decision's follow-up had called the script's `duration` "a stated check, not the source"; the decision's owner answered on 23 November 2026 that it is removed (C-2) [S5].
- **`filmkit.adoption` names what this release asks a film to remove or reword:** a script's `duration` or `credits_duration`, a cast's `runtime_fit`, and a line of the review prompt that cites the runtime without saying "This edition". A declaration without `credits_duration` is one finding, of the existing `declaration` question.
- **`produce fit` reports the runtime.** For the script's pause policy and for each variant it reports the runtime the assembly would give, the seconds of the fraction the gaps take and the seconds the credits take. It refuses only where the pause design refuses; "Narration exceeds the runtime" and "Narration is short by … for the declared gap limits" can no longer occur.
- **BREAKING: the convergence counts a settled edition and can no longer report it as missing its runtime.** Until now its record's `fit` said `fits` or `misses` against the declared runtime, and for a miss the command exited 1 and named the largest thought pause under which the edition would fit. Now the record's `fit` states the runtime the count gives, with the verdict `fits`, `refused` or `failed`. The verdict `misses`, its lever (`thought_pause_to_fit`) and the cast's `runtime_fit.reserve_seconds` are removed, and the convergence refuses a cast that still declares `runtime_fit` before its first effect.
- **BREAKING for a delivery's records:** the player check's binding and the delivery's readback receipt name each edition's runtime by its code, where they named one `duration` for the film.

Released editions keep their tag's engine and are not rebuilt: the three films pin `v0.22.3`. A film adopts this release with its December editions, in its own lane.

Out of scope: a ceiling or a target for any runtime; any change to a take's speed or pitch; the films' texts and pause policies; moving the scripts' other film-wide values (author, frame rate, chapter count) to the declaration, deferred in the design; the selection over the whole edition that the draft `let-narration-converge` describes, whose decision 3 loses its purpose here (see the design's Migration Plan).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `runtime-fit`: an edition's runtime is derived from its narration, in whole seconds; the fraction goes to the gaps within their ranges, then to the credits; every step reads the runtime and the credits from the edition's timeline; the dry run reports the runtime it would give.
- `film-engine`: a script declares no duration and no credits; the declaration states the credits once; the two editions may differ in length.
- `narration-convergence`: a settled edition is counted for its runtime; the miss, its lever and the reserve are removed.
- `build-time`: a scenario that named a convergence missing its runtime names one that the assembly refuses.
- `engine-distribution`: the adoption command names what a film's scripts, casts and review prompt state of the runtime and the credits that this release removes or asks to reword.

## Impact

- Code: `src/filmkit/soundtrack/assembly.py`, `soundtrack/pauses.py`, `soundtrack/fit.py`, `narration/fitting.py`, `narration/converge.py`, `specification.py`, `film.py`, `adoption.py`, `production.py`, `produce.py`; `picture/rendering.py`, `draft.py`, `equivalence.py`, `derivation.py`, `still_scan.py`; `captions/documents.py`; `delivery/packaging.py`, `verification.py`, `player.py`, `folder.py`, `player-check.mjs`, `player-read.mjs`; `review/prompts.py`. `research.md` lists every reader with its lines at 0.27.0; the design says how it is rebased, and its Sources where `research.md` is kept.
- Tests: the 25 Python test files that read or patch the engine's `DURATION`, and those that model a fixed runtime or the old binding (`tests/fit_bench.py`, `tests/narration/converging.py`, `tests/soundtrack/test_pauses.py`, `tests/delivery/player-receipt.test.mjs`, `tests/picture/test_still_record.py`); the tasks name each.
- The sample film: its scripts lose `"duration": 60` and `"credits_duration": 3`; its declaration gains `credits_duration = 3`; its review prompt says "This edition: exactly {duration} s"; its runtime becomes its narration's.
- A film that adopts this release, in its own December lane: removes `duration` and `credits_duration` from both scripts and declares `credits_duration` once in `content/film.toml`; removes `runtime_fit` from a cast that declares it (none does today); rewords "Each edition: exactly {duration} s" in its review prompt to "This edition". Its compositions (`film.duration - film.credits_duration`), its picture template's `data-duration` anchor and its entry page's two `/*RUNTIME*/` anchors need no change.
- Records: the timeline and the assembly receipt keep `duration`, now derived and whole; the timeline's `credits_duration` is the credits as laid out, in seconds as a number with a fraction where it held the script's integer; the convergence's `fit` gains `runtime_seconds` and loses `reserve_seconds`, `missing_seconds` and `pause`; the player binding and the delivery receipt give each edition's runtime by its code.
- Drafts: decision 3 of `let-narration-converge` and decision 8 of `faster-films-less-by-hand` lose their purpose; this Change edits neither.

Owner: the engine's maintainer.

## Sources

Numbered as in the design.

- **[S1]** `build/evidence/unified-voices-2026-11-23/fit-decision.md` in the engine's repository, read whole on 23 November 2026.
- **[S2]** The engine at `dev` `6d59ad6`, read on 23 November 2026: `src/filmkit/specification.py:15-22,34`, `src/filmkit/soundtrack/assembly.py:379-392`, `src/filmkit/soundtrack/pauses.py:434-480`.
- **[S5]** The films session's answers and rulings on this draft, 23 November 2026, given as the decision's owner under the owner's delegation D-28 and relayed by the coordinator; see the design's Sources for what they settle and where they are to be recorded.
