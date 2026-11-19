## Why

A thought that a gate refuses is settled by hand today: a person names it in a targets file with a phrase its transcript must hold, runs an audition, reads the proposals, binds them and narrates again. The owner asked on 18 November 2026 for the voice's systematic solution in place of tuning by hand. The draft `let-narration-converge` states that solution in eight decisions, and its own measurement of a whole film showed where the hand-kept inputs stand in its way:

- **No single definition of an acceptable take.** The audition qualifies a take by a part of what the assembly and the sound gate later hold, and by a phrase a person wrote. The measurement had to call the audition's private functions to judge a first take at all.
- **Chinese units are counted by character.** Ten Chinese first takes of 46 differed from their text in a recognition unit, and every differing unit was a homophone of the text's character or a particle a speaker says alike. A count by character ranks what a listener hears as the text below a take that says something else.
- **Nothing generates candidates by itself.** A refused thought waits for a person to say which thought, which phrase and how many seeds.

This Change is the first slice of that draft: its decisions 1, 2, 4 and 5. The selection over the whole edition for the runtime (decision 3), the speech model's interface (6), the calibration sets (7) and a reference's qualification (8) stay in the draft.

## What Changes

- **Units are compared by reading.** A substituted Chinese character with the same reading in its context, tone kept, is no difference, and the particles 的, 地 and 得 are one where the text says a particle. Latin units are compared by their letters and digits, and joined where one side writes two words as one. A take's record states the count by reading beside the count by unit.
- **A take is held to its words.** No unit of a take's transcript may differ from its text by reading: a command that binds takes with no person to hear them accepts none that is heard to say other words. An independent review of this Change's first form found that nothing held a take to its words; the limit was then measured on the stored first takes of a whole film before it was set.
- **One judgment of a take.** A new module measures a take once and gives its verdict on every line the film holds for a take: its length, how it ends and begins, its phrase ends, its unmarked pauses, the declared terms it says, its units, and its clarity where the film declares a line for a single thought. Each rule it shares with a gate has one owner that both ask. The audition qualifies a take by those lines; its required phrase and its preference order the qualified takes.
- **`python -m filmkit.narration.judge`** judges every thought of an edition's narration receipt, asks the selection's gates about the narration as they will measure it, writes one record and refuses with every refused thought and every failing line at once.
- **`python -m filmkit.narration.converge`** narrates what is missing, judges, generates candidates for each refused thought at the audition's seeds, chooses among the accepted ones, binds the choices into the cast's retakes, narrates and judges again, tries run-on takes for what is left, and names each thought it cannot settle as not narratable as written, with what each candidate failed. It needs no targets file, no phrase and no seed from a person.

Nothing here is **BREAKING** in form: the audition's commands, its targets file and its proposals keep their form, and a cast's retakes keep theirs. What an audition proposes changes: a take that a line of the judgment refuses, such as an unmarked pause above its limit or a word heard as another, is no longer proposed.

## Capabilities

### New Capabilities

- `narration-convergence`: the judgment of a take by the film's lines, the comparison of units by reading, the command that judges an edition's narration and the command that converges it.

### Modified Capabilities

- `narration-retakes`: a convergence's choices are bound as an audition's proposals are.

## Impact

- `src/filmkit/narration/`: `recognition.py` (the comparison by reading), a new `judgment.py`, `judge.py`, `converge.py` and `candidates.py`, and `audition.py`, which loses the measuring it handed over. Their tests under `tests/narration/`.
- The owners of the rules the judgment shares: `narration/take_edges.py`, `group_generation.py`, `terms.py`, `flow.py` and `selection.py`, `review/clarity.py` with `preflight.py`, `soundtrack/assembly.py`, and `child_processes.py` (the seconds a caller waits for a child asked to end). No gate's verdict changes.
- A film: nothing must change. A film that declares `review.clarity_thought_margin_db` has each take's clarity judged when the take is generated; one that declares only a floor has it recorded.
- Out of scope: the selection for the runtime, the pause design and the fit; the speech model and its interface; the gates on an assembled soundtrack; the review; the transcription's and the review's own records of differing units, which stay counts by character; the sample film's tasks.

Owner: the engine's maintainer.
