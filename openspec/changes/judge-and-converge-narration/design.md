## Context

The draft `let-narration-converge` states the narration that converges by itself in eight decisions and holds no specs or tasks: each slice is a Change of its own. This Change is its first slice, decisions 1, 2, 4 and 5. An independent review of its first form found that it bound takes no line held to their words and that several of its claims of one definition did not hold [S8]; the decisions below are as repaired. A mark such as [S3] names an entry under Sources at the end.

What the engine holds at `27e1027`, read in its sources [S4]:

- `narration/audition.py` synthesizes takes of the thoughts a targets file names, at the segment's seed + k × 7919, and measures each with private functions: its opening and ending (`take_edges`), the phrase ends it cuts, its longest unmarked pause (`flow.take_flow`), the declared terms it says (`terms.take_terms`), and its transcript against its text by recognition unit. A take qualifies when it ends naturally, cuts no phrase end, holds a phrase a person wrote, and opens in quiet where it opens its recording. Among qualifying takes the fewest differing units win.
- The assembly refuses a thought take that ends abruptly where the film's pause contract declares no release for its join (`soundtrack/assembly.py`). `preflight` holds a single thought to a clarity line only in a film that declares `review.clarity_thought_margin_db`, and says of any other film that a single thought has no line.
- A cast's retake is a seed bound to the SHA-256 of the thought's text and spoken text, with a run-on where the take was read on (`narration/retakes.py`).

What the draft's measurement found on a whole film, the essentials film at `v1.0.2` with its casts' retakes emptied, under mlx-audio 0.6.6 [S3]:

- 42 of 46 Chinese and 40 of 46 English first takes pass every line the engine refuses a take for. The failing lines: Chinese, ending 2, phrase 1, opening 2; English, ending 2, phrase 2, opening 2.
- Ten Chinese takes differ from their text in a recognition unit, and every differing unit is a homophone of the text's character (在 and 再, 作 and 做, 核 and 合, 它 and 他) or one of the particles 的 and 地: none differs by reading. Five English takes differ, by the recognizer's spellings of what was said (ten and 10, author's and authors, backtest and back test).
- With units compared as decision 1 states and a limit of none differing, the same stored first takes refuse no Chinese thought of 46 and two English ones (`ten` written `10`, twice); with the English reference the owner chose on 17 November 2026, one of 46 (`and` heard as `in`). [S9]
- The measurement's judge had to call the audition's private functions, and judged clarity on one frame grid against a line it set itself.

## Goals / Non-Goals

**Goals:**

- One definition of what a take must pass, used by the audition, by a judgment of a whole narration and by the convergence.
- A comparison of units that counts what a listener hears.
- A command that settles what a line refuses with no input from a person, and ends in a named question where it cannot.

**Non-Goals:**

- A new limit, but one: a take says its text (decision 3). Every other line judges by the film's declaration or by the constant of the engine's gate for it.
- The selection over the whole edition for the runtime, the speech model's interface, the calibration sets and a reference's qualification: decisions 3, 6, 7 and 8 of the draft.
- A change of the audition's commands or of the cast's form. What an audition qualifies a take by changes with decision 2.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **Units are compared by reading: Han characters by their reading, Latin units by their letters and digits.**
   - **Rests on:** the ten Chinese takes above, none of which differs by reading; pypinyin 0.55.0, which the engine's readings check already uses, reads 地 as `dì` and 得 as `dé` in 慢慢地说，说得清楚, where a speaker says both `de`; the English differences, of which `check's`, `authors` and `back test` hold the letters of the text's `checks`, `author's` and `backtest`.
   - **Considered:** (a) the count by character as it is; (b) readings without tone, which would count 买 and 卖 as one though a listener hears two words; (c) the dictionary's reading in context, tone kept, with the reading the film's pronunciation contract declares where it declares one, and 的, 地 and 得 as one unit where the text says a particle: its reading there is `de`, or it stands as a word of its own in the dictionary's division of the text and under no declared word; (d) Latin units as written; (e) Latin units by their letters and digits, an apostrophe dropped, and adjacent Latin units joined where the other side writes them as one; (f) a normalizer for numbers, which neither the engine nor a film's contract holds.
   - **Chosen because:** (c) and (e) remove every difference the measurement found that a listener cannot hear and keep the ones a listener can: another tone, another word, a dropped word. A Latin unit and a Han character are never alike, whatever the character's reading spells. (f) is not taken: `ten` against `10` stays a difference (decision 3, Open Questions).
   - **Applies to:** `narration/recognition.py`; a take's record, which states both counts. The transcription's `unit_error_rate` and the review's `differing_units` are records of a segment against its display text and keep the count by character.
   - **Reopened when:** a film's transcript shows a difference by reading that its owner hears as none. Known limit: 得 before 到 stands alone in the dictionary's division (得 | 到了), so 得到 heard as 的到 counts as alike.
   - **Sources:** [S3] [S5] [S8] [S9].
2. **A take is judged in one module, and each rule it shares with a gate has one owner.**
   - **Rests on:** the audition's private measures, which the draft's measurement had to call from outside; the assembly's rule for an ending, `preflight`'s rule for a thought's clarity, the engine's refusal of a recording of one second or less, and the review's finding that the first form restated three of them and left the audition a verdict of its own [S8].
   - **Considered:** (a) the audition's functions made public where they stand; (b) one module, `narration/judgment.py`, that holds the measures, what the film holds a take to and the verdict by line, with each shared rule in the module that owns its subject and called from both sides: a kept ending and the thought that opens its recording in `take_edges` (`kept_ending`, `opens_recording`; the assembly asks the first), a single thought's clarity lines in `review.clarity` (`thought_lines`, `under_its_line`; `preflight` asks them), a recording too short to be a take in `group_generation` (`too_short`; the synthesis asks it); (c) an audition that keeps its own qualification beside the judgment's.
   - **Chosen because:** (b) gives the three callers one definition. An audition qualifies a take by the judgment's lines and by nothing else; the required phrase a person wrote and the preference for a quiet ending or a length only order the qualified takes. (c) let `audition apply` bind a take `judge` refuses, and the reverse.
   - **Applies to:** `narration/judgment.py`, `audition.py`, `judge.py`, `converge.py`, `candidates.py` (the seeds, files, generation and binding both commands share), and the three owners named above. A candidate of the thought that holds a declared term's reference occurrence is not compared with the take it would replace: once bound it is the standard, so it passes where it shows two formants, as the gate asks of a reference (`terms.take_terms`).
   - **Reopened when:** a line can be judged only on an assembled soundtrack; that line then stays with its gate.
   - **Sources:** [S4] [S8].
3. **A take is held to its words: no unit of its transcript may differ from its text by reading.**
   - **Rests on:** the review's first finding [S8]: with units recorded and not judged, the convergence bound a take whose transcript held none of its words and exited 0, with no person to hear it; the audition's guard, a phrase a person wrote, has no successor in a command that takes none. The measurement on the stored first takes [S9]: with decision 1's comparison, a limit of none refuses no Chinese thought of 46 in four runs and two English thoughts in each run with the cast's reference (`ten` written `10`), one with the chosen reference (`and` heard as `in`).
   - **Considered:** (a) units recorded and not judged, as this Change first had it; (b) a phrase made from the thought's last units, which holds a take to its end only; (c) a limit above zero, which lets one wrong word a thought pass; (d) zero units differing by reading, as a constant of the judgment with its reason beside it.
   - **Chosen because:** (d): once a homophone, a spelling and a spacing are no differences, a unit that differs is a word a listener hears as another, and a convergence binds what it accepts. The owner decided it on 18 November 2026 on the review's finding, with the measurement as its condition: no stored run may refuse more than three thoughts of 46 for units alone, and none does.
   - **Applies to:** `judgment.UNIT_LIMIT`, the units line of `judgment.judge`, and with it the audition, `judge` and the convergence. A first take that differs is refused and gets candidates.
   - **Reopened when:** a film's first takes are refused for units in more than three thoughts of 46, or a thought is named as not narratable for a number the recognizer writes in digits in every candidate (Open Questions). In the run on the repaired tree neither happened [S10].
   - **Sources:** [S1] [S8] [S9].
4. **Clarity is a line of a take only where the film declares a line for a single thought.**
   - **Rests on:** `preflight`'s rule: with `review.clarity_thought_margin_db` a thought under the floor is refused unless the film keeps it in `review.clarity_exceptions` and it reads at or above the floor less the margin; without a margin no single thought is judged.
   - **Considered:** (a) the edition's floor as a line of every take, which the draft's measurement applied and which no film without a margin declares; (b) `preflight`'s rule, thought by thought.
   - **Chosen because:** (b) is the film's declaration and nothing else. A film that adopts the owner's line of 17 November 2026 for every thought declares a margin of zero and gets (a) by its own word.
   - **Applies to:** `judgment.held` and the clarity line of `judgment.judge`.
   - **Reopened when:** not applicable; the rule follows `preflight`'s.
   - **Sources:** [S4] [S6].
5. **A take's clarity is measured on the take alone, on the 16 grids of a thought.**
   - **Rests on:** the voice-clarity measure: a thought keeps few frames, so it is measured on 16 frame grids and judged by the median of their medians, against the soundtrack's loudness threshold. In this Change's acceptance run a take's value alone stood within 0.45 dB of its thought's value on the assembled soundtrack for each of 92 thoughts, and on the same side of the edition's floor for 89.
   - **Considered:** (a) one grid, as the draft's measurement took it; (b) the 16 grids, against the take's own threshold, since a candidate has no soundtrack.
   - **Chosen because:** (b) is the measure a thought is later judged by on its grids. It differs from the sound gate's in two things: the threshold, and the span, which is the whole take here and on the soundtrack the frames from the thought's first word to before its last. The two values of one take can differ, so a take near its line can still be refused on the soundtrack; the choice therefore prefers the widest margin. A take that keeps no frame has no value and is not judged, as the sound gate reads such a thought.
   - **Applies to:** `judgment.take_clarity`.
   - **Reopened when:** takes chosen above their line are refused by the sound gate in more than a rare case; the convergence then needs the assembled value in a second pass.
   - **Sources:** [S4] [S7].
6. **A choice takes the widest margin among the takes no line refuses.**
   - **Rests on:** the draft's decision 3 and its finding that a decoder's change alone moved the failing lines of 12 Chinese and 8 English thoughts of 46 each: a verdict at a line is not stable. With decision 3 every accepted take differs from its text by no unit by reading, so the count no longer orders a choice.
   - **Considered:** (a) the audition's order, the quietest ending; (b) the narrowest of a take's distances from the lines that have one, each as a share of its line: its clarity above its line, or above the floor where a thought has no line, and its unmarked pause nearest its limit below that limit; then the quietest ending, then the lowest seed.
   - **Chosen because:** (b) prefers the take least likely to be refused later and is the order the edition-wide selection will use, so a choice made now is not unmade by it. The pause is the one nearest its limit as a share, not the longest: 0.19 s under a script switch's 0.2 s stands nearer a refusal than 0.25 s under 0.4 s.
   - **Applies to:** `judgment.choose` and `judgment.margin`, used by the convergence; `flow.take_flow` records the pause nearest its limit beside the longest. The audition orders its qualified takes by the phrase and its preference.
   - **Reopened when:** the edition-wide selection lands and owns the order.
   - **Sources:** [S2] [S8].
7. **Candidates come in rounds at the audition's seeds, and a ladder ends in the text.**
   - **Rests on:** the draft's decisions 1 and 4; about one first take in ten is refused by a line. In the acceptance run 10 of 92 first takes were refused, and the first round settled each of them, with 30 candidates in all. On the repaired tree, with the units line, the same run refused 12 of 92, two of them English thoughts whose `ten` the recognizer wrote `10`, and the first round settled each, with 36 candidates: a candidate of either thought was written `ten`, and three candidates were refused for words heard as others. [S10]
   - **Considered:** (a) candidates for every thought; (b) rounds for refused thoughts only: `--takes` candidates a round at the segment's seed + k × 7919, k counted on from 11 across `--rounds` rounds, then one round of run-on takes for a thought that another follows, then a record that names the thought as not narratable as written with what each candidate failed.
   - **Chosen because:** (b) spends takes where a line asks for them, reproduces a take the audition would make at the same k, and ends in a decision that belongs to the text's owner.
   - **Applies to:** `narration/converge.py`; its two options are the budget, and a film's declaration of them is left to the slice that runs it in a build. A candidate is what its request makes it: its record holds the fingerprint of its text and run-on, reference, sampling, seed, model and libraries (`candidates.request_sha256`), and a recording a former run left is judged again only under the same fingerprint. A thought first refused by the last narration, when no round is left, is named as refused with no candidate tried, not as not narratable.
   - **Reopened when:** a film's first takes pass in fewer than half of its thoughts.
   - **Sources:** [S2] [S4] [S7].
8. **A choice is bound by the audition's own binding, and a retake narrates its segment again.**
   - **Rests on:** `retakes.bind_proposals`, which the audition's `apply` calls; a thought's request holds its segment's fingerprint, and a segment's request its thoughts' seeds, so one bound seed changes the request of every thought of its segment.
   - **Considered:** (a) a binding of the convergence's own; (b) the audition's, through one function both call; and for the narration after a round, (c) writing the chosen candidate's recording into the narration's folder, which would make a recording no narration made, or (d) the narration command itself, which generates each segment that holds a choice whole and reuses every other.
   - **Chosen because:** (b) and (d) leave the cast's form and the narration's receipts exactly as a person's audition leaves them, so a rebuild narrates each take once from the cast. The cost of (d) is one segment's narration for each segment with a choice, each round: in the acceptance run, 4 of 8 Chinese segments in 84 s and 3 of 8 English ones in 89 s.
   - **Applies to:** `candidates.bind`, `converge.narrate`. The convergence narrates into the narration's own receipt and refuses a cast that declares another; `judge` reads the receipt the cast declares.
   - **Reopened when:** a narration can reuse a thought's take across a change of its segment's other seeds, which the draft's incremental build would bring.
   - **Sources:** [S4] [S7].
9. **The selection's gates are asked about the narration as they will measure it.**
   - **Rests on:** the review's finding that two lines are judged here on another basis than the gates' [S8]: a take is aligned alone with its spoken text and its pauses are measured against its own speech, where the selection aligns the segment with its display text; the first word of a take has no word before it, so a term's vowel window differs. The acceptance run's two editions showed no disagreement in ten retaken thoughts, which establishes nothing for the eleventh.
   - **Considered:** (a) stating the difference only, as the clarity threshold's is stated; (b) judging the receipt's takes from the narration's own alignment record, which a candidate does not have; (c) asking the selection's own measure about each segment once the narration's alignment of the receipt's recordings stands beside it, and refusing a thought it refuses (`gate-pause`, `gate-terms`).
   - **Chosen because:** (c) closes the loop where the gate decides: `judge` records what the selection would refuse, and in a convergence such a thought goes to the next round like any refused thought. The selection's measure has one owner, `selection.narrated`, which `speech_refusals` and `judgment.gate_refused` both read.
   - **Applies to:** `judge.gate_of`, `judgment.gate_refused`, `judgment.with_gates`. Where no alignment of the receipt's recordings stands, the record says that the gates were not asked.
   - **Reopened when:** a candidate that every line accepts is refused by the gates in more than a rare case; the candidates are then judged in their segment.
   - **Sources:** [S4] [S8].
10. **A narration ended inside a thought is named by its file and not replayed.**

- **Rests on:** the engine's rule for a thought whose request stands started with no recording: "Unresolved native utterance; inspect before replay" (`group_generation`). The engine holds no path that clears such a request; a segment's own attempt that started and wrote nothing is taken up again.
- **Considered:** (a) the claim this Change first made, that the next run goes on, which held only for a narration ended between two thoughts; (b) a path of the convergence's own that removes the request, which would replay what the engine says to inspect; (c) naming the file and stopping before anything runs.
- **Chosen because:** (c) keeps the engine's rule and tells a person what to look at. The record says `running` from the run's first effect on, so a run ended at any point names no thought as unsettled.
- **Applies to:** `converge.leftovers`, `converge.begin`. The narration is given twice the time it may itself wait for its synthesis before anything is killed (`child_processes.run`, `seconds`).
- **Reopened when:** the engine takes up a started thought by itself.
- **Sources:** [S4] [S8].

## Risks / Trade-offs

- A recognizer's error on a take that says its text refuses the take. → The thought gets candidates, whose transcripts are the recognizer's again; a thought no candidate settles is named with each candidate's transcript in the record, for a person to hear.
- The particle rule can hide a 得 said as a particle where the text means another word (得到). → The count by unit stands beside the count by reading in every record, and decision 1 names the limit.
- A take's clarity on its own threshold and span is not its clarity on the soundtrack. → The choice prefers the margin, and the sound gate stays the judge of the assembled film.
- A thought the film keeps under its floor can be settled by a take at or above the floor; `preflight` then refuses the kept thought as a stale exception. → That is `preflight`'s rule for a declaration no thought needs any more, and the film's owner removes it.
- A run can be asked to end between a binding and the narration that follows it. → The record says `running` and holds the round's candidates; the next run narrates what the cast holds, judges the recorded candidates again from their recordings and goes on, unless the narration was ended inside a thought (decision 10).
- The recognizer and the aligner are loaded again after each narration, since the convergence lets every model go before it starts one. → Not measured: neither the seconds a reload costs nor the memory it frees.

## Open Questions

- Whether the two counts belong in the transcription's and the review's records as well.
- A number the text spells and the recognizer writes in digits (`ten`, `10`) refuses a take by decision 3, and neither the engine nor a film's contract holds how a number is said. Whether a film declares such readings, or the comparison learns them, is not decided; the stored runs hold two such thoughts of 46 with one reference and none with another. [S9]
- Whether a film declares the rounds and the takes a round in its declaration, and whether a build runs the convergence or the judgment alone.

## Sources

Read or measured on 18 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The owner, first-hand in the films' session, 18 November 2026:** at about 09:17 CST said the question was the voice's systematic solution, 「系统性解决方案，而不是手工调」.
- **[S2] The draft `let-narration-converge`:** `design.md`, decisions 1 to 5, as revised on 18 November 2026 after its measurement.
- **[S3] First takes of a whole film:** `build/evidence/let-narration-converge/voice-v2/report.md` with `judge.py`, `out/066-zh/judge.json`, `out/066-en/judge.json`, and `units-by-reading.py` with `units-by-reading.txt`. Subject: `ddwg-essentials-film` at `v1.0.2`, its casts' retakes emptied; the engine with mlx-audio 0.6.6.
- **[S4] The engine at `27e1027`:** `src/filmkit/narration/audition.py` (its module text states the audition's rule), `take_edges.py`, `flow.py`, `terms.py`, `retakes.py`, `run_on.py`, `synthesis.py`, `thought_groups.py` (`group_settings`, `parent_request`), `src/filmkit/soundtrack/assembly.py` (`_abrupt_thoughts`), `src/filmkit/preflight.py` (`clarity`) and `src/filmkit/review/clarity.py` (its module text states the measure).
- **[S5] pypinyin 0.55.0, as the engine's lock installs it:** `pinyin("慢慢地说，说得清楚的人", style=Style.TONE)` returns `dì` for 地, `dé` for 得 and `de` for 的; run in the engine's environment.
- **[S6] The clarity line:** the owner's decision of 17 November 2026, recorded in each film's local `build/evidence/next-edition/2026-11-17-owner-clarity/standard.md`.
- **[S7] The acceptance run of this Change:** `build/evidence/judge-and-converge-narration/report.md` with `run/run.sh`, `run/ticket.sh`, `run/tickets.txt`, `run/table.py`, `run/after.py` and `run/out/`. Subject: `ddwg-essentials-film` at `v1.0.2`, its casts' retakes emptied; `converge --rounds 2 --takes 3` on both editions with mlx-audio 0.6.6, then `select`, `assemble` and `check-sound`. One host ticket, 14:08 to 14:20 CST, the 1-minute load from 5.5 to 11.2, the swap at 8.7 to 10.8 GiB.
- **[S8] The independent review of this Change's first form, and its repair:** `build/evidence/judge-and-converge-narration/review-narration.md` (2 high, 13 medium and 16 low findings on the tree of 18 November 2026, 14:12 CST, with its demonstrations) and `repair.md` beside it (each finding's state and the test that fails without its repair).
- **[S9] The units line measured on stored first takes:** `build/evidence/judge-and-converge-narration/units-line/measure.py` with `measure.txt`: the transcripts of [S3]'s four runs, of the first takes with the chosen English reference (`build/evidence/let-narration-converge/voice-v3/out/c-en/judge.json`) and of this Change's first acceptance run, compared by reading without a model run on 18 November 2026.
- **[S10] The acceptance run on the repaired tree:** `build/evidence/judge-and-converge-narration/run2/table.md` with `timeline.txt`, each edition's `convergence.json` and judgment records, `run.sh`, `chain.sh` and `prepare.sh`: the essentials film at `v1.0.2` with its casts' retakes emptied again, mlx-audio 0.6.6, one host ticket on 18 November 2026, 15:09 to 15:20 CST, 666 s, the 1-minute load 9 to 12, the swap from 11.0 to 14.0 GiB with the pressure level at 2 once.
