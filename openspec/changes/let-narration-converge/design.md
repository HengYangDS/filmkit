## Context

What the engine does today, read at `v0.23.0`. A mark such as [S2] names an entry under Sources at the end.

- `narrate` synthesizes each thought of a segment from the cast's seed, or from the seed a retake binds to that thought, aligns the recordings and transcribes them; three processes share the work. `select` validates the recordings, the assembly designs the pauses and refuses a take that ends inside its last syllable or holds an unmarked pause above its limit, and `check-sound` holds the film's lines, the clarity line among them. [S3]
- A refusal is repaired by `narration.audition`: a targets file maps each refused thought to a phrase its take must contain; the audition narrates the thought at `seed + k * 7919` for `k` up to a count, judges how each take begins and ends, transcribes it, and proposes the qualified take with the fewest differing units; `apply` binds the proposals into the cast; the retaken thoughts are narrated again. [S3]
- Counted at the films' release tags: 430 of the 542 thoughts of the six editions are bound to a seed of their own, 79 % (39 to 136 an edition); ten are run-on takes; an edition's cast changed in 13 to 29 commits and a film's pause contract in 7 to 14. [S2]
- The films' takes were made with mlx-audio 0.5.8 and 0.6.4, whose trim of decoded audio cut 80 ms for each frame whose first codebook id is 0; mlx-audio 0.6.5 repairs it. How many of the 430 bound seeds answered that fault is not known. [S6]
- Measured with the English reference chosen on 17 November 2026: first takes of all 263 English thoughts reach the clarity line where they hold sound; the DDWG film's speech is 4.1 % longer than its release's, and the shortest of six takes a thought brings that to 0.9 %. [S4]
- One process narrates about 2.8 s of speech a second (twelve takes, one run); three processes took about a third less time than one on a whole edition; batches of four takes in one forward pass were no faster than single takes in that run. [S5] [S7]
- First takes of a whole film, measured on 18 November 2026 (the essentials film at 1.0.2, 46 thoughts an edition, every thought from its cast's own seed, one narration a cell) [S11]:

  | Edition and supply                             | Pass the lines the engine refuses a take for | Also at or above 18.0 dB | Refused mostly by |
  | ---------------------------------------------- | -------------------------------------------- | ------------------------ | ----------------- |
  | Chinese, mlx-audio 0.6.4                       | 35                                           | 31                       | endings (10)      |
  | Chinese, mlx-audio 0.6.6                       | 42                                           | 37                       | clarity (6)       |
  | English, mlx-audio 0.6.4                       | 41                                           | 6                        | clarity (40)      |
  | English, mlx-audio 0.6.6                       | 40                                           | 10                       | clarity (33)      |
  | English, the chosen reference, mlx-audio 0.6.6 | 43                                           | 43                       | phrase ends (2)   |

  The trim's repair settles 8 of the 10 Chinese endings and no English one. The English edition's reference at that tag reads under the line whatever the seed: its released takes, chosen by auditions, still stand under 18.0 dB in 30 of 46 thoughts. Of the film's 81 hand-bound seeds, the released take is clearer than the first take in 72: on this film the seeds were bound for clarity, which a seed moves by tenths of a decibel and a reference by whole decibels.

  The last row is the same edition narrated once with the reference the owner chose on 17 November 2026 and nothing else changed [S12]: every one of the 46 first takes stands at or above 18.0 dB (lowest 19.94, median 21.58), each thought 2.79 to 5.47 dB clearer than with the cast's reference; 43 pass every line the engine refuses a take for, and 40 of them hold no differing unit. The other three hold five between them: four are the recognizer's spellings of what the text says (`authors` for `author's`, `back test` for `backtest`, `check's` for `checks`) and one is a word heard as another (`in` for `and`). The speech is 4.3 % longer, 520.2 s against 498.9 s.

- The first slice, the Change `judge-and-converge-narration`, settled whole editions with no person on 18 November 2026 [S13]: the essentials film's two editions with their casts' own references (4 and 8 of 46 first takes refused, every one settled in round 1, 12 and 24 candidates, 227 s and 272 s), and its English edition with the chosen reference and the owner's line declared for every thought (4 refused, none for clarity; 12 candidates, 179 s; every thought at or above 18.0 dB, lowest 19.94). No second round, run-on round or unsettled thought occurred on a real model.
- That last edition does not fit its runtime: the assembly refuses it by 2.75 s of 600 s. Its speech with thought pauses is 569.35 s, against 560.78 s with the cast's own reference, which left 5.82 s free. A thought pause of 2.00 s in place of the declared 2.12 s, inside the film's declared range, fits it with 1.81 s free and no take changed. [S13]
- The recognizer's differing units in Chinese are homophones: in three sets of 46 takes, each of the 13 or 14 differing characters has the reading of the character the text holds (在 and 再, 它 and 他, 作 and 做, the particles 的 and 地). [S11]
- A decode's difference alone, mlx-audio 0.6.4 against 0.6.6 from equal codes, changes the failing lines of 12 Chinese and 8 English thoughts of 46. [S11]

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
- A search over seeds for what a seed cannot give. Clarity that the reference lacks is the reference's to give (decision 8).

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **One take a thought first, then candidates by themselves for what a line refuses.**
   - **Rests on:** on the supply that carries the trim's repair, 42 of 46 Chinese and 40 of 46 English first takes pass every line the engine refuses a take for; with the chosen English reference, 43 of 46; under mlx-audio 0.6.4 the films had bound a seed of their own to four thoughts in five, by hand.
   - **Considered:** (a) today's order: one take a thought, then auditions a person runs for what is refused; (b) several candidates for every thought in a first round, which this draft first chose and its own measurement took back; (c) one take a thought, then rounds of candidates only for thoughts that hold no accepted take or that the edition's fit asks for, up to a declared budget, with no input from a person.
   - **Chosen because:** (c) spends takes where a line asks for them, which the measurement puts at about one thought in ten, and needs no person to say where.
   - **Applies to:** the narration command and the cast's declarations (a round's count and the budget).
   - **Reopened when:** a film's first takes pass in fewer than half of its thoughts on a qualified reference; candidates for every thought then cost less than rounds.
   - **Sources:** [S2] [S3] [S6] [S11] [S12].
2. **A candidate is judged by the film's own gates, by the same code, when it is generated.**
   - **Rests on:** the audition qualifies a take by a part of what the assembly and the sound gate later hold, and by a phrase a person wrote.
   - **Considered:** (a) the audition's qualification as it is; (b) the gates' own functions applied to each candidate, the required phrase replaced by the thought's recognized units, compared by reading where the language has homophones, and its judged ending; (c) a learned score of naturalness: not measured, and no gate of the films is stated in it.
   - **Chosen because:** (b) leaves one definition of an acceptable take, so a candidate that is selected cannot be refused later by the line that selected it. A count of differing characters cannot be that line in Chinese: every differing character measured was a homophone of the text's, so the comparison is by reading (`narration/readings.py` holds the readings), with the particles a speaker says alike taken as one.
   - **Applies to:** `narration/take_edges.py`, `flow.py`, `terms.py`, `recognition.py`, `review/clarity.py` as called by the command; `recognition.py` gains the comparison by reading.
   - **Reopened when:** a gate can be judged only on the assembled soundtrack; that gate then stays where it is and the command reads its result in a second pass.
   - **Sources:** [S3] [S11].
3. **The selection is made over the whole edition and fits the runtime.**
   - **Rests on:** the fit of the DDWG film with the chosen English reference: closed by the shortest sound take of six a thought, where the audition breaks only ties by a take's whole length. On the essentials film the size of the question is measured: an edition settled thought by thought, each by its widest margin, misses its runtime by 2.75 s, 0.5 % of its speech [S13].
   - **Considered:** (a) a choice thought by thought, with the pause limits adjusted by a person; (b) the audition ranking by kept speech (decision 23 of the draft `decide-before-heavy-work`); (c) one choice a thought over the edition: the runtime met with pauses inside the pause contract, then the fewest units that differ by reading, then the widest margin above each line, found exactly, since an edition holds at most some hundreds of thoughts and a few candidates each.
   - **Chosen because:** (c) decides the fit where every thought's alternatives are known; (b) becomes its measure of a take's length. The margin stands in the order because a verdict at a line is not stable: a decoder's change alone moved the failing lines of 20 of 92 thoughts.
   - **Applies to:** `soundtrack/fit.py` and the pause design, called by the command; the draft `decide-before-heavy-work`'s decision 23 is taken up here.
   - **Reopened when:** no selection exists within the budget for an edition; the report then names the seconds that are missing, which is a question of the film's length or text for its owner.
   - **Sources:** [S4] [S11] [S13].
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
8. **A reference voice is qualified on the film's own thoughts before the film narrates with it.**
   - **Rests on:** the English editions: with the reference of their releases, 33 to 40 of 46 first takes and 30 of 46 auditioned takes stand under the clarity line; with the reference the owner chose on 17 November 2026, every first take that holds sound, of 263 thoughts, stands above it, and a whole edition narrated once with it holds no thought under the line, against 33 of 46 with the cast's reference on the same supply. That reference was derived, measured and compared by scripts outside any repository, and chosen by the owner's ear among candidates that already met the line.
   - **Considered:** (a) a reference chosen by ear and found wanting by an edition's gates; (b) a command that narrates a panel of the film's thoughts with a candidate reference and reports what the edition's lines would say: clarity by thought, the share of first takes accepted, the speech's length against the runtime; the owner then hears only references that pass.
   - **Chosen because:** (b) moves the largest cause of repeated narration to the cheapest point, before an edition is narrated, and leaves to the ear the one thing it alone decides, which voice.
   - **Applies to:** a reference's qualification record, which the cast binds beside the reference's digest; `preflight` reads it.
   - **Reopened when:** not applicable.
   - **Sources:** [S4] [S8] [S11] [S12].

## Risks / Trade-offs

- More takes are generated for an edition. → Rounds spend them where needed; a thought whose text, voice and seed are unchanged keeps its recording, as today; the command's record states the takes and the seconds.
- A selected take passes every gate and still sounds wrong to a listener. → The reviewers and the owner's listening stay; each such finding joins a calibration set, and the gate that missed it is repaired.
- The first round's count is set before anyone knows the share of first takes that pass on the repaired supply. → It is a declaration, measured on the first whole edition and changed there.

## Open Questions

- How many of the thoughts a first take leaves refused are settled by a second or a third seed. Three whole editions settled every refused thought within the three candidates of round 1 (16 thoughts; 31 of their 48 candidates accepted) [S13]; a round that fails was not met, so the budget's size is not measured.
- Whether the selection of decision 3 closes the 2.75 s that a settled edition with the chosen reference misses [S13], from the candidates a convergence already holds or from further ones, and what it costs in takes. Not measured. The pause policy closes it inside the film's declared range, which is the film's to decide and not the engine's. The sound gate of that edition was not reached: it needs the assembly's timeline.
- The share of first takes accepted on the DDWG and ETHOS films, and in Chinese with a reference qualified this way. Not measured; the essentials film's English edition is [S12].
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
- **[S11] First takes of a whole film:** `build/evidence/let-narration-converge/voice-v2/report.md` with `tables.md`, `judge.py`, `run.sh`, `ticket.sh`, `tickets.txt`, `out/<supply>-<edition>/judge.json`, and `units-by-reading.py` with `units-by-reading.txt`. Subject: `ddwg-essentials-film` at `v1.0.2` in clones whose casts' retakes were emptied; the engine at `v0.23.0` (mlx-audio 0.6.4) and at the supply Change's moves (0.6.6). Three host tickets, 11:25 to 11:53 on 18 November 2026, the 1-minute load from 8 to 18, the swap at 6.3 to 6.5 GiB.
- **[S12] First takes with the chosen English reference:** `build/evidence/let-narration-converge/voice-v3/report.md` with `tables-c.md`, `tables-c.py`, `run.sh`, `ticket.sh`, `tickets.txt` and `out/c-en/judge.json`. Subject: `ddwg-essentials-film` at `v1.0.2`, English edition, in a clone whose cast's retakes were emptied and whose reference was replaced by the chosen one; the engine at the supply Change's moves (mlx-audio 0.6.6). One host ticket, 13:10 to 13:14 on 18 November 2026, 237 s; the 1-minute load 10.8 to 14.8, the swap from 4.5 to 9.1 GiB with the pressure level at 2 when it ended.
- **[S13] The first slice on real models, and the fit with the chosen reference:** `build/evidence/judge-and-converge-narration/run2/table.md` (both editions with the casts' own references, one host ticket, 15:09 to 15:20 CST on 18 November 2026, the 1-minute load 9 to 12) and `build/evidence/let-narration-converge/voice-v4/report.md` with `out/en-convergence.json`, `out/timeline.txt`, `out/fit.log` and `out/fit-variants.log` (the English edition with the chosen reference, `clarity_minimum_db.en = 18.0` and `clarity_thought_margin_db = 0.0`; one host ticket, 18:02 to 18:06 CST, the 1-minute load 3.8 to 7.1, swap used 15.8 to 15.9 GiB; the fits read at 18:16 and 18:19 without a model). Subject: `ddwg-essentials-film` at `v1.0.2` in clones whose casts' retakes were emptied; the engine as the lane holds it at `b1d5ec1`.
