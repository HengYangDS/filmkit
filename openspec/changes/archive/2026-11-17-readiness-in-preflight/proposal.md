## Why

The three films this engine builds answer "is this edition ready for its first render?" with a script outside their repositories, and that script holds picture checks the engine does not: each one a line a reviewer drew on a rendered master (ETHOS film review round 20, DDWG film review rounds 41 and 42). A film that passes `check-picture` and `preflight` can therefore still be refused in review for a finding a light check makes in a minute, and the films' readiness depends on files no repository tracks. The draft Change `decide-before-heavy-work` holds the whole study; this Change admits its first slice, the part that lets a film drop its readiness script.

## What Changes

- **`check-picture` runs a fourth audit, the detail audit, through every frame at 60 frames per second.** It finds a line of a scene that loses part of its ink within one frame, a text outside every scene that moves over the pace line, a stroke that stands part-drawn in the quiet between two thoughts or whose tip races, and the names of a rail on two baselines that stand closer than 48 px. The strokes are read from what the composition publishes.
- **The frame audit reports runs far off centre**: each run of 0.5 s or more within one scene in which the lit picture stands more than 400 px to one side.
- **Each of these findings is gated unless the film declares it by identity with a reason**, in `[[picture.detail.exceptions]]`, and a declaration that matches no finding is refused as stale: the form the wrapping and motion exceptions have. **BREAKING** for a film that holds such a finding: `check-picture` refuses until it repairs or declares it.
- **`preflight` answers readiness.** It also asks for the sound gate's record on the current soundtrack, timeline and engine, and for a geometry record the delivery's verification would accept. It refuses a caption cue above the reading rate, and a thought under the clarity floor of a film that declares a line for single thoughts, unless the film declares each by identity with a reason. **BREAKING** for a film that calls `preflight` and holds such a cue undeclared, or runs it before `check-sound` or the geometry check.
- **A draft scan is asked only of a film that declares drafts.** The films replaced drafts by the every-frame audits; the sample film declares its drafts and keeps them.
- **`preflight` writes a readiness receipt that binds every input it judged by SHA-256, and `produce admitted` checks receipts without repeating the work**: the edition's own on every input, the other edition's on the inputs both share.

## Capabilities

### New Capabilities

- `picture-detail`: the detail audit's findings, how the picture gate judges them and how a film declares the ones it keeps.
- `edition-readiness`: the receipt that binds an edition's judged inputs, and the check of receipts against the inputs as they stand.

### Modified Capabilities

- `picture-gates`: `check-picture` runs the detail audit and binds its report; the frame audit measures runs far off centre, and the gate refuses them.
- `render-preflight`: the sound gate, the geometry record, the declared cues and the declared thoughts join what the check names; the draft scan becomes the film's to declare.
- `sample-film`: the sample film declares its drafts, and its picture task ends by asking whether both editions are still admitted.

## Impact

- `src/filmkit/picture/detail-audit.mjs` and its rule modules, `picture/rules/balance.mjs`, `picture/detail_gates.py`, `picture/gates.py`, `tools.py`, `film.py` (new declarations), `preflight.py`, `produce.py`, `production.py`, `delivery/verification.py` (the geometry requirement, extracted for `preflight` to ask) and their tests; the sample film's declaration and picture task; the README and the Changelog.
- A film's `check-picture` takes about 40 s longer for a 25-minute edition. An adopting film publishes its drawn strokes or is recorded as not judged for them, declares the findings it keeps in `content/film.toml`, and can call `preflight` and `admitted` where it ran its own script.
- Out of scope, and left in the draft with the reason in this Change's design: a flow judged at every phase of its clock, the row gap's declared floor, the sound gate's and the review prompt's part of the single-thought line, the comparison of changed takes, the listening plan in `preflight`, and admitting a host ticket on a receipt, which is the host's owner's.
