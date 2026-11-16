## Why

On 15 November 2026 three films built their next editions on `filmkit` 0.22. Expensive steps were spent and then voided by findings that a light check could have made first: five rendered pictures and a sixth interrupted, narration repeated for two thoughts, one render ticket refused after a 44-minute queue wait, and one audition that failed inside its ticket. The films' own records trace each to one of three gaps in the engine, not to the films:

- **A gate passes while it records findings that nobody disposed of.** Row gaps under the gate's own line, stretches over the pace line, captions above the reading rate and thoughts under the clarity floor were each recorded by a passing gate and found later by a reviewer or a script.
- **The order of cheap before expensive is not held across stages.** Narration ran on text that no independent recheck had passed; a sound stage run again voided the staged picture without any check saying so; a text edit left picture cues behind, which only the staged audit after narration reported; a retake that read clearer as a take read lower on the soundtrack than the take it replaced.
- **The engine's owner of "ready to render" is not the one the films use.** `preflight` requires a draft scan that the films' task lists do not make, so no film calls it, and each film's readiness rested on a script outside its repository.

This draft holds the intent in the repository. It has no specs or tasks yet: they are written when the Change is admitted, after the two editions still in build are released.

## What Changes

- **A passing gate leaves no finding undisposed.** Every class of finding a gate records is gated by a limit the film declares, declared by identity with a reason, or defined as informational in its spec. A declaration that matches no finding is refused as stale, as the wrapping and motion exceptions already are. This covers captions above the reading rate, thoughts under the clarity floor and row gaps. **BREAKING** for a film that holds such findings undeclared: its gate refuses until it declares or repairs them.
- **The row gap is gated at a floor the film declares**, 1.5 em unless it declares more, without a command-line flag.
- **The motion audit sees what a viewer sees leave.** A line that loses part of its ink within one frame while the rest stays is a pop, and a mark drawn outside a scene, such as a chapter title on its way to the running head, is either followed against the pace limit or named as outside it in the gate record.
- **A flow keeps the pace wherever its clock puts its points.** The motion audit judges a flow drawn on a way that moves at every phase of the flow's clock, so a pass does not depend on where a pause happens to put a point.
- **Caption breaks weigh the reading rate**, so a cue above the rate that another allowed break of its sentence brings under it is not produced.
- **`preflight` judges what a film builds and writes a receipt.** It also requires the sound gate's record bound to the current timeline and engine, asks for a draft scan only from a film that declares drafts, and writes a readiness receipt that binds every input it judged by digest; a second mode reads a receipt and refuses once an input has moved.
- **Text is reviewed before it is narrated.** A text review record binds a passing independent recheck to the scripts' digests; a film may declare that narration requires it. The script editor names the picture's cue phrases and labels that an edit leaves without their words.
- **A reading recorded for a place in the text moves with the text.** The script editor carries the recorded part of speech of each heteronym to its occurrence in the edited segment and names those it cannot place, and `preflight` derives the listening plan, so a reading left behind is refused before the build and not at review preparation.
- **A stroke that rests part-drawn through a quiet is a finding.** A composition publishes the share each drawn stroke has reached, and `check-picture` lists a stroke that stands between unmade and whole in the quiet after a thought.
- **A film declares what a single thought's clarity is judged against.** The declaration states the line for a thought beside the floor for the soundtrack and its segments, `check-sound` gates it, and the review prompt prints it, so a reviewer and the gate hold the same line.
- **Names on a rail's two baselines are neighbours.** The row gap also holds between names of one list that stand on alternate baselines.
- **A retake is judged on the soundtrack against the take it replaces.** A comparison with a previous edition lists each changed thought that reads lower than the replaced take beyond a margin, and `preflight` reads its record.
- **One study states the thresholds the films share and where each comes from**, so a film's design cites it instead of restating a value.

## Capabilities

### New Capabilities

- `edition-readiness`: the receipt that binds an edition's judged inputs, and the check of a receipt against the inputs as they stand.
- `text-review`: the record that binds an independent recheck's verdict to the scripts it read.

### Modified Capabilities

- `render-preflight`: the sound gate, the disposed findings, the text review and the changed takes join what the check names; the draft scan becomes the film's to declare.
- `picture-gates`: row gaps are gated at the declared floor; recorded classes are disposed.
- `sound-gates`: a thought under the clarity floor is gated unless declared; changed takes are compared with a previous edition.
- `caption-text`: breaks weigh the reading rate; a cue above it is gated unless declared.
- `narration-retakes`: a script edit names the picture's words it leaves behind; narration can require a text review.

## Impact

- `src/filmkit/preflight.py`, `picture/gates.py`, `soundtrack/` gates, `captions/`, `narration/script_edits.py`, `film.py` (new declarations) and their tests; the sample film declares what it holds.
- Each adopting film declares its accepted findings in `content/film.toml` and drops the scripts that counted them; its task list can call `preflight` before its first render ticket.
- Out of scope: admitting a host ticket on a receipt, which is the host's owner's; the review round's changes note, dispositions and release documents, which a later Change takes; the values of the thresholds themselves.

Owner: the engine's maintainer. Next action: admit the Change with its specs and tasks once the ETHOS film's edition 2.0.1 and the DDWG film's edition 1.3.1 are released. Read again: 2026-11-18.
