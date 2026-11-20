## Why

A narration that `converge` has settled can still miss the film's runtime: each thought takes the candidate with the widest margin, and nothing counts the edition. On the essentials film's English edition with the reference the owner chose, the settled edition misses by 2.75 s of 600 s, and the command exits 0; the miss is met one step later, when `produce assemble` refuses [S2]. The person who runs the film then asks `produce fit` with variants written by hand to find a pause that fits.

The draft `let-narration-converge` answers the miss with a selection over the whole edition (its decision 3). That selection was built, reviewed four times and shelved on 19 November 2026 [S1]. One part of it stands without the rest and was never in question: the convergence asking the assembly's own count, and naming the film's own lever for a miss.

## What Changes

- **A settled edition is counted.** When its rounds end with no thought refused, `converge` selects the edition's recordings and counts them under the script's pause policy, by the functions that `produce select` and `produce fit` run. The record's `fit` states the seconds free.
- **A miss is named with its lever.** For an edition that misses, the command exits 1 with one line: the seconds missing, and the largest thought pause of the script's declared range under which the edition would fit, or that no pause of that range fits. The pause is named and not applied: the pause policy is the film's.
- **A refusal of the count is the edition's.** What the selection or the assembly refuses for another reason than the runtime ends the command with that reason in one line, after the record is ended.
- **A reserve may be declared.** A cast may declare `runtime_fit.reserve_seconds`, the seconds that must stay free; without it an edition fits when the allocation accepts it.
- **`filmkit.soundtrack.fit` gives its reports to a caller.** `asked` returns what `produce fit` prints, without printing or refusing, and `thought_pause_to_fit` reads the lever. `produce fit` prints and refuses as before.

**BREAKING** for a film's scripts in one case: `converge` exits 1 for a settled edition that misses its runtime or that the selection or the assembly refuses, where it exited 0 before. Such an edition was refused by `produce select` or `produce assemble` already.

Nothing replaces a take, and the command gets no new option.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `narration-convergence`: a settled edition is asked whether it fits its runtime; the record holds the answer; the command's exit for a miss and for a refusal of the count.

## Impact

- `src/filmkit/soundtrack/fit.py` (`asked`, `REFUSALS`, `thought_pause_to_fit`), a new `src/filmkit/narration/fitting.py`, and `src/filmkit/narration/converge.py`. Their tests: `tests/soundtrack/test_fit.py`, `tests/narration/test_converge_fit.py`.
- A film: a script that runs `converge` and goes on by its exit now stops at a miss. A cast may declare the reserve; nothing must change.
- The record `convergence.json` gains `fit`. A record of an earlier engine has none, and nothing reads it there.
- Out of scope: any replacement of a take for the runtime, a budget of takes, the pause design, and the draft's other decisions.

Owner: the engine's maintainer.

## Sources

- **[S1]** `build/evidence/let-narration-converge/selection-shelved/`: `review-selection.md`, `reverify-selection.md`, `review-selection-3.md` and `final-check.md`, the four independent reviews of the shelved selection, 18 and 19 November 2026; read in part on 19 November 2026 (see the design's Sources).
- **[S2]** `build/evidence/let-narration-converge/voice-v4/report.md`, read on 19 November 2026: `produce fit` on the settled edition, free −2.75 s of 600 s; the essentials film at `v1.0.2`, the engine at `b1d5ec1`.
