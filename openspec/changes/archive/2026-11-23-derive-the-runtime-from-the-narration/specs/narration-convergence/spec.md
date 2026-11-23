## ADDED Requirements

### Requirement: A settled edition is counted for its runtime

When its rounds end with no thought refused, the convergence SHALL count the edition by the functions that `produce select` and `produce fit` run, and the record's fit SHALL state, as counted, the runtime the assembly would give and the seconds of the rounding's fraction that the gaps and the credits take. An edition whose allocation the assembly accepts SHALL be recorded as `fits`, with exit 0. No count SHALL be said as a miss, nor a thought pause named to reach a runtime.

#### Scenario: An edition counted

- **WHEN** no thought is refused and the speech with its designed thought pauses, its designed gaps and its closing quiet comes to 1472.14 s, with 3 s of credits
- **THEN** the command exits 0, and the record's fit states `fits`, a runtime of 1476 s and 0.86 s taken by the gaps

#### Scenario: A long narration

- **WHEN** a settled edition's speech alone comes to 1590.79 s
- **THEN** the command exits 0, and the record's fit states the runtime its count gives, with no seconds missing and no thought pause named

#### Scenario: A fraction the gaps cannot take

- **WHEN** every gap with a weight already stands at the top of its range and the rounding leaves 0.40 s
- **THEN** the command exits 0, and the record's fit states `fits`, the runtime in whole seconds, no seconds taken by the gaps and 0.40 s by the credits

### Requirement: An edition that the assembly refuses is refused

An edition whose clips or gaps cannot be designed under the script's pause policy SHALL end the command with exit 1 and one line that names that refusal, after the record is written as ended with the verdict `refused`.

#### Scenario: Clips that cannot be designed

- **WHEN** the edition's clips cannot be designed for their thought levels
- **THEN** the command exits 1 with one line that names the design's refusal, and the record's fit says `refused`

### Requirement: The count changes nothing and keeps nothing

The count SHALL replace no take, change no pause policy and write no tracked file. Below `build/` it SHALL write only what `produce select` and `produce fit` write for the edition: the selection's two records and the assembly's decode work files. A run SHALL keep nothing of the count for the next: a second run SHALL say the same lines and write the same record. `produce fit` SHALL print and refuse as the runtime fit states.

#### Scenario: The files written

- **WHEN** a settled edition is counted
- **THEN** the cast, the script and every recording are byte for byte as they were, and the files written, duration records apart, are the judgment's and the convergence's records, the selection's two records and the decode work files

#### Scenario: A second run on a counted edition

- **WHEN** the convergence runs again on an edition it counted, with nothing changed
- **THEN** it counts again, says the same line and writes the same record

#### Scenario: A run killed while it counts

- **WHEN** a run is killed between the selection and the end of the count
- **THEN** the record says that a run is under way and holds no fit, and the next run selects and counts again

### Requirement: A declaration the count does not take is refused before the run's first effect

The convergence SHALL refuse in one line, before it writes its record or narrates, a cast that declares `runtime_fit`, which nothing reads since an edition lasts as long as its narration, and a script whose pause policy the assembly refuses.

#### Scenario: A cast that still declares a reserve

- **WHEN** the cast declares `runtime_fit` with `reserve_seconds` of 0.5 s, or with no field
- **THEN** the command exits 1 naming the declaration, and no record is written

#### Scenario: A script that declares no thought range

- **WHEN** the script's pause policy declares no `thought_pause_range`
- **THEN** the command exits 1 with the policy's refusal in one line, and nothing has run

## REMOVED Requirements

### Requirement: A settled edition is asked whether it fits its runtime

**Reason**: no runtime stands beside the narration to fit or to miss, and a reserve kept free inside a runtime that the narration itself decides keeps nothing free. "A settled edition is counted for its runtime" states what the count records now.

**Migration**: a reader of the record's fit reads `runtime_seconds`; `reserve_seconds` is gone.

### Requirement: A miss names the seconds missing and the thought pause that would fit

**Reason**: no count can miss a runtime derived from it, and the films session's decision of 23 November 2026 forbids shortening thought pauses to reach a runtime, which was the one lever named.

**Migration**: none for a film; the record's fit holds no `missing_seconds` and no `pause`, and the command no longer exits 1 for a miss.

### Requirement: An edition with room that the assembly refuses is refused, not missed

**Reason**: with no miss there is nothing to tell a refusal apart from. "An edition that the assembly refuses is refused" keeps the refusal and its scenario of clips that cannot be designed.

**Migration**: none.

### Requirement: The asking changes nothing and keeps nothing

**Reason**: one of its scenarios was a second run on an edition that misses, which can no longer occur. "The count changes nothing and keeps nothing" keeps the requirement whole with that scenario on a counted edition.

**Migration**: none.

### Requirement: A declaration the count cannot read is refused before the run's first effect

**Reason**: the reserve it validated is removed. "A declaration the count does not take is refused before the run's first effect" refuses any `runtime_fit` in a cast and keeps the refusal of a pause policy the assembly refuses.

**Migration**: a cast that declares `runtime_fit` removes it; none of the three films' casts declares one.
