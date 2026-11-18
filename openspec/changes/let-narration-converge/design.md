## Context

What the engine does today, read at `v0.23.0`. A mark such as [S2] names an entry under Sources at the end.

- `narrate` synthesizes each thought of a segment from the cast's seed, or from the seed a retake binds to that thought, aligns the recordings and transcribes them; three processes share the work. `select` validates the recordings, the assembly designs the pauses and refuses a take that ends inside its last syllable or holds an unmarked pause above its limit, and `check-sound` holds the film's lines, the clarity line among them. [S3]
- A refusal is repaired by `narration.audition`: a targets file maps each refused thought to a phrase its take must contain; the audition narrates the thought at `seed + k * 7919` for `k` up to a count, judges how each take begins and ends, transcribes it, and proposes the qualified take with the fewest differing units; `apply` binds the proposals into the cast; the retaken thoughts are narrated again. [S3]
- Counted at the films' release tags: 430 of the 542 thoughts of the six editions are bound to a seed of their own, 79 % (39 to 136 an edition); ten are run-on takes; an edition's cast changed in 13 to 29 commits and a film's pause contract in 7 to 14. [S2]
- The films' takes were made with mlx-audio 0.5.8 and 0.6.4, whose trim of decoded audio cut 80 ms for each frame whose first codebook id is 0; mlx-audio 0.6.5 repairs it. How many of the 430 bound seeds answered that fault is not known. [S6]
- Measured with the English reference chosen on 17 November 2026: first takes of all 263 English thoughts reach the clarity line where they hold sound; the DDWG film's speech is 4.1 % longer than its release's, and the shortest of six takes a thought brings that to 0.9 %. [S4]
- One process narrates about 2.8 s of speech a second (twelve takes, one run); three processes took about a third less time than one on a whole edition; batches of four takes in one forward pass were no faster than single takes in that run. [S5] [S7]

## Goals / Non-Goals

**Goals:**

- An edition's narration reaches acceptance by one command, with no input a person keeps beside the film's declarations.
- The same take from the same tag: a rebuild repeats the selection without searching.
- The owner's ear decides what only an ear can: which voice, once, and whether a gate hears what the owner heard.
- The time of an edition's narration is measured and stated with the edition.

**Non-Goals:**

- New thresholds, or a gate lowered for one thought.
- A new voice. Another speech model is measured here and adopted elsewhere, after the owner has heard it.
- Changing a take's speed after it is made, or changing a film's text.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **Candidates for a thought are the normal path, in rounds.**
   - **Rests on:** four thoughts in five carry a seed an audition bound; the audition's own design already generates, judges and proposes, for the thoughts a person names.
   - **Considered:** (a) today's order: one take a thought, then auditions by hand for what is refused; (b) a fixed number of candidates for every thought; (c) rounds: a first round of a declared number of candidates a thought, then further rounds only for thoughts that hold no accepted candidate or that the edition's fit asks for, up to a declared budget.
   - **Chosen because:** (c) spends takes where they are needed and needs no person to say where.
   - **Applies to:** the narration command and the cast's declarations (the first round's count and the budget).
   - **Reopened when:** on the supply that carries the trim's repair most thoughts are accepted on their first take; (a)'s order with the repair made automatic then costs less.
   - **Sources:** [S2] [S3] [S6].
2. **A candidate is judged by the film's own gates, by the same code, when it is generated.**
   - **Rests on:** the audition qualifies a take by a part of what the assembly and the sound gate later hold, and by a phrase a person wrote.
   - **Considered:** (a) the audition's qualification as it is; (b) the gates' own functions applied to each candidate, the required phrase replaced by the thought's recognized units and its judged ending; (c) a learned score of naturalness: not measured, and no gate of the films is stated in it.
   - **Chosen because:** (b) leaves one definition of an acceptable take, so a candidate that is selected cannot be refused later by the line that selected it.
   - **Applies to:** `narration/take_edges.py`, `flow.py`, `terms.py`, `recognition.py`, `review/clarity.py` as called by the command.
   - **Reopened when:** a gate can be judged only on the assembled soundtrack; that gate then stays where it is and the command reads its result in a second pass.
   - **Sources:** [S3].
3. **The selection is made over the whole edition and fits the runtime.**
   - **Rests on:** the fit of the DDWG film with the chosen English reference: closed by the shortest sound take of six a thought, where the audition breaks only ties by a take's whole length.
   - **Considered:** (a) a choice thought by thought, with the pause limits adjusted by a person; (b) the audition ranking by kept speech (decision 23 of the draft `decide-before-heavy-work`); (c) one choice a thought over the edition: the runtime met with pauses inside the pause contract, then the fewest differing units, then the highest clarity, found exactly, since an edition holds at most some hundreds of thoughts and a few candidates each.
   - **Chosen because:** (c) decides the fit where every thought's alternatives are known; (b) becomes its measure of a take's length.
   - **Applies to:** `soundtrack/fit.py` and the pause design, called by the command; the draft `decide-before-heavy-work`'s decision 23 is taken up here.
   - **Reopened when:** no selection exists within the budget for an edition; the report then names the seconds that are missing, which is a question of the film's length or text for its owner.
   - **Sources:** [S4].
4. **A thought that stays unsettled climbs a ladder that ends in the text.**
   - **Rests on:** the owner's line of 17 November 2026: every thought, segment and soundtrack at or above the clarity line, with no allowance.
   - **Considered:** (a) a declared exception for the thought; (b) more candidates without limit; (c) more candidates within the budget, then run-on takes as `narration/run_on.py` makes them, then a report that names the thought as not narratable as written, with each candidate's failed line.
   - **Chosen because:** (c) ends in a decision that belongs to the text's owner and never in a pass nobody decided.
   - **Applies to:** the command's report; `preflight` reads it as it reads the sound gate's record.
   - **Reopened when:** the owner admits an allowance for a class of thoughts.
   - **Sources:** [S8].
5. **The chosen seeds are written by the command where the cast keeps them, with a record of every candidate.**
   - **Rests on:** a release's rebuild proof narrates each take once from the tracked cast and compares it byte for byte.
   - **Considered:** (a) the selection kept only in local evidence, so that a rebuild searches again; (b) the chosen seeds written to the cast's retakes by the command, each bound to its text's digest as today, and every candidate's measures kept as local evidence.
   - **Chosen because:** (b) keeps a rebuild at one pass and the cast's form as the films have it; what changes is who writes it.
   - **Applies to:** `narration/retakes.py`; the record beside the narration receipt.
   - **Reopened when:** never by this draft; the form is the released films'.
   - **Sources:** [S3].
6. **The speech model stands behind one interface, and another model is a measurement before it is a choice.**
   - **Rests on:** `narration/group_generation.py` calls one model's generator; the installed `mlx-audio` 0.6.6 carries models that take a requested duration or a speed, and documents Qwen3-TTS's own `speed` as not supported.
   - **Considered:** (a) the present model only; (b) a model with duration control in place of the selection; (c) one interface, a thought's text, a reference and a seed in and samples out, behind which each model is run by the same command and judged by the same gates.
   - **Chosen because:** (c). (b) would trade the films' chosen voices for a fit the selection already gives; with (c) such a model shows what it gives in the films' own measures.
   - **Applies to:** `narration/voice_model.py` and `group_generation.py`.
   - **Reopened when:** a model measured through the interface meets every gate on a whole edition on its first takes and the owner accepts its voice.
   - **Sources:** [S9].
7. **Each gate on sound keeps a calibration set of named findings.**
   - **Rests on:** the endings' gate was calibrated on takes with known endings, and the engine's local evidence holds that set; no other gate on sound has one.
   - **Considered:** (a) a gate written when a finding is named, tested on made examples; (b) a set a gate: takes that hold a finding the owner or a reviewer named, kept by film, tag, thought and digest, with the share of them the gate catches printed by the gate's check.
   - **Chosen because:** (b) makes "the gate hears what the owner heard" a number that a change to the gate cannot lower unseen.
   - **Applies to:** `sound-gates`; the sets as local evidence promoted with each release.
   - **Reopened when:** not applicable; a set grows with each finding.
   - **Sources:** [S10].

## Risks / Trade-offs

- More takes are generated for an edition. → Rounds spend them where needed; a thought whose text, voice and seed are unchanged keeps its recording, as today; the command's record states the takes and the seconds.
- A selected take passes every gate and still sounds wrong to a listener. → The reviewers and the owner's listening stay; each such finding joins a calibration set, and the gate that missed it is repaired.
- The first round's count is set before anyone knows the share of first takes that pass on the repaired supply. → It is a declaration, measured on the first whole edition and changed there.

## Open Questions

- How many thoughts are accepted on their first take with mlx-audio 0.6.6, on a whole edition. Not measured.
- What a round costs on a whole edition, in one and in three processes, with the host's memory and load stated. Not measured.
- Whether candidates in one batch are reproducible from their seeds and equal to single takes. One run of twelve takes compared throughput only.
- Whether a model with a requested duration keeps a reference voice closely enough to be heard by the owner at all. No such model was run.

## Sources

Read or measured on 18 November 2026 unless a date is given. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The owner, first-hand in the films' session, 18 November 2026:** at about 08:26 CST asked why the voice's improvement had left the plan and for faster iteration; at about 09:17 said the question was the voice's systematic solution, 「系统性解决方案，而不是手工调」.
- **[S2] Counts of the films' narration:** `build/evidence/let-narration-converge/figures/voice-figures.py` with its output `voice-figures.json` and `voice-figures.txt`, run on `ddwg-film` at `v1.3.1`, `ethos-film` at `v2.0.1` and `ddwg-essentials-film` at `v1.0.2`.
- **[S3] The engine at `v0.23.0`:** `src/filmkit/narration/audition.py` (its module text states the audition's rule), `narrate.py`, `synthesis.py`, `retakes.py`, `run_on.py`, `selection.py`, and `src/filmkit/soundtrack/assembly.py`, `fit.py`, `gates.py`.
- **[S4] The chosen English reference and the DDWG film's fit:** the draft `decide-before-heavy-work`, `design.md`, decision 23, and each film's local `build/evidence/next-edition/2026-11-17-owner-clarity/standard.md`.
- **[S5] Processes at once:** the archived Change `2026-11-17-shorten-the-build`, `design.md`, decision 10 (bench4 and the film trial, 17 November 2026).
- **[S6] The trim of decoded audio:** the README of `v0.23.0`, "Whole endings"; [mlx-audio's releases](https://github.com/Blaizzy/mlx-audio/releases), v0.6.5, pull request 1116; in the installed 0.6.6, `mlx_audio/tts/models/qwen3_tts/qwen3_tts.py`, the trim to the valid length.
- **[S7] The voice spike of 18 November 2026:** `build/evidence/let-narration-converge/voice-spike/report.md` with `arm0/` and `a/a1.log`: equal codes and another decode under mlx-audio 0.6.4 and 0.6.6 for 2 of 2 thoughts; twelve English takes singly at 2.79 s of speech a second and in batches of four at 2.65, one run. The spike's ticket ended with the host's forced logout at 09:27; its other arms were not run.
- **[S8] The clarity line:** the owner's decision of 17 November 2026, recorded in each film's local `build/evidence/next-edition/2026-11-17-owner-clarity/standard.md`.
- **[S9] Speech models with a duration or a speed:** `build/evidence/faster-films-less-by-hand/figures/mlx-audio-duration-parameters.txt`. No model was run.
- **[S10] The endings' calibration:** `build/evidence/ending-calibration/` and `build/evidence/gate-calibration/`, and the capability `narration-endings`.
