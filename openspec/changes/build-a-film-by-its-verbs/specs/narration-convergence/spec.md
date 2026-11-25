## ADDED Requirements

### Requirement: A narration asks the plan before any model loads

`filmkit narrate`, and the narration `python -m filmkit.narration.narrate` run to narrate or to check, SHALL refuse before any model loads while the plan calls the edition's narration not ready, naming each node before it that is not fresh with the verb that builds it. The narrations that the convergence of `filmkit narrate` runs SHALL not ask again.

#### Scenario: A retake before the source check

- **WHEN** the Chinese cast is edited for a retake and `python -m filmkit.narration.narrate --language zh --ids 24` runs before the source check has run again
- **THEN** it exits 1 before any step, in one line that names `check` and `filmkit build check`

## MODIFIED Requirements

### Requirement: A take's clarity is judged only by a line the film declares for a single thought

Where a film declares a clarity floor and a thought margin, a take that reads under the floor, or under the floor less the margin for a thought the film declares as kept, SHALL be named for the ear and not refused for its clarity, unless the owner's hearing settles its clarity. Where a film declares a floor and no margin, a take's clarity SHALL be recorded and not judged, and the record SHALL say so. Without a floor, clarity SHALL NOT be measured. The rule SHALL be the one the sound gate asks.

#### Scenario: A film with a floor and no thought line

- **WHEN** a film declares a floor of 17.0 dB for an edition and no thought margin, and a take reads 15.0 dB
- **THEN** the take's record states 15.0 dB and that a single thought has no line, and the clarity line refuses nothing

#### Scenario: A kept thought above its line

- **WHEN** a film declares a floor of 17.0 dB and a margin of 1.0 dB, keeps one thought, and that thought's take reads 16.5 dB
- **THEN** the clarity line passes for it, and a take of any other thought that reads 16.5 dB is named for the ear

#### Scenario: A thought under the line, heard by no one

- **WHEN** a thought's take passes every other line and reads 17.4 dB under an 18.0 dB thought line, and no record of hearing names it
- **THEN** the convergence generates no candidate for it, names it for the ear with its take's path, audio SHA-256, 17.4 dB and 18.0 dB, and exits 1, and the thought is not settled

#### Scenario: A thought under the line, heard on this take

- **WHEN** the film then records the owner's hearing of that take settling `clarity`
- **THEN** the thought is settled, and the judgment names nothing for the ear

#### Scenario: A thought under the line, heard on another take

- **WHEN** the film records a hearing settling `clarity` of another take of that thought
- **THEN** the thought is still named for the ear and is not settled

#### Scenario: A thought under the line that another line refuses

- **WHEN** a take reads under its thought line and also ends abruptly with no declared release
- **THEN** the take is refused by its ending line and its thought gets candidates, among which the convergence chooses by its margins as before

### Requirement: A refused thought gets candidates without a person's input

`filmkit narrate` SHALL, for each thought a line refuses, generate a round's candidates at the audition's seeds, counted on across rounds, and judge each by the same lines. It SHALL take no targets file, phrase or seed. It SHALL bind each choice into the cast's retakes, narrate and judge again, for the rounds asked for or until no thought is refused.

#### Scenario: One refused thought of two

- **WHEN** the second thought's take ends abruptly and the second of three candidates ends naturally
- **THEN** three candidates of that thought alone are generated, the second one's seed is bound, and the narration that follows is accepted

### Requirement: A settled edition is counted for its runtime

When its rounds end with no thought refused, the convergence SHALL count the edition by the functions of the node `select` and of the assembly's dry run, and the record's fit SHALL state, as counted, the runtime the assembly would give and the seconds of the rounding's fraction that the gaps and the credits take. An edition whose allocation the assembly accepts SHALL be recorded as `fits`, with exit 0. No count SHALL be said as a miss, nor a thought pause named to reach a runtime.

#### Scenario: An edition counted

- **WHEN** no thought is refused and the speech with its designed thought pauses, its designed gaps and its closing quiet comes to 1472.14 s, with 3 s of credits
- **THEN** the command exits 0, and the record's fit states `fits`, a runtime of 1476 s and 0.86 s taken by the gaps

#### Scenario: A long narration

- **WHEN** a settled edition's speech alone comes to 1590.79 s
- **THEN** the command exits 0, and the record's fit states the runtime its count gives, with no seconds missing and no thought pause named

#### Scenario: A fraction the gaps cannot take

- **WHEN** every gap with a weight already stands at the top of its range and the rounding leaves 0.40 s
- **THEN** the command exits 0, and the record's fit states `fits`, the runtime in whole seconds, no seconds taken by the gaps and 0.40 s by the credits

### Requirement: The count changes nothing and keeps nothing

The count SHALL replace no take, change no pause policy and write no tracked file. Below `build/` it SHALL write only what the node `select` and the assembly's dry run write for the edition: the selection's two records and the assembly's decode work files. A run SHALL keep nothing of the count for the next: a second run SHALL say the same lines and write the same record. The dry run SHALL print and refuse as the runtime fit states.

#### Scenario: The files written

- **WHEN** a settled edition is counted
- **THEN** the cast, the script and every recording are byte for byte as they were, and the files written, run records apart, are the judgment's and the convergence's records, the selection's two records and the decode work files

#### Scenario: A second run on a counted edition

- **WHEN** the convergence runs again on an edition it counted, with nothing changed
- **THEN** it counts again, says the same line and writes the same record

#### Scenario: A run killed while it counts

- **WHEN** a run is killed between the selection and the end of the count
- **THEN** the record says that a run is under way and holds no fit, and the next run selects and counts again

### Requirement: A judgment reads only the pinned dictionary

For an edition whose language declares its Latin-script words heard by CMUdict's pronunciations, a judgment SHALL read only the dictionary file the supply step placed, at the pinned SHA-256; where it is missing or differs, `judge`, `converge` and `audition` SHALL stop before any model loads, with one line that names the supply step. Its record SHALL name the dictionary's source and SHA-256 and the pronunciation's SHA-256. An edition of another language SHALL read no dictionary.

#### Scenario: No dictionary in place

- **WHEN** the supplied dictionary file is missing, or holds other bytes than its pinned SHA-256, and `judge` is asked about an English edition
- **THEN** the command exits 1 before any model loads, with one line that names `filmkit supply`

#### Scenario: A language that reads no dictionary

- **WHEN** no dictionary file is in place and `judge` is asked about the Chinese edition
- **THEN** the judgment runs as before and its record names no dictionary

#### Scenario: The record names the dictionary

- **WHEN** `judge` judges an English edition
- **THEN** its record names the dictionary's URL at its commit and its SHA-256, and the edition's pronunciation's SHA-256
