## ADDED Requirements

### Requirement: A settled edition is asked whether it fits its runtime

When its rounds end with no thought refused, the convergence SHALL select the edition's recordings and count them under the script's pause policy, by the functions that `produce select` and `produce fit` run. An edition SHALL fit when the count leaves at least the reserve free that its cast declares, and 0 s where it declares none. The count SHALL be compared as it is counted. For an edition that fits, the command SHALL exit 0 and its record SHALL state the seconds free.

#### Scenario: An edition that fits

- **WHEN** no thought is refused and the count leaves 0.8 s free
- **THEN** the command exits 0 and the record's fit states 0.8 s free

#### Scenario: An exact fit

- **WHEN** the count leaves no sample free and the cast declares no reserve
- **THEN** the edition fits

#### Scenario: A declared reserve

- **WHEN** the cast declares a reserve of 0.05 s and the count leaves 0.02 s free
- **THEN** the edition misses by 0.03 s, though the allocation accepts it

### Requirement: A miss names the seconds missing and the thought pause that would fit

For a settled edition that misses, the command SHALL exit 1 with one line that names the seconds missing and the largest thought pause, of the steps of 0.01 s up from the least value of the script's declared range to its declared pause, under which the count leaves the reserve free; or that no pause of the range fits, naming the range. The record SHALL state the same. The pause named SHALL be one that was counted, and SHALL NOT be applied. No miss SHALL be printed as no seconds.

#### Scenario: A miss that a shorter pause closes

- **WHEN** an edition with two thought joins and a thought pause of 0.45 s in a range of 0.3 to 0.6 s misses by 0.10 s
- **THEN** the line names 0.10 s and a thought pause of 0.4 s, and the script is unchanged

#### Scenario: A miss of one sample

- **WHEN** the count is one sample over the runtime
- **THEN** the command exits 1 and the seconds it names are not printed as 0.00

#### Scenario: No pause of the range fits

- **WHEN** the least pause of the range still leaves the edition 0.10 s over
- **THEN** the line says that no thought pause of the declared range fits, names the range and the 0.10 s

#### Scenario: A range whose least value lies off the steps from zero

- **WHEN** the declared range begins at 0.30405 s
- **THEN** the pauses tried begin at 0.30405 s, and the pause named is one of them as it was counted

### Requirement: The asking changes nothing and keeps nothing

The asking SHALL replace no take, change no pause policy and write no tracked file. Below `build/` it SHALL write only what `produce select` and `produce fit` write for the edition: the selection's two records and the assembly's decode work files. A run SHALL keep nothing of the count for the next: a second run SHALL say the same lines and write the same record. `produce fit` SHALL print and refuse as it did.

#### Scenario: The files written

- **WHEN** a settled edition is counted
- **THEN** the cast, the script and every recording are byte for byte as they were, and the files written, duration records apart, are the judgment's and the convergence's records, the selection's two records and the decode work files

#### Scenario: A second run on an edition that misses

- **WHEN** the convergence runs again on an edition that misses
- **THEN** it counts again, says the same line and writes the same record

#### Scenario: A run killed while it counts

- **WHEN** a run is killed between the selection and the end of the count
- **THEN** the record says that a run is under way and holds no fit, and the next run selects and counts again

### Requirement: What the count refuses is the edition's refusal

What the selection, the binding or the decoding of the count refuses SHALL end the command with exit 1 and one line that names the refusal, after the record is written as ended with it. With a thought unsettled the count SHALL NOT be asked. An edition whose cast declares no performance recording with its alignment, or whose script declares no pause policy, SHALL NOT be asked either, and the command's exit SHALL be as without the asking. The record SHALL say why the count was not asked.

#### Scenario: A recording changed since its receipt

- **WHEN** the binding refuses a recording whose waveform differs from its record
- **THEN** the command exits 1 with one line that names it, and the record is ended with that refusal

#### Scenario: The selection refuses two thoughts

- **WHEN** the selection's gates refuse two thoughts
- **THEN** the command's one line holds both refusals

#### Scenario: A recording that FFmpeg cannot decode

- **WHEN** FFmpeg ends with an error for a selected recording, whatever caused it
- **THEN** the record's fit says `refused`, and the command's one line names the command that failed and holds the last line of the error that FFmpeg wrote

#### Scenario: An error line that holds control characters

- **WHEN** the last line that FFmpeg wrote holds an escape, a bell or a tab
- **THEN** the command's one line holds a blank for each

#### Scenario: A thought unsettled

- **WHEN** a thought is still refused after its rounds
- **THEN** the count is not asked and the record says that thoughts are unsettled

#### Scenario: Nothing declared to count

- **WHEN** the cast declares no performance recording
- **THEN** the count is not asked, the record says so, and the command exits 0

### Requirement: An edition with room that the assembly refuses is refused, not missed

An edition whose count leaves the reserve free and whose allocation the assembly refuses, and one whose clips or gaps cannot be designed under the script's pause policy, SHALL end the command with exit 1 and one line that names that refusal, after the record is written as ended with the verdict `refused`. An edition whose count leaves less than the reserve free SHALL be a miss, whatever the allocation says of it.

#### Scenario: The allocation refuses an edition with room

- **WHEN** the count leaves 0.8 s free and the allocation refuses the edition for its gap limits
- **THEN** the command exits 1 with one line that names the allocation's refusal, and the record's fit says `refused` with 0.8 s free

#### Scenario: Clips that cannot be designed

- **WHEN** the edition's clips cannot be designed for their thought levels
- **THEN** the command exits 1 with one line that names the design's refusal, and the record's fit says `refused`

#### Scenario: A missed reserve that the allocation refuses too

- **WHEN** the cast declares a reserve of 0.05 s, the count leaves 0.02 s free and the allocation refuses the edition at every pause
- **THEN** the edition misses by 0.03 s, and the line says that no thought pause of the range fits, with the allocation's refusal at the largest pause that leaves the reserve free

### Requirement: A fault of the count ends the record and keeps its traceback

A fault of the count that is no refusal of the selection or the assembly SHALL be raised with its traceback, after the record is written as ended with the verdict `failed` and the fault's words. An error of the system that names no file by an absolute path, such as a decoder that is not installed, SHALL be such a fault. One that names a file by an absolute path, below the film's root or outside it, and a recording that is no WAV, SHALL be the edition's refusal, in one line.

#### Scenario: A record that lacks a segment

- **WHEN** the count ends in a `KeyError` for a segment that a record lacks
- **THEN** the command ends with that fault's traceback, and the record is ended with the fit `failed` and the fault's words

#### Scenario: A decoder that is not installed

- **WHEN** FFmpeg is not on the PATH when the recordings are decoded
- **THEN** the command ends with that fault's traceback, and the record's fit says `failed` and not `refused`

#### Scenario: A recording missing below the film's root

- **WHEN** a selected recording below the film's root is missing
- **THEN** the command exits 1 with one line that names the file, and the record's fit says `refused`

#### Scenario: A file named outside the film's root

- **WHEN** a recording or a receipt that the edition names by an absolute path outside the film's root is missing
- **THEN** the command exits 1 with one line that names the file, and the record's fit says `refused`

#### Scenario: A recording that is no WAV

- **WHEN** the selection reads a recording that is no WAV, or one that ends inside its header
- **THEN** the command exits 1 with one line, and the record's fit says `refused`

### Requirement: A declaration the count cannot read is refused before the run's first effect

The convergence SHALL refuse in one line, before it writes its record or narrates, a cast whose `runtime_fit` declares anything but `reserve_seconds` as a number of seconds from 0, and a script whose pause policy the assembly refuses.

#### Scenario: A reserve that is no number of seconds

- **WHEN** the cast declares a reserve of -0.1 s, or a text
- **THEN** the command exits 1 naming the declaration, and no record is written

#### Scenario: A script that declares no thought range

- **WHEN** the script's pause policy declares no `thought_pause_range`
- **THEN** the command exits 1 with the policy's refusal in one line, and nothing has run
