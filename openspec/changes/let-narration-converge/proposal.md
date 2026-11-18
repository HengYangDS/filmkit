## Why

On 18 November 2026 the owner asked for the voice's systematic solution, not tuning by hand. The narration is the part of an edition that is repeated most, and it runs on inputs a person keeps:

- **A refused thought is repaired by hand.** When the assembly or the sound gate refuses a take, a person writes a targets file that names the thought and a phrase its take must contain, runs an audition of other seeds, reads the proposals, binds them into the cast, narrates again and assembles again.
- **That repair is the rule, not the exception.** In the six released editions of the three films, 430 of 542 thoughts are bound to a seed of their own by an audition, 79 %; each edition's cast changed in 13 to 29 commits.
- **The runtime is fitted by hand.** A voice that reads longer than the film allows is fitted by pause limits a person adjusts and by auditions that prefer shorter takes; the pause contract of each film changed in 7 to 14 commits.
- **What a gate measures and what a listener hears are joined by memory.** A defect the owner or a reviewer names becomes a gate when someone writes one; only the endings have a calibration set.

This draft holds the intent in the repository. It has no specs or tasks: each slice of it is admitted as a Change of its own, with its specs and tasks. Its figures and the sources of every decision are listed in `design.md` under Sources.

## What Changes

- **One command narrates an edition until it is accepted.** It narrates one take a thought, generates candidates by itself for each thought a line refuses, judges every take by the gates the film already declares, selects one take a thought over the whole edition, and reports what it could not settle. No targets file, no phrase and no seed is written by a person.
- **A reference voice is qualified before a film narrates with it.** A command narrates a panel of the film's thoughts with a candidate reference and reports what the edition's lines would say of it; the owner hears only references that pass.
- **A candidate is judged where it is made.** The lines the assembly and the sound gate hold for a take (a whole ending, no cut phrase end, a quiet opening, no unmarked pause above its limit, the declared terms, the recognized units, the clarity line) are applied to each candidate when it is generated, by the same code. Recognized units are compared by reading where a language has homophones.
- **The selection fits the runtime.** One accepted candidate a thought is chosen so that the edition meets its length with pauses inside the film's pause contract, and among such choices the one with the fewest differing units, then the clearest.
- **A thought that no candidate settles climbs a ladder that ends in the text.** More candidates within a declared budget, then run-on takes, then the thought is reported as not narratable as written, with what each candidate failed. No gate is lowered for it.
- **The choice is recorded, and a rebuild repeats it in one pass.** The command writes the chosen seeds where the cast keeps them today and a record of every candidate's measures; a rebuild from a tag narrates the chosen seeds only.
- **The speech model stands behind one interface**, so that another model, one that takes a requested duration among them, can be measured by the same command before a film uses it.
- **Every gate on sound has a calibration set.** Takes with a finding the owner or a reviewer named are kept by reference, and each gate reports how many of them it catches; a miss is a defect of the gate.

## Capabilities

### New Capabilities

- `narration-convergence`: candidates, their judgment, the selection over an edition, the ladder and the record.
- `reference-qualification`: what a candidate reference gives on a film's own thoughts, recorded before the film narrates with it.

### Modified Capabilities

- `narration-retakes`: a retake is bound by the command that selected it; an audition by hand stays for a single thought a person wants to hear.
- `runtime-fit`: the fit is part of the selection.
- `sound-gates`: each gate names its calibration set and its result on it.

## Impact

- `src/filmkit/narration/` (synthesis, audition, retakes, selection), `soundtrack/fit.py`, `soundtrack/gates.py`, the sample film's tasks and their tests.
- Each adopting film: its narration task becomes one command; its cast keeps the seeds the command wrote.
- Out of scope: the films' texts and readings, which stay their owners'; the thresholds themselves; a change of voice, which the owner hears first; any change of a take's speed after it is made.

Owner: the engine's maintainer. Next action: admit the first slice, the candidate's judgment as one function with the comparison by reading, which the measurement of 18 November prototyped (`judge.py`); then measure what a second and a third seed settle. Read again: 2026-11-22.
