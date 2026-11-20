## Context

`python -m filmkit.narration.converge` settles each thought and exits 0 when no thought is refused (`src/filmkit/narration/converge.py` at `a620a57`). Whether the settled edition fits the runtime is counted by the assembly: `produce select` binds the recordings (`narration/selection.py`), and `produce fit` counts them under the script's pause policy and each variant (`soundtrack/fit.py`), up to the gap allocation, which refuses an edition whose speech, designed gaps and closing quiet exceed the runtime (`soundtrack/pauses.py`, `allocate_designed_gaps`).

The selection that would close a miss by replacing takes was shelved on 19 November 2026 after four independent reviews and three repairs [S1]. A pass of it changed the edition in four places, the tracked cast, the receipt, the selection's records and the convergence's record, and was made safe by a guard at every reader of the edition; the final check still found a reader without the guard and a state the guard could not see, because the readers of an edition are not a closed set [S1]. A next attempt works in a copy of the edition's narration state, and the edition adopts the result whole, by one rename, only once it was counted as fitting.

This Change keeps the part that changes nothing: the asking and the wording of a miss.

## Goals / Non-Goals

**Goals:**

- `converge` says whether a settled edition fits, by the assembly's own count.
- A miss names the seconds and the film's own lever in one line; the record states the same.
- The asking is a reading: no take replaced, no pause policy changed, no tracked file written, nothing kept between runs.

**Non-Goals:**

- Closing a miss. The film's owner changes the thought pause, the text or the film's length.
- A selection over the edition, a budget of takes, a mark in the cast, a guard at a reader.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **The count asked is the assembly's own, through the functions the two commands run.**
   - **Rests on:** `produce select` and `produce fit` are the only owners of what a selection and a count are [S3]. The shelved slice's first form held an estimate of its own beside the count, and its first review found the two apart [S1].
   - **Considered:** (a) an estimate from the takes' kept speech, without a selection; (b) `select` and then `soundtrack.fit.asked`, the reports of `produce fit` without its printing and its exit.
   - **Chosen because:** (b). The answer is then what `produce fit` would print, and the files written are the ones those two commands write: the selection's two records and the decode work files.
   - **Applies to:** `narration/fitting.py`, `soundtrack/fit.py`.
   - **Reopened when:** the assembly's count changes its steps; the reading follows it, since it calls it.
   - **Sources:** [S1] [S3].
2. **The count is compared as counted and rounded only where it is printed.**
   - **Rests on:** the allocation counts whole samples and refuses a miss of one sample. The shelved slice rounded the free seconds before it compared them: a miss of one sample was said as a refusal for another reason, and a miss under 5 ms as "0.00 s" [S1].
   - **Considered:** (a) rounding to the record's places first; (b) the unrounded figure in the record and in every comparison, and a printed figure that takes as many places as a value that is not zero needs.
   - **Chosen because:** (b): no figure decides that was not counted, and no miss is printed as no seconds.
   - **Applies to:** `fitting.read`, `fitting.seconds`, and `thought_pause_to_fit`, which returns the pause as it was counted and the seconds free unrounded.
   - **Reopened when:** not applicable.
   - **Sources:** [S1], the first review's L3 and L5.
3. **The lever named is the thought pause, read by steps inside the declared range.**
   - **Rests on:** on the one edition measured, the miss of 2.75 s is closed by a thought pause of 2.00 s for the declared 2.12 s, inside the film's range of 1.7 to 2.9 s, read there by variants written by hand [S2]. The pause policy is the film's declaration.
   - **Considered:** (a) no lever, the seconds alone; (b) the thought pause, in steps of 0.01 s up from the range's least value to the declared pause, the largest step with room found by halving, each step counted by the assembly on recordings decoded once; (c) other levers too: the paragraph pause, the caps.
   - **Chosen because:** (b). It is the lever the measurement used, one figure a person can try at once, and it costs one count a step tried. The steps begin at the range's own least value: a grid of hundredths from zero tried a pause below a range whose least value lies off it [S1]. A result that does not fit states the pause tried last, the seconds it still misses or the refusal of its design, apart, so that a missed reserve is never worded as a refusal. A step whose design is refused leaves no count and is taken as room, so the halving can end on a refused step; the steps under it are then counted one by one, down to the first that fits, so that a refusal between two pauses that fit hides none. Where none fits, that look below costs one count for each step down to the range's least value, beside the halving's counts.
   - **Applies to:** `soundtrack.fit.thought_pause_to_fit`.
   - **Reopened when:** a film's miss is closed by another lever more often than by this one; halving assumes that a shorter thought pause never leaves less free, and a count that breaks this reopens the search.
   - **Sources:** [S1], the first review's L6; [S2].
4. **The pause is named and never applied; the command's exit says the miss.**
   - **Rests on:** the constraint that the draft states for the selection, kept here: the pause policy is the film's to decide and not the engine's [S4].
   - **Considered:** (a) exit 0 with a warning; (b) exit 1 with one line for a settled edition that misses, and for one that the selection or the assembly refuses otherwise.
   - **Chosen because:** (b). An exit of 0 says that the edition is ready for the assembly, which then refuses it. The changed exit is stated as breaking in the proposal, the README and the changelog.
   - **Applies to:** `converge.main`, `fitting.said`.
   - **Reopened when:** a selection exists that closes a miss; the exit then follows what that selection leaves.
   - **Sources:** [S2] [S4].
5. **A refusal of the count is answered, and the record is ended first.**
   - **Rests on:** the second review found that the binding and the decoding raised past the asking and left the record `running` [S1].
   - **Considered:** (a) the selection's refusal alone; (b) every refusal that `produce` names for these owners (`fit.REFUSALS`, which `produce.REFUSALS` is built from), and what reading a file or running the decoder fails with (`OSError`, `subprocess.SubprocessError`, and `wave.Error` and `EOFError` for a recording that is no WAV).
   - **Chosen because:** (b): the command ends in one line whatever the count refuses, and the record of an ended run says `ended`. A selection's refusal of several lines is joined into one, and a character that is not printable is a blank in it. A fault that is no refusal, such as a record that lacks a segment, keeps its traceback, as in `produce`; the record is ended first, with the fit `failed` and the fault's words, since the thoughts are settled whatever the count does. An `OSError` that names no file by an absolute path is the host's and such a fault too: running a decoder that is not installed raises for the command's bare name. One that names a file by an absolute path, below the film's root or outside it, is the edition's refusal in the system's words (both held by tests). A decode that fails stays the edition's refusal whatever its cause, a full disk or a decoder that is killed among them, said with the last line FFmpeg wrote as its error. A count under the reserve is said as a miss also where the allocation refuses the edition: the miss line then holds both, the seconds missing and the allocation's refusal at the largest pause that leaves the reserve free, where `refused` would say the refusal alone.
   - **Applies to:** `fitting.read`, `fitting.pause_to_fit`.
   - **Reopened when:** an owner of the count gains a refusal of another kind; `fit.REFUSALS` names the set.
   - **Sources:** [S1], the second review's N-L7; [S3].
6. **Nothing is kept between runs.**
   - **Rests on:** what the shelved slice remembered between runs was where its reviews found most of their faults [S1].
   - **Considered:** (a) the former run's fit kept in the running record; (b) the running record holds no fit, and every run selects and counts again.
   - **Chosen because:** (b). A count costs seconds; a run that is killed while it counts leaves a record that says `running` and no fit, and the next run asks again. What a kill leaves on disk is what a kill of `produce select` or `produce fit` leaves: the selection's records, each written whole, possibly one of a former selection beside one of this, which the next selection writes again and which the assembly's binding refuses meanwhile; and decode work files, which the next decode overwrites.
   - **Applies to:** `converge.begin`, `converge.write_record`.
   - **Reopened when:** a count takes long enough on a film to be worth keeping; it is then kept bound to the digests of what was counted.
   - **Sources:** [S1] [S3].
7. **The reserve is one declaration in the cast, and 0 without it.**
   - **Rests on:** the engine at `a620a57` declares no reserve [S3]; the allocation accepts an edition with no sample free.
   - **Considered:** (a) no reserve; (b) `runtime_fit.reserve_seconds` in the edition's cast, a number of seconds from 0, read and refused before the run's first effect; (c) an option of the command.
   - **Chosen because:** (b). A film that wants room for the next text change declares it where its edition's other narration declarations stand, and the lever named leaves that room. An option would be a figure kept by hand outside the film. The shelved slice's other field of that declaration, the share by which a take may be shorter, is not taken.
   - **Applies to:** `fitting.declared`.
   - **Reopened when:** a film declares one reserve for both editions; it then moves to the film's declaration.
   - **Sources:** [S3].
8. **An edition that declares nothing to count is not asked, and the record says why.**
   - **Rests on:** `converge` judges a film whose script names no pause contract, though the assembly refuses such a film (`narration/judgment.py`, `held`) [S3]; `select` requires the cast's performance recording.
   - **Considered:** (a) the selection's refusal as the edition's for such a film, exit 1; (b) not asked, with the reason in the record and in the command's report, and the exit as before.
   - **Chosen because:** (b). Such an edition is not declared for the assembly yet; refusing it would end every judging run of a film in preparation. With a thought unsettled the count is not asked either: the edition is not the one that would be assembled.
   - **Applies to:** `fitting.read`, `converge.converge`.
   - **Reopened when:** a film is found to have shipped a miss because its cast declared no performance recording.
   - **Sources:** [S3].
9. **A pause policy that the assembly refuses is refused before the run's first effect.**
   - **Rests on:** at `a620a57` the judgment validates the script's pause policy while it loads (`judgment.held`), outside any handler: a script that declares no `thought_pause_range` ends `converge` in a traceback after a narration may have run [S3]. Found while this Change's attack on an undeclared range was written.
   - **Considered:** (a) leave it; (b) validate the policy where the reserve is read and refuse in one line.
   - **Chosen because:** (b): the reading of the range is this Change's, and its absence must be a refusal, not a traceback.
   - **Applies to:** `fitting.declared`.
   - **Reopened when:** not applicable.
   - **Sources:** [S3].

## Risks / Trade-offs

- A film's script that ran `converge` and went on by its exit now stops at a miss. → Stated as breaking; the edition was refused one step later before.
- The count adds a selection and a decode to every settling run. → On the essentials film's English edition the count was read in 4.7 s and the lever in 21.7 s without a model, as the second review cites from the shelved slice's reading [S1]; not measured again on this tree. That lever was read by halving alone: where a step is refused and none under it fits, the look below adds one count a step down to the range's least value, which was not measured.
- The lever is read only up to the declared pause and only for the thought pause. → The line says the range; other levers stay `produce fit --variants`.

## Open Questions

- What the count and the lever cost on the DDWG film (the longest of the three). Not measured.
- Whether the pause named for the essentials film's English edition is heard as the film's. Asked of that edition as settled with the chosen reference, the command names a thought pause of 2.04 s, declared at 2.12 s in a range from 1.7 to 2.9 s, under which the edition fits with 0.29 s free, and changes nothing [S5]; variants written by hand had fitted at 2.00 s with 1.81 s free [S2]. Whether the film narrated with that pause is heard as the film's is the film's and the owner's to say.

## Sources

Read on 19 November 2026 unless a date is given. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The four independent reviews of the shelved selection:** `build/evidence/let-narration-converge/selection-shelved/review-selection.md` (first review, 18 November 2026; read: L3, L5, L6 and its list of what the reviewer did not run), `reverify-selection.md` (second; read: N-L7 and the timing it cites from the shelved slice's reading, T7), `review-selection-3.md` (third; read: the lines on N-L7's repair) and `final-check.md` (19 November 2026, 06:57 to 07:26 CST; read: section A and the verdict, two medium faults, F1 and F2). The other parts of the four were not read for this Change.
- **[S2] The measured miss and the pause that closes it:** `build/evidence/let-narration-converge/voice-v4/report.md`, lines 14 and 29 to 41: `produce fit` on the settled English edition of the essentials film at `v1.0.2` with the chosen reference, free −2.75 s of 600 s; `produce fit --variants`, a thought pause of 2.00 s fits. The engine as its lane held it at `b1d5ec1`, 18 November 2026.
- **[S3] The engine at `a620a57`:** `src/filmkit/narration/converge.py`, `judge.py`, `selection.py`, `judgment.py` (`held`), `src/filmkit/soundtrack/fit.py`, `assembly.py` (`bound_recordings`, `decode_recordings`, `allocate`), `policy.py` (`designed_pause_policy`), `pauses.py` (`mean_preserving_pauses`, `allocate_designed_gaps`), `src/filmkit/produce.py` (`REFUSALS`), `src/filmkit/repository.py` (`write_text`).
- **[S4] The constraints on the selection:** the draft `let-narration-converge`, `design.md`, decision 3 and its Open Questions ("The pause policy closes it inside the film's declared range, which is the film's to decide and not the engine's").
- **[S5] The asking on a real settled edition:** `build/evidence/name-the-pause-that-fits/trial-3.2/trial.md`, with the command's log, the record's `fit`, the durations and the host's state beside it: one host ticket of 20 November 2026, 09:54:24 to 09:59:20 CST, on the essentials film's English edition at `v1.0.2` with the chosen reference and the owner's clarity line declared for every thought, by this Change's code as its tree stood that hour.
