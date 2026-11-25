## REMOVED Requirements

### Requirement: A pre-render check names every stale or missing input

**Reason**: `preflight` retires; each of its questions is answered by the node that owns its answer.

**Migration**: `filmkit plan` states readiness from the run records, and a render and a package wait for the gates `preflight` asked (`run-records`, "A heavy node waits for the gates on its inputs"); the stages by their nodes' freshness, the gates by the waits, the cover by `player-check-cover` ("A film paints its covers from its picture"), the words by `filmkit check`, an earlier package record by `package-film`'s own refusal.

### Requirement: A draft's still scan binds what it judged

**Reason**: moved with the draft's node.

**Migration**: `final-film-scan`, "A draft's still scan binds what it judged".

### Requirement: One command renders and scans an edition's draft

**Reason**: moved with the draft's node.

**Migration**: `final-film-scan`, "The node render-draft renders and scans an edition's draft".

### Requirement: The pre-render check asks for the sound gate and the geometry record

**Reason**: a render waits for the sound gate and for every edition's geometry check; the geometry check refuses its own record.

**Migration**: `filmkit plan` states readiness from the run records, and a render and a package wait for the gates `preflight` asked (`run-records`, "A heavy node waits for the gates on its inputs"); `picture-gates`, "The geometry check refuses a record that does not cover the staged film".

### Requirement: A film declares the cues it keeps above the reading rate

**Reason**: moved to the sound gate.

**Migration**: `sound-gates`, "The sound gate holds each cue to the edition's reading rate".

### Requirement: A film declares the line a single thought's clarity is judged against

**Reason**: moved to the sound gate, with the owner's hearing.

**Migration**: `sound-gates`, "The sound gate judges each thought against the film's thought line".

### Requirement: A draft's still scan settles nothing about the film

**Reason**: moved with the draft's node.

**Migration**: `final-film-scan`, "A draft's still scan settles nothing about the film".

### Requirement: The pre-render check asks the register

**Reason**: the register is asked by the source check.

**Migration**: `formal-register`, "The source check asks the register".

### Requirement: Preflight takes the owner's hearing of the selected take

**Reason**: moved to the sound gate.

**Migration**: `sound-gates`, "The sound gate takes the owner's hearing of the selected take".
